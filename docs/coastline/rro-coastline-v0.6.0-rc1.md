---
layout: default
title: "Coastline v0.6.0-rc1"
---

# Robust Route Optimiser — Coastline v0.6.0-rc1

---

## Endorsement Marker

| Field | Value |
|---|---|
| Framework | Robust Route Optimiser (RRO) |
| Version | 0.6.0-rc1 |
| Steward | U. Warring |
| Endorsement scope | Local stewardship only |
| External endorsement | None |
| Parent coastline | Open-Science Harbour |
| Falsifiability | See Novel Boundaries, §2 |
| Status | **Freeze candidate — Council-cleared** |

> *Local stewardship: U. Warring. Not externally endorsed. Framework under development.*

**Date:** 17 March 2026

---

## 0  Purpose and Scope

This coastline defines the architecture for a personal multimodal route optimiser for the corridor Haßlinghausen → Freiburg (Breisgau). The problem is non-trivial because the origin is not a railway node: creative selection of feeder hubs into the long-distance network is the primary lever for route quality.

The optimiser is a **state-dependent transport simulator with strategic output**. It operates on a graph that mutates in response to the physical state of the transport system and its environment. Route evaluation incorporates three functionally distinct signal types: continuous modulators (A), structural constraints (B), and binary disruption gates (C). The output is a portfolio of structurally diverse strategies.

### 0.1  Dual Robustness

The framework distinguishes two kinds of robustness:

**Forecast robustness (prediction layer):** How accurately does the model estimate the travel-time distribution T\_eff? Measured by prediction error of Q₀.₈(T\_eff) against realised arrival times. Improves with conditioning (B5), historical data (Phase C), and real-time blending (§3.3).

**Decision robustness (selection layer):** How well does the chosen route perform under disruptions not fully anticipated? A property of route structure: fewer transfers, lower node-stress, avoidance of fragile corridors. Captured through portfolio clustering (B4) and state-dependent graph G′ (B7).

J(r) captures forecast robustness. Decision robustness is structural.

### 0.2  Objective Function

```
J(r) = Q₀.₈(T_eff(r))  −  α_C · C(r)
```

| Term | Meaning | Note |
|---|---|---|
| Q₀.₈(T\_eff(r)) | 80th-percentile effective travel time | Forecast-robustness term |
| −α\_C · C(r) | Creativity bonus | Initial α\_C = 0.7; calibrated after ~20 journeys |

**Symbols:** α\_C = creativity weight. α\_RT = real-time blending weight (§3.3). Independent parameters.

**Reporting-only quantities:**

| Quantity | Meaning |
|---|---|
| E[T\_eff(r)] | Expected travel time |
| σ(T\_eff(r)) | Standard deviation |
| P\_miss(r) | Connection-miss probability |
| P\_cancel(r) | Leg-cancellation probability |
| Cost(r) | Fare |
| W(r) | Weather severity index |
| S\_node(r) | Max node-stress |
| Comfort(r) | Wait-comfort score (see §0.5) |

### 0.3  Creativity Metric

C(r) = 1 − (km on reference corridors R / total backbone km of *r*).

**Reference corridors R:** Two-pass protocol (calibration pass at α\_C = 0 → freeze top-3 → scoring pass). R versioned; updates only on structural GTFS changes.

**Creativity drift mitigation (v0.6.0-rc1):** When the GTFS feed changes structurally (new lines, discontinued services), R is re-calibrated. To prevent abrupt jumps in C(r) that could confuse the user, the new reference set R\_new is blended with R\_old over a transition window of 5 query-days:

```
R_transition(day d) = (1 − d/5) · R_old  +  (d/5) · R_new     for d ∈ [1, 5]
```

where blending means: a corridor is in R\_transition if it is in R\_old OR R\_new during the window, weighted by the day-fraction for C(r) computation. After day 5, R = R\_new fully. This ensures that "creative" routes do not suddenly become "conventional" (or vice versa) overnight.

### 0.4  MVP Slice (v0.6.0-rc1)

The architecture is designed for incremental activation. Not all components are needed from Phase A onward.

