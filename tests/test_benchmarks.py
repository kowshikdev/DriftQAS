import copy
import sqlite3
from dataclasses import asdict, replace

import numpy as np
import pytest

from driftqas import benchmark
from driftqas.calibration import Calibration
from driftqas.circuits import build_bank
from driftqas.cli import main
from driftqas.config import Config, config_from_mapping
from driftqas.policies import Observation, Policy
from driftqas.provenance import read_json, write_json
from driftqas.reporting import analyze_suite
from driftqas.runner import preflight, run
from driftqas.statistics import episode_metrics, paired_interval
from driftqas.storage import Store
from driftqas.suite_config import suite_from_mapping
from driftqas.tasks import make_task


def declaration(seeds=(1, 2, 3)):
    return {
        "name": "test-suite",
        "split": "development",
        "seed_sets": {"development": list(seeds), "held_out": [1001]},
        "bootstrap_samples": 500,
        "base": {
            "candidates": 2,
            "training_evaluations": 10,
            "epochs": 3,
            "budget_per_epoch": 1024,
            "low_shots": 16,
            "high_shots": 32,
            "initial_seeds": 1,
            "policies": ["reuse", "driftqas"],
        },
        "cases": [
            {"id": "stable", "overrides": {"scenario": "stable"}},
            {"id": "abrupt", "overrides": {"scenario": "abrupt"}},
        ],
    }


def fake_summary(config):
    outcomes = []
    for policy in config.policies:
        for epoch in range(config.epochs):
            # Large shared seed offsets cancel in paired differences. Correlated
            # epochs/cases must not multiply the reported independent sample size.
            regret = 10 + config.seed + epoch
            if policy == "driftqas":
                regret -= config.seed / 10 * (1 if config.scenario == "stable" else 3)
            outcomes.append(
                {
                    "policy": policy,
                    "epoch": epoch,
                    "candidate_id": "test",
                    "selection_regret": regret,
                    "confirmation_energy": -1.0,
                    "confirmation_standard_error": 0.1,
                    "audit_energy": -1.0,
                    "predicted_energy": -1.1,
                    "model_standard_deviation": 0.1,
                    "shots": 512,
                    "budget_limit": config.budget_per_epoch,
                    "by_phase": {"seed": 312, "confirmation": 200},
                }
            )
    return {"outcomes": outcomes}


@pytest.fixture
def fake_backend(monkeypatch):
    calls = []
    identity = {"test_identity": "fixed"}
    monkeypatch.setattr(benchmark, "runtime_identity", lambda: identity)

    def execute(config, output):
        calls.append((config.scenario, config.seed, output.name))
        output.mkdir(parents=True)
        write_json(
            output / "manifest.json",
            {
                "configuration": asdict(config),
                "status": "completed",
                **identity,
            },
        )
        summary = fake_summary(config)
        write_json(output / "summary.json", summary)
        (output / "candidates.json").write_text("[]\n")
        events = Store(output)
        events.append("test", {"seed": config.seed})
        events.export()
        events.close()
        return summary

    monkeypatch.setattr(benchmark, "run", execute)
    return calls, execute


@pytest.mark.parametrize(
    "change",
    [
        {"seed_sets": {"development": [1, 1], "held_out": [1001]}},
        {"seed_sets": {"development": [1], "held_out": [1]}},
        {"seed_sets": {"development": [True], "held_out": [1001]}},
        {"split": "test"},
        {"budget_typo": 1024},
        {"cases": [{"id": "../escape"}]},
        {"cases": [{"id": "stable", "overrides": {"policies": ["random"]}}]},
        {"cases": [{"id": "stable", "overrides": {"changed_edge": "4-5"}}]},
        {"cases": [{"id": "stable"}, {"id": "same"}]},
        {"primary_comparator": "driftqas"},
        {"bootstrap_samples": 0},
    ],
)
def test_invalid_suite_rejected_before_execution(change):
    with pytest.raises(ValueError):
        suite_from_mapping({**declaration(), **change})


def test_fixed_shot_seeds_checked_in_preflight():
    config = Config(
        candidates=3,
        initial_seeds=3,
        budget_per_epoch=1024,
        low_shots=16,
        high_shots=256,
        policies=("driftqas_fixed_shots",),
    )
    with pytest.raises(ValueError, match="Budget"):
        preflight(config)


def test_plan_is_read_only(tmp_path, capsys):
    output = tmp_path / "never-created"
    assert (
        main(["suite", "--config", "configs/suite_smoke.yaml", "--plan", "--output", str(output)])
        == 0
    )
    assert not output.exists()
    assert '"paired_episodes": 6' in capsys.readouterr().out


