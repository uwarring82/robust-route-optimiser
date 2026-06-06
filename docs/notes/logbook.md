---
layout: default
title: "Project Logbook"
---

# Project Logbook

Operational record for the Robust Route Optimiser: repository housekeeping,
infrastructure, releases, and FAIR-compliance steps.

This complements the [Design Log](design-log) — the design log records *architectural*
deliberation (what the system is and why); this logbook records *operational* steps
(what was done to the repository and when).

Entries are append-only and newest-last. Each entry: date, what changed, why, and
follow-ups.

---

## 2026-06-05 — Repository audit, cleanup, and FAIR kickoff

**Context.** First operational review of the repo since the initial commit. The repo
had accumulated artifacts from a mixed local-git / GitHub-web-upload workflow.

**Findings (state at start of session).**

| Item | Status | Note |
|---|---|---|
| Stray brace-expansion dirs `{docs…`, `{src,data…` | ✅ Removed | Empty, untracked; from a malformed `mkdir` run in a non-brace shell |
| Root `index.md` | ⚠️ Cruft | Duplicate of `docs/index.md`, older (uses `{{ site.baseurl }}` links, no demo link). Pages builds from `./docs`, so root copy is never served |
| Root `workflows/pages.yml` | ⚠️ Cruft | Byte-identical to `.github/workflows/pages.yml`. GitHub Actions only reads `.github/workflows/`, so root copy is dead |
| `.gitignore`, `src/`, `data/sample/` | ℹ️ Absent | Present in initial commit, since removed. README still references `src/` and `data/sample/` |
| `docs/demo/index.html` | ✅ Added | Interactive static demo (995 lines), linked from `docs/index.md` |
| GitHub Pages build | ✅ OK | `.github/workflows/pages.yml` builds Jekyll from `./docs`, deploys on push to `main` touching `docs/**` |

**Actions taken.**

- Removed stray brace-expansion directories (done before this session).
- Removed root `index.md` (dead duplicate of `docs/index.md`).
- Removed root `workflows/` (dead duplicate of `.github/workflows/`).
- Created this logbook (linked from `docs/index.md`).
- Added FAIR metadata: `CITATION.cff`, `codemeta.json`, `.zenodo.json`.
- Added `LICENSE-CODE` (MIT); updated README badges, licence, and citation sections.
- Re-added `.gitignore`.

**Decisions (this session).**

- Code license for `src/`: **MIT** (added as `LICENSE-CODE`; docs remain CC BY-SA 4.0 → dual-licensed).
- Zenodo DOI: **prepare metadata now**, mint DOI on first archived release.
- Git: commit directly to `main`.

**FAIR roadmap.** Making the project Findable, Accessible, Interoperable, Reusable:

- [x] **F** — Added `CITATION.cff` (author, ORCID, version, keywords, repo URL) → enables GitHub
      "Cite this repository" + machine-readable citation.
- [x] **F** — Added `.zenodo.json` deposition metadata + DOI badge placeholder in README.
      *(Activation steps below; DOI deferred by decision — see addendum.)*
- [x] **A** — Landing page + licenses openly reachable (Pages live from `./docs`, licenses stated).
- [x] **I** — Added `codemeta.json` (CodeMeta 3.0 / schema.org software metadata, ORCID via `@id`).
- [x] **R** — Code license decided (**MIT**) and added as `LICENSE-CODE`; README licence section updated.
- [x] **R** — Re-added `.gitignore`.
- [x] **R** — Added `CONTRIBUTING.md` (governance via Harbour Council-3, coastline/handbook split,
      conventions, B1–B7 falsification path); linked from README.
- [x] **Hygiene** — README "Project structure" synced with reality.

**Zenodo activation (manual, when ready to mint a DOI).**

