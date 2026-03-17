---
layout: default
title: Home
---

# Robust Route Optimiser

*State-dependent multimodal routing for robust travel decisions.*

---

## Architecture

The RRO operates on a **state-dependent transport graph** G′ that mutates in response to weather, infrastructure, and disruptions. It searches for a **portfolio of strategies** — not a single "best" route — ranked by a quantile-based objective function with creativity reward.

The framework distinguishes **forecast robustness** (prediction accuracy) from **decision robustness** (structural resilience) and keeps these architecturally separate throughout the pipeline.

---

## Documents

### Coastline (stable architecture)

The coastline defines *what the system is and why*. It contains falsifiable boundaries (B1–B7), the signal taxonomy (A/B/C), and the objective function.

→ **[Coastline v0.6.0-rc1]({{ site.baseurl }}/coastline/rro-coastline-v0.6.0-rc1)** — Freeze candidate

### Handbooks (implementation)

Handbooks define *how the system is built*. They are subordinate to the coastline and may change without coastline amendment.

| Handbook | Status |
|---|---|
| [Phase A — Static Engine]({{ site.baseurl }}/handbook/phase-a-engine) | Planned |
| [Phase B — State Graph]({{ site.baseurl }}/handbook/phase-b-state-graph) | Planned |
| [Phase C — Logger]({{ site.baseurl }}/handbook/phase-c-logger) | Planned |

### Design Log

Working notes, open questions, and deliberation records.

→ **[Design Log]({{ site.baseurl }}/notes/design-log)**

---

## Signal Processing Pipeline

```
G_base  →  [C: binary gates]  →  G″  →  [B: structural]  →  G′  →  [A: continuous via MC]  →  T_eff
```

| Signal | Type | Effect |
|---|---|---|
| NINA warning, line closure | **C — Binary gate** | Removes corridors |
| Baustelle, elevator, modal availability | **B — Structural** | Modifies topology |
| Weather, demand, traffic, events | **A — Continuous** | Adjusts delay distributions |

---

## Portfolio Output

| Strategy | Label | Criterion |
|---|---|---|
| Fastest | „Schnellste" | Lowest E[T\_eff] |
| Most robust | „Sicherste" | Lowest Q₀.₉₅(T\_eff) |
| Most creative | „Überraschung" | Highest C(r) |
| Low transfer | „Entspannt" | Fewest transfers |

---

## Status

| Component | Status |
|---|---|
| Coastline architecture | ✅ v0.6.0-rc1 |
| Phase A — Static prototype | 🔲 Not started |
| Phase B — Real-time + G′ | 🔲 Not started |
| Phase C — Historical conditioning | 🔲 Not started |

---

## Harbour

RRO is part of the [Open-Science Harbour](https://uwarring82.github.io/me). Local stewardship only. Not externally endorsed.

*Ulrich Warring · Physikalisches Institut, Universität Freiburg*
