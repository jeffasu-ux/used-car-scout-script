
    keys = {id(l): key(l) for l in items}
    kept: list[Listing] = []
    merged = 0
    for l in items:
        k = keys[id(l)]
        twin = None
        if k:
            for o in kept:
                if keys[id(o)] == k and abs(o.miles - l.miles) <= REPOST_MILES and \
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
                   help="price cap (required, no default): any=PRICE for all makes, or MAKE=PRICE per make (repeatable)")
    p.add_argument("--models", help="comma-separated model allow-list, e.g. camry,corolla,civic")
    p.add_argument("--out", help="output folder for reports (default: current folder)")
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
        print(f"Wrote {path}. Fill in zip and price_caps (required; there is no default price). Everything else has "
              f"defaults: radius_miles 50, min_miles_left 50000 (blank/0 = no cutoff), any make/model, and reports in "
              f"the current folder when output_dir is blank. Then run with --config {path}")
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
    first_run = not seen  # no (or empty) seen file: this run only sets the baseline
    for l in passing:
        old = seen.get(l.id)
        if seen and old is None:
            l.badge = "new"
        elif old and l.price and l.price < old:
            l.badge = f"price drop from ${old:,}"
    seen.update({l.id: l.price for l in passing if l.price})
    seen_path.write_text(json.dumps(seen))

    counts = {"raw": len(uniq), "in_radius": in_radius, "passing": len(passing), "reposts": reposts,
              "first_run": first_run}
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
        print(f"\n{reposts} repost(s) of the same car merged (same year/make/model, odometer ±1,000, price ±5%).")
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
    if first_run:
        print("\nFirst run: this sets the baseline; later runs mark new cars and price drops.")
    print(f"\nReport: {dated}\nLatest: {out / 'latest.html'}")
    if md_path:
        print(f"Markdown: {md_path}\nLatest MD: {out / 'latest.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
