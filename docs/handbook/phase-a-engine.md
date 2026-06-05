---
layout: default
title: "Phase A — Static Engine"
---

# Handbook: Phase A — Static Engine

> **Status:** Draft &nbsp;·&nbsp; **Subordinate to:** Coastline v0.6.0-rc1 &nbsp;·&nbsp; **engine_version:** `0.1.0-a` &nbsp;·&nbsp; **coastline_version:** `0.6.0-rc1`

This page is **subordinate** to [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1). The handbook may choose implementation details and set or adjust calibration thresholds (Coastline §6, *parameter sensitivity note*), but it must **never** contradict a coastline claim, boundary, or symbol. Where the two could be read as conflicting, the coastline wins and this page is wrong. All coastline references are cited inline as (Coastline §X).

---

## 1  Overview and Scope

### 1.1  Purpose

Phase A is a **standalone, deterministic, offline portfolio router** for the single corridor Haßlinghausen → Freiburg (Breisgau) (Coastline §0). It is the static-prototype slice of the Implementation Roadmap (Coastline §5, *Phase A — Static Prototype*): it operates exclusively on the base graph `G_base` built from static GTFS feeds and an OSM PBF extract, runs entirely from local data and a local routing server, and emits a clustered JSON portfolio. There are **no external APIs beyond GTFS feeds and OSM** (Coastline §0.4, §5).

The corridor is non-trivial because the origin Haßlinghausen is not a railway node; the primary lever for route quality is the **creative selection of feeder hubs** into the long-distance backbone (Coastline §0). Phase A therefore implements the full first-mile → backbone → last-mile decomposition (B1), creative hub enumeration and static dominance (B2), progressive deepening (B3), and clustered output (B4), but with every stochastic, state-dependent, and real-time mechanism switched off.

The deliverable is the data path:

```
GTFS + OSM ingest → OTP 2.x routing (progressive deepening) → deterministic scoring → portfolio clustering → JSON output
```

runnable from a CLI entry point (`src/rro/cli.py`) or a Jupyter session (Coastline §0.4, §5).

### 1.2  MVP slice (Coastline §0.4) — IN / OUT for Phase A

This restates the MVP table of Coastline §0.4 as the binding Phase A scope. Anything marked OUT is referenced in this handbook **only as a forward-hook** to Phase B/C and never described as active Phase A behaviour.

| Component / mechanism | Phase A | Module(s) |
|---|---|---|
| `G_base` (static GTFS + OSM) | **IN** — required, only graph | `data/ingest.py`, `graph/build.py` |
| B1 three-layer decomposition (first_mile / backbone / last_mile) | **IN** | `routing/decompose.py` |
| B2 creative hub discovery, **static** dominance (all stops within `t_first_minutes` = 45) | **IN** | `routing/hubs.py`, `routing/dominance.py` |
| B3 progressive deepening (Depth 0 direct + 1-transfer; Depth 1 2-transfer; Depth 2 creative ×2.5; ε-termination) | **IN** | `routing/deepening.py` |
| B4 clustered portfolio (min 2, max 4 strategies) | **IN** | `portfolio/cluster.py` |
| Deterministic `T_eff = T_schedule` | **IN** — only mode | `scoring/objective.py` |
| Creativity `C(r)`, two-pass with reference set `R` | **IN** | `scoring/creativity.py` |
| Structural decision-robustness proxy (stand-in for `Q₀.₉₅`) | **IN** | `scoring/robustness.py` |
| JSON portfolio + user-facing card mapping (Coastline §7) | **IN** | `portfolio/output.py`, `portfolio/card.py` |
| CLI / Jupyter interface | **IN** | `src/rro/cli.py` |
| Comfort scoring (Coastline §0.5) | optional (default off) | — |
| A-signals (weather, traffic, events) and conditioning `p(ΔT \| x)` | **OUT** → Phase B/C | forward-hook only |
| B-signals (Baustellen, elevator/accessibility edge removal, modal availability) | **OUT** → Phase B/C | forward-hook only |
| C-signals (NINA/BBK, full closures, density detector `ρ_disruption`) | **OUT** → Phase B/C | forward-hook only |
| State-dependent graph `G′` (and the `G_base → G″ → G′` mutation chain) | **OUT** → Phase B/C | forward-hook only |
| Real-time correction and `α_RT` | **OUT** → Phase B/C | forward-hook only |
| B2 situational / temporally-decoupled dominance | **OUT** → Phase B/C | forward-hook only |
| Monte Carlo with `p(ΔT \| x)` | **OUT** → Phase B/C | forward-hook only |
| Phase C logger + historical CDFs, hierarchical feature model | **OUT** → Phase C | forward-hook only |

### 1.3  Prerequisites

| Prerequisite | Detail | Used by |
|---|---|---|
| Python 3.11+ | Engine runtime; standard library plus the `src/rro/` package | all modules |
| A JRE (Java runtime) | Required to run **OpenTripPlanner 2.x** (Coastline §1.2); OTP is a Java application queried over its GTFS GraphQL API | `graph/build.py`, `graph/otp_client.py` |
| Corridor GTFS feeds | Static schedules for the Haßlinghausen → Freiburg corridor (DELFI/GTFS-DE, VER/VRR, DB; Coastline §1.1), fetched, validated and version-pinned | `data/feeds.py`, `data/ingest.py` |
| OSM PBF extract | Regional street/path network for first-mile and last-mile walking/feeder edges, version-pinned alongside GTFS | `data/ingest.py`, `graph/build.py` |

The OTP graph is built from the corridor GTFS feeds **plus** the OSM PBF extract and queried via OTP's **GTFS GraphQL API** (Coastline §1.2). `r5py` or a pure RAPTOR implementation (Delling et al. 2015; Coastline §1.2) are documented alternatives, but **OTP 2.x is the primary engine** for Phase A.

### 1.4  Deterministic-mode framing

Phase A runs in the single mode in which the effective travel time equals the scheduled travel time:

```
T_eff = T_schedule
```

Because `T_schedule` is a fixed timetable value with no delay model attached, the travel-time distribution is **degenerate** (a point mass). This has three consequences that hold identically wherever quantiles or expectations of `T_eff` appear in Phase A:

1. **Quantile collapse.** `Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule`. There is no spread to integrate, so the forecast-robustness term of the objective is just the scheduled time. The `quantile` config key is retained (default `0.8`) as a forward-hook but selects nothing in Phase A.

2. **Cluster collapse, structurally resolved.** The *Fastest* cluster (min `E[T_eff]`) and the *Sicherste* / most-robust cluster (min `Q₀.₉₅(T_eff)`) of B4 (Coastline §B4) would select on numerically identical keys and collapse into one strategy. Phase A therefore resolves the robust cluster with a **structural decision-robustness proxy** (Coastline §0.1 — *decision robustness is structural*), implemented in `scoring/robustness.py` as the lexicographic key: (1) fewest transfers, then (2) largest minimum transfer slack across legs (connection buffer, minutes), then (3) fewest structurally fragile legs (a leg is fragile if its only same-line recovery headway exceeds a calibration threshold; Phase-A default 30 min, see §6.3). This proxy is an **explicit Phase-A stand-in** and is **replaced by `Q₀.₉₅(T_eff)` in Phase B**; it is labelled as such everywhere it is used.

3. **No fake confidence interval.** Since `Q₀.₈ − E[T_eff] = 0` (Coastline §7 derives the displayed "±X min" from exactly this difference), the user-facing `confidence` field is the literal string `"scheduled"` rather than a synthetic ±X interval. This is consistent with — not a contradiction of — Coastline §7.

All other deterministic-mode resolutions follow from `T_eff = T_schedule`: the objective reduces to `J(r) = T_schedule − α_C · C(r)` (with initial `α_c = 0.7`, Coastline §0.2), and candidate generation, deepening, and clustering operate on schedule-exact times only.

### 1.5  What Phase A deliberately omits (forward-hooks to Phase B/C)

The following are **out of scope** for Phase A and appear in this handbook only as forward-hooks — never as active behaviour:

- **Phase B:** all A/B/C signals; the `G_base → G″ → G′` state-dependent graph mutation; real-time blending and `α_RT`; B2 **situational** and temporally-decoupled dominance; accessibility-driven elevator edge removal; weather overlays; simplified (RT-only) Monte Carlo. (Coastline §0.4, §3, §5 *Phase B*.)
- **Phase C:** Monte Carlo with full `p(ΔT \| x)`; the conditioned delay model with hierarchical features (Coastline §3.2); historical conditioning and CDFs; the corridor logger; `α_RT` / `α_C` / quantile re-calibration. (Coastline §0.4, §3, §5 *Phase C*.)
- **R-blending** of the creativity reference set (Coastline §0.3): activates only on a structural GTFS change and is a forward-hook in Phase A.

Comfort scoring (Coastline §0.5) is **optional** and defaults to off; the JSON `comfort` field may be left empty in Phase A, and `risks` is empty except for an experimental-taxi low-confidence warning (§4.2).

---

## 2  System Architecture and Pipeline

Phase A is the static-prototype slice of the optimiser (Coastline §0.4, §5). It instantiates the three-layer Layer A/B/C pipeline (Coastline §3.5) on a frozen graph and runs as a standalone CLI/Jupyter tool with **no external APIs beyond GTFS feeds and OSM**. This section specialises that pipeline, fixes the module map under `src/rro/`, defines the YAML config model, and pins the version constants.

### 2.1  Graph state in Phase A: G′ = G_base

The coastline pipeline mutates the base graph through three signal stages, `G_base → [C] → G″ → [B] → G′` (Coastline §3.1, §3.5). Phase A activates **none** of these stages: there are no C-signals (NINA, closures), no B-signals (Baustellen, elevator, modal availability), and no A-signals (weather, traffic, events). See the MVP slice table (Coastline §0.4), where every signal class is `—` in the Phase A column.

Therefore, stated plainly and identically wherever relevant:

> **In Phase A, G″ = G_base and G′ = G_base. There is no graph mutation.** The optimiser searches a single static graph built once from the corridor GTFS feeds and an OSM PBF extract.

All G′-related mechanics in the coastline — C→B→A staging, the streaming G″ update protocol (Coastline §3.5), `T_eff = ∞` stale-fallback realisations (Coastline §3.4) — are **forward-hooks for Phase B**, not active Phase A behaviour.

### 2.2  Deterministic mode

Phase A runs `mode = "deterministic"`: `T_eff = T_schedule` (Coastline §0.4, §3.2 Phase-A fallback `δ(0)` on `G_base`). The travel-time distribution is degenerate, so

```
Q₀.₈(T_eff) = Q₀.₉₅(T_eff) = E[T_eff] = T_schedule
```

Two consequences propagate through the whole pipeline and are resolved once here:

1. **Fastest (min E[T_eff]) and Sicherste/most-robust (min Q₀.₉₅) clusters collapse** onto the same ordering, since both quantiles equal `T_schedule`. To keep the `robust` cluster meaningful, Phase A resolves it with a **structural decision-robustness proxy** (Coastline §0.1 — decision robustness is structural), a lexicographic key: (1) fewest transfers, then (2) largest minimum transfer slack across legs (connection buffer in minutes), then (3) fewest structurally fragile legs (a leg is fragile if its only same-line recovery headway exceeds a threshold; default 30 min, §6.3). This proxy is an **explicit Phase-A stand-in for `Q₀.₉₅(T_eff)`, replaced in Phase B** by the Monte-Carlo quantile (Coastline §3.4). It is implemented in `scoring/robustness.py` and labelled as a proxy in every output card.
2. **No fake confidence interval.** The card `confidence` field is the literal string `"scheduled"`, not a `±X min` band, because Coastline §7 derives `±X` from `Q₀.₈ − E[T_eff]`, which is `0` here.

### 2.3  Pipeline specialised to Phase A

The coastline pipeline (Coastline §3.5) maps onto Phase A as three layers operating on the single static graph:

| Coastline layer | Phase A specialisation | Modules |
|---|---|---|
| **Layer A — Candidate generation** (on G′, α_C = 0) | Generate candidate routes on `G_base`. Three-layer decomposition (B1) → first-mile hub discovery within `T_first = 45 min` (B2) → static dominance filter (B2) → progressive deepening Depth 0/1/2 with ε-termination (B3). `α_C = 0` here is the creativity calibration pass (Coastline §0.3), used to enumerate backbone corridors and freeze the reference set R. | `routing/decompose.py`, `routing/hubs.py`, `routing/dominance.py`, `routing/deepening.py`, `graph/otp_client.py` |
| **Layer B — Portfolio construction** | Deterministic scoring (no Monte Carlo): compute `J(r) = T_schedule − α_C·C(r)` with `α_C = 0.7` (Coastline §0.2) in the scoring pass, `C(r)` two-pass (Coastline §0.3), and the structural robustness proxy. Then cluster into the B4 portfolio (min 2, max 4). | `scoring/objective.py`, `scoring/creativity.py`, `scoring/robustness.py`, `portfolio/cluster.py` |
| **Layer C — User presentation** | Serialise the portfolio to JSON and map each strategy to a user-facing card (Coastline §7). Comfort annotations (Coastline §0.5) are optional and empty in Phase A. | `portfolio/output.py`, `portfolio/card.py`, `cli.py` |

Creativity is **two-pass** (Coastline §0.3). The calibration pass runs Layer A at `α_C = 0`, enumerates backbone corridors, and freezes the top-3 by backbone-km as the reference set R. The scoring pass (Layer B) then computes `C(r) = 1 − (km on R / total backbone km of r)`. R-blending over the 5-query-day window (Coastline §0.3) is a **forward-hook**: in Phase A, R only changes on a structural GTFS feed change, and the static prototype recomputes R rather than blending.

### 2.4  Data-flow diagram