1. Sign in at [zenodo.org](https://zenodo.org) with GitHub; flip the toggle for
   `uwarring82/robust-route-optimiser` on the Zenodo *GitHub* page.
2. Create a GitHub **release** (e.g. tag `v0.6.0-rc1`). Zenodo reads `.zenodo.json` and
   archives the tarball, minting a version DOI + a concept DOI.
3. Replace the placeholder DOI badge in `README.md` with the concept-DOI badge (template
   is in an HTML comment right above it) and add `doi:`/`identifiers:` to `CITATION.cff`.

**Open follow-ups.**

- DOI: deferred by decision (see addendum below). Zenodo activation steps stand ready for
  when a release is cut.

---

## 2026-06-05 — Addendum: ORCID added, CONTRIBUTING added, DOI deferred

- **ORCID 0000-0001-8081-9718** added for the author across `CITATION.cff`
  (`orcid:` URL form), `.zenodo.json` (`orcid` bare id), and `codemeta.json` (Person `@id`);
  also surfaced in the README author block. Checksum verified (ISO 7064 MOD 11-2). This
  closes the last open Findable-metadata item.
- **`CONTRIBUTING.md`** added at repo root and linked from README.
- **DOI** explicitly **deferred** at the author's request — to be minted later via the
  Zenodo activation steps above. The placeholder DOI badge remains in README until then.

---

## 2026-06-05 — Phase A engine handbook drafted

**Context.** First implementation handbook. Moves [Phase A — Static Engine](../handbook/phase-a-engine)
from *Planned* to *Draft*, subordinate to Coastline v0.6.0-rc1.

**Method.** Authored with a multi-agent workflow under one binding design contract:
8 section authors (parallel) → 4 adversarial review lenses (coastline-fidelity, scope,
completeness, consistency) → synthesis → final fidelity verify. 23 findings (5 critical,
7 major) fixed during synthesis; verify verdict **pass**.

**Key design decisions baked in** (all handbook-level, no coastline amendment — Coastline §6):

- **Deterministic degeneracy made explicit.** `T_eff = T_schedule` ⇒ `Q₀.₈ = Q₀.₉₅ = E[T_eff]`,
  so the *Fastest* and *Sicherste* clusters collapse. Resolved with a **structural
  decision-robustness proxy** (Coastline §0.1): lexicographic (fewest transfers → largest
  min transfer slack → fewest fragile legs), an explicit stand-in for `Q₀.₉₅`, replaced in Phase B.
- **No fake confidence.** Card `confidence = "scheduled"` (the §7 ±X interval is `Q₀.₈ − E[T_eff] = 0`).
- **Creativity two-pass** (Coastline §0.3): calibration pass at `α_C = 0` freezes top-3 backbone
  corridors as `R`; scoring pass computes `C(r)`.
- **Tech contract:** OTP 2.x (GTFS GraphQL) on `G_base`; fixed `src/rro/` module map; one canonical
  JSON portfolio schema; ε-termination defaults (3 min / 0.05); `fragile_headway_min = 30`.

**Post-synthesis review (this session).** Read the full 1430-line draft; fixed 3 verify residuals
plus example-data slips (transfer-count vs last-mile boarding, a zero-duration leg, spurious
Hbf→Hbf last-mile legs, terminal-leg slack). Added a binding **transfer-count semantics** rule
in §4.1 (last-mile boarding excluded from `transfers` / `min_transfer_slack_min`). Verified
programmatically that all 6 JSON examples parse and that `J`, `creativity`, degeneracy,
`transfers`, `transfer_stations`, `expected_arrival`, `min_transfer_slack`, and terminal-null
invariants hold across every example.

**Status flips:** README + docs/index Phase A row → **Draft**. Implementation (`src/`) not yet started.

**Follow-ups.** Phase B and Phase C handbooks remain *Planned*. The §8.7 module seams are the
documented Phase B attachment points (G′ mutation stage in `graph/build.py`).

---

## 2026-06-05 — Phase A handbook: review response

Two independent reviews of the Draft (committed `bf9cdec`). Confirmed clean: coastline
subordination, `J` / `creativity` invariants, `"scheduled"` confidence, the §8.7 Phase B
seams. Fixed the following before the handbook is used as an implementation contract:

- **B4 floor (major).** §7.1 step 4 allowed a single-strategy portfolio when < 2 distinct
  routes exist — contradicting Coastline §B4 *min 2* and CLI exit `4`. Now **underfull → error**
  (exit `4`), never a 1-strategy result. *Min 2* stated as a hard floor.
- **`departure_time` (major).** Was used in CLI precedence + emitted JSON but absent from the
  config contract (which rejects unknown keys). Added to the §2.6 table (required via config
  **or** `--depart`).
- **Candidate identity (major).** Reconciled the dedup rule: the backbone signature's first
  board stop **is** the feeder hub, so feeder-hub choice is part of identity; only the
  first-mile leg (mode/path) is ignored. §4.3 and §5.3 now agree — different hubs → distinct
  candidates, same hub + different first-mile mode → merged.
- **Taxi `risks` (major).** `risks` is empty in Phase A **except** an experimental-taxi
  low-confidence warning (Coastline §6); aligned §2.8, §6.5, §7.3, §8.1, §8.4 (test row).
- **Test/fixture paths (minor).** Unified: GTFS sample = top-level `data/sample/` (§3.3);
  test artefacts under `src/rro/tests/` (`…/golden/`, `…/data/broken/`).
- **`J` precision + time formats (minor).** §2.8 now states one-decimal rounding for minute
  fields (two for `creativity`) and that `legs[].dep/arr` are ISO 8601 while
  `card.expected_arrival` is `HH:MM`.
- **Metadata drift (minor).** README tree `(planned)` → `(draft)`; README status →
  "Handbook drafted"; fixed the broken logbook → handbook relative link.
- **Clarified (not a bug):** config `epsilon` is a *map*; emitted `parameters.epsilon` is the
  `time_min` scalar by design — cross-referenced in §2.6.

Re-validated: all 6 JSON examples parse and every invariant (J, creativity, degeneracy,
transfers, expected_arrival, terminal-null) still holds.

---

## 2026-06-05 — Phase A handbook: review response (round 2)

Follow-up review caught three issues introduced or missed in round 1:

- **Time format vs examples (major).** Round 1 added the rule "legs are ISO 8601" but left the
  §2.8/§7.2 canonical examples in `HH:MM`. Converted the **§2.8 output-contract** example to ISO
  (now the canonical wire-format example alongside §8.1); marked §7.2 (and §4.4/§5.6) as `HH:MM`-
  abbreviated for readability, with the time-format bullet naming which examples are which.
- **Taxi-risk residual (major).** The §7.3 "Forward-hooks" paragraph still said `risks` are
  empty/inert. Added the experimental-taxi carve-out there, and swept the whole document — two more
  absolute "risks empty" statements (§1.5, §5.6) now carry the carve-out. A grep confirms none remain.
- **`departure_time` in examples (minor).** Added it to both `corridor.yml` examples (§2.6, §8.3)
  and documented enforcement: config may set it, `--depart` / `plan(depart=…)` override, and the
  engine errors if neither provides it.

Re-validated: 6 JSON blocks parse; §2.8 legs are ISO; both YAML configs parse with `departure_time`;
J / expected_arrival invariants hold.

---

## 2026-06-05 — Phase A engine scaffold (`src/rro/`)

First code in the repo. Scaffolded the Phase A package to the handbook §2.5 module map,
implementing the fully-specified **pure** functions for real and leaving typed stubs
(`NotImplementedError` citing the handbook) for the OTP/IO pieces.

- **Implemented + tested:** `config.py` (strict YAML contract, unknown-key rejection,
  `departure_time` enforcement §8.3); `scoring/objective.py` (`J`, degenerate `Q₀.₈`),
  `scoring/creativity.py` (`C(r)` formula), `scoring/robustness.py` (lexicographic key);
  `routing/dominance.py` (Pareto/`is_dominated`), `routing/deepening.py` `route_signature`
  (feeder hub in identity); `portfolio/output.py` (canonical JSON, `from_`→`"from"`),
  `portfolio/card.py` (`build_card` with §4.1 last-mile transfer exclusion); `cli.py`
  (`rro plan`, exit codes 0/2/3/4).
- **Stubbed:** `data/ingest`+`feeds`, `graph/build`+`otp_client`, `routing/decompose`+`hubs`,
  `scoring` geometry, `portfolio/cluster` (with `UnderfullPortfolioError` for the §7.1 floor).
- **Packaging:** `pyproject.toml` (MIT, `rro` entry point, pytest `pythonpath=src`).
- **Test fixtures:** `data/sample/`, `src/rro/tests/golden/`, `…/data/broken/` with READMEs
  describing the frozen-GTFS / golden-portfolio / negative-feed fixtures (handbook §3.3, §8.4).

**Verification:** `python -m pytest` → **28 passed**. Tests cover config strictness, the §2.8
`J` rounding example (`309.0 − 0.7·0.58 = 308.6`), `C(r)`, robustness ordering, dominance
(incl. mode-tie retention), `route_signature` (different hubs → different signatures), and the
last-mile transfer-exclusion + `"from"` serialisation. End-to-end: a real YAML config loads,
the CLI returns exit `2` on config errors, and a valid config reaches the pipeline stub.

**Status:** README Phase A row → "Scaffold + unit tests; B1–B4 pipeline pending". Next:
fill the routing→scoring→clustering pipeline and produce the first golden-route portfolio.

---

## 2026-06-05 — Scaffold review response (contract edges)

Review of the scaffold flagged four contract edges; all fixed before building the pipeline:

- **CLI traceback (major).** A valid `rro plan` raised `NotImplementedError` (exit 1 via uncaught
  traceback, outside the documented codes). Now returns a documented diagnostic: added
  `EXIT_NOTIMPL = 1` to `cli.py` and to handbook §8.1, printed cleanly to stderr.
- **Config type validation (major).** `config.py` rejected unknown keys but not wrong types.
  Added scalar type/range/ISO checks (`origin` non-empty str, `t_first_minutes`/`depths` positive
  int, `alpha_c ≥ 0`, `quantile ∈ (0,1]`, `accessibility_required` bool, ISO-8601 `departure_time`,
  feed field types). `--depart` overrides are ISO-validated too.
- **Dominance string compare (major).** `routing/dominance.py` compared `arrival_time` strings
  lexicographically — wrong across UTC offsets and midnight. Now parses ISO 8601 to offset-aware
  `datetime` before comparison; `HubArrival.arrival_time` documented as ISO. Added regression tests
  (cross-offset + cross-midnight) that fail under string compare.
- **`creativity_from_km` bound (minor).** Claimed `[0,1]` but didn't enforce it. Now raises
  `ValueError` on negative inputs or `reference_km > backbone_km` (tolerating FP overshoot), so the
  result is always in `[0,1]` (handbook §6.3).

**Verification:** `python -m pytest` → **51 passed** (was 28; +23). New: config type/range/ISO
cases, CLI exit-code contract (0/1/2 paths), absolute-time dominance, creativity bounds. Manually
reproduced the reviewer's bad-type configs (`origin: 42`, `departure_time: tomorrow`, feed
`url: 123`) — all now rejected with exit 2; a valid plan exits 1 with no traceback.

