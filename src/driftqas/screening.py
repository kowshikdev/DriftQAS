"""Offline, development-only opportunity screening; never controller feedback."""

from pathlib import Path

import numpy as np

from driftqas.calibration import snapshot
from driftqas.circuits import build_bank
from driftqas.diagnostics import TOLERANCE
from driftqas.evaluation import audit_energy
from driftqas.provenance import digest, file_digest, read_json, runtime_identity, write_json
from driftqas.reporting import _csv
from driftqas.suite_config import Suite
from driftqas.tasks import make_task

REPORTS = {
    "screen_manifest.json",
    "screen_status.json",
    "screen_summary.json",
    "audit_energies.csv",
    "screen_transitions.csv",
    "report.md",
}


def bank_settings(config, seed: int) -> dict:
    return {
        "task": config.task,
        "n_qubits": config.n_qubits,
        "field": config.field,
        "size": config.candidates,
        "seed": seed,
        "max_evaluations": config.training_evaluations,
        "design": config.bank_design,
    }


def screen_plan(suite: Suite) -> dict:
    if suite.split != "development":
        raise ValueError("Opportunity screening is development-only; reserved seeds stay unseen")
    if any(
        c.configuration.task != "ising"
        or c.configuration.n_qubits < 3
        or c.configuration.epochs < 2
        for c in suite.cases
    ):
        raise ValueError("Screen multi-edge Ising tasks with at least three qubits/two epochs")
    settings = [bank_settings(c.configuration, seed) for c in suite.cases for seed in suite.seeds]
    banks = {digest(value): value for value in settings}
    return {
        "unique_banks": banks,
        "ideal_objective_call_upper_bound": sum(
            b["size"] * b["max_evaluations"] for b in banks.values()
        ),
        "audit_rows": sum(
            c.configuration.candidates * c.configuration.epochs * len(suite.seeds)
            for c in suite.cases
        ),
        "paired_case_seeds": len(suite.cases) * len(suite.seeds),
        "online_shots": 0,
    }


def transition_metrics(bank, old, current, previous: dict, energies: dict) -> dict:
    ids = [c.candidate_id for c in bank]
    if set(previous) != set(ids) or set(energies) != set(ids):
        raise ValueError("Screen needs complete candidate audit grids")
    if not all(
        not isinstance(v, bool) and isinstance(v, (int, float)) and np.isfinite(v)
        for v in [*previous.values(), *energies.values()]
    ):
        raise ValueError("Screen needs finite audit energies")
    before, after = min(previous.values()), min(energies.values())
    previous_winners = [i for i in ids if previous[i] <= before + TOLERANCE]
    # A tied former optimum that remains optimal prevents a genuine winner-set reversal.
    opportunity = min(energies[i] - after for i in previous_winners)
    changed = old.errors != current.errors
    unaffected, violations = [], 0
    for candidate in bank:
        exposure = current.exposure(candidate.footprint, old, 1.0)
        if exposure == 0:
            violations += abs(
                energies[candidate.candidate_id] - previous[candidate.candidate_id]
            ) > (TOLERANCE)
            if candidate.footprint:
                unaffected.append(candidate.candidate_id)
    unaffected_regret = min((energies[i] - after for i in unaffected), default=None)
    reversal = opportunity > TOLERANCE
    reusable_winner = unaffected_regret is not None and unaffected_regret <= TOLERANCE
    return {
        "calibration_changed": changed,
        "previous_optimal_set_regret": float(opportunity),
        "winner_set_reversal": reversal,
        "unaffected_nonempty_candidates": len(unaffected),
        "best_unaffected_nonempty_regret": unaffected_regret,
        "unaffected_nonempty_winner": reusable_winner,
        "locality_opportunity": changed and reversal and reusable_winner,
        "zero_exposure_violations": int(violations),
    }


