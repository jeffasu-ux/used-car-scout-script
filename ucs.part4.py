
def fetch_craigslist(cfg: dict, http: Polite, home: tuple[float, float]) -> tuple[list[Listing], SourceStatus]:
    sec = cfg["craigslist"]
    st = SourceStatus("Craigslist")
    if not sec.get("enabled", True):
        st.note = "disabled in config"
        return [], st
    out: dict[str, Listing] = {}
    seen_titles: set[tuple[str, int | None]] = set()
    errors: list[str] = []
    via: set[str] = set()
    try:
        base = cl_base(cfg, http)
    except Exception as exc:  # noqa: BLE001
        st.note = f"could not reach craigslist.org ({exc})"
        return [], st
    for make, cap in search_targets(cfg):
        # make None = the `any` cap: one search over ALL cars in the price range (no make filter, and no
        # odometer ceiling, since unrated makes are kept regardless of miles)
        tag = make or "all makes"
        q: dict[str, Any] = {"cat": "cta", "postal": cfg["zip"],
                             "search_distance": radius_of(cfg) or search_radius(cfg),
                             "radius": radius_of(cfg) or search_radius(cfg), "max_price": int(cap)}
        if make:
            q = {"cat": "cta", "auto_make_model": make, **{k: v for k, v in q.items() if k != "cat"}}
        if make and min_left_of(cfg):
            max_life = max((LIFESPAN.get(make) or {"x": 250_000}).values())
            q["max_auto_miles"] = max(max_life - min_left_of(cfg), 0)
        if cfg.get("min_price"):
            q["min_price"] = int(cfg["min_price"])
        if cfg.get("year_min"):
            q["min_auto_year"] = int(cfg["year_min"])
        if cfg.get("year_max"):
            q["max_auto_year"] = int(cfg["year_max"])
        if sec.get("purveyor") in ("owner", "dealer"):
            q["purveyor"] = sec["purveyor"]
        if sec.get("clean_title_only", True):
            q["auto_title_status"] = 1
        try:
            r = http.get(base + "?" + urlencode(q))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{tag}: {exc}")
            continue
        why = blocked(r)
        if why:
            errors.append(f"{tag}: {why}")
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        geo: dict[tuple[str, int], tuple[float, float]] = {}
        ld = soup.find("script", id="ld_searchpage_results")
        if ld and ld.string:
            try:
                for el in json.loads(ld.string).get("itemListElement") or []:
                    it = el.get("item") or {}
                    off = it.get("offers") or {}
                    g = ((off.get("availableAtOrFrom") or {}).get("geo")) or {}
                    if "latitude" in g:
                        geo[(html.unescape(it.get("name", "")).strip(), to_int(off.get("price")) or 0)] = (
                            float(g["latitude"]), float(g["longitude"]))
            except Exception:  # noqa: BLE001
                pass
        n = 0
        for li in soup.select("li.cl-static-search-result"):
            a = li.find("a")
            url = (a.get("href") if a else "") or ""
            title = (li.get("title") or (a.get_text(" ", strip=True) if a else "")).strip()
            if not url or not_a_car(title):
                continue
            pe = li.select_one(".price")
            price = to_int(pe.get_text()) if pe else parse_price(li.get_text(" "))
            lid = "cl:" + url.rstrip("/").split("/")[-1].replace(".html", "")
            dupe = (re.sub(r"\s+", " ", title.lower()), price)
            if lid in out or dupe in seen_titles:  # same car reposted
                continue
            seen_titles.add(dupe)
            ll = geo.get((title, price or 0))
            mk = find_make(title) or make or (infer_make(title) if any_cap(cfg) is not None else "")
            le = li.select_one(".location")
            out[lid] = Listing(id=lid, source="Craigslist", url=url, title=title, price=price,
                               miles=parse_miles(title), year=parse_year(title), make=mk,
                               model=model_from_title(title, mk), lat=ll[0] if ll else None,
                               lon=ll[1] if ll else None, place=le.get_text(" ", strip=True) if le else "",
                               seller="private seller" if sec.get("purveyor") == "owner" else "")
            n += 1
        # Fallbacks for the 2026 JS-rendered layout: (a) JSON-LD items, (b) the page's JSON search API.
        rows: list[dict] = []
        how = ""
        if n == 0 and ld and ld.string:
            try:
                for el in json.loads(ld.string).get("itemListElement") or []:
                    it = el.get("item") or {}
                    off = it.get("offers") or {}
                    g = ((off.get("availableAtOrFrom") or {}).get("geo")) or {}
                    u = it.get("url") or off.get("url") or el.get("url") or ""
                    if not u:
                        continue
                    rows.append({"id": "cl:" + u.rstrip("/").split("/")[-1].replace(".html", ""), "url": u,
                                 "title": html.unescape(it.get("name", "")).strip(), "price": to_int(off.get("price")),
                                 "miles": None, "lat": float(g["latitude"]) if "latitude" in g else None,
                                 "lon": float(g["longitude"]) if "longitude" in g else None, "place": ""})
                how = "JSON-LD" if rows else ""
            except Exception:  # noqa: BLE001
                rows = []
        if n == 0 and not rows:
            am = re.search(r'"areaId"\s*:\s*(\d+)', r.text)
            area_id = int(sec.get("area_id") or (am.group(1) if am else 0))
            if area_id:
                try:
                    rows = cl_sapi(http, area_id, q, sec)
                    how = "search API"
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{tag}: {exc}")
            else:
                errors.append(f"{tag}: no listings in page HTML and no areaId found (JS-only page)")
        for d in rows:
            title = d["title"]
            if not title or not_a_car(title) or d["id"] in out:
                continue
            dupe = (re.sub(r"\s+", " ", title.lower()), d["price"])
            if dupe in seen_titles:
                continue
            seen_titles.add(dupe)
            mk = find_make(title) or make or (infer_make(title) if any_cap(cfg) is not None else "")
            out[d["id"]] = Listing(id=d["id"], source="Craigslist", url=d["url"], title=title, price=d["price"],
                                   miles=d["miles"] if d["miles"] is not None else parse_miles(title),
                                   year=parse_year(title), make=mk, model=model_from_title(title, mk),
                                   lat=d["lat"], lon=d["lon"], place=d["place"], posted=int(d.get("pid") or 0),
                                   seller="private seller" if sec.get("purveyor") == "owner" else "")
            n += 1
        if how:
            via.add(how)
        # `any` searches return many cars whose odometer is only on the detail page; the JSON search API
        # has odometer + map pin for every result, so fill those in with one extra request (matched by URL).
        if any_cap(cfg) is not None and n and how != "search API":
            am = re.search(r'"areaId"\s*:\s*(\d+)', r.text)
            area_id = int(sec.get("area_id") or (am.group(1) if am else 0))
            if area_id:
                try:
                    extra = {d["url"]: d for d in cl_sapi(http, area_id, q, sec)}
                    filled = 0
                    for l in out.values():
                        d = extra.get(l.url)
                        if not d:
                            continue
                        if l.miles is None and d["miles"] is not None:
                            l.miles = d["miles"]
                            filled += 1
                        if l.lat is None and d["lat"] is not None:
                            l.lat, l.lon = d["lat"], d["lon"]
                        l.place = l.place or d["place"]
                        l.posted = l.posted or int(d.get("pid") or 0)
                    via.add(f"search API odometer for {filled}")
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{tag}: odometer lookup: {exc}")
    items = list(out.values())
    # Read detail pages (odometer, VIN, map pin, description) for the most promising candidates.
    cap = int(sec.get("detail_pages", 30))
    def prio(l: Listing) -> tuple:
        mk, _ = model_key(l.make, l.title, cfg.get("lifespan_overrides") or {})
        return (mk is None, l.year is None, -(l.year or 0), l.price or 10**9)
    detailed = 0
    def worth_opening(l: Listing) -> bool:
        # don't spend requests on cars we already know are outside the radius or unrated
        # (with `any`, unrated makes are kept, so they may be opened too, after every rated car: see prio)
        rad = radius_of(cfg)
        if rad and l.lat is not None and l.lon is not None and haversine(home, (l.lat, l.lon)) > rad:
            return False
        if any_cap(cfg) is not None and l.make not in cfg["price_caps"]:
            return True
        return model_key(l.make, l.title, cfg.get("lifespan_overrides") or {})[0] is not None
    for l in [x for x in sorted(items, key=prio) if worth_opening(x)][:cap]:
        try:
            r = http.get(l.url)
            if blocked(r):
                continue
        except Exception:  # noqa: BLE001
            continue
        detailed += 1
        s = BeautifulSoup(r.text, "html.parser")
        attrs = [e.get_text(" ", strip=True) for e in s.select(".attrgroup .attr")] or \
                [e.get_text(" ", strip=True) for e in s.select(".attrgroup span")]
        body = s.select_one("#postingbody")
        l.text = ((body.get_text(" ", strip=True) if body else "") + "\n" + " | ".join(attrs))[:4000]
        for a in attrs:
            al = a.lower()
            if al.startswith("odometer"):
                l.miles = to_int(a.split(":", 1)[-1]) or l.miles
            elif al.startswith("vin"):
                l.vin = a.split(":", 1)[-1].strip().upper()
            elif al.startswith("title status:") and "clean" not in al:
                l.text += f"\n{a} branded title"
            elif re.match(r"^(19|20)\d\d\s", a) and not l.year:
                l.year = parse_year(a)
        if l.miles is None:
            l.miles = parse_miles(l.text)
        mp = s.select_one("#map")
        if mp and mp.get("data-latitude"):
            try:
                l.lat, l.lon = float(mp["data-latitude"]), float(mp["data-longitude"])
            except (TypeError, ValueError):
                pass
    st.count = len(items)
    st.note = ((f"via {', '.join(sorted(via))}; " if via else "") + (f"{detailed} detail pages read" if items else "")
               + (f"; errors: {'; '.join(errors)}" if errors else ""))
    if not items and not errors:
        st.note = "no listings parsed (page layout may have changed)"
    return items, st


