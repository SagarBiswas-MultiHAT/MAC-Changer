"""Validation unit tests."""

from __future__ import annotations

from macchanger_pro.core import normalize_mac, validate_interface_name, validate_mac


def test_validate_mac_accepts_canonical_value() -> None:
    assert validate_mac("aa:bb:cc:dd:ee:ff")


def test_validate_mac_rejects_invalid_values() -> None:
    assert not validate_mac("gg:bb:cc:dd:ee:ff")
    assert not validate_mac("aa-bb-cc-dd-ee-ff")
    assert not validate_mac("aa:bb:cc:dd:ee")


def test_normalize_mac_returns_lowercase_trimmed_value() -> None:
    assert normalize_mac(" AA:BB:CC:DD:EE:FF ") == "aa:bb:cc:dd:ee:ff"


def test_validate_interface_name_enforces_expected_pattern() -> None:
    assert validate_interface_name("eth0")
    assert validate_interface_name("wlan0.100")
    assert not validate_interface_name("../../etc/passwd")
    assert not validate_interface_name("name with spaces")
