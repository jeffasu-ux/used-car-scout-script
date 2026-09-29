
# Model names distinctive enough to imply the make when a title omits it ("2018 Civic EX", "2002 F150").
# Digit-only and 2-letter keys and everyday words are left out.
_GENERIC_MODELS = {"fit", "flex", "edge", "element", "pilot", "compass", "journey", "quest", "echo", "century",
                   "liberty", "soul", "legacy", "spark", "insight", "passport", "discovery", "continental",
                   "aviator", "terrain", "cooper", "genesis", "matrix", "commander", "volt", "bolt", "express",
                   "transit", "defender", "envoy", "regal", "sable", "mariner", "dart", "rogue", "titan",
                   "patriot", "caliber", "nitro", "juke", "leaf", "kicks", "forte", "stinger", "atlas",
                   "beetle", "golf", "ranger", "escape", "focus", "sonic", "trax", "eos", "vibe", "tribute"}
_counts: dict[str, int] = {}
for _tbl in LIFESPAN.values():
    for _k in _tbl:
        _counts[_k] = _counts.get(_k, 0) + 1
MODEL_MAKE: dict[str, str] = {k: mk for mk, tbl in LIFESPAN.items() for k in tbl
                              if _counts[k] == 1 and len(k) >= 3 and not k.isdigit() and k not in _GENERIC_MODELS}
MODEL_MAKE.update({"ranger": "ford", "escape": "ford", "focus": "ford", "rogue": "nissan", "golf": "volkswagen",
                   "beetle": "volkswagen", "juke": "nissan"})  # generic words, but unambiguous next to a model year
# Common US-market model names that are NOT in the lifespan table, so a title like "1995 Neon" still gets its
# make (with `any`, it then uses the make average, or "no lifespan data" for makes without one). These only
# count when the title also has a model year.
EXTRA_MODEL_MAKE: dict[str, str] = {
    **dict.fromkeys(["neon", "stratus", "intrepid", "magnum", "viper", "grand caravan", "ram van", "sprinter van"], "dodge"),
    **dict.fromkeys(["cavalier", "lumina", "monte carlo", "astro", "s10", "s-10", "beretta", "el camino", "chevelle",
                     "caprice", "uplander", "aveo", "ssr", "captiva", "k10", "c10", "k1500", "c1500", "k2500",
                     "c2500"], "chevrolet"),
    **dict.fromkeys(["windstar", "freestar", "five hundred", "contour", "probe", "thunderbird", "excursion",
                     "e-150", "e-250", "e-350", "e150", "e250", "e350", "ecosport", "aerostar", "escort", "f-100",
                     "f100"], "ford"),
    **dict.fromkeys(["celica", "tercel", "previa", "t100", "supra", "paseo", "cressida", "mr2"], "toyota"),
    **dict.fromkeys(["prelude", "del sol", "cr-z", "clarity"], "honda"),
    **dict.fromkeys(["cube", "240sx", "300zx", "stanza", "nv200"], "nissan"),
    **dict.fromkeys(["protege", "millenia", "626", "rx-8", "rx8", "rx-7", "rx7", "mpv", "b2300", "b3000", "b4000"], "mazda"),
    **dict.fromkeys(["entourage", "xg350", "tiburon"], "hyundai"),
    **dict.fromkeys(["spectra", "amanti", "rondo", "borrego", "sephia"], "kia"),
    **dict.fromkeys(["montero", "diamante", "3000gt", "eclipse"], "mitsubishi"),
    **dict.fromkeys(["tribeca", "svx"], "subaru"),
    **dict.fromkeys(["sl1", "sl2", "sc2", "ion", "vue", "aura"], "saturn"),
    **dict.fromkeys(["sunfire", "grand am", "bonneville", "aztek", "firebird", "solstice", "trans am", "fiero"], "pontiac"),
    **dict.fromkeys(["alero", "cutlass", "bravada", "delta 88", "achieva"], "oldsmobile"),
    **dict.fromkeys(["prowler"], "plymouth"),
    **dict.fromkeys(["concorde", "lhs", "crossfire", "le baron", "lebaron", "new yorker", "cirrus"], "chrysler"),
    **dict.fromkeys(["comanche", "cj5", "cj-5", "cj7", "cj-7"], "jeep"),
    **dict.fromkeys(["9-3", "9-5"], "saab"),
    **dict.fromkeys(["sx4", "grand vitara", "vitara", "xl-7", "xl7", "kizashi", "samurai", "forenza", "aerio"], "suzuki"),
    **dict.fromkeys(["rodeo", "trooper", "ascender", "hombre"], "isuzu"),
    **dict.fromkeys(["villager", "marauder", "montego"], "mercury"),
    **dict.fromkeys(["skylark", "terraza", "cascada", "roadmaster", "riviera"], "buick"),
    **dict.fromkeys(["seville", "eldorado", "catera", "xlr", "fleetwood"], "cadillac"),
    **dict.fromkeys(["mark lt", "mark viii", "zephyr", "blackwood"], "lincoln"),
    **dict.fromkeys(["rabbit", "routan", "cabrio", "corrado", "vanagon", "eurovan", "arteon"], "volkswagen"),
    **dict.fromkeys(["clk", "cls"], "mercedes"),
    **dict.fromkeys(["c70", "s70", "v50"], "volvo"),
    **dict.fromkeys(["500l", "500x"], "fiat"),
    **dict.fromkeys(["giulia", "stelvio"], "alfa romeo"),
    **dict.fromkeys(["jimmy", "sonoma", "s15"], "gmc"),
}


