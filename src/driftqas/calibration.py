"""Declared synthetic entangler noise, with changes only revealed epoch by epoch."""

import json
from dataclasses import asdict, dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Calibration:
    epoch: int
    errors: dict[str, float]
    scenario: str

    @property
    def calibration_id(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:16]

    def exposure(self, footprint: dict[str, int], old: "Calibration", scale: float) -> float:
        return sum(
            count * abs(self.errors.get(edge, 0.0) - old.errors.get(edge, 0.0)) / scale
            for edge, count in footprint.items()
        )


def snapshot(
    n_qubits: int,
    epoch: int,
    epochs: int,
    scenario: str,
    base_error: float,
    drift_error: float,
    changed_edge: str,
) -> Calibration:
    errors = {f"{i}-{i + 1}": base_error for i in range(n_qubits - 1)}
    if changed_edge not in errors:
        raise ValueError("changed_edge must be on the simulated chain")
    onset = max(1, epochs // 2)
    if scenario == "abrupt" and epoch >= onset:
        errors[changed_edge] = drift_error
    elif scenario == "gradual":
        errors[changed_edge] = base_error + (drift_error - base_error) * epoch / max(1, epochs - 1)
    elif scenario == "recurring" and epoch % 3 == 1:
        errors[changed_edge] = drift_error
    elif scenario not in {"stable", "abrupt", "gradual", "recurring"}:
        raise ValueError(f"Unknown drift scenario: {scenario}")
    return Calibration(epoch, errors, scenario)
