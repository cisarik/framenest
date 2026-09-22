"""Transient text results for one bridge process.

Answers live in memory for the life of the process. This module does not open
a library database, render HTML, or write answer assets.
"""

from __future__ import annotations

import re
import secrets

RESULT_ID_RE = re.compile(r"^[a-f0-9]{16}$")


class ResultStore:
    """In-memory map of job answers. Nothing is written to disk."""

    def __init__(self) -> None:
        self._records: dict[str, dict] = {}

    @staticmethod
    def valid_id(result_id: object) -> bool:
        return isinstance(result_id, str) and RESULT_ID_RE.fullmatch(result_id) is not None

    def put_text(self, job_id: str, text: str, url: str | None) -> str:
        result_id = secrets.token_hex(8)
        self._records[result_id] = {
            "result_id": result_id,
            "job_id": job_id,
            "text": text,
            "url": url,
        }
        return result_id

    def get(self, result_id: str) -> dict | None:
        if not self.valid_id(result_id):
            return None
        record = self._records.get(result_id)
        return dict(record) if record is not None else None
