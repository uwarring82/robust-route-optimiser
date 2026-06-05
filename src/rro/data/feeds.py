"""Corridor GTFS feed registry (handbook §3.2, Coastline §1.1).

The registry is the single source of truth for *which* feeds enter ``G_base``.
It is data-driven so re-targeting the optimiser to another corridor is a
config/registry change, not a code change. The OSM PBF is a registry entry like
any other, discriminated by ``kind: osm_pbf``.
"""

from __future__ import annotations

from rro.config import Feed


def resolve_registry(feeds: list) -> list:
    """Materialise the validated feed registry from the config ``feeds[]`` list.

    Phase A scaffold: validation already happens in :func:`rro.config._parse_feeds`
    (≥1 ``gtfs`` + exactly one ``osm_pbf``); this will add per-feed coverage
    metadata (e.g. Flixbus gaps, handbook §8.6).
    """
    raise NotImplementedError("Phase A scaffold: feed-registry resolution pending")
