"""Core domain logic for MAC operations."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from random import SystemRandom

from .errors import BackupError, OperationError, ValidationError
from .system import SystemContext

MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
INTERFACE_REGEX = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
_RANDOM = SystemRandom()


@dataclass(frozen=True, slots=True)
class InterfaceMac:
    """Pair of interface name and current MAC address."""

    interface: str
    mac: str | None


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Structured response from core operations."""

    action: str
    interface: str | None = None
    mac: str | None = None
    previous_mac: str | None = None
    interfaces: tuple[InterfaceMac, ...] = ()


def validate_mac(mac: str) -> bool:
    """Return whether ``mac`` is in canonical hexadecimal MAC format."""

    return bool(MAC_REGEX.fullmatch(mac.strip()))


def normalize_mac(mac: str) -> str:
    """Normalize a user-provided MAC to lowercase canonical form."""

    return mac.strip().lower()


def validate_interface_name(interface: str) -> bool:
    """Return whether an interface name is syntactically valid."""

    return bool(INTERFACE_REGEX.fullmatch(interface.strip()))


def generate_locally_administered_unicast_mac(
    randint: Callable[[int, int], int] | None = None,
) -> str:
    """
    Generate a locally-administered unicast MAC address.

    Bit semantics:
    - Bit 0 of first octet must be 0 (unicast)
    - Bit 1 of first octet must be 1 (locally administered)
    """

    chooser = randint or _RANDOM.randint
    first_octet = chooser(0, 255)
    first_octet = (first_octet & 0b11111100) | 0b00000010
    octets = [first_octet] + [chooser(0, 255) for _ in range(5)]
    return ":".join(f"{octet:02x}" for octet in octets)


@dataclass(slots=True)
class MacChangerService:
    """High-level interface used by CLI and tests."""

    system: SystemContext
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("macchanger_pro"))

    def resolve_interface(self, interface: str) -> str:
        """Validate and normalize interface existence."""

        candidate = interface.strip()
        if not validate_interface_name(candidate):
            raise ValidationError(f"Invalid interface name: {interface}")

        if not self.system.interface_exists(candidate):
            available = ", ".join(self.system.list_interfaces()) or "none"
            raise ValidationError(f"Interface {candidate} not found. Available: {available}")

        return candidate

    def list_interfaces_with_macs(self) -> OperationResult:
        """Return all discovered interfaces and their current MAC addresses."""

        interfaces = tuple(
            InterfaceMac(interface=name, mac=self.system.read_interface_mac(name))
            for name in self.system.list_interfaces()
        )
        return OperationResult(action="list", interfaces=interfaces)

    def show_mac(self, interface: str) -> OperationResult:
        """Return current MAC for a validated interface."""

        resolved = self.resolve_interface(interface)
        mac = self.system.read_interface_mac(resolved)
        if mac is None:
            raise OperationError(f"Unable to read current MAC for interface {resolved}")
        return OperationResult(action="show", interface=resolved, mac=mac)

    def set_mac(self, interface: str, new_mac: str) -> OperationResult:
        """Set a specific MAC after validation and backup."""

        resolved = self.resolve_interface(interface)
        if not validate_mac(new_mac):
            raise ValidationError(f"Invalid MAC format: {new_mac}")
        normalized = normalize_mac(new_mac)

        previous_mac = self.system.read_interface_mac(resolved)
        if previous_mac is None:
            raise OperationError(f"Cannot read current MAC for interface {resolved}")

        self.system.write_backup_mac_if_missing(resolved, previous_mac)
        self.logger.info("Setting MAC for %s -> %s", resolved, normalized)
        self._apply_mac(resolved, normalized)

        current_mac = self.system.read_interface_mac(resolved) or normalized
        return OperationResult(
            action="set",
            interface=resolved,
            previous_mac=previous_mac,
            mac=current_mac,
        )

    def randomize_mac(self, interface: str) -> OperationResult:
        """Generate and apply a random locally-administered unicast MAC."""

        generated = generate_locally_administered_unicast_mac()
        result = self.set_mac(interface, generated)
        return OperationResult(
            action="random",
            interface=result.interface,
            previous_mac=result.previous_mac,
            mac=result.mac,
        )

    def restore_mac(self, interface: str) -> OperationResult:
        """Restore a previously backed up original MAC."""

        resolved = self.resolve_interface(interface)
        backup_mac = self.system.read_backup_mac(resolved)
        if not backup_mac:
            raise BackupError(
                f"No backup found for interface {resolved} in {self.system.backup_dir}"
            )
        if not validate_mac(backup_mac):
            raise BackupError(f"Backup MAC is invalid for interface {resolved}: {backup_mac}")

        previous_mac = self.system.read_interface_mac(resolved)
        self.logger.info("Restoring MAC for %s -> %s", resolved, backup_mac)
        self._apply_mac(resolved, backup_mac)
        current_mac = self.system.read_interface_mac(resolved) or backup_mac
        return OperationResult(
            action="restore",
            interface=resolved,
            previous_mac=previous_mac,
            mac=current_mac,
        )

    def _apply_mac(self, interface: str, mac: str) -> None:
        """Apply MAC with ``ip`` first and ``ifconfig`` fallback."""

        if self.system.command_exists("ip"):
            commands = [
                ["ip", "link", "set", "dev", interface, "down"],
                ["ip", "link", "set", "dev", interface, "address", mac],
                ["ip", "link", "set", "dev", interface, "up"],
            ]
        elif self.system.command_exists("ifconfig"):
            commands = [
                ["ifconfig", interface, "down"],
                ["ifconfig", interface, "hw", "ether", mac],
                ["ifconfig", interface, "up"],
            ]
        else:
            raise OperationError("No suitable command found. Install iproute2 or net-tools.")

        for command in commands:
            self.system.run_command(command)