def run_screen(suite: Suite, output: Path) -> dict:
    plan = screen_plan(suite)  # Reject reserved partitions before creating any output.
    if output.exists():
        raise ValueError(f"Refusing to overwrite opportunity screen: {output}")
    output.mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "declaration": suite.declaration(),
        "runtime": runtime_identity(),
        "plan": plan,
        "tolerance": TOLERANCE,
        "scope": "Development-only exact audits; no policy performance, online feedback, "
        "test-seed screening, or evidence of controller superiority.",
    }
    manifest["screen_id"] = digest(manifest)
    write_json(output / "screen_manifest.json", manifest)
    write_json(output / "screen_status.json", {"status": "running"})
    banks, cache, audit_rows, transitions = {}, {}, [], []
    calls, audit_calls = 0, 0
    try:
        (output / "banks").mkdir()
        for identifier, settings in plan["unique_banks"].items():
            task = make_task(settings["task"], settings["n_qubits"], settings["field"])
            bank = build_bank(
                task,
                settings["size"],
                settings["seed"],
                settings["max_evaluations"],
                settings["design"],
            )
            if len(bank) != settings["size"] or len({c.candidate_id for c in bank}) != len(bank):
                raise ValueError("Incomplete/duplicate screen bank")
            calls += sum(c.training_evaluations for c in bank)
            write_json(output / "banks" / f"{identifier}.json", [c.export() for c in bank])
            banks[identifier] = task, bank
        for case in suite.cases:
            config = case.configuration
            for seed in suite.seeds:
                identifier = digest(bank_settings(config, seed))
                task, bank = banks[identifier]
                previous, old = None, None
                for epoch in range(config.epochs):
                    current = snapshot(
                        task.n_qubits,
                        epoch,
                        config.epochs,
                        config.scenario,
                        config.base_error,
                        config.drift_error,
                        config.changed_edge,
                    )
                    key = (identifier, digest(current.errors))
                    if key not in cache:
                        cache[key] = {c.candidate_id: audit_energy(task, c, current) for c in bank}
                        audit_calls += len(bank)
                    energies = cache[key]
                    if not all(np.isfinite(v) for v in energies.values()):
                        raise ValueError("Nonfinite screen audit")
                    prefix = {"case_id": case.case_id, "seed": seed, "epoch": epoch}
                    audit_rows.extend(
                        {**prefix, "bank_id": identifier, "candidate_id": i, "energy": energy}
                        for i, energy in energies.items()
                    )
                    if previous is not None:
                        transitions.append(
                            {**prefix, **transition_metrics(bank, old, current, previous, energies)}
                        )
                    previous, old = energies, current
        _csv(output / "audit_energies.csv", audit_rows)
        _csv(output / "screen_transitions.csv", transitions)
        summaries = []
        for case in suite.cases:
            rows = [r for r in transitions if r["case_id"] == case.case_id]
            summaries.append(
                {
                    "case_id": case.case_id,
                    "n_seed_clusters": len(suite.seeds),
                    "seeds_with_winner_set_reversal": len(
                        {r["seed"] for r in rows if r["winner_set_reversal"]}
                    ),
                    "seeds_with_locality_opportunity": len(
                        {r["seed"] for r in rows if r["locality_opportunity"]}
                    ),
                    "max_previous_optimal_set_regret": max(
                        r["previous_optimal_set_regret"] for r in rows
                    ),
                    "zero_exposure_violations": sum(r["zero_exposure_violations"] for r in rows),
                }
            )
        result = {
            "schema_version": 1,
            "screen_id": manifest["screen_id"],
            "case_summaries": summaries,
            "unique_banks": len(banks),
            "ideal_objective_calls": calls,
            "audit_evaluations_executed": audit_calls,
            "audit_rows": len(audit_rows),
            "online_shots": 0,
            "meaning": manifest["scope"],
        }
        if len(audit_rows) != plan["audit_rows"]:
            raise ValueError("Incomplete screen audit matrix")
        write_json(output / "screen_summary.json", result)
        lines = [
            "# Multi-edge opportunity screen (development only)",
            "",
            manifest["scope"],
            "",
            "| Case | Seeds | Winner-set reversals | Locality opportunities | "
            "Invariance violations |",
            "|---|---:|---:|---:|---:|",
        ]
        for r in summaries:
            lines.append(
                f"| {r['case_id']} | {r['n_seed_clusters']} | "
                f"{r['seeds_with_winner_set_reversal']} | "
                f"{r['seeds_with_locality_opportunity']} | {r['zero_exposure_violations']} |"
            )
        lines += [
            "",
            "A reversal requires every previous tolerance-optimal candidate to have "
            "positive current regret. A locality opportunity additionally requires an unaffected "
            "candidate with a nonempty compiled CX footprint to be currently optimal. "
            "Neither condition establishes a benefit over global matching.",
            "",
            f"Shared bank preparation: {calls} ideal objective calls; "
            f"{audit_calls} distinct exact audit evaluations; zero online shots.",
            "",
        ]
        (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
        if any(r["zero_exposure_violations"] for r in summaries):
            raise ValueError("Zero-exposure invariance violated; screen is invalid")
        write_json(output / "screen_status.json", {"status": "completed"})
        names = REPORTS | {f"banks/{i}.json" for i in banks}
        if any((output / name).is_symlink() for name in names):
            raise ValueError("Screen artifacts must not be symlinks")
        write_json(
            output / "completed.json",
            {
                "screen_id": manifest["screen_id"],
                "hashes": {name: file_digest(output / name) for name in sorted(names)},
            },
        )
        return result
    except BaseException as exc:
        write_json(output / "screen_status.json", {"status": "failed", "error": str(exc)})
        raise


def verify_screen(output: Path) -> dict:
    manifest = read_json(output / "screen_manifest.json")
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported screen manifest schema")
    identifier = manifest.pop("screen_id")
    if digest(manifest) != identifier:
        raise ValueError("Screen manifest digest mismatch")
    receipt = read_json(output / "completed.json")
    if (output / "banks").is_symlink() or any(
        digest(settings) != bank_id
        for bank_id, settings in manifest["plan"]["unique_banks"].items()
    ):
        raise ValueError("Invalid screen bank identities/directory")
    names = REPORTS | {f"banks/{i}.json" for i in manifest["plan"]["unique_banks"]}
    if receipt["screen_id"] != identifier or set(receipt["hashes"]) != names:
        raise ValueError("Screen receipt identity/artifact list mismatch")
    for name in names:
        path = output / name
        if path.is_symlink() or file_digest(path) != receipt["hashes"][name]:
            raise ValueError(f"Screen artifact checksum mismatch: {name}")
    result = read_json(output / "screen_summary.json")
    if read_json(output / "screen_status.json")["status"] != "completed":
        raise ValueError("Screen is not completed")
    if result["screen_id"] != identifier:
        raise ValueError("Screen summary identity mismatch")
    return result


def select_locality_cell(suite: Suite, output: Path, receipt_path: Path) -> dict:
    """Apply the declared 3-of-5 gate, never optimize against controller outcomes."""
    screen_plan(suite)
    if receipt_path.exists():
        raise ValueError(f"Refusing to overwrite selection receipt: {receipt_path}")
    summary = verify_screen(output)
    manifest = read_json(output / "screen_manifest.json")
    if digest(manifest["declaration"]) != digest(suite.declaration()):
        raise ValueError("Selection configuration does not match the verified screen")
    if len(suite.seeds) != 5 or len(suite.cases) != 12:
        raise ValueError("The declared locality gate requires five seeds and twelve cases")
    rows = {r["case_id"]: r for r in summary["case_summaries"]}
    if len(rows) != 12 or set(rows) != {c.case_id for c in suite.cases}:
        raise ValueError("Incomplete/duplicate selection case summaries")
    cells, used = [], set()
    for field, cap in ((0.5, 120), (1.5, 120), (0.5, 480), (1.5, 480)):
        counts = {}
        for profile, edge in (("stable", "1-2"), ("abrupt", "0-1"), ("abrupt", "1-2")):
            cases = [
                c
                for c in suite.cases
                if (
                    c.configuration.field == field
                    and c.configuration.training_evaluations == cap
                    and c.configuration.scenario == profile
                    and c.configuration.changed_edge == edge
                    and c.configuration.task == "ising"
                    and c.configuration.n_qubits == 4
                )
            ]
            if len(cases) != 1:
                raise ValueError("Selection requires the complete predeclared field/fit/edge grid")
            used.add(cases[0].case_id)
            row = rows[cases[0].case_id]
            if row["n_seed_clusters"] != 5 or row["zero_exposure_violations"]:
                raise ValueError("Invalid seed count or invariance failure in selection")
            counts[f"{profile}-{edge}"] = row["seeds_with_locality_opportunity"]
        eligible = counts["abrupt-0-1"] >= 3 and counts["abrupt-1-2"] >= 3
        cells.append(
            {"field": field, "training_evaluations": cap, "counts": counts, "eligible": eligible}
        )
    if len(used) != 12:
        raise ValueError("Selection did not retain every declared grid case")
    selected = next((c for c in cells if c["eligible"]), None)
    result = {
        "schema_version": 1,
        "screen_id": summary["screen_id"],
        "status": "selected" if selected else "blocked",
        "selection": selected,
        "ordered_cells": cells,
        "rule": "First admissible cell in field/cap order (0.5,120), (1.5,120), "
        "(0.5,480), (1.5,480); at least 3/5 seeds with locality opportunity on BOTH abrupt "
        "edge cases; no controller outcomes used. A failed gate stops before reserved seeds.",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(receipt_path, result)
    return result
