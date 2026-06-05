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

import csv
import hashlib
import io
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


def _read_csv(z: zipfile.ZipFile, archive_name: str) -> list:
    with z.open(archive_name) as raw:
        return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")))


def validate_gtfs(path) -> list:
    """Structural GTFS validation (handbook §3.3, §8.4).

    A fast in-process pre-flight gate: valid zip; required files + a service
    calendar present; referential integrity (``trips`` → routes/services,
    ``stop_times`` → trips/stops); and strictly increasing ``stop_sequence`` per
    trip. This is intended for the trimmed corridor sample and pinned feeds; the
    canonical full check for large national archives is the external MobilityData
    *gtfs-validator* (§3.3). Returns ERROR/WARNING :class:`Finding`s.
    """
    if not zipfile.is_zipfile(path):
        return [Finding("ERROR", f"{path} is not a valid zip archive")]

    findings = []
    with zipfile.ZipFile(path) as z:
        by_base = {}
        for n in z.namelist():
            by_base.setdefault(os.path.basename(n), n)

        for m in sorted(REQUIRED_GTFS - set(by_base)):
            findings.append(Finding("ERROR", f"GTFS missing required file: {m}"))
        if "calendar.txt" not in by_base and "calendar_dates.txt" not in by_base:
            findings.append(Finding("ERROR", "GTFS missing service calendar "
                                              "(calendar.txt or calendar_dates.txt)"))
        if REQUIRED_GTFS - set(by_base):
            return findings  # core files missing — deeper checks not meaningful

        try:
            stops = _read_csv(z, by_base["stops.txt"])
            routes = _read_csv(z, by_base["routes.txt"])
            trips = _read_csv(z, by_base["trips.txt"])
            stop_times = _read_csv(z, by_base["stop_times.txt"])
            services = set()
            for cal in ("calendar.txt", "calendar_dates.txt"):
                if cal in by_base:
                    services |= {r["service_id"] for r in _read_csv(z, by_base[cal]) if r.get("service_id")}
        except (csv.Error, UnicodeDecodeError, KeyError) as e:
            findings.append(Finding("ERROR", f"GTFS parse error: {e}"))
            return findings

    stop_ids = {r["stop_id"] for r in stops if r.get("stop_id")}
    route_ids = {r["route_id"] for r in routes if r.get("route_id")}
    trip_ids = {r["trip_id"] for r in trips if r.get("trip_id")}

    for label, ids in (("stops.txt", stop_ids), ("routes.txt", route_ids), ("trips.txt", trip_ids)):
        if not ids:
            findings.append(Finding("ERROR", f"{label} has no id values"))

    for rid in sorted({t["route_id"] for t in trips if t.get("route_id") and t["route_id"] not in route_ids}):
        findings.append(Finding("ERROR", f"trips.txt references unknown route_id {rid!r}"))
    for sid in sorted({t["service_id"] for t in trips if t.get("service_id") and t["service_id"] not in services}):
        findings.append(Finding("ERROR", f"trips.txt references unknown service_id {sid!r}"))
    for tid in sorted({s["trip_id"] for s in stop_times if s.get("trip_id") and s["trip_id"] not in trip_ids}):
        findings.append(Finding("ERROR", f"stop_times.txt references unknown trip_id {tid!r}"))
    for sid in sorted({s["stop_id"] for s in stop_times if s.get("stop_id") and s["stop_id"] not in stop_ids}):
        findings.append(Finding("ERROR", f"stop_times.txt references unknown stop_id {sid!r}"))

    seqs_by_trip = {}
    for st in stop_times:
        tid = st.get("trip_id")
        if tid is not None:
            seqs_by_trip.setdefault(tid, []).append(st.get("stop_sequence"))
    for tid, seqs in seqs_by_trip.items():
        try:
            nums = [int(s) for s in seqs]
        except (TypeError, ValueError):
            findings.append(Finding("ERROR", f"stop_times.txt has non-integer stop_sequence for trip {tid!r}"))
            continue
        if any(nums[i] >= nums[i + 1] for i in range(len(nums) - 1)):
            findings.append(Finding("ERROR", f"stop_times.txt stop_sequence not strictly increasing for trip {tid!r}"))
    return findings


def validate_osm(path) -> list:
    """OSM PBF structural validation: non-empty + a valid ``OSMHeader`` (§3.3).

    Deeper checks (way/node counts, corridor-bbox coverage) require a PBF parser
    and are **deferred** — a forward-hook behind this seam.
    """
    if os.path.getsize(path) == 0:
        return [Finding("ERROR", "OSM PBF is empty")]
    with open(path, "rb") as f:
        head = f.read(64)
    if b"OSMHeader" not in head:
        return [Finding("ERROR", "OSM file is not a valid PBF (no OSMHeader in header)")]
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

    # Skip download only when the cached artefact exists AND — if a real sha256 is
    # pinned — matches it. A stale/corrupt cache for the same (id, version_pin) is
    # re-fetched rather than poisoning every future run.
    need_download = not dest.exists()
    if dest.exists() and _is_real_sha(feed.sha256) and sha256_file(dest) != feed.sha256:
        need_download = True
    if need_download:
        # Download to a temp sibling, then atomic-rename — a failed or partial
        # download never leaves a usable-looking dest behind.
        tmp = dest.with_name(dest.name + ".part")
        try:
            downloader(feed.url, str(tmp))
        except Exception as e:  # noqa: BLE001 - normalise any transport failure
            try:
                tmp.unlink()
            except OSError:
                pass
            raise IngestError(f"failed to fetch {feed.id} from {feed.url}: {e}") from e
        os.replace(str(tmp), str(dest))

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
