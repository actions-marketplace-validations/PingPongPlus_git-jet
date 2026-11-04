"""Live and offline rendering with a network-free synthetic demo."""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from .art import CARRIERS, DEFAULT_CARRIER, DEFAULT_GRAPH_THEME, GRAPH_THEMES
from .calendar import Calendar
from .demo import demo_calendar
from .export import Options, render_assets
from .github import GitHubClient, GitHubError
from .water import DEFAULT_WATER, WATER_STYLES


def main(argv=None):
    parser = argparse.ArgumentParser(prog="git-jet")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect", help="collect a real UTC commit calendar")
    collect.add_argument("--username", required=True)
    collect.add_argument("--days", type=int, default=365)
    collect.add_argument("--end-date", type=date.fromisoformat)
    collect.add_argument("--output", type=Path, default=Path("out/calendar.json"))
    render = sub.add_parser("render", help="generate transparent GIF/PNG assets")
    source = render.add_mutually_exclusive_group(required=True)
    source.add_argument("--username")
    source.add_argument("--demo", action="store_true")
    source.add_argument("--calendar", type=Path)
    render.add_argument("--days", type=int)
    render.add_argument("--end-date", type=date.fromisoformat)
    render.add_argument("--scale", type=int, default=2)
    render.add_argument("--fps", type=int, default=20)
    render.add_argument(
        "--carrier",
        choices=CARRIERS,
        default=DEFAULT_CARRIER,
        help="carrier artwork (default: lincoln)",
    )
    render.add_argument(
        "--water",
        choices=WATER_STYLES,
        default=DEFAULT_WATER,
        help="water artwork: ocean or original (default: ocean)",
    )
    render.add_argument(
        "--graph-theme",
        choices=GRAPH_THEMES,
        default=DEFAULT_GRAPH_THEME,
        help="calendar colors: blue (default) or github (green)",
    )
    render.add_argument(
        "--jets", type=int, choices=(1, 2, 3), default=1, help="simultaneous jets (default: 1)"
    )
    render.add_argument("--seed", help="reproduce a route; omit for fresh randomness on each run")
    render.add_argument(
        "--auto-compress",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="lower scale, then FPS when needed to fit GIF limits (default: enabled)",
    )
    render.add_argument("--output-dir", type=Path, default=Path("out"))
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            options = Options(args.scale, args.fps)
            if args.demo:
                calendar, source_name = (
                    demo_calendar(args.days if args.days is not None else 365),
                    "demo",
                )
            elif args.calendar:
                calendar, source_name = Calendar.read(args.calendar), "cache"
                if args.days is not None and args.days != len(calendar.days):
                    raise ValueError(
                        "cached calendar has a different day window; collect fresh data"
                    )
            else:
                calendar = GitHubClient(os.environ.get("GITHUB_TOKEN", "")).collect(
                    args.username,
                    days=args.days if args.days is not None else 365,
                    end=args.end_date,
                )
                source_name = "live"
            if args.end_date is not None and calendar.days[-1].date != args.end_date:
                raise ValueError("calendar observation date differs; collect fresh data")
            report = render_assets(
                calendar,
                args.output_dir,
                options,
                jets=args.jets,
                carrier=args.carrier,
                water=args.water,
                graph_theme=args.graph_theme,
                seed=args.seed,
                source=source_name,
                auto_compress=args.auto_compress,
            )
            print(json.dumps(report, indent=2))
            return 0
        calendar = GitHubClient(os.environ.get("GITHUB_TOKEN", "")).collect(
            args.username, days=args.days, end=args.end_date
        )
        calendar.write(args.output)
        print(json.dumps({"calendar": str(args.output.resolve()), "total_commits": calendar.total}))
        return 0
    except (GitHubError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"git-jet: {error}", file=sys.stderr)
        return 1
