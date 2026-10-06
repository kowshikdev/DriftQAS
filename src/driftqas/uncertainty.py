"""Frozen, posthoc seed-cluster interval calibration; never online feedback.

One maximum residual per seed includes every declared case, epoch and candidate.
The order statistic follows the split-calibration rank construction. It requires
exchangeable independent seed clusters for a coverage interpretation. It does not
certify arbitrary hardware drift, unknown noise or adaptive online stopping.
"""

import math
from pathlib import Path

import numpy as np

from driftqas.diagnostics import diagnostic_rows
from driftqas.protocol import protocol_declaration
from driftqas.provenance import canonical, digest, read_json, write_json
from driftqas.reporting import _csv
from driftqas.statistics import NORMAL_95


def cluster_quantile(scores, alpha: float) -> tuple[float, int]:
    values = np.asarray(scores, dtype=float)
    if (
        values.ndim != 1
        or not values.size
        or not np.isfinite(values).all()
        or np.any(values < 0)
        or not np.isfinite(alpha)
        or not 0 < alpha < 1
    ):
        raise ValueError("Calibration needs finite nonnegative cluster scores and 0 < alpha < 1")
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    if rank > len(values):
        raise ValueError("Too few calibration seed clusters for a finite interval at this alpha")
    return max(1.0, float(np.sort(values)[rank - 1])), rank


def _frozen(manifest: dict) -> dict:
    frozen = manifest.get("frozen_protocol", {})
    payload = {key: value for key, value in frozen.items() if key != "frozen_id"}
    if frozen.get("schema_version") != 1 or digest(payload) != frozen.get("frozen_id"):
        raise ValueError("A valid frozen cross-partition protocol is required")
    if canonical(frozen["runtime"]) != canonical(manifest["runtime"]) or canonical(
        frozen["declaration"]
    ) != canonical(protocol_declaration(manifest["declaration"])):
        raise ValueError("Suite does not match its frozen protocol")
    return frozen


def fit_calibration(suite_dir: Path, output: Path) -> dict:
    if output.exists():
        raise ValueError(f"Refusing to overwrite interval calibration: {output}")
    manifest, _, predictions, _ = diagnostic_rows(suite_dir)
    if manifest["declaration"]["split"] != "calibration":
        raise ValueError("Fit uncertainty scales only on the separate calibration partition")
    frozen = _frozen(manifest)
    settings = frozen["interval_calibration"]
    alpha, floor = settings["alpha"], settings["standard_deviation_floor"]
    seeds = manifest["declaration"]["seed_sets"]["calibration"]
    policies = manifest["declaration"]["cases"][0]["configuration"]["policies"]
    scales, scores, ranks = {}, {}, {}
    for policy in policies:
        scores[policy] = [
            {
                "seed": seed,
                "score": max(
                    abs(row["predicted_energy"] - row["audit_energy"])
                    / (NORMAL_95 * max(floor, row["model_standard_deviation"]))
                    for row in predictions
                    if row["policy"] == policy and row["seed"] == seed
                ),
            }
            for seed in seeds
        ]
        scales[policy], ranks[policy] = cluster_quantile(
            [row["score"] for row in scores[policy]], alpha
        )
    result = {
        "schema_version": 1,
        "frozen_id": frozen["frozen_id"],
        "calibration_suite_digest": manifest["protocol_digest"],
        "calibration_seeds": seeds,
        "settings": settings,
        "temperatures": scales,
        "order_statistic_ranks": ranks,
        "seed_cluster_scores": scores,
        "interpretation": "Posthoc intervals only, not policy tuning or an anytime-valid racing "
        "bound. Per-policy joint seed coverage depends on exchangeable seed clusters under the "
        "identical frozen simulation protocol; no guarantee for arbitrary distribution shift. "
        "Policies are not covered simultaneously by a multiplicity-adjusted guarantee.",
    }
    result["calibration_id"] = digest(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, result)
    return result


def read_calibration(path: Path) -> dict:
    artifact = read_json(path)
    payload = {key: value for key, value in artifact.items() if key != "calibration_id"}
    if artifact.get("schema_version") != 1 or digest(payload) != artifact.get("calibration_id"):
        raise ValueError("Interval calibration schema/digest mismatch")
    return artifact


