from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.responses import ErrorDetail, ErrorResponse


def create_error_response(
    status_code: int,
    code: str,
    message: str,
    field: Optional[str] = None,
    details: Optional[list[dict[str, Any]]] = None,
) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorDetail(code=code, message=message, field=field, details=details)
    ).model_dump(exclude_none=True)
    return JSONResponse(status_code=status_code, content=content)

async def global_exception_handler(request: Request, exc: Exception):
    return create_error_response(500, "SERVICE_UNAVAILABLE", "An unexpected error occurred.")