```
                         ┌──────────────────────────────────────────────┐
   corridor GTFS feeds ──┤                                              │
   (data/feeds.py)       │   data/ingest.py  — fetch · validate · pin   │
   OSM PBF extract     ──┤                                              │
                         └───────────────────────┬──────────────────────┘
                                                 │  pinned GTFS + OSM
                                                 ▼
                                   ┌──────────────────────────────┐
                                   │  graph/build.py              │
                                   │  OTP 2.x graph build  → G_base│   (G′ = G_base; no mutation)
                                   └──────────────┬───────────────┘
                                                 │  G_base (static)
   ─────────────────────────────────────────────┼──────────────────────────────── LAYER A
                                                 ▼      (queried via graph/otp_client.py, GraphQL)
                         ┌───────────────────────────────────────────────┐
                         │  routing/decompose.py  — B1 first/backbone/last │
                         └──────────────┬────────────────────────────────┘
                                        ▼
                         ┌───────────────────────────────────────────────┐
                         │  routing/hubs.py       — B2 hubs ≤ T_first=45m  │
                         │  routing/dominance.py  — B2 static dominance    │
                         └──────────────┬────────────────────────────────┘
                                        ▼
                         ┌───────────────────────────────────────────────┐
                         │  routing/deepening.py  — B3 Depth 0/1/2         │
                         │     Depth 0: direct + 1-transfer                │
                         │     Depth 1: 2-transfer                         │
                         │     Depth 2: creative expansion ×2.5            │
                         │     ε-termination (no criterion improves > ε)   │
                         └──────────────┬────────────────────────────────┘
                                        │  candidate routes
   ─────────────────────────────────────┼──────────────────────────────── LAYER B
                                        ▼
                         ┌───────────────────────────────────────────────┐
                         │  scoring/creativity.py — C(r), reference R (2-pass)│
                         │  scoring/objective.py  — J(r), Q₀.₈ = T_schedule  │
                         │  scoring/robustness.py — structural proxy         │
                         └──────────────┬────────────────────────────────┘
                                        ▼
                         ┌───────────────────────────────────────────────┐
                         │  portfolio/cluster.py  — B4 clustering (2–4)    │
                         │     fastest · robust · creative · low_transfer  │
                         └──────────────┬────────────────────────────────┘
                                        │  clustered portfolio
   ─────────────────────────────────────┼──────────────────────────────── LAYER C
                                        ▼
                         ┌───────────────────────────────────────────────┐
                         │  portfolio/output.py   — JSON portfolio         │
                         │  portfolio/card.py     — §7 user-facing card    │
                         └──────────────┬────────────────────────────────┘
                                        ▼
                              JSON portfolio  +  summary cards
                                  (via cli.py / Jupyter)
```

### 2.5  Module map (`src/rro/`)

The repository layout is fixed by contract; each module has a single responsibility.

| Path | Responsibility | Boundary / Coastline ref |
|---|---|---|
| `config.py` | Load and validate corridor + user config (YAML); resolve defaults. | §0.4 |
| `data/feeds.py` | Corridor GTFS feed registry (which feeds, where). | §1.1 |
| `data/ingest.py` | Fetch, validate, and version-pin GTFS feeds + OSM PBF extract. | §1.1 |
| `graph/build.py` | Orchestrate the OTP 2.x graph build from pinned GTFS + OSM → `G_base`. | §1.2 |
| `graph/otp_client.py` | OTP GraphQL client wrapper; issue itinerary queries. | §1.2 |
| `routing/decompose.py` | B1 three-layer decomposition (first-mile / backbone / last-mile). | B1 |
| `routing/hubs.py` | B2 first-mile hub enumeration within the `T_first` window (45 min). | B2 |
| `routing/dominance.py` | B2 static dominance filter over enumerated hubs/routes. | B2 |
| `routing/deepening.py` | B3 progressive deepening controller (Depth 0/1/2, ε-termination). | B3 |
| `scoring/objective.py` | `J(r)`; deterministic `Q₀.₈` (= `T_schedule`). | §0.2 |
| `scoring/creativity.py` | `C(r)`; reference-corridor R management (two-pass). | §0.3 |
| `scoring/robustness.py` | Structural decision-robustness proxy (Phase-A `Q₀.₉₅` stand-in). | §0.1 |
| `portfolio/cluster.py` | B4 clustering into 2–4 strategies. | B4 |
| `portfolio/output.py` | JSON portfolio serialisation. | §0.4 |
| `portfolio/card.py` | Map each strategy to the Coastline §7 user-facing card. | §7 |
| `cli.py` | CLI entry point (argparse or click). | §5 |
| `tests/` | Unit tests + golden-route integration tests. | §5 |

Per Coastline §1.2, the primary routing engine is **OpenTripPlanner 2.x**, queried through its GTFS GraphQL API, with the OTP graph built from the corridor GTFS feeds plus an OSM PBF extract. A `r5py` / pure-RAPTOR implementation is a documented alternative engine behind the `graph/otp_client.py` boundary, but **OTP 2.x is primary** in Phase A.

### 2.6  Configuration model (YAML)

`config.py` loads a single YAML document combining corridor and user configuration. Keys, with Phase-A defaults:

| Key | Type | Default | Meaning / Coastline ref |
|---|---|---|---|
| `origin` | string | — (required) | Origin location (e.g. Haßlinghausen). §0 |
| `destination` | string | — (required) | Destination (e.g. Freiburg (Breisgau) Hbf). §0 |
| `departure_time` | string (ISO 8601) | — (required via config **or** `--depart`) | Query departure instant; the `--depart` CLI flag overrides it (§8.1). Echoed to `query.departure_time`. |
| `t_first_minutes` | int | `45` | First-mile hub window `T_first` (B2). |
| `depths` | int | `3` | Progressive-deepening depth count: Depth 0/1/2 (B3). |
| `epsilon` | map | see below | B3 ε-termination thresholds: `time_min` (3) and `creativity` (0.05); calibration-adjustable (§6). Emitted in JSON `parameters.epsilon` as the `time_min` scalar (§2.8). |
| `alpha_c` | float | `0.7` | Creativity weight `α_C` for `J(r)` (§0.2). |
| `quantile` | float | `0.8` | Objective quantile for `Q₀.₈` (degenerate here). §0.2 |
| `fragile_headway_min` | float | `30` | Same-line recovery-headway threshold for the structural robustness proxy (§0.1); calibration-adjustable (§6). |
| `bahncard` | string / null | `null` | BahnCard status; comfort layer only (§0.5), optional in Phase A. |
| `accessibility_required` | bool | `false` | Accessibility profile (§5, B5 inversion). Forward-hook; no elevator edge removal in Phase A. |
| `feeds[]` | list | — (required) | Corridor feed registry entries (GTFS and the OSM PBF, by `kind`) consumed by `data/feeds.py`. §1.1 |

The single canonical representation of `epsilon` is a **map** of its two independently calibration-adjustable thresholds. Example config:

```yaml
origin: "Haßlinghausen"
destination: "Freiburg (Breisgau) Hbf"
departure_time: "2026-06-05T08:00:00+02:00"   # required via config OR --depart; --depart overrides
t_first_minutes: 45
depths: 3
epsilon:
  time_min: 3          # E[T_eff], structural-slack criteria (minutes)
  creativity: 0.05     # C(r) criterion (dimensionless)
alpha_c: 0.7
quantile: 0.8
fragile_headway_min: 30
bahncard: null
accessibility_required: false
feeds:
  - id: "delfi-de"
    kind: gtfs
    url: "https://www.opendata-oepnv.de/.../GTFS-DE.zip"
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "vrr"
    kind: gtfs
    url: "https://.../vrr-gtfs.zip"
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "osm-corridor"
    kind: osm_pbf
    url: "https://.../corridor-extract.osm.pbf"
    version_pin: "2026-05-31"
    sha256: "<digest>"
```

The OSM PBF is **one of the `feeds[]` entries**, discriminated by `kind: osm_pbf`; there is no separate top-level `osm_pbf` key. `config.py` rejects unknown keys and requires at least one `kind: gtfs` entry and exactly one `kind: osm_pbf` entry.

`accessibility_required` is parsed and stored but **inert in Phase A**: accessibility-driven elevator-edge removal (Coastline §5 Class B, accessibility-profile inversion) is a Phase-B forward-hook. The B3 ε-termination defaults are `time_min = 3` (minutes, for `E[T_eff]` and structural slack) and `creativity = 0.05` (for `C(r)`): a depth halts when no new route improves any active portfolio criterion (`E[T_eff]`, `C(r)`, transfers, structural slack) by more than the matching threshold. Both thresholds, and `fragile_headway_min`, are **calibration-adjustable** under the parameter-sensitivity note (Coastline §6) and may be changed in this handbook without coastline amendment, provided the boundary claim is unchanged.

### 2.7  Version constants

Pinned in code and echoed into every JSON portfolio under `query`:

| Constant | Value | Meaning |
|---|---|---|
| `engine_version` | `"0.1.0-a"` | This Phase-A handbook implementation. |
| `coastline_version` | `"0.6.0-rc1"` | Governing coastline the engine conforms to. |

### 2.8  Portfolio output contract

Layer C emits the canonical JSON portfolio. `portfolio/output.py` produces the document; `portfolio/card.py` fills the `card` block per Coastline §7.

```json
{
  "query": {
    "origin": "Haßlinghausen",
    "destination": "Freiburg (Breisgau) Hbf",
    "departure_time": "2026-06-05T08:00:00+02:00",
    "generated_at": "2026-06-05T07:42:00+02:00",
    "coastline_version": "0.6.0-rc1",
    "engine_version": "0.1.0-a"
  },
  "parameters": {
    "alpha_c": 0.7,
    "quantile": 0.8,
    "t_first_minutes": 45,
    "epsilon": 3,
    "mode": "deterministic"
  },
  "reference_corridors": [
    { "corridor_id": "wuppertal-koeln-mainz-freiburg", "backbone_km": 498.1 },
    { "corridor_id": "hagen-koeln-frankfurt-freiburg", "backbone_km": 505.7 },
    { "corridor_id": "hagen-koeln-mainz-freiburg", "backbone_km": 512.4 }
  ],
  "strategies": [
    {
      "cluster": "robust",
      "label": "Sicherste",
      "score": {
        "J": 271.0,
        "Q08_T_eff_min": 271.0,
        "E_T_eff_min": 271.0,
        "creativity": 0.0,
        "transfers": 1,
        "min_transfer_slack_min": 11,
        "fragile_legs": 0,
        "backbone_km": 312.4,
        "reference_km": 312.4
      },
      "legs": [
        { "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen", "to": "Wuppertal Hbf", "dep": "2026-06-05T08:05:00+02:00", "arr": "2026-06-05T08:38:00+02:00", "line": "CE61", "transfer_slack_min": 11 },
        { "layer": "backbone", "mode": "rail", "from": "Wuppertal Hbf", "to": "Freiburg (Breisgau) Hbf", "dep": "2026-06-05T08:49:00+02:00", "arr": "2026-06-05T12:31:00+02:00", "line": "ICE", "transfer_slack_min": null }
      ],
      "card": {
        "strategy_label": "Sicherste",
        "expected_arrival": "12:31",
        "confidence": "scheduled",
        "transfers": 1,
        "transfer_stations": ["Wuppertal Hbf"],
        "price_eur": null,
        "comfort": [],
        "risks": []
      }
    }
  ]
}
```

Field rules in Phase A, consistent across the handbook:

- `parameters.mode` is always `"deterministic"`.
- `parameters.epsilon` serialises the `time_min` component of the ε map (the value the time and structural-slack criteria use); the paired `creativity` threshold (0.05) lives in `routing/deepening.py` and is set via `epsilon.creativity` in config.
- Because the distribution is degenerate, `score.Q08_T_eff_min == score.E_T_eff_min == T_schedule` for every strategy (Coastline §0.4, §3.2).
- `score.J == Q08_T_eff_min − α_C · creativity` (Coastline §0.2), up to the one-decimal rounding noted below: with `creativity ∈ [0,1]` and `α_C = 0.7`, J sits within 0.7 min of `Q08_T_eff_min`. In the example above `creativity = 0`, so `J = Q08_T_eff_min = 271.0`.
- `card.confidence` is the literal string `"scheduled"` — not a `±X` band, since `Q₀.₈ − E[T_eff] = 0` (Coastline §7).
- The `robust` cluster is ordered by the structural decision-robustness proxy (transfers → `min_transfer_slack_min` → `fragile_legs`), an explicit Phase-A stand-in for `Q₀.₉₅(T_eff)` (Coastline §0.1, §0.4).
- `card.comfort` is optional and empty in Phase A; `card.risks` is empty **except** a low-confidence warning string when an experimental taxi first-mile leg is selected (Coastline §6, §4.2). No B/C signals are active.
- `card.price_eur` may be `null` where fare data is unavailable in the static slice.
- **Numeric precision.** Minute-valued fields (`J`, `Q08_T_eff_min`, `E_T_eff_min`, `*_slack_min`) are emitted rounded to **one decimal**; `creativity` to **two decimals**. The invariants above hold up to that rounding (e.g. `309.0 − 0.7·0.58 = 308.594 → 308.6`).
- **Time formats.** `legs[].dep` / `legs[].arr` are **ISO 8601** datetimes with offset in emitted JSON (as in the contract example above and §8.1). For readability, the multi-strategy worked examples in §4.4, §5.6, and §7.2 abbreviate leg times to `HH:MM`. `card.expected_arrival` is always local **`HH:MM`**, equal to the last leg's arrival.

See [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) for the governing boundaries (B1–B4), the objective function (§0.2), and the user-facing card specification (§7).

---

## 3  Data Ingestion and Graph Build

This section specifies how Phase A assembles the static base graph **G_base** (Coastline §0.4, MVP slice) from corridor GTFS feeds plus an OpenStreetMap (OSM) PBF extract, and how that graph is served to the routing layers via OpenTripPlanner 2.x (Coastline §1.2). Phase A operates under a hard boundary: **no external APIs beyond GTFS feeds and OSM** (Coastline §5). There is no GTFS-RT, no weather, no NINA, no traffic, and no logger ingestion — those are Phase B/C forward-hooks only. All geography is data-driven (feed registry + config), never hard-coded; the Haßlinghausen → Freiburg corridor is the default *configuration*, not a constant baked into the code.

The deterministic-mode resolution applies downstream of this section: because Phase A uses `mode = "deterministic"` with **T_eff = T_schedule**, the ingested timetable is the sole source of travel time and the distribution of T_eff is degenerate (so Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule). Ingestion therefore optimises for *schedule fidelity and reproducibility*, not for any real-time signal.

### 3.1  Module responsibilities

| Module | Responsibility |
|---|---|
| `src/rro/config.py` | Load corridor + user config (YAML); resolve `origin`, `destination`, `feeds[]`, `t_first_minutes`, etc. |
| `src/rro/data/feeds.py` | Corridor feed *registry*: declares each feed source, kind, licence, and version pin |
| `src/rro/data/ingest.py` | Fetch, validate (GTFS checker), and version-pin GTFS feeds and the OSM PBF extract |
| `src/rro/graph/build.py` | Orchestrate the OTP 2.x graph build from pinned GTFS + OSM PBF |
| `src/rro/graph/otp_client.py` | Wrap the OTP GTFS GraphQL API for the routing layers |

