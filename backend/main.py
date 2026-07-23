import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import get_settings
from core.errors import (
    DialectaError,
    dialecta_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from core.limiter import limiter
from core.middleware import RequestLoggingMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routers import auth, debate, reports, admin

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("dialecta")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DIALECTA backend starting — environment: %s", settings.ENVIRONMENT)
    logger.info("CORS allowed origin: %s", settings.FRONTEND_URL)
    yield
    logger.info("DIALECTA backend shutting down")


app = FastAPI(
    title="DIALECTA",
    description="Multi-agent AI debate system",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

app.add_exception_handler(DialectaError, dialecta_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(auth.router)
app.include_router(debate.router)
app.include_router(reports.router)
app.include_router(admin.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}