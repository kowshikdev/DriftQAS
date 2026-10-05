"""Small fixed Hamiltonians and qubit-wise commuting measurement groups."""

import json
from dataclasses import dataclass
from hashlib import sha256

import numpy as np
from qiskit.quantum_info import SparsePauliOp


@dataclass(frozen=True)
class Group:
    basis: str
    terms: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class Task:
    name: str
    n_qubits: int
    terms: tuple[tuple[str, float], ...]
    provenance: str

    @property
    def operator(self) -> SparsePauliOp:
        return SparsePauliOp.from_list(list(self.terms))

    @property
    def reference_energy(self) -> float:
        return float(np.linalg.eigvalsh(self.operator.to_matrix())[0])

    @property
    def task_id(self) -> str:
        return sha256(json.dumps(self.terms).encode()).hexdigest()[:16]

    @property
    def constant(self) -> float:
        return sum(c for p, c in self.terms if set(p) == {"I"})

    @property
    def groups(self) -> tuple[Group, ...]:
        groups: list[tuple[list[str], list[tuple[str, float]]]] = []
        for label, coeff in self.terms:
            if set(label) == {"I"}:
                continue
            for basis, terms in groups:
                if all(a == "I" or b == "I" or a == b for a, b in zip(basis, label, strict=True)):
                    for j, axis in enumerate(label):
                        if axis != "I":
                            basis[j] = axis
                    terms.append((label, coeff))
                    break
            else:
                groups.append((list(label), [(label, coeff)]))
        return tuple(Group("".join(b), tuple(t)) for b, t in groups)


def make_task(name: str = "h2", n_qubits: int = 4, field: float = 0.5) -> Task:
    if name == "h2":
        return Task(
            "h2",
            2,
            (
                ("II", -1.052373245772859),
                ("IZ", 0.39793742484318045),
                ("ZI", -0.39793742484318045),
                ("ZZ", -0.01128010425623538),
                ("XX", 0.18093119978423156),
            ),
            "Qiskit Algorithms H2 at 0.735 A; this operator's eigenvalue convention, "
            "without adding a nuclear-energy offset. "
            "https://qiskit-community.github.io/qiskit-algorithms/"
            "tutorials/01_algorithms_introduction.html",
        )
    if name != "ising" or not 2 <= n_qubits <= 6 or not np.isfinite(field) or field <= 0:
        raise ValueError("Use h2 or ising with 2–6 qubits and a positive finite field")
    terms = []
    for i in range(n_qubits - 1):
        label = ["I"] * n_qubits
        label[-1 - i] = label[-2 - i] = "Z"
        terms.append(("".join(label), -1.0))
    for i in range(n_qubits):
        label = ["I"] * n_qubits
        label[-1 - i] = "X"
        terms.append(("".join(label), -float(field)))
    return Task(
        f"ising_{n_qubits}_h{field:g}",
        n_qubits,
        tuple(terms),
        "Open-boundary transverse-field Ising: -sum ZZ - h sum X; J=1.",
    )