---

## 2026-06-05 — Scaffold review response (round 2: validation holes)

Follow-up review found two gaps left by round 1; both closed:

- **CLI overrides bypassed validation (major).** `--alpha-c -1`, `--epsilon -5`, `--quantile 2`
  were written onto the loaded Config after `parse_config`, so they reached the pipeline (exit 1)
  instead of failing validation. Added `validate_config(cfg)` (re-checks scalar ranges on a
  Config object) and call it in `cmd_plan` after overrides → exit 2.
- **Offset not enforced (major).** `validate_departure` accepted naive ISO datetimes
  (`2026-06-08T07:30:00`). Now requires `tzinfo` (UTC offset); `dominance._arrival` likewise
  rejects naive `HubArrival.arrival_time` with a clear error instead of a later `TypeError`.
- **`--epsilon` wording (minor).** Handbook §8.3 claimed `--epsilon` overrides either component;
  narrowed to: `--epsilon` overrides `epsilon.time_min`, `epsilon.creativity` is config-only —
  matching the implemented CLI.

**Verification:** `python -m pytest` → **61 passed** (+10). Reproduced the reviewer's cases:
`--alpha-c -1` / `--epsilon -5` / `--quantile 2` and a naive `departure_time` all now exit 2.

With the CLI/config boundary hardened, the next move is **track 1**: implement `portfolio/cluster.py`
(B4) against hand-built scored candidates, exercise underfull/tie-break/collapse, and serialise the
first synthetic portfolio — locking the B4→Layer C seam before any OTP wiring.

