"""Package entrypoint tests."""

from __future__ import annotations

import runpy

import pytest


def test_package_main_invokes_cli_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    import macchanger_pro.cli as cli_module

    def fake_entrypoint() -> None:
        raise SystemExit(0)

    monkeypatch.setattr(cli_module, "entrypoint", fake_entrypoint)

    with pytest.raises(SystemExit) as exc:
        runpy.run_module("macchanger_pro.__main__", run_name="__main__")

    assert exc.value.code == 0
