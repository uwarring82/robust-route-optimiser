# Contributing to the Robust Route Optimiser

Thank you for your interest. RRO is a personal research framework under **local
stewardship** (U. Warring), developed within the conventions of the
[Open-Science Harbour](https://uwarring82.github.io/me). It is openly licensed and
openly developed; contributions, corrections, and challenges are welcome within the
process described here.

## Ways to contribute

- **Falsification challenges.** The framework rests on falsifiable boundaries **B1–B7**
  (see the [Coastline](docs/coastline/rro-coastline-v0.6.0-rc1.md), §Novel Boundaries). If
  you can show a boundary's metric or threshold is wrong, ill-posed, or unmet, open an
  issue labelled `falsification` with the boundary id and your reasoning or data.
- **Corrections.** Typos, broken links, unclear prose, or errors in the documentation —
  open an issue or a small pull request.
- **Open questions.** The [Design Log](docs/notes/design-log.md) lists open questions
  (OTP vs. Hafas, taxi-heuristic calibration, B7 sample size, Flixbus GTFS, scope). Input
  on any of these is valuable — comment via an issue.
- **Code** (once `src/` exists). Engine contributions for Phases A–C.

## How decisions are made

Architectural decisions follow the Harbour **Council-3 (ADM-EC)** deliberative process
(Guardian / Architect / Scout stances). Two layers, different bars for change:

| Layer | What it is | To change it |
|---|---|---|
| **Coastline** (`docs/coastline/`) | *What the system is and why* — objective function, signal taxonomy, boundaries B1–B7 | Requires deliberation and a version bump; recorded in the [Design Log](docs/notes/design-log.md) |
| **Handbook** (`docs/handbook/`) | *How the system is built* — implementation detail | May change freely without a coastline amendment |

Propose coastline-level changes as an issue first so they can be deliberated before a PR.

## Conventions

- **Design Log** ([docs/notes/design-log.md](docs/notes/design-log.md)) records *architectural*
  decisions (date, decision, stance). **Logbook** ([docs/notes/logbook.md](docs/notes/logbook.md))
  records *operational* steps (housekeeping, infrastructure, releases, FAIR). Add an entry
  when your change belongs in either.
- **Class D exclusion.** Sensitive social variables are excluded by design and protected by
  a formal Exception Protocol (Coastline). Do not introduce them without invoking that protocol.
- **Sample data only.** Never commit raw bulk data. Small illustrative samples go in
  `data/sample/`; raw/large data is git-ignored.
- **Commits / PRs.** Use clear, imperative commit subjects. Keep PRs focused; describe the
  *why*, and reference the boundary or open question they address.

## Documentation build

Documentation is [Jekyll](https://jekyllrb.com/), built from `./docs` and deployed to GitHub
Pages on push to `main`. To preview locally:

```bash
cd docs && bundle exec jekyll serve   # http://localhost:4000/robust-route-optimiser/
```

## Licensing of contributions

This project is dual-licensed (see [README](README.md#licence)). By contributing you agree
that your contributions are licensed accordingly:

- **Documentation** under [CC BY-SA 4.0](LICENSE)
- **Code** under [MIT](LICENSE-CODE)

## Contact

Open an issue, or reach the steward via the
[Open-Science Harbour](https://uwarring82.github.io/me).

*Local stewardship: U. Warring. Not externally endorsed. Framework under development.*