### 3.2  Feed registry (`data/feeds.py`)

The registry is the single source of truth for *which* feeds enter G_base. It is data-driven so that re-targeting the optimiser to another corridor is a config/registry change, not a code change. Per Coastline §1.1, the Phase A corridor draws on:

| Feed | Source (Coastline §1.1) | Role in corridor |
|---|---|---|
| DELFI / GTFS-DE (national GTFS-DE) | opendata-oepnv.de | Long-distance + national backbone coverage |
| VRR GTFS (regional) | opendata-oepnv.de / regional portal | Ruhr / first-mile and feeder services near origin |
| VER / Süd-Westfalen GTFS (regional) | opendata-oepnv.de / regional portal | Süd-Westfalen feeder services around Haßlinghausen |
| OSM PBF corridor extract | openstreetmap.org | Walk network for first-mile / last-mile and station access |

Each registry entry is a typed record carrying the fields needed for reproducibility. The entry schema is identical to the `feeds[]` entries in the corridor config (§2.6): the OSM PBF is **a registry entry like any other**, discriminated by `kind: osm_pbf`:

```yaml
# resolved from feeds[] in the corridor config, materialised in data/feeds.py
- id: delfi-de
  kind: gtfs
  url: https://www.opendata-oepnv.de/.../GTFS-DE.zip
  licence: "CC BY 4.0 (DELFI)"      # recorded, not enforced at runtime
  version_pin: "2026-05-31"          # publication/effective date used as the pin
  sha256: "<digest of the pinned archive>"
- id: vrr
  kind: gtfs
  url: https://.../vrr-gtfs.zip
  licence: "<regional terms>"
  version_pin: "2026-05-31"
  sha256: "<digest>"
- id: ver-swf
  kind: gtfs
  url: https://.../ver-suedwestfalen-gtfs.zip
  licence: "<regional terms>"
  version_pin: "2026-05-31"
  sha256: "<digest>"
- id: osm-corridor
  kind: osm_pbf
  url: "<corridor OSM extract endpoint>"
  bbox: [6.9, 47.9, 7.9, 51.4]        # data-driven corridor bounding box, NOT hard-coded geography
  version_pin: "2026-05-31"
  sha256: "<digest>"
```

`config.py` reads `feeds[]` from the corridor YAML and hands the resolved list to `feeds.py`, which validates that every required `kind` is present (at least one `gtfs` feed and exactly one `osm_pbf` extract) before any build proceeds. The OSM `bbox` is derived from `origin`, `destination`, and `t_first_minutes` rather than written literally, keeping geography data-driven (Coastline §0 — the origin is not a railway node, so feeder geography must be discoverable, not assumed).

### 3.3  Ingestion pipeline (`data/ingest.py`)

`data/ingest.py` performs four steps per feed, in order, and is idempotent against the `version_pin` + `sha256`:

1. **Fetch.** Download each `url` to a local cache keyed by `(id, version_pin)`. If a cached artefact with the recorded `sha256` already exists, the download is skipped (reproducible re-runs are network-free).
2. **Validate (GTFS checker).** Run a GTFS validator — the MobilityData *gtfs-validator* (the canonical checker for `gtfs.org` feeds, Coastline §1.1) — over each GTFS archive. The build is gated on the validator: any **ERROR**-level finding (missing required files, broken `stop_times`/`trips` references, invalid `service_id` calendar) aborts ingestion; **WARNING**-level findings are logged and surfaced but do not block. The OSM PBF is validated structurally (readable header, non-empty way/node count, coverage of the corridor `bbox`).
3. **Version-pin.** Record `version_pin` (feed publication/effective date) and compute the `sha256` of each artefact, writing them back into the registry/lockfile so the exact graph inputs are reproducible. Two runs against the same lockfile produce byte-identical OTP inputs — a precondition for the golden-route integration tests under `src/rro/tests/`.
4. **Stage.** Place validated, pinned artefacts in the OTP build input directory for `graph/build.py`.

**Repository hygiene (binding):** raw bulk feeds are **never committed**. National GTFS-DE archives and corridor OSM extracts live only in the local cache and are listed in `.gitignore`. The repository tracks only:

- the **registry/lockfile** in `data/feeds.py` (URLs, licences, `version_pin`, `sha256`); and
- a small, redacted **`data/sample`** fixture — a trimmed GTFS feed and a tiny OSM extract covering the corridor — used by unit and golden-route tests so the suite runs without network access.

This keeps the build reproducible (anyone can re-fetch the exact pinned inputs from the lockfile) without redistributing bulk third-party data.

### 3.4  OTP graph build (`graph/build.py`)

`graph/build.py` orchestrates an **OpenTripPlanner 2.x** graph build (Coastline §1.2) from the staged, pinned GTFS feeds plus the OSM PBF extract:

1. Assemble the OTP build directory containing all pinned GTFS `.zip` files and the corridor OSM `.pbf`.
2. Invoke OTP 2.x in build mode (`--build --save`) to produce a serialised `graph.obj`. OTP fuses the OSM walk network (for first-mile / last-mile and station access — B1 layers) with the transit timetable into a single routable graph; this serialised graph **is** G_base for Phase A.
3. Stamp the resulting graph with a build manifest recording `engine_version = "0.1.0-a"`, `coastline_version = "0.6.0-rc1"`, the feed lockfile digests, and the OTP version, so a graph can be traced to its exact inputs.

Because Phase A is `mode = "deterministic"`, no state-dependent mutation is applied at build time: the pipeline stops at G_base. The Coastline §3.1 mutation chain G_base → [C] → G″ → [B] → G′ is a **Phase B forward-hook**; in Phase A, G′ ≡ G″ ≡ G_base and only the static graph is built and served. This is the single load-bearing seam at which Phase B attaches its graph-mutation stage (see §8.6).

### 3.5  OTP GraphQL client (`graph/otp_client.py`)

The routing layers never touch the OTP process directly. `graph/otp_client.py` wraps OTP's **GTFS GraphQL API**, exposing typed query helpers (e.g. plan an itinerary between two coordinates/stops at a departure time, enumerate stops within the first-mile window) consumed by `routing/decompose.py` (B1), `routing/hubs.py` (B2), and `routing/deepening.py` (B3). The client:

- targets a locally served OTP 2.x instance loaded with the G_base graph (no third-party routing API — Coastline §5);
- passes a fixed departure time and requests scheduled timetables only, consistent with T_eff = T_schedule (the returned itinerary times are taken as exact; no realtime updater is configured);
- returns leg structure (`mode`, `from`, `to`, `dep`, `arr`, `line`) and transfer points that downstream scoring maps onto the canonical portfolio legs (`first_mile | backbone | last_mile`).

### 3.6  Alternative routing backend (documented, not default)

OTP 2.x is the **primary** engine for Phase A. As a documented alternative, the same GTFS + OSM PBF inputs can drive **`r5py`** (a Python binding over a RAPTOR-family routing engine — RAPTOR is cited in Coastline §1.2). An `r5py` backend would build its transport network from the identical pinned feeds and OSM extract and could be exposed behind the same `otp_client.py` interface contract. It is recorded here as a fallback/comparison path only; all Phase A acceptance criteria and golden-route tests target the OTP 2.x GraphQL path.

### 3.7  Phase A boundary summary

- **In scope:** static GTFS (DELFI/GTFS-DE, VRR, VER/Süd-Westfalen) + OSM PBF → validated, version-pinned inputs → OTP 2.x build → G_base served over GraphQL.
- **Forward-hooks only (out of scope here):** GTFS-RT and α_RT, weather, NINA/closures/Baustellen and the C→B→A mutation to G″/G′, the Phase C corridor logger and historical conditioning. These are referenced for continuity but contribute **no active Phase A behaviour** (Coastline §0.4, §5).

See [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) §1.1 (data standards), §1.2 (routing infrastructure), and §5 (Phase A — static prototype, no external APIs).

---

## 4  First Mile and Hub Discovery (B1, B2)

The origin, Haßlinghausen, is **not a railway node** (Coastline §0). The whole route-quality lever in this corridor is therefore the choice of *which* long-distance feeder hub to enter the backbone at. This section covers the two boundaries that produce that choice: the **three-layer decomposition (B1)** that splits a door-to-door journey into operational segments, and the **static hub discovery (B2)** that enumerates and prunes the candidate feeder hubs. Both run on `G_base` only — static GTFS + OSM, no live traffic, no historical conditioning (Coastline §0.4 MVP slice). Everything situational (temporal decoupling, live road traffic, accessibility-driven edge removal) is a **Phase B forward-hook** and is explicitly out of scope here.

Implemented in `src/rro/routing/decompose.py` (B1) and `src/rro/routing/hubs.py` + `src/rro/routing/dominance.py` (B2). The backbone search that consumes the surviving hubs is B3 (`routing/deepening.py`), documented in §5.

### 4.1  B1 — Three-Layer Decomposition

A route `r` in the Haßlinghausen → Freiburg (Breisgau) corridor decomposes naturally into three operational layers (Coastline §B1):

| Layer | Segment | Modes | Phase A treatment |
|---|---|---|---|
| `first_mile` | origin → feeder hub | walk, bus, taxi (experimental) | enumerated + dominance-filtered (B2) |
| `backbone` | feeder hub → Freiburg (Breisgau) Hbf | rail (long-distance + regional) | progressive deepening (B3) |
| `last_mile` | Freiburg (Breisgau) Hbf → destination | walk, tram, bus | single OTP point-to-point query |

This is the *working* decomposition, not an architectural invariant. Per Coastline §B1 it is **relaxed to two layers when route structure demands** — concretely, when the dominant candidate at a given departure has a direct origin→long-distance-node leg (the first mile *is* the entry to the backbone), the `first_mile` and `backbone` layers collapse and the corridor is treated as `backbone` + `last_mile`. `decompose.py` exposes the layer count as a property of the returned route, not a fixed assumption; the JSON `legs[].layer` field carries one of `first_mile | backbone | last_mile` per leg, and a two-layer route simply emits no `first_mile` leg.

**Last-mile generation rule.** `last_mile` is a **single OTP point-to-point itinerary** (shortest `E[T_eff]`) from Freiburg (Breisgau) Hbf to the destination — it is **not enumerated and not dominance-filtered**, unlike the first mile (full `T_first` enumeration + dominance) and the backbone (B3 deepening). It is appended after backbone selection and is **excluded from the backbone search budget**. When the destination *is* Freiburg (Breisgau) Hbf, there is no last-mile leg and the route terminates at the backbone arrival.

**Transfer-count semantics (binding across the handbook).** Consistent with this appended status, the last-mile boarding is **not counted** in `score.transfers` / `card.transfer_stations` and is **excluded** from `score.min_transfer_slack_min`; all three report **first-mile + backbone line changes only**. The last-mile leg still appears in `legs[]` and its arrival sets `card.expected_arrival`. Each leg's `transfer_slack_min` is the raw connection buffer to the next leg's departure (`dep(next) − arr(this)`), or `null` for the terminal leg.

Decomposition is **structural metadata only** in Phase A: it labels legs and partitions the search, but it does not alter edge weights or `J(r)`. The creativity metric `C(r)` is defined over backbone km exclusively (Coastline §0.3), so the first/last-mile layers carry `creativity = 0` contribution and exist to (a) bound the B2 enumeration window and (b) drive the `last_mile` OTP query.

### 4.2  B2 — First-Mile Hub Enumeration (`hubs.py`)

**Enumeration rule (Coastline §B2).** Enumerate **all** stops reachable within `T_first = 45 min` of the origin — config key `t_first_minutes`, default 45 — across **walk, bus, and taxi**. This is an exhaustive reachability sweep, not a nearest-*k* shortcut: B2 is falsified if nearest-*k* (*k* ≤ 3) matches the **situational** dominance filter over > 90 % of windows (Coastline §B2). Phase A computes only the *static* filter and so cannot adjudicate this; it computes the full reachable set so the test remains decidable once the situational filter exists in Phase B.

Mechanically, for each first-mile mode we issue an isochrone / one-to-many query against OpenTripPlanner 2.x (Coastline §1.2) through its GTFS GraphQL API (`graph/otp_client.py`), rooted at the origin coordinates, with `maxDuration = 45 min`. The OTP graph is built (`graph/build.py`) from the corridor GTFS feeds plus the OSM PBF extract, so walk and local-bus reachability come straight from `G_base`. Each reached transit stop that is (or connects directly to) a long-distance / regional rail node becomes a **candidate feeder hub**. A candidate hub-arrival is the tuple:

```
hub_arrival = (hub_id, arrival_time, cost_eur, transfers, first_mile_mode)
```

where `arrival_time` is the scheduled arrival at the hub under the deterministic mode (see below), `transfers` counts first-mile transfers only, and `cost_eur` is the first-mile fare (rail backbone fares are scored later in `scoring/`).

**Deterministic mode.** Phase A runs `T_eff = T_schedule` as the only mode (Coastline §0.4). The travel-time distribution is degenerate, so `Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule` for every leg, including first-mile legs. Hub-arrival times are therefore exact scheduled times; there is no first-mile delay sampling (that is Phase B `α_RT` real-time blending, a forward-hook). The B2 **situational / temporal-decoupled dominance** of Coastline §B2 — the 2-hour `t_departure − t_query` cutoff that swaps live traffic for historical profiles — is **not active in Phase A**; we use *static* dominance only (Coastline §0.4: "B2 dominance filter (static) ✓ required" vs "B2 situational dominance — Phase B").

**Illustrative candidate hubs.** For the Haßlinghausen origin the computed set typically includes feeders such as **Wuppertal Hbf, Hagen Hbf, Gevelsberg, and Schwelm**. These are **illustrative only** — the actual set is computed from the GTFS + OSM data at query time by the 45-minute sweep above and will vary with feed version, departure time, and enabled first-mile modes. Do not hard-code them; they are documentation examples, not a registry.

**Taxi first-mile (experimental).** The taxi mode is an **experimental, replaceable module** gated behind an `experimental` flag (Coastline §6). Its travel time is a time-of-day heuristic on OSM drive time only (no live road traffic in Phase A); it is explicitly unvalidated outside the Haßlinghausen corridor and is **not architecture-bearing**. When a taxi first-mile leg survives into the portfolio, the user-facing card MUST carry a **low-confidence warning** (Coastline §6) — surfaced via the `card.risks` field — and the leg `mode` is `"taxi"`. The flag defaults off; with it off, B2 enumerates walk + bus only.

### 4.3  B2 — Static Dominance Filter (`dominance.py`)

