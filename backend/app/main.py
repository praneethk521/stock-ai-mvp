from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.routes import router
from app.core.config import get_settings
from app.core.errors import error_response, http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.core.observability import configure_observability, metrics_response, observe_request

settings = get_settings()
configure_observability(settings)
limiter = Limiter(key_func=get_remote_address, default_limits=['120/minute'])

app = FastAPI(
    title=settings.app_name,
    version='0.2.0',
    description='Stock market insights and AI-assisted recommendations. Informational only, not financial advice.',
)
app.state.limiter = limiter


@app.middleware('http')
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get('x-request-id') or str(uuid4())
    request.state.request_id = request_id
    response = await observe_request(
        request,
        call_next,
        metrics_enabled=settings.metrics_enabled,
        route_prefix=settings.api_v1_prefix,
    )
    response.headers['x-request-id'] = request_id
    return response


@app.get('/metrics', include_in_schema=False)
async def metrics() -> Response:
    return metrics_response()


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return error_response(request, status_code=429, message='Rate limit exceeded', code='rate_limited')


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)
app.include_router(router, prefix=settings.api_v1_prefix)
