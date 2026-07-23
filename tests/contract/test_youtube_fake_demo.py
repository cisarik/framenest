"""Contract test for the deterministic no-network YouTube acceptance demo."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_youtube_fake_demo_runs_the_real_loopback_cli_to_acceptance() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            repository_root / "tests/support/youtube_fake_demo.py",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=45,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Traceback" not in result.stdout + result.stderr
    payloads = [
        json.loads(line)
        for line in (result.stdout + result.stderr).splitlines()
    ]
    acceptance = [
        payload
        for payload in payloads
        if payload.get("event") == "acceptance"
    ]
    assert acceptance == [
        {
            "claim_count": 5,
            "event": "acceptance",
            "location_count": 3,
            "logical_media_count": 3,
            "new_claim_id": acceptance[0]["new_claim_id"],
            "provider_submission_count": 0,
            "recovered_claim_id": acceptance[0]["recovered_claim_id"],
            "repeated_claim_id": acceptance[0]["repeated_claim_id"],
            "resume_seen": True,
            "staging_residue_count": 0,
            "status": "pass",
            "youtube_analysis_notification_count": 0,
        }
    ]
