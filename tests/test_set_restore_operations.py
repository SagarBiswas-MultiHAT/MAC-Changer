"""Core set/restore operation tests."""

from __future__ import annotations

import pytest

from conftest import FakeSystemContext
from macchanger_pro.core import MacChangerService
from macchanger_pro.errors import BackupError, OperationError


def test_set_mac_prefers_ip_commands(fake_system: FakeSystemContext) -> None:
    service = MacChangerService(system=fake_system)
    result = service.set_mac("eth0", "aa:bb:cc:dd:ee:ff")

    assert result.action == "set"
    assert fake_system.interfaces["eth0"] == "aa:bb:cc:dd:ee:ff"
    assert fake_system.backups["eth0"] == "00:11:22:33:44:55"
    assert fake_system.commands == [
        ["ip", "link", "set", "dev", "eth0", "down"],
        ["ip", "link", "set", "dev", "eth0", "address", "aa:bb:cc:dd:ee:ff"],
        ["ip", "link", "set", "dev", "eth0", "up"],
    ]


def test_set_mac_falls_back_to_ifconfig(fake_system: FakeSystemContext) -> None:
    fake_system.available_commands = {"ifconfig"}
    service = MacChangerService(system=fake_system)

    result = service.set_mac("eth0", "aa:bb:cc:dd:ee:ff")

    assert result.action == "set"
    assert fake_system.interfaces["eth0"] == "aa:bb:cc:dd:ee:ff"
    assert fake_system.commands == [
        ["ifconfig", "eth0", "down"],
        ["ifconfig", "eth0", "hw", "ether", "aa:bb:cc:dd:ee:ff"],
        ["ifconfig", "eth0", "up"],
    ]


def test_set_mac_raises_when_no_supported_command(fake_system: FakeSystemContext) -> None:
    fake_system.available_commands = set()
    service = MacChangerService(system=fake_system)

    with pytest.raises(OperationError):
        service.set_mac("eth0", "aa:bb:cc:dd:ee:ff")


def test_restore_requires_existing_backup(fake_system: FakeSystemContext) -> None:
    service = MacChangerService(system=fake_system)

    with pytest.raises(BackupError):
        service.restore_mac("eth0")


def test_restore_mac_applies_saved_backup(fake_system: FakeSystemContext) -> None:
    fake_system.backups["eth0"] = "de:ad:be:ef:00:01"
    fake_system.interfaces["eth0"] = "aa:bb:cc:dd:ee:ff"
    service = MacChangerService(system=fake_system)

    result = service.restore_mac("eth0")

    assert result.action == "restore"
    assert fake_system.interfaces["eth0"] == "de:ad:be:ef:00:01"


def test_set_mac_propagates_command_failures(fake_system: FakeSystemContext) -> None:
    fake_system.run_fail_on.add(("ip", "link", "set", "dev", "eth0", "down"))
    service = MacChangerService(system=fake_system)

    with pytest.raises(OperationError):
        service.set_mac("eth0", "aa:bb:cc:dd:ee:ff")