def test_ablation_relevance_and_refresh_are_separate_controls():
    bank = build_bank(make_task("ising", 4), 2, 7, 10)
    bank[0] = replace(bank[0], footprint={"0-1": 1})
    old = Calibration(0, {"0-1": 0.005, "1-2": 0.005, "2-3": 0.005}, "abrupt")
    unused = Calibration(1, {"0-1": 0.005, "1-2": 0.005, "2-3": 0.04}, "abrupt")
    affected = Calibration(1, {"0-1": 0.04, "1-2": 0.005, "2-3": 0.005}, "abrupt")
    observation = Observation(bank[0].candidate_id, old, -4, 0.01, 16)
    full = Policy("driftqas", bank, 7)
    global_relevance = Policy("driftqas_global_relevance", bank, 7)
    no_refresh = Policy("driftqas_no_refresh", bank, 7)
    assert full.relevance(observation, unused) == 1
    assert global_relevance.relevance(observation, unused) < 1
    assert no_refresh.relevance(observation, affected) == full.relevance(observation, affected)
    for policy in (full, global_relevance, no_refresh):
        policy.add(observation)
        policy.begin_epoch(affected)
    assert full.refresh_queue == global_relevance.refresh_queue == [bank[0].candidate_id]
    assert no_refresh.refresh_queue == []


def test_fixed_shot_run_and_predictions_locked_before_confirmation(tmp_path):
    config = Config(
        candidates=2,
        training_evaluations=10,
        epochs=2,
        budget_per_epoch=256,
        low_shots=8,
        high_shots=32,
        initial_seeds=1,
        policies=("driftqas_fixed_shots",),
    )
    summary = run(config, tmp_path / "run")
    import json

    records = [
        json.loads(line)
        for line in (tmp_path / "run" / "experiments.jsonl").read_text().splitlines()
    ]
    requests = [record["payload"] for record in records if record["kind"] == "request"]
    assert all(
        r["requested_shots_per_group"] == 32 for r in requests if r["phase"] != "confirmation"
    )
    locks = [record["payload"] for record in records if record["kind"] == "locked_recommendation"]
    for lock, outcome in zip(locks, summary["outcomes"], strict=True):
        assert lock["predicted_energy"] == outcome["predicted_energy"]
        assert lock["model_standard_deviation"] == outcome["model_standard_deviation"]
        assert outcome["shots"] <= config.budget_per_epoch
    assert len(episode_metrics(summary, asdict(config))) == 1


def test_paired_bootstrap_and_small_sample_guard():
    assert paired_interval([0.1] * 4, 500, 7)["ci95_low"] is None
    constant = paired_interval([-0.25] * 5, 500, 7)
    assert constant["ci95_low"] == constant["ci95_high"] == -0.25
    values = np.array([-0.1, 0, 0.2, 0.4, 0.9])
    result = paired_interval(values, 1000, 7)
    assert result == paired_interval(values, 1000, 7)
    shifted = paired_interval(values + 3, 1000, 7)
    assert shifted["mean_difference"] == pytest.approx(result["mean_difference"] + 3)
    assert shifted["ci95_low"] == pytest.approx(result["ci95_low"] + 3)
    assert shifted["ci95_high"] == pytest.approx(result["ci95_high"] + 3)
    with pytest.raises(ValueError):
        paired_interval([float("nan")], 500, 7)


def test_reports_use_paired_seed_clusters_across_epochs_and_cases(tmp_path, fake_backend):
    suite = suite_from_mapping(declaration(seeds=(1, 2, 3, 4, 5)))
    result = benchmark.run_suite(suite, tmp_path / "suite")
    primary = result["primary_analysis"]
    assert result["complete_pairs"] == 10
    assert primary["n_seed_clusters"] == 5  # not 10 cases or 30 epochs
    assert primary["mean_difference"] == pytest.approx(-0.6)
    assert primary["target_better_seeds"] == 5
    assert primary["ci95_high"] < 0
    summary = read_json(tmp_path / "suite" / "suite_summary.json")
    assert sum(row["primary"] for row in summary["paired_comparisons"]) == 1
    before = (tmp_path / "suite" / "paired_comparisons.csv").read_bytes()
    analyze_suite(tmp_path / "suite")
    assert (tmp_path / "suite" / "paired_comparisons.csv").read_bytes() == before


def test_complete_resume_skips_execution_and_recovers_missing_receipt(tmp_path, fake_backend):
    calls, _ = fake_backend
    suite = suite_from_mapping(declaration())
    output = tmp_path / "suite"
    benchmark.run_suite(suite, output)
    count = len(calls)
    (output / "episodes" / "stable" / "seed_1" / "completed.json").unlink()
    benchmark.run_suite(suite, output, resume=True)
    assert len(calls) == count
    assert read_json(output / "suite_status.json")["completed_episodes"] == 6
    with pytest.raises(ValueError, match="not empty"):
        benchmark.run_suite(suite, output)