def find_make(text: str) -> str:
    t = (text or "").lower()
    for m in KNOWN_MAKES:
        if re.search(rf"(?<![a-z]){re.escape(m)}(?![a-z])", t):
            return norm_make(m)
    return ""


# Conservative typo fixes seen in real listings, plus glued-on suffixes ("focus52km" -> "focus 52km").
TYPOS = [(r"(?<![a-z])(?<!santa )cruz(?![a-z])", "cruze"), (r"(?<![a-z])camey(?![a-z])", "camry"),
         (r"(?<![a-z])pruis(?![a-z])", "prius"), (r"(?<![a-z])corrolla(?![a-z])", "corolla"),
         (r"(?<![a-z])carolla(?![a-z])", "corolla"), (r"(?<![a-z])acord(?![a-z])", "accord"),
         (r"(?<![a-z])civc(?![a-z])", "civic"), (r"(?<![a-z])tacomo(?![a-z])", "tacoma"),
         (r"(?<![a-z])silverato(?![a-z])", "silverado"), (r"(?<![a-z])expidition(?![a-z])", "expedition")]
_ALL_MODELS = sorted({k for tbl in LIFESPAN.values() for k in tbl if k[-1].isalpha() and len(k) >= 4}, key=len, reverse=True)
_GLUED = re.compile(r"(?<![a-z0-9-])(" + "|".join(re.escape(k) for k in _ALL_MODELS) +
                    r")(\d+(?:k|km|mi|miles)?|k|km)(?![a-z0-9])")


FUZZY_MODELS = {"on": False}  # typo / glued-suffix fixes: switched on for `any` (all makes) searches in build_config


def normalize_models(t: str) -> str:
    """Lower-case title text with aliases (and, for `any` searches, common misspellings and glued suffixes) fixed."""
    for a, b in ALIASES.items():
        t = re.sub(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", b, t)
    if not FUZZY_MODELS["on"]:
        return t
    for rx, rep in TYPOS:
        t = re.sub(rx, rep, t)
    return _GLUED.sub(r"\1 \2", t)


def infer_make(title: str) -> str:
    """Make from a distinctive model name, for titles like '2018 Civic EX' (used only with the `any` cap)."""
    has_year = parse_year(title) is not None
    t = normalize_models(" " + (title or "").lower().replace("_", " ") + " ")
    for k in sorted(MODEL_MAKE, key=len, reverse=True):
        if (has_year or len(k) >= 6) and re.search(rf"(?<![a-z0-9-]){re.escape(k)}(?![a-z0-9-])", t):
            return MODEL_MAKE[k]
    if has_year:
        for k in sorted(EXTRA_MODEL_MAKE, key=len, reverse=True):
            if re.search(rf"(?<![a-z0-9-]){re.escape(k)}(?![a-z0-9-])", t):
                return EXTRA_MODEL_MAKE[k]
    return ""


def model_key(make: str, text: str, overrides: dict[str, int]) -> tuple[str | None, int | None]:
    make = norm_make(make)
    t = normalize_models(" " + (text or "").lower().replace("_", " ") + " ")
    if make == "bmw":  # 328i / 535xi / 330e -> "3 series" / "5 series"
        t = re.sub(r"(?<![a-z0-9])([2-7])\d\d(?:i|d|e|xi|ci|li|is|xd)(?![a-z0-9])", r"\1 series", t)
    elif make == "mercedes":  # C300 / E 350 / ML350 / GLK350 -> class names
        t = re.sub(r"(?<![a-z0-9-])(cla|gla|glc|glk|gle|gls|slk|ml|gl|c|e|s)[ -]?\d{2,3}[a-z]*(?![a-z0-9])",
                   lambda m: {"c": "c-class", "e": "e-class", "s": "s-class"}.get(m.group(1), m.group(1)), t)
    for k, v in overrides.items():  # user overrides "make model"
        mk, _, md = k.lower().partition(" ")
        if mk == make and md and re.search(rf"(?<![a-z0-9-]){re.escape(md)}(?![a-z0-9-])", t):
            return md, int(v)
    table = LIFESPAN.get(make) or {}
    for k in sorted(table, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9-]){re.escape(k)}(?![a-z0-9-])", t):
            # "is" / "es" etc. only count as Lexus models when followed by a number or space-trim
            return k, table[k]
    return None, None


