---
layout: default
title: "Phase C — Logger"
---

# Handbook: Phase C — Historical Logger and Conditioning

**Status:** Planned

This handbook will cover the Phase C historical data layer:

- SQLite schema for the corridor logger
- Asynchronous GTFS-RT polling daemon (30s interval)
- Weather co-logging (Bright Sky integration)
- Structural state co-logging (G′ snapshot per poll)
- Data custodianship protocol (90-day raw, aggregates permanent)
- Feature engineering: ρ\_disruption, S\_node, P(connection | Δt)
- Hierarchical feature model (Tier 1 → 2 → 3 → regression)
- Monte Carlo integration with empirical CDFs
- Calibration workflow (α\_RT, α\_C, quantile level)
- B4 calibration freeze protocol
- B5/B6/B7 falsification logging and monitoring
- Bootstrap from Bahn-Vorhersage / piebro archives
- Weather backfill from Open-Meteo ERA5

**Prerequisite:** [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) (§3, §5 Phase C)
