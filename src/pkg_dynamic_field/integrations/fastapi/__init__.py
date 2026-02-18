from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from starlette.responses import JSONResponse

from ...domain.exceptions import FieldSchemaNotFoundError, FieldValidationError


def install_field_error_handlers(app: FastAPI) -> None:
    """Install exception handlers for field-related domain errors."""

    @app.exception_handler(FieldSchemaNotFoundError)
    async def field_schema_not_found_handler(request: Request, exc: FieldSchemaNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Field validation failed",
                "errors": [
                    {"path": e.path, "message": e.message, "code": e.code}
                    for e in exc.errors
                ],
            },
        )


__all__ = [
    "install_field_error_handlers",
]
