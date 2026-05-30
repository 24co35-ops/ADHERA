from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.responses import ErrorResponse, ErrorDetail

def create_error_response(status_code: int, code: str, message: str, field: str = None) -> JSONResponse:
    content = ErrorResponse(
        error=ErrorDetail(code=code, message=message, field=field)
    ).model_dump(exclude_none=True)
    return JSONResponse(status_code=status_code, content=content)

async def global_exception_handler(request: Request, exc: Exception):
    return create_error_response(500, "SERVICE_UNAVAILABLE", "An unexpected error occurred.")