def tesla_warranty(key: str, text: str, year: int, as_of: float) -> tuple[float, int | None]:
    """(years_left, mileage_cap or None=unlimited). Assumes in service Jan 1 of model year."""
    if key in ("model s", "model x"):
        cap = None if year < 2020 else 150_000
    elif re.search(r"long range|performance|\blr\b|awd", text.lower()):
        cap = 120_000
    else:
        cap = 100_000
    return year + 8 - as_of, cap


UNRATED_LABEL = "no lifespan data — est. miles left unknown"


def mark_unrated(l: Listing) -> None:
    """`any` search: keep a make/model we have no lifespan data for, clearly labeled, low-info confidence."""
    l.unrated = True
    l.status = "pass"
    l.est_left = None
    l.notes.append(UNRATED_LABEL)
    l.confidence = "low"
    l.conf_why = "low info: no lifespan data for this make/model" + (f"; {l.conf_why}" if l.conf_why else "")


def set_confidence(l: Listing) -> None:
    """Confidence tier: high = history report + 0 accidents; medium = history + accidents; low = no history."""
    if l.source == "Auction":
        l.confidence, l.conf_why = "low", "auction: as-is, no history report"
    elif l.accidents is None:
        l.confidence, l.conf_why = "low", ("private seller, no history report" if l.source == "Craigslist"
                                             else "no history report data")
    elif l.accidents == 0:
        l.confidence, l.conf_why = "high", "history report: 0 accidents"
    else:
        l.confidence, l.conf_why = "medium", f"history report: {l.accidents} accident(s)"
    if l.owners is not None:
        l.conf_why += f", {l.owners} owner(s)"


