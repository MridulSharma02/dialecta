from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("dialecta")


class ErrorCode:
    INVALID_CREDENTIALS = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    TOKEN_INVALID = "AUTH_003"
    EMAIL_NOT_VERIFIED = "AUTH_004"
    INSUFFICIENT_PERMISSIONS = "AUTH_005"
    REFRESH_TOKEN_INVALID = "AUTH_006"

    DEBATE_NOT_FOUND = "DEBATE_001"
    DEBATE_LIMIT_REACHED = "DEBATE_002"
    DEBATE_ALREADY_RUNNING = "DEBATE_003"
    TOPIC_INVALID = "DEBATE_004"
    CHECKPOINT_NOT_FOUND = "DEBATE_005"

    AGENT_DEGRADED = "AGENT_001"
    AGENT_TIMEOUT = "AGENT_002"
    LLM_UNAVAILABLE = "AGENT_003"

    REPORT_NOT_FOUND = "REPORT_001"
    REPORT_GENERATION_FAILED = "REPORT_002"

    VALIDATION_ERROR = "INPUT_001"
    TOPIC_TOO_LONG = "INPUT_002"
    INJECTION_DETECTED = "INPUT_003"

    INTERNAL_ERROR = "SERVER_001"
    NOT_FOUND = "SERVER_002"
    RATE_LIMITED = "SERVER_003"


class DialectaError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(DialectaError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status_code=401)


class PermissionError(DialectaError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(ErrorCode.INSUFFICIENT_PERMISSIONS, message, status_code=403)


class NotFoundError(DialectaError):
    def __init__(self, resource: str):
        super().__init__(ErrorCode.NOT_FOUND, f"{resource} not found", status_code=404)


class RateLimitError(DialectaError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(ErrorCode.RATE_LIMITED, message, status_code=429)


class AgentDegradedError(DialectaError):
    def __init__(self, agent_name: str):
        super().__init__(
            ErrorCode.AGENT_DEGRADED,
            f"Agent '{agent_name}' is degraded and has been excluded from this debate",
            status_code=503,
        )


class ValidationError(DialectaError):
    def __init__(self, message: str):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, status_code=422)


class InjectionDetectedError(DialectaError):
    def __init__(self):
        super().__init__(
            ErrorCode.INJECTION_DETECTED,
            "Topic contains disallowed content",
            status_code=400,
        )


def ok(data: dict | list | None = None, message: str = "OK") -> dict:
    return {"success": True, "message": message, "data": data}


def err(code: str, message: str) -> dict:
    return {"success": False, "error": {"code": code, "message": message}}


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://dialecta-tau.vercel.app",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-ID",
}


async def dialecta_exception_handler(request: Request, exc: DialectaError) -> JSONResponse:
    logger.warning("DialectaError %s: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=err(exc.code, exc.message),
        headers=CORS_HEADERS,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning("HTTPException %s: %s", exc.status_code, exc.detail)
    safe_message = exc.detail if isinstance(exc.detail, str) else "An error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content=err(f"HTTP_{exc.status_code}", safe_message),
        headers=CORS_HEADERS,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.debug("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=err(ErrorCode.VALIDATION_ERROR, "Invalid request data"),
        headers=CORS_HEADERS,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=err(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred"),
        headers=CORS_HEADERS,
    )