The 45-minute sweep over-generates: many hub-arrivals are strictly worse than others and must not consume backbone-search budget. Phase A applies a **static, multi-criteria dominance** relation over the enumerated hub-arrivals (Coastline §B2 — but with *static* not situational evaluation, per §0.4).

**Dominance relation.** A hub-arrival `a` is **dominated by** hub-arrival `b` (written `b ≻ a`) iff `b` is **no later in arrival, no more expensive, and no more transfers**, with **at least one strict** inequality:

```
b ≻ a  ⇔  b.arrival_time ≤ a.arrival_time
       ∧  b.cost_eur      ≤ a.cost_eur
       ∧  b.transfers     ≤ a.transfers
       ∧  ( b.arrival_time < a.arrival_time
          ∨ b.cost_eur      < a.cost_eur
          ∨ b.transfers     < a.transfers )
```

The filter returns the **non-dominated (Pareto-optimal) frontier** of hub-arrivals over the three criteria `(arrival_time, cost_eur, transfers)`. The comparison is **per-hub-arrival, not per-hub**: two arrivals at the *same* hub on different feeders/modes are compared like any other pair, and an arrival at one hub can dominate an arrival at a different hub.

**Mode is not a dominance dimension.** `first_mile_mode` is carried on every hub-arrival but is **not** one of the dominance criteria — dominance is over `(arrival_time, cost_eur, transfers)` only. Two arrivals equal on all three criteria but differing in mode (e.g. a taxi arrival and a bus arrival at the same hub at the same time and cost) are **mutually non-dominating** (the strictness clause fails both ways) and are **both retained** into B3. B3 deduplicates downstream on the *backbone* route signature (§5.4), which ignores the **first-mile leg** (its mode and path) but **not** the feeder hub — the hub is the backbone board stop and is part of the signature. So a taxi/bus pair reaching the *same hub* on the *same backbone* collapses to one candidate, and the surviving entry retains its feeder hub and preferred mode for B4; arrivals at *different* hubs stay distinct. To avoid emitting a confusing duplicate that differs only in first-mile mode, when two retained arrivals feed the identical backbone the controller keeps the lower-`first_mile_mode`-risk feeder (walk/bus preferred over experimental taxi) unless the taxi feeder is strictly faster; the taxi variant is surfaced only when it yields a distinct, strictly better backbone candidate.

```python
def is_dominated(a: HubArrival, frontier: Iterable[HubArrival]) -> bool:
    for b in frontier:
        no_worse = (b.arrival_time <= a.arrival_time
                    and b.cost_eur <= a.cost_eur
                    and b.transfers <= a.transfers)
        strictly_better = (b.arrival_time < a.arrival_time
                           or b.cost_eur < a.cost_eur
                           or b.transfers < a.transfers)
        if no_worse and strictly_better:
            return True
    return False
```

**Dimensions and their limits.** Dominance is evaluated over exactly the three static dimensions above. It deliberately does **not** prune on comfort, node-stress, weather, or any A/B/C signal — those are Phase B/C and are not computed on `G_base`. The Coastline §6 caveat ("dominance filter may prune in unmodelled dimensions") applies: a hub-arrival that is dominated on time/cost/transfers might have been preferable on an unmodelled axis, but Phase A has no such axis, so the filter is sound *within its declared dimensions*. The surviving frontier is passed to the B3 progressive-deepening controller (`routing/deepening.py`) as the set of backbone entry points.

**Forward-hooks (NOT Phase A behaviour).** The following are referenced only so the static filter is a clean drop-in target later; none execute in Phase A: temporal decoupling at the 2 h `t_departure − t_query` cutoff (Coastline §B2, §6 sensitivity note — calibration-adjustable); live road-traffic modulation of taxi/bus first-mile times (Class A, Coastline §B5); situational dominance on `G′` (Coastline §0.4 — Phase B); and accessibility-driven elevator-edge removal at hubs (`accessibility_required`, Coastline §B5 B2 inversion — Phase B). In Phase A `accessibility_required` is carried through config (`config.py`) and serialised, but does not alter the graph.

### 4.4  Output Contribution

B1/B2 do not emit the portfolio JSON themselves (that is `portfolio/output.py`), but they populate the `first_mile` legs of each strategy and the `t_first_minutes` parameter. The relevant slice of the [canonical portfolio schema](../coastline/rro-coastline-v0.6.0-rc1) (abridged — one strategy, `parameters`/`legs`/`card` only):

```json
{
  "parameters": { "alpha_c": 0.7, "quantile": 0.8, "t_first_minutes": 45, "epsilon": 3, "mode": "deterministic" },
  "strategies": [
    {
      "cluster": "fastest",
      "label": "Schnellste",
      "legs": [
        { "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen", "to": "Schwelm",
          "dep": "07:12", "arr": "07:34", "line": "VER 553", "transfer_slack_min": 6 },
        { "layer": "backbone", "mode": "rail", "from": "Schwelm", "to": "Freiburg (Breisgau) Hbf",
          "dep": "07:40", "arr": "11:58", "line": "ICE 105", "transfer_slack_min": null }
      ],
      "card": { "strategy_label": "Schnellste", "confidence": "scheduled", "transfers": 1,
                "transfer_stations": ["Schwelm"], "risks": [] }
    }
  ]
}
```

In Phase A the card `confidence` field is the **string `"scheduled"`**, not a fake `±X` interval: because the distribution is degenerate, `Q₀.₈ − E[T_eff] = 0`, so the Coastline §7 confidence interval collapses to zero and is reported as scheduled. A surviving taxi first-mile leg adds a low-confidence warning string to `card.risks` (Coastline §6). `comfort` and `risks` are otherwise optional/empty in Phase A.

---

## 5  Backbone Search — Progressive Deepening (B3)

The backbone layer (B1, the middle of the three-layer decomposition; Coastline §B1) connects each surviving feeder hub to **Freiburg (Breisgau) Hbf**. Phase A searches this layer by **progressive deepening** (Coastline §B3): three successively wider sweeps over `G_base`, halted by ε-termination as soon as a deeper sweep stops contributing portfolio-relevant routes. Because Phase A operates on `G_base` only — not on the state-dependent `G′` of Coastline §3.1 — all routing is **schedule-based**: OTP is queried with no GTFS-RT feed, no real-time correction, and no delay model. This is the Phase A fallback `δ(0)` on `G_base` (Coastline §3.2): the travel-time distribution is degenerate, so T_eff = T_schedule and Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule. The deepening controller therefore reasons about *schedule* travel time and route *structure*, never about a non-trivial distribution.

The whole stage is the controller `routing/deepening.py`, which drives the OTP 2.x GraphQL client (`graph/otp_client.py`; Coastline §1.2) over the graph built in `graph/build.py`. Its input is the hub set surviving the static dominance filter (`routing/dominance.py`, Coastline §B2); its output is a deduplicated **candidate pool** of backbone routes handed to scoring (`scoring/objective.py`, `scoring/creativity.py`, `scoring/robustness.py`) and then to B4 clustering (`portfolio/cluster.py`).

> Forward-hook: in Phase B the same controller runs on `G′` with α_RT real-time blending and situational dominance; both are explicitly **out of scope** here (Coastline §0.4 MVP slice, §5). Nothing in B3 mutates the graph.

### 5.1  Depth ladder

Each depth issues OTP queries from every surviving hub to Freiburg (Breisgau) Hbf and widens the structural reach. The controller maps the Coastline §B3 depth ladder onto two concrete OTP knobs: `maxTransfers` (structural reach) and the candidate budget `numItineraries` (how many alternatives OTP returns per origin–destination pair, equivalently the search radius).

| Depth | Coastline §B3 reach | `maxTransfers` | Candidate budget (`numItineraries`) | Search radius (date/time window) |
|---|---|---|---|---|
| **0** | direct + 1-transfer backbone routes | 1 | `base_budget` (default 6) | departure window `[t_dep, t_dep + search_window]` |
| **1** | 2-transfer | 2 | `base_budget` | same window |
| **2** | creative expansion ×2.5 | 2 | `round(2.5 × base_budget)` (default 15) | window widened ×2.5 |

Depth 2 is the **creative expansion 2.5×** of Coastline §B3: the candidate budget and the departure search window are both scaled by `creative_factor = 2.5` (calibration-adjustable per Coastline §6 parameter-sensitivity note). Widening the budget and window surfaces alternative corridors — later trains, indirect feeder hubs, atypical line combinations — that maximise C(r) (Coastline §0.3) without relaxing the transfer ceiling further. Depth 2 explicitly does **not** raise `maxTransfers` beyond 2; it deepens *exploration*, not transfer count, keeping the low-transfer and robust clusters meaningful.

### 5.2  OTP query issuance (schedule-based, no RT)

For each surviving hub `h` and each depth `d`, the controller issues one OTP `plan` GraphQL query via `graph/otp_client.py`:

```graphql
query Backbone($from: InputCoordinates!, $to: InputCoordinates!,
               $dateTime: ..., $numItineraries: Int!, $maxTransfers: Int!) {
  plan(
    from: $from, to: $to,
    date: <t_dep.date>, time: <t_dep.time>,
    arriveBy: false,
    transportModes: [{ mode: RAIL }, { mode: BUS }, { mode: TRAM },
                     { mode: SUBWAY }, { mode: WALK }],
    numItineraries: $numItineraries,    # depth-scaled candidate budget
    maxTransfers: $maxTransfers,        # depth-scaled structural reach
    searchWindow: <search_window_seconds>  # depth-scaled radius (Depth 2 ×2.5)
  ) { itineraries { startTime endTime legs {
        mode route { shortName }
        from { name } to { name } startTime endTime
        trip { gtfsId } } } }
}
```

The query carries **no `GTFS-RT` source and no realtime updater**: the OTP graph is built from corridor GTFS feeds plus the OSM PBF extract only (Coastline §5). Every returned itinerary is treated as a `T_schedule` realisation; the controller stamps each with `confidence = "scheduled"` semantics downstream (the JSON `confidence` string), consistent with the degenerate distribution. `arriveBy: false` anchors the search to the requested departure; the last-mile layer is appended separately and is not part of the backbone budget (§4.1).

> Implementation note: OTP 2.x is **primary**. A pure RAPTOR implementation or **r5py** is a documented alternative backend (Coastline §1.2); the controller depends only on the `graph/otp_client.py` interface (issue query → list of itineraries), so the backend is swappable without touching `routing/deepening.py`.

### 5.3  Deduplication and candidate-pool accumulation

OTP returns overlapping itineraries across hubs and depths (the same backbone train re-returned at Depth 1/2 inside a wider budget, or reached via different first-mile modes). The controller accumulates into a single candidate pool keyed by a **structural route signature** so that one canonical entry survives per distinct backbone *route* — where the feeder hub (the stop at which the backbone is boarded) is part of that identity:

```python
def route_signature(itinerary) -> tuple:
    # Structural identity of the BACKBONE layer only:
    # ordered sequence of (line, board_stop, alight_stop) for transit legs.
    # The first backbone board_stop IS the feeder hub, so feeder-hub choice is
    # part of the signature; only the first-mile leg (mode + path to the hub)
    # and the exact minute-level departure are ignored.
    return tuple(
        (leg.line, leg.from_stop, leg.to_stop)
        for leg in itinerary.transit_legs
    )
```

Pool accumulation rules (`routing/deepening.py`):

- A new itinerary whose `route_signature` is unseen is **added**.
- A duplicate signature is **merged**: the controller keeps the variant with the earlier arrival (lower `T_schedule`) and records the alternative departure time as an additional service on that backbone, so connection-slack computation in `scoring/robustness.py` sees the full headway picture.
- Routes reaching the **same backbone train at the same feeder hub** but differing only in the first-mile leg (walk vs bus vs taxi to that hub) share a signature and are **merged**, the survivor keeping its feeder hub and preferred first-mile mode (§4.3). Routes boarding at **different feeder hubs** have different board stops, hence different signatures, and stay **distinct candidates** for B4 — preserving feeder-hub choice as the Phase A lever (Coastline §0).

The pool is **monotone-accumulating across depths**: Depth 1 and Depth 2 add to the Depth 0 pool, they never reset it. This is what lets ε-termination compare the *enriched* pool against the *pre-depth* pool.

### 5.4  ε-termination

The controller halts a depth — and stops deepening entirely — when that depth's newly admitted routes fail to improve **any active portfolio criterion** beyond ε (Coastline §B3 termination). The four active Phase A criteria are exactly the dimensions B4 will cluster on:

| Criterion | Source module | ε threshold (contract default) |
|---|---|---|
| E[T_eff] (= T_schedule) | `scoring/objective.py` | 3 min (`epsilon.time_min`) |
| Structural slack (`min_transfer_slack_min`) | `scoring/robustness.py` | 3 min (`epsilon.time_min`) |
| C(r) creativity | `scoring/creativity.py` | 0.05 (`epsilon.creativity`) |
| transfers (fewest) | leg structure | any strict decrease |

Both the 3 min time threshold (`epsilon.time_min`) and the 0.05 creativity threshold (`epsilon.creativity`) are the contract defaults and are marked **calibration-adjustable** (Coastline §6 parameter-sensitivity note); they live under the YAML `epsilon` map (§2.6).

```python
def deepen(hubs, pool, criteria, eps):
    for depth in range(DEPTHS):          # DEPTHS = 3 (YAML `depths`)
        budget, max_transfers, window = depth_params(depth)  # ×2.5 at depth 2
        new = []
        for h in hubs:
            for itin in otp_client.plan(h, FREIBURG_HBF,
                                        budget, max_transfers, window):
                if pool.add(route_signature(itin), itin):   # dedup-aware
                    new.append(itin)
        if not improves_any(new, pool, criteria, eps):
            break          # ε-termination: this depth added nothing useful
    return pool
```

`improves_any` returns true iff at least one route in `new` betters the incumbent best on E[T_eff], or on `min_transfer_slack_min`, by more than `eps.time_min` (3 min); **or** improves best C(r) by more than `eps.creativity` (0.05); **or** strictly lowers the minimum transfer count present in the pool. Because the distribution is degenerate, the time comparison uses T_schedule directly — there is no Q₀.₈ − E[T_eff] gap to consider here (it is identically 0). Note that ε-termination is evaluated *after* Depth 0 has run unconditionally, so the pool always contains at least the direct + 1-transfer set before any halt.