---

## 2026-06-05 — Scaffold review response (round 3: non-finite numbers)

- **NaN/Inf bypassed range checks (major).** Every comparison against `NaN` is false, so
  `--alpha-c nan`, `--epsilon nan`, `--quantile nan` (and YAML `.nan`/`.inf`) passed validation.
  Added `math.isfinite` to `_check_number`, which covers both the YAML and CLI paths (shared
  validator). `Inf` is rejected too.
- **§8.1 precedence wording (minor).** "all other parameters come from corridor.yml" contradicted
  the `--alpha-c/--epsilon/--quantile` overrides listed next; reworded to list the calibration
  overrides explicitly and note they are re-validated (exit 2).

**Verification:** `python -m pytest` → **69 passed** (+8). Reproduced: CLI `nan`/`inf` overrides and
YAML `.nan` all exit 2.

---

## 2026-06-05 — Track 1: B4 clustering + synthetic golden portfolio

Implemented `portfolio/cluster.py` (B4) against hand-built `ScoredCandidate`s — locking the
B4→Layer C seam before any OTP wiring.

- **Algorithm.** Found that naive precedence-greedy mis-assigns: with 3 routes, `low_transfer`
  would grab the creative route before `creative`. Implemented **iterative claim resolution**
  instead — each cluster nominates its best unassigned route; a contested route goes to the
  highest-precedence nominator (`fastest → robust → low_transfer → creative`); losers re-nominate;
  clusters with no distinct route are dropped (min 2, max 4); <2 distinct → `UnderfullPortfolioError`
  (exit 4). This reproduces the §7.2 outcome (fastest/robust/creative, low_transfer dropped).
- **Handbook §7.1 step 3** realigned from the ill-defined "largest margin" to the implemented
  precedence rule (the "fixed precedence" line was already authoritative); added `ScoredCandidate`
  to `models.py`.
- **Synthetic golden.** `src/rro/tests/golden/expected_portfolio.json` (202 lines) built from the
  real clustering + serialisation, with a fixed `generated_at`. `test_golden_portfolio_matches`
  regenerates and diffs it — the regression guard for the B4→Layer C output.

**Verification:** `python -m pytest` → **77 passed** (+8). New: underfull (incl. signature
collapse), 2→2 precedence order, 3→fastest/robust/creative, direct-contest precedence,
4-strategy cap, golden match + card invariants.

**Next:** the IO track — OTP 2.x graph build, GTFS/OSM ingest, `otp_client` GraphQL — feeding
real candidates into this now-stable B4→Layer C output.

