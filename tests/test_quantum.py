import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from driftqas.budget import Budget
from driftqas.calibration import Calibration
from driftqas.circuits import build_bank
from driftqas.evaluation import audit_energy, group_statistics, sample
from driftqas.tasks import Group, make_task


@pytest.fixture(scope="module")
def trained_bank():
    return build_bank(make_task(), 3, 7, 160)


def test_h2_reference_and_identity_not_measured():
    task = make_task()
    assert task.reference_energy == pytest.approx(-1.85727503020238, abs=1e-10)
    assert len(task.groups) == 2
    assert all("II" not in [p for p, _ in g.terms] for g in task.groups)


def test_ising_operator_and_grouping():
    task = make_task("ising", 4, 0.5)
    assert len(task.terms) == 7
    assert len(task.groups) == 2
    assert np.allclose(task.operator.to_matrix(), task.operator.to_matrix().conj().T)


def test_group_variance_retains_covariance():
    # IZ and ZI are perfectly correlated. Treating them independently halves the variance.
    group = Group("ZZ", (("IZ", 1.0), ("ZI", 1.0)))
    mean, variance = group_statistics(group, {"00": 2, "11": 2})
    assert mean == 0.0
    assert variance == pytest.approx(4 / 3)


def test_endianness_and_constant():
    group = Group("ZZ", (("IZ", 2.0), ("ZI", 3.0)))
    mean, variance = group_statistics(group, {"01": 10})
    assert mean == 1.0  # rightmost bit is physical qubit 0
    assert variance == 0.0


def test_zero_noise_matches_statevector(trained_bank):
    task = make_task()
    calibration = Calibration(0, {"0-1": 0.0}, "stable")
    for candidate in trained_bank:
        exact = float(
            Statevector.from_instruction(candidate.circuit).expectation_value(task.operator).real
        )
        assert audit_energy(task, candidate, calibration) == pytest.approx(exact, abs=1e-10)
        assert candidate.ideal_energy == pytest.approx(exact, abs=1e-10)
    assert min(c.ideal_energy for c in trained_bank) - task.reference_energy < 1e-5


def test_finite_shots_match_noisy_target_and_count_all_groups(trained_bank):
    task, candidate = make_task(), trained_bank[0]
    calibration = Calibration(0, {"0-1": 0.04}, "stable")
    budget = Budget(16384, 0)
    result = sample(task, candidate, calibration, 8192, 51, budget)
    target = audit_energy(task, candidate, calibration)
    assert abs(result.energy - target) < 6 * result.standard_error + 1e-6
    assert result.shots == budget.spent == 16384
    assert all(sum(g["counts"].values()) == 8192 for g in result.groups)


def test_budget_rejected_before_backend_execution(trained_bank, monkeypatch):
    def unexpected_backend(*args, **kwargs):
        raise AssertionError("Backend must not execute when allocation is unaffordable")

    monkeypatch.setattr("driftqas.evaluation.AerSimulator", unexpected_backend)
    budget = Budget(100, 20)
    with pytest.raises(ValueError, match="budget"):
        sample(make_task(), trained_bank[0], Calibration(0, {"0-1": 0.0}, "stable"), 64, 1, budget)
    assert budget.spent == 0


def test_training_cap_is_hard_even_below_optimizer_initialization_size():
    bank = build_bank(make_task(), 4, 9, 4)
    assert all(0 < c.training_evaluations <= 4 for c in bank)
