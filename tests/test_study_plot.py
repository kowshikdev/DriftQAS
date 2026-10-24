import copy
import runpy
from pathlib import Path

import pytest

from driftqas.provenance import file_digest, read_json, write_json


def plot_fixture(tmp_path, global_primary):
    source = Path("examples/benchmarks/v04/h2-held-out")
    summary = copy.deepcopy(read_json(source / "suite_summary.json"))
    for row in summary["paired_comparisons"]:
        row["primary"] = (
            row["scope"] == "all_cases"
            and row["metric"] == "mean_selection_regret"
            and row["comparator"] == ("global_racing" if global_primary else "reuse_racing")
        )
    write_json(tmp_path / "suite_summary.json", summary)
    write_json(tmp_path / "suite_status.json", {"status": "completed"})
    receipt = {
        "suite_protocol_digest": summary["protocol_digest"],
        "files_sha256": {
            name: file_digest(tmp_path / name)
            for name in ("suite_summary.json", "suite_status.json")
        },
    }
    write_json(tmp_path / "export_receipt.json", receipt)
    return runpy.run_path("scripts/plot_exposure_study.py")["plot"]


@pytest.mark.parametrize("global_primary", [False, True])
def test_figure_labels_actual_primary_and_never_silently_overwrites(tmp_path, global_primary):
    plot = plot_fixture(tmp_path, global_primary)
    output = tmp_path / "figure.svg"
    plot(tmp_path, output, "Test fixture, not research evidence")
    text = output.read_text()
    expected = "Global matching" if global_primary else "Blind racing reuse"
    assert f"{expected} (primary)" in text
    other = "Blind racing reuse" if global_primary else "Global matching"
    assert f"{other} (primary)" not in text
    with pytest.raises(ValueError, match="overwrite"):
        plot(tmp_path, output)


def test_figure_rejects_damaged_export(tmp_path):
    plot = plot_fixture(tmp_path, True)
    (tmp_path / "suite_summary.json").write_text("corrupted")
    with pytest.raises(ValueError, match="checksum"):
        plot(tmp_path, tmp_path / "figure.svg")
