from dataclasses import replace
from types import SimpleNamespace

import pytest

from driftqas import screening
from driftqas.calibration import Calibration
from driftqas.cli import main
from driftqas.provenance import digest, read_json, write_json
from driftqas.suite_config import load_suite, suite_from_mapping


def declaration():
    return suite_from_mapping(
        {
            "name": "screen-test",
            "split": "development",
            "seed_sets": {"development": [4001], "held_out": [6001]},
            "base": {
                "task": "ising",
                "n_qubits": 3,
                "candidates": 4,
                "bank_design": "stratified",
                "training_evaluations": 4,
                "epochs": 2,
                "budget_per_epoch": 256,
                "low_shots": 8,
                "high_shots": 16,
                "initial_seeds": 1,
                "policies": ["driftqas_racing", "global_racing"],
            },
            "cases": [
                {"id": "abrupt", "overrides": {}},
                {"id": "stable", "overrides": {"scenario": "stable"}},
            ],
            "primary_target": "driftqas_racing",
            "primary_comparator": "global_racing",
        }
    )


def test_screen_rejects_reserved_partitions_before_writes(tmp_path, monkeypatch):
    suite = replace(declaration(), split="held_out")
    monkeypatch.setattr(screening, "build_bank", lambda *args: pytest.fail("Unexpected training"))
    with pytest.raises(ValueError, match="development-only"):
        screening.run_screen(suite, tmp_path / "reserved")
    assert not (tmp_path / "reserved").exists()


def test_plan_shares_banks_and_does_not_execute(monkeypatch):
    monkeypatch.setattr(screening, "build_bank", lambda *args: pytest.fail("Plan executed"))
    plan = screening.screen_plan(declaration())
    assert len(plan["unique_banks"]) == 1
    assert plan["ideal_objective_call_upper_bound"] == 16
    assert plan["audit_rows"] == 16 and plan["online_shots"] == 0
    h2 = replace(
        declaration(),
        cases=(
            replace(
                declaration().cases[0],
                configuration=replace(declaration().cases[0].configuration, task="h2"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="multi-edge"):
        screening.screen_plan(h2)


def example():
    bank = [
        SimpleNamespace(candidate_id="affected", footprint={"0-1": 1}),
        SimpleNamespace(candidate_id="unaffected", footprint={"1-2": 1}),
        SimpleNamespace(candidate_id="product", footprint={}),
    ]
    old = Calibration(0, {"0-1": 0.005, "1-2": 0.005}, "abrupt")
    current = Calibration(1, {"0-1": 0.12, "1-2": 0.005}, "abrupt")
    return bank, old, current


def test_locality_requires_nonempty_unaffected_winner_and_rank_change():
    bank, old, current = example()
    before = {"affected": -3.0, "unaffected": -2.9, "product": -2.8}
    after = {**before, "affected": -2.7}
    row = screening.transition_metrics(bank, old, current, before, after)
    assert row["winner_set_reversal"] and row["locality_opportunity"]
    assert row["unaffected_nonempty_candidates"] == 1
    assert row["previous_optimal_set_regret"] == pytest.approx(0.2)
    assert row["zero_exposure_violations"] == 0
    product_wins = {**after, "product": -3.1}
    assert not screening.transition_metrics(bank, old, current, before, product_wins)[
        "locality_opportunity"
    ]


def test_tied_old_winner_does_not_create_false_reversal():
    bank, old, current = example()
    before = {"affected": -3.0, "unaffected": -3.0, "product": -2.8}
    row = screening.transition_metrics(bank, old, current, before, {**before, "affected": -2.7})
    assert row["previous_optimal_set_regret"] == 0
    assert not row["winner_set_reversal"] and not row["locality_opportunity"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True])
def test_invalid_audits_rejected(bad):
    bank, old, current = example()
    values = {"affected": -3.0, "unaffected": -2.9, "product": -2.8}
    with pytest.raises(ValueError, match="finite"):
        screening.transition_metrics(bank, old, current, values, {**values, "affected": bad})
    with pytest.raises(ValueError, match="complete"):
        screening.transition_metrics(bank, old, current, values, {})


def test_physical_screen_complete_sealed_and_cached(tmp_path, monkeypatch):
    output = tmp_path / "screen"
    real = screening.audit_energy
    calls = []

    def counted(*args):
        calls.append(args)
        return real(*args)

    monkeypatch.setattr(screening, "audit_energy", counted)
    result = screening.run_screen(declaration(), output)
    assert result["unique_banks"] == 1 and result["ideal_objective_calls"] <= 16
    assert result["audit_evaluations_executed"] == len(calls) == 8
    assert result["audit_rows"] == 16
    assert screening.verify_screen(output) == result
    assert main(["verify-screen", "--screen-dir", str(output)]) == 0
    (output / "incidental.tmp").write_text("not an experiment artifact")
    assert screening.verify_screen(output) == result
    with pytest.raises(ValueError, match="overwrite"):
        screening.run_screen(declaration(), output)
    (output / "audit_energies.csv").write_text("corrupt")
    with pytest.raises(ValueError, match="checksum"):
        screening.verify_screen(output)


def test_failed_screen_preserves_failure_and_no_completion(tmp_path, monkeypatch):
    def broken(*args):
        raise RuntimeError("Deliberate audit failure")

    monkeypatch.setattr(screening, "audit_energy", broken)
    output = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="Deliberate"):
        screening.run_screen(declaration(), output)
    assert read_json(output / "screen_status.json")["status"] == "failed"
    assert not (output / "completed.json").exists()


def test_forged_bank_path_rejected_before_artifact_reads(tmp_path):
    output = tmp_path / "screen"
    screening.run_screen(declaration(), output)
    manifest = read_json(output / "screen_manifest.json")
    settings = next(iter(manifest["plan"]["unique_banks"].values()))
    manifest["plan"]["unique_banks"] = {"../../outside": settings}
    manifest.pop("screen_id")
    manifest["screen_id"] = digest(manifest)
    write_json(output / "screen_manifest.json", manifest)
    with pytest.raises(ValueError, match="bank identities"):
        screening.verify_screen(output)


@pytest.mark.parametrize("passes", [False, True])
def test_selection_follows_declared_order_or_stops(tmp_path, monkeypatch, passes):
    from pathlib import Path

    suite = load_suite(Path("configs/locality_screen.yaml"))
    summary = {
        "screen_id": "example",
        "case_summaries": [
            {
                "case_id": c.case_id,
                "n_seed_clusters": 5,
                "zero_exposure_violations": 0,
                "seeds_with_locality_opportunity": 3 if passes else 2,
            }
            for c in suite.cases
        ],
    }
    monkeypatch.setattr(screening, "verify_screen", lambda path: summary)
    monkeypatch.setattr(screening, "read_json", lambda path: {"declaration": suite.declaration()})
    result = screening.select_locality_cell(suite, tmp_path, tmp_path / "selection.json")
    assert result["status"] == ("selected" if passes else "blocked")
    assert len(result["ordered_cells"]) == 4
    if passes:
        assert result["selection"]["field"] == 0.5
        assert result["selection"]["training_evaluations"] == 120
    else:
        assert result["selection"] is None
    with pytest.raises(ValueError, match="overwrite"):
        screening.select_locality_cell(suite, tmp_path, tmp_path / "selection.json")
