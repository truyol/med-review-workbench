import logging
import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.request_id import get_request_id


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper()),
        ),
        cache_logger_on_first_use=True,
    )


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            self._log_completed(request, started=started, status_code=500)
            raise

        self._log_completed(request, started=started, status_code=response.status_code)
        return response

    @staticmethod
    def _log_completed(request: Request, *, started: float, status_code: int) -> None:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        structlog.get_logger("api.access").info(
            "request.completed",
            request_id=get_request_id(),
            method=request.method,
            path=request.url.path,
            status=status_code,
            duration_ms=duration_ms,
        )
