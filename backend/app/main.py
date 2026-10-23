import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router as api_v1_router
from app.core.config import get_settings
from app.core.database import async_engine
from app.schemas.common import HealthResponse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ReqID: %(request_id)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app")

settings = get_settings()


class CorrelationIdFilter(logging.Filter):
    """Ensure every log record has a request_id attribute to prevent format crashes."""
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "system"
        return True


# Attach correlation filter to root logger handlers
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and clean resource shutdown."""
    logger.info(
        "Starting %s in %s environment (Debug=%s)",
        settings.PROJECT_NAME,
        settings.ENVIRONMENT,
        settings.DEBUG,
        extra={"request_id": "startup"},
    )
    yield
    logger.info(
        "Shutting down application and disposing connection pools...",
        extra={"request_id": "shutdown"},
    )
    await async_engine.dispose()
    logger.info("Database connection pools disposed successfully.", extra={"request_id": "shutdown"})


def create_app() -> FastAPI:
    """Application factory for FastAPI app instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Private educational learning and productivity management platform",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # 1. Correlation ID & Access Logging Middleware
    @app.middleware("http")
    async def correlation_id_and_logging_middleware(
        request: Request, call_next
    ) -> Response:
        # Extract or generate correlation ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id

        start_time = time.perf_counter()
        # Process request
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Attach request ID to response headers
        response.headers["X-Request-ID"] = req_id

        # Log request execution without printing sensitive cookies/auth payloads
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "%s %s - %d %s (%.2fms) [Client: %s]",
            request.method,
            request.url.path,
            response.status_code,
            response.headers.get("content-type", "none"),
            duration_ms,
            client_host,
            extra={"request_id": req_id},
        )
        return response

    # 2. CORS Middleware (Explicit origins with credentials support)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 3. Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "unknown")
        headers = exc.headers or {}
        headers["X-Request-ID"] = req_id
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "code": "HTTP_ERROR",
                "request_id": req_id,
            },
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "unknown")
        # Extract clean error details
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append(f"{loc}: {err.get('msg')}")
        detail_msg = "; ".join(errors)

        return JSONResponse(
            status_code=422,
            content={
                "error": "Request validation failed",
                "detail": detail_msg,
                "code": "VALIDATION_ERROR",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", "unknown")
        logger.exception("Unhandled server exception: %s", exc, extra={"request_id": req_id})

        detail_text = str(exc) if settings.DEBUG else "An unexpected error occurred"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": detail_text,
                "code": "INTERNAL_SERVER_ERROR",
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id},
        )

    # 4. Root API and Health Routes
    @app.get("/", tags=["Root"])
    async def root_info() -> dict:
        return {
            "name": settings.PROJECT_NAME,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "docs": "/docs" if settings.DEBUG else "disabled",
        }

    # Root health check alias
    @app.get("/health", tags=["Health"], response_model=HealthResponse)
    async def root_health(request: Request) -> Response:
        from app.api.v1.health import check_health
        from app.core.database import async_session_factory
        async with async_session_factory() as db:
            res = Response()
            health_data = await check_health(response=res, db=db)
            return JSONResponse(
                status_code=res.status_code,
                content=health_data.model_dump(),
                headers={"X-Request-ID": getattr(request.state, "request_id", "system")},
            )

    # 5. Mount API v1 router
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
