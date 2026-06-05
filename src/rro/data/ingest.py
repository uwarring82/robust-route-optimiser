"""GTFS + OSM ingestion: fetch, validate, version-pin, stage (handbook §3.3).

Idempotent against the local cache keyed by ``(id, version_pin)``: a feed already
present is not re-downloaded (reproducible re-runs are network-free). GTFS archives
are structurally validated (required files present); any ERROR-level finding aborts
ingestion. Raw bulk feeds are never committed — only the lockfile and a trimmed
``data/sample`` fixture (§3.3).

The downloader is injectable (``downloader(url, dest) -> None``) so tests and
offline runs need no network, mirroring the OTP client's transport seam.
"""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from rro.config import Feed


class IngestError(RuntimeError):
    """A fatal ingestion failure (fetch error or ERROR-level validation; CLI exit 2)."""


# GTFS files that must be present for a usable feed (gtfs.org; handbook §8.4).
REQUIRED_GTFS = {"agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt"}


@dataclass
class Finding:
    """A validation finding. ``level`` is ``"ERROR"`` (aborts) or ``"WARNING"``."""

    level: str
    message: str


@dataclass
class IngestedFeed:
    """One fetched, validated, pinned feed (§3.3)."""

    feed: Feed
    path: str
    sha256: str
    findings: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(f.level != "ERROR" for f in self.findings)


def sha256_file(path) -> str:
    """SHA-256 hex digest of a file, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_real_sha(s) -> bool:
    """True for a 64-char hex digest (a placeholder like ``<digest>`` is not)."""
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s.lower())


def _ext(kind: str) -> str:
    return ".zip" if kind == "gtfs" else ".osm.pbf"


def _default_downloader(url: str, dest: str) -> None:
    import urllib.request

    urllib.request.urlretrieve(url, dest)  # noqa: S310 - url comes from the pinned registry


def validate_gtfs(path) -> list:
    """Structural GTFS validation: valid zip + required files present (§3.3, §8.4)."""
    if not zipfile.is_zipfile(path):
        return [Finding("ERROR", f"{path} is not a valid zip archive")]
    with zipfile.ZipFile(path) as z:
        names = {os.path.basename(n) for n in z.namelist()}
    findings = [Finding("ERROR", f"GTFS missing required file: {m}")
                for m in sorted(REQUIRED_GTFS - names)]
    if "calendar.txt" not in names and "calendar_dates.txt" not in names:
        findings.append(Finding("ERROR", "GTFS missing service calendar "
                                          "(calendar.txt or calendar_dates.txt)"))
    return findings


def validate_osm(path) -> list:
    """Light OSM PBF validation: non-empty, with an ``OSMHeader`` near the start (§3.3)."""
    if os.path.getsize(path) == 0:
        return [Finding("ERROR", "OSM PBF is empty")]
    with open(path, "rb") as f:
        head = f.read(64)
    if b"OSMHeader" not in head:
        return [Finding("WARNING", "OSM file does not look like a PBF (no OSMHeader in header)")]
    return []


def _validate(feed: Feed, path) -> list:
    return validate_gtfs(path) if feed.kind == "gtfs" else validate_osm(path)


def ingest_feed(feed: Feed, cache_dir, *, downloader: Optional[Callable] = None,
                validate: bool = True) -> IngestedFeed:
    """Fetch (cache-aware), pin (sha256), and validate one feed (§3.3)."""
    downloader = downloader or _default_downloader
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / f"{feed.id}-{feed.version_pin or 'unpinned'}{_ext(feed.kind)}"

    if not dest.exists():
        try:
            downloader(feed.url, str(dest))
        except Exception as e:  # noqa: BLE001 - normalise any transport failure
            raise IngestError(f"failed to fetch {feed.id} from {feed.url}: {e}") from e

    digest = sha256_file(dest)
    findings = []
    if _is_real_sha(feed.sha256) and digest != feed.sha256:
        findings.append(Finding(
            "ERROR", f"sha256 mismatch for {feed.id}: expected {feed.sha256}, got {digest}"))
    if validate:
        findings.extend(_validate(feed, dest))
    return IngestedFeed(feed=feed, path=str(dest), sha256=digest, findings=findings)


def ingest_feeds(feeds, cache_dir, *, downloader: Optional[Callable] = None,
                 validate: bool = True) -> list:
    """Ingest all feeds; raise :class:`IngestError` if any has an ERROR finding (§3.3)."""
    results = [ingest_feed(f, cache_dir, downloader=downloader, validate=validate) for f in feeds]
    errors = [fd.message for r in results for fd in r.findings if fd.level == "ERROR"]
    if errors:
        raise IngestError("ingestion failed:\n" + "\n".join(errors))
    return results


def to_lockfile(results) -> dict:
    """Reproducibility lockfile mapping ``feed.id`` → pinned digest + path (§3.3)."""
    return {
        r.feed.id: {
            "kind": r.feed.kind,
            "version_pin": r.feed.version_pin,
            "sha256": r.sha256,
            "path": r.path,
        }
        for r in results
    }


def write_lockfile(results, path) -> None:
    """Write the lockfile as sorted JSON."""
    Path(path).write_text(
        json.dumps(to_lockfile(results), indent=2, sort_keys=True) + "\n", encoding="utf-8")