def fetch_autodev(cfg: dict, http: Polite) -> tuple[list[Listing], SourceStatus]:
    st = SourceStatus("Auto.dev")
    if not cfg["autodev"].get("enabled", True):
        st.note = "disabled in config"
        return [], st
    key = (os.environ.get("AUTO_DEV_API_KEY") or "").strip()
    if not key:
        st.note = "skipped: AUTO_DEV_API_KEY not set"
        return [], st
    hdr = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    out: dict[str, Listing] = {}
    errors: list[str] = []
    pages = int(cfg["autodev"].get("pages_per_make", 3))
    y0 = int(cfg.get("year_min") or 2000)
    y1 = int(cfg.get("year_max") or dt.date.today().year + 1)
    for make, cap in search_targets(cfg):  # make None = all makes (`any` cap)
        max_life = max((LIFESPAN.get(make or "") or {"x": 250_000}).values())
        for pg in range(1, pages + 1):
            params = {"zip": cfg["zip"], "distance": search_radius(cfg),
                      "retailListing.price": f"{int(cfg.get('min_price') or 1)}-{int(cap)}",
                      "vehicle.year": f"{y0}-{y1}", "limit": 20, "page": pg}
            if make:
                params = {"vehicle.make": make.title() if make != "bmw" else "BMW", **params}
            if make and min_left_of(cfg):
                params["retailListing.miles"] = f"0-{max(max_life - min_left_of(cfg), 0)}"
            try:
                r = http.get("https://api.auto.dev/listings?" + urlencode(params), headers=hdr)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{make} p{pg}: {exc}")
                break
            if r.status_code != 200:
                msg = f"{make} p{pg}: HTTP {r.status_code}"
                if r.status_code in (401, 402, 403):
                    msg += " (key invalid, trial ended, or plan limit)"
                errors.append(msg)
                break
            try:
                data = r.json().get("data") or []
            except Exception:  # noqa: BLE001
                errors.append(f"{make} p{pg}: non-JSON reply")
                break
            for d in data:
                v, rl, h = d.get("vehicle") or {}, d.get("retailListing") or {}, d.get("history")
                if not rl or rl.get("used") is False or not rl.get("vdp"):
                    continue
                vin = (d.get("vin") or v.get("vin") or "").upper()
                title = " ".join(str(x) for x in [v.get("year"), v.get("make"), v.get("model"), v.get("trim")] if x)
                body = f"{v.get('bodyStyle', '')} {v.get('style', '')} {v.get('type', '')}"
                if not_a_car(title) or DENY.search(f"{title} {body} {rl.get('dealer', '')}"):
                    continue
                loc = d.get("location") or []
                acc = to_int(h.get("accidentCount")) if isinstance(h, dict) and h.get("accidentCount") is not None else None
                own = to_int(h.get("ownerCount")) if isinstance(h, dict) and h.get("ownerCount") is not None else None
                lid = f"ad:{vin or rl.get('vdp')}"
                out[lid] = Listing(
                    id=lid, source="Auto.dev", url=rl.get("vdp", ""), title=title, price=to_int(rl.get("price")),
                    miles=to_int(rl.get("miles")), year=to_int(v.get("year")), make=norm_make(v.get("make", "")),
                    model=f"{v.get('model', '')} {v.get('trim', '') or ''} {v.get('series', '') or ''} {v.get('fuel', '') or ''}".lower().strip(),
                    vin=vin, lat=float(loc[1]) if len(loc) >= 2 and loc[1] is not None else None,
                    lon=float(loc[0]) if len(loc) >= 2 and loc[0] is not None else None,
                    zip=str(rl.get("zip") or ""), place=f"{rl.get('city', '')}, {rl.get('state', '')}".strip(", "),
                    seller=rl.get("dealer", "") or "dealer", cpo=bool(rl.get("cpo")), accidents=acc, owners=own,
                    text=f"{title} {body}")
            if len(data) < 20:
                break
    st.count = len(out)
    if errors:
        st.note = "errors: " + "; ".join(errors)
    return list(out.values()), st


