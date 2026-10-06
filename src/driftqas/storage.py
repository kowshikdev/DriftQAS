"""Append-only JSON experiment events in SQLite and portable JSONL export."""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        # The live pager and its journals never use the final artifact's name.
        self.live_path = directory / "experiments.live.sqlite"
        self.connection = sqlite3.connect(self.live_path)
        self.connection.execute(
            "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "kind TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        self.connection.commit()

    def append(self, kind: str, payload: dict) -> None:
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        with self.connection:
            self.connection.execute(
                "INSERT INTO events(kind,payload) VALUES (?,?)", (kind, encoded)
            )

    def export(self) -> None:
        with (self.directory / "experiments.jsonl").open("w", encoding="utf-8") as f:
            for identifier, kind, payload in self.connection.execute(
                "SELECT id,kind,payload FROM events ORDER BY id"
            ):
                f.write(
                    json.dumps({"id": identifier, "kind": kind, "payload": json.loads(payload)})
                    + "\n"
                )

    def close(self) -> None:
        # Publish a closed snapshot atomically. No writer retains a handle to the
        # final artifact, and the backup includes all committed pager state.
        snapshot = self.directory / "experiments.snapshot.sqlite"
        try:
            with closing(sqlite3.connect(snapshot)) as destination:
                self.connection.backup(destination)
        finally:
            self.connection.close()
        with snapshot.open("rb") as stream:
            os.fsync(stream.fileno())
        snapshot.replace(self.directory / "experiments.sqlite")
        self.live_path.unlink()
