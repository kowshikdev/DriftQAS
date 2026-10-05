"""Explicit Pauli measurements, correlated-term variance, and isolated exact audit."""

from dataclasses import asdict, dataclass
from time import perf_counter, process_time

import numpy as np
from qiskit.quantum_info import DensityMatrix
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from driftqas.budget import Budget
from driftqas.calibration import Calibration
from driftqas.circuits import Candidate
from driftqas.tasks import Group, Task


@dataclass
class Evaluation:
    energy: float
    variance: float
    shots: int
    shots_per_group: int
    cpu_seconds: float
    wall_seconds: float
    groups: list[dict]
    seed: int

    @property
    def standard_error(self) -> float:
        return float(np.sqrt(self.variance))

    def export(self) -> dict:
        return {**asdict(self), "standard_error": self.standard_error}


def noise_model(calibration: Calibration) -> NoiseModel:
    model = NoiseModel()
    for edge, probability in calibration.errors.items():
        left, right = map(int, edge.split("-"))
        error = depolarizing_error(probability, 2)
        model.add_quantum_error(error, "cx", [left, right])
        model.add_quantum_error(error, "cx", [right, left])
    return model


def group_statistics(group: Group, counts: dict[str, int]) -> tuple[float, float]:
    n = sum(counts.values())
    if n < 2:
        raise ValueError("At least two shots are required to estimate variance")
    values, weights = [], []
    masks = [
        (int("".join("0" if p == "I" else "1" for p in label), 2), coeff)
        for label, coeff in group.terms
    ]
    for bits, count in counts.items():
        state = int(bits.replace(" ", ""), 2)
        value = sum(coeff * (-1 if (state & mask).bit_count() % 2 else 1) for mask, coeff in masks)
        values.append(value)
        weights.append(count)
    mean = float(np.average(values, weights=weights))
    variance = float(np.dot(weights, (np.asarray(values) - mean) ** 2) / (n - 1) / n)
    return mean, variance


def sample(
    task: Task,
    candidate: Candidate,
    calibration: Calibration,
    shots: int,
    seed: int,
    budget: Budget,
    phase: str = "search",
) -> Evaluation:
    if shots < 2:
        raise ValueError("shots_per_group must be at least 2")
    circuits = []
    for group in task.groups:
        circuit = candidate.circuit.copy()
        for q, axis in enumerate(reversed(group.basis)):
            if axis == "X":
                circuit.h(q)
            elif axis == "Y":
                circuit.sdg(q)
                circuit.h(q)
        circuit.measure_all()
        circuits.append(circuit)
    # Charge before execution. If Aer fails, this conservative reservation remains charged.
    budget.charge(len(circuits) * shots, phase)
    start = perf_counter()
    cpu_start = process_time()
    backend = AerSimulator(
        method="density_matrix", noise_model=noise_model(calibration), max_parallel_threads=1
    )
    result = backend.run(circuits, shots=shots, seed_simulator=seed).result()
    if not result.success:
        raise RuntimeError(f"Aer execution failed: {result.status}")
    energy, variance, records, actual = task.constant, 0.0, [], 0
    for i, group in enumerate(task.groups):
        counts = result.get_counts(i)
        total = sum(counts.values())
        if total != shots:
            raise RuntimeError("Executed counts differ from reserved shot allocation")
        mean, mean_variance = group_statistics(group, counts)
        energy += mean
        variance += mean_variance
        actual += total
        records.append(
            {
                "basis": group.basis,
                "terms": list(group.terms),
                "counts": counts,
                "mean": mean,
                "variance_of_mean": mean_variance,
                "shots": total,
            }
        )
    return Evaluation(
        energy,
        variance,
        actual,
        shots,
        process_time() - cpu_start,
        perf_counter() - start,
        records,
        seed,
    )


def audit_energy(task: Task, candidate: Candidate, calibration: Calibration) -> float:
    """Hidden offline metric, never passed into the selection policy."""
    circuit = candidate.circuit.copy()
    circuit.save_density_matrix()
    backend = AerSimulator(
        method="density_matrix", noise_model=noise_model(calibration), max_parallel_threads=1
    )
    result = backend.run(circuit, shots=1).result()
    density = DensityMatrix(result.data(0)["density_matrix"])
    return float(density.expectation_value(task.operator).real)
