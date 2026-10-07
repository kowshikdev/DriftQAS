import copy
import json
import runpy
import shutil
from dataclasses import replace
from zipfile import ZipFile

import numpy as np
import pytest

from driftqas import benchmark, diagnostics, protocol, uncertainty
from driftqas.calibration import Calibration
from driftqas.circuits import build_bank
from driftqas.config import Config
from driftqas.diagnostics import analyze_diagnostics, diagnostic_rows
from driftqas.evaluation import audit_energy
from driftqas.policies import POLICY_COMPONENTS, Observation, Policy
from driftqas.provenance import digest, read_json, write_json
from driftqas.runner import preflight
from driftqas.suite_config import suite_from_mapping
from driftqas.tasks import make_task


@pytest.fixture(scope="module")
def bank():
    return build_bank(make_task(), 3, 7, 30, "stratified")


def test_stratified_anchors_replay_and_have_bounded_training():
    task = make_task("ising", 4)
    bank = build_bank(task, 5, 7, 25, "stratified")
    replay = build_bank(task, 5, 7, 25, "stratified")
    assert bank[1].footprint == {}
    assert all(edge not in bank[i + 2].footprint for i, edge in enumerate(("0-1", "1-2", "2-3")))
    for first, second in zip(bank, replay, strict=True):
        assert first.training_evaluations <= 25
        assert first.candidate_id == second.candidate_id
        assert first.parameters == second.parameters
        assert first.footprint == second.footprint


def test_zero_exposure_invariance_on_exact_physical_audit():
    task = make_task("ising", 4)
    bank = build_bank(task, 5, 7, 25, "stratified")
    old = Calibration(0, {"0-1": 0.005, "1-2": 0.005, "2-3": 0.005}, "abrupt")
    changed = Calibration(1, {**old.errors, "1-2": 0.25}, "abrupt")
    shifts = []
    for candidate in bank:
        shift = abs(audit_energy(task, candidate, changed) - audit_energy(task, candidate, old))
        shifts.append(shift)
        if changed.exposure(candidate.footprint, old, 0.02) == 0:
            assert shift < 1e-10
    assert max(shifts) > 1e-3


def test_component_compatibility_restore_and_same_family_controls(bank):
    old = Calibration(0, {"0-1": 0.005}, "recurring")
    changed = Calibration(1, {"0-1": 0.12}, "recurring")
    restored = Calibration(2, old.errors, "recurring")
    observations = [Observation(c.candidate_id, old, -1.7, 0.001, 32) for c in bank]
    local = Policy("driftqas_racing", bank, 7)
    global_policy = Policy("global_racing", bank, 7)
    blind = Policy("reuse_racing", bank, 7)
    fresh = Policy("fresh_racing", bank, 7)
    for policy in (local, global_policy, blind, fresh):
        for observation in observations:
            policy.add(observation)
        policy.begin_epoch(changed)
    assert local.relevance(observations[0], changed) == 0
    assert local.relevance(observations[1], changed) == 1
    assert local.relevance(observations[0], restored) == 1
    assert global_policy.relevance(observations[1], changed) == 0
    assert blind.relevance(observations[0], changed) == 1
    assert not fresh.observations
    candidate, shots, phase = local.choose(changed, 16, 64)
    assert candidate.footprint  # Invalidated evidence is remeasured before racing.
    assert shots == 16 and phase == "revalidation"
    assert (
        replace(POLICY_COMPONENTS["reuse_racing"], relevance="matching_circuit")
        == POLICY_COMPONENTS["driftqas_racing"]
    )
    assert (
        replace(POLICY_COMPONENTS["driftqas_racing"], allocation="uniform")
        == POLICY_COMPONENTS["driftqas_racing_uniform"]
    )


def test_racing_shot_weighted_variance_and_floor(bank):
    current = Calibration(0, {"0-1": 0.005}, "stable")
    policy = Policy("driftqas_racing", bank, 7)
    policy.add(Observation(bank[0].candidate_id, current, -1, 0.04, 10))
    policy.add(Observation(bank[0].candidate_id, current, -2, 0.01, 30))
    policy.add(Observation(bank[1].candidate_id, current, -1.8, 0, 16))
    means, errors, totals = policy._racing_statistics(current)
    assert means[0] == -1.75
    assert errors[0] == pytest.approx(np.sqrt(0.25**2 * 0.04 + 0.75**2 * 0.01))
    assert errors[1] == 0.002
    assert list(totals) == [40, 16, 0]


