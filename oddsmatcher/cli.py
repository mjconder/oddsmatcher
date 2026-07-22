"""Command-line entry point: ``oddsmatcher scan``."""

import argparse
import sys
from pathlib import Path

from oddsmatcher.aggregate import DEFAULT_HORIZON, best_prices, collect_quotes
from oddsmatcher.sources import (
    NorthwoodSource,
    OddsSource,
    OpenlineSource,
    SourceError,
    StatelineSource,
)

DEFAULT_FIXTURES = Path("fixtures")


def build_sources(fixtures_root: Path) -> list[OddsSource]:
    return [
        NorthwoodSource(fixtures_root / "northwood"),
        OpenlineSource(fixtures_root / "openline"),
        StatelineSource(fixtures_root / "stateline"),
    ]


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        quotes = collect_quotes(build_sources(args.fixtures))
    except SourceError as exc:
        print(f"oddsmatcher: {exc}", file=sys.stderr)
        return 1
    views = best_prices(quotes, horizon=args.horizon)
    for view in views:
        print(f"{view.event_name} [{view.market}]")
        for outcome, price in sorted(view.prices.items()):
            print(f"  {outcome:<6} {price.decimal_odds:>6.2f}  ({price.source})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oddsmatcher",
        description="Aggregate bookmaker odds and show the best available price.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser(
        "scan", help="show the best available price per outcome"
    )
    scan.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    scan.add_argument(
        "--horizon",
        type=float,
        default=DEFAULT_HORIZON,
        help="max quote age in seconds",
    )
    scan.set_defaults(func=cmd_scan)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code: int = args.func(args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
