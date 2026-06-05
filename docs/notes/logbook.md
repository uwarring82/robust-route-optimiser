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

**Context.** First implementation handbook. Moves [Phase A — Static Engine](phase-a-engine)
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

## Future entries

Append new operational entries below as the project progresses.
