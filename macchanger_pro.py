#!/usr/bin/env python3
"""Backward-compatible script wrapper for the packaged CLI."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

if __name__ == "__main__":
    from macchanger_pro.cli import entrypoint

    entrypoint()