---

## 2026-06-05 — Track 1 review response (deterministic collapse)

- **Duplicate-signature collapse was input-order dependent (major).** `_distinct` only replaced
  on strictly-faster `E_T_eff_min`, so a bus-first vs taxi-first ordering of two same-backbone
  same-time candidates changed the emitted card (risk/price) — breaking the byte-stable seam and
  ignoring §4.3's lower-risk-first-mile rule. Added `_collapse_key = (E_T_eff_min, taxi-risk,
  stable-leg-key)`: faster wins; on a tie the non-taxi feeder wins (taxi survives only when
  strictly faster); fully order-independent.
- **Two cluster-order constants (minor).** `models.CLUSTERS` (§B4 catalogue order) vs
  `cluster.CLUSTER_PRECEDENCE` (tie/output order) could drift. Added a module-load `assert` that
  they (and `CLUSTER_LABELS`) cover the same ids, plus a test, and clarified the comments.

**Verification:** `python -m pytest` → **81 passed** (+4): collapse prefers non-taxi under both
input orders, keeps taxi when strictly faster, constants consistent. The synthetic golden is
byte-identical (collapse only affects duplicate signatures).

---

## 2026-06-05 — IO track item 1: OTP GraphQL `plan` client

First IO module. Implemented `graph/otp_client.py` against recorded responses — no live OTP needed.

- **Collapse total-order patch first.** `_collapse_key` now tie-breaks over every emitted field
  (full legs incl. slack, whole score, price, warning, `None` ordered last), so same-backbone
  candidates differing only in price are order-independent.
- **OTP client.** `PLAN_QUERY` (GTFS GraphQL, scheduled search per §5.2), a response parser
  (`parse_itinerary`/`parse_leg` → `OTPItinerary`/`OTPLeg`, epoch-ms → offset-aware UTC), and a thin
  `OTPClient` with an **injectable transport** (default urllib POST). Error paths normalised to
  `OTPError` (→ CLI exit 3): GraphQL `errors`, null `plan`, non-dict response, transport exceptions.
  `isochrone` (hub discovery, §4.2) left as a stub — different OTP API.

**Verification:** `python -m pytest` → **92 passed** (+11 over 81: +2 collapse price tie-break,
+9 OTP client — parsing, time conversion, variable construction, empty/`errors`/null-plan/non-dict/
transport-exception paths).

**Next (IO):** `data/feeds.py` + `data/ingest.py` (registry + fetch over a trimmed corridor sample),
then `routing/hubs.py` + `decompose.py`, then wire `routing/deepening.py` to the client + dedup pool.

---

## 2026-06-05 — OTP client review response + schema research

Review flagged two client majors + an open question (pin `plan` vs migrate to `planConnection`).

- **`searchWindow: Int → Long` (major).** Matches OTP's GTFS GraphQL schema; the `Int` form could
  be rejected live. Already landed in `e92358e`.
- **Parse errors → `OTPError` (major).** Leg missing `mode`, null/non-list `legs`, non-numeric
  times, non-object itinerary/leg now normalise to `OTPError` (exit 3). Landed in `e92358e`.
- **Open question resolved by research (workflow, 4 agents, primary sources).** Verified against the
  OTP dev-2.x GTFS GraphQL schema files + Changelog: `plan.searchWindow` is **Long, integer
  seconds**; the `plan` query is **deprecated since 2.7.0 but not removed** in any 2.x (functional
  through 2.9.0); `planConnection` would add relay pagination + ISO-8601 `Duration` for no Phase A
  benefit. **Decision: keep `plan`, pin OTP 2.9.0.** Applied: `transportModes` corrected to
  `[TransportMode]` (was `[TransportMode!]` — a live-reject bug); `OTP_PINNED_VERSION = "2.9.0"`;
  handbook §1.3/§3.5 pin 2.9.0 with the deprecation rationale. Deprecated epoch-ms `startTime`/
  `endTime` kept (functional; absolute instant is correct for dominance) — migration to
  `planConnection` + `OffsetDateTime` leg-times noted as a forward-hook behind the client seam.

**Verification:** `python -m pytest` → **97 passed**; query schema-type assertions added.

**Next (IO):** `data/feeds.py` + `data/ingest.py` over a trimmed corridor sample.

---

## 2026-06-05 — IO track items 2–3: feed registry + GTFS/OSM ingestion

Two seam-polish items closed first (committed `a1f407c`): `_execute` now normalises non-list /
non-dict GraphQL `errors`; missing/null `plan.itineraries` raises `OTPError` (empty `[]` stays a
valid no-routes result); handbook §5.2 query sketch refreshed to match the implemented seam.

Then implemented `data/feeds.py` + `data/ingest.py` (handbook §3.2/§3.3):

- **`feeds.py`** — `FeedRegistry.from_feeds` splits ≥1 GTFS + exactly one OSM PBF; exposes `all()`
  (OSM last) and `osm_bbox`.
- **`ingest.py`** — `ingest_feed`/`ingest_feeds` with an **injectable downloader** (offline tests),
  cache keyed by `(id, version_pin)` (idempotent — no re-download), sha256 pinning (real digests
  verified, `<digest>` placeholders skipped), structural `validate_gtfs` (valid zip + required files
  + service calendar; basenames so nested archives pass) and light `validate_osm` (non-empty +
  `OSMHeader`). ERROR findings abort via `IngestError` (exit 2); `to_lockfile`/`write_lockfile` for
  reproducibility.

**Verification:** `python -m pytest` → **114 passed** (100 → +14: 3 registry, 11 ingestion incl.
caching, sha mismatch, missing-file abort, fetch-failure normalisation, OSM header). All offline.

**Next (IO):** `routing/hubs.py` + `routing/decompose.py` (B1/B2 over OTP responses), then wire
`routing/deepening.py` (Depth 0/1/2 + dedup pool) — at which point the pipeline runs end-to-end and
the synthetic golden is replaced by one over the `data/sample/` fixture.

---

## 2026-06-05 — Ingestion review response (cache safety + real validation)

Review flagged three ingestion majors; all fixed so bad inputs fail cleanly at ingest, not later in OTP.

- **Cache poisoning (major).** `dest.exists()` alone could keep a partial/stale file forever. Now:
  download to a `.part` temp + **atomic rename** (a failed/partial fetch leaves nothing usable), and
  skip the download only when the cached file exists **and** matches a pinned real `sha256` — a stale
  cache that fails its pin is re-fetched.
- **Shallow GTFS validation (major).** A zip with the right filenames but junk contents used to pass.
  `validate_gtfs` now parses the CSVs and checks **referential integrity** (`trips`→routes/services,
  `stop_times`→trips/stops) and **strictly increasing `stop_sequence`** per trip. (Documented as a
  fast in-process pre-flight; the MobilityData gtfs-validator remains the canonical full check for
  large national archives, §3.3.)
- **Non-PBF OSM (major).** Missing `OSMHeader` is now an **ERROR** (was WARNING), so a non-PBF file
  can't reach graph build; deeper checks (way/node counts, bbox coverage) explicitly deferred.
- Handbook §3.3 updated to match (atomic fetch + sha-gated cache; the deeper GTFS checks; OSM header
  ERROR + deferred PBF parsing).

**Verification:** `python -m pytest` → **119 passed**. New: dangling stop/service refs, non-monotone
`stop_sequence`, non-PBF OSM ERROR, no-partial-on-fetch-failure, stale-cache-vs-pin re-download.

**Next (IO):** `routing/hubs.py` + `routing/decompose.py` — translate `OTPItinerary`/`OTPLeg` into the
domain model (`Leg` with B1 layer tags, `HubArrival` for B2), the bridge to the pure pipeline.

---

## 2026-06-05 — IO bridge: B1 decomposition + B2 hub-arrival parsing

One stale handbook sentence patched first: §8.4 no longer claims date-aware service-calendar coverage
(the validator only checks `service_id`s are defined); date-coverage marked deferred.

Then the OTP→domain bridge — `routing/decompose.py` + `routing/hubs.py`, built against constructed
`OTPItinerary`/`OTPLeg` objects (and one full path through the real `parse_itinerary`):

- **`decompose.py`** — `decompose(itinerary, tz=None)` tags each leg with its B1 layer (backbone =
  the first→last `RAIL` span; before = `first_mile`, after = `last_mile`; ends-at-rail-hub ⇒ no
  last-mile; no-rail falls back to the transit span) and emits domain `Leg`s with per-leg slack and
  optional tz localisation. `feeder_hub(legs)` = first backbone board stop.
- **`hubs.py`** — `hub_arrival(itinerary)` builds a `HubArrival` (hub = final stop, transfers =
  transit legs − 1, first-mile mode, offset-aware arrival); `hub_arrivals(itineraries, t_first)`
  filters by reachability and feeds the existing `dominance.pareto_frontier`. The exhaustive OTP
  isochrone enumeration stays a documented stub (distinct OTP API).

**Verification:** `python -m pytest` → **131 passed** (+12): layer tagging variants, tz localisation,
real-parser path; hub-arrival fields, transfer counting, T_first filtering, and dominance over parsed
hub arrivals.

**Next (IO):** `routing/deepening.py` — wire Depth 0/1/2 to the OTP client + the dedup pool
(`route_signature` already exists), and `graph/build.py`. Then the pipeline runs end-to-end and the
synthetic golden is replaced by one over the `data/sample/` fixture.

---

## 2026-06-05 — Bridge review response (boundary safety)

Three boundary issues that would amplify under deepening, all fixed:

- **decompose mislabelled segments (major).** The rail-span heuristic is only valid for a complete
  route; a first-mile segment ending in a walk (`BUS origin→stop, WALK stop→hub`) had no rail and was
  mislabelled (bus→backbone, walk→last_mile, feeder_hub→origin). Added a `role` param
  (`door_to_door` default | `first_mile` | `backbone` | `last_mile`); segments pass their role and get
  a single layer. Unknown role raises.
- **hub_arrival accepted any itinerary (major).** A full door-to-door route would emit Freiburg as the
  hub. `hub_arrival(itinerary, t_first_minutes)` now **requires** the window and raises if the
  itinerary exceeds it (not a first-mile segment); `hub_arrivals` passes it.
- **slack banker's-rounded (minor).** `round(x)` could turn a 30 s buffer into 0. Now keeps precise
  minutes (`round(x, 2)`), so sub-minute buffers survive (0.5).

**Verification:** `python -m pytest` → **135 passed** (+4): role tagging of a walk-terminated
first-mile segment, unknown-role error, sub-minute slack, and hub_arrival rejecting a full route.

**Next (IO):** `routing/deepening.py` — Depth 0/1/2 over the OTP client + the `route_signature` dedup
pool — the last major piece before the pipeline runs end-to-end.

---

## 2026-06-05 — IO: B3 progressive-deepening controller

Implemented `routing/deepening.py` (handbook §5) — the last major algorithmic piece.

- **Refactor first:** moved the §4.1 transfer/slack semantics (`transfer_stations`, `count_transfers`,
  `min_transfer_slack`) into `decompose.py` (B1-owned); `card.py` re-exports `transfer_stations` so
  existing imports/tests are unaffected.
- **Controller:** `depth_params` (Depth 0/1/2 ladder: maxTransfers 1/2/2, budget 6/6/15, window
  ×2.5 at Depth 2); `Candidate.from_itinerary` (decompose → backbone `route_signature` + structural
  metrics); `CandidatePool` (dedup by signature, **merge** keeps the earlier arrival and records
  alternative departures, monotone-accumulating); `_improves_any` ε-termination over E[T_eff] /
  structural slack / transfers / optional C(r); `deepen(plan_fn, …)` runs the ladder and halts when a
  depth adds no improvement (Depth 0 unconditional). `plan_fn` is **injectable** — testable against
  recorded itineraries, decoupled from OTP place/coords.

**Verification:** `python -m pytest` → **145 passed** (+10): depth ladder + clamp, candidate metrics,
pool dedup/merge (both add orders), ε-termination (stop on no-new, continue while improving, stop on
sub-ε gain), monotone accumulation, empty-first-depth stop.

**Remaining for end-to-end:** `graph/build.py` (OTP graph build), `otp_client.isochrone` +
`hubs.enumerate_hubs` (hub discovery), and the top-level wiring (hub assembly → `plan_fn`, two-pass
C(r)/R calibration, scoring assembly → B4). Then the synthetic golden is replaced by one over the
`data/sample/` fixture.

---

## 2026-06-05 — Deepening review response (improvement detection + first-mile modes)

- **Deepening ignored same-signature improvements (major).** `CandidatePool.add` returned `False` on
  a duplicate signature even when the duplicate *replaced* the kept route with an earlier arrival, so
  `deepen` left the improved candidate out of `new` and ε-terminated despite a real gain (a 50-min
  improvement at Depth 1 skipped Depth 2). `add` now returns `True` on **added or improved**, so the
  improvement reaches `_improves_any`.
- **hub_arrival allowed disallowed first-mile modes (minor).** A 20-min `RAIL` itinerary became
  `first_mile_mode='rail'`. Added an allowed-mode guard (walk/bus/taxi; OTP CAR/FLEX for taxi);
  `hub_arrival` raises on a non-first-mile mode and `hub_arrivals` skips such itineraries.

**Verification:** `python -m pytest` → **149 passed** (+4): deeper-after-same-signature-improvement,
`add` improvement signalling, rail first-mile rejection, and `hub_arrivals` mode-skip.

**Next:** end-to-end wiring — hubs → `plan_fn` → `deepen` → score → cluster → output, tested offline
with a fake OTP client; then `cli.plan` produces a real portfolio over `data/sample/`.

---

## 2026-06-05 — End-to-end pipeline wired

`pipeline.plan_portfolio` now threads the whole Phase A path: hub discovery (B2) → static dominance →
progressive deepening (B3) → two-pass C(r) calibration → scoring → B4 clustering → portfolio JSON.
Parameterised by two injectable plan functions (`hub_plan_fn`, `backbone_plan_fn`), so it runs fully
offline in tests; `otp_plan_fns(client)` builds the live OTP-backed pair.

- **Enablers:** added leg `distance` through OTP (`OTPLeg.distance`, query field, parser) → domain
  (`Leg.distance_m`, not serialised) → `decompose`; needed for backbone km / C(r).
- **Two-pass creativity (real):** `calibrate_reference` freezes the top-3 backbone signatures by km as
  R (with `leg_keys`); `creativity_of_route` / `reference_km_of` measure leg-level overlap. `_corridor_id`
  slugs the hub chain.
- **Scoring assembly:** `scoring/assemble.score_route` → `ScoredCandidate` with the canonical `Score`;
  `creativity` derived from the rounded `backbone_km`/`reference_km` so the §2.8 invariant holds exactly.
- **Refactor:** the §4.1 transfer/slack helpers already moved to `decompose` (B1) last commit are reused.
- **CLI:** `cmd_plan` now calls `plan_portfolio` (OTP-backed); `--otp-url` added; exit codes wired
  (4 underfull, 3 OTP, 1 not-implemented), `--card` renders the §7 table. Live path stops cleanly at the
  isochrone stub (exit 1).

**Verification:** `python -m pytest` → **156 passed** (+7). New: creativity calibration / overlap /
slug determinism; end-to-end pipeline producing a 4-strategy portfolio (fastest/robust/low_transfer/
creative) over a hand-built fixture, scoring invariants, and a **pipeline golden**
(`expected_pipeline_portfolio.json`). Smoke: `rro plan` reaches the pipeline and exits 1 at isochrone.

**Remaining for a live run:** `graph/build.py` (OTP 2.9.0 graph build) and `otp_client.isochrone` +
`hubs.enumerate_hubs` (one-to-many hub discovery) — then `rro plan` produces a real portfolio against a
served OTP instance over the `data/sample/` fixture.

---

## 2026-06-05 — Pipeline review response (deterministic collapse + OTP place contract)

- **Same-backbone collapse order-dependent again (major).** `deepen` collapses same-signature
  duplicates *before* B4, so B4's total-order `_collapse_key` was bypassed and a bus-first vs
  taxi-first ordering changed the emitted card risk. `CandidatePool.add` now breaks an **equal-arrival**
  tie deterministically via `_collapse_pref` (non-taxi over taxi, then stable leg key) — taxi survives
  only when strictly faster (§4.3), independent of input order; ε-termination still triggers only on a
  strictly-earlier arrival.
- **OTP place contract (major).** The pipeline passed hub/destination **strings** to `OTPClient.plan`,
  which only accepted coordinates. Extended `plan` to route strings to `fromPlace`/`toPlace` (OTP stop
  id `FeedId:StopId` or `"lat,lon"`) and coordinates to `from`/`to` (now nullable, per the OTP schema);
  handbook §5.2 query synced. Documented in `otp_plan_fns` that live use needs `HubArrival.hub_id` /
  `config.destination` to be resolvable stop ids (a live-OTP precondition).

**Verification:** `python -m pytest` → **160 passed** (+4): pool non-taxi-on-equal-arrival (both
orders) + taxi-when-strictly-faster; end-to-end bus-first/taxi-first → identical card; OTP place
identifiers via fromPlace/toPlace. Both goldens byte-identical.

---

## 2026-06-06 — Milestone: Phase A engine algorithmically complete (offline)

Marking a clean boundary. The Phase A engine is implemented, tested, and regression-guarded
end-to-end **offline** (two independent reviews concur, no blocking findings on `c511751`).

**Done (all under `src/rro/`, 160 tests, no skips):** strict config; B1 decomposition; B2 hub
discovery + static dominance; B3 progressive deepening (depth ladder, dedup pool, ε-termination,
deterministic collapse); scoring (deterministic `J`, two-pass `C(r)`/R, structural-robustness proxy);
B4 clustering; canonical JSON + §7 cards; the OTP GraphQL `plan` client (pinned OTP 2.9.0, injectable
transport); feed registry + GTFS/OSM ingestion (atomic cache, structural validation); and the
`plan_portfolio` pipeline. Two goldens (B4-level + full-pipeline) lock the output.

**Remaining = live-OTP infrastructure (a different context: JVM / feeds / OSM), NOT new algorithms:**

1. Stand up OTP 2.9.0 and build a graph from the pinned corridor GTFS + OSM PBF (`graph/build.py`).
2. Implement `otp_client.isochrone` + `hubs.enumerate_hubs` (one-to-many hub discovery).
3. Make `origin`/`destination` and `HubArrival.hub_id` resolvable OTP places (stop ids / coords) for
   the live run — see the §2.6 / §3.5 precondition.
4. Replace the synthetic pipeline golden with one captured from real OTP responses over `data/sample/`.

Parked here intentionally; the live integration is the focused next session.

---

## Future entries

Append new operational entries below as the project progresses.