> Deterministic-mode resolution restated: the robust ("Sicherste") cluster cannot be resolved by Q₀.₉₅(T_eff) in Phase A because Q₀.₉₅ = Q₀.₈ = E[T_eff] = T_schedule and would collapse the fastest and most-robust clusters. The active "structural slack" criterion above is the **structural decision-robustness proxy** of `scoring/robustness.py` (Coastline §0.1 — decision robustness is structural): a lexicographic key of (1) fewest transfers, (2) largest `min_transfer_slack_min`, (3) fewest `fragile_legs` (fragile-headway default 30 min; see §6.3). It is an **explicit Phase-A stand-in**, replaced by Q₀.₉₅(T_eff) in Phase B.

### 5.5  Two-pass interaction with creativity

C(r) is computed two-pass (Coastline §0.3). The **calibration pass** runs once at α_C = 0 — effectively a Depth-0/1 enumeration of backbone corridors — and freezes the top-3 backbones by backbone-km as the reference set R (`scoring/creativity.py`, surfaced as `reference_corridors[]` in the JSON). The **scoring pass** then computes, for every candidate the deepening controller admits, `C(r) = 1 − (km on R / total backbone km)`. The ×2.5 creative expansion at Depth 2 exists precisely to feed the scoring pass with off-R candidates so the "Überraschung" cluster has material to select from. R-blending (Coastline §0.3) is a **forward-hook**, triggered only on structural GTFS change, and is not exercised in a single Phase A query.

### 5.6  Candidate-pool contribution to the portfolio

Each surviving candidate carries the fields B4 and the cards consume. The deepening controller is responsible for the structural fields (`transfers`, `legs`, `backbone_km`); scoring fills the rest. The portfolio JSON (canonical schema) reflects pool members under `strategies[].score`/`legs` (abridged to one strategy), e.g.:

```json
{
  "parameters": { "alpha_c": 0.7, "quantile": 0.8, "t_first_minutes": 45,
                  "epsilon": 3, "mode": "deterministic" },
  "strategies": [
    {
      "cluster": "creative",
      "label": "Überraschung",
      "score": { "J": 326.7, "Q08_T_eff_min": 327.0, "E_T_eff_min": 327.0,
                 "creativity": 0.41, "transfers": 1,
                 "min_transfer_slack_min": 11, "fragile_legs": 1,
                 "backbone_km": 488.0, "reference_km": 287.9 },
      "legs": [
        { "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen",
          "to": "Wuppertal Hbf", "dep": "08:05", "arr": "08:38",
          "line": "CE61", "transfer_slack_min": 11 },
        { "layer": "backbone", "mode": "rail", "from": "Wuppertal Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "08:49", "arr": "12:55",
          "line": "IC 2013", "transfer_slack_min": null }
      ],
      "card": { "strategy_label": "Überraschung", "expected_arrival": "12:55",
                "confidence": "scheduled", "transfers": 1,
                "transfer_stations": ["Wuppertal Hbf"],
                "price_eur": null, "comfort": [], "risks": [] }
    }
  ]
}
```

`J = Q08_T_eff_min − α_C·creativity = 327.0 − 0.7·0.41 = 326.71` (Coastline §0.2); `Q08_T_eff_min` equals `E_T_eff_min` and `confidence` is the literal string `"scheduled"` — both direct consequences of T_eff = T_schedule, consistent with Coastline §7 deriving the displayed `±X min` from Q₀.₈ − E[T_eff] (= 0 here). `comfort` is empty in Phase A and `risks` is empty unless an experimental-taxi warning applies (§4.2).

### 5.7  Falsification hook (forward-hook only)

Coastline §B3 falsification states the boundary is falsified if "Portfolio from full search ≡ three-corridor portfolio over > 90% of windows." Phase A cannot adjudicate this — the > 90%-of-windows test needs the window logger, which is a Phase C activity (Coastline §5) — but a single, **optional, non-persistent** per-run structural comparison can be derived purely from static-mode output. This is a **forward-hook only**: it accumulates no windows, is written to no cross-run logger, captures no user selection, and draws no falsification conclusion in Phase A.

This per-run structural comparison is the **canonical B3 falsification record**; §8.5 lists its field detail (which criterion last cleared ε, etc.) as the same record, not a second one. After deepening, `routing/deepening.py` may build a *naive baseline* — the three top backbone corridors by backbone-km (the frozen reference set R), each as a single fastest itinerary — and compare the deepened B4 portfolio against it:

```python
def falsification_record(deepened_portfolio, reference_corridors):
    naive = top3_corridor_portfolio(reference_corridors)   # = R, fastest each
    return {
        "differs": set(sig(deepened_portfolio)) != set(sig(naive)),
        "n_deepened": len(deepened_portfolio),
        "n_naive": len(naive),
        "novel_signatures": sorted(set(sig(deepened_portfolio)) - set(sig(naive))),
        "max_depth_reached": deepened_portfolio.max_depth,
        "terminated_early": deepened_portfolio.terminated_early,
        "eps_criterion_last_cleared": deepened_portfolio.last_eps_criterion,
    }
```

The record is derived solely from static-mode artefacts (the deepened portfolio vs the frozen R) with no B/C signal and no realised arrival. Phase A neither aggregates across windows nor persists the record; the §B3 > 90%-of-windows adjudication is Phase C (Coastline §5). The record exists so that, once the Phase C logger exists, the §B3 boundary has a single well-defined per-window input.

**Cross-reference:** [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) — §B3 (progressive deepening, termination, falsification), §B1 (three-layer decomposition), §B2 (T_first hub window), §0.3 (creativity two-pass), §0.4 / §5 (Phase A MVP), §3.2 (Phase A `δ(0)` fallback).

---

## 6  Scoring — Objective, Creativity, Robustness

Scoring is Layer B of the pipeline (Coastline §3.5): once B3 progressive deepening has produced a candidate set, each route *r* is reduced to a comparable score vector that B4 then clusters. In Phase A the engine runs in **deterministic mode** (`parameters.mode = "deterministic"`) on `G_base` only (Coastline §5). Three modules carry the work, each matching one term or facet of the coastline objective:

- `scoring/objective.py` — J(r) and the (degenerate) deterministic Q₀.₈(T_eff).
- `scoring/creativity.py` — C(r) and the two-pass reference-corridor set R.
- `scoring/robustness.py` — the structural decision-robustness proxy that stands in for Q₀.₉₅(T_eff).

All three are pure functions of route structure plus the frozen calibration artefacts (R, α_C). They never touch the graph, real-time state, or any A/B/C signal — those are forward-hooks for Phase B (Coastline §0.4 MVP table).

### 6.1  B-scoring contract: the deterministic degeneracy

The single resolution that shapes this entire section comes from `T_eff = T_schedule` (Coastline §0.4, "Deterministic T_eff = T_schedule" is the *only mode* in Phase A). With no delay model — Phase A uses the δ(0) fallback on `G_base` (Coastline §3.2) — the per-route travel-time distribution is **degenerate**: it puts all mass on a single point, T_schedule. Every quantile therefore collapses onto the mean:

```
Q₀.₈(T_eff) = Q₀.₉₅(T_eff) = E[T_eff] = T_schedule        (Phase A only)
σ(T_eff) = 0,  P_miss = P_cancel = 0
```

Two consequences propagate through scoring:

1. The objective's forecast-robustness term Q₀.₈(T_eff) reduces to T_schedule. J(r) becomes a creativity-discounted schedule time (see §6.2).
2. The B4 "Most robust" cluster, defined on Q₀.₉₅(T_eff) (Coastline §B4), would be **indistinguishable** from the "Fastest" cluster on min E[T_eff] — both keyed on T_schedule. Phase A breaks this tie with a *structural* proxy (`robustness.py`), justified by Coastline §0.1: "Decision robustness is structural." This is an explicit Phase-A stand-in, replaced by Q₀.₉₅(T_eff) once the Monte Carlo distribution exists in Phase B (Coastline §3.4).

### 6.2  B-objective — `scoring/objective.py`

Implements the coastline objective verbatim (Coastline §0.2):

```
J(r) = Q₀.₈(T_eff(r)) − α_C · C(r)
```

with the deterministic substitution Q₀.₈(T_eff(r)) = T_schedule(r). α_C is read from config (`parameters.alpha_c`, key `alpha_c`), initial value **0.7** (Coastline §0.2); α_C calibration after ~20 journeys is a Phase C activity (Coastline §5; counter reset per §B4) — Phase A only consumes the configured value. Units: T_schedule in minutes; C(r) ∈ [0, 1] dimensionless; α_C in minutes-per-creativity-unit, so J is in minutes (lower is better). Because C(r) ≤ 1 and α_C = 0.7, the creativity term α_C·C(r) is at most 0.7 min: it nudges J by under a minute, never by a schedule-scaled amount.

```python
def quantile_T_eff(route, q: float = 0.8) -> float:
    # Phase A: degenerate distribution → every quantile is T_schedule.
    # Q08_T_eff_min == Q095 == E_T_eff_min == T_schedule.
    return route.t_schedule_min

def objective(route, alpha_c: float, ref) -> float:
    q08 = quantile_T_eff(route, 0.8)          # == T_schedule
    c = creativity(route, ref)                 # scoring/creativity.py
    return q08 - alpha_c * c                    # J, minutes
```

The module emits, per route, the score fields consumed by `portfolio/output.py`: `J`, `Q08_T_eff_min`, `E_T_eff_min`, and `creativity`. In Phase A `Q08_T_eff_min == E_T_eff_min` by construction, and `J == Q08_T_eff_min − α_C·creativity` exactly; the engine still emits all of them, so the schema is stable across phases and the consumer never special-cases the mode.

**Reporting-only quantities (Coastline §0.2).** The coastline lists quantities that are *reported but not part of J(r)*. Phase A can compute the structural subset directly from the deterministic itinerary and emits them into the `score`/`card` blocks for display:

| Quantity | Phase A value/source | Schema field |
|---|---|---|
| E[T_eff(r)] | = T_schedule (degenerate) | `score.E_T_eff_min` |
| transfers | count of first-mile + backbone line changes (last-mile boarding excluded, §4.1) | `score.transfers`, `card.transfers` |
| Cost(r) | static fare from feed/fare rules + `bahncard` config | `card.price_eur` |
| Comfort(r) | optional ordinal per transfer (Coastline §0.5) | `card.comfort` |
| σ(T_eff), P_miss, P_cancel, W(r), S_node | **not emitted** in Phase A — degenerate (0) or require B/A signals | forward-hook (Phase B) |

These are reporting-only by definition: they annotate routes but never enter J(r) and never drive clustering (Comfort is explicitly user-applied decision robustness, Coastline §0.5, not a model term).

### 6.3  B-creativity — `scoring/creativity.py`

Implements the creativity metric and its **two-pass protocol** (Coastline §0.3):

```
C(r) = 1 − (km on reference corridors R / total backbone km of r)
```

C(r) is **backbone-only** (Coastline §B1 layer 2): first-mile and last-mile legs are excluded from both numerator and denominator. A route that runs entirely on the most-travelled trunk lines scores C(r) ≈ 0; a route that reaches Freiburg over off-trunk corridors scores C(r) → 1. C(r) is corridor-relative (Coastline §6) — it measures novelty *against this corridor's own backbone usage*, not absolute distance.

**Two-pass computation.**

1. **Calibration pass (α_C = 0).** Run candidate generation with the creativity bonus switched off (α_C = 0, matching the Layer-A convention in Coastline §3.5). Enumerate the backbone corridors that appear across the generated routes and accumulate backbone-km per distinct corridor. **Freeze the top-3 corridors by backbone-km** as the reference set R. Each R entry serialises to `reference_corridors[]` as `{ corridor_id, backbone_km }`. Because α_C = 0, this pass is purely structural and independent of any creativity weighting — it defines "conventional" for the corridor.
2. **Scoring pass.** With α_C at its configured value (0.7), compute C(r) for every candidate as `1 − (km_of_r_on_R / total_backbone_km_of_r)`, where `km_of_r_on_R` sums backbone-km of *r* that overlap any frozen R corridor.

```python
def calibrate_reference(candidates) -> ReferenceSet:
    # Pass 1: α_C = 0. Sum backbone km per corridor across candidates,
    # freeze the top-3 by backbone-km as R.
    km = accumulate_backbone_km(candidates)
    top3 = sorted(km.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return ReferenceSet(corridors=top3, version=next_R_version())

def creativity(route, ref: ReferenceSet) -> float:
    total = route.backbone_km
    if total == 0:
        return 0.0                     # no backbone (e.g. relaxed 2-layer, Coastline §B1)
    on_R = backbone_km_on(route, ref.corridors)
    return 1.0 - on_R / total          # C(r) ∈ [0, 1]
```

The scoring pass also fills `score.backbone_km` (total) and `score.reference_km` (`km_of_r_on_R`) so C(r) is reproducible and auditable from the JSON alone (`creativity == 1 − reference_km / backbone_km`).

**R versioning.** R is **versioned and updated only on structural GTFS changes** (Coastline §0.3) — new lines or discontinued services — never per query. Phase A pins the GTFS + OSM extract (`data/ingest.py` version-pin), so within a pinned data version R is constant: the two passes above run once per data version and R is cached against the feed/version hash. `ReferenceSet.version` records which calibration produced the current R; it travels with the portfolio implicitly via `query.coastline_version` / `query.engine_version` and the pinned feeds.

**R-blending (forward-hook).** When the feed changes structurally, Coastline §0.3 blends R_old into R_new over a 5-query-day window:

```
R_transition(day d) = (1 − d/5)·R_old + (d/5)·R_new ,  d ∈ [1, 5]
```

so a corridor counts toward R if it is in R_old OR R_new, day-fraction-weighted. **In Phase A this is a documented forward-hook, not active behaviour.** The static prototype operates on a single pinned feed version (Coastline §5), so no structural transition occurs within a run; `creativity.py` exposes the blend signature but the engine only ever invokes it with d outside [1,5] (i.e. R = R_new fully). The transition machinery activates in Phase B once feeds refresh under operation.

### 6.4  B-robustness — `scoring/robustness.py` (Phase-A stand-in for Q₀.₉₅)

The B4 "Most robust" / „Sicherste" cluster is defined on **min Q₀.₉₅(T_eff)** (Coastline §B4). Under the deterministic degeneracy Q₀.₉₅ = T_schedule, so this criterion cannot discriminate routes (see §6.1). Phase A substitutes a **structural decision-robustness proxy**, grounded in Coastline §0.1 ("Decision robustness is structural … fewer transfers, lower node-stress, avoidance of fragile corridors") and applied as an explicit **lexicographic** key — better is *smaller* at each level, ties broken at the next:

