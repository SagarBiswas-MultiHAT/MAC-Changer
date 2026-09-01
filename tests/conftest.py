"""Shared fixtures for macchanger_pro tests."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
src_string = str(SRC_PATH)
if src_string in sys.path:
    sys.path.remove(src_string)
sys.path.insert(0, src_string)

from macchanger_pro.errors import OperationError, PlatformError, PrivilegeError  # noqa: E402


@dataclass
class FakeSystemContext:
    """In-memory system adapter used for deterministic tests."""

    interfaces: dict[str, str] = field(default_factory=lambda: {"eth0": "00:11:22:33:44:55"})
    available_commands: set[str] = field(default_factory=lambda: {"ip"})
    backups: dict[str, str] = field(default_factory=dict)
    commands: list[list[str]] = field(default_factory=list)
    run_fail_on: set[tuple[str, ...]] = field(default_factory=set)
    root: bool = True
    linux: bool = True
    backup_dir: Path = Path("/tmp/macchanger-test-backups")

    def ensure_linux(self) -> None:
        if not self.linux:
            raise PlatformError("macchanger_pro only supports Linux hosts.")

    def ensure_root(self) -> None:
        if not self.root:
            raise PrivilegeError("This operation requires root privileges. Re-run with sudo.")

    def list_interfaces(self) -> list[str]:
        return sorted(self.interfaces.keys())

    def interface_exists(self, interface: str) -> bool:
        return interface in self.interfaces

    def read_interface_mac(self, interface: str) -> str | None:
        return self.interfaces.get(interface)

    def write_backup_mac_if_missing(self, interface: str, current_mac: str) -> Path:
        if interface not in self.backups:
            self.backups[interface] = current_mac.lower()
        return self.backup_dir / f"{interface}.orig"

    def read_backup_mac(self, interface: str) -> str | None:
        return self.backups.get(interface)

    def command_exists(self, command: str) -> bool:
        return command in self.available_commands

    def run_command(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        command = list(args)
        self.commands.append(command)
        if tuple(command) in self.run_fail_on:
            raise OperationError("forced command failure")

        if (
            len(command) == 7
            and command[:4] == ["ip", "link", "set", "dev"]
            and command[5] == "address"
        ):
            self.interfaces[command[4]] = command[6].lower()
        if (
            len(command) == 5
            and command[0] == "ifconfig"
            and command[2] == "hw"
            and command[3] == "ether"
        ):
            self.interfaces[command[1]] = command[4].lower()

        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")


@pytest.fixture
def fake_system() -> FakeSystemContext:
    """Return a fresh fake system context for each test."""

    return FakeSystemContext()
