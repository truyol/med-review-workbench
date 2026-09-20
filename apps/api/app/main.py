from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes.health import router as health_router
from app.domain.errors import ApiError
from app.observability.logging import AccessLogMiddleware, configure_logging
from app.observability.request_id import RequestIdMiddleware, get_request_id
from app.settings import get_settings


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "")) or get_request_id()


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    next_action: str,
    details: object | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "next_action": next_action,
        "request_id": request_id,
    }
    if details is not None:
        error["details"] = details

    response_headers = dict(headers or {})
    response_headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=response_headers,
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.ensure_runtime_dirs()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Med Review Workbench API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            next_action=exc.next_action,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            message="请求参数不合法。",
            next_action="请修正输入后重试。",
            details=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return _error_response(
                request,
                status_code=exc.status_code,
                code="NOT_FOUND",
                message="请求的资源不存在。",
                next_action="请检查地址或返回上一页。",
                headers=exc.headers,
            )
        return _error_response(
            request,
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message="请求未能完成。",
            next_action="请检查请求后重试。",
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        structlog.get_logger("api.error").error(
            "request.failed",
            request_id=_request_id(request),
            path=request.url.path,
            error_type=type(exc).__name__,
            error_code="INTERNAL_ERROR",
        )
        return _error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="服务暂时无法完成请求。",
            next_action="请稍后重试；如问题持续，请携带 request_id 反馈。",
        )

    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