| Component | Phase A | Phase B | Phase C |
|---|---|---|---|
| G\_base (static GTFS + OSM) | ✓ required | ✓ | ✓ |
| B3 progressive deepening | ✓ required | ✓ | ✓ |
| B4 portfolio clustering | ✓ required | ✓ | ✓ |
| B2 dominance filter (static) | ✓ required | ✓ | ✓ |
| Deterministic T\_eff = T\_schedule | ✓ (only mode) | fallback | fallback |
| C-signals (NINA, closures) | — | ✓ activates | ✓ |
| B-signals (Baustellen, elevator, modal) | — | ✓ activates | ✓ |
| G′ state-dependent graph | — | ✓ activates | ✓ |
| B2 situational dominance | — | ✓ activates | ✓ |
| A-signals (weather, traffic, events) | — | ✓ (unconditional RT) | ✓ (conditioned) |
| Monte Carlo with p(ΔT \| x) | — | simplified (RT only) | ✓ full |
| Phase C logger + historical CDFs | — | — | ✓ activates |
| Hierarchical feature model | — | — | ✓ activates |
| Comfort scoring (§0.5) | optional | optional | optional |

**Phase A MVP** requires only: GTFS ingest → OTP routing with progressive deepening → deterministic scoring → portfolio clustering → JSON output. This can run as a standalone CLI tool with no external APIs beyond GTFS feeds and OSM.

### 0.5  Wait-Comfort Layer (v0.6.0-rc1)

Transfer and waiting times are not merely temporal costs — their experienced quality depends on the station environment. This layer is **reporting-only** (not part of J(r)) and **optional** in all phases.

**Comfort features per waiting leg:**

| Feature | Source | Effect |
|---|---|---|
| DB Lounge availability | DB Lounge opening hours (published) | High comfort during business hours if BahnCard status qualifies |
| BahnCard status | User configuration | Determines Lounge access (BC 100, BC 25/50 Business, bahn.bonus Gold+) |
| Platform facilities | GTFS pathways + station data | Covered waiting area, seating, food/drink |
| Waiting duration | Schedule | Short waits (< 15 min) low impact; long waits (> 45 min) high impact |

**Comfort score:** A simple ordinal per transfer station:

| Level | Condition |
|---|---|
| **High** | DB Lounge accessible (BahnCard status + opening hours match) AND wait > 30 min |
| **Medium** | Covered waiting area with seating AND food available |
| **Low** | Open platform only or unknown |

The comfort score is displayed per transfer in the portfolio view. Routes with long transfers at high-comfort stations may be preferred by the user even if J(r) is slightly worse — this is a decision-robustness factor that the user applies, not the model.

**Integration:** The comfort layer operates after Layer B (scoring) and annotates routes in Layer C (presentation). It never modifies the graph, edge weights, or the objective function. It is a pure display enrichment.

---

## 1  External Constraints (Citation Only)

### 1.1  Data Standards

| Constraint | Reference |
|---|---|
| GTFS | gtfs.org |
| GTFS Realtime | gtfs.org/realtime |
| OpenStreetMap | openstreetmap.org |
| DELFI / GTFS-DE | opendata-oepnv.de |
| DB Open Data | data.deutschebahn.com |
| VER / VRR GTFS | Regional feeds, Süd-Westfalen / Ruhr |

### 1.2  Routing Infrastructure

| Constraint | Reference |
|---|---|
| OpenTripPlanner (OTP) | opentripplanner.org |
| Valhalla | valhalla.github.io |
| RAPTOR | Delling et al. (2015) |
| Connection Scan Algorithm | Dibbelt et al. (2018) |

### 1.3  Historical Data

| Source | Note |
|---|---|
| Bahn-Vorhersage | DB Timetable API archive since 2021 |
| piebro/deutsche-bahn-data | Historical delay/cancellation |
| Own corridor logger | Planned; see Phase C |

### 1.4  Weather Data

