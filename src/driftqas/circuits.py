"""Seeded architecture bank, bounded ideal training, fixed physical compilation."""

import json
from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter

import numpy as np
from qiskit import QuantumCircuit, qasm3, transpile
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from driftqas.tasks import Task


class _TrainingLimit(Exception):
    pass


def _train(template, parameters, task, rng, limit):
    calls = 0
    best_energy = float("inf")
    best_parameters = None
    operator = task.operator

    def objective(values):
        nonlocal calls, best_energy, best_parameters
        if calls >= limit:
            raise _TrainingLimit
        calls += 1
        bound = template.assign_parameters(dict(zip(parameters, values, strict=True)))
        energy = float(Statevector.from_instruction(bound).expectation_value(operator).real)
        if energy < best_energy:
            best_energy, best_parameters = energy, values.copy()
        return energy

    try:
        minimize(
            objective,
            rng.uniform(-0.3, 0.3, len(parameters)),
            method="COBYLA",
            options={"maxiter": max(limit, len(parameters) + 2), "tol": 1e-6},
        )
    except _TrainingLimit:
        pass
    return best_parameters, best_energy, calls


@dataclass
class Candidate:
    candidate_id: str
    spec: dict
    parameters: list[float]
    ideal_energy: float
    training_evaluations: int
    preparation_seconds: float
    circuit: QuantumCircuit
    footprint: dict[str, int]

    @property
    def parameter_id(self) -> str:
        return sha256(json.dumps(self.parameters).encode()).hexdigest()[:16]

    def export(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "parameter_id": self.parameter_id,
            "spec": self.spec,
            "parameters": self.parameters,
            "ideal_energy": self.ideal_energy,
            "training_evaluations": self.training_evaluations,
            "preparation_seconds": self.preparation_seconds,
            "footprint": self.footprint,
            "compiled_depth": self.circuit.depth(),
            "compiled_qasm3": qasm3.dumps(self.circuit),
        }


def circuit_footprint(circuit: QuantumCircuit) -> dict[str, int]:
    footprint: dict[str, int] = {}
    for instruction in circuit.data:
        if instruction.operation.name == "cx":
            qubits = sorted(circuit.find_bit(q).index for q in instruction.qubits)
            key = f"{qubits[0]}-{qubits[1]}"
            footprint[key] = footprint.get(key, 0) + 1
    return footprint


def _template(n: int, blocks: list[dict], hf: bool):
    circuit = QuantumCircuit(n)
    if hf:
        circuit.x(0)
    count = sum(n * len(block["rotations"]) for block in blocks)
    parameters = ParameterVector("theta", count)
    j = 0
    for block in blocks:
        for q in range(n):
            for rotation in block["rotations"]:
                getattr(circuit, rotation)(parameters[j], q)
                j += 1
        for left, right in block["edges"]:
            circuit.cx(left, right)
    return circuit, parameters


def build_bank(task: Task, size: int, seed: int, max_evaluations: int) -> list[Candidate]:
    rng = np.random.default_rng(seed)
    candidates = []
    signatures: set[str] = set()
    attempt = 0
    while len(candidates) < size:
        if attempt > 10000:
            raise ValueError("Requested library is larger than the generated search space")
        layers = 1 if attempt == 0 else int(rng.integers(0, 4))
        blocks = []
        for layer in range(layers + 1):
            rotations = ["ry"]
            if attempt and rng.integers(2):
                rotations.append("rz")
            edges = [
                [q, q + 1]
                for q in range(task.n_qubits - 1)
                if layer < layers and (attempt == 0 or rng.random() < 0.75)
            ]
            if attempt and rng.random() < 0.5:
                edges = [list(reversed(edge)) for edge in reversed(edges)]
            blocks.append({"rotations": rotations, "edges": edges})
        spec = {
            "qubits": task.n_qubits,
            "layers": layers,
            "blocks": blocks,
            "hf": task.name == "h2",
            "compiler_seed": seed,
            "basis_gates": ["ry", "rz", "cx"],
            "optimization_level": 1,
            "physical_mapping": list(range(task.n_qubits)),
        }
        signature = json.dumps(spec, sort_keys=True)
        attempt += 1
        if signature in signatures:
            continue
        signatures.add(signature)
        template, params = _template(task.n_qubits, blocks, spec["hf"])
        training_start = perf_counter()
        values, trained_energy, objective_calls = _train(
            template, params, task, rng, max_evaluations
        )
        bound = template.assign_parameters(dict(zip(params, values, strict=True)))
        coupling = [[i, i + 1] for i in range(task.n_qubits - 1)]
        coupling += [list(reversed(edge)) for edge in coupling.copy()]
        compiled = transpile(
            bound,
            basis_gates=spec["basis_gates"],
            coupling_map=coupling,
            initial_layout=spec["physical_mapping"],
            optimization_level=1,
            seed_transpiler=seed,
        )
        candidates.append(
            Candidate(
                sha256(signature.encode()).hexdigest()[:16],
                spec,
                values.tolist(),
                trained_energy,
                objective_calls,
                perf_counter() - training_start,
                compiled,
                circuit_footprint(compiled),
            )
        )
    return candidates
