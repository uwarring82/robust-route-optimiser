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
    plan.add_argument("--otp-url", default="http://localhost:8080/otp/gtfs/v1",
                      help="OTP 2.x GTFS GraphQL endpoint")
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

    from datetime import datetime, timezone

    from rro.graph.otp_client import OTPClient, OTPError
    from rro.pipeline import otp_plan_fns, plan_portfolio
    from rro.portfolio.cluster import UnderfullPortfolioError
    from rro.portfolio.output import to_json

    client = OTPClient(args.otp_url)
    hub_plan_fn, backbone_plan_fn = otp_plan_fns(client)
    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        portfolio = plan_portfolio(
            cfg, departure, hub_plan_fn=hub_plan_fn,
            backbone_plan_fn=backbone_plan_fn, generated_at=generated_at)
    except UnderfullPortfolioError as e:
        print(f"underfull portfolio: {e}", file=sys.stderr)
        return EXIT_UNDERFULL
    except NotImplementedError as e:
        print(f"not yet implemented: {e}", file=sys.stderr)
        return EXIT_NOTIMPL
    except OTPError as e:
        print(f"OTP error: {e}", file=sys.stderr)
        return EXIT_OTP

    document = to_json(portfolio)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            fh.write(document + "\n")
    else:
        print(document)
    if args.card:
        _print_card_table(portfolio)
    return EXIT_OK


def _print_card_table(portfolio) -> None:
    """Render the Coastline §7 summary cards to stderr (handbook §8.1)."""
    headers = ["Strategy", "Arrival", "Confidence", "Transfers", "Transfer stations", "Price"]
    print(" | ".join(headers), file=sys.stderr)
    for s in portfolio.strategies:
        c = s.card
        price = f"{c.price_eur:.2f} €" if c.price_eur is not None else "—"
        print(" | ".join([c.strategy_label, c.expected_arrival, c.confidence,
                          str(c.transfers), ", ".join(c.transfer_stations), price]),
              file=sys.stderr)


def main(argv: Optional[list] = None) -> int:
    """Console entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        return cmd_plan(args)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
