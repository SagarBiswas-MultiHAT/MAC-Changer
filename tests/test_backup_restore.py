"""Backup and restore storage tests."""

from __future__ import annotations

import os
import stat
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from macchanger_pro.system import SystemContext


@dataclass
class NoopRunner:
    """Runner that reports success for every command."""

    def run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=list(args), returncode=0, stdout="", stderr="")


def test_write_backup_if_missing_is_idempotent(tmp_path: Path) -> None:
    backup_dir = tmp_path / "backups"
    context = SystemContext(
        runner=NoopRunner(),
        backup_dir=backup_dir,
        sys_class_net=tmp_path / "net",
        which=lambda _: None,
    )

    first = context.write_backup_mac_if_missing("eth0", "00:11:22:33:44:55")
    second = context.write_backup_mac_if_missing("eth0", "aa:bb:cc:dd:ee:ff")

    assert first == second
    assert first.exists()
    assert first.read_text(encoding="utf-8").strip() == "00:11:22:33:44:55"
    assert context.read_backup_mac("eth0") == "00:11:22:33:44:55"

    if os.name != "nt":
        mode = stat.S_IMODE(first.stat().st_mode)
        assert mode == 0o600


def test_read_backup_mac_returns_none_when_file_missing(tmp_path: Path) -> None:
    context = SystemContext(
        runner=NoopRunner(),
        backup_dir=tmp_path / "backups",
        sys_class_net=tmp_path / "net",
        which=lambda _: None,
    )

    assert context.read_backup_mac("wlan0") is None
