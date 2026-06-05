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

- [x] **F** — Added `CITATION.cff` (author, version, keywords, repo URL) → enables GitHub
      "Cite this repository" + machine-readable citation. *(ORCID still TODO.)*
- [x] **F** — Added `.zenodo.json` deposition metadata + DOI badge placeholder in README.
      *(Activation steps below.)*
- [x] **A** — Landing page + licenses openly reachable (Pages live from `./docs`, licenses stated).
- [x] **I** — Added `codemeta.json` (CodeMeta 3.0 / schema.org software metadata).
- [x] **R** — Code license decided (**MIT**) and added as `LICENSE-CODE`; README licence section updated.
- [x] **R** — Re-added `.gitignore`.
- [x] **Hygiene** — README "Project structure" synced with reality.
- [ ] **R** — Optional: add `CONTRIBUTING.md` (governance currently via Harbour Council-3).

**Zenodo activation (manual, when ready to mint a DOI).**

1. Sign in at [zenodo.org](https://zenodo.org) with GitHub; flip the toggle for
   `uwarring82/robust-route-optimiser` on the Zenodo *GitHub* page.
2. Create a GitHub **release** (e.g. tag `v0.6.0-rc1`). Zenodo reads `.zenodo.json` and
   archives the tarball, minting a version DOI + a concept DOI.
3. Replace the placeholder DOI badge in `README.md` with the concept-DOI badge (template
   is in an HTML comment right above it) and add `doi:`/`identifiers:` to `CITATION.cff`.

**Open follow-ups.**

- ORCID iD needed for `CITATION.cff` / `.zenodo.json` / `codemeta.json` (Findable metadata).
  Add it and uncomment the `orcid:` line in `CITATION.cff`.

---

## Future entries

Append new operational entries below as the project progresses.
