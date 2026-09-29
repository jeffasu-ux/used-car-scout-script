
def row_html(l: Listing, rank: str = "", excluded: bool = False) -> str:
    ded = "; ".join(f"{n} −{d // 1000}k" for n, d in l.deductions)
    life = f"{l.model_key} ~{l.life_low // 1000}k" if l.life_low else ("no lifespan data" if l.unrated else "unrated")
    notes = "; ".join(l.flags + l.notes)
    price = f"${l.price:,}" if l.price else "—"
    if l.price_note:
        price += f"<br><small>{esc(l.price_note)}</small>"
    first = f"<td>{esc(l.status)}</td>" if excluded else f"<td>{esc(rank)}</td>"
    return (f"<tr>{first}<td><span class='b {l.confidence}'>{l.confidence}</span> {badge_html(l)}"
            f"<br><small>{esc(l.conf_why)}</small></td>"
            f"<td><a href='{esc(l.url)}' target='_blank' rel='noopener'>{esc(l.title)}</a><br><small>{esc(l.source)}"
            f"{' · ' + esc(l.seller) if l.seller else ''}{' · CPO' if l.cpo else ''}{' · VIN ' + esc(l.vin) if l.vin else ''}</small></td>"
            f"<td class='num'>{price}</td><td class='num'>{fmt(l.miles)}</td>"
            f"<td class='num'><b>{left_txt(l)}</b><br><small>{esc(life)}{(' − ' + esc(ded)) if ded else ''}</small></td>"
            f"<td class='num'>{l.dist if l.dist is not None else '—'} mi<br><small>{esc(l.dist_basis)}</small></td>"
            f"<td><small>{esc(l.place)}{'<br>' if l.place and notes else ''}{esc(notes)}</small></td></tr>")


def table(rows: list[Listing], excluded: bool = False, ranks: list[str] | None = None) -> str:
    head = ("<tr><th>" + ("Why excluded" if excluded else "#") + "</th><th>Confidence</th><th>Car</th><th>Price</th>"
            "<th>Miles</th><th>Est. miles left</th><th>Distance</th><th>Notes</th></tr>")
    body = "".join(row_html(l, (ranks or [""] * len(rows))[i], excluded) for i, l in enumerate(rows))
    return f"<table>{head}{body}</table>"


def models_default(cfg: dict) -> str:
    if any_cap(cfg) is not None:
        return "any make/model (all makes; those without lifespan data labeled)"
    return "any rated model" if min_left_of(cfg) else "any model"


def unrated_method(cfg: dict) -> str:
    mml = min_left_of(cfg)
    base = "excluded" if mml else "kept as low-info (no longevity cutoff set)"
    if any_cap(cfg) is None:
        return base
    return ("kept (with the `any` cap they are never cut by the miles-left minimum), labeled \"" + UNRATED_LABEL +
            "\", given low-info confidence and sorted below every rated car that passes"
            + ("" if not cfg["price_caps"] else f"; unrated models of makes with their own cap are {base}"))


