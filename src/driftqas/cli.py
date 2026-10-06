"""Small CLI for declared configuration-driven runs."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from driftqas.analysis import analyze
from driftqas.benchmark import run_suite
from driftqas.config import load_config
from driftqas.reporting import analyze_suite
from driftqas.runner import run
from driftqas.suite_config import load_suite


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="driftqas")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "compare"):
        command = subcommands.add_parser(name, help="Run the policies declared in a configuration")
        command.add_argument("--config", type=Path, required=True)
        command.add_argument("--output", type=Path)
    analysis = subcommands.add_parser("analyze", help="Export CSV and plot from a completed run")
    analysis.add_argument("--run-dir", type=Path, required=True)
    suite = subcommands.add_parser("suite", help="Run a declared repeated-seed benchmark suite")
    suite.add_argument("--config", type=Path, required=True)
    suite.add_argument("--output", type=Path)
    modes = suite.add_mutually_exclusive_group()
    modes.add_argument(
        "--plan", action="store_true", help="Validate and print costs without execution"
    )
    modes.add_argument("--resume", action="store_true", help="Verify and skip completed episodes")
    report = subcommands.add_parser("analyze-suite", help="Verify and report a complete suite")
    report.add_argument("--suite-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            print(json.dumps(analyze(args.run_dir), indent=2))
        elif args.command == "analyze-suite":
            print(json.dumps(analyze_suite(args.suite_dir), indent=2))
        elif args.command == "suite":
            declared = load_suite(args.config)
            if args.plan:
                print(json.dumps(declared.plan(), indent=2))
            else:
                if args.resume and args.output is None:
                    raise ValueError("--resume requires --output pointing to the original suite")
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                output = args.output or Path("results") / f"{declared.name}-{timestamp}"
                print(json.dumps(run_suite(declared, output, args.resume), indent=2))
                print(f"Completed: {output.resolve()}")
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            output = args.output or Path("results") / timestamp
            run(load_config(args.config), output)
            print(json.dumps(analyze(output), indent=2))
            print(f"Completed: {output.resolve()}")
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    return 0
