"""Append-only JSON experiment events in SQLite and portable JSONL export."""

import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        self.connection = sqlite3.connect(directory / "experiments.sqlite")
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
        self.connection.close()
