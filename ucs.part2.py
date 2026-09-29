# Known weak points (well-documented recalls / TSBs / class actions / owner reports), applied to rated
# models by year range: (makes, models or None = any model of those makes, first year, last year,
# text that must appear or None, text that rules it out or None, label, est. miles deducted).
_MANUAL = r"\bmanual\b|\bstick\b|\b[56]-?speed\b|\b[56]mt\b"
WEAK_POINTS: list[tuple[tuple[str, ...], tuple[str, ...] | None, int, int, str | None, str | None, str, int]] = [
    (("nissan",), ("altima", "sentra", "versa", "rogue", "pathfinder", "murano", "juke", "quest"), 2013, 2018,
     None, _MANUAL, "Nissan 2013-18 CVT (Jatco) failures", 30_000),
    (("infiniti",), ("qx60", "jx35"), 2013, 2018, None, None, "Infiniti QX60/JX35 2013-18 CVT", 30_000),
    (("ford",), ("focus",), 2012, 2016, None, _MANUAL + r"|\belectric\b|\bst\b", "Ford PowerShift DPS6 dual-clutch (2012-16 Focus)", 40_000),
    (("ford",), ("fiesta",), 2011, 2016, None, _MANUAL + r"|\bst\b", "Ford PowerShift DPS6 dual-clutch (2011-16 Fiesta)", 40_000),
    (("ford",), ("f-150", "f-250", "f-350"), 2004, 2010, r"5\.4|triton", None, "Ford 5.4 3V cam phasers / timing (2004-10)", 25_000),
    (("ford",), ("expedition",), 2005, 2010, None, None, "Ford 5.4 3V cam phasers / timing (2005-10 Expedition)", 25_000),
    (("lincoln",), ("navigator",), 2005, 2010, None, None, "Ford 5.4 3V cam phasers / timing (2005-10 Navigator)", 25_000),
    (("ford",), ("f-250", "f-350", "econoline"), 2003, 2010, r"6\.0|6\.4|power ?stroke|diesel", None,
     "Ford 6.0 / 6.4 Power Stroke diesel (2003-10) head gasket / EGR / injector trouble", 40_000),
    (("hyundai",), ("sonata", "santa fe", "tucson"), 2011, 2019, None, r"\bv6\b|3\.3|3\.5|hybrid|1\.6|diesel",
     "Hyundai/Kia Theta II 2.0T/2.4 engine (2011-19) bearing failure / oil use", 30_000),
    (("kia",), ("optima", "sorento", "sportage"), 2011, 2019, None, r"\bv6\b|3\.3|3\.5|hybrid|1\.6|diesel",
     "Hyundai/Kia Theta II 2.0T/2.4 engine (2011-19) bearing failure / oil use", 30_000),
    (("chevrolet",), ("silverado", "tahoe", "suburban", "avalanche"), 2007, 2021, None,
     r"\b[23]500\b|\bhd\b|diesel|duramax|4\.3|2\.7|4\.8", "GM AFM/DFM V8 lifter failures (2007-21)", 20_000),
    (("gmc",), ("sierra", "yukon"), 2007, 2021, None, r"\b[23]500\b|\bhd\b|diesel|duramax|4\.3|2\.7|4\.8",
     "GM AFM/DFM V8 lifter failures (2007-21)", 20_000),
    (("cadillac",), ("escalade",), 2007, 2021, None, None, "GM AFM/DFM V8 lifter failures (2007-21)", 20_000),
    (("chevrolet",), ("equinox",), 2010, 2017, None, r"\bv6\b|3\.0|3\.6|1\.5|diesel", "GM 2.4 Ecotec oil consumption (2010-17 Equinox)", 30_000),
    (("gmc",), ("terrain",), 2010, 2017, None, r"\bv6\b|3\.0|3\.6|1\.5|diesel", "GM 2.4 Ecotec oil consumption (2010-17 Terrain)", 30_000),
    (("chevrolet",), ("malibu",), 2010, 2013, None, r"\bv6\b|3\.6|\bltz\b", "GM 2.4 Ecotec oil consumption (2010-13 Malibu)", 30_000),
    (("chevrolet",), ("cruze",), 2011, 2016, None, r"diesel|2\.0", "Chevy Cruze 1.4T PCV / coolant leaks (2011-16)", 20_000),
    (("chevrolet",), ("traverse",), 2009, 2012, None, None, "GM 3.6 V6 timing chain stretch (2009-12)", 20_000),
    (("gmc",), ("acadia",), 2007, 2012, None, None, "GM 3.6 V6 timing chain stretch (2007-12)", 20_000),
    (("buick",), ("enclave",), 2008, 2012, None, None, "GM 3.6 V6 timing chain stretch (2008-12)", 20_000),
    (("cadillac",), ("deville", "dts", "sts"), 2000, 2011, None, None, "Cadillac Northstar V8 head gaskets (to 2011)", 30_000),
    (("subaru",), ("outback", "forester", "legacy", "impreza", "baja"), 1999, 2011, None, r"3\.0|3\.6|\bh6\b|\bwrx\b|\bsti\b",
     "Subaru EJ25 2.5 head gaskets (before 2012)", 25_000),
    (("bmw",), None, 2012, 2015, r"28i|20i|\bn20\b", None, "BMW N20 2.0T timing chain guides (2012-15)", 30_000),
    (("volkswagen",), ("gti", "cc", "tiguan", "eos"), 2008, 2012, None, r"\bv6\b|3\.6|vr6",
     "VW/Audi 2.0T (EA888 gen 1) oil consumption (2008-12)", 30_000),
    (("volkswagen",), ("jetta", "passat"), 2008, 2012, r"2\.0 ?t|\bgli\b|turbo|\btsi\b", r"tdi|diesel",
     "VW/Audi 2.0T (EA888 gen 1) oil consumption (2008-12)", 30_000),
    (("audi",), ("a4", "a5", "q5", "tt", "a3"), 2008, 2012, None, r"\bv6\b|3\.2|3\.0|tdi|diesel",
     "VW/Audi 2.0T (EA888 gen 1) oil consumption (2008-12)", 30_000),
    (("jeep",), ("cherokee", "renegade", "compass"), 2014, 2017, None, _MANUAL, "ZF 9-speed automatic shifting/failure (2014-17)", 20_000),
    (("chrysler",), ("200",), 2015, 2017, None, None, "ZF 9-speed automatic shifting/failure (2015-17)", 20_000),
    (("honda",), ("odyssey", "pilot"), 2008, 2013, None, None, "Honda V6 VCM oil consumption / misfires (2008-13)", 20_000),
    (("honda",), ("accord",), 2008, 2013, r"\bv6\b|3\.5|\bex-?l v6\b", None, "Honda V6 VCM oil consumption / misfires (2008-13)", 20_000),
    (("porsche",), ("boxster", "911", "cayman"), 1997, 2008, None, None, "Porsche M96/M97 IMS bearing (1997-2008)", 30_000),
    (("mini",), ("cooper", "countryman", "clubman"), 2007, 2012, None, None, "Mini 1.6 'Prince' engine timing chain / oil use (2007-12)", 20_000),
]
# Mazda: no major model-wide engine/transmission weak point in these years (CX-7 turbo reflected in its lower lifespan).