def test_racing_stopping_and_uniform_ablation(bank):
    current = Calibration(0, {"0-1": 0.005}, "stable")
    for name in ("driftqas_racing", "driftqas_racing_uniform"):
        policy = Policy(name, bank, 7)
        for i, candidate in enumerate(bank):
            policy.add(Observation(candidate.candidate_id, current, -2 if i == 0 else -1, 1e-6, 32))
        action = policy.choose(current, 16, 64)
        assert (action is None) == (name == "driftqas_racing")
        assert policy.recommend(current) == bank[0]


@pytest.mark.parametrize(
    "changes",
    [
        {"bank_design": "cherry-picked"},
        {"racing_beta": 0},
        {"racing_floor": float("nan")},
    ],
)
def test_new_config_validation(changes):
    with pytest.raises(ValueError):
        replace(Config(), **changes).validate()


def test_bank_coverage_preflight_and_ideal_no_search(bank):
    with pytest.raises(ValueError, match="Budget"):
        preflight(
            Config(
                candidates=8,
                initial_seeds=1,
                budget_per_epoch=256,
                low_shots=32,
                high_shots=64,
                policies=("driftqas_racing",),
            )
        )
    ideal = Policy("ideal_only", bank, 7)
    assert ideal.choose(Calibration(0, {"0-1": 0.005}, "stable"), 16, 64) is None
    assert ideal.recommend(Calibration(0, {"0-1": 0.12}, "abrupt")).ideal_energy == min(
        c.ideal_energy for c in bank
    )


def declaration():
    return {
        "name": "exposure-test",
        "split": "development",
        "seed_sets": {
            "development": [7],
            "calibration": list(range(101, 121)),
            "held_out": [2001, 2002],
        },
        "base": {
            "candidates": 3,
            "training_evaluations": 25,
            "epochs": 3,
            "bank_design": "stratified",
            "budget_per_epoch": 256,
            "low_shots": 8,
            "high_shots": 16,
            "initial_seeds": 1,
            "policies": ["ideal_only", "reuse_racing", "global_racing", "driftqas_racing"],
        },
        "cases": [{"id": "abrupt", "overrides": {"scenario": "abrupt", "drift_error": 0.2}}],
        "primary_target": "driftqas_racing",
        "primary_comparator": "reuse_racing",
        "bootstrap_samples": 100,
    }


def test_calibration_partition_and_pairwise_overlap():
    suite = suite_from_mapping({**declaration(), "split": "calibration"})
    assert len(suite.seeds) == 20
    for pair in (
        ("development", "calibration"),
        ("development", "held_out"),
        ("calibration", "held_out"),
    ):
        bad = copy.deepcopy(declaration())
        bad["seed_sets"][pair[1]][0] = bad["seed_sets"][pair[0]][0]
        with pytest.raises(ValueError, match="disjoint"):
            suite_from_mapping(bad)


def test_freeze_validation_before_writes(tmp_path, monkeypatch):
    suite = suite_from_mapping(declaration())
    identity = {"test_identity": "fixed"}
    monkeypatch.setattr(protocol, "runtime_identity", lambda: identity)
    monkeypatch.setattr(benchmark, "runtime_identity", lambda: identity)
    path = tmp_path / "frozen.json"
    frozen = protocol.freeze_protocol(suite, path)
    assert protocol.validate_frozen(replace(suite, split="calibration"), path, identity) == frozen
    with pytest.raises(ValueError, match="overwrite"):
        protocol.freeze_protocol(suite, path)
    output = tmp_path / "never-written"
    with pytest.raises(ValueError, match="requires --frozen"):
        benchmark.run_suite(replace(suite, split="calibration"), output)
    changed = copy.deepcopy(declaration())
    changed["base"]["racing_beta"] = 3
    with pytest.raises(ValueError, match="declaration mismatch"):
        benchmark.run_suite(suite_from_mapping(changed), output, frozen=path)
    monkeypatch.setattr(benchmark, "runtime_identity", lambda: {"test_identity": "changed"})
    with pytest.raises(ValueError, match="source/environment"):
        benchmark.run_suite(suite, output, frozen=path)
    assert not output.exists()
    path.write_text(path.read_text().replace('"alpha": 0.05', '"alpha": 0.1'))
    with pytest.raises(ValueError, match="digest"):
        protocol.read_frozen(path)