| Rank | Key | Direction | Schema field | Rationale (Coastline §0.1) |
|---|---|---|---|---|
| 1 | transfers | fewest | `score.transfers` | each transfer is an unmodelled failure point |
| 2 | min transfer slack across legs (connection buffer, minutes) | **largest** | `score.min_transfer_slack_min` | a route is only as robust as its tightest connection |
| 3 | structurally fragile legs | fewest | `score.fragile_legs` | fragile legs lack same-line recovery |

A leg is **structurally fragile** when its only same-line recovery option has a headway exceeding a threshold — i.e. if the scheduled service is missed, the next vehicle on the same line is far enough away that the leg has no realistic in-line recovery. The threshold is a **calibration variable** (config key `fragile_headway_min`), adjustable in this handbook without coastline amendment (Coastline §6, parameter-sensitivity note). **Phase-A default: fragile-headway threshold = 30 min.** Transfer slack per leg is computed from the static schedule as `dep(next leg) − arr(this leg)` at the transfer station and surfaced per leg as `legs[].transfer_slack_min`; `score.min_transfer_slack_min` is the minimum over a route's transfer boundaries.

```python
def robustness_key(route, fragile_headway_min: float = 30.0):
    # Lexicographic: smaller tuple is more robust.
    # (1) fewest transfers, (2) LARGEST min slack → negate to sort ascending,
    # (3) fewest structurally fragile legs.
    return (
        route.transfers,
        -route.min_transfer_slack_min,
        count_fragile_legs(route, fragile_headway_min),
    )
```

This proxy is labelled, everywhere it is surfaced, as a **Phase-A stand-in** for Q₀.₉₅(T_eff): it captures *structural* decision robustness, the only robustness facet observable without a delay distribution. In Phase B, once Monte Carlo on `G′` yields an empirical T_eff distribution (Coastline §3.4), the „Sicherste" cluster reverts to **min Q₀.₉₅(T_eff)** as the coastline mandates, and this module is retired or demoted to a tie-breaker.

**Dominance in score space.** Static dominance (B2, `routing/dominance.py`) prunes in the candidate space, but dominance may also be applied **in score space** before clustering: a route dominated on every active Phase-A criterion — (E[T_eff], C(r), transfers, structural-slack/fragility) — by another route, with strict improvement on at least one, can be dropped, since no B4 cluster could prefer it. This mirrors the B3 ε-termination criteria (§5.4; default `epsilon.time_min = 3` min for time, `epsilon.creativity = 0.05` for C(r), calibration-adjustable, Coastline §6) and keeps the cluster input minimal. As with B2, score-space dominance "may prune in unmodelled dimensions" (Coastline §6); Phase A accepts this within the four scored dimensions only.

### 6.5  Output mapping

`scoring/*` populates the `strategies[].score` block; `portfolio/output.py` and `portfolio/card.py` consume it. The deterministic mode produces the following invariants in the canonical schema (abridged — one strategy, `score` and `card` only):

```json
{
  "parameters": { "alpha_c": 0.7, "quantile": 0.8, "mode": "deterministic" },
  "strategies": [
    {
      "cluster": "robust",
      "label": "Sicherste",
      "score": {
        "J": 317.9,
        "Q08_T_eff_min": 318.0,
        "E_T_eff_min": 318.0,
        "creativity": 0.08,
        "transfers": 1,
        "min_transfer_slack_min": 11.0,
        "fragile_legs": 0,
        "backbone_km": 402.0,
        "reference_km": 369.8
      },
      "card": { "confidence": "scheduled", "comfort": [], "risks": [] }
    }
  ]
}
```

Note `Q08_T_eff_min == E_T_eff_min` (degeneracy), and `J == Q08_T_eff_min − α_C·creativity = 318.0 − 0.7·0.08 = 317.94 ≈ 317.9` (Coastline §0.2). `card.confidence` is the **string `"scheduled"`**, not a `±X min` interval: the user-facing confidence interval is derived as Q₀.₈ − E[T_eff] (Coastline §7), which equals **0** here, so no honest interval exists. `card.comfort` is optional/empty in Phase A and `card.risks` is empty unless an experimental-taxi low-confidence warning applies (Coastline §6, §4.2). The „Sicherste" cluster above is ranked by the structural proxy, not Q₀.₉₅ — the Phase-A stand-in.

> Cross-reference: [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) §0.1 (dual robustness), §0.2 (J(r), reporting-only), §0.3 (C(r), R, R-blending), §0.4 (MVP slice), §B4 (clusters), §6 (parameter sensitivity), §7 (confidence interval).

---

## 7  Portfolio Construction and Output (B4, §7)

This section closes the Phase A pipeline. The candidate routes surviving B3 progressive deepening (`routing/deepening.py`) and their scores from `scoring/objective.py`, `scoring/creativity.py`, and `scoring/robustness.py` are assembled into a structurally diverse portfolio (B4, Coastline §B4), serialised to the canonical JSON schema (`portfolio/output.py`), and mapped to user-facing summary cards (`portfolio/card.py`, Coastline §7). All Phase A behaviour stays inside the deterministic-mode resolution `T_eff = T_schedule` ⇒ `Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule` (Coastline §0.4, MVP slice).

See the coastline ground truth at [../coastline/rro-coastline-v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1).

### 7.1  B4 — Clustered Portfolio (`portfolio/cluster.py`)

B4 forms a portfolio of **min 2, max 4** strategies (Coastline §B4) by selecting, from the deepening output, one representative route per cluster. The cluster catalogue and selection criteria follow Coastline §B4 verbatim:

| Cluster (`cluster`) | Coastline criterion | Phase A selection key | `label` |
|---|---|---|---|
| `fastest` | Lowest E[T_eff] | min `E_T_eff_min` (= `T_schedule`) | „Schnellste" |
| `robust` | Lowest Q₀.₉₅(T_eff) | **structural decision-robustness proxy** (lexicographic, see below) | „Sicherste" |
| `creative` | Highest C(r) | max `creativity` = max C(r) | „Überraschung" |
| `low_transfer` | Fewest transfers | min `transfers` | „Entspannt" |

#### Deterministic-mode collapse of `fastest` and `robust`

Because Phase A fixes `T_eff = T_schedule`, the travel-time distribution is degenerate, so `Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule` (Coastline §0.4). The Coastline §B4 `fastest` cluster (min E[T_eff]) and `robust`/Sicherste cluster (min Q₀.₉₅(T_eff)) would therefore select on identical numerics and **collapse onto the same route**. This is expected and not a defect.

Phase A resolves the `robust` cluster with a **structural decision-robustness proxy** — robustness here is a property of route *structure*, not of a travel-time quantile (Coastline §0.1: "Decision robustness is structural"). The proxy is computed in `scoring/robustness.py` as a lexicographic key over surviving routes:

1. **fewest transfers** (`transfers`), then
2. **largest minimum transfer slack across legs** (`min_transfer_slack_min`, the connection buffer in minutes; tie-broken toward larger), then
3. **fewest structurally fragile legs** (`fragile_legs`): a leg is fragile if its only same-line recovery headway exceeds the calibration threshold (default 30 min; see §6.4).

This proxy is an **explicit Phase-A stand-in for Q₀.₉₅(T_eff)** and is replaced by the true Monte-Carlo quantile in Phase B; `portfolio/cluster.py` and every emitted strategy must label the `robust` cluster as a structural proxy, never as a realised-quantile result. The fragile-leg headway threshold (`fragile_headway_min`, default 30 min) is a calibration variable, adjustable in this handbook without coastline amendment (Coastline §6, parameter-sensitivity note), provided the adjustment is logged and the §B4 boundary is unchanged.

#### De-duplication rule (route reuse across clusters)

In deterministic mode several clusters frequently select the **same physical route** — `fastest` and `robust` collapse by construction, and the fewest-transfers route is often also fastest. B4 must still emit a portfolio of structurally *distinct* strategies. The de-duplication rule:

1. Score every surviving route against all four cluster keys.
2. For each route, determine the cluster in which it ranks **strongest and distinctly** — i.e. the cluster where it is the unique top route. A route is assigned to **exactly one** cluster: its strongest distinct claim.
3. If two clusters would map to the same route, assign that route to the cluster where its margin over the runner-up is largest; the other cluster then takes its **next-best** route, provided that route is not already assigned.
4. Drop a cluster entirely when no unassigned route can represent it. This **reduces the number of strategies** (e.g. to 3, or to the floor of 2) but **never below 2** (Coastline §B4). If fewer than 2 distinct routes exist in total, the portfolio is **underfull**: no valid portfolio can be emitted, so the run fails with a diagnostic (CLI exit `4`, §8.1) rather than returning a single-strategy result. Coastline §B4's *min 2* is a hard floor, not a target.

Cluster precedence when resolving a tie for the same route is fixed and deterministic: `fastest` → `robust` → `low_transfer` → `creative`. The `creative` strategy is the one most often *kept distinct*, because max C(r) (Coastline §0.3) typically selects an off-backbone route that no time/transfer key would surface.

Ordering of `strategies` in the output follows the same fixed precedence so the portfolio is reproducible across runs (`engine_version = "0.1.0-a"`).

### 7.2  Output serialisation (`portfolio/output.py`)

`portfolio/output.py` renders a complete multi-strategy portfolio below; **field names are exact and stable across phases** and Phase A populates the deterministic subset, leaving forward-hook fields empty or constant. For readability the leg `dep`/`arr` here are abbreviated to `HH:MM` — the canonical wire format is ISO 8601, as in §2.8 and §8.1. Each strategy's `legs[]` terminate at the stated `card.expected_arrival` and contain every transfer station and every transfer the `transfers` count implies (the last-mile leg is included; `expected_arrival = E[T_eff] = T_schedule =` the last leg's `arr`).

```json
{
  "query": {
    "origin": "Haßlinghausen",
    "destination": "Freiburg Innenstadt",
    "departure_time": "2026-06-05T07:15:00+02:00",
    "generated_at": "2026-06-05T06:48:12+02:00",
    "coastline_version": "0.6.0-rc1",
    "engine_version": "0.1.0-a"
  },
  "parameters": {
    "alpha_c": 0.7,
    "quantile": 0.8,
    "t_first_minutes": 45,
    "epsilon": 3,
    "mode": "deterministic"
  },
  "reference_corridors": [
    { "corridor_id": "HAGEN-KOELN-MAINZ-FREIBURG", "backbone_km": 512.4 },
    { "corridor_id": "HAGEN-KOELN-FRANKFURT-FREIBURG", "backbone_km": 505.7 },
    { "corridor_id": "WUPPERTAL-KOELN-FRANKFURT-FREIBURG", "backbone_km": 498.1 }
  ],
  "strategies": [
    {
      "cluster": "fastest",
      "label": "Schnellste",
      "score": {
        "J": 282.9,
        "Q08_T_eff_min": 283.0,
        "E_T_eff_min": 283.0,
        "creativity": 0.16,
        "transfers": 2,
        "min_transfer_slack_min": 9,
        "fragile_legs": 0,
        "backbone_km": 512.4,
        "reference_km": 430.4
      },
      "legs": [
        {
          "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen Mitte",
          "to": "Hagen Hbf", "dep": "07:15", "arr": "07:52",
          "line": "VER 591", "transfer_slack_min": 11
        },
        {
          "layer": "backbone", "mode": "rail", "from": "Hagen Hbf",
          "to": "Köln Hbf", "dep": "08:03", "arr": "09:01",
          "line": "ICE 945", "transfer_slack_min": 9
        },
        {
          "layer": "backbone", "mode": "rail", "from": "Köln Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "09:10", "arr": "11:52",
          "line": "ICE 105", "transfer_slack_min": 6
        },
        {
          "layer": "last_mile", "mode": "tram", "from": "Freiburg (Breisgau) Hbf",
          "to": "Freiburg Innenstadt", "dep": "11:58", "arr": "12:04",
          "line": "1", "transfer_slack_min": null
        }
      ],
      "card": {
        "strategy_label": "Schnellste",
        "expected_arrival": "12:04",
        "confidence": "scheduled",
        "transfers": 2,
        "transfer_stations": ["Hagen Hbf", "Köln Hbf"],
        "price_eur": 84.90,
        "comfort": [],
        "risks": []
      }
    },
    {
      "cluster": "robust",
      "label": "Sicherste",
      "score": {
        "J": 296.9,
        "Q08_T_eff_min": 297.0,
        "E_T_eff_min": 297.0,
        "creativity": 0.21,
        "transfers": 1,
        "min_transfer_slack_min": 18,
        "fragile_legs": 0,
        "backbone_km": 505.7,
        "reference_km": 399.5
      },
      "legs": [
        {
          "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen Mitte",
          "to": "Wuppertal Hbf", "dep": "07:10", "arr": "07:54",
          "line": "VER 643", "transfer_slack_min": 18
        },
        {
          "layer": "backbone", "mode": "rail", "from": "Wuppertal Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "08:12", "arr": "12:05",
          "line": "ICE 103", "transfer_slack_min": 6
        },
        {
          "layer": "last_mile", "mode": "tram", "from": "Freiburg (Breisgau) Hbf",
          "to": "Freiburg Innenstadt", "dep": "12:11", "arr": "12:17",
          "line": "1", "transfer_slack_min": null
        }
      ],
      "card": {
        "strategy_label": "Sicherste",
        "expected_arrival": "12:17",
        "confidence": "scheduled",
        "transfers": 1,
        "transfer_stations": ["Wuppertal Hbf"],
        "price_eur": 84.90,
        "comfort": [],
        "risks": []
      }
    },
    {
      "cluster": "creative",
      "label": "Überraschung",
      "score": {
        "J": 308.6,
        "Q08_T_eff_min": 309.0,
        "E_T_eff_min": 309.0,
        "creativity": 0.58,
        "transfers": 2,
        "min_transfer_slack_min": 12,
        "fragile_legs": 1,
        "backbone_km": 547.9,
        "reference_km": 230.1
      },
      "legs": [
        {
          "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen Mitte",
          "to": "Witten Hbf", "dep": "07:20", "arr": "07:48",
          "line": "VER 332", "transfer_slack_min": 12
        },
        {
          "layer": "backbone", "mode": "rail", "from": "Witten Hbf",
          "to": "Mannheim Hbf", "dep": "08:00", "arr": "10:48",
          "line": "IC 2304", "transfer_slack_min": 15
        },
        {
          "layer": "backbone", "mode": "rail", "from": "Mannheim Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "11:03", "arr": "12:29",
          "line": "ICE 73", "transfer_slack_min": 14
        },
        {
          "layer": "last_mile", "mode": "tram", "from": "Freiburg (Breisgau) Hbf",
          "to": "Freiburg Innenstadt", "dep": "12:35", "arr": "12:41",
          "line": "1", "transfer_slack_min": null
        }
      ],
      "card": {
        "strategy_label": "Überraschung",
        "expected_arrival": "12:41",
        "confidence": "scheduled",
        "transfers": 2,
        "transfer_stations": ["Witten Hbf", "Mannheim Hbf"],
        "price_eur": 72.40,
        "comfort": [],
        "risks": []
      }
    }
  ]
}
```

