"""Shared test fixtures for the Phase A engine."""

from __future__ import annotations

import pytest


@pytest.fixture
def valid_config_dict() -> dict:
    """A minimal valid corridor config mirroring handbook §8.3."""
    return {
        "origin": "Haßlinghausen",
        "destination": "Freiburg (Breisgau) Hbf",
        "departure_time": "2026-06-08T07:30:00+02:00",
        "feeds": [
            {"id": "delfi-de", "kind": "gtfs", "url": "https://example/gtfs.zip"},
            {"id": "osm-corridor", "kind": "osm_pbf", "url": "https://example/c.osm.pbf"},
        ],
    }
