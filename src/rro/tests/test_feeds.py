"""Unit tests for the corridor feed registry (handbook §3.2)."""

from __future__ import annotations

import pytest

from rro.config import Feed
from rro.data.feeds import FeedRegistry, resolve_registry


def _gtfs(i):
    return Feed(id=f"g{i}", kind="gtfs", url="http://x/g.zip")


def _osm():
    return Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf", bbox=[6.9, 47.9, 7.9, 51.4])


def test_resolve_registry_splits_gtfs_and_osm():
    reg = resolve_registry([_gtfs(1), _gtfs(2), _osm()])
    assert [f.id for f in reg.gtfs] == ["g1", "g2"]
    assert reg.osm.id == "osm"
    assert reg.osm_bbox == [6.9, 47.9, 7.9, 51.4]
    assert len(reg.all()) == 3
    assert reg.all()[-1].kind == "osm_pbf"  # OSM last


def test_registry_requires_a_gtfs_feed():
    with pytest.raises(ValueError, match="GTFS"):
        resolve_registry([_osm()])


def test_registry_requires_exactly_one_osm():
    with pytest.raises(ValueError, match="OSM"):
        resolve_registry([_gtfs(1), _osm(), _osm()])
    with pytest.raises(ValueError, match="OSM"):
        FeedRegistry.from_feeds([_gtfs(1)])
