"""Common experiment identity and strict, atomic JSON records."""

import json
import os
import platform
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def file_digest(path: Path) -> str:
    result = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path: Path) -> dict:
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON value in {path}: {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def write_json(path: Path, value: object) -> None:
    # The suite's exclusive writer lock protects its fixed temporary filename.
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def runtime_identity() -> dict:
    return {
        "python": platform.python_version(),
        "thread_environment": {
            name: os.environ.get(name)
            for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "versions": {
            package: version(package)
            for package in (
                "driftqas",
                "qiskit",
                "qiskit-aer",
                "numpy",
                "scipy",
                "scikit-learn",
                "PyYAML",
                "matplotlib",
            )
        },
        "source_digest": sha256(
            b"".join(
                path.name.encode() + b"\0" + path.read_bytes()
                for path in sorted(Path(__file__).parent.glob("*.py"))
            )
        ).hexdigest(),
    }
