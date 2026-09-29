
CSV_FIELDS = ["status", "rank", "confidence", "conf_why", "source", "year", "make", "model", "title", "price", "miles",
              "est_left", "life_low", "deductions", "dist", "dist_basis", "place", "seller", "vin", "url", "flags"]


def write_csv(path: Path, rows: list[Listing], ranked: bool) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for i, l in enumerate(rows, 1):
            w.writerow({"status": l.status, "rank": i if ranked else "", "confidence": l.confidence, "conf_why": l.conf_why,
                        "source": l.source, "year": l.year, "make": l.make, "model": l.model_key or l.model,
                        "title": l.title, "price": l.price, "miles": l.miles, "est_left": l.est_left, "life_low": l.life_low,
                        "deductions": "; ".join(f"{n} -{d}" for n, d in l.deductions), "dist": l.dist,
                        "dist_basis": l.dist_basis, "place": l.place, "seller": l.seller, "vin": l.vin, "url": l.url,
                        "flags": "; ".join(l.flags + l.notes)})


# --------------------------------------------------------------------------- main

def build_config(args: argparse.Namespace) -> dict:
    cfg = deep_merge(DEFAULTS, {})
    if args.config:
        cfg = deep_merge(cfg, load_config_file(Path(args.config)))
    if args.zip:
        cfg["zip"] = args.zip
    if args.radius is not None:
        cfg["radius_miles"] = args.radius
    if args.cap:
        caps = {}
        for c in args.cap:
            mk, _, pr = c.partition("=")
            caps[norm_make(mk)] = int(pr.replace(",", "").replace("$", ""))
        cfg["price_caps"] = caps
    if args.models:
        cfg["models"] = [m.strip().lower() for m in args.models.split(",") if m.strip()]
    if args.out:
        cfg["output_dir"] = args.out
    if args.csv:
        cfg["csv"] = True
    if args.no_md:
        cfg["md"] = False
    if args.min_miles_left is not None:
        cfg["min_miles_left"] = args.min_miles_left
    if args.top is not None:
        cfg["top_n"] = args.top
    if args.min_price is not None:
        cfg["min_price"] = args.min_price
    if args.year_min is not None:
        cfg["year_min"] = args.year_min
    if args.no_craigslist:
        cfg["craigslist"]["enabled"] = False
    if args.no_autodev:
        cfg["autodev"]["enabled"] = False
    if args.detail_pages is not None:
        cfg["craigslist"]["detail_pages"] = args.detail_pages
    if args.auction_url:
        cfg["auctions"] = {"enabled": True, "urls": [{"url": u, "zip": args.auction_zip or ""} for u in args.auction_url]}
    caps = {norm_make(str(k)): int(str(v).replace(",", "").replace("$", "")) for k, v in (cfg.get("price_caps") or {}).items()
            if v not in (None, "")}
    anyc = next((caps.pop(k) for k in ANY_MAKE_KEYS if k in caps), None)
    cfg["_any_cap"] = anyc
    FUZZY_MODELS["on"] = anyc is not None
    # `any` = one cap for ALL makes (see cap_for); explicit per-make caps stay in price_caps and win for that make
    cfg["price_caps"] = caps
    cfg["zip"] = str(cfg.get("zip") or "").strip()
    missing = [k for k, ok in [("zip", re.fullmatch(r"\d{5}", cfg["zip"])),
                               ("price_caps", cfg["price_caps"] or anyc is not None),
                               ("output_dir", cfg.get("output_dir"))] if not ok]
    if missing:
        raise SystemExit(f"Missing required setting(s): {', '.join(missing)}. Use --config or --zip/--cap/--out (see --help).")
    return cfg


