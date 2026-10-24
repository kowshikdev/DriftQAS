import runpy
from pathlib import Path

import pytest

from driftqas.benchmark import run_suite
from driftqas.provenance import read_json, write_json
from driftqas.suite_config import load_suite


def test_locality_diagnostics_retain_full_suite_and_export(tmp_path):
    suite = load_suite(Path("configs/locality_ci.yaml"))
    root = tmp_path / "suite"
    run_suite(suite, root)
    analyze = runpy.run_path("scripts/analyze_locality.py")["analyze"]
    result = analyze(root)
    assert result["split"] == "development"
    assert len(result["case_summaries"]) == 2
    assert all(r["n_seed_clusters"] == 1 for r in result["case_summaries"])
    assert all(r["zero_exposure_violations"] == 0 for r in result["case_summaries"])
    export = runpy.run_path("scripts/export_study.py")["export"]
    output = tmp_path / "export"
    export(root, output)
    assert read_json(output / "locality_summary.json") == result
    assert (output / "locality_transitions.csv").exists()
    broken = {**result, "protocol_digest": "wrong"}
    write_json(root / "locality_summary.json", broken)
    with pytest.raises(ValueError, match="do not match"):
        export(root, tmp_path / "wrong-export")
