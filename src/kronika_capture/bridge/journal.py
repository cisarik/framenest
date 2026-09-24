"""Private SQLite capture coordination, committed before protocol acknowledgement."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


class JournalUnavailable(Exception):
    """Safe failure; never include SQLite paths or stored content."""


class Journal:
    """One durable transaction for job state and service fencing metadata."""

    def __init__(self, root: Path) -> None:
        self.path = root / "capture-journal.sqlite3"
        try:
            root.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(root, 0o700)
            fd = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            os.chmod(self.path, 0o600)
            self.connection = sqlite3.connect(self.path, check_same_thread=False)
            self.connection.execute("PRAGMA journal_mode=DELETE")
            self.connection.execute("PRAGMA synchronous=FULL")
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, "
                "request_id TEXT UNIQUE NOT NULL, record TEXT NOT NULL)"
            )
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS service (singleton INTEGER PRIMARY KEY CHECK(singleton=1), "
                "record TEXT NOT NULL)"
            )
            self.connection.commit()
            with self.connection:
                self.connection.execute("PRAGMA quick_check").fetchall()
            # SQLite syncs transactions; also make initial directory creation durable.
            directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except (OSError, sqlite3.Error):
            if hasattr(self, "connection"):
                self.connection.close()
            raise JournalUnavailable() from None

    def load(self) -> tuple[list[dict], dict]:
        try:
            # Hold the writer lock through recovery and its new epoch commit.
            # A concurrent old manager must not admit work between load and reconciliation.
            self.connection.execute("BEGIN IMMEDIATE")
            check = self.connection.execute("PRAGMA quick_check").fetchall()
            if check != [("ok",)]:
                raise ValueError()
            records = [json.loads(row[0]) for row in self.connection.execute("SELECT record FROM jobs")]
            if any(not isinstance(record, dict) for record in records):
                raise ValueError()
            row = self.connection.execute("SELECT record FROM service WHERE singleton=1").fetchone()
            return records, json.loads(row[0]) if row else {}
        except (sqlite3.Error, ValueError, TypeError):
            self.connection.rollback()
            raise JournalUnavailable() from None

    def commit(self, records: list[dict], service: dict, *, expected_epoch: str | None) -> None:
        try:
            if not self.connection.in_transaction:
                self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute("SELECT record FROM service WHERE singleton=1").fetchone()
            actual_epoch = json.loads(row[0]).get("epoch") if row else None
            if actual_epoch != expected_epoch:
                raise JournalUnavailable()
            retained = {r["job_id"] for r in records}
            for (job_id,) in self.connection.execute("SELECT job_id FROM jobs").fetchall():
                if job_id not in retained:
                    self.connection.execute("DELETE FROM jobs WHERE job_id=?", (job_id,))
            self.connection.executemany(
                "INSERT INTO jobs VALUES (?, ?, ?) ON CONFLICT(job_id) DO UPDATE SET "
                "request_id=excluded.request_id, record=excluded.record WHERE record<>excluded.record",
                [(r["job_id"], r["request_id"], json.dumps(r, ensure_ascii=False)) for r in records],
            )
            self.connection.execute(
                "INSERT OR REPLACE INTO service VALUES (1, ?)", (json.dumps(service),)
            )
            self.connection.commit()
        except (sqlite3.Error, OSError, ValueError, JournalUnavailable):
            try:
                self.connection.rollback()
            except sqlite3.Error:
                pass
            raise JournalUnavailable() from None

    def close(self) -> None:
        self.connection.close()


class JournalResults:
    """Compatibility result lookup backed by retained jobs, without a second cache."""

    def __init__(self, manager) -> None:
        self.manager = manager

    def get(self, result_id: str) -> dict | None:
        return self.manager.result_record(result_id)
