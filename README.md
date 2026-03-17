# Robust Route Optimiser (RRO)

**State-dependent multimodal routing for robust travel decisions.**

[![Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://uwarring82.github.io/robust-route-optimiser/)
[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)

---

## What is this?

RRO is a personal route-planning framework for the corridor **Haßlinghausen → Freiburg (Breisgau)**. It goes beyond standard journey planners by:

- treating the transport graph as **state-dependent** — topology changes with weather, infrastructure, and disruptions
- searching for a **portfolio of strategies** (fastest, most robust, most creative, fewest transfers) rather than a single "best" route
- conditioning travel-time predictions on **observable system load** (weather, demand, node-stress) without relying on sensitive social data
- separating **forecast robustness** (how good is the prediction?) from **decision robustness** (how resilient is the route?)

The framework is designed for a specific corridor but the architecture generalises to any peripheral-to-core network geometry.

## Project structure

```
robust-route-optimiser/
├── docs/                          # Published documentation (GitHub Pages)
│   ├── index.md                   # Landing page
│   ├── coastline/                 # Stable framework architecture
│   │   └── rro-coastline-v0.6.0-rc1.md
│   ├── handbook/                  # Implementation handbooks
│   │   ├── phase-a-engine.md      # (planned)
│   │   ├── phase-b-state-graph.md # (planned)
│   │   └── phase-c-logger.md     # (planned)
│   └── notes/                     # Design log and open sketches
│       └── design-log.md
├── src/                           # Engine code (future)
├── data/sample/                   # Small example data (never raw bulk)
├── .github/workflows/pages.yml    # GitHub Pages deployment
├── README.md                      # This file
└── LICENSE
```

## Documentation

The canonical documentation is published via GitHub Pages:

**→ [uwarring82.github.io/robust-route-optimiser](https://uwarring82.github.io/robust-route-optimiser/)**

### Key documents

| Document | Status | Description |
|---|---|---|
| [Coastline v0.6.0-rc1](docs/coastline/rro-coastline-v0.6.0-rc1.md) | **Freeze candidate** | Core architecture: objective function, signal taxonomy, graph model, boundaries B1–B7 |
| Handbook: Phase A Engine | Planned | OTP integration, progressive deepening, portfolio clustering |
| Handbook: Phase B State Graph | Planned | Real-time signals, G′ construction, weather overlay |
| Handbook: Phase C Logger | Planned | GTFS-RT daemon, SQLite schema, feature engineering |

## Harbour context

RRO is part of the [Open-Science Harbour](https://uwarring82.github.io/me). It follows Harbour conventions:

- **Endorsement Marker** on every framework document (local stewardship, no external endorsement claimed)
- **Coastline / Handbook separation** — stable architecture vs. implementation detail
- **Falsifiable boundaries** (B1–B7) with explicit metrics and thresholds
- **Class D exclusion** of sensitive social variables, protected by formal Exception Protocol
- **Council-3 ADM-EC** deliberative process for architectural decisions

## Status

| Phase | Status |
|---|---|
| Coastline architecture | ✅ v0.6.0-rc1 freeze candidate |
| Phase A — Static prototype | 🔲 Not started |
| Phase B — Real-time + G′ | 🔲 Not started |
| Phase C — Historical conditioning | 🔲 Not started |

## Licence

Documentation: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Code (future): TBD — will be specified when `src/` is populated.

## Author

**Ulrich Warring**
Physikalisches Institut, Albert-Ludwigs-Universität Freiburg

*High impact, no fame.*
