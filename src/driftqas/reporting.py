"""Complete-pair reports with seed-cluster uncertainty and coverage diagnostics."""

import csv
from pathlib import Path

import numpy as np

from driftqas.benchmark import completed_episodes
from driftqas.provenance import write_json
from driftqas.runner import measurement_seed
from driftqas.statistics import MIN_INTERVAL_SEEDS, episode_metrics, paired_interval
from driftqas.suite_config import PRIMARY_METRIC


def _csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _interval_text(row: dict) -> str:
    if row["ci95_low"] is None:
        return f"unavailable (fewer than {MIN_INTERVAL_SEEDS} seeds)"
    return f"[{row['ci95_low']:.6g}, {row['ci95_high']:.6g}]"


def analyze_suite(output: Path) -> dict:
    # No report is written until every declared episode/policy/epoch and seal verifies.
    manifest, completed = completed_episodes(output)
    declaration = manifest["declaration"]
    seeds = declaration["seed_sets"][declaration["split"]]
    cases = [case["case_id"] for case in declaration["cases"]]
    policies = declaration["cases"][0]["configuration"]["policies"]
    target, primary_comparator = declaration["primary_target"], declaration["primary_comparator"]
    rows, index = [], {}
    for episode, summary in completed:
        for metrics in episode_metrics(summary, episode["configuration"]):
            row = {
                "case_id": episode["case_id"],
                "seed": episode["seed"],
                "split": declaration["split"],
                **metrics,
            }
            rows.append(row)
            index[(row["case_id"], row["seed"], row["policy"])] = row
    metric_names = [name for name in rows[0] if name not in {"case_id", "seed", "split", "policy"}]
    summaries, contrasts = [], []
    for scope in ["all_cases", *cases]:
        included = cases if scope == "all_cases" else [scope]
        for policy in policies:
            summaries.append(
                {
                    "scope": scope,
                    "policy": policy,
                    "n_seed_clusters": len(seeds),
                    "n_cases": len(included),
                    **{
                        metric: float(
                            np.mean(
                                [
                                    np.mean(
                                        [index[(case, seed, policy)][metric] for case in included]
                                    )
                                    for seed in seeds
                                ]
                            )
                        )
                        for metric in metric_names
                    },
                }
            )
        for comparator in policies:
            if comparator == target:
                continue
            for metric in (PRIMARY_METRIC, "final_selection_regret", "mean_shots"):
                # Same seed may share a bank across cases. Average within that cluster
                # first, then bootstrap clusters, preserving pairing and dependence.
                differences = [
                    float(
                        np.mean(
                            [
                                index[(case, seed, target)][metric]
                                - index[(case, seed, comparator)][metric]
                                for case in included
                            ]
                        )
                    )
                    for seed in seeds
                ]
                contrasts.append(
                    {
                        "scope": scope,
                        "target": target,
                        "comparator": comparator,
                        "metric": metric,
                        "primary": scope == "all_cases"
                        and comparator == primary_comparator
                        and metric == PRIMARY_METRIC,
                        **paired_interval(
                            differences,
                            declaration["bootstrap_samples"],
                            measurement_seed(
                                declaration["bootstrap_seed"], scope, comparator, metric
                            ),
                        ),
                    }
                )
    primary = next(row for row in contrasts if row["primary"])
    notes = [
        "Differences are target minus comparator; negative regret differences favor target.",
        "Primary metric averages all declared epochs, then cases equally within seed, then seeds.",
        "Independent seed clusters are the resampling units, "
        "not shots, epochs, policies, or cases.",
        f"95% percentile intervals are withheld below {MIN_INTERVAL_SEEDS} seeds. This threshold "
        "does not guarantee sufficient power or accurate bootstrap coverage.",
        "One contrast is primary. Other intervals are descriptive and unadjusted for multiplicity.",
        "Coverage uses locked mean +/- 1.959964 model SD or independent confirmation SE against "
        "the later exact noisy audit. It is a diagnostic, not a calibration guarantee.",
        "Coverage is averaged by episode and seed; "
        "correlated epochs are not independent coverage trials.",
        "A suite with mixed Hamiltonians reports an equal-weight raw-energy macro average. "
        "Use per-case results for physical interpretation.",
        "A held_out label records declared intent; it cannot prove seeds were never inspected.",
        "Frozen library, frozen parameters, synthetic CX noise; no hardware or superiority claim.",
    ]
    result = {
        "schema_version": 1,
        "name": declaration["name"],
        "split": declaration["split"],
        "protocol_digest": manifest["protocol_digest"],
        "complete_pairs": len(completed),
        "n_seed_clusters": len(seeds),
        "primary_analysis": primary,
        "policy_summaries": summaries,
        "paired_comparisons": contrasts,
        "notes": notes,
    }
    _csv(output / "episodes.csv", rows)
    _csv(output / "policy_summary.csv", summaries)
    _csv(output / "paired_comparisons.csv", contrasts)
    write_json(output / "suite_summary.json", result)
    lines = [
        f"# {declaration['name']} ({declaration['split']})",
        "",
        f"Complete paired episodes: **{len(completed)}**; "
        f"independent seed clusters: **{len(seeds)}**.",
        f"Protocol: `{manifest['protocol_digest']}`.",
        "",
        f"Primary contrast: **{target} minus {primary_comparator}**, mean selection regret.",
        f"Mean difference: **{primary['mean_difference']:.6g}**; "
        f"95% interval: {_interval_text(primary)}.",
        "Negative differences favor the target. This development or declared held-out report "
        "does not itself establish superiority.",
        "",
        "## Declared cases",
        "",
        "| Case | Task | Profile | Epochs | Shot limit / epoch |",
        "|---|---|---|---:|---:|",
    ]
    for case in declaration["cases"]:
        config = case["configuration"]
        task = (
            "H2"
            if config["task"] == "h2"
            else f"Ising {config['n_qubits']}q, field {config['field']}"
        )
        lines.append(
            f"| {case['case_id']} | {task} | {config['scenario']} | "
            f"{config['epochs']} | {config['budget_per_epoch']} |"
        )
    lines.extend(
        [
            "",
            "## Paired mean-regret contrasts",
            "",
            "| Scope | Comparator | Difference | 95% interval | Better / tie / worse seeds |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in contrasts:
        if row["metric"] == PRIMARY_METRIC:
            lines.append(
                f"| {row['scope']} | {row['comparator']} | {row['mean_difference']:.6g} | "
                f"{_interval_text(row)} | {row['target_better_seeds']} / "
                f"{row['tied_seeds']} / {row['target_worse_seeds']} |"
            )
    lines.extend(
        [
            "",
            "## Coverage and resource diagnostics (all cases)",
            "",
            "| Policy | Mean regret | Budget used | Confirmation coverage | Model coverage | "
            "Zero confirmation SE |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summaries:
        if row["scope"] == "all_cases":
            lines.append(
                f"| {row['policy']} | {row[PRIMARY_METRIC]:.6g} | "
                f"{row['budget_utilization']:.1%} | {row['confirmation_coverage_95']:.1%} | "
                f"{row['model_coverage_95']:.1%} | {row['confirmation_zero_se_fraction']:.1%} |"
            )
    lines.extend(["", "## Interpretation", "", *[f"- {note}" for note in notes], ""])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "report": str(output / "report.md"),
        "summary": str(output / "suite_summary.json"),
        "complete_pairs": len(completed),
        "primary_analysis": primary,
    }
