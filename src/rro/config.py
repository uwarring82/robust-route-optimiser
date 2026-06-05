"""Corridor + user configuration loader (handbook §2.6, §8.3).

Loads a single YAML document, applies the Phase-A defaults, and validates it
strictly: unknown keys are rejected **and** every scalar is type/range checked
(``departure_time`` must be valid ISO 8601). ``departure_time`` is optional at
load time — it may come from config or be supplied per-run (``--depart`` /
``plan(depart=...)``); :func:`require_departure_time` enforces presence (§8.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


class ConfigError(ValueError):
    """Raised on any malformed or contract-violating configuration."""


# Strict allow-lists (handbook §2.6: "config.py rejects unknown keys").
ALLOWED_KEYS = {
    "origin", "destination", "departure_time", "t_first_minutes", "depths",
    "epsilon", "alpha_c", "quantile", "fragile_headway_min", "bahncard",
    "accessibility_required", "feeds",
}
ALLOWED_EPSILON_KEYS = {"time_min", "creativity"}
ALLOWED_FEED_KEYS = {"id", "kind", "url", "licence", "version_pin", "sha256", "bbox"}
FEED_KINDS = {"gtfs", "osm_pbf"}


@dataclass
class Epsilon:
    """B3 ε-termination thresholds (handbook §2.6, §5.4). Calibration-adjustable."""

    time_min: float = 3.0
    creativity: float = 0.05


@dataclass
class Feed:
    """One corridor feed-registry entry (handbook §3.2). The OSM PBF is a feed
    of ``kind: osm_pbf``; there is no separate top-level OSM key."""

    id: str
    kind: str
    url: str
    version_pin: Optional[str] = None
    sha256: Optional[str] = None
    licence: Optional[str] = None
    bbox: Optional[list] = None


@dataclass
class Config:
    """Resolved Phase-A configuration with defaults from handbook §2.6."""

    origin: str
    destination: str
    feeds: list  # list[Feed]
    departure_time: Optional[str] = None
    t_first_minutes: int = 45
    depths: int = 3
    epsilon: Epsilon = field(default_factory=Epsilon)
    alpha_c: float = 0.7
    quantile: float = 0.8
    fragile_headway_min: float = 30.0
    bahncard: Optional[str] = None
    accessibility_required: bool = False


# --- scalar validators -----------------------------------------------------

def _reject_unknown(d: dict, allowed: set, where: str) -> None:
    extra = set(d) - allowed
    if extra:
        raise ConfigError(f"unknown key(s) in {where}: {sorted(extra)}")


def _check_str(value, key: str, *, allow_none: bool = False):
    if value is None and allow_none:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value


def _check_number(value, key: str, *, minimum=None, maximum=None, exclusive_min=False):
    # bool is a subclass of int — reject it where a number is expected.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{key} must be a number")
    if minimum is not None and (value <= minimum if exclusive_min else value < minimum):
        raise ConfigError(f"{key} must be {'>' if exclusive_min else '>='} {minimum}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{key} must be <= {maximum}")
    return value


def _check_int(value, key: str, *, minimum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{key} must be an integer")
    if minimum is not None and value < minimum:
        raise ConfigError(f"{key} must be >= {minimum}")
    return value


def _check_bool(value, key: str):
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be a boolean")
    return value


def validate_departure(value, key: str = "departure_time") -> str:
    """Validate an ISO 8601 departure timestamp (handbook §2.6, §8.3)."""
    if not isinstance(value, str):
        raise ConfigError(f"{key} must be an ISO 8601 string")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise ConfigError(f"{key} must be a valid ISO 8601 datetime, got {value!r}")
    return value


# --- parsing ---------------------------------------------------------------

def load_config(path) -> Config:
    """Load and validate a corridor YAML config file."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return parse_config(raw)


