"""Platform and privilege guard tests."""

from __future__ import annotations

from conftest import FakeSystemContext
from macchanger_pro.cli import EXIT_PLATFORM, EXIT_PRIVILEGE, run


def test_non_linux_returns_platform_exit_code(fake_system: FakeSystemContext) -> None:
    fake_system.linux = False

    exit_code = run(
        ["--list"],
        context=fake_system,
        input_fn=lambda _: "",
        output_fn=lambda _: None,
    )

    assert exit_code == EXIT_PLATFORM


def test_non_root_set_operation_returns_privilege_exit_code(fake_system: FakeSystemContext) -> None:
    fake_system.root = False

    exit_code = run(
        ["-i", "eth0", "--set", "aa:bb:cc:dd:ee:ff", "--yes"],
        context=fake_system,
        input_fn=lambda _: "",
        output_fn=lambda _: None,
    )

    assert exit_code == EXIT_PRIVILEGE
