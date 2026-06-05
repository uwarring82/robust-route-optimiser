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

## Future entries

Append new operational entries below as the project progresses.
