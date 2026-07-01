from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=['120/minute'])

app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    description='Stock market insights and AI-assisted recommendations. Informational only, not financial advice.',
)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={'detail': 'Rate limit exceeded'})

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['Authorization', 'Content-Type'],
)
app.include_router(router, prefix=settings.api_v1_prefix)
