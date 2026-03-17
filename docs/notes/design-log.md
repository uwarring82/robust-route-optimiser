---
layout: default
title: "Design Log"
---

# Design Log

Working notes, deliberation records, and open questions for the Robust Route Optimiser.

---

## 2026-03-17 — Coastline deliberation (v0.1.0 → v0.6.0-rc1)

The coastline was developed through six iterations in a single Council-3 session, with Guardian, Architect, and Scout stances contributing corrections at each stage.

### Key architectural decisions

| Version | Decision | Stance |
|---|---|---|
| v0.2.0 | Objective → Q₀.₈ quantile (eliminates double-counting) | Guardian |
| v0.2.0 | Creativity reference externalised (two-pass protocol) | Guardian |
| v0.3.0 | Exogenous system-load conditioning (B5) | Guardian |
| v0.3.0 | "Observable system load, not cause model" principle | Guardian |
| v0.4.0 | Symbol collision resolved (α\_C, α\_RT) | Architect |
| v0.4.0 | Pipeline architecture (Layer A/B/C) | Architect |
| v0.4.0 | MC computational constraint (no graph search in loop) | Architect |
| v0.4.0 | α\_RT temporal decay | Architect |
| v0.4.0 | Hierarchical feature model | Architect |
| v0.4.0 | Class D Exception Protocol | Scout |
| v0.5.0 | Signal Type Taxonomy (A/B/C) | Functional review |
| v0.5.0 | State-dependent graph G′ | Functional review |
| v0.5.0 | B7 — graph architecture as falsifiable claim | Functional review |
| v0.6.0 | Escape-vector protocol | Architect |
| v0.6.0 | Density detector for GTFS-RT cascades | Scout |
| v0.6.0 | Accessibility profile inversion | Scout |
| v0.6.0 | Fallback validity conditions | Scout |
| v0.6.0 | Dual robustness (forecast vs. decision) | Guardian |
| v0.6.0-rc1 | B4 conjunctive falsification | Scout |
| v0.6.0-rc1 | Streaming G″ update (pipeline abort) | Scout |
| v0.6.0-rc1 | Wait-comfort layer (DB Lounge, BahnCard) | User requirement |
| v0.6.0-rc1 | Creativity drift mitigation (R-blending) | External review |
| v0.6.0-rc1 | MVP slice table | External review |

### Open questions

- **Hafas dependency:** Will OTP be fast enough for dominance-filtered hub search, or is DB Hafas needed?
- **Taxi heuristic validation:** How to calibrate the time-of-day availability model for Haßlinghausen specifically?
- **B7 sample size:** Will there be enough C-signal events in 12 months for meaningful falsification?
- **Flixbus GTFS:** How to supplement GTFS-DE with Flixbus data?
- **Scope expansion:** Should the framework be generalised beyond Haßlinghausen → Freiburg before or after Phase A validation?

---

## Future entries

Design log entries will be added as the project progresses through Phase A implementation and beyond.