def test_failed_episode_retried_in_new_attempt_without_overwrite(
    tmp_path, fake_backend, monkeypatch
):
    calls, execute = fake_backend
    failed = False

    def interrupt(config, output):
        nonlocal failed
        if config.seed == 2 and not failed:
            failed = True
            output.mkdir(parents=True)
            write_json(output / "manifest.json", {"status": "failed"})
            (output / "partial-event.txt").write_text("preserve me")
            raise RuntimeError("injected evaluator failure")
        return execute(config, output)

    monkeypatch.setattr(benchmark, "run", interrupt)
    suite = suite_from_mapping(declaration())
    output = tmp_path / "suite"
    with pytest.raises(RuntimeError, match="injected"):
        benchmark.run_suite(suite, output)
    assert not (output / "report.md").exists()
    with pytest.raises(ValueError, match="Incomplete"):
        analyze_suite(output)
    benchmark.run_suite(suite, output, resume=True)
    assert calls.count(("stable", 1, "attempt_0001")) == 1
    assert ("stable", 2, "attempt_0002") in calls
    assert (
        output / "episodes/stable/seed_2/attempt_0001/partial-event.txt"
    ).read_text() == "preserve me"


def test_resume_refuses_changed_protocol_environment_and_artifacts(
    tmp_path, fake_backend, monkeypatch
):
    calls, _ = fake_backend
    suite = suite_from_mapping(declaration())
    output = tmp_path / "suite"
    benchmark.run_suite(suite, output)
    count = len(calls)
    changed = copy.deepcopy(declaration())
    changed["base"]["training_evaluations"] += 1
    with pytest.raises(ValueError, match="Cannot resume"):
        benchmark.run_suite(suite_from_mapping(changed), output, resume=True)
    monkeypatch.setattr(benchmark, "runtime_identity", lambda: {"test_identity": "changed"})
    with pytest.raises(ValueError, match="Cannot resume"):
        benchmark.run_suite(suite, output, resume=True)
    monkeypatch.setattr(benchmark, "runtime_identity", lambda: {"test_identity": "fixed"})
    summary_path = output / "episodes/stable/seed_1/attempt_0001/summary.json"
    summary_path.write_text(summary_path.read_text() + " ")
    with pytest.raises(ValueError, match="checksum"):
        benchmark.run_suite(suite, output, resume=True)
    with pytest.raises(ValueError, match="checksum"):
        analyze_suite(output)
    assert len(calls) == count


def test_unsealed_event_export_must_match_database(tmp_path, fake_backend):
    _, execute = fake_backend
    suite = suite_from_mapping(declaration())
    episode = suite.episodes()[0]
    attempt = tmp_path / "attempt_0001"
    execute(config_from_mapping(episode["configuration"]), attempt)
    (attempt / "experiments.jsonl").write_text("")
    with pytest.raises(ValueError, match="event count mismatch"):
        benchmark._seal(tmp_path, attempt, episode, {"test_identity": "fixed"})
    assert not (tmp_path / "completed.json").exists()


def test_finalized_database_contains_all_exported_events(tmp_path):
    events = Store(tmp_path)
    assert (tmp_path / "experiments.live.sqlite").exists()
    assert not (tmp_path / "experiments.sqlite").exists()
    for index in range(100):
        events.append("sample", {"index": index, "counts": {"00": index + 2}})
    events.export()
    events.close()
    benchmark._verify_event_export(tmp_path)
    with sqlite3.connect(tmp_path / "experiments.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 100
    assert not (tmp_path / "experiments.snapshot.sqlite").exists()
    assert not (tmp_path / "experiments.live.sqlite").exists()
    with pytest.raises(sqlite3.ProgrammingError):
        events.append("late", {})


@pytest.mark.parametrize("corrupt", ["duplicate", "missing", "budget", "nonfinite"])
def test_invalid_outcomes_cannot_enter_analysis(corrupt):
    config = Config(candidates=2, initial_seeds=1)
    summary = fake_summary(config)
    if corrupt == "duplicate":
        summary["outcomes"][-1] = summary["outcomes"][0]
    elif corrupt == "missing":
        summary["outcomes"].pop()
    elif corrupt == "budget":
        summary["outcomes"][0]["shots"] = config.budget_per_epoch + 1
    else:
        summary["outcomes"][0]["predicted_energy"] = float("nan")
    with pytest.raises(ValueError):
        episode_metrics(summary, asdict(config))
