"""Domain errors for macchanger_pro."""

from __future__ import annotations


class MacChangerError(Exception):
    """Base class for all domain-specific errors."""


class PlatformError(MacChangerError):
    """Raised when the current operating system is unsupported."""


class PrivilegeError(MacChangerError):
    """Raised when an operation requires elevated privileges."""


class ValidationError(MacChangerError):
    """Raised when user input fails validation."""


class OperationError(MacChangerError):
    """Raised when a command or system operation fails."""


class BackupError(MacChangerError):
    """Raised when backup read/write operations fail."""
