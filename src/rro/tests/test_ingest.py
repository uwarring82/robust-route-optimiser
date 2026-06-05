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

# A minimal *valid* GTFS feed (referentially consistent, monotone stop_times).
_VALID_GTFS = {
    "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\n1,Test,http://t,Europe/Berlin\n",
    "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\nS1,Hasslinghausen,51.30,7.27\nS2,Freiburg Hbf,47.99,7.84\n",
    "routes.txt": "route_id,agency_id,route_short_name,route_type\nR1,1,ICE,2\n",
    "trips.txt": "route_id,service_id,trip_id\nR1,SVC,T1\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                      "T1,07:00:00,07:00:00,S1,1\nT1,11:00:00,11:00:00,S2,2\n",
    "calendar.txt": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
                    "SVC,1,1,1,1,1,0,0,20260101,20261231\n",
}


def _make_gtfs_zip(path, *, omit=None, override=None, prefix=""):
    files = dict(_VALID_GTFS)
    if override:
        files.update(override)
    if omit:
        files.pop(omit, None)
    with zipfile.ZipFile(path, "w") as z:
        for name, content in files.items():
            z.writestr(prefix + name, content)


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


# --- happy path + pinning --------------------------------------------------

def test_ingest_valid_gtfs(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(version_pin="2026-05-31"), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert res.ok
    assert res.findings == []
    assert res.sha256 == sha256_file(src)


def test_placeholder_sha_not_verified(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(sha256="<digest>"), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert res.ok


def test_sha256_mismatch_is_error(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    res = ingest_feed(_gtfs_feed(sha256="0" * 64), tmp_path / "cache",
                      downloader=_downloader_copying(src))
    assert not res.ok
    assert any("sha256" in f.message for f in res.findings)


# --- GTFS structural validation --------------------------------------------

def test_missing_required_file_aborts(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src, omit="stop_times.txt")
    with pytest.raises(IngestError, match="stop_times.txt"):
        ingest_feeds([_gtfs_feed()], tmp_path / "cache", downloader=_downloader_copying(src))


def test_not_a_zip_is_error(tmp_path):
    src = tmp_path / "src.zip"
    src.write_text("definitely not a zip")
    res = ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("zip" in f.message for f in res.findings)


def test_dangling_stop_reference_is_error(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src, override={
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                          "T1,07:00:00,07:00:00,S1,1\nT1,11:00:00,11:00:00,S9,2\n"})  # S9 undefined
    res = ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("unknown stop_id" in f.message for f in res.findings)


def test_dangling_service_reference_is_error(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src, override={"trips.txt": "route_id,service_id,trip_id\nR1,NOPE,T1\n"})
    res = ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("unknown service_id" in f.message for f in res.findings)


def test_non_increasing_stop_sequence_is_error(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src, override={
        "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                          "T1,07:00:00,07:00:00,S1,2\nT1,11:00:00,11:00:00,S2,1\n"})  # 2 then 1
    res = ingest_feed(_gtfs_feed(), tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("stop_sequence" in f.message for f in res.findings)


def test_valid_feed_in_nested_archive(tmp_path):
    zp = tmp_path / "nested.zip"
    _make_gtfs_zip(zp, prefix="feed/")  # files under feed/ — basenames still count
    assert validate_gtfs(zp) == []


# --- OSM validation --------------------------------------------------------

def test_osm_empty_is_error(tmp_path):
    src = tmp_path / "c.osm.pbf"
    src.write_bytes(b"")
    feed = Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf")
    res = ingest_feed(feed, tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok


def test_osm_non_pbf_is_error(tmp_path):
    src = tmp_path / "c.osm.pbf"
    src.write_bytes(b"this is not a pbf file at all, just bytes")
    feed = Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf")
    res = ingest_feed(feed, tmp_path / "cache", downloader=_downloader_copying(src))
    assert not res.ok
    assert any("OSMHeader" in f.message for f in res.findings)


def test_osm_with_header_ok(tmp_path):
    src = tmp_path / "c.osm.pbf"
    src.write_bytes(b"\x00\x00\x00\x0d\x0a\x09OSMHeader----- rest of pbf -----")
    feed = Feed(id="osm", kind="osm_pbf", url="http://x/c.pbf")
    res = ingest_feed(feed, tmp_path / "cache", downloader=_downloader_copying(src))
    assert res.ok


# --- cache safety / atomicity ----------------------------------------------

def test_caching_skips_second_download(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    feed = _gtfs_feed(version_pin="v1")
    dl = _downloader_copying(src)
    ingest_feed(feed, tmp_path / "cache", downloader=dl)
    ingest_feed(feed, tmp_path / "cache", downloader=dl)
    assert dl.calls["n"] == 1  # second run used the cache


def test_fetch_failure_leaves_no_partial(tmp_path):
    cache = tmp_path / "cache"

    def partial_then_fail(url, dest):
        Path(dest).write_text("partial bytes")  # writes to the .part temp
        raise OSError("connection reset")

    with pytest.raises(IngestError, match="failed to fetch"):
        ingest_feed(_gtfs_feed(version_pin="v1"), cache, downloader=partial_then_fail)
    # No usable artefact and no leftover .part file poison future runs.
    assert not (cache / "delfi-v1.zip").exists()
    assert not (cache / "delfi-v1.zip.part").exists()


def test_stale_cache_failing_pin_is_redownloaded(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    good_sha = sha256_file(src)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "delfi-v1.zip").write_text("stale corrupt content")  # wrong vs pin

    dl = _downloader_copying(src)
    res = ingest_feed(_gtfs_feed(version_pin="v1", sha256=good_sha), cache, downloader=dl)
    assert dl.calls["n"] == 1   # stale cache was re-fetched
    assert res.ok and res.sha256 == good_sha


# --- lockfile --------------------------------------------------------------

def test_lockfile_records_pinned_digest(tmp_path):
    src = tmp_path / "src.zip"
    _make_gtfs_zip(src)
    [res] = ingest_feeds([_gtfs_feed(version_pin="2026-05-31")], tmp_path / "cache",
                         downloader=_downloader_copying(src))
    lock = to_lockfile([res])
    assert lock["delfi"]["sha256"] == res.sha256
    assert lock["delfi"]["version_pin"] == "2026-05-31"
    assert lock["delfi"]["kind"] == "gtfs"
