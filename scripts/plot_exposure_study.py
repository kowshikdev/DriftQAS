"""Plot paired held-out contrasts from a checksum-verified compact study export."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from driftqas.provenance import file_digest, read_json  # noqa: E402

LABELS = {
    "reuse_racing": "Blind racing reuse",
    "reuse": "Original GP reuse",
    "driftqas": "Original GP DriftQAS",
    "fresh_racing": "Fresh racing",
    "global_racing": "Global matching",
    "driftqas_racing_uniform": "Uniform component matching",
    "ideal_only": "Ideal-only selection",
}


def plot(export_dir: Path, output: Path, title: str = "Frozen H₂ held-out study"):
    if output.exists():
        raise ValueError(f"Refusing to overwrite study figure: {output}")
    receipt = read_json(export_dir / "export_receipt.json")
    for name in ("suite_summary.json", "suite_status.json"):
        if file_digest(export_dir / name) != receipt["files_sha256"][name]:
            raise ValueError(f"Compact report checksum mismatch: {name}")
    summary = read_json(export_dir / "suite_summary.json")
    if (
        summary["split"] != "held_out"
        or read_json(export_dir / "suite_status.json")["status"] != "completed"
        or summary["protocol_digest"] != receipt["suite_protocol_digest"]
    ):
        raise ValueError("Plot only a matching, completed held-out export")
    rows = {
        row["comparator"]: row
        for row in summary["paired_comparisons"]
        if row["scope"] == "all_cases" and row["metric"] == "mean_selection_regret"
    }
    if set(rows) != set(LABELS) or any(row["ci95_low"] is None for row in rows.values()):
        raise ValueError("The figure needs every declared control and finite intervals")
    if sum(bool(row["primary"]) for row in rows.values()) != 1:
        raise ValueError("The figure needs exactly one predeclared primary contrast")
    order = sorted(LABELS, key=lambda policy: not rows[policy]["primary"])
    labels = [LABELS[p] + (" (primary)" if rows[p]["primary"] else "") for p in order]
    plt.rcParams.update({"svg.hashsalt": "driftqas-v04", "font.size": 10})
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for index, policy in enumerate(order):
        row = rows[policy]
        color = "#087f8c" if row["primary"] else "#5a6472"
        ax.hlines(index, row["ci95_low"], row["ci95_high"], color=color, linewidth=2)
        ax.plot(row["mean_difference"], index, "o", color=color, markersize=7)
    ax.set_yticks(range(len(order)), labels)
    ax.invert_yaxis()
    ax.axvline(0, color="#19212d", linewidth=1, linestyle="--")
    ax.set_xlabel("Mean regret difference: component-matched racing minus comparator")
    ax.set_title(
        f"{title} · {summary['n_seed_clusters']} seed clusters\n"
        "All declared cases and epochs included; negative favors component matching",
        loc="left",
        pad=18,
        fontsize=12,
    )
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(
        0.02,
        0.02,
        "Whiskers: 95% paired seed-cluster percentile bootstrap intervals. "
        "Secondary contrasts are unadjusted.",
        fontsize=9,
        color="#5a6472",
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"Date": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="Frozen H₂ held-out study")
    args = parser.parse_args()
    plot(args.export_dir, args.output, args.title)


if __name__ == "__main__":
    main()
