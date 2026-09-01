"""Additional CLI path coverage tests."""

from __future__ import annotations

import pytest

from conftest import FakeSystemContext
from macchanger_pro.cli import (
    EXIT_ABORTED,
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_OPERATION,
    choose_interface,
    handle_list,
    run,
)
from macchanger_pro.core import MacChangerService
from macchanger_pro.errors import OperationError


def _input_from(values: list[str]):
    iterator = iter(values)

    def _reader(_: str) -> str:
        return next(iterator)

    return _reader


def test_choose_interface_interactive_path(fake_system: FakeSystemContext) -> None:
    fake_system.interfaces = {
        "eth0": "00:11:22:33:44:55",
        "wlan0": "66:77:88:99:aa:bb",
    }
    service = MacChangerService(system=fake_system)
    output: list[str] = []

    selected = choose_interface(
        service=service,
        cli_interface=None,
        input_fn=_input_from(["x", "3", "2"]),
        output_fn=output.append,
    )

    assert selected == "wlan0"
    assert output[0] == "Available interfaces:"
    assert output.count("Invalid selection. Try again.") == 2


def test_choose_interface_raises_when_no_interfaces(fake_system: FakeSystemContext) -> None:
    fake_system.interfaces = {}
    service = MacChangerService(system=fake_system)

    with pytest.raises(OperationError):
        choose_interface(service, None, input_fn=lambda _: "", output_fn=lambda _: None)


def test_handle_list_outputs_empty_message(fake_system: FakeSystemContext) -> None:
    fake_system.interfaces = {}
    service = MacChangerService(system=fake_system)
    output: list[str] = []

    handle_list(service, output.append)

    assert output == ["No non-loopback interfaces found."]


def test_run_list_returns_success(fake_system: FakeSystemContext) -> None:
    output: list[str] = []
    exit_code = run(["--list"], context=fake_system, input_fn=lambda _: "", output_fn=output.append)

    assert exit_code == EXIT_OK
    assert output[0] == "Interfaces and MACs:"


def test_run_returns_operation_error_for_show_without_interfaces() -> None:
    context = FakeSystemContext(interfaces={})
    exit_code = run(
        ["--show"],
        context=context,
        input_fn=lambda _: "",
        output_fn=lambda _: None,
    )

    assert exit_code == EXIT_OPERATION


def test_run_handles_keyboard_interrupt(
    fake_system: FakeSystemContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    import macchanger_pro.cli as cli_module

    def interrupting_choose_interface(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_module, "choose_interface", interrupting_choose_interface)
    exit_code = run(
        ["--show"],
        context=fake_system,
        input_fn=lambda _: "",
        output_fn=lambda _: None,
    )

    assert exit_code == EXIT_INTERRUPTED


def test_restore_success_path(fake_system: FakeSystemContext) -> None:
    fake_system.backups["eth0"] = "de:ad:be:ef:00:01"
    output: list[str] = []

    exit_code = run(
        ["-i", "eth0", "--restore", "--yes"],
        context=fake_system,
        input_fn=lambda _: "",
        output_fn=output.append,
    )

    assert exit_code == EXIT_OK
    assert any("Restored original MAC" in line for line in output)


def test_random_operation_can_be_aborted(fake_system: FakeSystemContext) -> None:
    output: list[str] = []

    exit_code = run(
        ["-i", "eth0", "--random"],
        context=fake_system,
        input_fn=lambda _: "n",
        output_fn=output.append,
    )

    assert exit_code == EXIT_ABORTED
    assert output[-1] == "Aborted."


def test_interactive_set_custom_mac_path(fake_system: FakeSystemContext) -> None:
    output: list[str] = []
    exit_code = run(
        ["-i", "eth0"],
        context=fake_system,
        input_fn=_input_from(["aa:bb:cc:dd:ee:ff", "y"]),
        output_fn=output.append,
    )

    assert exit_code == EXIT_OK
    assert fake_system.interfaces["eth0"] == "aa:bb:cc:dd:ee:ff"
