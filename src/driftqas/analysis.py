"""Portable comparison tables and figures; no fabricated research conclusions."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze(directory: Path) -> dict:
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    rows = summary["outcomes"]
    fields = [
        "policy",
        "epoch",
        "candidate_id",
        "shots",
        "budget_limit",
        "confirmation_energy",
        "confirmation_standard_error",
        "audit_energy",
        "best_library_energy",
        "selection_regret",
        "ground_state_excess",
    ]
    with (directory / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for policy in dict.fromkeys(row["policy"] for row in rows):
        selected = [row for row in rows if row["policy"] == policy]
        epochs = [r["epoch"] for r in selected]
        axes[0].plot(epochs, [r["selection_regret"] for r in selected], "o-", label=policy)
        axes[1].plot(epochs, [r["shots"] for r in selected], "o-", label=policy)
    axes[0].set(xlabel="Calibration epoch", ylabel="Offline selection regret")
    axes[1].set(xlabel="Calibration epoch", ylabel="Total sampled shots per epoch")
    axes[1].set_ylim(bottom=0)
    for axis in axes:
        axis.grid(alpha=0.2)
    axes[0].legend(fontsize=8)
    figure.suptitle("Simulated drift — single-run development comparison")
    figure.savefig(directory / "comparison.png", dpi=160)
    plt.close(figure)
    return {
        "rows": len(rows),
        "comparison": str(directory / "comparison.csv"),
        "figure": str(directory / "comparison.png"),
    }
