"""Archive verified raw experiment evidence, without source or runtime temporaries."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from driftqas.benchmark import (
    _verify_attempt,
    artifact_names,
    completed_episodes,
    episode_directory,
    load_manifest,
)
from driftqas.provenance import file_digest, read_json


def bundle(suites: list[Path], output: Path, failed_suite: Path | None = None) -> dict:
    if output.exists():
        raise ValueError(f"Refusing to overwrite evidence bundle: {output}")
    declared = [*suites, *([failed_suite] if failed_suite else [])]
    if len({path.name for path in declared}) != len(declared):
        raise ValueError("Archive suite directory names must be unique")
    paths, expected_hashes, records = {}, {}, []
    for suite_dir in declared:
        failed = suite_dir == failed_suite
        status = read_json(suite_dir / "suite_status.json")
        if failed:
            if status["status"] != "failed":
                raise ValueError("The preserved failed suite must remain marked failed")
            manifest = load_manifest(suite_dir)
            episodes = manifest["episodes"]
        else:
            if status["status"] != "completed":
                raise ValueError("Evidence requires verified, completed suites")
            manifest, completed = completed_episodes(suite_dir)
            episodes = [episode for episode, _ in completed]
        for name in ("suite_manifest.json", "suite_status.json"):
            paths[f"{suite_dir.name}/{name}"] = suite_dir / name
        for episode in episodes:
            root = episode_directory(suite_dir, episode)
            receipt = read_json(root / "completed.json")
            attempt = root / receipt["attempt"]
            if failed:
                # Preserve the invalid original seal, but require its actual data to match.
                _verify_attempt(attempt, episode, manifest["runtime"])
                for name in artifact_names(episode):
                    if file_digest(attempt / name) != receipt["hashes"].get(name):
                        raise ValueError("Preserved failed suite has changed canonical data")
            for name in artifact_names(episode):
                path = attempt / name
                archive_name = f"{suite_dir.name}/{path.relative_to(suite_dir).as_posix()}"
                paths[archive_name] = path
                expected_hashes[archive_name] = receipt["hashes"][name]
            receipt_path = root / "completed.json"
            paths[f"{suite_dir.name}/{receipt_path.relative_to(suite_dir).as_posix()}"] = (
                receipt_path
            )
        records.append(
            {
                "directory": suite_dir.name,
                "status": status["status"],
                "protocol_digest": manifest["protocol_digest"],
                "paired_episodes": len(episodes),
                "interpretation": "Failed attempt retained for audit, not analysis input or "
                "additional independent evidence."
                if failed
                else "Verified complete raw suite.",
            }
        )
    receipt = {
        "schema_version": 1,
        "suites": records,
        "files_sha256": {
            name: expected_hashes[name] if name in expected_hashes else file_digest(path)
            for name, path in sorted(paths.items())
        },
        "scope": "Raw counts, predictions, audits, ledgers, banks, QASM, manifests and original "
        "completion receipts. Source code and incidental runtime/transport files are excluded. "
        "Use the matching GitHub source and tested environment for derived reports. A preserved "
        "failed suite is intentionally not accepted by complete-pair reporting.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(paths.items()):
            archive.write(path, name)
        archive.writestr("EVIDENCE.json", json.dumps(receipt, indent=2) + "\n")
    with ZipFile(output) as archive:
        for name, expected in receipt["files_sha256"].items():
            if sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError(f"Evidence archive checksum mismatch: {name}")
        if json.loads(archive.read("EVIDENCE.json")) != receipt:
            raise ValueError("Evidence archive receipt mismatch")
    return {
        "path": str(output.resolve()),
        "size_bytes": output.stat().st_size,
        "suites": records,
        "files": len(paths),
        "sha256": file_digest(output),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suites", nargs="+", type=Path, required=True)
    parser.add_argument("--failed-suite", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(bundle(args.suites, args.output, args.failed_suite), indent=2))


if __name__ == "__main__":
    main()