@pytest.fixture(scope="module")
def verified_episode(tmp_path_factory):
    output = tmp_path_factory.mktemp("diagnostics") / "suite"
    benchmark.run_suite(suite_from_mapping(declaration()), output)
    return output


def test_full_bank_diagnostics_real_budgeted_episode(tmp_path, verified_episode):
    output = verified_episode
    manifest, exposures, predictions, episodes = diagnostic_rows(output)
    assert manifest["declaration"]["split"] == "development"
    assert len(predictions) == 4 * 3 * 3
    assert sum(row["selected"] for row in predictions) == 4 * 3
    assert len(exposures) == 2 * 3
    assert episodes[0]["zero_exposure_violations"] == 0
    assert analyze_diagnostics(output)["case_summaries"][0]["n_seed_clusters"] == 1
    receipt = read_json(output / "episodes/abrupt/seed_7/completed.json")
    attempt = output / "episodes/abrupt/seed_7" / receipt["attempt"]
    events = [json.loads(line) for line in (attempt / "experiments.jsonl").read_text().splitlines()]
    assert all(
        event["payload"]["phase"] == "confirmation"
        for event in events
        if event["kind"] == "request" and event["payload"]["policy"] == "ideal_only"
    )
    with pytest.raises(ValueError, match="calibration partition"):
        uncertainty.fit_calibration(output, tmp_path / "invalid-calibration.json")


@pytest.mark.parametrize(
    "corruption",
    ["missing", "duplicate", "negative-sd", "late-lock", "visible-audit", "audit-mismatch"],
)
def test_diagnostic_grid_and_chronology_guards(tmp_path, monkeypatch, verified_episode, corruption):
    output = tmp_path / "suite"
    shutil.copytree(verified_episode, output)
    manifest, completed = benchmark.completed_episodes(output)
    # Bypass only checksums to exercise semantic guards on intentionally corrupt input.
    monkeypatch.setattr(diagnostics, "completed_episodes", lambda _: (manifest, completed))
    path = output / "episodes/abrupt/seed_7/attempt_0001/experiments.jsonl"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    prediction = next(event for event in events if event["kind"] == "locked_predictions")
    if corruption == "missing":
        prediction["payload"]["predictions"].pop()
    elif corruption == "duplicate":
        prediction["payload"]["predictions"].append(prediction["payload"]["predictions"][0])
    elif corruption == "negative-sd":
        prediction["payload"]["predictions"][0]["model_standard_deviation"] = -1
    elif corruption == "late-lock":
        lock = next(event for event in events if event["kind"] == "locked_recommendation")
        prediction["id"] = lock["id"] + 1
    elif corruption == "visible-audit":
        next(event for event in events if event["kind"] == "offline_audit")["payload"][
            "policy_visible"
        ] = True
    else:
        lock = next(event for event in events if event["kind"] == "locked_recommendation")
        next(
            event
            for event in events
            if event["kind"] == "offline_audit"
            and event["payload"]["candidate_id"] == lock["payload"]["candidate_id"]
        )["payload"]["energy"] += 0.1
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    with pytest.raises(ValueError):
        diagnostic_rows(output)


def test_cluster_quantile_finite_sample_rank_and_no_shrink():
    scores = list(range(1, 21))
    temperature, rank = uncertainty.cluster_quantile(scores, 0.05)
    assert temperature == 20 and rank == 20
    assert uncertainty.cluster_quantile([0.1] * 20, 0.05)[0] == 1
    with pytest.raises(ValueError, match="Too few"):
        uncertainty.cluster_quantile(scores[:18], 0.05)
    with pytest.raises(ValueError, match="finite"):
        uncertainty.cluster_quantile([float("nan")], 0.05)


def synthetic_diagnostics(split, frozen):
    declaration = {**frozen["declaration"], "split": split}
    manifest = {
        "declaration": declaration,
        "runtime": frozen["runtime"],
        "frozen_protocol": frozen,
        "protocol_digest": "test-digest",
    }
    predictions = []
    policies = declaration["cases"][0]["configuration"]["policies"]
    for policy in policies:
        for seed in declaration["seed_sets"][split]:
            for candidate, residual in (("a", 0.03), ("b", 0.005)):
                predictions.append(
                    {
                        "policy": policy,
                        "seed": seed,
                        "selected": candidate == "b",
                        "predicted_energy": -1 + residual,
                        "audit_energy": -1,
                        "model_standard_deviation": 0.01,
                    }
                )
    return manifest, [], predictions, []