def evaluate_calibration(suite_dir: Path, calibration_path: Path) -> dict:
    manifest, _, predictions, _ = diagnostic_rows(suite_dir)
    if manifest["declaration"]["split"] != "held_out":
        raise ValueError("Evaluate calibrated intervals on the held_out partition only")
    frozen, artifact = _frozen(manifest), read_calibration(calibration_path)
    if (
        frozen["frozen_id"] != artifact["frozen_id"]
        or artifact["settings"] != frozen["interval_calibration"]
    ):
        raise ValueError("Calibration/test frozen protocol mismatch")
    seed_sets = manifest["declaration"]["seed_sets"]
    seeds, calibration_seeds = seed_sets["held_out"], artifact["calibration_seeds"]
    if calibration_seeds != seed_sets["calibration"] or set(seeds) & set(calibration_seeds):
        raise ValueError("Calibration/test seed mismatch or overlap")
    policies = manifest["declaration"]["cases"][0]["configuration"]["policies"]
    if set(artifact["temperatures"]) != set(policies):
        raise ValueError("Calibration policy mismatch")
    settings = artifact["settings"]
    floor = settings["standard_deviation_floor"]
    cluster_rows, summaries = [], []
    for policy in policies:
        score_rows = artifact["seed_cluster_scores"][policy]
        if [r["seed"] for r in score_rows] != calibration_seeds:
            raise ValueError("Calibration score seed mismatch")
        temperature, rank = cluster_quantile([r["score"] for r in score_rows], settings["alpha"])
        if (
            temperature != artifact["temperatures"][policy]
            or rank != artifact["order_statistic_ranks"][policy]
        ):
            raise ValueError("Calibration order statistic mismatch")
        for seed in seeds:
            rows = [r for r in predictions if r["policy"] == policy and r["seed"] == seed]
            residuals = np.array([abs(r["predicted_energy"] - r["audit_energy"]) for r in rows])
            raw = NORMAL_95 * np.array([r["model_standard_deviation"] for r in rows])
            calibrated = temperature * np.maximum(raw, NORMAL_95 * floor)
            selected = np.array([r["selected"] for r in rows])
            raw_covered, covered = residuals <= raw + 1e-12, residuals <= calibrated + 1e-12
            cluster_rows.append(
                {
                    "policy": policy,
                    "seed": seed,
                    "raw_selected_coverage": float(raw_covered[selected].mean()),
                    "calibrated_selected_coverage": float(covered[selected].mean()),
                    "raw_full_bank_coverage": float(raw_covered.mean()),
                    "calibrated_full_bank_coverage": float(covered.mean()),
                    "raw_joint_seed_coverage": bool(raw_covered.all()),
                    "calibrated_joint_seed_coverage": bool(covered.all()),
                    "mean_raw_width": float((2 * raw).mean()),
                    "mean_calibrated_width": float((2 * calibrated).mean()),
                    "mean_selected_calibrated_width": float((2 * calibrated[selected]).mean()),
                }
            )
        rows = [r for r in cluster_rows if r["policy"] == policy]
        metrics = [name for name in rows[0] if name not in {"seed", "policy"}]
        summaries.append(
            {
                "policy": policy,
                "n_seed_clusters": len(seeds),
                "temperature": temperature,
                **{metric: float(np.mean([r[metric] for r in rows])) for metric in metrics},
            }
        )
    result = {
        "schema_version": 1,
        "frozen_id": frozen["frozen_id"],
        "held_out_suite_digest": manifest["protocol_digest"],
        "calibration_id": artifact["calibration_id"],
        "nominal_joint_seed_coverage": 1 - settings["alpha"],
        "calibration_seed_clusters": len(calibration_seeds),
        "held_out_seed_clusters": len(seeds),
        "policy_summaries": summaries,
        "notes": [
            artifact["interpretation"],
            "Raw Gaussian intervals and floored/scaled intervals are reported separately.",
            "One joint trial is one seed spanning every declared case, epoch and bank candidate.",
            "Selected/full-bank rates are descriptive; "
            "correlated points are not independent trials.",
            "Higher coverage with very wide intervals is not evidence of a useful precise model.",
        ],
    }
    _csv(suite_dir / "calibrated_seed_coverage.csv", cluster_rows)
    _csv(suite_dir / "calibrated_policy_summary.csv", summaries)
    write_json(suite_dir / "calibrated_summary.json", result)
    return result
