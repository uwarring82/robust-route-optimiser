# Sample corridor data

Small, redacted example data only — **never raw bulk feeds** (Coastline §5
custodianship; handbook §3.3). Raw GTFS-DE archives and full OSM extracts live in
the local cache and are git-ignored; only the lockfile in `src/rro/data/feeds.py`
and this trimmed fixture are tracked.

Intended contents (added with the ingestion + golden-route work, handbook §8.4):

- a hand-trimmed multi-feed GTFS extract covering the Haßlinghausen feeder hubs
  and the backbone to Freiburg (Breisgau) Hbf;
- a tiny OSM PBF clip for first/last-mile walking and bus access.

Because the sample is frozen and the engine is deterministic
(`T_eff = T_schedule`), the full pipeline reproduces a byte-stable portfolio for
the golden-route tests.
