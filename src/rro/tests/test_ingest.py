"""Unit tests for GTFS/OSM ingestion (handbook §3.3), fully offline."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from rro.config import Feed
from rro.data.ingest import (
    IngestError,
    ingest_feed,
    ingest_feeds,
    sha256_file,
    to_lockfile,
    validate_gtfs,
)


def _make_gtfs_zip(path, *, complete=True):
    files = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt"]
    if not complete:
        files.remove("stop_times.txt")
    with zipfile.ZipFile(path, "w") as z:
        for name in files:
            z.writestr(name, "id\n")


def _downloader_copying(src):
    """A fake downloader that copies a prepared file and counts its calls."""
    calls = {"n": 0}

    def dl(url, dest):
        calls["n"] += 1
        Path(dest).write_bytes(Path(src).read_bytes())

    dl.calls = calls
    return dl


def _gtfs_feed(**kw):
    return Feed(id=kw.pop("id", "delfi"), kind="gtfs", url="http://x/g.zip", **kw)


def test_ingest_valid_gtfs(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(version_pin="2026-05-31"), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert res.ok
    assert res.findings == []
    assert res.sha256 == sha256_file(src)


def test_missing_required_file_aborts(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src, complete=False)
    with pytest.raises(IngestError, match="stop_times.txt"):
        ingest_feeds([_gtfs_feed()], tmp_path / "cache", downloader=_downloader_copying(src))


def test_not_a_zip_is_error(tmp_path):
    src = tmp_path / "src.zip"
    src.write_text("definitely not a zip")
    res = ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("zip" in f.message for f in res.findings)


def test_sha256_mismatch_is_error(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(sha256="0" * 64), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert not res.ok
    assert any("sha256" in f.message for f in res.findings)


def test_placeholder_sha_not_verified(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(sha256="<digest>"), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert res.ok  # placeholder is not a real digest → not verified


def test_caching_skips_second_download(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    feed = _gtfs_feed(version_pin="v1")
    dl = _downloader_copying(src)
    ingest_feed(feed, tmp_path / "cache", downloader=dl)
    ingest_feed(feed, tmp_path / "cache", downloader=dl)
    assert dl.calls["n"] == 1  # second run used the cache


def test_fetch_failure_normalised_to_ingest_error(tmp_path):
    def boom(url, dest):
        raise OSError("connection refused")

    with pytest.raises(IngestError, match="failed to fetch"):
        ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=boom)


def test_osm_empty_is_error(tmp_path):
    src = tmp_path / "c.osm.pbf"
    src.write_bytes(b"")
    feed = Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf")
    res = ingest_feed(feed, tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok


def test_osm_with_header_ok(tmp_path):
    src = tmp_path / "c.osm.pbf"
    src.write_bytes(b"\x00\x00\x00\x0d\x0a\x09OSMHeader----- rest of pbf -----")
    feed = Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf")
    res = ingest_feed(feed, tmp_path / "cache", downloader=_downloader_copying(src))
    assert res.ok


def test_validate_gtfs_directly_on_subdir_entries(tmp_path):
    # Names may be nested in the archive; basenames are what count.
    zp = tmp_path / "nested.zip"
    with zipfile.ZipFile(zp, "w") as z:
        for name in ["feed/agency.txt", "feed/stops.txt", "feed/routes.txt",
                     "feed/trips.txt", "feed/stop_times.txt", "feed/calendar.txt"]:
            z.writestr(name, "id\n")
    assert validate_gtfs(zp) == []


def test_lockfile_records_pinned_digest(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    [res] = ingest_feeds([_gtfs_feed(version_pin="2026-05-31")], tmp_path / "cache",
                         downloader=_downloader_copying(src))
    lock = to_lockfile([res])
    assert lock["delfi"]["sha256"] == res.sha256
    assert lock["delfi"]["version_pin"] == "2026-05-31"
    assert lock["delfi"]["kind"] == "gtfs"
