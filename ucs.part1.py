#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx>=0.27",
#     "beautifulsoup4>=4.12",
#     "pyyaml>=6.0",
# ]
# ///
"""Used car scout: find used cars near a ZIP that should plausibly last another 100k+ miles.

Sources
  * Craigslist (no key; best-effort HTML scrape of public search pages)
  * Auto.dev dealer listings (optional; set AUTO_DEV_API_KEY, skipped with a notice if missing)
  * Public/municipal auction pages (optional; off unless you list URLs in the config)

Hard filters (all configurable)
  1. Radius (optional, default 50 mi): straight-line miles from your ZIP, measured from each
     listing's own lat/long and/or ZIP (the farther of the two if both exist). No usable
     location = excluded. Set blank/0 = no distance cutoff (distance is still shown).
  2. Price: per-make price caps, or `any: <price>` for one cap on EVERY make (all makes, rated or not).
  3. Longevity (optional): est. miles left = low end of typical model lifespan (conservative
     estimates for most US-market makes; with `any`, unlisted models of a known make use a labeled
     "make-average estimate") - odometer - known weak-point deductions by year range (Honda 2014-16
     CVT, hybrid pack age, Tesla pack warranty, early S/X, Nissan CVTs, Ford DPS6 / 5.4 3V,
     Hyundai/Kia Theta II, GM AFM / 2.4, Subaru EJ25, BMW N20, VW/Audi 2.0T, ZF 9-speed, ...).
     Must be >= min_miles_left (default 50,000). With `any`, makes we have no lifespan data
     for at all are KEPT (never cut by min_miles_left), labeled "no lifespan data — est. miles left unknown",
     given low-info (low) confidence and sorted below every rated car that passes. With explicit
     per-make caps only, unrated models / no odometer are excluded when a cutoff is set.
     Set blank/0 = no longevity cutoff: those cars are kept and marked low-info.
  4. Branded titles (salvage / rebuilt / flood) mentioned in the listing = excluded.

Ranking: confidence is a TIER, not a penalty. high (history report, 0 accidents) ->
medium (history report, 1+ accidents) -> low (no history: private sale, auction, dealer
without history data). Low-confidence cars only fill pick slots nobody better can fill,
and are labeled. Within a tier, cars are ordered by a value score (price low, miles low,
est. miles left high).

This is a screen, not a buy signal. Get a pre-purchase inspection. The script only reads
public listings; it never contacts sellers.

Usage
  uv run ucs.py --init-config my-scout.yaml      # write a starter config, then edit it
  uv run ucs.py --config my-scout.yaml
  uv run ucs.py --zip 12345 --radius 30 --cap toyota=15000 --cap honda=15000 --out ./reports --csv
  uv run ucs.py --zip 12345 --cap any=15000 --out ./reports     # all makes, 50 mi, 50k+ left (unrated labeled)
  uv run ucs.py --zip 12345 --cap any=15000 --radius 0 --min-miles-left 0 --out ./reports  # no cutoffs
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import io
import json
import math
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

# --------------------------------------------------------------------------- config

DEFAULTS: dict[str, Any] = {
    "zip": "",                 # REQUIRED: 5-digit US ZIP to search around
    "lat": None,               # optional: override the ZIP's center point
    "lon": None,
    "radius_miles": 50,        # optional hard radius, straight-line miles (default 50); None/0 = any distance
    "price_caps": {},          # REQUIRED: {make: max_price}, e.g. {"toyota": 15000}, or {"any": 15000} for ALL makes
    "models": [],              # optional: only these models (e.g. ["camry", "corolla", "civic"]); empty = any model
    "min_price": 0,            # skip listings priced below this (junk / parts cars)
    "year_min": None,
    "year_max": None,
    "min_miles_left": 50_000,  # optional longevity cutoff (default 50,000); None/0 = no cutoff
    "top_n": 8,                # number of picks at the top of the report
    "output_dir": "",          # REQUIRED: where reports go (dated HTML + latest.html [+ CSV])
    "csv": False,
    "md": True,                # also write a Markdown report (dated .md + latest.md)
    "craigslist": {
        "enabled": True,
        "search_url": "",      # optional: a Craigslist city search page, e.g. https://www.craigslist.org/search/city/<city-st>
        "purveyor": "owner",   # owner | dealer | all
        "clean_title_only": True,
        "detail_pages": 30,    # open up to N listing pages to read odometer + map pin (polite, ~1.5 s each)
    },
    "autodev": {
        "enabled": True,       # still skipped if AUTO_DEV_API_KEY is not set
        "pages_per_make": 3,   # 20 listings per page
    },
    "auctions": {
        "enabled": False,      # off by default
        "urls": [],            # list of {url: ..., zip: "5-digit ZIP of the lot", label: "..."}
    },
    "lifespan_overrides": {},  # {"toyota yaris": 220000} to rate or re-rate a model (low-end lifespan, miles)
    "request_delay_s": 1.5,
}

SAMPLE_CONFIG = """\
# Used car scout config. Every field here can also be set on the command line (see --help).
zip: ""               # your 5-digit ZIP (required)
radius_miles: 50      # optional hard radius in straight-line miles; set blank/0 for no cutoff (any distance)
price_caps:           # required: the most you'll pay. One cap for ALL makes (default; makes/models
  any: 15000          #   without lifespan data are kept and labeled "est. miles left unknown"):
  # ...or per make instead (these limit the search to those makes, or override `any` for that make):
  # toyota: 15000
  # honda: 15000
  # tesla: 29999
