import json
from dataclasses import replace

import pytest

from driftqas.budget import Budget
from driftqas.calibration import Calibration, snapshot
from driftqas.circuits import build_bank
from driftqas.config import Config, load_config
from driftqas.policies import Observation, Policy
from driftqas.runner import run
from driftqas.tasks import make_task


def test_confirmation_reserve_is_protected():
    budget = Budget(1000, 200)
    budget.charge(800, "search")
    with pytest.raises(ValueError):
        budget.charge(1, "precision")
    assert budget.spent == 800
    budget.charge(200, "confirmation")
    assert budget.spent == 1000
    with pytest.raises(ValueError):
        budget.charge(1, "confirmation")


def test_unused_component_change_does_not_discount_evidence():
    old = Calibration(0, {"0-1": 0.005, "1-2": 0.005}, "abrupt")
    new = Calibration(1, {"0-1": 0.005, "1-2": 0.04}, "abrupt")
    assert new.exposure({"0-1": 3}, old, 0.02) == 0
    assert new.exposure({"1-2": 3}, old, 0.02) > 0


def test_policy_relevance_and_recurrence():
    bank = build_bank(make_task(), 2, 7, 30)
    candidate = bank[0]
    old = Calibration(0, {"0-1": 0.005}, "recurring")
    changed = Calibration(1, {"0-1": 0.04}, "recurring")
    restored = Calibration(2, {"0-1": 0.005}, "recurring")
    observation = Observation(candidate.candidate_id, old, -1.8, 0.001, 128)
    policy = Policy("driftqas", bank, 7)
    assert policy.relevance(observation, changed) < 1
    assert policy.relevance(observation, restored) == 1
    assert Policy("reuse", bank, 7).relevance(observation, changed) == 1


def test_stable_profile_and_future_epoch_are_not_mutated():
    first = snapshot(4, 0, 4, "abrupt", 0.005, 0.04, "1-2")
    future = snapshot(4, 3, 4, "abrupt", 0.005, 0.04, "1-2")
    assert first.errors["1-2"] == 0.005
    assert future.errors["1-2"] == 0.04


@pytest.mark.parametrize(
    "changes",
    [
        {"low_shots": 1},
        {"high_shots": 1},
        {"drift_error": -0.01},
        {"seed": -1},
        {"initial_seeds": 100},
        {"policies": ("driftqas", "driftqas")},
        {"forgetting": float("nan")},
        {"confirmation_fraction": 1},
    ],
)
def test_invalid_config_fails_fast(changes):
    with pytest.raises(ValueError):
        replace(Config(), **changes).validate()


def test_unknown_config_field_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("budget_typo: 4000", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown"):
        load_config(path)


def test_reproducible_protocol_keeps_audit_outside_policy_and_locks_before_confirmation(tmp_path):
    config = Config(
        candidates=2,
        training_evaluations=40,
        epochs=2,
        budget_per_epoch=1024,
        low_shots=32,
        high_shots=64,
        initial_seeds=1,
        policies=("restart", "driftqas"),
    )
    first = run(config, tmp_path / "first")
    second = run(config, tmp_path / "second")
    keys = ("candidate_id", "confirmation_energy", "shots", "selection_regret", "audit_energy")
    for a, b in zip(first["outcomes"], second["outcomes"], strict=True):
        assert {k: a[k] for k in keys} == {k: b[k] for k in keys}
        assert a["shots"] <= a["budget_limit"]
        assert sum(a["by_phase"].values()) == a["shots"]
        assert a["by_phase"]["confirmation"] > 0
    records = [
        json.loads(line)
        for line in (tmp_path / "first" / "experiments.jsonl").read_text().splitlines()
    ]
    first_audit = next(r["id"] for r in records if r["kind"] == "offline_audit")
    assert all(r["id"] < first_audit for r in records if r["kind"] == "locked_recommendation")
    for lock in [r for r in records if r["kind"] == "locked_recommendation"]:
        matching = [
            r
            for r in records
            if r["kind"] == "measurement"
            and r["payload"]["phase"] == "confirmation"
            and r["payload"]["policy"] == lock["payload"]["policy"]
            and r["payload"]["epoch"] == lock["payload"]["epoch"]
        ]
        assert len(matching) == 1
        assert matching[0]["id"] > lock["id"]
        assert matching[0]["payload"]["candidate_id"] == lock["payload"]["candidate_id"]
    with pytest.raises(ValueError, match="not empty"):
        run(config, tmp_path / "first")