def fetch_auctions(cfg: dict, http: Polite) -> tuple[list[Listing], SourceStatus]:
    """Best-effort: parse public auction list pages for 'YEAR MAKE MODEL' lots of the wanted makes."""
    st = SourceStatus("Auctions")
    sec = cfg.get("auctions") or {}
    urls = sec.get("urls") or []
    if not sec.get("enabled") or not urls:
        st.note = "off (add auctions.urls and set auctions.enabled to use)"
        return [], st
    makes = set(cfg["price_caps"]) | (set(KNOWN_MAKES) if any_cap(cfg) is not None else set())
    out: dict[str, Listing] = {}
    errors: list[str] = []
    pat = re.compile(r"\b(19\d\d|20[0-3]\d)\s+(" + "|".join(re.escape(m) for m in makes) + r")\b[\s,]+([\w\-]+(?:\s[\w\-]+)?)", re.I)
    for ent in urls:
        ent = {"url": ent} if isinstance(ent, str) else dict(ent)
        url, lz, label = ent.get("url", ""), str(ent.get("zip") or ""), ent.get("label") or urlparse(ent.get("url", "")).netloc
        try:
            r = http.get(url)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
            continue
        why = blocked(r)
        if why:
            errors.append(f"{label}: {why}")
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        found = 0
        for node in soup.find_all(string=pat):
            el = node.parent
            # climb to a container with some context (price, miles), but not the whole page
            for _ in range(4):
                if el.parent is not None and len(el.parent.get_text(" ", strip=True)) < 900:
                    el = el.parent
            ctx = el.get_text(" ", strip=True)
            m = pat.search(ctx) or pat.search(str(node))
            if not m:
                continue
            a = el.find("a", href=True) or (el if el.name == "a" and el.get("href") else None)
            link = urljoin(str(r.url), a["href"]) if a else str(r.url)
            lid = f"auc:{link}:{m.group(0).lower()}"
            if lid in out:
                continue
            zm = re.search(r"\b[A-Z]{2}\s+(\d{5})\b", ctx)
            out[lid] = Listing(id=lid, source="Auction", url=link, title=m.group(0), price=parse_price(ctx),
                               price_note="current bid, not final; buyer premium extra", miles=parse_miles(ctx),
                               year=int(m.group(1)), make=norm_make(m.group(2)), model=m.group(3).lower(),
                               vin=(VIN.search(ctx).group(1) if VIN.search(ctx) else ""),
                               zip=(zm.group(1) if zm else lz), seller=label, text=ctx[:2000])
            found += 1
        if not found:
            errors.append(f"{label}: no matching lots parsed (JS-only sites need a manual check)")
    st.count = len(out)
    if errors:
        st.note = "; ".join(errors)
    return list(out.values()), st

