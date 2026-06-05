"""GTFS + OSM ingestion: fetch, validate, version-pin (handbook §3.3).

Idempotent against ``(version_pin, sha256)``: fetch → validate (GTFS checker;
ERROR-level aborts, WARNING logs) → version-pin → stage for the OTP build. Raw
bulk feeds are never committed; only the lockfile and a ``data/sample`` fixture.
"""

from __future__ import annotations

from rro.config import Feed


def ingest_feeds(feeds: list, cache_dir: str) -> list:
    """Fetch, validate, and pin each feed; return staged input paths (§3.3)."""
    raise NotImplementedError("Phase A scaffold: GTFS/OSM ingestion pending")


def validate_gtfs(path: str) -> list:
    """Run the structural GTFS validator; return findings. ERROR-level → abort (§3.3, §8.4)."""
    raise NotImplementedError("Phase A scaffold: GTFS validation pending")
