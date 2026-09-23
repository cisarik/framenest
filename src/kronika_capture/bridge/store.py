"""Durable local bridge state: job JSON, config, and the metadata-only log."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import threading
import time
from pathlib import Path

from kronika_capture import config, paths

JOB_GLOB = "*.json"


def _atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.chmod(path, mode)


class Store:
    """Filesystem-backed bridge state rooted in one state directory."""

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        log_max_bytes: int = config.LOG_MAX_BYTES,
    ) -> None:
        self.root = Path(root) if root is not None else paths.state_dir()
        self.jobs_dir = self.root / "jobs"
        self.config_path = self.root / "config.json"
        self.token_path = self.root / "token"
        self.log_path = self.root / "bridge.log"
        self.log_rotated_path = self.root / "bridge.log.1"
        self.log_max_bytes = log_max_bytes
        self._lock = threading.Lock()
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for directory in (self.root, self.jobs_dir):
            directory.mkdir(parents=True, exist_ok=True)
            os.chmod(directory, 0o700)

    def _job_path(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def save_job(self, job_id: str, record: dict) -> None:
        payload = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        with self._lock:
            _atomic_write(self._job_path(job_id), payload.encode("utf-8"))

    def _remove_job(self, path: Path) -> None:
        """Drop one job record and any staged asset leftovers under its stem."""

        stem = path.stem
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        shutil.rmtree(self.jobs_dir / stem, ignore_errors=True)

    def prune(
        self,
        max_items: int = config.JOB_RETENTION_MAX_ITEMS,
        max_age_s: float = config.JOB_RETENTION_MAX_AGE_S,
    ) -> list[str]:
        now = time.time()
        removed: list[str] = []
        with self._lock:
            entries = sorted(
                self.jobs_dir.glob(JOB_GLOB),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            keep: list[Path] = []
            for path in entries:
                try:
                    age = now - path.stat().st_mtime
                except OSError:
                    continue
                if age > max_age_s:
                    removed.append(path.name)
                    self._remove_job(path)
                else:
                    keep.append(path)
            for path in keep[max(max_items, 0):]:
                removed.append(path.name)
                self._remove_job(path)
            self._prune_orphan_job_dirs()
        return removed

    def _prune_orphan_job_dirs(self) -> None:
        """Remove direct child directories of jobs/ that have no matching JSON.

        HE-5b-F01: a crash after staging and before promotion can leave
        `<jobs>/<name>/` with no `{name}.json`. Skip symlinks and never
        follow them; remove only directories, never files.
        """

        try:
            children = list(self.jobs_dir.iterdir())
        except OSError:
            return
        for child in children:
            try:
                if child.is_symlink():
                    continue
                if not child.is_dir(follow_symlinks=False):
                    continue
                record = self.jobs_dir / f"{child.name}.json"
                if record.exists():
                    continue
                shutil.rmtree(child, ignore_errors=True)
            except OSError:
                continue

    def load_config(self) -> dict:
        try:
            raw = self.config_path.read_text(encoding="utf-8")
        except OSError:
            return {}
        try:
            payload = json.loads(raw)
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def save_config(self, payload: dict) -> None:
        data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        with self._lock:
            _atomic_write(self.config_path, data.encode("utf-8"))

    def update_config(self, mutator):
        """Read, mutate, and atomically rewrite config.json under one lock.

        The mutator receives the loaded config and may return any value; the
        write happens only when it returns, so other keys are never dropped.
        """

        with self._lock:
            payload = self.load_config()
            result = mutator(payload)
            data = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            _atomic_write(self.config_path, data.encode("utf-8"))
            return result

    def append_log(self, entry: dict) -> None:
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
        encoded = line.encode("utf-8")
        with self._lock:
            try:
                current = self.log_path.stat().st_size
            except OSError:
                current = 0
            if current and current + len(encoded) > self.log_max_bytes:
                try:
                    os.replace(self.log_path, self.log_rotated_path)
                except OSError:
                    pass
            try:
                descriptor = os.open(
                    self.log_path,
                    os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                    0o600,
                )
            except OSError:
                return
            with os.fdopen(descriptor, "ab") as handle:
                handle.write(encoded)

    def log_size(self) -> int:
        try:
            return self.log_path.stat().st_size
        except OSError:
            return 0

    def token_mode(self) -> int | None:
        try:
            return stat.S_IMODE(self.token_path.stat().st_mode)
        except OSError:
            return None
