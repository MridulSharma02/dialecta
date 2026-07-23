import time
import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("dialecta.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        request.state.request_id = request_id

        logger.info(
            "[%s] → %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("[%s] Unhandled during dispatch", request_id)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "[%s] ← %s %s %.1fms",
            request_id,
            response.status_code,
            request.url.path,
            elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response