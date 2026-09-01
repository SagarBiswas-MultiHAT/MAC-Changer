"""Operating-system adapters and command execution primitives."""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .errors import BackupError, OperationError, PlatformError, PrivilegeError

DEFAULT_BACKUP_DIR = Path("/var/lib/macchanger")


class CommandRunner(Protocol):
    """Protocol for command execution used by the domain service."""

    def run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Run a command and return its completed process metadata."""


@dataclass(slots=True)
class SubprocessCommandRunner:
    """Command runner backed by ``subprocess.run``."""

    def run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args),
            check=True,
            capture_output=True,
            text=True,
        )


def backup_dir_from_env() -> Path:
    """Resolve backup directory from environment with secure default."""

    configured_path = os.environ.get("MACCHANGER_BACKUP_DIR", "").strip()
    if configured_path:
        return Path(configured_path).expanduser()
    return DEFAULT_BACKUP_DIR


@dataclass(slots=True)
class SystemContext:
    """All OS integration points used by core logic."""

    runner: CommandRunner = field(default_factory=SubprocessCommandRunner)
    backup_dir: Path = field(default_factory=backup_dir_from_env)
    sys_class_net: Path = Path("/sys/class/net")
    which: Callable[[str], str | None] = shutil.which
    platform_system: Callable[[], str] = platform.system
    geteuid: Callable[[], int] | None = field(default_factory=lambda: getattr(os, "geteuid", None))

    def ensure_linux(self) -> None:
        """Ensure this process is running on Linux."""

        if self.platform_system().lower() != "linux":
            raise PlatformError("macchanger_pro only supports Linux hosts.")

    def ensure_root(self) -> None:
        """Ensure the effective user id is root."""

        if self.geteuid is None:
            raise PrivilegeError("Root privilege checks are unavailable on this platform.")
        if self.geteuid() != 0:
            raise PrivilegeError("This operation requires root privileges. Re-run with sudo.")

    def command_exists(self, command: str) -> bool:
        """Return whether a command is available in PATH."""

        return self.which(command) is not None

    def run_command(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        """Run a command and normalize failures to ``OperationError``."""

        try:
            return self.runner.run(args)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            joined = " ".join(args)
            raise OperationError(f"Command failed: {joined}. {detail}") from exc
        except OSError as exc:
            joined = " ".join(args)
            raise OperationError(f"Unable to execute command: {joined}. {exc}") from exc

    def list_interfaces(self) -> list[str]:
        """List non-loopback interfaces using sysfs with ``ip`` fallback."""

        if self.sys_class_net.exists():
            interfaces = sorted(
                entry.name
                for entry in self.sys_class_net.iterdir()
                if entry.is_dir() and entry.name != "lo"
            )
            if interfaces:
                return interfaces

        if not self.command_exists("ip"):
            return []

        output = self.run_command(["ip", "-o", "link", "show"]).stdout
        discovered: list[str] = []
        for line in output.splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            raw_name = parts[1].strip()
            name = raw_name.split("@", maxsplit=1)[0]
            if name and name != "lo" and name not in discovered:
                discovered.append(name)
        return discovered

    def interface_exists(self, interface: str) -> bool:
        """Return whether an interface exists on the host."""

        return interface in self.list_interfaces()

    def read_interface_mac(self, interface: str) -> str | None:
        """Read the current interface MAC from sysfs when available."""

        address_file = self.sys_class_net / interface / "address"
        try:
            return address_file.read_text(encoding="utf-8").strip().lower()
        except OSError:
            return None

    def ensure_backup_dir(self) -> None:
        """Ensure backup directory exists with root-only directory permissions."""

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.chmod(0o700)
            current_mode = stat.S_IMODE(self.backup_dir.stat().st_mode)
            if current_mode != 0o700:
                self.backup_dir.chmod(0o700)
        except OSError as exc:
            raise BackupError(
                f"Unable to create or secure backup directory {self.backup_dir}: {exc}"
            ) from exc

    def backup_file(self, interface: str) -> Path:
        """Return backup path for a specific interface."""

        return self.backup_dir / f"{interface}.orig"

    def read_backup_mac(self, interface: str) -> str | None:
        """Read a backed-up MAC, if one exists."""

        file_path = self.backup_file(interface)
        if not file_path.exists():
            return None
        try:
            return file_path.read_text(encoding="utf-8").strip().lower()
        except OSError as exc:
            raise BackupError(f"Unable to read backup file {file_path}: {exc}") from exc

    def write_backup_mac_if_missing(self, interface: str, current_mac: str) -> Path:
        """Persist original MAC using an atomic write when backup is absent."""

        self.ensure_backup_dir()
        file_path = self.backup_file(interface)
        if file_path.exists():
            return file_path

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.backup_dir,
                prefix=f"{interface}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(current_mac + "\n")
                temporary_path = Path(handle.name)

            os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, file_path)
            file_path.chmod(0o600)
        except OSError as exc:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink(missing_ok=True)
            raise BackupError(f"Unable to persist backup for interface {interface}: {exc}") from exc
        return file_path
