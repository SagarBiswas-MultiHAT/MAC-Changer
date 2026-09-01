"""CLI behavior tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import FakeSystemContext
from macchanger_pro.cli import (
    EXIT_ABORTED,
    EXIT_OK,
    EXIT_VALIDATION,
    run,
)


def _input_from(values: list[str]):
    iterator = iter(values)

    def _reader(_: str) -> str:
        return next(iterator)

    return _reader


def test_help_command_renders_without_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    process = subprocess.run(
        [sys.executable, "macchanger_pro.py", "--help"],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert process.returncode == 0
    assert "usage:" in process.stdout.lower()


def test_set_command_non_interactive(fake_system: FakeSystemContext) -> None:
    output: list[str] = []
    exit_code = run(
        ["-i", "eth0", "--set", "aa:bb:cc:dd:ee:ff", "--yes"],
        context=fake_system,
        input_fn=lambda _: pytest.fail("input should not be called"),
        output_fn=output.append,
    )

    assert exit_code == EXIT_OK
    assert any("MAC successfully changed" in line for line in output)


def test_restore_aborted_by_user(fake_system: FakeSystemContext) -> None:
    output: list[str] = []
    exit_code = run(
        ["-i", "eth0", "--restore"],
        context=fake_system,
        input_fn=lambda _: "n",
        output_fn=output.append,
    )

    assert exit_code == EXIT_ABORTED
    assert output[-1] == "Aborted."


def test_interactive_restore_flow(fake_system: FakeSystemContext) -> None:
    fake_system.backups["eth0"] = "de:ad:be:ef:00:01"
    output: list[str] = []
    exit_code = run(
        ["-i", "eth0"],
        context=fake_system,
        input_fn=_input_from(["restore"]),
        output_fn=output.append,
    )

    assert exit_code == EXIT_OK
    assert any("Restored original MAC" in line for line in output)


def test_invalid_set_value_returns_validation_error(fake_system: FakeSystemContext) -> None:
    exit_code = run(
        ["-i", "eth0", "--set", "not-a-mac", "--yes"],
        context=fake_system,
        input_fn=lambda _: "ignored",
        output_fn=lambda _: None,
    )

    assert exit_code == EXIT_VALIDATION


def test_show_does_not_require_root(fake_system: FakeSystemContext) -> None:
    fake_system.root = False
    output: list[str] = []
    exit_code = run(
        ["-i", "eth0", "--show"],
        context=fake_system,
        input_fn=lambda _: pytest.fail("input should not be called"),
        output_fn=output.append,
    )

    assert exit_code == EXIT_OK
    assert output == ["eth0 current MAC: 00:11:22:33:44:55"]
