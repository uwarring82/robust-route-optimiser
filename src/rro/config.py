"""Corridor + user configuration loader (handbook §2.6, §8.3).

Loads a single YAML document, applies the Phase-A defaults, and **rejects unknown
keys**. ``departure_time`` is optional at load time: it may be set in config or
supplied per-run (``--depart`` / ``plan(depart=...)``); :func:`require_departure_time`
enforces that exactly one source provides it (§8.3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


def _reject_unknown(d: dict, allowed: set, where: str) -> None:
    extra = set(d) - allowed
    if extra:
        raise ConfigError(f"unknown key(s) in {where}: {sorted(extra)}")


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

    eps_raw = raw.get("epsilon", {}) or {}
    if not isinstance(eps_raw, dict):
        raise ConfigError("epsilon must be a map of {time_min, creativity}")
    _reject_unknown(eps_raw, ALLOWED_EPSILON_KEYS, "epsilon")
    epsilon = Epsilon(**eps_raw)

    feeds = _parse_feeds(raw["feeds"])

    return Config(
        origin=raw["origin"],
        destination=raw["destination"],
        feeds=feeds,
        departure_time=raw.get("departure_time"),
        t_first_minutes=raw.get("t_first_minutes", 45),
        depths=raw.get("depths", 3),
        epsilon=epsilon,
        alpha_c=raw.get("alpha_c", 0.7),
        quantile=raw.get("quantile", 0.8),
        fragile_headway_min=raw.get("fragile_headway_min", 30.0),
        bahncard=raw.get("bahncard"),
        accessibility_required=raw.get("accessibility_required", False),
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
        if f["kind"] not in FEED_KINDS:
            raise ConfigError(
                f"feeds[{i}] kind must be one of {sorted(FEED_KINDS)}, got {f['kind']!r}"
            )
        feeds.append(Feed(**f))

    n_gtfs = sum(1 for f in feeds if f.kind == "gtfs")
    n_osm = sum(1 for f in feeds if f.kind == "osm_pbf")
    if n_gtfs < 1:
        raise ConfigError("at least one feed of kind 'gtfs' is required (§2.6)")
    if n_osm != 1:
        raise ConfigError("exactly one feed of kind 'osm_pbf' is required (§2.6)")
    return feeds


def require_departure_time(cfg: Config, override: Optional[str] = None) -> str:
    """Resolve ``departure_time`` from a CLI/notebook override or config (§8.3).

    The override (``--depart`` / ``plan(depart=...)``) wins; otherwise the config
    value is used. Raises :class:`ConfigError` if neither provides one.
    """
    dep = override or cfg.departure_time
    if not dep:
        raise ConfigError(
            "departure_time required via config or --depart / plan(depart=...)"
        )
    return dep
