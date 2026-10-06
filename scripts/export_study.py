"""Export compact, verified v0.4 reports without pretending they are raw suites."""

import argparse
import shutil
from pathlib import Path

from driftqas.benchmark import completed_episodes, episode_directory
from driftqas.diagnostics import analyze_diagnostics
from driftqas.provenance import file_digest, read_json, write_json
from driftqas.reporting import analyze_suite

REPORTS = (
    "suite_manifest.json",
    "suite_status.json",
    "suite_summary.json",
    "report.md",
    "episodes.csv",
    "policy_summary.csv",
    "paired_comparisons.csv",
    "diagnostics_summary.json",
    "exposure_episodes.csv",
)
CALIBRATED = (
    "calibrated_summary.json",
    "calibrated_seed_coverage.csv",
    "calibrated_policy_summary.csv",
)


def export(suite_dir: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError(f"Choose a new compact-export directory: {output}")
    manifest, completed = completed_episodes(suite_dir)
    if read_json(suite_dir / "suite_status.json").get("status") != "completed":
        raise ValueError("Export only a suite marked completed")
    analyze_suite(suite_dir)
    analyze_diagnostics(suite_dir)
    names = [*REPORTS]
    if (suite_dir / CALIBRATED[0]).exists():
        calibrated = read_json(suite_dir / CALIBRATED[0])
        if calibrated["held_out_suite_digest"] != manifest["protocol_digest"]:
            raise ValueError("Calibrated report does not match suite")
        names.extend(CALIBRATED)
    receipts = []
    for episode, _ in completed:
        root = episode_directory(suite_dir, episode)
        receipt = read_json(root / "completed.json")
        receipts.append(
            {
                "case_id": episode["case_id"],
                "seed": episode["seed"],
                "attempt": receipt["attempt"],
                "completion_receipt_sha256": file_digest(root / "completed.json"),
                "core_artifact_sha256": {
                    name: receipt["hashes"][name]
                    for name in (
                        "manifest.json",
                        "summary.json",
                        "candidates.json",
                        "experiments.jsonl",
                        "experiments.sqlite",
                    )
                },
            }
        )
    output.mkdir(parents=True)
    for name in names:
        shutil.copyfile(suite_dir / name, output / name)
    write_json(output / "audit_receipts.json", {"episodes": receipts})
    result = {
        "schema_version": 1,
        "suite_protocol_digest": manifest["protocol_digest"],
        "complete_paired_episodes": len(completed),
        "files_sha256": {
            name: file_digest(output / name) for name in [*names, "audit_receipts.json"]
        },
        "scope": "Compact verified reports and raw artifact hashes only. Raw databases, "
        "counts, QASM and original completion receipts are not included. This export cannot "
        "be used as input to analyze-suite, diagnose-suite, or interval fitting/evaluation. "
        "Rerun the declared configuration to regenerate complete suites.",
    }
    write_json(output / "export_receipt.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = export(args.suite_dir, args.output)
    print(f"Exported {result['complete_paired_episodes']} verified episodes to {args.output}")


if __name__ == "__main__":
    main()
