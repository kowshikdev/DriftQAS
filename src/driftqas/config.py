"""Fail-fast validation for inexpensive, declared simulation experiments."""

from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import yaml

from driftqas.policies import POLICIES


@dataclass(frozen=True)
class Config:
    task: str = "h2"
    n_qubits: int = 4
    field: float = 0.5
    candidates: int = 8
    training_evaluations: int = 100
    seed: int = 7
    epochs: int = 3
    scenario: str = "abrupt"
    base_error: float = 0.005
    drift_error: float = 0.04
    changed_edge: str = "0-1"
    budget_per_epoch: int = 8192
    confirmation_fraction: float = 0.2
    low_shots: int = 128
    high_shots: int = 512
    initial_seeds: int = 3
    policies: tuple[str, ...] = ("restart", "reuse", "driftqas")
    drift_scale: float = 0.02
    forgetting: float = 1.0

    def validate(self) -> "Config":
        if self.task not in {"h2", "ising"} or not 2 <= self.n_qubits <= 6:
            raise ValueError("Task must be h2 or ising; Ising size must be 2–6")
        for name in (
            "candidates",
            "training_evaluations",
            "epochs",
            "budget_per_epoch",
            "low_shots",
            "high_shots",
            "initial_seeds",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        if self.candidates > 64 or self.epochs > 100 or self.training_evaluations < 4:
            raise ValueError("Prototype supports up to 64 candidates/100 epochs and >=4 fit calls")
        if self.low_shots < 2 or self.high_shots < self.low_shots:
            raise ValueError("Use high_shots >= low_shots >= 2")
        if self.initial_seeds > self.candidates:
            raise ValueError("initial_seeds cannot exceed candidate count")
        if not self.policies or len(set(self.policies)) != len(self.policies):
            raise ValueError("Specify a nonempty unique policy list")
        if any(p not in POLICIES for p in self.policies):
            raise ValueError(f"Policies must be chosen from {POLICIES}")
        if self.scenario not in {"stable", "abrupt", "gradual", "recurring"}:
            raise ValueError("Unknown scenario")
        for value in (self.base_error, self.drift_error):
            if not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Depolarizing probabilities must be finite and between 0 and 1")
        if not 0 < self.confirmation_fraction < 1:
            raise ValueError("confirmation_fraction must be strictly between 0 and 1")
        if not np.isfinite(self.drift_scale) or self.drift_scale <= 0:
            raise ValueError("drift_scale must be positive and finite")
        if not np.isfinite(self.forgetting) or self.forgetting < 0:
            raise ValueError("forgetting must be nonnegative and finite")
        if not np.isfinite(self.field) or self.field <= 0:
            raise ValueError("field must be positive and finite")
        return self


def load_config(path: Path) -> Config:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Configuration must be a YAML mapping")
    unknown = set(data) - {f.name for f in fields(Config)}
    if unknown:
        raise ValueError(f"Unknown configuration fields: {sorted(unknown)}")
    if "policies" in data:
        data["policies"] = tuple(data["policies"])
    return Config(**data).validate()
