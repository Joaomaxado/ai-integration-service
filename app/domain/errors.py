from datetime import datetime, timezone

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.schemas import ErrorResponse


def error_body(
    http_status: int,
    code: str,
    message: str,
    details: str | list | dict | None = None,
) -> dict:
    return ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=http_status,
        code=code,
        message=message,
        details=details,
    ).model_dump(mode="json")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_body(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
            "Os dados fornecidos são inválidos.",
            exc.errors(),
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_by_status = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        503: "SERVICE_UNAVAILABLE",
    }
    message = exc.detail if isinstance(exc.detail, str) else "Erro ao processar a requisição."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(
            exc.status_code,
            code_by_status.get(exc.status_code, "HTTP_ERROR"),
            message,
        ),
    )
