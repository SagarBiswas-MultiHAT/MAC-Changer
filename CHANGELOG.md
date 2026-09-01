# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial CI/CD pipeline with lint, test, build, and dependency audit stages.
- Python package layout under `src/macchanger_pro` with typed modules.
- Backward-compatible wrapper script at repository root.
- Unit and integration-style tests with coverage gating.
- Governance and security documents:
  - `CONTRIBUTING.md`
  - `CODE_OF_CONDUCT.md`
  - `SECURITY.md`
  - `LICENSE`
- Docker, Makefile, Dependabot, issue templates, and PR template.

### Changed

- Rewrote CLI internals to separate concerns across CLI/core/system modules.
- Added explicit Linux platform guard and stable exit code handling.
- Added secure atomic backup file creation and stricter validation.
- Rewrote README for improved onboarding and operational clarity.

## [1.0.0] - 2026-02-24

### Added

- Production-grade project foundation with packaging, testing, and automation.

