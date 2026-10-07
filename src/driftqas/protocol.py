"""Cross-partition protocol freeze, before calibration or held-out execution."""

import json
from pathlib import Path

from driftqas.provenance import canonical, digest, read_json, runtime_identity, write_json
from driftqas.suite_config import Suite


def protocol_declaration(declaration: dict) -> dict:
    # The selected partition is the only difference permitted across study phases.
    return json.loads(
        canonical({key: value for key, value in declaration.items() if key != "split"})
    )


def read_frozen(path: Path) -> dict:
    frozen = read_json(path)
    payload = {key: value for key, value in frozen.items() if key != "frozen_id"}
    if frozen.get("schema_version") != 1 or digest(payload) != frozen.get("frozen_id"):
        raise ValueError("Frozen protocol schema/digest mismatch")
    return frozen


def freeze_protocol(suite: Suite, output: Path) -> dict:
    if suite.split != "development":
        raise ValueError("Freeze from the development declaration before other partitions")
    if "calibration" not in suite.seed_sets:
        raise ValueError("Declare a separate calibration seed partition before freezing")
    if output.exists():
        raise ValueError(f"Refusing to overwrite a frozen protocol: {output}")
    frozen = {
        "schema_version": 1,
        "declaration": protocol_declaration(suite.declaration()),
        "runtime": runtime_identity(),
        "interval_calibration": {
            "method": "per-policy seed-cluster maximum normalized absolute residual",
            "alpha": 0.05,
            "standard_deviation_floor": 0.002,
            "shrink_intervals": False,
        },
        "meaning": "Content-addressed pre-execution declaration, not proof of an unseen test. "
        "Calibration scales are posthoc diagnostics and never alter the online policy.",
    }
    frozen["frozen_id"] = digest(frozen)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, frozen)
    return frozen


def validate_frozen(suite: Suite, path: Path, identity: dict) -> dict:
    frozen = read_frozen(path)
    if canonical(frozen["declaration"]) != canonical(protocol_declaration(suite.declaration())):
        raise ValueError("Frozen protocol declaration mismatch; do not retune after freezing")
    if canonical(frozen["runtime"]) != canonical(identity):
        raise ValueError("Frozen protocol source/environment mismatch")
    return frozen
