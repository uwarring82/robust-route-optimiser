# Golden-route fixtures

Holds the byte-stable expected output of the deterministic Phase A pipeline
(handbook §8.4):

- `expected_portfolio.json` — the canonical portfolio produced by the full
  B1→B4 pipeline for a fixed `corridor.yml` and a fixed `--depart`, over the
  frozen `data/sample/` GTFS+OSM fixture. The comparison ignores only
  `query.generated_at`.
- A second case fixing `alpha_c=0.0` locks the calibration-pass reference-set
  selection (`reference_corridors`).

These files are generated once the B1→B4 pipeline is implemented (the routing,
scoring, and clustering stubs are filled in). Until then this directory is a
placeholder.