models: []            # optional allow-list, e.g. [camry, corolla, rav4, civic, accord, cr-v]
min_price: 4000       # skip parts cars / scams below this
year_min: null
min_miles_left: 50000 # optional est. miles left cutoff; set blank/0 for no cutoff
top_n: 8
output_dir: ""        # folder for reports (required), e.g. ~/Documents/used-car-scout
csv: false
md: true              # also write Markdown (dated .md + latest.md)
craigslist:
  enabled: true
  purveyor: owner     # owner | dealer | all
  clean_title_only: true
  detail_pages: 30
autodev:
  enabled: true       # needs AUTO_DEV_API_KEY in the environment; skipped otherwise
  pages_per_make: 3
auctions:
  enabled: false      # optional public/municipal auction pages (best-effort parsing)
  urls: []
  # - url: https://example-auction-site/list?cat=vehicles
  #   zip: "00000"
  #   label: County surplus auction
"""


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


ANY_MAKE_KEYS = ("any", "all", "*")


def opt_num(v: Any) -> float | None:
    """Optional numeric setting: None / '' / 0 mean 'not set'."""
    try:
        f = float(str(v).replace(",", "")) if v not in (None, "") else 0.0
    except ValueError:
        return None
    return f if f > 0 else None


def radius_of(cfg: dict) -> float | None:
    return opt_num(cfg.get("radius_miles"))


def min_left_of(cfg: dict) -> int | None:
    v = opt_num(cfg.get("min_miles_left"))
    return int(v) if v else None


def search_radius(cfg: dict) -> int:
    """Distance sent to search sites: the radius, or a generous 100 mi when there is no cutoff."""
    r = radius_of(cfg)
    return int(math.ceil(r)) if r else 100


def any_cap(cfg: dict) -> int | None:
    """The `any` (all makes) price cap, or None when only per-make caps are set."""
    return cfg.get("_any_cap")


def cap_for(cfg: dict, make: str) -> int | None:
    """Price cap for a make: its own cap if set, else the `any` cap (covers every make, even unknown)."""
    c = cfg["price_caps"].get(make)
    return c if c is not None else any_cap(cfg)


def search_targets(cfg: dict) -> list[tuple[str | None, int]]:
    """(make or None, max price) searches to run. None = one search across ALL makes (the `any` cap);
    per-make searches are added only for explicit caps above the `any` cap (lower ones are applied
    when filtering)."""
    anyc = any_cap(cfg)
    if anyc is None:
        return list(cfg["price_caps"].items())
    return [(None, int(anyc))] + [(m, int(c)) for m, c in cfg["price_caps"].items() if int(c) > int(anyc)]


def caps_text(cfg: dict) -> str:
    anyc = any_cap(cfg)
    if anyc is None:
        return ", ".join(f"{m.title()} ≤ ${int(c):,}" for m, c in cfg["price_caps"].items())
    extra = ", ".join(f"{m.title()} ≤ ${int(c):,}" for m, c in cfg["price_caps"].items() if int(c) != int(anyc))
    return f"Any make ≤ ${int(anyc):,}" + (f" ({extra})" if extra else "")


def load_config_file(path: Path) -> dict:
    text = path.expanduser().read_text()
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if path.suffix.lower() == ".toml":
        import tomllib
        return tomllib.loads(text)
    if yaml is None:
        raise SystemExit("pyyaml is required for YAML configs")
    return yaml.safe_load(text) or {}


# --------------------------------------------------------------------------- models

@dataclass
class Listing:
    id: str
    source: str            # "Craigslist" | "Auto.dev" | "Auction"
    url: str
    title: str
    price: int | None = None
    miles: int | None = None
    year: int | None = None
    make: str = ""
    model: str = ""        # free text (model + trim), lower case
    vin: str = ""
    lat: float | None = None
    lon: float | None = None
    zip: str = ""
    place: str = ""
    seller: str = ""
    cpo: bool = False
    accidents: int | None = None   # from a history report; None = no history data
    owners: int | None = None
    text: str = ""
    price_note: str = ""
    # computed
    dist: float | None = None
    dist_basis: str = ""
    model_key: str | None = None
    life_low: int | None = None
    est_left: int | None = None
    deductions: list[tuple[str, int]] = field(default_factory=list)
    confidence: str = "low"
    conf_why: str = ""
    flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: str = ""       # pass | reason excluded
    value: float = 0.0
    badge: str = ""
    posted: int = 0        # Craigslist posting id when known (higher = newer)
    unrated: bool = False  # kept under `any` without lifespan data (est. miles left unknown)
    odo_suspect: bool = False  # `any`: odometer implausibly low for the car's age (sorted after credible cars)


@dataclass
class SourceStatus:
    name: str
    count: int = 0
    note: str = ""


# --------------------------------------------------------------------------- longevity

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

