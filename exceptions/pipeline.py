from exceptions.base import QuantSystemError


class PipelineExecutionError(QuantSystemError, ValueError):
    """Raised when a pipeline cannot continue due to invalid runtime state."""
