"""macchanger_pro package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .cli import run

try:
    __version__ = version("macchanger-pro")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__", "run"]
