"""Interface discovery and sysfs parsing tests."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from macchanger_pro.system import SystemContext


@dataclass
class StaticRunner:
    """Runner that always returns static stdout."""

    stdout: str = ""

    def run(self, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=list(args),
            returncode=0,
            stdout=self.stdout,
            stderr="",
        )


def test_list_interfaces_from_sysfs(tmp_path: Path) -> None:
    net_root = tmp_path / "sys" / "class" / "net"
    (net_root / "lo").mkdir(parents=True)
    (net_root / "eth0").mkdir(parents=True)
    (net_root / "wlan0").mkdir(parents=True)
    (net_root / "eth0" / "address").write_text("00:11:22:33:44:55\n", encoding="utf-8")

    context = SystemContext(
        runner=StaticRunner(),
        sys_class_net=net_root,
        which=lambda _: None,
    )

    assert context.list_interfaces() == ["eth0", "wlan0"]
    assert context.read_interface_mac("eth0") == "00:11:22:33:44:55"


def test_list_interfaces_falls_back_to_ip_output(tmp_path: Path) -> None:
    missing_sysfs = tmp_path / "missing"
    output = "\n".join(
        [
            "1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default",
            "2: eth0@if3: <BROADCAST> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default",
            "3: wlan0: <BROADCAST> mtu 1500 qdisc mq state UP mode DORMANT group default",
        ]
    )
    context = SystemContext(
        runner=StaticRunner(stdout=output),
        sys_class_net=missing_sysfs,
        which=lambda command: "/usr/sbin/ip" if command == "ip" else None,
    )

    assert context.list_interfaces() == ["eth0", "wlan0"]
