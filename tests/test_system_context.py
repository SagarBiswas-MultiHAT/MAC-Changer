"""SystemContext behavior and error mapping tests."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from macchanger_pro.errors import OperationError, PlatformError, PrivilegeError
from macchanger_pro.system import SystemContext


@dataclass
class RaisingRunner:
    """Runner that raises a configured exception."""

    exception: Exception

    def run(self, _args: list[str]) -> subprocess.CompletedProcess[str]:
        raise self.exception


@dataclass
class OutputRunner:
    """Runner that emits controlled output."""

    stdout: str

    def run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout=self.stdout, stderr="")


def test_ensure_linux_raises_on_unsupported_platform(tmp_path: Path) -> None:
    context = SystemContext(
        runner=OutputRunner(""),
        sys_class_net=tmp_path / "missing",
        platform_system=lambda: "Windows",
    )

    with pytest.raises(PlatformError):
        context.ensure_linux()


def test_ensure_root_raises_when_geteuid_unavailable(tmp_path: Path) -> None:
    context = SystemContext(
        runner=OutputRunner(""),
        sys_class_net=tmp_path / "missing",
        geteuid=None,
    )

    with pytest.raises(PrivilegeError):
        context.ensure_root()


def test_ensure_root_raises_for_non_root_user(tmp_path: Path) -> None:
    context = SystemContext(
        runner=OutputRunner(""),
        sys_class_net=tmp_path / "missing",
        geteuid=lambda: 1000,
    )

    with pytest.raises(PrivilegeError):
        context.ensure_root()


def test_run_command_wraps_called_process_errors(tmp_path: Path) -> None:
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=["ip", "link", "show"],
        stderr="boom",
    )
    context = SystemContext(
        runner=RaisingRunner(error),
        sys_class_net=tmp_path / "missing",
    )

    with pytest.raises(OperationError, match="Command failed"):
        context.run_command(["ip", "link", "show"])


def test_run_command_wraps_os_errors(tmp_path: Path) -> None:
    context = SystemContext(
        runner=RaisingRunner(OSError("missing executable")),
        sys_class_net=tmp_path / "missing",
    )

    with pytest.raises(OperationError, match="Unable to execute command"):
        context.run_command(["ip", "link", "show"])


def test_list_interfaces_returns_empty_without_sysfs_or_ip(tmp_path: Path) -> None:
    context = SystemContext(
        runner=OutputRunner(""),
        sys_class_net=tmp_path / "missing",
        which=lambda _name: None,
    )

    assert context.list_interfaces() == []
    assert not context.interface_exists("eth0")
    assert context.read_interface_mac("eth0") is None


def test_list_interfaces_skips_malformed_lines_and_duplicates(tmp_path: Path) -> None:
    output = "\n".join(
        [
            "garbage without colon",
            "1: lo: <LOOPBACK>",
            "2: eth0@if4: <BROADCAST>",
            "3: eth0@if4: <BROADCAST>",
            "4: wlan0: <BROADCAST>",
        ]
    )
    context = SystemContext(
        runner=OutputRunner(output),
        sys_class_net=tmp_path / "missing",
        which=lambda name: "/usr/sbin/ip" if name == "ip" else None,
    )

    assert context.list_interfaces() == ["eth0", "wlan0"]


def test_backup_dir_resolution_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MACCHANGER_BACKUP_DIR", "/tmp/custom-macchanger")
    context = SystemContext()

    assert context.backup_dir == Path("/tmp/custom-macchanger")
