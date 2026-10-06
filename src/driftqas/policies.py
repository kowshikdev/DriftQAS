"""Transparent staged scheduling; ideal-source priors plus noisy residual modeling.

This is a finite-library research scaffold, not a novel optimal acquisition algorithm.
Audit energies and future calibration are absent from this module's interface.
"""

import warnings
from dataclasses import dataclass, replace

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

from driftqas.calibration import Calibration
from driftqas.circuits import Candidate


@dataclass(frozen=True)
class Components:
    relevance: str = "none"
    refresh: str = "none"
    allocation: str = "staged"
    restart: bool = False
    random: bool = False


_DRIFTQAS = Components(relevance="circuit", refresh="affected")
POLICY_COMPONENTS = {
    "random": Components(random=True),
    "restart": Components(restart=True),
    "reuse": Components(),
    "global_forgetting": Components(relevance="global"),
    "periodic_refresh": Components(refresh="periodic"),
    "driftqas": _DRIFTQAS,
    # Each ablation changes exactly one control; the model/features are unchanged.
    "driftqas_global_relevance": replace(_DRIFTQAS, relevance="global"),
    "driftqas_no_refresh": replace(_DRIFTQAS, refresh="none"),
    "driftqas_fixed_shots": replace(_DRIFTQAS, allocation="fixed"),
}
POLICIES = tuple(POLICY_COMPONENTS)


@dataclass
class Observation:
    candidate_id: str
    calibration: Calibration
    energy: float
    variance: float
    shots_per_group: int


class Policy:
    def __init__(
        self,
        name: str,
        bank: list[Candidate],
        seed: int,
        drift_scale: float = 0.02,
        forgetting: float = 1.0,
    ):
        if name not in POLICIES:
            raise ValueError(f"Unknown policy: {name}")
        self.name, self.bank = name, bank
        self.components = POLICY_COMPONENTS[name]
        self.rng = np.random.default_rng(seed)
        self.observations: list[Observation] = []
        self.by_id = {c.candidate_id: c for c in bank}
        self.drift_scale, self.forgetting = drift_scale, forgetting
        self.refresh_queue: list[str] = []

    def add(self, observation: Observation) -> None:
        self.observations.append(observation)

    def minimum_shots(self, low_shots: int, high_shots: int) -> int:
        return high_shots if self.components.allocation == "fixed" else low_shots

    def begin_epoch(self, calibration: Calibration) -> None:
        self.refresh_queue = []
        if self.components.restart:
            self.observations = []
        elif self.components.refresh != "none" and self.observations:
            means, _ = self.predict(calibration)
            for i in np.argsort(means)[:3]:
                candidate = self.bank[int(i)]
                old = [o for o in self.observations if o.candidate_id == candidate.candidate_id]
                affected = any(
                    calibration.exposure(candidate.footprint, o.calibration, self.drift_scale) > 0
                    for o in old
                )
                if old and (self.components.refresh == "periodic" or affected):
                    self.refresh_queue.append(candidate.candidate_id)

    def _features(self, candidate: Candidate, calibration: Calibration) -> list[float]:
        counts = [candidate.footprint.get(edge, 0) for edge in sorted(calibration.errors)]
        return [
            candidate.ideal_energy,
            candidate.spec["layers"] / 3,
            len(candidate.parameters) / 48,
            candidate.circuit.depth() / 48,
            *[c / 6 for c in counts],
            *[
                c * calibration.errors[e] / 0.1
                for c, e in zip(counts, sorted(calibration.errors), strict=True)
            ],
        ]

    def relevance(self, observation: Observation, current: Calibration) -> float:
        if self.components.relevance == "global":
            exposure = (
                max(
                    abs(current.errors[e] - observation.calibration.errors[e])
                    for e in current.errors
                )
                / self.drift_scale
            )
        elif self.components.relevance == "circuit":
            exposure = current.exposure(
                self.by_id[observation.candidate_id].footprint,
                observation.calibration,
                self.drift_scale,
            )
        else:
            return 1.0
        return float(np.exp(-min(20.0, self.forgetting * exposure)))

    def predict(self, current: Calibration) -> tuple[np.ndarray, np.ndarray]:
        ideal = np.array([c.ideal_energy for c in self.bank])
        if not self.observations:
            return ideal, np.full(len(self.bank), 0.1)
        x, y, noise = [], [], []
        for observation in self.observations:
            candidate = self.by_id[observation.candidate_id]
            x.append(self._features(candidate, observation.calibration))
            y.append(observation.energy - candidate.ideal_energy)
            relevance = self.relevance(observation, current)
            # Discounted evidence receives extra transfer variance, not a changed label.
            noise.append(max(1e-5, observation.variance) / relevance + 0.01 * (1.0 - relevance))
        gp = GaussianProcessRegressor(
            kernel=ConstantKernel(0.04, constant_value_bounds="fixed")
            * Matern(length_scale=1.0, length_scale_bounds="fixed", nu=1.5),
            alpha=np.array(noise),
            optimizer=None,
            normalize_y=False,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            gp.fit(np.array(x), np.array(y))
        residual, std = gp.predict(
            np.array([self._features(c, current) for c in self.bank]), return_std=True
        )
        return ideal + residual, std

    def choose(
        self, current: Calibration, low_shots: int, high_shots: int
    ) -> tuple[Candidate, int, str] | None:
        if self.refresh_queue:
            return (
                self.by_id[self.refresh_queue.pop(0)],
                self.minimum_shots(low_shots, high_shots),
                "revalidation",
            )
        totals = {
            c.candidate_id: sum(
                o.shots_per_group
                for o in self.observations
                if o.candidate_id == c.candidate_id
                and o.calibration.calibration_id == current.calibration_id
            )
            for c in self.bank
        }
        eligible = [i for i, c in enumerate(self.bank) if totals[c.candidate_id] < 2 * high_shots]
        if not eligible:
            return None
        if self.components.random:
            index = int(self.rng.choice(eligible))
        else:
            means, std = self.predict(current)
            index = min(eligible, key=lambda i: means[i] - 0.5 * std[i])
        candidate = self.bank[index]
        total = totals[candidate.candidate_id]
        shots = (
            high_shots
            if self.components.allocation == "fixed"
            else low_shots
            if total == 0
            else max(low_shots, high_shots - total)
        )
        old = any(o.candidate_id == candidate.candidate_id for o in self.observations)
        phase = "precision" if total else "revalidation" if old else "exploration"
        return candidate, shots, phase

    def recommend(self, current: Calibration) -> Candidate:
        means, _ = self.predict(current)
        return self.bank[int(np.argmin(means))]
