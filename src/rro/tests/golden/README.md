# Golden-route fixtures

Holds the byte-stable expected output of the deterministic Phase A pipeline
(handbook §8.4):

- `expected_portfolio.json` — the canonical portfolio produced by the full
  B1→B4 pipeline for a fixed `corridor.yml` and a fixed `--depart`, over the
  frozen `data/sample/` GTFS+OSM fixture. The comparison ignores only
  `query.generated_at`.
- A second case fixing `alpha_c=0.0` locks the calibration-pass reference-set
  selection (`reference_corridors`).

`expected_portfolio.json` currently holds a **synthetic** golden: hand-built
`ScoredCandidate`s fed through the real B4 clustering (`portfolio/cluster.py`) and
serialisation (`portfolio/output.py`, `card.py`). It locks the B4→Layer C seam —
`test_cluster.py::test_golden_portfolio_matches` regenerates it and diffs. Once the
routing/scoring pipeline produces candidates from the frozen `data/sample/` GTFS,
this is replaced by an end-to-end golden over real itineraries.
