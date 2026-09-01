"""Command-line interface for macchanger_pro."""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Callable, Sequence

from .core import (
    MacChangerService,
    generate_locally_administered_unicast_mac,
    normalize_mac,
    validate_mac,
)
from .errors import BackupError, OperationError, PlatformError, PrivilegeError, ValidationError
from .system import SystemContext

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

EXIT_OK = 0
EXIT_INTERRUPTED = 1
EXIT_PLATFORM = 2
EXIT_PRIVILEGE = 3
EXIT_VALIDATION = 4
EXIT_OPERATION = 5
EXIT_ABORTED = 6


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(description="macchanger_pro: safe, production-ready MAC tool")
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--set",
        "-s",
        metavar="MAC",
        help="Set the MAC address to MAC (format: aa:bb:cc:dd:ee:ff)",
    )
    action_group.add_argument(
        "--random",
        "-r",
        action="store_true",
        help="Set a locally-administered random MAC",
    )
    action_group.add_argument(
        "--restore",
        "-R",
        action="store_true",
        help="Restore previously backed-up original MAC",
    )
    parser.add_argument(
        "--interface",
        "-i",
        metavar="IFACE",
        help="Network interface (e.g. wlan0). If omitted, prompt or auto-select.",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List non-loopback interfaces and MACs",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current MAC for the selected interface",
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Automatic yes to prompts")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser


def configure_logging(debug: bool) -> logging.Logger:
    """Configure logger with environment override support."""

    configured_level = os.environ.get("MACCHANGER_LOG_LEVEL", "INFO").strip().upper()
    level = logging.DEBUG if debug else getattr(logging, configured_level, logging.INFO)
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)
    return logging.getLogger("macchanger_pro")


def choose_interface(
    service: MacChangerService,
    cli_interface: str | None,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> str:
    """Return a validated interface from CLI or interactive prompt."""

    if cli_interface:
        return service.resolve_interface(cli_interface)

    interfaces = service.system.list_interfaces()
    if not interfaces:
        raise OperationError("No non-loopback interfaces found.")

    if len(interfaces) == 1:
        return interfaces[0]

    output_fn("Available interfaces:")
    for index, interface in enumerate(interfaces, start=1):
        mac = service.system.read_interface_mac(interface) or "unknown"
        output_fn(f"  {index}. {interface} (MAC: {mac})")

    while True:
        try:
            selected = input_fn("Select interface by number: ").strip()
        except EOFError as exc:
            raise OperationError("No selection received.") from exc
        try:
            index = int(selected)
        except ValueError:
            output_fn("Invalid selection. Try again.")
            continue
        if 1 <= index <= len(interfaces):
            return interfaces[index - 1]
        output_fn("Invalid selection. Try again.")


def confirm(prompt: str, assume_yes: bool, input_fn: Callable[[str], str]) -> bool:
    """Prompt for yes/no confirmation unless ``assume_yes`` is set."""

    if assume_yes:
        return True
    response = input_fn(prompt).strip().lower()
    return response in {"y", "yes"}


def handle_list(service: MacChangerService, output_fn: Callable[[str], None]) -> None:
    """List interfaces and current MAC addresses."""

    result = service.list_interfaces_with_macs()
    if not result.interfaces:
        output_fn("No non-loopback interfaces found.")
        return
    output_fn("Interfaces and MACs:")
    for item in result.interfaces:
        output_fn(f"  {item.interface}: {item.mac or 'unknown'}")


def handle_show(
    service: MacChangerService,
    interface: str,
    output_fn: Callable[[str], None],
) -> None:
    """Display current MAC for one interface."""

    result = service.show_mac(interface)
    output_fn(f"{result.interface} current MAC: {result.mac or 'unknown'}")


def handle_restore(
    service: MacChangerService,
    interface: str,
    yes: bool,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> int:
    """Restore backed-up MAC address for an interface."""

    if not confirm(f"Restore original MAC for {interface}? [y/N]: ", yes, input_fn):
        output_fn("Aborted.")
        return EXIT_ABORTED
    result = service.restore_mac(interface)
    output_fn(f"Restored original MAC for {result.interface}. Current: {result.mac or 'unknown'}")
    return EXIT_OK


def handle_set_or_random(
    service: MacChangerService,
    interface: str,
    args: argparse.Namespace,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> int:
    """Set MAC from explicit value, random generation, or interactive flow."""

    if args.random:
        target_mac = generate_locally_administered_unicast_mac()
    elif args.set:
        target_mac = args.set
    else:
        current = service.system.read_interface_mac(interface) or "unknown"
        output_fn(f"Selected interface: {interface} (current MAC: {current})")
        choice = input_fn(
            "Enter new MAC (or 'random' to generate, 'restore' to restore original): "
        ).strip()
        lowered_choice = choice.lower()
        if lowered_choice == "random":
            target_mac = generate_locally_administered_unicast_mac()
        elif lowered_choice == "restore":
            result = service.restore_mac(interface)
            output_fn(
                f"Restored original MAC for {result.interface}. Current: {result.mac or 'unknown'}"
            )
            return EXIT_OK
        else:
            target_mac = choice

    if not validate_mac(target_mac):
        raise ValidationError(f"Invalid MAC format: {target_mac}")
    normalized_target = normalize_mac(target_mac)

    if not confirm(
        f"Apply MAC {normalized_target} to interface {interface}? [y/N]: ",
        args.yes,
        input_fn,
    ):
        output_fn("Aborted.")
        return EXIT_ABORTED

    result = service.set_mac(interface, normalized_target)
    output_fn(
        f"MAC successfully changed for {result.interface}. "
        f"New MAC: {result.mac or normalized_target}"
    )
    service.logger.info("Operation completed.")
    return EXIT_OK


def run(
    argv: Sequence[str] | None = None,
    *,
    context: SystemContext | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    """Run CLI and return process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    logger = configure_logging(args.debug)
    system = context or SystemContext()
    service = MacChangerService(system=system, logger=logger)

    try:
        system.ensure_linux()

        if args.list:
            handle_list(service, output_fn)
            return EXIT_OK

        interface = choose_interface(service, args.interface, input_fn, output_fn)

        if args.show:
            handle_show(service, interface, output_fn)
            return EXIT_OK

        if args.restore:
            system.ensure_root()
            return handle_restore(service, interface, args.yes, input_fn, output_fn)

        system.ensure_root()
        return handle_set_or_random(service, interface, args, input_fn, output_fn)
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting.")
        return EXIT_INTERRUPTED
    except PlatformError as exc:
        logger.error("%s", exc)
        return EXIT_PLATFORM
    except PrivilegeError as exc:
        logger.error("%s", exc)
        return EXIT_PRIVILEGE
    except ValidationError as exc:
        logger.error("%s", exc)
        return EXIT_VALIDATION
    except (BackupError, OperationError) as exc:
        logger.error("%s", exc)
        return EXIT_OPERATION


def entrypoint() -> None:
    """Set process exit code for console script invocation."""

    raise SystemExit(run())


if __name__ == "__main__":
    entrypoint()