| Source | Type | Access |
|---|---|---|
| DWD MOSMIX | 10-day forecast, hourly | opendata.dwd.de, free |
| DWD CDC | Historical observations | opendata.dwd.de |
| Bright Sky | JSON API for DWD | api.brightsky.dev, free |
| Open-Meteo | Forecast + ERA5 historical | open-meteo.com, CC BY 4.0 |
| wetterdienst | Unified Python client | pip install wetterdienst |

### 1.5  Event, Infrastructure, Safety, and Comfort Data

| Source | Signal class | Note |
|---|---|---|
| DB Baustelleninformationen | B (or C if full closure) | Speed restrictions, closures |
| OSM railway tags | B | Single-track, electrification |
| Public event calendars | A | Bundesliga, Messen, festivals |
| GTFS-RT Service Alerts | B or C (density detector) | Cancellations, closures |
| NINA / BBK Warnings | C | Civil protection alerts |
| DB Streckenagent | B or C | Line disruptions |
| Elevator/escalator status | B | Transfer accessibility |
| Road traffic | A | First-mile modulation |
| DB Lounge opening hours | Comfort | Published schedules |
| GTFS pathways / station facilities | Comfort | Platform amenities |

---

## 2  Novel Boundaries (Falsifiable, Versioned)

### B1 — Three-Layer Decomposition

**Claim:** A door-to-door route in the Haßlinghausen → Freiburg corridor decomposes *naturally* into three operational layers in the default case:

1. **First mile:** Origin → feeder hub. Modally dynamic, situationally evaluated.
2. **Backbone:** Feeder hub → Freiburg Hbf. Via progressive deepening.
3. **Last mile:** Freiburg Hbf → destination.

Working decomposition unless falsified by route structure. Relaxed to two layers if needed.

### B2 — Creative Hub Discovery with Situational Dominance

All stops within T\_first (45 min) evaluated, dominance-filtered.

**Temporal decoupling:** If t\_departure − t\_query > 2 hours, historical profiles used instead of live traffic for dominance evaluation.

**Falsification:** nearest-*k* (*k* ≤ 3) same as situational filter over > 90% of windows.

### B3 — Corridor-Agnostic Backbone Search

Progressive deepening on G′: Depth 0 (direct + 1-transfer) → Depth 1 (2-transfer) → Depth 2 (creative expansion 2.5×).

**Termination:** Halt when no new route improves any portfolio criterion beyond ε.

**Falsification:** Portfolio from full search ≡ three-corridor portfolio over > 90% of windows.

### B4 — Clustered Portfolio Output

| Cluster | Criterion | User-facing label |
|---|---|---|
| Fastest | Lowest E[T\_eff] | „Schnellste" |
| Most robust | Lowest Q₀.₉₅(T\_eff) | „Sicherste" |
| Most creative | Highest C(r) | „Überraschung" |
| Low transfer | Fewest transfers | „Entspannt" |

Min 2, max 4 strategies. Comfort annotations (§0.5) displayed per transfer.

**Dual falsification (v0.6.0, clarified in rc1):**

- **Usage indicator:** User selects same cluster > 20 journeys → triggers UX review (should portfolio still be shown?). This is a review trigger, not a falsification.
- **Performance falsification (primary, scientific):** Clustered portfolio does not improve realised arrival reliability or reduce post-selection regret relative to single-best, measured over ≥ 30 journeys. This is the falsification criterion.

Both conditions must hold simultaneously (conjunctive) for full deprecation of the portfolio. Usage concentration alone indicates preference, not failure.

**Calibration freeze protocol (v0.6.0-rc1):** When α\_C is calibrated at ~20 journeys, the B4 performance-falsification journey counter resets to zero. This ensures that post-calibration behavioural data is homogeneous and that pre-calibration route selection patterns (which may have been suboptimal due to uncalibrated α\_C) do not contaminate the falsification assessment.

### B5 — Exogenous System-Load Conditioning

**Design principle:** Model the *state of the system under load*, not the causes of disruption.

**Signal Type Taxonomy:**

| Type | Effect | Integration | Example |
|---|---|---|---|
| **(A) Continuous** | Adjusts edge weights | x → p(ΔT \| x) | Weather, hour, traffic, events |
| **(B) Structural** | Modifies graph topology | G″ → G′ | Baustelle, elevator, modal avail. |
| **(C) Binary gate** | Removes corridors | G\_base → G″ | NINA, full closure |

