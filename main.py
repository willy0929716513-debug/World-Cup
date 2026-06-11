#!/usr/bin/env python3
"""
Football Prediction System — CLI Entry Point

Usage:
  python main.py <HOME_CODE> <AWAY_CODE> [options]

Examples:
  python main.py ARG BRA
  python main.py ESP FRA --stage "Quarter-Final" --venue "AT&T Stadium, Dallas"
  python main.py GER ENG --date "2026-07-04" --neutral false
  python main.py --list
"""
from __future__ import annotations
import argparse
import sys
import os

# Make sure repo root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.loader import get_team, get_market_data, list_teams
from src.models import ensemble
from src.report.generator import print_report, console


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="World Cup 2026 Football Prediction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("home", nargs="?", help="Home team FIFA 3-letter code (e.g. BRA)")
    p.add_argument("away", nargs="?", help="Away team FIFA 3-letter code (e.g. ARG)")
    p.add_argument("--date",     default="2026-06-14", metavar="YYYY-MM-DD",
                   help="Match date (default: 2026-06-14)")
    p.add_argument("--venue",    default="MetLife Stadium, East Rutherford, NJ",
                   help="Venue name")
    p.add_argument("--comp",     default="FIFA World Cup 2026",
                   help="Competition name")
    p.add_argument("--stage",    default="Group Stage",
                   help="Match stage (e.g. 'Quarter-Final')")
    p.add_argument("--neutral",  default="true",
                   help="true/false — whether it is a neutral venue (default: true)")
    p.add_argument("--list",     action="store_true",
                   help="List all available team codes")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list:
        codes = list_teams()
        console.print("\n[bold bright_yellow]Available team codes:[/]\n")
        for i, code in enumerate(codes, 1):
            console.print(f"  {code}", end="  " if i % 6 != 0 else "\n")
        console.print("\n")
        return

    if not args.home or not args.away:
        parser.print_help()
        sys.exit(1)

    neutral = args.neutral.lower() not in ("false", "0", "no")

    # ── Load teams ────────────────────────────────────────────────────────────
    try:
        home = get_team(args.home)
        away = get_team(args.away)
    except ValueError as e:
        console.print(f"\n[bold red]Error:[/] {e}\n")
        sys.exit(1)

    # ── Load market data (from home team's stored odds as match odds) ─────────
    market = get_market_data(args.home)

    # ── Run ensemble model ────────────────────────────────────────────────────
    console.print(
        f"\n[dim]Running 7 prediction models for "
        f"[bold]{home.name}[/] vs [bold]{away.name}[/] "
        f"({100_000:,} Monte Carlo simulations)...[/]"
    )
    result = ensemble.run(home, away, market_data=market, neutral=neutral)

    # ── Print full report ─────────────────────────────────────────────────────
    print_report(
        home=home,
        away=away,
        result=result,
        market=market,
        match_date=args.date,
        venue=args.venue,
        competition=args.comp,
        stage=args.stage,
    )


if __name__ == "__main__":
    main()
