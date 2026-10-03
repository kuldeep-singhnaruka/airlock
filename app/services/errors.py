class ModelBackendError(Exception):
    """The model provider failed. The API layer turns this into HTTP 502."""


class SchemaMismatchError(Exception):
    """The model returned JSON that still failed Pydantic validation."""


class ToolLoopError(Exception):
    """The model kept calling tools past the configured round limit."""