def merge_reposts(items: list[Listing], cfg: dict) -> tuple[list[Listing], int]:
    """Same car posted more than once with different titles: same year, make and model (normalized),
    odometer within 500 mi and price within 5%. Keeps the lower price (then the newer post) and notes it."""
    ov = cfg.get("lifespan_overrides") or {}

    def key(l: Listing) -> tuple | None:
        if not (l.year and l.make and l.miles is not None and l.price):
            return None
        mk = model_key(l.make, f"{l.make} {l.model} {l.title}", ov)[0]
        if mk is None:  # fall back to the first word of the normalized model text
            words = re.findall(r"[a-z0-9-]+", normalize_models(" " + (l.model or "") + " "))
            mk = words[0] if words else None
        return (l.year, l.make, mk) if mk else None

    keys = {id(l): key(l) for l in items}
    kept: list[Listing] = []
    merged = 0
    for l in items:
        k = keys[id(l)]
        twin = None
        if k:
            for o in kept:
                if keys[id(o)] == k and abs(o.miles - l.miles) <= 500 and \
                        abs(o.price - l.price) <= 0.05 * max(o.price, l.price):
                    twin = o
                    break
        if twin is None:
            kept.append(l)
            continue
        merged += 1
        better = l if (l.price < twin.price or (l.price == twin.price and l.posted > twin.posted)) else twin
        other = twin if better is l else l
        if better is l:
            kept[kept.index(twin)] = l
            l.notes += [n for n in twin.notes if n.startswith("repost")]
        better.notes.append(f"repost of the same car merged (other listing ${other.price:,}: {other.url})")
    return kept, merged


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scout used cars near a ZIP and estimate miles left on each (defaults: 50 mi radius, 50k+ miles left; both optional).")
    p.add_argument("--config", help="YAML/JSON/TOML config file")
    p.add_argument("--init-config", metavar="PATH", help="write a starter YAML config and exit")
    p.add_argument("--zip")
    p.add_argument("--radius", type=float, help="hard radius in miles (default 50; 0 = any distance)")
    p.add_argument("--cap", action="append", metavar="MAKE=PRICE",
                   help="per-make price cap; repeat per make (sets the makes searched); any=PRICE = all makes")
    p.add_argument("--models", help="comma-separated model allow-list, e.g. camry,corolla,civic")
    p.add_argument("--out", help="output folder for reports")
    p.add_argument("--csv", action="store_true", help="also write CSVs (passing + excluded)")
    p.add_argument("--no-md", action="store_true", help="don't write the Markdown report (on by default)")
    p.add_argument("--min-miles-left", type=int, help="min est. miles left (default 50000; 0 = no cutoff)")
    p.add_argument("--min-price", type=int)
    p.add_argument("--year-min", type=int)
    p.add_argument("--top", type=int, help="number of top picks")
    p.add_argument("--detail-pages", type=int, help="max Craigslist listing pages to open (default 30)")
    p.add_argument("--no-craigslist", action="store_true")
    p.add_argument("--no-autodev", action="store_true")
    p.add_argument("--auction-url", action="append", help="public auction list page to parse (repeatable; turns auctions on)")
    p.add_argument("--auction-zip", help="ZIP of the auction lot, used for distance when the page has none")
    args = p.parse_args(argv)

    if args.init_config:
        path = Path(args.init_config).expanduser()
        if path.exists():
            raise SystemExit(f"{path} already exists; not overwriting.")
        path.write_text(SAMPLE_CONFIG)
        print(f"Wrote {path}. Fill in zip, price_caps and output_dir (radius_miles 50 and min_miles_left 50000 are optional defaults; blank/0 = no cutoff), "
              f"then run with --config {path}")
        return 0

    cfg = build_config(args)
    run_at = dt.datetime.now()
    as_of = run_at.year + (run_at.timetuple().tm_yday - 1) / 365.25
    if cfg.get("lat") is not None and cfg.get("lon") is not None:
        home = (float(cfg["lat"]), float(cfg["lon"]))
    else:
        c = zip_centroid(cfg["zip"])
        if not c:
            raise SystemExit(f"Could not find the center of ZIP {cfg['zip']}; set lat/lon in the config.")
        home = c
    http = Polite(float(cfg.get("request_delay_s", 1.5)))
    listings: list[Listing] = []
    sources: list[SourceStatus] = []
    for name, fn in [("Craigslist", lambda: fetch_craigslist(cfg, http, home)),
                     ("Auto.dev", lambda: fetch_autodev(cfg, http)),
                     ("Auctions", lambda: fetch_auctions(cfg, http))]:
        print(f"Searching {name}…", flush=True)
        try:
            items, st = fn()
        except Exception as exc:  # noqa: BLE001 — one broken source must not kill the run
            items, st = [], SourceStatus(name, 0, f"failed: {exc}")
        print(f"  {st.name}: {st.count}" + (f" ({st.note})" if st.note else ""), flush=True)
        listings += items
        sources.append(st)

    # de-dupe across sources by VIN (prefer the one with a history report)
    by_vin: dict[str, Listing] = {}
    uniq: list[Listing] = []
    for l in sorted(listings, key=lambda x: x.accidents is None):
        if l.vin and len(l.vin) == 17:
            if l.vin in by_vin:
                continue
            by_vin[l.vin] = l
        uniq.append(l)
    uniq, reposts = merge_reposts(uniq, cfg)

    wanted_models = [m.lower() for m in cfg.get("models") or []]
    passing: list[Listing] = []
    excluded: list[Listing] = []
    in_radius = 0
    for l in uniq:
        locate(l, home)
        cap = cap_for(cfg, l.make)
        if l.dist is None:
            l.status = "no location in listing"
        elif radius_of(cfg) and l.dist > radius_of(cfg):
            l.status = f"over {cfg['radius_miles']} mi"
        elif cap is None:
            l.status = "make not in price caps"
        elif l.price is None:
            l.status = "no price"
        elif l.price > cap or l.price < int(cfg.get("min_price") or 0):
            l.status = "outside price range"
        else:
            in_radius += 1
            assess(l, cfg, as_of)
            if l.status == "pass" and wanted_models and not any(
                    m in (l.model_key or "") or m in l.model or m in l.title.lower() for m in wanted_models):
                l.status = "model not in your list"
            if l.status == "pass" and cfg.get("year_min") and l.year and l.year < int(cfg["year_min"]):
                l.status = "older than year_min"
        if not l.conf_why:
            set_confidence(l)
            l.model_key, l.life_low = model_key(l.make, f"{l.make} {l.model} {l.title}", cfg.get("lifespan_overrides") or {})
        (passing if l.status == "pass" else excluded).append(l)

    # value score within the passing set: average percentile of price (low), miles (low), est left (high)
    n = len(passing)
    if n > 1:
        def pct(vals: list[float]) -> list[float]:
            o = sorted(vals)
            return [o.index(v) / (n - 1) for v in vals]
        P = pct([l.price for l in passing])
        M = pct([l.miles if l.miles is not None else 10**7 for l in passing])
        E = pct([-l.est_left if l.est_left is not None else 10**7 for l in passing])
        for i, l in enumerate(passing):
            l.value = round((P[i] + M[i] + E[i]) / 3, 3)
    tier = {"high": 0, "medium": 1, "low": 2}
    # rated cars first (unrated = `any` cars with no lifespan data), then tier, low-info last in tier
    passing.sort(key=lambda l: (l.unrated, l.odo_suspect, tier[l.confidence], l.est_left is None, l.value, l.dist or 0))
    picks = passing[: int(cfg["top_n"])]  # tier-sorted, so low-confidence only fills leftover slots

    out = Path(os.path.expanduser(str(cfg["output_dir"])))
    out.mkdir(parents=True, exist_ok=True)
    seen_path = out / ".ucs-seen.json"
    try:
        seen = json.loads(seen_path.read_text()) if seen_path.exists() else {}
    except Exception:  # noqa: BLE001
        seen = {}
    for l in passing:
        old = seen.get(l.id)
        if seen and old is None:
            l.badge = "new"
        elif old and l.price and l.price < old:
            l.badge = f"price drop from ${old:,}"
    seen.update({l.id: l.price for l in passing if l.price})
    seen_path.write_text(json.dumps(seen))

    counts = {"raw": len(uniq), "in_radius": in_radius, "passing": len(passing), "reposts": reposts}
    page = render(cfg, picks, passing, excluded, sources, counts, run_at)
    stamp = run_at.strftime("%Y-%m-%d_%H%M")
    dated = out / f"used-car-scout-{stamp}.html"
    dated.write_text(page, encoding="utf-8")
    (out / "latest.html").write_text(page, encoding="utf-8")
    md_path = None
    if cfg.get("md", True):
        md = render_md(cfg, picks, passing, excluded, sources, counts, run_at)
        md_path = out / f"used-car-scout-{stamp}.md"
        md_path.write_text(md, encoding="utf-8")
        (out / "latest.md").write_text(md, encoding="utf-8")
    if cfg.get("csv"):
        write_csv(out / f"used-car-scout-{stamp}.csv", passing, True)
        write_csv(out / f"used-car-scout-{stamp}-excluded.csv", excluded, False)

    if reposts:
        print(f"\n{reposts} repost(s) of the same car merged (same year/make/model, odometer ±500, price ±5%).")
    print(f"\n{counts['raw']} unique listings → {in_radius} within {'radius & ' if radius_of(cfg) else ''}price → {len(passing)} pass all hard filters.")
    reasons: dict[str, int] = {}
    for l in excluded:
        reasons[l.status] = reasons.get(l.status, 0) + 1
    for k, v in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  excluded — {k}: {v}")
    print("\nTop picks:")
    for i, l in enumerate(picks, 1):
        print(f"  {i}. [{l.confidence}] {l.title} — ${l.price:,}, {fmt(l.miles)} mi, "
              f"{UNRATED_LABEL if l.unrated else '~' + fmt(l.est_left) + ' left'}, {l.dist} mi"
              f" ({l.source}){'  LOW-CONFIDENCE GAP FILLER' if l.confidence == 'low' else ''}")
    nu = [l for l in passing if l.unrated]
    if nu:
        print(f"\n{len(nu)} passing car(s) with no lifespan data (est. miles left unknown), listed after rated cars.")
    if not picks:
        print("  (none)")
    print(f"\nReport: {dated}\nLatest: {out / 'latest.html'}")
    if md_path:
        print(f"Markdown: {md_path}\nLatest MD: {out / 'latest.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
