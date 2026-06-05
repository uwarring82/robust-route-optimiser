"""CLI entry point for the RRO Phase A engine (handbook §8.1).

``rro plan`` loads a corridor config, resolves the departure, and runs the
B1→B4 pipeline. The pipeline itself is not yet wired in this scaffold; config
loading, flag precedence, and exit codes are.

Exit codes (§8.1): 0 = portfolio emitted; 1 = internal error / not-yet-implemented
pipeline (scaffold); 2 = config/validation failure; 3 = OTP graph/query error;
4 = portfolio underfull (< 2 strategies).
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from rro import COASTLINE_VERSION, ENGINE_VERSION
from rro.config import (
    ConfigError,
    load_config,
    require_departure_time,
    validate_config,
)

EXIT_OK = 0
EXIT_NOTIMPL = 1
EXIT_VALIDATION = 2
EXIT_OTP = 3
EXIT_UNDERFULL = 4


def build_parser() -> argparse.ArgumentParser:
    """Construct the ``rro`` argument parser (handbook §8.1)."""
    p = argparse.ArgumentParser(
        prog="rro",
        description="Robust Route Optimiser — Phase A static engine",
    )
    p.add_argument(
        "--version", action="version",
        version=f"rro {ENGINE_VERSION} (coastline {COASTLINE_VERSION})",
    )
    sub = p.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="plan a clustered portfolio for the corridor")
    plan.add_argument("--from", dest="origin", help="override config origin")
    plan.add_argument("--to", dest="destination", help="override config destination")
    plan.add_argument("--depart", dest="departure_time", help="ISO 8601 departure; overrides config")
    plan.add_argument("--config", required=True, help="path to corridor.yml")
    plan.add_argument("--json-out", help="write the JSON portfolio to this path")
    plan.add_argument("--card", action="store_true", default=True, help="print the §7 card table")
    plan.add_argument("--alpha-c", type=float, dest="alpha_c", help="override α_C")
    plan.add_argument("--epsilon", type=float, help="override ε time_min (min)")
    plan.add_argument("--quantile", type=float, help="override reporting quantile")
    return p


def _apply_overrides(cfg, args) -> None:
    if args.origin:
        cfg.origin = args.origin
    if args.destination:
        cfg.destination = args.destination
    if args.alpha_c is not None:
        cfg.alpha_c = args.alpha_c
    if args.quantile is not None:
        cfg.quantile = args.quantile
    if args.epsilon is not None:
        cfg.epsilon.time_min = args.epsilon


def cmd_plan(args) -> int:
    """Run the ``plan`` subcommand (handbook §8.1)."""
    try:
        cfg = load_config(args.config)
    except (ConfigError, FileNotFoundError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return EXIT_VALIDATION

    _apply_overrides(cfg, args)

    # CLI overrides bypass the load-time YAML validation — re-validate ranges.
    try:
        validate_config(cfg)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return EXIT_VALIDATION

    try:
        departure = require_departure_time(cfg, args.departure_time)
    except ConfigError as e:
        print(f"usage error: {e}", file=sys.stderr)
        return EXIT_VALIDATION

    # Phase A pipeline (B1→B4) is not yet wired in this scaffold. Return a
    # documented diagnostic (exit 1) rather than crashing with a traceback.
    print(
        "rro: Phase A pipeline not yet implemented (scaffold). "
        f"Config resolved for {cfg.origin!r} → {cfg.destination!r} @ {departure}. "
        "Wiring (handbook §2.3): data.ingest → graph.build → "
        "routing(decompose/hubs/dominance/deepening) → "
        "scoring(objective/creativity/robustness) → portfolio(cluster/output/card).",
        file=sys.stderr,
    )
    return EXIT_NOTIMPL


def main(argv: Optional[list] = None) -> int:
    """Console entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        return cmd_plan(args)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
