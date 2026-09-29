
# --------------------------------------------------------------------------- report

def esc(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def fmt(v: Any) -> str:
    return f"{v:,}" if isinstance(v, int) else "—"


CSS = """
body{font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1d1d1f}
h1{margin-bottom:4px} .muted{color:#666} table{border-collapse:collapse;width:100%;margin:8px 0 20px;font-size:14px}
th,td{border-bottom:1px solid #e3e3e3;padding:6px 8px;text-align:left;vertical-align:top} th{background:#f6f6f6;position:sticky;top:0}
.b{display:inline-block;padding:1px 7px;border-radius:9px;font-size:12px;font-weight:600;white-space:nowrap}
.high{background:#d9f5df;color:#135c25}.medium{background:#fff1c9;color:#6b4d00}.low{background:#fde0dc;color:#8a1c0f}
.new{background:#dbe9ff;color:#0b3d91} .warn{color:#8a1c0f;font-weight:600} .num{text-align:right;white-space:nowrap}
.card{border:1px solid #ddd;border-radius:10px;padding:12px 14px;margin:0 0 12px} .card h3{margin:0 0 4px;font-size:17px}
details{margin:8px 0} summary{cursor:pointer;font-weight:600} small{color:#666}
"""


def badge_html(l: Listing) -> str:
    return f"<span class='b new'>{esc(l.badge)}</span>" if l.badge else ""


def left_txt(l: Listing) -> str:
    return "unknown" if l.unrated else fmt(l.est_left)


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