def parse_config(raw: dict) -> Config:
    """Validate a raw config mapping into a :class:`Config` (strict)."""
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")
    _reject_unknown(raw, ALLOWED_KEYS, "config")

    for req in ("origin", "destination", "feeds"):
        if req not in raw:
            raise ConfigError(f"missing required key: {req}")

    departure_time = raw.get("departure_time")
    if departure_time is not None:
        validate_departure(departure_time)

    eps_raw = raw.get("epsilon", {}) or {}
    if not isinstance(eps_raw, dict):
        raise ConfigError("epsilon must be a map of {time_min, creativity}")
    _reject_unknown(eps_raw, ALLOWED_EPSILON_KEYS, "epsilon")
    epsilon = Epsilon(
        time_min=_check_number(eps_raw.get("time_min", 3.0), "epsilon.time_min", minimum=0),
        creativity=_check_number(eps_raw.get("creativity", 0.05), "epsilon.creativity", minimum=0),
    )

    bahncard = raw.get("bahncard")
    if bahncard is not None:
        _check_str(bahncard, "bahncard")

    return Config(
        origin=_check_str(raw["origin"], "origin"),
        destination=_check_str(raw["destination"], "destination"),
        feeds=_parse_feeds(raw["feeds"]),
        departure_time=departure_time,
        t_first_minutes=_check_int(raw.get("t_first_minutes", 45), "t_first_minutes", minimum=1),
        depths=_check_int(raw.get("depths", 3), "depths", minimum=1),
        epsilon=epsilon,
        alpha_c=_check_number(raw.get("alpha_c", 0.7), "alpha_c", minimum=0),
        quantile=_check_number(raw.get("quantile", 0.8), "quantile", minimum=0, maximum=1, exclusive_min=True),
        fragile_headway_min=_check_number(raw.get("fragile_headway_min", 30.0), "fragile_headway_min", minimum=0, exclusive_min=True),
        bahncard=bahncard,
        accessibility_required=_check_bool(raw.get("accessibility_required", False), "accessibility_required"),
    )


def _parse_feeds(raw_feeds) -> list:
    if not isinstance(raw_feeds, list) or not raw_feeds:
        raise ConfigError("feeds must be a non-empty list")
    feeds = []
    for i, f in enumerate(raw_feeds):
        if not isinstance(f, dict):
            raise ConfigError(f"feeds[{i}] must be a mapping")
        _reject_unknown(f, ALLOWED_FEED_KEYS, f"feeds[{i}]")
        for req in ("id", "kind", "url"):
            if req not in f:
                raise ConfigError(f"feeds[{i}] missing required key: {req}")
        _check_str(f["id"], f"feeds[{i}].id")
        _check_str(f["url"], f"feeds[{i}].url")
        if f["kind"] not in FEED_KINDS:
            raise ConfigError(
                f"feeds[{i}] kind must be one of {sorted(FEED_KINDS)}, got {f['kind']!r}"
            )
        for opt in ("version_pin", "sha256", "licence"):
            if f.get(opt) is not None:
                _check_str(f[opt], f"feeds[{i}].{opt}")
        if f.get("bbox") is not None:
            _check_bbox(f["bbox"], f"feeds[{i}].bbox")
        feeds.append(Feed(**f))

    n_gtfs = sum(1 for f in feeds if f.kind == "gtfs")
    n_osm = sum(1 for f in feeds if f.kind == "osm_pbf")
    if n_gtfs < 1:
        raise ConfigError("at least one feed of kind 'gtfs' is required (§2.6)")
    if n_osm != 1:
        raise ConfigError("exactly one feed of kind 'osm_pbf' is required (§2.6)")
    return feeds


def _check_bbox(bbox, key: str) -> None:
    if (not isinstance(bbox, list) or len(bbox) != 4
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in bbox)):
        raise ConfigError(f"{key} must be a list of four numbers [minlon, minlat, maxlon, maxlat]")


def require_departure_time(cfg: Config, override: Optional[str] = None) -> str:
    """Resolve ``departure_time`` from a CLI/notebook override or config (§8.3).

    The override (``--depart`` / ``plan(depart=...)``) wins; otherwise the config
    value is used. Validates ISO 8601 format. Raises :class:`ConfigError` if
    neither source provides a valid timestamp.
    """
    dep = override or cfg.departure_time
    if not dep:
        raise ConfigError(
            "departure_time required via config or --depart / plan(depart=...)"
        )
    return validate_departure(dep)