**Processing order:** G\_base → [C] → G″ → [B] → G′ → [A via MC] → T\_eff

**Hybrid signals:** Some signals are structurally primary but induce continuous secondary effects. Example: Baustelle with single-track = B (graph annotation) + A (increased delay in MC). Primary classification determines G′ mutation; secondary flows through conditioning.

**Shadow capacity (v0.6.0):** Baustelle with residual capacity < 20% → escalated to C. Retained in G\_fallback for emergency re-routing only.

#### Class A — Continuous Modulators

A1 Weather (Bright Sky/DWD: precipitation, wind, temperature, thunderstorm, snow). Aggregation: hazards worst-case, continuous weighted-average, residuals by leg length. A2 Demand (hour, weekday, holidays). A3 Road traffic (first-mile; temporal decoupling applies). A4 Events (Bundesliga, Messen, festivals).

#### Class B — Structural Constraints

B1 Baustellen (closure → remove; capacity → annotate + A-secondary; shadow < 20% → C). B2 Transfer accessibility (profile-dependent; see below). B3 First-mile modal availability (mode unavailable → remove edges).

**Accessibility profile inversion:** `accessibility_required = true` → unknown elevator status = transfer edge removed (pessimistic). Default profile → transfer normal.

#### Class C — Binary Disruption Gates

C1 NINA/BBK warnings → corridor removal. **Escape-vector protocol:** origin/destination in C-zone → degrade adjacent edges to B with max penalty.

C2 Full closures → line removal. **Density detector:** ρ\_disruption > 5 alerts / 30 min on single line → entity-level alerts escalated to C.

#### Class D — Excluded Variables

Suicide/self-harm, crime, social deprivation, psychological models, political sentiment. **Exception Protocol:** formal coastline amendment required.

#### Derived Features

D1 ρ\_disruption(station, t) = alerts per 4h window. D2 S\_node ∈ [0,1], monotone. D3 P(connection | Δt) per station-pair. D4 Cross-line delay correlation.

**Falsification for B5:** Conditioned Q₀.₈ RMSE < unconditional by ≥ 5%, over ≥ 50 journeys.

### B6 — Node-Stress as Route-Selection Signal

Routes avoiding high S\_node have lower realised Q₀.₈. Wilcoxon + bootstrap (B=5000) over ≥ 30 pairs. Bayesian sequential: demote if posterior < 0.2, confirm if > 0.9.

### B7 — State-Dependent Graph Architecture

**Claim:** G′ (C→B→A) produces portfolios with lower realised prediction error than G\_base with equivalent weight-only penalties.

**Metric:** |Q₀.₈(predicted) − T\_arrival(realised)| for chosen route. G′ median error must be > 3 min lower than G\_base over ≥ 40 qualifying journeys.

**Early-review trigger:** At 6 months or ≥ 20 qualifying journeys: if point estimate favours G\_base or G\_base superior in > 70% of pairs → initiate boundary review.

---

## 3  Conditioned Delay Model

### 3.1  State-Dependent Graph Construction

```
G_base  →  [C: gates + density detector]  →  G″  →  [B: structural + shadow]  →  G′
```

Step C: NINA, route-level alerts, density cascades → remove edges. Escape-vector for origin/destination. Step B: Baustellen, elevator, modal → modify/remove. Step A: feature vector x per remaining edge.

### 3.2  Conditional Distribution

p(ΔT\_l | x\_l) with hierarchical feature model: Tier 1 (hour × weather, 72 bins) → Tier 2 (+weekday, n>30) → Tier 3 (+S\_node/ρ/event, n>50) → regression (500+ journeys).

Fallbacks: Phase A δ(0) on G\_base. Phase B δ(α\_RT · ΔT\_RT) on G′. Phase C full on G′.

### 3.3  Real-Time Correction