def assess(l: Listing, cfg: dict, as_of: float) -> None:
    text = f"{l.make} {l.model} {l.title}"
    l.model_key, l.life_low = model_key(l.make, text, cfg.get("lifespan_overrides") or {})
    set_confidence(l)
    blob = f"{l.title}\n{l.text}"
    l.flags = [lab for rx, lab in CAUTION if rx.search(blob)]
    if l.year and l.price and l.year >= int(as_of) - 8 and l.price < 7000:
        l.flags.append("priced far below market for its age: possible scam or hidden damage")
    branded = [lab for rx, lab in BRANDED if rx.search(blob)]
    if l.make == "honda" and l.model_key in ("civic", "accord", "cr-v") and l.year in (2016, 2017, 2018) \
            and re.search(r"1\.5|turbo|\bex\b|touring|sport", blob.lower()):
        l.notes.append("1.5T oil-dilution reports on some 2016-18 cars: check oil level/smell")
    mml = min_left_of(cfg)
    if branded:
        l.flags = branded + l.flags
        l.status = "branded title"
        return
    covered_by_any = any_cap(cfg) is not None and l.make not in cfg["price_caps"]
    if (l.model_key is None or l.life_low is None) and covered_by_any and l.make in MAKE_AVG:
        # `any` search, model not individually rated: conservative make average, clearly labeled
        l.model_key, l.life_low = MAKE_AVG_LABEL, MAKE_AVG[l.make]
        l.notes.append(f"{MAKE_AVG_LABEL} (model not individually rated; {l.make.title()} average)")
    if l.model_key is None or l.life_low is None:
        l.status = "unrated model"
        if covered_by_any:
            # `any` = all makes: never drop a car just because we have no lifespan data for it
            mark_unrated(l)
            return
        if mml is None:  # no longevity bar: keep it, but flag as low-info
            l.status = "pass"
            l.notes.append("unrated model: no lifespan data, est. miles left unknown (low info)")
        return
    if l.miles is None or not l.year:
        l.status = "odometer/year not in listing"
        if mml is None:
            l.status = "pass"
            l.notes.append("odometer/year not in listing: est. miles left unknown (low info)")
        return
    ded: list[tuple[str, int]] = []
    m = blob.lower()
    age = as_of - l.year
    if l.make == "honda" and l.model_key in ("fit", "civic", "accord", "hr-v") and 2014 <= l.year <= 2016 \
            and not re.search(r"v-?6", m):
        ded.append(("Honda 2014-16 CVT", D_HONDA_CVT))
    if "hybrid" in m or l.model_key in ("prius", "insight", "ct"):
        if age >= 12:
            ded.append((f"hybrid pack ~{int(age)} yrs old", D_HYBRID_12Y))
        elif age >= 8:
            ded.append((f"hybrid pack ~{int(age)} yrs old", D_HYBRID_8Y))
    if l.make == "tesla":
        yl, cap = tesla_warranty(l.model_key, m, l.year, as_of)
        ml = None if cap is None else cap - l.miles
        if yl <= 0 or (ml is not None and ml <= 0):
            ded.append(("Tesla pack warranty expired (~$12-16k pack)", D_TESLA_WARRANTY_OUT))
        elif yl < 2 or (ml is not None and ml < 25_000):
            left = f"{max(yl, 0):.1f} yr" + ("" if ml is None else f" / {ml:,} mi")
            ded.append((f"Tesla pack warranty nearly up ({left} left)", D_TESLA_WARRANTY_NEAR))
        else:
            l.notes.append(f"Tesla pack warranty left: {yl:.1f} yr" + ("" if ml is None else f" / {ml:,} mi"))
        if l.model_key in ("model s", "model x") and 2014 <= l.year <= 2016:
            ded.append(("2014-16 Model S/X drive unit / MCU", D_TESLA_EARLY_SX))
    for makes, models, y0, y1, need, veto, label, d in WEAK_POINTS:
        if l.make in makes and (models is None or l.model_key in models) and y0 <= l.year <= y1 \
                and (need is None or re.search(need, m)) and (veto is None or not re.search(veto, m)):
            ded.append((label, d))
    if any_cap(cfg) is not None and age >= 8 and l.miles < 2_000 * age:
        # seller-entered placeholders ("1 mile", "1,000"), rolled-over or km odometers inflate miles left
        l.odo_suspect = True
        l.flags.append(f"odometer looks implausibly low for a {int(age)}-yr-old car (placeholder, rollover or km?): verify")
    raw = l.life_low - l.miles - sum(d for _, d in ded)
    l.deductions = ded
    l.est_left = int(raw // 1000 * 1000)
    l.status = "pass" if mml is None or raw >= mml else f"< {mml:,} est. miles left"
    if mml is None and raw <= 0:
        l.notes.append("already past the low end of typical lifespan")


# --------------------------------------------------------------------------- geo

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "used-car-scout"
GAZ_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_zcta_national.zip"
_ZIPS: dict[str, tuple[float, float]] | None = None


def zip_centroid(z: str, client: httpx.Client | None = None) -> tuple[float, float] | None:
    """ZIP centroid from the Census 2020 ZCTA gazetteer (downloaded once, cached)."""
    global _ZIPS
    z = str(z or "").strip()[:5]
    if not re.fullmatch(r"\d{5}", z):
        return None
    if _ZIPS is None:
        _ZIPS = {}
        cache = CACHE / "zcta_centroids.json"
        try:
            if cache.exists():
                _ZIPS = {k: tuple(v) for k, v in json.loads(cache.read_text()).items()}
            else:
                print("Downloading Census ZIP centroids (one time, ~1 MB)…", flush=True)
                r = httpx.get(GAZ_URL, timeout=60, follow_redirects=True)
                r.raise_for_status()
                zf = zipfile.ZipFile(io.BytesIO(r.content))
                txt = zf.read(zf.namelist()[0]).decode("utf-8", "ignore")
                for ln in txt.splitlines():
                    p = [x.strip() for x in ln.split("\t")]
                    if p and p[0].isdigit() and len(p) >= 7:
                        _ZIPS[p[0]] = (float(p[5]), float(p[6]))
                CACHE.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(_ZIPS))
        except Exception as exc:  # noqa: BLE001
            print(f"  ZIP centroid download failed ({exc}); ZIP-only listings can't be placed.", flush=True)
    return _ZIPS.get(z)


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 3958.8
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    return 2 * r * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def locate(l: Listing, home: tuple[float, float]) -> None:
    cands: list[tuple[float, str]] = []
    if l.lat is not None and l.lon is not None:
        cands.append((haversine(home, (l.lat, l.lon)), "listing coordinates"))
    zc = zip_centroid(l.zip) if l.zip else None
    if zc:
        cands.append((haversine(home, zc), f"ZIP {l.zip} centroid"))
    if not cands:
        l.dist, l.dist_basis = None, "no location in listing"
        return
    d, basis = max(cands)  # conservative: farther of the two
    if len(cands) == 2 and abs(cands[0][0] - cands[1][0]) > 5:
        basis += f" (coords {cands[0][0]:.1f} mi vs ZIP {cands[1][0]:.1f} mi; used farther)"
    l.dist, l.dist_basis = round(d, 1), basis


