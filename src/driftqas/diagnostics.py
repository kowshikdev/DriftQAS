"""Read-only exposure, rank-reversal and full-bank prediction diagnostics.

These functions consume completed, sealed episodes only. They have no interface to
the online controller, and exact audit energies must remain offline.
"""

import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from driftqas.benchmark import completed_episodes, episode_directory
from driftqas.calibration import Calibration
from driftqas.provenance import read_json, write_json
from driftqas.reporting import _csv

TOLERANCE = 1e-8


def _finite(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(f"Nonfinite/invalid diagnostic value: {label}")
    return float(value)


def _unique(records: list[dict], kind: str, key) -> dict:
    selected = [record for record in records if record["kind"] == kind]
    result = {key(record["payload"]): record for record in selected}
    if len(result) != len(selected):
        raise ValueError(f"Duplicate {kind} diagnostic events")
    return result


def diagnostic_rows(output: Path) -> tuple[dict, list[dict], list[dict], list[dict]]:
    manifest, completed = completed_episodes(output)
    exposure_rows, prediction_rows, episode_rows = [], [], []
    for episode, summary in completed:
        root = episode_directory(output, episode)
        attempt = root / read_json(root / "completed.json")["attempt"]
        candidates = json.loads((attempt / "candidates.json").read_text(encoding="utf-8"))
        config = episode["configuration"]
        ids = [candidate["candidate_id"] for candidate in candidates]
        if len(set(ids)) != config["candidates"] or len(ids) != config["candidates"]:
            raise ValueError("Incomplete/duplicate diagnostic candidate bank")
        records = [
            json.loads(line)
            for line in (attempt / "experiments.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        expected = {
            (policy, epoch) for policy in config["policies"] for epoch in range(config["epochs"])
        }
        calibrations = _unique(records, "calibration", lambda p: (p["policy"], p["epoch"]))
        predictions = _unique(records, "locked_predictions", lambda p: (p["policy"], p["epoch"]))
        locks = _unique(records, "locked_recommendation", lambda p: (p["policy"], p["epoch"]))
        confirmations = _unique(
            [
                record
                for record in records
                if record["kind"] == "measurement" and record["payload"]["phase"] == "confirmation"
            ],
            "measurement",
            lambda p: (p["policy"], p["epoch"]),
        )
        if any(
            set(mapping) != expected
            for mapping in (calibrations, predictions, locks, confirmations)
        ):
            raise ValueError("Complete full-bank locked predictions required (v0.4 episodes)")
        audits = _unique(records, "offline_audit", lambda p: (p["epoch"], p["candidate_id"]))
        if set(audits) != {
            (epoch, identifier) for epoch in range(config["epochs"]) for identifier in ids
        }:
            raise ValueError("Incomplete diagnostic audit grid")
        if min(record["id"] for record in audits.values()) <= max(
            record["id"] for record in confirmations.values()
        ) or any(
            record["payload"].get("policy_visible") is not False for record in audits.values()
        ):
            raise ValueError("Audit must be offline and after every policy confirmation")
        energies = {
            key: _finite(record["payload"]["energy"], "audit") for key, record in audits.items()
        }
        outcomes = {(r["policy"], r["epoch"]): r for r in summary["outcomes"]}
        snapshots = {}
        prefix = {"case_id": episode["case_id"], "seed": episode["seed"]}
        for policy, epoch in sorted(expected):
            key = (policy, epoch)
            payload = calibrations[key]["payload"]
            calibration = Calibration(epoch, payload["errors"], payload["scenario"])
            if calibration.calibration_id != payload["calibration_id"]:
                raise ValueError("Diagnostic calibration identity mismatch")
            if epoch in snapshots and snapshots[epoch] != calibration:
                raise ValueError("Policies must see the same calibration")
            snapshots[epoch] = calibration
            prediction, lock, confirmation = predictions[key], locks[key], confirmations[key]
            if not prediction["id"] < lock["id"] < confirmation["id"]:
                raise ValueError("Predictions must be locked before independent confirmation")
            if prediction["payload"]["calibration_id"] != calibration.calibration_id:
                raise ValueError("Locked prediction calibration mismatch")
            estimates = prediction["payload"]["predictions"]
            if len(estimates) != len(ids) or {r["candidate_id"] for r in estimates} != set(ids):
                raise ValueError("Incomplete/duplicate full-bank prediction grid")
            selected = lock["payload"]["candidate_id"]
            if selected not in ids or confirmation["payload"]["candidate_id"] != selected:
                raise ValueError("Locked recommendation/confirmation candidate mismatch")
            for estimate in estimates:
                identifier = estimate["candidate_id"]
                mean = _finite(estimate["predicted_energy"], "predicted energy")
                std = _finite(estimate["model_standard_deviation"], "model SD")
                if std < 0:
                    raise ValueError("Diagnostic model SD must be nonnegative")
                if identifier == selected:
                    for name in ("predicted_energy", "model_standard_deviation"):
                        if (
                            estimate[name] != lock["payload"][name]
                            or estimate[name] != outcomes[key][name]
                        ):
                            raise ValueError("Locked full-bank/selected prediction mismatch")
                    if abs(energies[(epoch, identifier)] - outcomes[key]["audit_energy"]) > 1e-12:
                        raise ValueError("Selected summary/audit mismatch")
                prediction_rows.append(
                    {
                        **prefix,
                        "policy": policy,
                        "epoch": epoch,
                        "candidate_id": identifier,
                        "selected": identifier == selected,
                        "predicted_energy": mean,
                        "model_standard_deviation": std,
                        "audit_energy": energies[(epoch, identifier)],
                    }
                )
        initial_best = min(ids, key=lambda identifier: energies[(0, identifier)])
        opportunities, correlations = [], []
        changed_transitions, rank_reversals = 0, 0
        local_pairs = []
        for epoch in range(1, config["epochs"]):
            old, current = snapshots[epoch - 1], snapshots[epoch]
            changed = old.errors != current.errors
            changed_transitions += changed
            previous_best = min(ids, key=lambda identifier: energies[(epoch - 1, identifier)])
            opportunity = energies[(epoch, previous_best)] - min(energies[(epoch, i)] for i in ids)
            opportunities.append(opportunity)
            rank_reversals += opportunity > TOLERANCE
            pairs = []
            for candidate in candidates:
                identifier = candidate["candidate_id"]
                shift = energies[(epoch, identifier)] - energies[(epoch - 1, identifier)]
                exposure = current.exposure(candidate["footprint"], old, config["drift_scale"])
                pairs.append(
                    {
                        **prefix,
                        "epoch": epoch,
                        "calibration_changed": changed,
                        "candidate_id": identifier,
                        "exposure": exposure,
                        "energy_shift": shift,
                        "absolute_energy_shift": abs(shift),
                        "zero_exposure_violation": exposure == 0 and abs(shift) > TOLERANCE,
                        "previous_best_regret": opportunity,
                    }
                )
            x = [row["exposure"] for row in pairs]
            y = [row["absolute_energy_shift"] for row in pairs]
            if changed and np.ptp(x) > TOLERANCE and np.ptp(y) > TOLERANCE:
                correlations.append(float(spearmanr(x, y).statistic))
            exposure_rows.extend(pairs)
            local_pairs.extend(pairs)
        episode_rows.append(
            {
                **prefix,
                "changed_transitions": int(changed_transitions),
                "rank_reversals": int(rank_reversals),
                "mean_transition_opportunity": float(np.mean(opportunities))
                if opportunities
                else 0.0,
                "max_transition_opportunity": max(opportunities, default=0.0),
                "mean_initial_best_regret": float(
                    np.mean(
                        [
                            energies[(epoch, initial_best)] - min(energies[(epoch, i)] for i in ids)
                            for epoch in range(config["epochs"])
                        ]
                    )
                ),
                "exposure_shift_spearman": float(np.mean(correlations)) if correlations else None,
                "zero_exposure_pairs": sum(row["exposure"] == 0 for row in local_pairs),
                "zero_exposure_violations": sum(
                    row["zero_exposure_violation"] for row in local_pairs
                ),
            }
        )
    return manifest, exposure_rows, prediction_rows, episode_rows


def analyze_diagnostics(output: Path) -> dict:
    manifest, exposures, predictions, episodes = diagnostic_rows(output)
    cases = [case["case_id"] for case in manifest["declaration"]["cases"]]
    summaries = []
    for case in cases:
        rows = [row for row in episodes if row["case_id"] == case]
        correlations = [
            r["exposure_shift_spearman"] for r in rows if r["exposure_shift_spearman"] is not None
        ]
        summaries.append(
            {
                "case_id": case,
                "n_seed_clusters": len(rows),
                "seeds_with_rank_reversal": sum(r["rank_reversals"] > 0 for r in rows),
                "mean_transition_opportunity": float(
                    np.mean([r["mean_transition_opportunity"] for r in rows])
                ),
                "mean_initial_best_regret": float(
                    np.mean([r["mean_initial_best_regret"] for r in rows])
                ),
                "mean_exposure_shift_spearman": float(np.mean(correlations))
                if correlations
                else None,
                "n_seeds_with_defined_correlation": len(correlations),
                "zero_exposure_violations": sum(r["zero_exposure_violations"] for r in rows),
            }
        )
    result = {
        "schema_version": 1,
        "protocol_digest": manifest["protocol_digest"],
        "case_summaries": summaries,
        "notes": [
            "Rank reversal requires previous winner regret > 1e-8, not an ID change among ties.",
            "Opportunity uses exact audits for diagnostics only, never for policy decisions.",
            "Correlation is descriptive within a bank/transition, averaged within a seed first.",
            "Constant-exposure or constant-shift correlations are undefined, not zero.",
            "Zero-exposure invariance is specific to the synthetic CX-only noise model.",
        ],
    }
    if exposures:
        _csv(output / "exposure_pairs.csv", exposures)
    _csv(output / "prediction_diagnostics.csv", predictions)
    _csv(output / "exposure_episodes.csv", episodes)
    write_json(output / "diagnostics_summary.json", result)
    return result
