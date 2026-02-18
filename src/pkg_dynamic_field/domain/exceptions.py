from __future__ import annotations


class FieldError:
    """Data carrier for a single field validation failure (not an Exception)."""

    def __init__(self, path: str, message: str, code: str = "invalid"):
        self.path = path
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        return f"FieldError(path={self.path!r}, message={self.message!r}, code={self.code!r})"


class FieldSchemaNotFoundError(Exception):
    """Raised when no field schema exists for a given kind."""

    def __init__(self, kind: str):
        self.kind = kind
        super().__init__(f"No field schema found for kind '{kind}'")


class FieldValidationError(Exception):
    """Raised when field values fail validation against their schema."""

    def __init__(self, errors: list):
        self.errors = errors
        super().__init__(f"Field validation failed with {len(errors)} error(s)")