**Field semantics**

| Path | Phase A meaning |
|---|---|
| `query.coastline_version` / `query.engine_version` | Pinned constants `"0.6.0-rc1"` / `"0.1.0-a"`. |
| `parameters.alpha_c` | α_C, initial **0.7** (Coastline §0.2); used by J(r). |
| `parameters.quantile` | The reporting quantile 0.8; in deterministic mode `Q₀.₈` collapses to `T_schedule` (Coastline §0.4). |
| `parameters.t_first_minutes` | T_first window for B2 first-mile hub enumeration, **45 min** (Coastline §B2). |
| `parameters.epsilon` | B3 ε-termination, serialises the `epsilon.time_min` component (default **3 min**; the C(r) `epsilon.creativity` of 0.05 lives in `routing/deepening.py`); calibration-adjustable (Coastline §6). |
| `parameters.mode` | Always `"deterministic"` in Phase A. |
| `reference_corridors[]` | The frozen reference set **R** from the §0.3 calibration pass (α_C = 0): top-3 backbone corridors by `backbone_km`. Used by `scoring/creativity.py` for C(r); R-blending is a forward-hook (Coastline §0.3), inactive in Phase A. |
| `strategies[].cluster` / `.label` | B4 cluster id and its §B4 German user-facing label. |
| `score.J` | J(r) = `T_schedule` − α_C·C(r) (Coastline §0.2); equals `Q08_T_eff_min − 0.7·creativity`. |
| `score.Q08_T_eff_min` / `.E_T_eff_min` | Equal in Phase A (degenerate distribution); both equal `T_schedule` minutes. |
| `score.creativity` | C(r) = 1 − (`reference_km` / `backbone_km`) (Coastline §0.3). |
| `score.transfers` | Transfer count over first-mile + backbone line changes (last-mile excluded, §4.1). |
| `score.min_transfer_slack_min` | Smallest connection buffer across legs; key #2 of the structural robustness proxy. |
| `score.fragile_legs` | Count of structurally fragile legs (same-line recovery headway over `fragile_headway_min`); key #3 of the proxy. |
| `score.backbone_km` / `.reference_km` | Total backbone km of *r* and km of *r* lying on R; inputs to C(r). |
| `legs[].layer` | B1 layer tag: `first_mile` / `backbone` / `last_mile` (Coastline §B1). |
| `legs[].transfer_slack_min` | Per-leg connection buffer feeding `min_transfer_slack_min`. |
| `card.*` | The §7 presentation projection (next subsection). |

The `robust` strategy's `score.Q08_T_eff_min` is emitted for schema completeness only; it is **not** the basis of selection — the lexicographic structural proxy is. Tooling and detail views must surface the proxy keys (`transfers`, `min_transfer_slack_min`, `fragile_legs`), labelled as a Phase-A structural stand-in for Q₀.₉₅(T_eff).

### 7.3  Summary cards (`portfolio/card.py`, Coastline §7)

`portfolio/card.py` projects each strategy onto the Coastline §7 per-route summary card. Only the §7-permitted fields cross into the card; internal numerics stay in `score`.

| Card field (`card.*`) | Source in Phase A | Coastline §7 |
|---|---|---|
| `strategy_label` | `strategies[].label` (German cluster label) | "Strategy label" ← B4 cluster |
| `expected_arrival` | `HH:MM` derived from `E_T_eff_min` = `T_schedule` (last leg `arr`) | "Expected arrival" ← E[T_eff] |
| `confidence` | Constant string **`"scheduled"`** | "Confidence ← Q₀.₈ − E[T_eff]" |
| `transfers` | `score.transfers` | "Transfers" ← leg structure |
| `transfer_stations` | Station names at each transfer, from `legs[]` | transfer station names |
| `price_eur` | Fare estimate (BahnCard-aware via `bahncard` config) | "Price ← Cost(r)" |
| `comfort` | **Optional, empty `[]`** in Phase A (§0.5 reporting-only, optional) | "Comfort" (§0.5) |
| `risks` | **Empty `[]`** in Phase A, except an experimental-taxi low-confidence warning (Coastline §6, §4.2) | "Risks ← S_node, B-signals" |

#### `confidence` is the string `"scheduled"`, not a fake interval

Coastline §7 derives the displayed confidence as a „±X min" 80% interval from `Q₀.₈ − E[T_eff]`. In deterministic mode this difference is **exactly 0** (the distribution is degenerate, Coastline §0.4), so there is no honest interval to show. Phase A therefore sets `confidence` to the fixed string `"scheduled"` rather than fabricating a `±0 min` or any other interval. This is the §7-consistent rendering of a zero-width interval: the arrival is exactly the scheduled time, with no modelled spread. The „±X min" form returns automatically in Phase B once Q₀.₈ ≠ E[T_eff].

#### Suppressed internals (Coastline §7)

Per Coastline §7, **no Q₀.₈, Q₀.₉₅, S_node, ρ_disruption numerical values or feature vectors are surfaced** on the card. The robustness proxy keys, J(r), creativity C(r), backbone km, and the raw quantile fields remain in the `score` object for tooling, golden-route tests, and optional advanced detail views, but never appear on the user-facing card. The user sees labels, the HH:MM arrival, the `"scheduled"` confidence string, transfer count and station names, and price.

**Forward-hooks (not active Phase A behaviour):** the §7 weather-warning icon (A1), the populated `comfort` annotations (§0.5), and the populated `risks` list (S_node / B-signals) are deferred to Phase B/C. In Phase A `comfort` is empty and no weather field is emitted; `risks` is empty **except** an experimental-taxi low-confidence warning (§4.2). `portfolio/card.py` must otherwise leave these slots inert rather than synthesise placeholder values.

---

## 8  Interfaces, Testing, and Roadmap

This section specifies how the Phase A engine is driven (CLI and Jupyter), how it is validated (unit, golden-route, and GTFS-validation tests), the limitations inherited from the coastline (Coastline §6), and the precise seams at which Phase B signals attach. Everything here operates on `G_base` only and uses no external API beyond GTFS feeds and OSM (Coastline §0.4, §5).

### 8.1  CLI (`src/rro/cli.py`)

`cli.py` exposes a single `plan` subcommand (argparse or click). It loads a corridor + user config (`config.py`), builds/queries the OTP 2.x graph via `graph/otp_client.py`, runs the B1→B2→B3→B4 pipeline, and emits the canonical JSON portfolio on stdout plus a rendered card table (Coastline §7) on stderr. The engine runs in deterministic mode throughout, so `T_eff = T_schedule` and therefore `Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule` (the Fastest and Sicherste clusters would collapse on time alone, so the robust cluster is resolved by the structural decision-robustness proxy in `scoring/robustness.py` — fewest transfers, then largest minimum transfer slack, then fewest fragile legs; an explicit Phase-A stand-in for `Q₀.₉₅(T_eff)`, replaced in Phase B per Coastline §0.1).

```text
rro plan \
  --from "Haßlinghausen" \
  --to "Freiburg (Breisgau) Hbf" \
  --depart 2026-06-08T07:30:00+02:00 \
  --config corridor.yml \
  [--json-out portfolio.json] \
  [--card]            # also print the Coastline §7 card table (default: on)
```

Flag-to-config precedence: `--from/--to/--depart` override `origin/destination/departure_time`; all other parameters come from `corridor.yml`. The departure timestamp is ISO 8601 with offset and is passed verbatim into `query.departure_time`. `--alpha-c`, `--epsilon`, and `--quantile` are accepted as overrides for calibration runs (Coastline §6 parameter-sensitivity note) but default from config.

Exit codes: `0` = portfolio emitted (min 2 strategies, Coastline §B4); `2` = GTFS/OSM validation failure (`data/ingest.py`); `3` = OTP graph/query error (`graph/otp_client.py`); `4` = portfolio underfull (fewer than 2 clusterable strategies survived B3). Constants `engine_version = "0.1.0-a"` and `coastline_version = "0.6.0-rc1"` are stamped into every `query` block.

**Example JSON output** (abridged to two of the up-to-four clusters; `mode` is `"deterministic"`, `confidence` is the string `"scheduled"` because the distribution is degenerate and `Q₀.₈ − E[T_eff] = 0`, consistent with Coastline §7):

```json
{
  "query": {
    "origin": "Haßlinghausen",
    "destination": "Freiburg (Breisgau) Hbf",
    "departure_time": "2026-06-08T07:30:00+02:00",
    "generated_at": "2026-06-05T09:14:22+02:00",
    "coastline_version": "0.6.0-rc1",
    "engine_version": "0.1.0-a"
  },
  "parameters": {
    "alpha_c": 0.7,
    "quantile": 0.8,
    "t_first_minutes": 45,
    "epsilon": 3,
    "mode": "deterministic"
  },
  "reference_corridors": [
    { "corridor_id": "EN-Wuppertal-Koeln-RheinHSL", "backbone_km": 412.0 },
    { "corridor_id": "EN-Hagen-Frankfurt-RheinMain", "backbone_km": 498.0 },
    { "corridor_id": "EN-Dortmund-Mannheim-Rhein", "backbone_km": 521.0 }
  ],
  "strategies": [
    {
      "cluster": "fastest",
      "label": "Schnellste",
      "score": {
        "J": 268.0, "Q08_T_eff_min": 268.0, "E_T_eff_min": 268.0,
        "creativity": 0.04, "transfers": 2, "min_transfer_slack_min": 8,
        "fragile_legs": 1, "backbone_km": 415.0, "reference_km": 398.4
      },
      "legs": [
        { "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen Mitte",
          "to": "Wuppertal Hbf", "dep": "2026-06-08T07:34:00+02:00",
          "arr": "2026-06-08T08:08:00+02:00", "line": "CE61", "transfer_slack_min": 9 },
        { "layer": "backbone", "mode": "rail", "from": "Wuppertal Hbf",
          "to": "Köln Hbf", "dep": "2026-06-08T08:17:00+02:00",
          "arr": "2026-06-08T08:55:00+02:00", "line": "RE", "transfer_slack_min": 8 },
        { "layer": "backbone", "mode": "rail", "from": "Köln Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "2026-06-08T09:03:00+02:00",
          "arr": "2026-06-08T11:58:00+02:00", "line": "ICE", "transfer_slack_min": null }
      ],
      "card": {
        "strategy_label": "Schnellste", "expected_arrival": "11:58",
        "confidence": "scheduled", "transfers": 2,
        "transfer_stations": ["Wuppertal Hbf", "Köln Hbf"],
        "price_eur": 89.9, "comfort": [], "risks": []
      }
    },
    {
      "cluster": "creative",
      "label": "Überraschung",
      "score": {
        "J": 288.6, "Q08_T_eff_min": 289.0, "E_T_eff_min": 289.0,
        "creativity": 0.53, "transfers": 2, "min_transfer_slack_min": 12,
        "fragile_legs": 0, "backbone_km": 470.0, "reference_km": 220.9
      },
      "legs": [
        { "layer": "first_mile", "mode": "bus", "from": "Haßlinghausen Mitte",
          "to": "Hagen Hbf", "dep": "2026-06-08T07:41:00+02:00",
          "arr": "2026-06-08T08:19:00+02:00", "line": "583", "transfer_slack_min": 14 },
        { "layer": "backbone", "mode": "rail", "from": "Hagen Hbf",
          "to": "Frankfurt (Main) Hbf", "dep": "2026-06-08T08:33:00+02:00",
          "arr": "2026-06-08T10:41:00+02:00", "line": "IC", "transfer_slack_min": 12 },
        { "layer": "backbone", "mode": "rail", "from": "Frankfurt (Main) Hbf",
          "to": "Freiburg (Breisgau) Hbf", "dep": "2026-06-08T10:53:00+02:00",
          "arr": "2026-06-08T12:13:00+02:00", "line": "ICE", "transfer_slack_min": null }
      ],
      "card": {
        "strategy_label": "Überraschung", "expected_arrival": "12:13",
        "confidence": "scheduled", "transfers": 2,
        "transfer_stations": ["Hagen Hbf", "Frankfurt (Main) Hbf"],
        "price_eur": 71.4, "comfort": [], "risks": []
      }
    }
  ]
}
```

The objective is the coastline form throughout (Coastline §0.2): `J(r) = Q₀.₈(T_eff) − α_C·C(r) = T_schedule − α_C·C(r)`, with `C(r)` dimensionless in `[0,1]` and `α_C` in minutes-per-creativity-unit. So the creativity term `α_C·C(r)` is at most 0.7 min and J sits within 0.7 min of `Q08_T_eff_min`: for the fastest strategy `J = 268.0 − 0.7·0.04 ≈ 268.0`, and for the creative strategy `J = 289.0 − 0.7·0.53 ≈ 288.6`. The bonus never scales with the schedule time.

**Rendered card table** (`portfolio/card.py`, Coastline §7; only the active fields are populated in Phase A — `comfort` is empty, `risks` is empty unless an experimental-taxi warning applies (§4.2), `confidence` is `scheduled`):

| Strategy | Expected arrival | Confidence | Transfers | Transfer stations | Price |
|---|---|---|---|---|---|
| Schnellste | 11:58 | scheduled | 2 | Wuppertal Hbf, Köln Hbf | 89.90 € |
| Überraschung | 12:13 | scheduled | 2 | Hagen Hbf, Frankfurt (Main) Hbf | 71.40 € |

The weather/comfort/risk columns of the Coastline §7 card are forward-hooks (Phase B activates A-signals and comfort §0.5); in Phase A they render as empty cells — except the risk column, which carries an experimental-taxi low-confidence warning when a taxi first-mile leg is selected (§4.2).

### 8.2  Jupyter usage

The same pipeline is importable for notebook-driven exploration and calibration sweeps. No engine logic lives in the notebook; it only orchestrates the library and renders results.

