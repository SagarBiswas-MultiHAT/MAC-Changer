# MAC-Changer_Pro

Linux MAC address management with safe backup/restore, strict validation, and automation-ready CLI behavior.

<div align="right">

[![CI](https://github.com/SagarBiswas-MultiHAT/MAC-Changer_Pro/actions/workflows/ci.yml/badge.svg)](https://github.com/SagarBiswas-MultiHAT/MAC-Changer_Pro/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/badge/pypi-v2.0.0-blue.svg)](https://pypi.org/project/MAC-Changer_Pro/)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](tests/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/type_checked-mypy_strict-blue.svg)](https://mypy-lang.org/)
[![Security: pip-audit](https://img.shields.io/badge/security-pip--audit%20clean-success.svg)](SECURITY.md)

</div>

## Overview

`MAC-Changer_Pro` is a production-focused CLI utility for working with Linux interface MAC addresses safely.  
It lets you inspect, set, randomize, and restore MAC addresses while preserving original values in a protected backup directory.

This project is for engineers, students, and security practitioners who need predictable networking behavior in labs or authorized administration workflows.  
The CLI is designed for both interactive use and script automation, with clear errors, stable exit codes, and a testable architecture.

### Output/Testing

```
┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro --list
Interfaces and MACs:
  eth0: 00:15:5d:45:60:8f

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --show
eth0 current MAC: 00:15:5d:45:60:8f

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --set aa:bb:cc:dd:ee:ff
Apply MAC aa:bb:cc:dd:ee:ff to interface eth0? [y/N]: Y
2026-02-24 23:01:12,739 [INFO] Setting MAC for eth0 -> aa:bb:cc:dd:ee:ff
MAC successfully changed for eth0. New MAC: aa:bb:cc:dd:ee:ff
2026-02-24 23:01:12,860 [INFO] Operation completed.

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --show
eth0 current MAC: aa:bb:cc:dd:ee:ff

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --random
Apply MAC 56:7a:46:19:fc:bc to interface eth0? [y/N]: Y
2026-02-24 23:01:29,282 [INFO] Setting MAC for eth0 -> 56:7a:46:19:fc:bc
MAC successfully changed for eth0. New MAC: 56:7a:46:19:fc:bc
2026-02-24 23:01:29,314 [INFO] Operation completed.

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --show
eth0 current MAC: 56:7a:46:19:fc:bc

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --restore
Restore original MAC for eth0? [y/N]: y
2026-02-24 23:01:41,304 [INFO] Restoring MAC for eth0 -> 00:15:5d:45:60:8f
Restored original MAC for eth0. Current: 00:15:5d:45:60:8f

┌──(.venv)(root㉿HP-SAGAR)-[/mnt/h/updatedReposV1/updatedReposV2/MacChanger-V1-Max]      
└─# MAC-Changer_Pro -i eth0 --show
eth0 current MAC: 00:15:5d:45:60:8f
```


## Features

- Dynamic interface discovery (`/sys/class/net` with `ip` fallback)
- Strict MAC address validation
- Standards-correct random MAC generation (locally administered + unicast)
- Automatic original MAC backup before first mutation
- Safe restore flow from stored backup
- `iproute2` first, `ifconfig` fallback for legacy environments
- Stable, explicit exit codes for platform, privilege, validation, and operation errors
- Console script (`MAC-Changer_Pro`) plus compatibility wrapper (`macchanger_pro.py`)

## Demo / Screenshots

Screenshots coming soon.

## Quick Start

### Prerequisites

- Linux host (Ubuntu/Debian/Kali tested)
- Python 3.10 or newer
- `ip` command from `iproute2`
- Root privileges (`sudo`) for MAC-changing operations

### Installation

```bash
git clone https://github.com/SagarBiswas-MultiHAT/MacChanger-V1-MAX.git
cd MacChanger-V1-MAX
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Run the Project

```bash
MAC-Changer_Pro --help
```

You should see usage text with flags such as `--set`, `--random`, `--restore`, `--list`, and `--show`.

## Usage Examples

### 1) List available interfaces

```bash
MAC-Changer_Pro --list
```

Prints non-loopback interfaces and their current MAC addresses.

### 2) Show MAC for one interface

```bash
MAC-Changer_Pro -i eth0 --show
```

Shows the current MAC without modifying the interface.

### 3) Set an explicit MAC

```bash
MAC-Changer_Pro -i eth0 --set aa:bb:cc:dd:ee:ff
```

Validates format, writes a one-time backup of the original MAC, then applies the new address.

### 4) Apply a random standards-correct MAC

```bash
MAC-Changer_Pro -i eth0 --random
```

Generates and applies a locally administered unicast MAC suitable for privacy/lab workflows.

### 5) Restore the original hardware MAC

```bash
MAC-Changer_Pro -i eth0 --restore
```

Loads the saved backup and re-applies it.

### 6) Compatibility wrapper

```bash
python macchanger_pro.py --help
```

The top-level script remains available for existing workflows.

### 7) If `sudo MAC-Changer_Pro` says "command not found"

Some Linux environments reset `PATH` under `sudo`, so virtualenv-installed commands are not visible.

Use one of these options:

```bash
# Option A: run as root shell (no sudo prefix needed)
MAC-Changer_Pro -i eth0 --random

# Option B: sudo with absolute command path
sudo "$(command -v MAC-Changer_Pro)" -i eth0 --random

# Option C: compatibility wrapper
sudo python macchanger_pro.py -i eth0 --random
```

## Project Structure

```text
MacChanger-V1-MAX/
|-- .github/
|   |-- workflows/ci.yml                # CI pipeline: lint -> test -> build -> audit
|   |-- ISSUE_TEMPLATE/                 # Bug/feature templates
|   |-- PULL_REQUEST_TEMPLATE.md        # PR checklist
|   `-- dependabot.yml                  # Automated dependency updates
|-- src/macchanger_pro/
|   |-- __init__.py                     # Package exports and version resolution
|   |-- __main__.py                     # python -m macchanger_pro entrypoint
|   |-- cli.py                          # Argument parsing and user interaction
|   |-- core.py                         # Domain logic and orchestration
|   |-- system.py                       # OS/command/filesystem adapters
|   `-- errors.py                       # Custom exception taxonomy
|-- tests/                              # Unit and integration-style tests
|-- docs/audit-phase1.md                # Baseline audit report
|-- macchanger_pro.py                   # Backward-compatible wrapper script
|-- pyproject.toml                      # Packaging, lint, test, and typing config
|-- Makefile                            # Common development commands
|-- Dockerfile                          # Reproducible containerized runtime/tooling
|-- SECURITY.md                         # Vulnerability reporting policy
|-- CONTRIBUTING.md                     # Contribution guidelines
|-- CODE_OF_CONDUCT.md                  # Community conduct expectations
|-- CHANGELOG.md                        # Versioned change history
`-- LICENSE                             # MIT license
```

## Running Tests

```bash
make test
```

Coverage report with threshold enforcement:

```bash
make coverage
```

Direct pytest invocation:

```bash
python -m pytest
```

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) for setup, standards, and PR expectations.

## Roadmap

- [ ] Add optional persistence integrations for NetworkManager profiles
- [ ] Add structured JSON output mode for automation pipelines
- [ ] Add integration tests for containerized Linux network namespaces
- [ ] Publish release artifacts to PyPI
- [ ] Add shell completion scripts (bash/zsh/fish)

## License

Released under the [MIT License](LICENSE).

## Acknowledgments

- Linux `iproute2` maintainers for modern interface control tooling
- Python and pytest communities for reliable CLI/testing foundations
- Security training communities that advocate authorized, ethical lab usage
