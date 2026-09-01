# Contributing Guide

Thanks for contributing to `macchanger-pro`.

## Prerequisites

- Python 3.10+
- Linux for privileged runtime validation
- `iproute2` (for real MAC operations)

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Development Workflow

1. Create a branch from `main`.
2. Make focused changes with tests.
3. Run local checks:

```bash
make lint
make test
make build
make audit
```

4. Open a pull request using the provided template.

## Code Standards

- Keep CLI behavior backward compatible unless discussed in an issue.
- Add type hints for all new production code.
- Add tests for bug fixes and new features.
- Avoid shell interpolation in subprocess calls; pass argument lists.

## Commit Message Style

Use concise, imperative subject lines, for example:

- `feat: add linux platform guard`
- `fix: normalize fallback interface parsing`
- `test: cover missing backup restore path`

## Pull Request Expectations

- Explain what changed and why.
- Reference related issues.
- Include terminal output for `make lint` and `make test`.
- Update documentation and changelog when behavior changes.

