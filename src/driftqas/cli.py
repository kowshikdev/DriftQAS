"""Small CLI for declared configuration-driven runs."""

import argparse
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from driftqas.analysis import analyze
from driftqas.benchmark import run_suite
from driftqas.config import load_config
from driftqas.diagnostics import analyze_diagnostics
from driftqas.protocol import freeze_protocol
from driftqas.reporting import analyze_suite
from driftqas.runner import run
from driftqas.suite_config import load_suite
from driftqas.uncertainty import evaluate_calibration, fit_calibration


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
    suite.add_argument("--split", choices=("development", "calibration", "held_out"))
    suite.add_argument("--frozen", type=Path, help="Cross-partition freeze from development")
    modes = suite.add_mutually_exclusive_group()
    modes.add_argument(
        "--plan", action="store_true", help="Validate and print costs without execution"
    )
    modes.add_argument("--resume", action="store_true", help="Verify and skip completed episodes")
    report = subcommands.add_parser("analyze-suite", help="Verify and report a complete suite")
    report.add_argument("--suite-dir", type=Path, required=True)
    diagnostics = subcommands.add_parser(
        "diagnose-suite", help="Offline exposure/rank/prediction checks"
    )
    diagnostics.add_argument("--suite-dir", type=Path, required=True)
    freeze = subcommands.add_parser(
        "freeze", help="Freeze code, cases and partitions before final study"
    )
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    fit = subcommands.add_parser(
        "calibrate", help="Fit posthoc intervals on separate calibration seeds"
    )
    fit.add_argument("--suite-dir", type=Path, required=True)
    fit.add_argument("--output", type=Path, required=True)
    coverage = subcommands.add_parser(
        "evaluate-calibration", help="Fresh-seed calibrated interval diagnostics"
    )
    coverage.add_argument("--suite-dir", type=Path, required=True)
    coverage.add_argument("--calibration", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            print(json.dumps(analyze(args.run_dir), indent=2))
        elif args.command == "analyze-suite":
            print(json.dumps(analyze_suite(args.suite_dir), indent=2))
        elif args.command == "diagnose-suite":
            print(json.dumps(analyze_diagnostics(args.suite_dir), indent=2))
        elif args.command == "freeze":
            print(json.dumps(freeze_protocol(load_suite(args.config), args.output), indent=2))
        elif args.command == "calibrate":
            print(json.dumps(fit_calibration(args.suite_dir, args.output), indent=2))
        elif args.command == "evaluate-calibration":
            print(json.dumps(evaluate_calibration(args.suite_dir, args.calibration), indent=2))
        elif args.command == "suite":
            declared = load_suite(args.config)
            if args.split:
                if args.split not in declared.seed_sets:
                    raise ValueError(f"No declared seed partition: {args.split}")
                declared = replace(declared, split=args.split)
            if args.plan:
                print(json.dumps(declared.plan(), indent=2))
            else:
                if args.resume and args.output is None:
                    raise ValueError("--resume requires --output pointing to the original suite")
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                output = args.output or Path("results") / f"{declared.name}-{timestamp}"
                print(json.dumps(run_suite(declared, output, args.resume, args.frozen), indent=2))
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