def render(cfg: dict, picks: list[Listing], passing: list[Listing], excluded: list[Listing],
           sources: list[SourceStatus], counts: dict, run_at: dt.datetime) -> str:
    caps = caps_text(cfg)
    rad, mml = radius_of(cfg), min_left_of(cfg)
    models = ", ".join(cfg.get("models") or []) or models_default(cfg)
    where = (f"Within <b>{esc(cfg['radius_miles'])} mi</b> of ZIP <b>{esc(cfg['zip'])}</b>" if rad
             else f"<b>Any distance</b> from ZIP <b>{esc(cfg['zip'])}</b>")
    must = f" ·\nmust have ≥ <b>{mml:,}</b> est. miles left" if mml else ""
    src_rows = "".join(f"<tr><td>{esc(s.name)}</td><td class='num'>{s.count}</td><td>{esc(s.note)}</td></tr>" for s in sources)
    manual = cfg.get("manual_check_links") or []
    manual_html = ("<p><b>Check by hand (not scraped):</b></p><ul>" + "".join(
        f"<li><a href='{esc(m.get('url', ''))}' target='_blank' rel='noopener'>{esc(m.get('label') or m.get('url', ''))}</a>"
        f"{(' — ' + esc(m['note'])) if m.get('note') else ''}</li>" for m in manual) + "</ul>") if manual else ""
    cards = []
    for i, l in enumerate(picks, 1):
        low = ("<p class='warn'>LOW CONFIDENCE — shown only because no high- or medium-confidence car "
               "was left to fill this slot. No history report; inspect extra carefully.</p>") if l.confidence == "low" else ""
        if l.unrated:
            low = ("<p class='warn'>NO LIFESPAN DATA — est. miles left unknown. Shown only because no rated car was "
                   "left to fill this slot; low-info confidence, judge condition and history yourself.</p>")
        ded = "; ".join(f"{n} −{d // 1000}k" for n, d in l.deductions)
        cards.append(
            f"<div class='card'><h3>{i}. <a href='{esc(l.url)}' target='_blank' rel='noopener'>{esc(l.title)}</a> "
            f"<span class='b {l.confidence}'>{l.confidence} confidence</span> {badge_html(l)}</h3>{low}"
            f"<div><b>${l.price:,}</b>{(' <small>(' + esc(l.price_note) + ')</small>') if l.price_note else ''} · {fmt(l.miles)} mi · "
            f"{('<b>' + UNRATED_LABEL + '</b>') if l.unrated else ('<b>~' + fmt(l.est_left) + ' est. miles left</b>')} · {l.dist if l.dist is not None else '—'} mi away</div>"
            f"<small>{esc(l.source)}{' · ' + esc(l.seller) if l.seller else ''}{' · ' + esc(l.place) if l.place else ''} · "
            f"{esc(l.conf_why)} · lifespan basis {(esc(l.model_key) + ' ~' + str(l.life_low // 1000) + 'k') if l.life_low else ('none' if l.unrated else 'unrated')}"
            f"{(' − ' + esc(ded)) if ded else ''} · distance from {esc(l.dist_basis)}"
            f"{(' · ' + esc('; '.join(l.flags + l.notes))) if (l.flags or l.notes) else ''}</small></div>")
    groups: dict[str, list[Listing]] = {}
    for l in excluded:
        key = l.status if not l.status.startswith("<") else "too few est. miles left"
        groups.setdefault(key, []).append(l)
    excl_html = "".join(f"<details><summary>{esc(k)} ({len(v)})</summary>{table(v, excluded=True)}</details>"
                        for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1])))
    tiers = {t: sum(1 for l in passing if l.confidence == t) for t in ("high", "medium", "low")}
    nu = sum(1 for l in passing if l.unrated)
    unr = f"; {len(passing) - nu} rated, {nu} with no lifespan data (est. miles left unknown, listed after rated cars)" if nu else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Used car scout — {run_at:%Y-%m-%d}</title><style>{CSS}</style></head><body>
