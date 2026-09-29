
# Typical lifespan with good maintenance (low end, miles). Conservative on purpose: round numbers at
# the LOW end of what owners commonly reach, not averages or maximums. Informed by general public
# reliability knowledge: Consumer Reports reliability surveys, iSeeCars "longest-lasting vehicles"
# studies (share of each model reaching 200k/250k miles), RepairPal reliability ratings, and widely
# reported recalls / TSBs / class actions for the weak points below. These are screening estimates,
# not measured stats; add or correct any model with `lifespan_overrides`.
LIFESPAN: dict[str, dict[str, int]] = {
    "toyota": {"corolla": 250_000, "camry": 250_000, "avalon": 250_000, "prius": 250_000,
               "rav4": 250_000, "highlander": 250_000, "4runner": 250_000, "tacoma": 250_000,
               "tundra": 250_000, "sequoia": 250_000, "sienna": 220_000, "venza": 220_000,
               "land cruiser": 250_000, "fj cruiser": 250_000, "matrix": 220_000, "yaris": 200_000,
               "corolla cross": 220_000, "c-hr": 200_000, "echo": 200_000, "solara": 220_000},
    "lexus": {"es": 250_000, "rx": 250_000, "gx": 250_000, "lx": 250_000, "ls": 250_000,
              "is": 220_000, "ct": 220_000, "gs": 220_000, "nx": 220_000, "ux": 200_000},
    "honda": {"civic": 220_000, "accord": 220_000, "cr-v": 220_000, "element": 220_000,
              "odyssey": 200_000, "pilot": 200_000, "ridgeline": 200_000, "passport": 200_000,
              "crosstour": 200_000, "s2000": 200_000,
              "fit": 180_000, "insight": 180_000, "hr-v": 180_000},
    "acura": {"tsx": 220_000, "tlx": 200_000, "rdx": 200_000, "mdx": 200_000, "tl": 200_000,
              "ilx": 200_000, "rsx": 200_000, "rl": 180_000},
    "mazda": {"mazda3": 200_000, "mazda6": 200_000, "cx-5": 200_000, "cx-3": 180_000,
              "cx-30": 200_000, "cx-50": 200_000, "cx-9": 180_000, "mx-5": 200_000,
              "mazda5": 180_000, "tribute": 180_000, "cx-7": 150_000},
    "tesla": {"model 3": 250_000, "model y": 250_000, "model s": 200_000, "model x": 200_000},
    "scion": {"xb": 200_000, "xd": 200_000, "xa": 200_000, "tc": 200_000, "im": 200_000,
              "ia": 180_000, "fr-s": 180_000},
    "subaru": {"outback": 200_000, "forester": 200_000, "legacy": 200_000, "crosstrek": 200_000,
               "impreza": 180_000, "ascent": 180_000, "baja": 180_000, "brz": 180_000, "wrx": 150_000},
    "nissan": {"frontier": 200_000, "xterra": 200_000, "titan": 200_000, "armada": 180_000,
               "pathfinder": 180_000, "altima": 180_000, "maxima": 180_000, "350z": 180_000,
               "370z": 180_000, "murano": 160_000, "rogue": 160_000, "sentra": 160_000,
               "quest": 160_000, "kicks": 160_000, "versa": 150_000, "juke": 150_000, "leaf": 150_000},
    "infiniti": {"g35": 180_000, "g37": 180_000, "q50": 180_000, "q60": 180_000, "qx80": 180_000,
                 "qx56": 180_000, "fx35": 180_000, "ex35": 180_000, "m35": 180_000, "m37": 180_000,
                 "qx60": 160_000, "jx35": 160_000, "qx50": 160_000},
    "hyundai": {"elantra": 180_000, "sonata": 180_000, "santa fe": 180_000, "tucson": 180_000,
                "kona": 180_000, "palisade": 180_000, "genesis": 180_000, "azera": 180_000,
                "ioniq": 180_000, "santa cruz": 180_000, "accent": 160_000, "veloster": 160_000},
    "kia": {"optima": 180_000, "k5": 180_000, "sorento": 180_000, "sportage": 180_000, "forte": 180_000,
            "telluride": 180_000, "niro": 180_000, "stinger": 180_000, "seltos": 180_000,
            "cadenza": 180_000, "soul": 170_000, "sedona": 170_000, "carnival": 170_000, "rio": 160_000},
    "genesis": {"g70": 180_000, "g80": 180_000, "g90": 180_000, "gv70": 180_000, "gv80": 180_000},
    "mitsubishi": {"outlander": 180_000, "lancer": 180_000, "mirage": 160_000, "eclipse cross": 160_000,
                   "galant": 160_000, "endeavor": 160_000},
    "ford": {"f-150": 200_000, "f-250": 250_000, "f-350": 250_000, "crown victoria": 250_000,
             "econoline": 250_000, "ranger": 200_000, "expedition": 200_000, "transit": 200_000,
             "explorer": 180_000, "edge": 180_000, "fusion": 180_000, "mustang": 180_000,
             "taurus": 180_000, "flex": 180_000, "bronco": 180_000, "maverick": 180_000,
             "escape": 170_000, "bronco sport": 170_000, "focus": 150_000, "fiesta": 150_000},
    "chevrolet": {"silverado": 200_000, "tahoe": 200_000, "suburban": 200_000, "avalanche": 200_000,
                  "express": 250_000, "colorado": 180_000, "impala": 180_000, "camaro": 180_000,
                  "corvette": 180_000, "volt": 180_000, "malibu": 170_000, "traverse": 170_000,
                  "blazer": 170_000, "trailblazer": 170_000, "equinox": 160_000, "trax": 160_000,
                  "cruze": 150_000, "sonic": 150_000, "spark": 150_000, "bolt": 150_000,
                  "cobalt": 150_000, "hhr": 150_000},
    "gmc": {"sierra": 200_000, "yukon": 200_000, "savana": 250_000, "canyon": 180_000,
            "envoy": 170_000, "acadia": 170_000, "terrain": 160_000},
    "ram": {"1500": 200_000, "2500": 250_000, "3500": 250_000, "promaster": 180_000},
    "dodge": {"dakota": 180_000, "charger": 180_000, "challenger": 180_000, "durango": 180_000,
              "caravan": 170_000, "journey": 150_000, "dart": 150_000, "avenger": 150_000,
              "caliber": 150_000, "nitro": 150_000},
    "jeep": {"wrangler": 200_000, "grand cherokee": 180_000, "gladiator": 180_000, "wagoneer": 180_000,
             "cherokee": 160_000, "liberty": 160_000, "commander": 160_000, "compass": 150_000,
             "patriot": 150_000, "renegade": 150_000},
    "chrysler": {"300": 180_000, "town & country": 170_000, "pacifica": 160_000, "200": 150_000,
                 "sebring": 150_000, "pt cruiser": 150_000},
    "buick": {"century": 200_000, "lesabre": 200_000, "park avenue": 200_000, "lacrosse": 180_000,
              "lucerne": 180_000, "enclave": 170_000, "regal": 170_000, "rendezvous": 170_000,
              "encore": 160_000, "envision": 160_000, "verano": 160_000},
    "cadillac": {"escalade": 200_000, "xt5": 170_000, "xts": 170_000, "dts": 170_000, "deville": 170_000,
                 "ct6": 170_000, "ct5": 170_000, "ct4": 160_000, "cts": 160_000, "ats": 160_000,
                 "xt4": 160_000, "sts": 160_000, "srx": 150_000},
    "lincoln": {"town car": 250_000, "navigator": 200_000, "mkz": 180_000, "mkx": 180_000,
                "mkt": 180_000, "continental": 180_000, "aviator": 180_000, "nautilus": 180_000,
                "mkc": 170_000, "corsair": 170_000},
    "mercury": {"grand marquis": 250_000, "milan": 180_000, "sable": 180_000, "mountaineer": 180_000,
                "mariner": 170_000},
    "pontiac": {"vibe": 220_000, "grand prix": 170_000, "g6": 150_000},
    "volkswagen": {"jetta": 170_000, "passat": 170_000, "golf": 170_000, "touareg": 170_000,
                   "gti": 160_000, "tiguan": 160_000, "atlas": 160_000, "beetle": 160_000,
                   "cc": 150_000, "eos": 150_000},
    "audi": {"a4": 160_000, "a6": 160_000, "q5": 160_000, "a3": 150_000, "a5": 150_000, "q7": 150_000,
             "q3": 150_000, "tt": 150_000, "allroad": 150_000, "a8": 150_000},
    # BMW / Mercedes model numbers (328i, C300, ML350...) are folded into series/class names in model_key()
    "bmw": {"3 series": 150_000, "5 series": 150_000, "x3": 150_000, "x5": 150_000, "4 series": 150_000,
            "2 series": 150_000, "7 series": 140_000, "x1": 140_000, "x6": 140_000, "z4": 150_000},
    "mercedes": {"e-class": 170_000, "sprinter": 200_000, "glc": 160_000, "c-class": 150_000,
                 "s-class": 150_000, "glk": 150_000, "ml": 150_000, "gle": 150_000, "gl": 150_000,
                 "gls": 150_000, "slk": 150_000, "cla": 140_000, "gla": 140_000},
    "volvo": {"xc90": 180_000, "xc70": 180_000, "xc60": 180_000, "s60": 180_000, "v70": 180_000,
              "s80": 180_000, "s90": 170_000, "xc40": 170_000, "s40": 170_000, "v60": 170_000},
    "mini": {"cooper": 140_000, "countryman": 130_000, "clubman": 130_000},
    "porsche": {"911": 200_000, "boxster": 170_000, "cayman": 170_000, "macan": 170_000,
                "cayenne": 160_000, "panamera": 160_000},
    "land rover": {"defender": 150_000, "range rover sport": 130_000, "range rover": 130_000,
                   "discovery sport": 130_000, "discovery": 130_000, "lr4": 130_000, "lr3": 130_000,
                   "evoque": 130_000, "velar": 130_000},
    "jaguar": {"xf": 150_000, "xj": 150_000, "xk": 150_000, "f-pace": 150_000, "f-type": 150_000,
               "e-pace": 140_000, "x-type": 140_000, "s-type": 140_000},
}
# Make-level fallback (conservative make average) for models not listed above. Used only for makes
# covered by the `any` cap, and labeled "make-average estimate" in reports. Makes absent from both
# tables are "no lifespan data".
MAKE_AVG: dict[str, int] = {
    "toyota": 220_000, "lexus": 220_000, "honda": 200_000, "acura": 200_000, "mazda": 180_000,
    "tesla": 200_000, "scion": 200_000, "subaru": 180_000, "nissan": 160_000, "infiniti": 170_000,
    "hyundai": 170_000, "kia": 170_000, "genesis": 180_000, "mitsubishi": 160_000, "ford": 180_000,
    "chevrolet": 170_000, "gmc": 180_000, "ram": 200_000, "dodge": 160_000, "jeep": 170_000,
    "chrysler": 160_000, "buick": 170_000, "cadillac": 160_000, "lincoln": 180_000,
    "mercury": 180_000, "pontiac": 160_000, "saturn": 150_000, "volkswagen": 160_000, "audi": 150_000,
    "bmw": 150_000, "mercedes": 150_000, "volvo": 170_000, "mini": 130_000, "porsche": 160_000,
    "land rover": 130_000, "jaguar": 140_000,
}
MAKE_AVG_LABEL = "make-average estimate"
ALIASES = {"crv": "cr-v", "hrv": "hr-v", "rav 4": "rav4", "4 runner": "4runner",
           "cx5": "cx-5", "cx3": "cx-3", "mazda 3": "mazda3", "mazda 6": "mazda6",
           "model3": "model 3", "modely": "model y", "models": "model s", "modelx": "model x",
           "cx9": "cx-9", "cx30": "cx-30", "cx50": "cx-50", "cx7": "cx-7", "mazda 5": "mazda5",
           "mx5": "mx-5", "miata": "mx-5", "chr": "c-hr", "frs": "fr-s", "f150": "f-150", "f 150": "f-150",
           "f250": "f-250", "f 250": "f-250", "f350": "f-350", "f 350": "f-350", "crown vic": "crown victoria",
           "town and country": "town & country", "t&c": "town & country", "pt-cruiser": "pt cruiser",
           "fpace": "f-pace", "ftype": "f-type", "xtype": "x-type", "stype": "s-type", "rangerover": "range rover",
           "pro master": "promaster", "towncar": "town car"}
