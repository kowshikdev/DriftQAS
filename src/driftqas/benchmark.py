"""Sequential, sealed benchmark episodes with non-destructive episode-level resume."""

import json
import os
import re
import sqlite3
from contextlib import closing, contextmanager
from itertools import zip_longest
from pathlib import Path

from driftqas.config import config_from_mapping
from driftqas.protocol import validate_frozen
from driftqas.provenance import (
    canonical,
    digest,
    file_digest,
    read_json,
    runtime_identity,
    write_json,
)
from driftqas.runner import run
from driftqas.statistics import episode_metrics
from driftqas.suite_config import Suite

_ATTEMPT = re.compile(r"attempt_[0-9]{4,}\Z")
_REQUIRED = {
    "manifest.json",
    "summary.json",
    "candidates.json",
    "experiments.jsonl",
    "experiments.sqlite",
}


@contextmanager
def _writer_lock(output: Path):
    path = output / ".suite.lock"
    try:
        stream = path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError(
            f"Suite is locked: {path}. If a process crashed, verify no writer is running "
            "before manually removing this lock."
        ) from exc
    try:
        with stream:
            stream.write(f"pid={os.getpid()}\n")
        yield
    finally:
        path.unlink()


def episode_directory(output: Path, episode: dict) -> Path:
    return output / "episodes" / episode["case_id"] / f"seed_{episode['seed']}"


def _verify_event_export(path: Path) -> None:
    """Check committed database events against the portable export before sealing."""
    uri = (path / "experiments.sqlite").resolve().as_uri() + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            rows = connection.execute("SELECT id,kind,payload FROM events ORDER BY id")
            with (path / "experiments.jsonl").open(encoding="utf-8") as stream:
                for row, line in zip_longest(rows, stream):
                    if row is None or line is None:
                        raise ValueError(f"SQLite/JSONL event count mismatch: {path}")
                    identifier, kind, payload = row
                    event = {"id": identifier, "kind": kind, "payload": json.loads(payload)}
                    if canonical(event) != canonical(json.loads(line)):
                        raise ValueError(f"SQLite/JSONL event mismatch at id {identifier}: {path}")
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Invalid episode event database: {path}") from exc


def _verify_attempt(path: Path, episode: dict, identity: dict) -> dict:
    manifest = read_json(path / "manifest.json")
    if manifest.get("status") != "completed":
        raise ValueError(f"Episode is not completed: {path}")
    if canonical(manifest.get("configuration")) != canonical(episode["configuration"]):
        raise ValueError(f"Episode configuration mismatch: {path}")
    if any(manifest.get(key) != value for key, value in identity.items()):
        raise ValueError(f"Episode source/environment mismatch: {path}")
    if any(not (path / name).is_file() for name in _REQUIRED):
        raise ValueError(f"Completed episode is missing required artifacts: {path}")
    _verify_event_export(path)
    summary = read_json(path / "summary.json")
    episode_metrics(summary, episode["configuration"])
    return summary


def _seal(root: Path, attempt: Path, episode: dict, identity: dict) -> dict:
    summary = _verify_attempt(attempt, episode, identity)
    write_json(
        root / "completed.json",
        {
            "attempt": attempt.name,
            "hashes": {
                path.relative_to(attempt).as_posix(): file_digest(path)
                for path in sorted(attempt.rglob("*"))
                if path.is_file()
            },
        },
    )
    return summary


def read_completed(root: Path, episode: dict, identity: dict) -> dict | None:
    receipt_path = root / "completed.json"
    if not receipt_path.exists():
        return None
    receipt = read_json(receipt_path)
    name, hashes = receipt.get("attempt", ""), receipt.get("hashes", {})
    if not isinstance(name, str) or not _ATTEMPT.fullmatch(name) or not _REQUIRED <= set(hashes):
        raise ValueError(f"Invalid completion receipt: {root}")
    attempt = root / name
    for relative, expected in hashes.items():
        path = attempt / relative
        if (
            Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or path.is_symlink()
            or not path.is_file()
            or file_digest(path) != expected
        ):
            raise ValueError(f"Episode artifact checksum mismatch: {path}")
    return _verify_attempt(attempt, episode, identity)