# --------------------------------------------------------------------------- parsing helpers

K_MILES = re.compile(r"\b(\d{2,3})\s*k\s*(?:mi|miles|mile)?\b", re.I)
MILES = re.compile(r"(?:odometer|mileage)[^\d]{0,12}(\d{1,3}(?:,\d{3})+|\d{3,6})\b|(\d{1,3}(?:,\d{3})+|\d{4,6})\s*(?:mi|miles)\b", re.I)
PRICE = re.compile(r"\$\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{3,6})")
YEAR = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
_APOS = "'\u2018\u2019`"
YY_LEAD = re.compile(rf"(?<![\w{_APOS}])[{_APOS}](\d\d)(?![\d{_APOS}\"])")      # '82, ‘82, ’07
YY_TRAIL = re.compile(rf"^\W*?(\d\d)\s?[{_APOS}](?![\d{_APOS}\"])")             # 07 ' Nissan..., 07' Civic
VIN = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")


def to_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip()
    s = s.split(".", 1)[0] if re.fullmatch(r"-?[\d,]+\.\d+", s) else s
    d = re.sub(r"[^\d]", "", s)
    return int(d) if d else None


def parse_miles(text: str) -> int | None:
    if not text:
        return None
    k = K_MILES.search(text)
    if k and 10 <= int(k.group(1)) <= 400:
        return int(k.group(1)) * 1000
    m = MILES.search(text)
    if not m:
        return None
    v = to_int(m.group(1) or m.group(2))
    if v is None or 1990 <= v <= 2035 or v > 500_000:
        return None
    return v


def parse_year(text: str) -> int | None:
    m = YEAR.search(text or "")
    if m:
        return int(m.group(1))
    m = YY_LEAD.search(text or "") or YY_TRAIL.search(text or "")
    if not m:
        return None
    yy = int(m.group(1))
    y = 2000 + yy if yy <= (dt.date.today().year + 1) % 100 else 1900 + yy
    return y if y >= 1950 else None


def parse_price(text: str) -> int | None:
    m = PRICE.search(text or "")
    return to_int(m.group(1)) if m else None


def model_from_title(title: str, make: str) -> str:
    t = (title or "").lower()
    if make and make in t:
        t = t.split(make, 1)[1]
    t = YEAR.sub("", t)
    return re.sub(r"\s+", " ", t).strip(" -/,.")


# --------------------------------------------------------------------------- http

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


class Polite:
    def __init__(self, delay: float):
        self.delay = delay
        self._last = 0.0
        self.c = httpx.Client(headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                                       "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"},
                              timeout=httpx.Timeout(20.0, connect=10.0), follow_redirects=True)

    def get(self, url: str, **kw: Any) -> httpx.Response:
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        return self.c.get(url, **kw)


def blocked(resp: httpx.Response) -> str | None:
    # test visible text only: pages that merely load a reCAPTCHA <script> are not blocks
    blob = BeautifulSoup(re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", resp.text), "html.parser").get_text(" ")[:3000].lower()
    if resp.status_code in (401, 403, 429) or "your request has been blocked" in blob or "captcha" in blob:
        return f"HTTP {resp.status_code} (site blocked automated access)"
    if resp.status_code >= 400:
        return f"HTTP {resp.status_code}"
    return None


# --------------------------------------------------------------------------- sources

def cl_base(cfg: dict, http: Polite) -> str:
    """Resolve the Craigslist city search page for the ZIP (Craigslist redirects www -> nearest city)."""
    url = (cfg["craigslist"].get("search_url") or "").strip()
    if url:
        return url.split("?", 1)[0]
    r = http.get("https://www.craigslist.org/search/cta?" + urlencode({"postal": cfg["zip"]}))
    final = str(r.url).split("?", 1)[0]
    # 2026 layout: www and <city>.craigslist.org searches both land on
    # https://www.craigslist.org/search/city/<city-st>?cat=...  That page serves any category via
    # the cat= parameter (we always send cat=cta), so it is a valid base as-is.
    m = re.match(r"https?://www\.craigslist\.org/search/city/[^/?#]+", final)
    if m:
        return m.group(0)
    m = re.match(r"https?://([a-z0-9-]+)\.craigslist\.org", final)
    if m and m.group(1) != "www":
        return f"https://{m.group(1)}.craigslist.org/search/cta"
    return final

