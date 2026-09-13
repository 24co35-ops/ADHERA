import logging
from typing import Any, Optional

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError

from app.core.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger("adhera.core.exceptions")


def is_timeout_error(exc: Exception) -> bool:
    """Check if exception represents a database or network timeout."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout)):
        return True
    err_str = str(exc).lower()
    return (
        "gateway timeout" in err_str
        or "504" in err_str
        or "timed out" in err_str
        or "timeout" in err_str
        or "query_timeout" in err_str
        or "statement timeout" in err_str
        or "canceling statement due to statement timeout" in err_str
    )


def is_db_unavailable_error(exc: Exception) -> bool:
    """Check if exception represents a database connection failure or 503/502 error."""
    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
        return True
    err_str = str(exc).lower()
    return (
        "service unavailable" in err_str
        or "503" in err_str
        or "502" in err_str
        or "bad gateway" in err_str
        or "connection refused" in err_str
    )


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


async def postgrest_exception_handler(request: Request, exc: APIError) -> JSONResponse:
    logger.error("PostgREST APIError on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    if is_timeout_error(exc):
        return create_error_response(504, "GATEWAY_TIMEOUT", "Database query timed out. Please try again.")
    if is_db_unavailable_error(exc):
        return create_error_response(503, "SERVICE_UNAVAILABLE", "Database service temporarily unavailable. Please try again.")
    return create_error_response(503, "SERVICE_UNAVAILABLE", f"Database error: {getattr(exc, 'message', str(exc))}")


async def timeout_exception_handler(request: Request, exc: httpx.TimeoutException) -> JSONResponse:
    logger.error("HTTP/Database timeout on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return create_error_response(504, "GATEWAY_TIMEOUT", "Database query timed out. Please try again.")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    if is_timeout_error(exc):
        return create_error_response(504, "GATEWAY_TIMEOUT", "Database query timed out. Please try again.")
    if is_db_unavailable_error(exc):
        return create_error_response(503, "SERVICE_UNAVAILABLE", "Database service temporarily unavailable. Please try again.")
    return create_error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred.")

