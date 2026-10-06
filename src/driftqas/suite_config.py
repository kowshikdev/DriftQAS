"""Predeclared cases and disjoint seed partitions for repeated-seed studies."""

import re
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from driftqas.config import Config, config_from_mapping
from driftqas.runner import preflight

_SLUG = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
PRIMARY_METRIC = "mean_selection_regret"


@dataclass(frozen=True)
class Case:
    case_id: str
    configuration: Config


@dataclass(frozen=True)
class Suite:
    name: str
    split: str
    seed_sets: dict[str, tuple[int, ...]]
    cases: tuple[Case, ...]
    primary_target: str
    primary_comparator: str
    bootstrap_samples: int
    bootstrap_seed: int

    @property
    def seeds(self) -> tuple[int, ...]:
        return self.seed_sets[self.split]

    def declaration(self) -> dict:
        return {
            "name": self.name,
            "split": self.split,
            "seed_sets": {name: list(seeds) for name, seeds in self.seed_sets.items()},
            "cases": [
                {"case_id": case.case_id, "configuration": asdict(case.configuration)}
                for case in self.cases
            ],
            "primary_target": self.primary_target,
            "primary_comparator": self.primary_comparator,
            "primary_metric": PRIMARY_METRIC,
            "primary_scope": "equal-weight mean over all declared cases and epochs",
            "bootstrap_samples": self.bootstrap_samples,
            "bootstrap_seed": self.bootstrap_seed,
        }

    def episodes(self) -> list[dict]:
        return [
            {
                "case_id": case.case_id,
                "seed": seed,
                "configuration": {**asdict(case.configuration), "seed": seed},
            }
            for case in self.cases
            for seed in self.seeds
        ]

    def plan(self) -> dict:
        policies = self.cases[0].configuration.policies
        return {
            "name": self.name,
            "split": self.split,
            "cases": len(self.cases),
            "seeds": list(self.seeds),
            "policies": list(policies),
            "paired_episodes": len(self.cases) * len(self.seeds),
            "policy_episodes": len(self.cases) * len(self.seeds) * len(policies),
            "online_shot_upper_bound": sum(
                case.configuration.epochs
                * case.configuration.budget_per_epoch
                * len(policies)
                * len(self.seeds)
                for case in self.cases
            ),
            "ideal_objective_call_upper_bound": sum(
                case.configuration.candidates
                * case.configuration.training_evaluations
                * len(self.seeds)
                for case in self.cases
            ),
            "offline_audit_evaluations": sum(
                case.configuration.candidates * case.configuration.epochs * len(self.seeds)
                for case in self.cases
            ),
            "primary_contrast": f"{self.primary_target} minus {self.primary_comparator}",
            "primary_metric": PRIMARY_METRIC,
            "matrix": [
                {
                    "case_id": case.case_id,
                    "task": case.configuration.task,
                    "n_qubits": 2
                    if case.configuration.task == "h2"
                    else case.configuration.n_qubits,
                    "field": case.configuration.field
                    if case.configuration.task == "ising"
                    else None,
                    "scenario": case.configuration.scenario,
                    "epochs": case.configuration.epochs,
                    "budget_per_epoch": case.configuration.budget_per_epoch,
                }
                for case in self.cases
            ],
            "note": "Simulation only. Preparation repeats per case/seed and is shared across "
            "policies, not charged as online shots. A held_out label does not prove an unseen run.",
        }


def _mapping(value, label):
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a mapping with string keys")
    return value


def _unknown(data, allowed, label):
    unknown = set(data) - set(allowed)
    if unknown:
        raise ValueError(f"Unknown {label} fields: {sorted(unknown)}")


def _seeds(value, label):
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= 1000
        or any(type(seed) is not int or not 0 <= seed < 2**32 for seed in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError(f"{label} needs 1–1000 unique integer seeds in [0, 2**32)")
    return tuple(value)


def suite_from_mapping(data: dict) -> Suite:
    data = _mapping(data, "Suite")
    _unknown(
        data,
        {
            "name",
            "split",
            "seed_sets",
            "base",
            "cases",
            "primary_target",
            "primary_comparator",
            "bootstrap_samples",
            "bootstrap_seed",
        },
        "suite",
    )
    required = {"name", "split", "seed_sets", "base", "cases"}
    if not required <= set(data):
        raise ValueError(f"Missing suite fields: {sorted(required - set(data))}")
    if not isinstance(data["name"], str) or not _SLUG.fullmatch(data["name"]):
        raise ValueError("Suite name must be a lowercase slug, up to 64 characters")
    if data["split"] not in ("development", "held_out"):
        raise ValueError("split must be development or held_out")
    partitions = _mapping(data["seed_sets"], "seed_sets")
    if set(partitions) != {"development", "held_out"}:
        raise ValueError("Declare both development and held_out seed sets")
    seed_sets = {name: _seeds(values, name) for name, values in partitions.items()}
    if set(seed_sets["development"]) & set(seed_sets["held_out"]):
        raise ValueError("Development and held_out seeds must be disjoint")
    base = _mapping(data["base"], "base")
    if "seed" in base:
        raise ValueError("Use seed_sets, not a seed in base")
    config_from_mapping(base)
    entries = data["cases"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 256:
        raise ValueError("Declare 1–256 cases")
    cases, identifiers, configurations = [], set(), set()
    for entry in entries:
        entry = _mapping(entry, "Case")
        _unknown(entry, {"id", "overrides"}, "case")
        identifier = entry.get("id")
        if (
            not isinstance(identifier, str)
            or not _SLUG.fullmatch(identifier)
            or identifier in identifiers
            or identifier == "all_cases"
        ):
            raise ValueError("Each case needs a unique safe lowercase id (not all_cases)")
        overrides = _mapping(entry.get("overrides", {}), "overrides")
        if {"seed", "policies"} & set(overrides):
            raise ValueError("Cases cannot override seeds or the shared policy list")
        # Seed zero is a placeholder in the declaration, replaced by each declared seed.
        config = config_from_mapping({**base, **overrides, "seed": 0})
        preflight(config)
        signature = repr(asdict(config))
        if signature in configurations:
            raise ValueError("Duplicate case configurations would silently change case weighting")
        identifiers.add(identifier)
        configurations.add(signature)
        cases.append(Case(identifier, config))
    target, comparator = (
        data.get("primary_target", "driftqas"),
        data.get("primary_comparator", "reuse"),
    )
    if target == comparator or any(
        policy not in cases[0].configuration.policies for policy in (target, comparator)
    ):
        raise ValueError("Primary target and comparator must be distinct declared policies")
    samples, bootstrap_seed = data.get("bootstrap_samples", 5000), data.get("bootstrap_seed", 2026)
    if type(samples) is not int or not 100 <= samples <= 100000:
        raise ValueError("bootstrap_samples must be an integer between 100 and 100000")
    if type(bootstrap_seed) is not int or not 0 <= bootstrap_seed < 2**32:
        raise ValueError("bootstrap_seed must be an integer in [0, 2**32)")
    return Suite(
        data["name"],
        data["split"],
        seed_sets,
        tuple(cases),
        target,
        comparator,
        samples,
        bootstrap_seed,
    )


def load_suite(path: Path) -> Suite:
    with path.open(encoding="utf-8") as stream:
        return suite_from_mapping(yaml.safe_load(stream))
