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
     per-make caps only, unrated models / no odometer are excluded when a cutoff is set. With either
     kind of cap, a rated (or make-average) car whose listing has no odometer or model year is
     excluded when a cutoff is set ("odometer/year not in listing").
     Set blank/0 = no longevity cutoff: those cars are kept and marked low-info.
  4. Branded titles (salvage / rebuilt / flood) mentioned in the listing = excluded.

There is no default price: price_caps is required (the script exits with a message without one).
Reports go to output_dir, or the current working folder when it is blank. The first run into a
folder sets the baseline; later runs mark new cars and price drops. Reposts of the same car
(same year/make/model, odometer within 1,000 mi, price within 5%) are merged.

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
    "price_caps": {},          # REQUIRED, no default: {make: max_price}, e.g. {"toyota": 15000}, or {"any": 12000} for ALL makes
    "models": [],              # optional: only these models (e.g. ["camry", "corolla", "civic"]); empty = any model
    "min_price": 0,            # skip listings priced below this (junk / parts cars)
    "year_min": None,
    "year_max": None,
    "min_miles_left": 50_000,  # optional longevity cutoff (default 50,000); None/0 = no cutoff
    "top_n": 8,                # number of picks at the top of the report
    "output_dir": "",          # where reports go (dated HTML + latest.html [+ MD, CSV]); blank = current working folder
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
        "enabled": "auto",     # auto = on only when AUTO_DEV_API_KEY is set; true = on (notes a missing key); false = off
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
# REQUIRED: fill in zip and price_caps (there is no default price). Everything else has a working default.
zip: ""               # REQUIRED: your 5-digit US ZIP, e.g. "12345"
price_caps:           # REQUIRED, no default: the most you'll pay. Replace <YOUR_MAX_PRICE> with a number.
  any: <YOUR_MAX_PRICE>   # one cap for ALL makes (makes/models without lifespan data are kept and labeled)
  # ...or caps per make instead (these limit the search to those makes, or override `any` for that make):
  # toyota: 15000
  # honda: 12000
radius_miles: 50      # hard radius in straight-line miles (default 50); blank/0 = any distance
models: []            # [] = any make/model; or an allow-list, e.g. [camry, corolla, rav4, civic, accord, cr-v]
min_price: 4000       # skip listings priced under this (parts cars / scams)
year_min: null        # oldest model year to include, e.g. 2010; null = any year
min_miles_left: 50000 # est. miles left cutoff (default 50,000); blank/0 = no cutoff
top_n: 8              # number of top picks in the report
output_dir: ""        # folder for reports; blank = the folder you run the script from
csv: false            # also write CSVs (passing + excluded)
md: true              # also write Markdown (dated .md + latest.md); HTML is always written
craigslist:
  enabled: true
  purveyor: owner     # owner = private sellers only | dealer | all
  clean_title_only: true  # true = only listings Craigslist marks as clean title; salvage/rebuilt/flood
                          #   titles mentioned in a listing are excluded either way
  detail_pages: 30    # listing pages opened to read odometer/VIN/map pin (~1.5 s each)
autodev:
  enabled: auto       # auto = use Auto.dev dealer listings only when AUTO_DEV_API_KEY is set (paid after a
                      #   free trial); false = never
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
