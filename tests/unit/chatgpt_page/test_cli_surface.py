"""CLI surface after the strip."""

from __future__ import annotations

from kronika.cli import main
from kronika.config import UPLOAD_UNAVAILABLE

REMOVED = (
    ["search", "latest"],
    ["web-search", "latest"],
    ["deep-research", "topic"],
    ["library"],
    ["library", "ui"],
    ["project", "list"],
    ["setup"],
    ["token", "rotate"],
    ["ingest"],
    ["author"],
    ["verify"],
    ["extension"],
)


def test_removed_commands_exit_2() -> None:
    for argv in REMOVED:
        assert main(argv) == 2


def test_ask_file_flag_keeps_the_frozen_sentence(capsys) -> None:
    assert main(["ask", "-f", "/tmp/frames.zip", "identify"]) == 2
    captured = capsys.readouterr()
    assert captured.err.strip() == UPLOAD_UNAVAILABLE
    assert captured.out == ""


def test_supported_commands_parse() -> None:
    assert main(["ask", "--help"]) == 0
    assert main(["bridge", "--help"]) == 0
    assert main(["login", "--help"]) == 0
    assert main(["bridge", "run", "--help"]) == 0
    assert main(["bridge", "status", "--help"]) == 0
