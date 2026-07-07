from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


ERROR_CODES = {
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    422: 'validation_error',
    429: 'rate_limited',
    500: 'internal_error',
    502: 'provider_error',
    503: 'service_unavailable',
}


def error_response(
    request: Request,
    status_code: int,
    message: str,
    code: str | None = None,
    details: Any | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        'error': {
            'code': code or ERROR_CODES.get(status_code, 'api_error'),
            'message': message,
            'status_code': status_code,
            'request_id': getattr(request.state, 'request_id', None),
        }
    }
    if details is not None:
        body['error']['details'] = details
    return JSONResponse(status_code=status_code, content=body)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = str(exc.detail) if exc.detail else ERROR_CODES.get(exc.status_code, 'API error')
    return error_response(request, status_code=exc.status_code, message=message)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request,
        status_code=422,
        message='Request validation failed',
        code='validation_error',
        details=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        request,
        status_code=500,
        message='Unexpected server error',
        code='internal_error',
    )
