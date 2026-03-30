from exceptions.base import QuantSystemError


class DataUnavailableError(QuantSystemError, FileNotFoundError):
    """Raised when required data files or data assets are unavailable."""


class SchemaValidationError(QuantSystemError, ValueError):
    """Raised when data schema or required fields do not match expectations."""


class CacheCorruptionError(QuantSystemError, ValueError):
    """Raised when cache content is unreadable or inconsistent."""
