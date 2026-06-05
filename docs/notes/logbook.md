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

## Future entries

Append new operational entries below as the project progresses.
