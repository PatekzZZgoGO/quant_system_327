from exceptions.base import QuantSystemError


class ConfigurationError(QuantSystemError, ValueError):
    """Raised when configuration is missing or invalid."""
