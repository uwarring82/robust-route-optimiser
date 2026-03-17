---
layout: default
title: "Phase B — State Graph"
---

# Handbook: Phase B — State-Dependent Graph

**Status:** Planned

This handbook will cover the Phase B real-time and state-dependent graph layer:

- Signal ingestion (GTFS-RT, NINA, Bright Sky, DB facility APIs)
- Graph mutation pipeline: G\_base → [C] → G″ → [B] → G′
- Binary gate processing (C1, C2 + density detector)
- Structural constraint processing (Baustellen, elevator, modal availability)
- Escape-vector protocol
- Shadow capacity rule
- Weather overlay with aggregation protocol
- Real-time correction with α\_RT temporal decay
- Situational dominance with temporal decoupling
- Streaming G″ update protocol
- Accessibility profiles
- Comfort layer (DB Lounge, BahnCard)

**Prerequisite:** [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) (§3, §5 Phase B)