T\_eff = T\_hist(x) + α\_RT · ΔT\_RT. Temporal decay: active/< 60min → 1.0; 60–180min → 0.7; 180+ → 0.5; next-day → 0.3. Phase B fallback: T\_hist → T\_schedule. Cancellations: binary removal + re-compute.

### 3.4  Monte Carlo Integration

On G′, N = 1000. Sample delays (D4 correlations). Evaluate P(connection | Δt). Missed → next same-line (lookup). Cancelled → fallback with validity check. Q₀.₈ from empirical distribution.

**Fallback validity (v0.6.0):** Constraint hash + time window. Stale fallback (edge removed post-Layer A) → T\_eff = ∞ for that realisation.

**No graph search inside MC loop.**

### 3.5  Pipeline Architecture

```
[Signals]  →  G_base  →  [C]  →  G″  →  [B]  →  G′
                                                    ↓
                                        Layer A: Candidate Generation (on G′, α_C = 0)
                                                    ↓
                                        Layer B: Portfolio Construction (MC, clustering)
                                                    ↓
                                        Layer C: User Presentation (+ comfort annotations)
```

**Streaming G″ update protocol (v0.6.0-rc1):** If a C-signal arrives after Layer A completion but before Layer B completion (race condition), the pipeline aborts Layer B and returns to Layer A with the updated G″. This is preferred over proceeding with T\_eff = ∞ penalised realisations, which waste computational budget on invalidated routes. The T\_eff = ∞ mechanism remains as a defensive fallback for C-signals arriving *during* a Monte Carlo batch that cannot be interrupted.

---

## 4  Graph Model

### 4.1  Edge Types

| Edge type | Weight | State-dependent? |
|---|---|---|
| Scheduled transit | Timetable + p(ΔT \| x) | A: delay; B/C: removal |
| Walking | OSM distance/speed | Rarely |
| Taxi / ride-hail | Drive time + traffic | A: traffic; B: availability |
| Local bus | Timetable + adherence | A: delay; B: hours |
| Transfer | Connection time + accessibility | A: delay; B: elevator |
| Waiting | Headway | No (but comfort-annotated) |

### 4.2  Node Annotations

S\_node, ρ\_disruption, Baustelle, event flag, elevator status, NINA zone, DB Lounge availability.

---

## 5  Implementation Roadmap

### Phase A — Static Prototype

G\_base only. GTFS + OSM → OTP → progressive deepening → deterministic scoring → clustered portfolio. CLI/Jupyter. **No external APIs beyond GTFS + OSM.**

### Phase B — Real-Time + G′

Activate C/B signals → G′. Weather overlay. RT correction with temporal decay. Situational dominance with temporal decoupling. Accessibility profiles. Comfort annotations. Streaming G″ update protocol.

### Phase C — Full Conditioning

Logger (GTFS-RT/30s + weather + structural state). **Custodianship:** 90-day raw retention; aggregates permanent; sharing at station-day granularity, CC BY-SA 4.0. DB GTFS-RT ToS verified. Hierarchical features Tier 1→2→3→regression. Calibration (α\_RT, α\_C, quantile). **B4 counter resets after α\_C calibration.** Min viable: 3 months weekday logging.

---

## 6  Boundary Conditions and Limitations

- **Taxi availability:** Time-of-day heuristic only. **Experimental module** — explicitly marked as unvalidated outside the Haßlinghausen corridor, requiring corridor-specific calibration. Not architecture-bearing; designed as a replaceable component with an `experimental` flag. UI should display a warning when taxi first-mile is selected for departure times with low confidence.
- GTFS-DE Flixbus coverage incomplete.
- C(r) corridor-relative; creativity drift mitigated by R-blending (§0.3).
- GTFS-RT reliability varies; α\_RT mitigates.
- Phase C: ~3 months minimum.
- Weather aggregation: hazard worst-case, continuous weighted; residuals by leg length.
- Event data may miss smaller events.
- **Class D exclusion** architectural (Exception Protocol).
- Dominance filter: may prune in unmodelled dimensions.
- Cross-leg correlation: early Phase C assumes conditional independence.
- α\_C, α\_RT, quantile 0.8: initial estimates.
- Hafas gap monitored.
- Phase C data sovereignty: custodianship protocol.
- NINA API: not guaranteed for all hazard types.
- Elevator data: DB APIs incomplete; pessimistic fallback for `accessibility_required`.
- Road traffic: free-tier limited; OSM baseline fallback.
- B7 sample size: early-review trigger at 6 months.
- **Comfort layer** (§0.5): DB Lounge hours may change; BahnCard status is user-configured and not verified by the system.

