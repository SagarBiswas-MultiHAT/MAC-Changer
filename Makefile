PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev lint test coverage build audit run-help

install-dev:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=src/macchanger_pro --cov-report=term-missing --cov-report=xml --cov-fail-under=80

build:
	$(PYTHON) -m build

audit:
	$(PYTHON) -m pip_audit -r requirements-audit.txt

run-help:
	$(PYTHON) macchanger_pro.py --help
