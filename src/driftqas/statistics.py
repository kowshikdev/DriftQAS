"""Seed-cluster percentile bootstrap, never treating epochs or shots as replicates."""

import numpy as np

MIN_INTERVAL_SEEDS = 5
NORMAL_95 = 1.959963984540054


def episode_metrics(summary: dict, config: dict) -> list[dict]:
    """Validate a complete episode, then reduce epochs before any inference."""
    outcomes = summary.get("outcomes", [])
    expected = {
        (policy, epoch) for policy in config["policies"] for epoch in range(config["epochs"])
    }
    actual = [(row["policy"], row["epoch"]) for row in outcomes]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Episode has missing, duplicate, or unexpected policy/epoch outcomes")
    numerical = (
        "selection_regret",
        "confirmation_energy",
        "confirmation_standard_error",
        "audit_energy",
        "predicted_energy",
        "model_standard_deviation",
    )
    for row in outcomes:
        if not all(np.isfinite(row[name]) for name in numerical):
            raise ValueError("Episode contains nonfinite outcomes")
        if any(
            row[name] < 0
            for name in (
                "selection_regret",
                "confirmation_standard_error",
                "model_standard_deviation",
            )
        ):
            raise ValueError("Regret and standard errors must be nonnegative")
        if (
            type(row["shots"]) is not int
            or not 0 < row["shots"] <= config["budget_per_epoch"]
            or row["budget_limit"] != config["budget_per_epoch"]
            or sum(row["by_phase"].values()) != row["shots"]
            or row["by_phase"].get("confirmation", 0) <= 0
            or any(type(cost) is not int or cost < 0 for cost in row["by_phase"].values())
        ):
            raise ValueError("Episode shot ledger does not match the declared budget")
    metrics = []
    for policy in config["policies"]:
        rows = sorted(
            (row for row in outcomes if row["policy"] == policy), key=lambda r: r["epoch"]
        )

        def mean(values):
            return float(np.mean(values))

        metrics.append(
            {
                "policy": policy,
                "mean_selection_regret": mean([r["selection_regret"] for r in rows]),
                "final_selection_regret": rows[-1]["selection_regret"],
                "mean_shots": mean([r["shots"] for r in rows]),
                "budget_utilization": mean([r["shots"] / r["budget_limit"] for r in rows]),
                "confirmation_coverage_95": mean(
                    [
                        abs(r["confirmation_energy"] - r["audit_energy"])
                        <= NORMAL_95 * r["confirmation_standard_error"] + 1e-12
                        for r in rows
                    ]
                ),
                "model_coverage_95": mean(
                    [
                        abs(r["predicted_energy"] - r["audit_energy"])
                        <= NORMAL_95 * r["model_standard_deviation"] + 1e-12
                        for r in rows
                    ]
                ),
                "confirmation_zero_se_fraction": mean(
                    [r["confirmation_standard_error"] == 0 for r in rows]
                ),
                "mean_confirmation_standard_error": mean(
                    [r["confirmation_standard_error"] for r in rows]
                ),
                "mean_model_standard_deviation": mean(
                    [r["model_standard_deviation"] for r in rows]
                ),
                "mean_absolute_prediction_error": mean(
                    [abs(r["predicted_energy"] - r["audit_energy"]) for r in rows]
                ),
            }
        )
    return metrics


def paired_interval(differences, samples: int, seed: int) -> dict:
    """Interval for a mean paired difference; inputs are independent seed clusters.

    When cases share a seed, first average the within-seed paired differences across
    cases. This retains case/epoch dependence rather than multiplying sample size.
    """
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or not values.size or not np.isfinite(values).all():
        raise ValueError("Paired differences must be a nonempty finite vector")
    if type(samples) is not int or not 100 <= samples <= 100000:
        raise ValueError("Use 100–100000 bootstrap samples")
    result = {
        "n_seed_clusters": int(values.size),
        "mean_difference": float(values.mean()),
        "ci95_low": None,
        "ci95_high": None,
        "target_better_seeds": int(np.sum(values < -1e-12)),
        "tied_seeds": int(np.sum(np.abs(values) <= 1e-12)),
        "target_worse_seeds": int(np.sum(values > 1e-12)),
        "interval_status": "insufficient_seeds",
    }
    if values.size < MIN_INTERVAL_SEEDS:
        return result
    rng = np.random.default_rng(seed)
    means = []
    # Bound temporary memory even for large declared sample/seed counts.
    for start in range(0, samples, 256):
        indices = rng.integers(0, values.size, size=(min(256, samples - start), values.size))
        means.append(values[indices].mean(axis=1))
    low, high = np.quantile(np.concatenate(means), [0.025, 0.975])
    result.update(
        {
            "ci95_low": float(low),
            "ci95_high": float(high),
            "interval_status": "computed_unadjusted_percentile",
        }
    )
    return result