MAKE_ALIASES = {"chevy": "chevrolet", "vw": "volkswagen", "mercedes-benz": "mercedes", "range rover": "land rover",
                "nisann": "nissan", "nissian": "nissan", "toyta": "toyota", "hundai": "hyundai", "hyndai": "hyundai",
                "volkswagon": "volkswagen", "mercedez": "mercedes", "chevorlet": "chevrolet", "cheverolet": "chevrolet"}
KNOWN_MAKES = ["toyota", "lexus", "honda", "acura", "mazda", "tesla", "subaru", "nissan", "hyundai",
               "kia", "ford", "chevrolet", "chevy", "gmc", "volkswagen", "vw", "bmw", "mercedes-benz",
               "mercedes", "audi", "jeep", "ram", "dodge", "chrysler", "buick", "cadillac", "volvo",
               "mitsubishi", "infiniti", "lincoln", "mini", "porsche", "genesis", "scion",
               "land rover", "range rover", "jaguar", "alfa romeo", "fiat", "pontiac", "saturn", "mercury",
               "oldsmobile", "plymouth", "hummer", "saab", "suzuki", "isuzu", "smart", "polestar", "rivian",
               "nisann", "nissian", "toyta", "hundai", "hyndai", "volkswagon", "mercedez", "chevorlet", "cheverolet"]

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
                  r"school bus|shuttle bus|motorhome|motor home|\bRV\b|camper ?van|forklift|limo(?:usine)?|"
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

