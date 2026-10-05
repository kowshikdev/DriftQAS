"""Small CLI for declared configuration-driven runs."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from driftqas.analysis import analyze
from driftqas.config import load_config
from driftqas.runner import run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="driftqas")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "compare"):
        command = subcommands.add_parser(name, help="Run the policies declared in a configuration")
        command.add_argument("--config", type=Path, required=True)
        command.add_argument("--output", type=Path)
    analysis = subcommands.add_parser("analyze", help="Export CSV and plot from a completed run")
    analysis.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            print(json.dumps(analyze(args.run_dir), indent=2))
        else:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            output = args.output or Path("results") / timestamp
            run(load_config(args.config), output)
            print(json.dumps(analyze(output), indent=2))
            print(f"Completed: {output.resolve()}")
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    return 0