def load_manifest(output: Path) -> dict:
    manifest = read_json(output / "suite_manifest.json")
    declared_digest = manifest.get("protocol_digest")
    payload = {key: value for key, value in manifest.items() if key != "protocol_digest"}
    if manifest.get("schema_version") != 1 or digest(payload) != declared_digest:
        raise ValueError("Suite manifest schema/digest mismatch")
    return manifest


def completed_episodes(output: Path) -> tuple[dict, list[tuple[dict, dict]]]:
    """Read-only complete-pair gate for reporting, independent of current source version."""
    manifest = load_manifest(output)
    completed = []
    missing = []
    for episode in manifest["episodes"]:
        summary = read_completed(episode_directory(output, episode), episode, manifest["runtime"])
        if summary is None:
            missing.append(f"{episode['case_id']}/seed_{episode['seed']}")
        else:
            completed.append((episode, summary))
    if missing:
        raise ValueError(f"Incomplete suite: {len(missing)} missing episodes: {', '.join(missing)}")
    return manifest, completed


def run_suite(suite: Suite, output: Path, resume: bool = False, frozen: Path | None = None) -> dict:
    # All configs/resources have already passed load_suite's preflight, before any write.
    manifest = {
        "schema_version": 1,
        "declaration": suite.declaration(),
        "episodes": suite.episodes(),
        "runtime": runtime_identity(),
        "plan": suite.plan(),
    }
    if frozen is not None:
        manifest["frozen_protocol"] = validate_frozen(suite, frozen, manifest["runtime"])
    elif suite.split == "calibration" or (
        suite.split == "held_out" and "calibration" in suite.seed_sets
    ):
        raise ValueError("Calibration/held_out study execution requires --frozen protocol.json")
    manifest["protocol_digest"] = digest(manifest)
    if resume:
        previous = load_manifest(output)
        if canonical(previous) != canonical(manifest):
            raise ValueError(
                "Cannot resume: suite declaration, source, or dependency versions changed"
            )
    elif output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(
            f"Output directory is not empty: {output}; use --resume for this exact suite"
        )
    output.mkdir(parents=True, exist_ok=True)
    with _writer_lock(output):
        if not resume:
            write_json(output / "suite_manifest.json", manifest)
        identity = manifest["runtime"]
        # Check all receipts before spending resources on any pending episode.
        cache = {
            (episode["case_id"], episode["seed"]): read_completed(
                episode_directory(output, episode), episode, identity
            )
            for episode in manifest["episodes"]
        }
        state = {
            "status": "running",
            "protocol_digest": manifest["protocol_digest"],
            "total_episodes": len(cache),
            "completed_episodes": sum(v is not None for v in cache.values()),
        }
        write_json(output / "suite_status.json", state)
        try:
            for episode in manifest["episodes"]:
                key = (episode["case_id"], episode["seed"])
                if cache[key] is not None:
                    print(f"Verified completed episode: {key[0]} / seed {key[1]}", flush=True)
                    continue
                root = episode_directory(output, episode)
                root.mkdir(parents=True, exist_ok=True)
                attempts = sorted(path for path in root.iterdir() if _ATTEMPT.fullmatch(path.name))
                # A crash after run completion but before receipt creation can be sealed.
                finished = [
                    path
                    for path in attempts
                    if (path / "manifest.json").is_file()
                    and read_json(path / "manifest.json").get("status") == "completed"
                ]
                if len(finished) > 1:
                    raise ValueError(f"Ambiguous completed attempts: {root}")
                if finished:
                    attempt = finished[0]
                else:
                    number = max((int(path.name.split("_")[1]) for path in attempts), default=0) + 1
                    attempt = root / f"attempt_{number:04d}"
                    state["active_episode"] = {
                        "case_id": key[0],
                        "seed": key[1],
                        "attempt": attempt.name,
                    }
                    write_json(output / "suite_status.json", state)
                    print(f"Running {key[0]} / seed {key[1]} / {attempt.name}", flush=True)
                    run(config_from_mapping(episode["configuration"]), attempt)
                cache[key] = _seal(root, attempt, episode, identity)
                state["completed_episodes"] += 1
                state.pop("active_episode", None)
                write_json(output / "suite_status.json", state)
            from driftqas.reporting import analyze_suite

            result = analyze_suite(output)
            state["status"] = "completed"
            write_json(output / "suite_status.json", state)
            return result
        except BaseException as exc:
            state.update(
                {
                    "status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            write_json(output / "suite_status.json", state)
            raise
