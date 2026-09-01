# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-09-01

### Added

- Python package layout under `src/macchanger_pro` with typed modules: `cli`, `core`, `system`, `errors`.
- `__main__.py` entrypoint enabling `python -m macchanger_pro` invocation.
- Installable via pip/pipx as `macchanger-pro` console script.
- CI/CD pipeline (GitHub Actions) with four gated stages: lint, test (Python 3.10-3.13 matrix), build, and dependency audit.
- Unit and integration-style test suite across 10 test modules with 80% coverage gate enforced.
- `pyproject.toml` with full packaging, Ruff linting, mypy strict typing, and pytest configuration.
- `Makefile` with `test`, `lint`, `format`, `coverage`, and `build` targets.
- `Dockerfile` for containerized runtime and development tooling.
- Dependabot config for automated dependency updates.
- GitHub issue templates (bug report, feature request) and PR template.
- Community governance files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `LICENSE`.
- `.editorconfig`, `.dockerignore`, `.pre-commit-config.yaml`, `.env.example`.
- `docs/audit-phase1.md` baseline audit report.

### Changed

- Rewrote CLI internals to separate concerns across `cli`, `core`, and `system` modules.
- Added Linux platform guard with clean error on non-Linux systems.
- Stable, documented exit codes across all error paths.
- Atomic backup file creation and stricter MAC format validation.
- Backward-compatible wrapper at repository root preserved for existing workflows.
- Rewrote README with updated install instructions, project structure diagram, and usage examples.

## [1.0.0] - 2026-02-24

### Added

- Production-grade project foundation with packaging, testing, and automation.