D_HONDA_CVT = 30_000           # 2014-2016 Fit / Civic / Accord (4-cyl) / HR-V CVT
D_HYBRID_8Y = 20_000           # hybrid pack 8-11 years old
D_HYBRID_12Y = 40_000          # hybrid pack 12+ years old
D_TESLA_WARRANTY_OUT = 40_000  # pack warranty over: ~$12-16k pack uncovered
D_TESLA_WARRANTY_NEAR = 20_000 # < 2 yrs or < 25k mi of pack warranty left
D_TESLA_EARLY_SX = 40_000      # 2014-2016 Model S/X drive unit / MCU issues

BRANDED = [(re.compile(r"\bsalvage\b", re.I), "salvage title mentioned"),
           (re.compile(r"\brebuilt\b|\breconstructed\b", re.I), "rebuilt title mentioned"),
           (re.compile(r"\bflood", re.I), "flood mentioned"),
           (re.compile(r"\bbranded title\b", re.I), "branded title")]
CAUTION = [(re.compile(r"\btrue miles unknown\b|\btmu\b|\bnot actual miles\b", re.I), "true miles unknown"),
           (re.compile(r"needs?\s+(an?\s+)?(engine|transmission)", re.I), "needs engine/transmission"),
           (re.compile(r"mechanic'?s?\s+special|not running|does not run|won'?t start", re.I), "not running / mechanic's special"),
           (re.compile(r"\bas[- ]is\b", re.I), "sold as-is"),
           (re.compile(r"\bcash only\b|\bwire\b|\bshipping\b|\bescrow\b|\bgift card", re.I), "possible scam language")]
DENY = re.compile(r"\b(fire ?truck|ambulance|dump truck|box truck|flatbed|tow truck|wrecker|bucket truck|"
                  r"school bus|shuttle bus|motorhome|motor home|\bRV\b|forklift|limo(?:usine)?|"
                  r"food truck|parts only|parting out|for parts|"
                  # special-purpose bodies
                  r"hearse|funeral|stretch limo|party bus|church bus|coach bus|motor ?coach|coachmen|"
                  r"wheelchair (?:van|bus)|paratransit|ice cream truck|"
                  # not cars: powersports, trailers, boats
                  r"can-?am|ryker|polaris|slingshot|motorcycle|dirt ?bike|atv|utv|side[- ]by[- ]side|"
                  r"golf cart|scooter|moped|jet ?ski|pontoon|"
                  r"(?:utility|cargo|enclosed|car|boat|camper|travel|dump|equipment) trailer|"
                  # heavy / commercial trucks
                  r"freightliner|peterbilt|kenworth|mack truck|hino|isuzu npr|"
                  r"international (?:4[0-9]00|7[0-9]00|durastar|prostar|lonestar|workstar|terrastar)|"
                  r"logging truck|log truck|semi[- ]truck|semi tractor|day cab|sleeper cab|cdl|"
                  # engine / transmission only
                  r"engine only|motor only|transmission only|long block|short block|crate engine|"
                  r"(?:engine|motor|transmission) for sale)\b", re.I)
# Standalone engine listings ("396 with 4 speed", "350 engine"): an old engine size at the start, no model year
ENGINE_ONLY = re.compile(r"^\W*(?:283|302|305|318|327|340|350|351|360|383|390|396|400|402|425|427|428|429|440|454|455|460|"
                         r"ls[1-9]|lsx|hemi)\b(?!.*\b(?:19[5-9]\d|20[0-3]\d)\b)", re.I)


def not_a_car(title: str) -> bool:
    """Special-purpose vehicles, non-cars and engine-only listings (excluded at the source)."""
    if DENY.search(title or ""):
        return True
    return bool(ENGINE_ONLY.search(title or "")) and not find_make(title) and not infer_make(title)


def norm_make(s: str) -> str:
    s = (s or "").strip().lower()
    return MAKE_ALIASES.get(s, s)


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