```python
from rro.config import load_config
from rro.routing.deepening import plan
from rro.portfolio.output import to_json
from rro.portfolio.card import render_cards

cfg = load_config("corridor.yml")
portfolio = plan(
    origin="Haßlinghausen",
    destination="Freiburg (Breisgau) Hbf",
    depart="2026-06-08T07:30:00+02:00",
    config=cfg,
)                                  # deterministic: T_eff = T_schedule
print(to_json(portfolio))          # canonical schema
render_cards(portfolio)            # Coastline §7 card table as a DataFrame

# Calibration sweep (Coastline §6 parameter-sensitivity note): vary α_C only.
for alpha_c in (0.0, 0.5, 0.7, 1.0):
    p = plan(origin="Haßlinghausen", destination="Freiburg (Breisgau) Hbf",
             depart="2026-06-08T07:30:00+02:00",
             config=cfg.with_overrides(alpha_c=alpha_c))
    print(alpha_c, [s.cluster for s in p.strategies])
```

The two-pass creativity protocol (Coastline §0.3) is visible here: `alpha_c=0.0` is exactly the calibration pass that `scoring/creativity.py` uses to enumerate backbone corridors and freeze the top-3 by backbone-km as the reference set `R`; the scoring pass then computes `C(r) = 1 − (km on R / total backbone km)`. R-blending over a 5-day window is a forward-hook and only fires on structural GTFS change.

### 8.3  Corridor config (`corridor.yml`)

`config.py` loads a single YAML file using the contract keys verbatim (§2.6). Unknown keys are rejected; defaults match the coastline initial values. The OSM PBF is a `feeds[]` entry discriminated by `kind: osm_pbf`, and `epsilon` is the canonical two-field map.

```yaml
# corridor.yml — consumed by src/rro/config.py
origin: "Haßlinghausen"
destination: "Freiburg (Breisgau) Hbf"
departure_time: "2026-06-08T07:30:00+02:00"  # required via config OR --depart; --depart overrides
t_first_minutes: 45          # B2 first-mile window T_first (Coastline §B2)
depths: 3                    # B3 Depth 0/1/2 (Coastline §B3)
epsilon:
  time_min: 3                # ε-termination: 3 min for time/structural-slack criteria
  creativity: 0.05           # ε-termination: 0.05 for C(r)
alpha_c: 0.7                 # creativity weight α_C (Coastline §0.2)
quantile: 0.8                # Q₀.₈ (degenerate in Phase A ⇒ = T_schedule)
fragile_headway_min: 30      # robustness proxy fragile-leg threshold (Coastline §0.1, §6)
bahncard: null               # reporting-only in Phase A; comfort §0.5 is optional
accessibility_required: false  # default profile; elevator-edge removal is Phase B
feeds:                       # corridor feed registry (data/feeds.py)
  - id: "VRR"
    kind: gtfs
    url: "https://opendata-oepnv.de/..."
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "VER"
    kind: gtfs
    url: "https://opendata-oepnv.de/..."
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "DELFI-DE"
    kind: gtfs
    url: "https://opendata-oepnv.de/..."
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "DB-LD"
    kind: gtfs
    url: "https://data.deutschebahn.com/..."
    version_pin: "2026-05-31"
    sha256: "<digest>"
  - id: "OSM-corridor"
    kind: osm_pbf
    url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf"
    version_pin: "2026-05-31"
    sha256: "<digest>"
```

The `epsilon` map carries both contract defaults explicitly: `epsilon.time_min` (3 min) and `epsilon.creativity` (0.05), each independently calibration-adjustable (Coastline §6). The C(r) threshold is overridable via the `epsilon.creativity` key (or the `--epsilon` CLI override accepting either component). `quantile` is carried through to the JSON `parameters` block for provenance even though it has no effect under the degenerate distribution; `parameters.epsilon` in the emitted JSON serialises the `time_min` component. `departure_time` may be set here for reproducible runs or supplied per-call via `--depart` (CLI) / `plan(depart=…)` (Jupyter), which override the config value; `config.py` accepts its absence and `plan()` / the CLI raises a usage error if neither config nor the call provides it.

### 8.4  Testing

Testing has three tiers, all under `src/rro/tests/`.

**Unit tests (one suite per module).** Each module is tested in isolation against fixtures:

| Module | Representative unit assertions |
|---|---|
| `config.py` | contract keys parsed; unknown key rejected; defaults applied (`alpha_c=0.7`, `t_first_minutes=45`, `epsilon.time_min=3`, `epsilon.creativity=0.05`, `fragile_headway_min=30`) |
| `data/feeds.py` | feed registry resolves ids; `kind` discriminates GTFS vs `osm_pbf`; pinned versions surfaced |
| `data/ingest.py` | GTFS files present/well-formed; version pin recorded; OSM PBF bbox covers corridor |
| `graph/build.py` | OTP build invoked with the pinned GTFS + OSM inputs; build is idempotent for identical inputs |
| `graph/otp_client.py` | GraphQL query shape; deterministic mode passes no real-time args; error → exit 3 |
| `routing/decompose.py` | B1 splits an itinerary into `first_mile`/`backbone`/`last_mile`; 2-layer relaxation when no feeder hub differs from origin (Coastline §B1); last-mile is a single point-to-point query |
| `routing/hubs.py` | B2 enumerates exactly the stops reachable within `T_first = 45 min`; none beyond |
| `routing/dominance.py` | B2 static dominance prunes hub-arrivals over all three declared dimensions (`arrival_time` ∧ `cost_eur` ∧ `transfers`) with strict improvement on at least one; keeps Pareto front; mode is not a dominance dimension |
| `routing/deepening.py` | B3 Depth 0→1→2 ordering; creative ×2.5 expansion at Depth 2; ε-termination halts when no criterion improves beyond its `epsilon.*` threshold |
| `scoring/objective.py` | `J = T_schedule − α_C·C(r)` (within 0.7 of `Q08_T_eff_min`); `Q08_T_eff_min == E_T_eff_min == T_schedule` |
| `scoring/creativity.py` | two-pass: pass-1 at `α_C=0` freezes top-3 by backbone-km as `R`; pass-2 `C(r)=1−(km on R/total)`; bounds `[0,1]` |
| `scoring/robustness.py` | lexicographic key (transfers, then min transfer slack, then fragile-leg count); fragile-leg flag when same-line recovery headway exceeds `fragile_headway_min` (default 30) |
| `portfolio/cluster.py` | min 2 / max 4 clusters; degenerate-time collapse routes Sicherste to the structural proxy, not to `Q₀.₈` |
| `portfolio/output.py` | emitted JSON matches the canonical schema field-for-field; `mode == "deterministic"`; `confidence == "scheduled"`; `J == Q08_T_eff_min − 0.7·creativity` |
| `portfolio/card.py` | §7 mapping; `comfort` empty, `risks` empty unless an experimental-taxi warning applies (§4.2); `expected_arrival` is `E[T_eff]` as `HH:MM` = last-leg arr |

**Golden-route integration fixtures.** The frozen GTFS sample is the shared `data/sample/` fixture (§3.3) — a hand-trimmed multi-feed extract covering the Haßlinghausen feeder hubs and the backbone to Freiburg (Breisgau) Hbf, plus a small OSM PBF clip for first/last-mile walking and bus access. Because the sample is frozen and the engine is deterministic (`T_eff = T_schedule`), the full B1→B4 pipeline must reproduce a byte-stable expected portfolio (`src/rro/tests/golden/expected_portfolio.json`) for a fixed `corridor.yml` and a fixed `--depart`. The comparison ignores only `query.generated_at`. This is the primary regression guard: any change to dominance, deepening order, ε-termination, the structural proxy, or the card mapping that alters route selection will diff against the golden file. A second golden case fixes `alpha_c=0.0` to lock the calibration-pass reference-set selection (`reference_corridors`).

**GTFS validation tests.** `data/ingest.py` runs structural validation on every feed at ingest and the test suite asserts it: required files (`stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`, `calendar*.txt`), referential integrity (every `stop_id`/`trip_id`/`route_id` referenced is defined), monotone `stop_times` sequences, and service-calendar coverage of the planned departure date. Validation failure must raise before graph build and map to CLI exit 2. A negative fixture (a deliberately corrupted feed in `src/rro/tests/data/broken/`) asserts the failure path.

### 8.5  Falsification instrumentation (forward-hook only)

Two coastline boundaries — B3 (portfolio-vs-three-corridor, Coastline §B3) and B4 (dual falsification, Coastline §B4) — are adjudicated only over many realised journeys/windows, which **Phase A cannot supply**: the > 90%-of-windows B3 test and the ≥ 30-journey B4 performance falsification both require the Phase C logger and realised arrivals (Coastline §5 Phase C, §0.4), which are **out of scope** for Phase A. Phase A therefore runs **no logger**, captures **no user cluster selection**, maintains **no per-journey ledger** and **no usage counter**, and stamps **no calibration-epoch** — all of that is Phase B/C machinery.

What Phase A provides is **schema and seam readiness only**, so the later logger and ledger attach without a rewrite:

- **Canonical B3 record (non-persistent, static-mode only).** The single per-run structural comparison defined in §5.7 — `falsification_record(...)` with `{ differs, n_deepened, n_naive, novel_signatures, max_depth_reached, terminated_early, eps_criterion_last_cleared }` — is the **one authoritative B3 falsification record**. It is derived purely from static-mode output (the deepened portfolio vs the frozen reference set R), accumulates no windows, is **not persisted to any cross-run logger**, and draws no conclusion. The > 90%-of-windows adjudication is Phase C (Coastline §5).
- **B4 ledger seam (reserved schema).** The canonical JSON portfolio is designed as a **strict superset** of the Phase B/C record: the fields a future B4 dual-falsification ledger needs (offered clusters, `J`, structural-proxy keys, `C(r)`) are already present in `strategies[]`, and the realised-arrival / selected-cluster / regret / calibration-epoch columns are **reserved (null/absent)** for Phase B/C to populate. Phase A neither writes nor reads them.

No realised-arrival, delay, weather, real-time, user-selection, or calibration-epoch field is produced in Phase A; those columns exist in the schema only as reserved slots so the Phase B/C logger (Coastline §5 Phase C) and the B4 ledger (Coastline §B4) form a strict superset.

### 8.6  Phase A limitations (Coastline §6)

These are the coastline limitations that bind Phase A specifically:

- **Taxi first-mile is experimental.** The taxi/ride-hail option in `routing/hubs.py` is a time-of-day heuristic only, carries an `experimental` flag, and is unvalidated outside the Haßlinghausen corridor (Coastline §6). It is replaceable and not architecture-bearing; the §7 card must surface a low-confidence warning when a taxi first-mile is selected for a departure time with low heuristic confidence. In Phase A the warning is the only consequence — there is no traffic conditioning.
- **GTFS-DE / Flixbus coverage gaps.** Flixbus and parts of the GTFS-DE aggregate are incomplete (Coastline §6); `data/feeds.py` records coverage per feed and `routing/hubs.py`/`routing/deepening.py` may therefore miss some long-distance-bus options. Golden-route tests must not assume Flixbus presence.
- **Deterministic robustness is structural-only.** With `T_eff = T_schedule` the travel-time distribution is degenerate, so `Q₀.₈ = Q₀.₉₅ = E[T_eff]` and the Sicherste cluster cannot be resolved by `Q₀.₉₅`. Phase A substitutes the structural decision-robustness proxy (`scoring/robustness.py`) and labels every robust strategy as a Phase-A stand-in for `Q₀.₉₅(T_eff)` (Coastline §0.1). No forecast-robustness claim is made in Phase A.
- **Calibration thresholds are not constants.** `epsilon.time_min` (3 min), `epsilon.creativity` (0.05), `fragile_headway_min` (30 min), and `alpha_c = 0.7` are calibration variables, adjustable in this handbook without coastline amendment provided the change is logged and no boundary claim changes (Coastline §6 parameter-sensitivity note).

### 8.7  Transition to Phase B

Phase A is built so that Phase B activates by attaching signal inputs to existing modules and inserting one graph-mutation stage — no rewrite of the routing core. The slots are:

| Phase A module | Phase B signal input attached | Effect |
|---|---|---|
| `graph/build.py` | **`G′` mutation stage inserted here**: `G_base → [C] → G″ → [B] → G′` (Coastline §3.1) | C-gates (NINA/closures), B-structural (Baustellen, elevator, modal) rebuild the graph before search |
| `routing/dominance.py` | B2 situational dominance + temporal decoupling (Coastline §B2) | live/historical first-mile evaluation replaces static dominance |
| `routing/hubs.py` | A3 road traffic for taxi/bus first-mile; B3 modal availability | first-mile edges modulated/removed by state |
| `scoring/objective.py` | non-degenerate `Q₀.₈` via Monte Carlo with `p(ΔT\|x)`; `T_eff = T_hist + α_RT·ΔT_RT` (Coastline §3.3–3.4) | Fastest (`min E[T_eff]`) and Sicherste (`min Q₀.₉₅`) clusters separate; `α_RT` enters |
| `scoring/robustness.py` | superseded: structural proxy replaced by `Q₀.₉₅(T_eff)` for the Sicherste cluster (Coastline §0.1, §B4) | the Phase-A stand-in retires |
| `portfolio/card.py` | A1 weather warning (`W(r) > threshold`), comfort §0.5, risk strings (`S_node`, B-signals); `confidence` becomes `±X` from `Q₀.₈ − E[T_eff]` | the §7 card fields empty in Phase A populate |

The single load-bearing insertion is the **`G′` mutation stage in `graph/build.py`**: Phase A builds `G_base` and stops; Phase B inserts the `[C] → G″ → [B] → G′` chain (and, later, the streaming `G″` update / Layer-A abort protocol, Coastline §3.5) ahead of the unchanged B3 search. Because `routing/deepening.py`, `routing/decompose.py`, and `portfolio/cluster.py` already operate on whatever graph they are handed, they require no change to consume `G′`. The reserved schema slots (§8.5) become the historical baseline against which B3 and B4 are judged once Phase B/C begins producing realised journeys.

See [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) §0.4 (MVP slice), §5 (roadmap), §6 (limitations), and §7 (presentation) for the binding boundaries this section implements.

---

**Prerequisite:** [Coastline v0.6.0-rc1](../coastline/rro-coastline-v0.6.0-rc1) — read it first; this handbook is subordinate to it (§0.4 MVP slice, §5 Phase A).

**Next: Phase B** — activate C/B signals → `G′`, real-time correction with `α_RT` and temporal decay, situational dominance, non-degenerate `Q₀.₉₅(T_eff)` via Monte Carlo (Coastline §3, §5 *Phase B*). The Phase A module seams (§8.7) are the attachment points.
