"""Posthoc locality diagnostics on every episode of a verified complete suite."""

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from driftqas.benchmark import episode_directory
from driftqas.calibration import snapshot
from driftqas.diagnostics import diagnostic_rows
from driftqas.provenance import read_json, write_json
from driftqas.reporting import _csv
from driftqas.screening import transition_metrics


def analyze(suite_dir: Path) -> dict:
    manifest, _, predictions, _ = diagnostic_rows(suite_dir)
    audits = {
        (r["case_id"], r["seed"], r["epoch"], r["candidate_id"]): r["audit_energy"]
        for r in predictions
    }
    transitions = []
    for episode in manifest["episodes"]:
        root = episode_directory(suite_dir, episode)
        attempt = root / read_json(root / "completed.json")["attempt"]
        bank = [
            SimpleNamespace(candidate_id=c["candidate_id"], footprint=c["footprint"])
            for c in read_json(attempt / "candidates.json")
        ]
        c = episode["configuration"]
        previous, old = None, None
        for epoch in range(c["epochs"]):
            calibration = snapshot(
                c["n_qubits"],
                epoch,
                c["epochs"],
                c["scenario"],
                c["base_error"],
                c["drift_error"],
                c["changed_edge"],
            )
            energies = {
                candidate.candidate_id: audits[
                    (episode["case_id"], episode["seed"], epoch, candidate.candidate_id)
                ]
                for candidate in bank
            }
            if previous is not None:
                transitions.append(
                    {
                        "case_id": episode["case_id"],
                        "seed": episode["seed"],
                        "epoch": epoch,
                        **transition_metrics(bank, old, calibration, previous, energies),
                    }
                )
            previous, old = energies, calibration
    summaries = []
    for case in manifest["declaration"]["cases"]:
        rows = [r for r in transitions if r["case_id"] == case["case_id"]]
        summaries.append(
            {
                "case_id": case["case_id"],
                "n_seed_clusters": len({r["seed"] for r in rows}),
                "seeds_with_winner_set_reversal": len(
                    {r["seed"] for r in rows if r["winner_set_reversal"]}
                ),
                "seeds_with_locality_opportunity": len(
                    {r["seed"] for r in rows if r["locality_opportunity"]}
                ),
                "zero_exposure_violations": sum(r["zero_exposure_violations"] for r in rows),
            }
        )
    result = {
        "schema_version": 1,
        "protocol_digest": manifest["protocol_digest"],
        "split": manifest["declaration"]["split"],
        "case_summaries": summaries,
        "meaning": "Posthoc diagnostics for ALL declared seeds/cases. No screening, "
        "case exclusion, primary-contrast change, policy feedback or tuning. The tie-aware "
        "definition is fixed in the pre-test development protocol.",
    }
    _csv(suite_dir / "locality_transitions.csv", transitions)
    write_json(suite_dir / "locality_summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.suite_dir), indent=2))


if __name__ == "__main__":
    main()