**Parameter sensitivity note (v0.6.0-rc1):** The following numerical thresholds are *calibration variables*, not architectural constants. They require corridor-specific calibration during Phase C, with sensitivity analysis planned for the first 20 qualifying journeys:

| Parameter | Current value | Sensitivity |
|---|---|---|
| B2 temporal decoupling cutoff | 2 hours | May need adjustment for very early/late departures |
| B5 shadow capacity threshold | 20% residual | May vary by corridor topology |
| B7 early-review superiority threshold | 70% | Depends on G′≠G\_base event frequency |
| Density detector threshold | 5 alerts / 30 min | DB-specific; other operators may differ |
| B4 usage review threshold | 20 journeys | Depends on travel frequency |

These thresholds may be adjusted in the implementation handbook without coastline amendment, provided the adjustment is logged and the architectural claim (the boundary) remains unchanged.

---

## 7  User-Facing Presentation (v0.6.0-rc1)

The internal complexity of the model must not reach the user unfiltered. Layer C presents the portfolio with the following simplified view:

**Per-route summary card:**

| Field | Display | Internal source |
|---|---|---|
| Strategy label | „Schnellste" / „Sicherste" / „Überraschung" / „Entspannt" | B4 cluster |
| Expected arrival | HH:MM | E[T\_eff] |
| Confidence | „±X min" (80% interval) | Q₀.₈ − E[T\_eff] |
| Transfers | count + station names | Leg structure |
| Weather warning | icon if W(r) > threshold | A1 aggregation |
| Comfort | „Lounge verfügbar" / „Überdacht" / „Bahnsteig" per transfer | §0.5 |
| Risks | „Knoten unter Stress" / „Baustelle" / „Kein Aufzug" | S\_node, B-signals |
| Price | € | Cost(r) |

No Q₀.₈, S\_node numerical values, ρ\_disruption, or feature vectors are shown. The user sees labels, times, and warnings. Advanced users can optionally expand a detail view.

---

## 8  Version History

| Version | Date | Summary |
|---|---|---|
| 0.1.0 | 2026-03-17 | Initial coastline. |
| 0.2.0 | 2026-03-17 | Guardian #1: Q₀.₈; creativity externalised; dominance; deepening; RT blending; clustering. |
| 0.3.0 | 2026-03-17 | Guardian #2: B5 system-load; B6 node-stress; weather/event sources; conditioned delay model. |
| 0.4.0 | 2026-03-17 | Architect + Scout: symbols; terminology; B3 termination; B6 stats; S\_node; pipeline; MC constraint; α\_RT decay; hierarchical features; weather split; Class D protocol; custodianship; Hafas. |
| 0.5.0 | 2026-03-17 | Functional review: Signal taxonomy A/B/C; G′; B7; situational first-mile; elevator; NINA; density detector. |
| 0.6.0 | 2026-03-17 | Freeze candidate: B1 softened; B2 temporal decoupling; B4 dual falsification; B5 hybrid/shadow; B7 metric/early-review; escape-vector; accessibility inversion; fallback validity; dual robustness. |
| 0.6.0-rc1 | 2026-03-17 | Release candidate: (i) B4 falsification clarified as conjunctive; (ii) calibration freeze protocol; (iii) streaming G″ update (pipeline abort on C-signal race); (iv) MVP slice table; (v) user-facing presentation layer; (vi) wait-comfort layer with DB Lounge/BahnCard; (vii) creativity drift mitigation (R-blending); (viii) taxi module explicitly experimental; (ix) parameter sensitivity note; (x) user-facing summary card design. |

---

*End of Coastline Document · Open-Science Harbour*
