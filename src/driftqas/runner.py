"""Run chronological comparisons, then audit locked recommendations offline."""

import json
import platform
from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from qiskit import qasm3

from driftqas.budget import Budget
from driftqas.calibration import snapshot
from driftqas.circuits import build_bank
from driftqas.config import Config
from driftqas.evaluation import audit_energy, sample
from driftqas.policies import Observation, Policy
from driftqas.storage import Store
from driftqas.tasks import make_task


def measurement_seed(*parts: object) -> int:
    return int.from_bytes(sha256(json.dumps(parts).encode()).digest()[:4], "big")


def run(config: Config, output: Path) -> dict:
    config.validate()
    task = make_task(config.task, config.n_qubits, config.field)
    initial_calibration = snapshot(
        task.n_qubits,
        0,
        config.epochs,
        config.scenario,
        config.base_error,
        config.drift_error,
        config.changed_edge,
    )
    groups = len(task.groups)
    reserve = int(config.budget_per_epoch * config.confirmation_fraction) // groups * groups
    seeds_cost = config.initial_seeds * config.low_shots * groups
    if reserve < 2 * groups or seeds_cost > config.budget_per_epoch - reserve:
        raise ValueError("Budget cannot fund initial seeds and independent confirmation")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(f"Output directory is not empty: {output}. Choose a new run directory.")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "configuration": asdict(config),
        "task": asdict(task),
        "reference_energy": task.reference_energy,
        "python": platform.python_version(),
        "versions": {
            p: version(p)
            for p in (
                "driftqas",
                "qiskit",
                "qiskit-aer",
                "numpy",
                "scipy",
                "scikit-learn",
                "PyYAML",
                "matplotlib",
            )
        },
        "source_digest": sha256(
            b"".join(
                p.name.encode() + b"\0" + p.read_bytes()
                for p in sorted(Path(__file__).parent.glob("*.py"))
            )
        ).hexdigest(),
        "scope": "frozen-parameter finite-library selection under synthetic CX noise",
        "seed_convention": "SHA256(seed, task, candidate, calibration, phase, repetition); "
        "shared streams across matched policy actions; "
        "confirmation uses a distinct phase",
        "status": "preparing",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Preparing {config.candidates} circuits for {task.name}...", flush=True)
    started = perf_counter()
    try:
        bank = build_bank(task, config.candidates, config.seed, config.training_evaluations)
    except Exception as exc:
        manifest.update({"status": "failed", "error": str(exc)})
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        raise
    preparation = {
        "shared_wall_seconds": perf_counter() - started,
        "ideal_objective_calls": sum(c.training_evaluations for c in bank),
        "sampled_shots": 0,
        "accounting": "Shared ideal preparation reported separately, not hidden "
        "inside online-shot savings. No QPU training performed.",
    }
    (output / "candidates.json").write_text(
        json.dumps([c.export() for c in bank], indent=2), encoding="utf-8"
    )
    store = Store(output)
    store.append("preparation", preparation)
    outcomes = []
    try:
        for name in config.policies:
            policy = Policy(name, bank, config.seed, config.drift_scale, config.forgetting)
            repetitions: dict[tuple, int] = defaultdict(int)
            policy_started = perf_counter()
            for epoch in range(config.epochs):
                # No future snapshots are materialized or given to the policy.
                calibration = (
                    initial_calibration
                    if epoch == 0
                    else snapshot(
                        task.n_qubits,
                        epoch,
                        config.epochs,
                        config.scenario,
                        config.base_error,
                        config.drift_error,
                        config.changed_edge,
                    )
                )
                store.append(
                    "calibration",
                    {
                        "policy": name,
                        **asdict(calibration),
                        "calibration_id": calibration.calibration_id,
                    },
                )
                budget = Budget(config.budget_per_epoch, reserve)
                policy.begin_epoch(calibration)

                def evaluate(
                    candidate,
                    shots,
                    phase,
                    *,
                    epoch=epoch,
                    repetitions=repetitions,
                    calibration=calibration,
                    name=name,
                    policy=policy,
                    budget=budget,
                ):
                    key = (epoch, candidate.candidate_id, phase)
                    repetition = repetitions[key]
                    repetitions[key] += 1
                    seed = measurement_seed(
                        config.seed,
                        task.task_id,
                        candidate.candidate_id,
                        calibration.calibration_id,
                        phase,
                        repetition,
                    )
                    request = {
                        "policy": name,
                        "epoch": epoch,
                        "phase": phase,
                        "candidate_id": candidate.candidate_id,
                        "parameter_id": candidate.parameter_id,
                        "calibration_id": calibration.calibration_id,
                        "source": "noisy_finite_shot_aer",
                        "seed": seed,
                        "requested_shots_per_group": shots,
                        "requested_total_shots": shots * groups,
                        "repetition": repetition,
                        "rng_state": policy.rng.bit_generator.state,
                    }
                    store.append("request", request)
                    try:
                        result = sample(task, candidate, calibration, shots, seed, budget, phase)
                    except Exception as exc:
                        store.append(
                            "failure",
                            {
                                **request,
                                "error": str(exc),
                                "conservatively_charged_shots": budget.spent,
                            },
                        )
                        raise
                    store.append(
                        "measurement", {**request, **result.export(), "ledger_spent": budget.spent}
                    )
                    return Observation(
                        candidate.candidate_id, calibration, result.energy, result.variance, shots
                    ), result

                if not policy.observations:
                    for candidate in bank[: config.initial_seeds]:
                        observation, _ = evaluate(candidate, config.low_shots, "seed")
                        policy.add(observation)
                while budget.search_remaining >= config.low_shots * groups:
                    action = policy.choose(calibration, config.low_shots, config.high_shots)
                    if action is None:
                        break
                    candidate, shots, phase = action
                    shots = min(shots, budget.search_remaining // groups)
                    means, uncertainty = policy.predict(calibration)
                    index = next(
                        i for i, c in enumerate(bank) if c.candidate_id == candidate.candidate_id
                    )
                    store.append(
                        "decision",
                        {
                            "policy": name,
                            "epoch": epoch,
                            "phase": phase,
                            "candidate_id": candidate.candidate_id,
                            "predicted_energy": float(means[index]),
                            "model_standard_deviation": float(uncertainty[index]),
                            "requested_total_shots": shots * groups,
                            "rule": "uniform allocation"
                            if name == "random"
                            else "staged refresh/promotion or mean - 0.5 * model SD",
                            "historical_relevance": [
                                policy.relevance(o, calibration)
                                for o in policy.observations
                                if o.candidate_id == candidate.candidate_id
                            ],
                        },
                    )
                    observation, _ = evaluate(candidate, shots, phase)
                    policy.add(observation)
                recommendation = policy.recommend(calibration)
                store.append(
                    "locked_recommendation",
                    {
                        "policy": name,
                        "epoch": epoch,
                        "candidate_id": recommendation.candidate_id,
                        "search_shots": budget.spent,
                        "confirmation_shots_reserved": reserve,
                    },
                )
                observation, confirmed = evaluate(recommendation, reserve // groups, "confirmation")
                # Only subsequent epochs can use the confirmation; choice is already locked.
                policy.add(observation)
                outcome = {
                    "policy": name,
                    "epoch": epoch,
                    "candidate_id": recommendation.candidate_id,
                    "confirmation_energy": confirmed.energy,
                    "confirmation_standard_error": confirmed.standard_error,
                    "shots": budget.spent,
                    "budget_limit": budget.limit,
                    "by_phase": budget.by_phase,
                    "policy_elapsed_seconds": perf_counter() - policy_started,
                }
                outcomes.append(outcome)
                store.append("epoch_outcome", outcome)
                destination = output / "circuits" / name
                destination.mkdir(parents=True, exist_ok=True)
                (destination / f"epoch_{epoch}.qasm").write_text(
                    qasm3.dumps(recommendation.circuit), encoding="utf-8"
                )
                print(
                    f"{name:18} epoch={epoch} shots={budget.spent:6} "
                    f"confirmation={confirmed.energy:.6f} "
                    f"±{confirmed.standard_error:.6f}",
                    flush=True,
                )
        # Audit begins only after every policy has finished. No audit scores enter memory.
        print("Auditing locked recommendations independently...", flush=True)
        audit_started = perf_counter()
        scores: dict[tuple[int, str], float] = {}
        for epoch in range(config.epochs):
            calibration = snapshot(
                task.n_qubits,
                epoch,
                config.epochs,
                config.scenario,
                config.base_error,
                config.drift_error,
                config.changed_edge,
            )
            for candidate in bank:
                energy = audit_energy(task, candidate, calibration)
                scores[(epoch, candidate.candidate_id)] = energy
                store.append(
                    "offline_audit",
                    {
                        "epoch": epoch,
                        "candidate_id": candidate.candidate_id,
                        "energy": energy,
                        "policy_visible": False,
                    },
                )
        for outcome in outcomes:
            energy = scores[(outcome["epoch"], outcome["candidate_id"])]
            best = min(scores[(outcome["epoch"], c.candidate_id)] for c in bank)
            outcome.update(
                {
                    "audit_energy": energy,
                    "best_library_energy": best,
                    "selection_regret": energy - best,
                    "ground_state_excess": energy - task.reference_energy,
                }
            )
        summary = {
            "scope": manifest["scope"],
            "preparation": preparation,
            "audit_wall_seconds": perf_counter() - audit_started,
            "outcomes": outcomes,
            "claims": "Smoke/development result only; no novelty, superiority, "
            "hardware speedup, or quantum-advantage claim.",
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        manifest["status"] = "completed"
        return summary
    except Exception as exc:
        manifest.update({"status": "failed", "error": str(exc)})
        raise
    finally:
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        store.export()
        store.close()