def test_calibration_uses_full_bank_max_and_fresh_seed_evaluation(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "runtime_identity", lambda: {"test": "fixed"})
    frozen = protocol.freeze_protocol(suite_from_mapping(declaration()), tmp_path / "frozen.json")
    monkeypatch.setattr(
        uncertainty, "diagnostic_rows", lambda _: synthetic_diagnostics("calibration", frozen)
    )
    path = tmp_path / "calibration.json"
    artifact = uncertainty.fit_calibration(tmp_path, path)
    assert (
        artifact["temperatures"]["driftqas_racing"] > 1.5
    )  # selected residual alone would not inflate.
    assert all(
        r["seed"] not in frozen["declaration"]["seed_sets"]["held_out"]
        for r in artifact["seed_cluster_scores"]["driftqas_racing"]
    )
    monkeypatch.setattr(
        uncertainty, "diagnostic_rows", lambda _: synthetic_diagnostics("held_out", frozen)
    )
    result = uncertainty.evaluate_calibration(tmp_path, path)
    row = result["policy_summaries"][0]
    assert row["raw_full_bank_coverage"] == 0.5
    assert row["calibrated_joint_seed_coverage"] == 1
    assert row["mean_calibrated_width"] > row["mean_raw_width"]
    assert result["held_out_seed_clusters"] == 2
    before = artifact["calibration_id"]
    assert read_json(path)["calibration_id"] == before  # Evaluation never refits.
    corrupt = read_json(path)
    corrupt["temperatures"]["driftqas_racing"] += 1
    write_json(path, corrupt)
    with pytest.raises(ValueError, match="digest"):
        uncertainty.evaluate_calibration(tmp_path, path)


def test_calibration_rejects_protocol_or_seed_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(protocol, "runtime_identity", lambda: {"test": "fixed"})
    frozen = protocol.freeze_protocol(suite_from_mapping(declaration()), tmp_path / "frozen.json")
    monkeypatch.setattr(
        uncertainty, "diagnostic_rows", lambda _: synthetic_diagnostics("calibration", frozen)
    )
    path = tmp_path / "calibration.json"
    artifact = uncertainty.fit_calibration(tmp_path, path)
    monkeypatch.setattr(
        uncertainty, "diagnostic_rows", lambda _: synthetic_diagnostics("held_out", frozen)
    )
    for name, value, message in (
        ("frozen_id", "different", "protocol mismatch"),
        ("calibration_seeds", [2001], "seed mismatch"),
    ):
        changed = {**artifact, name: value}
        changed["calibration_id"] = digest(
            {k: v for k, v in changed.items() if k != "calibration_id"}
        )
        write_json(path, changed)
        with pytest.raises(ValueError, match=message):
            uncertainty.evaluate_calibration(tmp_path, path)


def test_compact_export_is_verified_non_overwriting_and_not_a_raw_suite(tmp_path, verified_episode):
    export = runpy.run_path("scripts/export_study.py")["export"]
    output = tmp_path / "export"
    result = export(verified_episode, output)
    assert result["complete_paired_episodes"] == 1
    assert "experiments.sqlite" not in result["files_sha256"]
    assert not (output / "episodes").exists()
    assert read_json(output / "audit_receipts.json")["episodes"][0]["core_artifact_sha256"][
        "experiments.jsonl"
    ]
    with pytest.raises(ValueError, match="new compact-export"):
        export(verified_episode, output)
    corrupt = tmp_path / "corrupt"
    shutil.copytree(verified_episode, corrupt)
    path = corrupt / "episodes/abrupt/seed_7/attempt_0001/experiments.jsonl"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        export(corrupt, tmp_path / "never-written")
    assert not (tmp_path / "never-written").exists()


def test_raw_evidence_bundle_verifies_and_excludes_incidental_files(tmp_path, verified_episode):
    bundle = runpy.run_path("scripts/bundle_evidence.py")["bundle"]
    output = tmp_path / "evidence.zip"
    incidental = verified_episode / "unrelated-runtime-file"
    incidental.write_text("not experiment evidence")
    result = bundle([verified_episode], output)
    assert result["suites"][0]["paired_episodes"] == 1
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert "EVIDENCE.json" in archive.namelist()
        assert any(name.endswith("experiments.sqlite") for name in archive.namelist())
        assert not any(name.endswith(incidental.name) for name in archive.namelist())
        assert not any(name.endswith(".py") for name in archive.namelist())
    with pytest.raises(ValueError, match="overwrite"):
        bundle([verified_episode], output)
