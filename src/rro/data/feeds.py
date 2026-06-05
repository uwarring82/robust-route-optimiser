"""Corridor GTFS feed registry (handbook §3.2, Coastline §1.1).

The registry is the single source of truth for *which* feeds enter ``G_base``. It
is data-driven so re-targeting the optimiser to another corridor is a config
change, not a code change. The OSM PBF is a registry entry like any other,
discriminated by ``kind: osm_pbf``.
"""

from __future__ import annotations

from dataclasses import dataclass

from rro.config import Feed


@dataclass
class FeedRegistry:
    """The resolved corridor feeds: ≥1 GTFS feed and exactly one OSM PBF (§3.2)."""

    gtfs: list  # list[Feed]
    osm: Feed

    @classmethod
    def from_feeds(cls, feeds: list) -> "FeedRegistry":
        gtfs = [f for f in feeds if f.kind == "gtfs"]
        osm = [f for f in feeds if f.kind == "osm_pbf"]
        if not gtfs:
            raise ValueError("feed registry requires at least one GTFS feed (§3.2)")
        if len(osm) != 1:
            raise ValueError("feed registry requires exactly one OSM PBF feed (§3.2)")
        return cls(gtfs=gtfs, osm=osm[0])

    def all(self) -> list:
        """All feeds (GTFS first, then the OSM PBF)."""
        return [*self.gtfs, self.osm]

    @property
    def osm_bbox(self):
        """The corridor OSM bounding box, if declared (§3.2)."""
        return self.osm.bbox


def resolve_registry(feeds: list) -> FeedRegistry:
    """Materialise the validated feed registry from the config ``feeds[]`` list (§3.2).

    Feed-level validation (≥1 GTFS, exactly one OSM PBF) already happens in
    :func:`rro.config._parse_feeds`; this re-checks it so the registry is sound
    even when built from feeds assembled outside the config loader.
    """
    return FeedRegistry.from_feeds(feeds)
