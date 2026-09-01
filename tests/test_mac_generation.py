"""Random MAC generation tests."""

from __future__ import annotations

from macchanger_pro.core import generate_locally_administered_unicast_mac, validate_mac


def test_generated_mac_is_valid_and_has_expected_bits() -> None:
    mac = generate_locally_administered_unicast_mac()
    assert validate_mac(mac)

    first_octet = int(mac.split(":")[0], 16)
    assert first_octet & 0b00000010  # locally administered bit set
    assert (first_octet & 0b00000001) == 0  # multicast bit cleared


def test_generation_can_be_deterministic_for_tests() -> None:
    values = iter([0xFF, 0x01, 0x02, 0x03, 0x04, 0x05])

    def fake_randint(_: int, __: int) -> int:
        return next(values)

    mac = generate_locally_administered_unicast_mac(randint=fake_randint)
    assert mac == "fe:01:02:03:04:05"