<h1>Used car scout — {run_at:%Y-%m-%d %H:%M}</h1>
<p class="muted">{where} · {esc(caps)} · models: {esc(models)}{must}.</p>
<p><b>{counts['raw']}</b> listings found{f" ({counts['reposts']} repost(s) of the same car merged)" if counts.get('reposts') else ""} → <b>{counts['in_radius']}</b> within {'radius &amp; ' if rad else ''}price →
<b>{counts['passing']}</b> pass every hard filter (confidence: high {tiers['high']} · medium {tiers['medium']} · low {tiers['low']}){unr}.</p>
{'<p><b>First run:</b> this sets the baseline; later runs mark new cars and price drops.</p>' if counts.get('first_run') else ''}
<h2>Sources this run</h2><table><tr><th>Source</th><th>Listings</th><th>Notes</th></tr>{src_rows}</table>
{manual_html}
<h2>Top picks</h2>
<p class="muted">Ranked by confidence tier first (high: history report, 0 accidents → medium: history report, accidents → low: no history),
then by value (price, miles, est. miles left) inside each tier. Cars with no lifespan data always come after rated cars.</p>
{''.join(cards) or '<p>No car passed every hard filter this run.</p>'}
<h2>All cars that passed ({len(passing)})</h2>
{table(passing, ranks=[str(i) for i in range(1, len(passing) + 1)]) if passing else '<p>None.</p>'}
<h2>Excluded ({len(excluded)})</h2>{excl_html or '<p>None.</p>'}
<h2>Method</h2><p class="muted"><small>Est. miles left = low end of typical lifespan for the model with good maintenance
(conservative estimates for most US-market makes, e.g. Corolla/Camry/RAV4/Prius 250k; Civic/Accord/CR-V 220k; F-150/Silverado 200k;
Outback/Forester 200k; Altima/Sonata 180k; BMW 3/5 Series 150k; Tesla 3/Y 250k, S/X 200k)
minus odometer, minus weak-point deductions: Honda 2014–16 CVT (Fit/Civic/Accord 4-cyl/HR-V) −30k; hybrid pack 8–11 yrs −20k, 12+ yrs −40k;
Tesla pack warranty expired −40k / under 2 yrs or 25k mi left −20k; 2014–16 Model S/X drive unit/MCU −40k; plus known issues such as
Nissan 2013–18 CVTs, Ford PowerShift DPS6, Ford 5.4 3V cam phasers, Hyundai/Kia Theta II, GM AFM lifters and 2.4 oil use, Subaru EJ25 head gaskets,
BMW N20 timing chains, VW/Audi 2.0T oil use, ZF 9-speed (each −20k to −40k, shown per car).{(" With the `any` cap, unlisted models of a known make use a conservative "
"make average, labeled &quot;make-average estimate&quot;.") if any_cap(cfg) is not None else ""} Models not in the table are
"unrated" and {esc(unrated_method(cfg))}. Distance is straight-line from the ZIP center to the listing's own coordinates or ZIP centroid (farther of the two).
Craigslist is scraped best-effort from public pages; auction bids are not final. This report is a screen, not a buy signal:
get a pre-purchase inspection and a history report before you commit.</small></p>
</body></html>"""


def md_esc(v: Any) -> str:
    return re.sub(r"([|\\`*_\[\]<>])", r"\\\1", "" if v is None else str(v)).replace("\n", " ")


def md_row(l: Listing, first: str) -> str:
    ded = "; ".join(f"{n} −{d // 1000}k" for n, d in l.deductions)
    life = f"{l.model_key} ~{l.life_low // 1000}k" if l.life_low else ("no lifespan data" if l.unrated else "unrated")
    price = f"${l.price:,}" if l.price else "—"
    if l.price_note:
        price += f" ({l.price_note})"
    seller = " · ".join(x for x in [l.source, l.seller, "CPO" if l.cpo else "", f"VIN {l.vin}" if l.vin else ""] if x)
    notes = "; ".join(x for x in [l.place, "; ".join(l.flags + l.notes)] if x)
    cells = [md_esc(first),
             f"**{l.confidence}**" + (f" ({md_esc(l.badge)})" if l.badge else "") + f"<br>{md_esc(l.conf_why)}",
             f"[{md_esc(l.title)}]({l.url})<br>{md_esc(seller)}",
             md_esc(price), fmt(l.miles),
             f"**{left_txt(l)}**<br>{md_esc(life)}" + (f" − {md_esc(ded)}" if ded else ""),
             f"{l.dist if l.dist is not None else '—'} mi<br>{md_esc(l.dist_basis)}",
             md_esc(notes)]
    return "| " + " | ".join(cells) + " |"


def md_table(rows: list[Listing], excluded: bool = False) -> str:
    head = ("| " + ("Why excluded" if excluded else "#") + " | Confidence | Car | Price | Miles | Est. miles left | Distance | Notes |\n"
            "|---|---|---|---:|---:|---:|---:|---|")
    return head + "\n" + "\n".join(md_row(l, l.status if excluded else str(i)) for i, l in enumerate(rows, 1))


def render_md(cfg: dict, picks: list[Listing], passing: list[Listing], excluded: list[Listing],
              sources: list[SourceStatus], counts: dict, run_at: dt.datetime) -> str:
    """Markdown twin of render(): same header, counts, sources, picks, tables and method note."""
    caps = caps_text(cfg)
    rad, mml = radius_of(cfg), min_left_of(cfg)
    models = ", ".join(cfg.get("models") or []) or models_default(cfg)
    where = (f"Within **{cfg['radius_miles']} mi** of ZIP **{cfg['zip']}**" if rad
             else f"**Any distance** from ZIP **{cfg['zip']}**")
    must = f" · must have ≥ **{mml:,}** est. miles left" if mml else ""
    tiers = {t: sum(1 for l in passing if l.confidence == t) for t in ("high", "medium", "low")}
    nu = sum(1 for l in passing if l.unrated)
    unr = f"; {len(passing) - nu} rated, {nu} with no lifespan data (est. miles left unknown, listed after rated cars)" if nu else ""
    L: list[str] = [f"# Used car scout — {run_at:%Y-%m-%d %H:%M}", "",
                    f"{where} · {caps} · models: {models}{must}.", "",
                    f"**{counts['raw']}** listings found" + (f" ({counts['reposts']} repost(s) of the same car merged)" if counts.get("reposts") else "")
                    + f" → **{counts['in_radius']}** within {'radius & ' if rad else ''}price → "
                    f"**{counts['passing']}** pass every hard filter (confidence: high {tiers['high']} · "
                    f"medium {tiers['medium']} · low {tiers['low']}){unr}.", "",
                    *(["**First run:** this sets the baseline; later runs mark new cars and price drops.", ""]
                      if counts.get("first_run") else []),
                    "## Sources this run", "", "| Source | Listings | Notes |", "|---|---:|---|"]
    L += [f"| {md_esc(s.name)} | {s.count} | {md_esc(s.note)} |" for s in sources]
    manual = cfg.get("manual_check_links") or []
    if manual:
        L += ["", "**Check by hand (not scraped):**", ""]
        L += [f"- [{md_esc(m.get('label') or m.get('url', ''))}]({m.get('url', '')})" + (f" — {md_esc(m['note'])}" if m.get("note") else "")
              for m in manual]
    L += ["", "## Top picks", "",
          "_Ranked by confidence tier first (high: history report, 0 accidents → medium: history report, accidents → "
          "low: no history), then by value (price, miles, est. miles left) inside each tier. Cars with no lifespan data "
          "always come after rated cars._", ""]
    if not picks:
        L.append("No car passed every hard filter this run.")
    for i, l in enumerate(picks, 1):
        ded = "; ".join(f"{n} −{d // 1000}k" for n, d in l.deductions)
        L.append(f"{i}. **[{md_esc(l.title)}]({l.url})** — {l.confidence} confidence" + (f" · _{l.badge}_" if l.badge else ""))
        if l.unrated:
            L.append("   - **NO LIFESPAN DATA — est. miles left unknown.** Shown only because no rated car was left to "
                     "fill this slot; low-info confidence, judge condition and history yourself.")
        elif l.confidence == "low":
            L.append("   - **LOW CONFIDENCE** — shown only because no high- or medium-confidence car was left to fill "
                     "this slot. No history report; inspect extra carefully.")
        L.append(f"   - **${l.price:,}**" + (f" ({md_esc(l.price_note)})" if l.price_note else "") +
                 f" · {fmt(l.miles)} mi · " + (f"**{UNRATED_LABEL}**" if l.unrated else f"**~{fmt(l.est_left)} est. miles left** ")
                 + ("" if l.unrated else f"(lifespan basis {md_esc(l.model_key)} ~{l.life_low // 1000}k" + (f" − {md_esc(ded)}" if ded else ", no deductions") + ")"
                    if l.life_low else "(unrated model: lifespan unknown)"))
        L.append(f"   - {l.dist if l.dist is not None else '—'} mi away (distance from {md_esc(l.dist_basis)})")
        L.append("   - " + " · ".join(md_esc(x) for x in [l.source, l.seller, l.place] if x) + f" · confidence: {md_esc(l.conf_why)}")
        if l.flags or l.notes:
            L.append("   - Flags/notes: " + md_esc("; ".join(l.flags + l.notes)))
        L.append(f"   - Link: {l.url}")
    L += ["", f"## All cars that passed ({len(passing)})", "", md_table(passing) if passing else "None.", "",
          f"## Excluded ({len(excluded)})", ""]
    groups: dict[str, list[Listing]] = {}
    for l in excluded:
        key = l.status if not l.status.startswith("<") else "too few est. miles left"
        groups.setdefault(key, []).append(l)
    if not groups:
        L.append("None.")
    for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        L += [f"### {md_esc(k)} ({len(v)})", "", md_table(v, excluded=True), ""]
    L += ["", "## Method", "",
          "Est. miles left = low end of typical lifespan for the model with good maintenance (conservative estimates for most "
          "US-market makes, e.g. Corolla/Camry/RAV4/Prius 250k; Civic/Accord/CR-V 220k; F-150/Silverado 200k; Outback/Forester 200k; "
          "Altima/Sonata 180k; BMW 3/5 Series 150k; Tesla 3/Y 250k, S/X 200k) minus odometer, minus "
          "weak-point deductions: Honda 2014–16 CVT (Fit/Civic/Accord 4-cyl/HR-V) −30k; hybrid pack 8–11 yrs −20k, 12+ yrs −40k; "
          "Tesla pack warranty expired −40k / under 2 yrs or 25k mi left −20k; 2014–16 Model S/X drive unit/MCU −40k; plus known issues "
          "such as Nissan 2013–18 CVTs, Ford PowerShift DPS6, Ford 5.4 3V cam phasers, Hyundai/Kia Theta II, GM AFM lifters and 2.4 oil "
          "use, Subaru EJ25 head gaskets, BMW N20 timing chains, VW/Audi 2.0T oil use, ZF 9-speed (each −20k to −40k, shown per car). "
          + ("With the `any` cap, unlisted models of a known make use a conservative make average, labeled \"make-average estimate\". "
             if any_cap(cfg) is not None else "") + "Models not in "
          f"the table are \"unrated\" and {unrated_method(cfg)}. Distance is straight-line from the ZIP center to the listing's own coordinates or "
          "ZIP centroid (farther of the two). Craigslist is scraped best-effort from public pages; auction bids are not final. "
          "This report is a screen, not a buy signal: get a pre-purchase inspection and a history report before you commit.", ""]
    return "\n".join(L)


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
            caps[mk] = pr
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
    raw_caps = cfg.get("price_caps") or {}
    if not isinstance(raw_caps, dict):
        raise SystemExit("price_caps must be a list of make: price pairs, e.g. `price_caps: {any: 12000}` "
                         "(or --cap any=12000). There is no default price.")
    caps = {}
    problems: list[str] = []
    for k, v in raw_caps.items():
        if v in (None, ""):
            continue
        num = str(v).replace(",", "").replace("$", "").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)?", num):
            problems.append(f"price_caps: `{k}: {v}` is not a price. Set the most you'll pay as a number, e.g. "
                            "`any: 12000` in the config or --cap any=12000 (there is no default price)")
            continue
        caps[norm_make(str(k))] = int(float(num))
    anyc = next((caps.pop(k) for k in ANY_MAKE_KEYS if k in caps), None)
    cfg["_any_cap"] = anyc
    FUZZY_MODELS["on"] = anyc is not None
    # `any` = one cap for ALL makes (see cap_for); explicit per-make caps stay in price_caps and win for that make
    cfg["price_caps"] = caps
    cfg["zip"] = str(cfg.get("zip") or "").strip()
    if not re.fullmatch(r"\d{5}", cfg["zip"]):
        problems.append('zip: set your 5-digit US ZIP (config `zip: "12345"` or --zip 12345)')
    if not (cfg["price_caps"] or anyc is not None) and not problems:
        problems.append("price_caps: no price limit set, and there is no default. Add the most you'll pay, e.g. "
                        "`price_caps: {any: 12000}` in the config or --cap any=12000")
    if problems:
        raise SystemExit("Can't run yet. Missing required setting(s):\n  - " + "\n  - ".join(problems))
    if not str(cfg.get("output_dir") or "").strip():
        cfg["output_dir"] = os.getcwd()  # blank = current working folder
    return cfg


REPOST_MILES = 1_000  # same car reposted: odometers within this many miles (and prices within 5%)


def merge_reposts(items: list[Listing], cfg: dict) -> tuple[list[Listing], int]:
    """Same car posted more than once with different titles: same year, make and model (normalized),
    odometer within 1,000 mi and price within 5%. Keeps the lower price (then the newer post) and notes it."""
    ov = cfg.get("lifespan_overrides") or {}

    def key(l: Listing) -> tuple | None:
        if not (l.year and l.make and l.miles is not None and l.price):
            return None
        mk = model_key(l.make, f"{l.make} {l.model} {l.title}", ov)[0]
        if mk is None:  # fall back to the first word of the normalized model text
            words = re.findall(r"[a-z0-9-]+", normalize_models(" " + (l.model or "") + " "))
            mk = words[0] if words else None
        return (l.year, l.make, mk) if mk else None
