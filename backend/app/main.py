import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from app.config import settings, enforce_security_on_startup
from app.routers import auth, customers, facilities, stats
from app.utils.log_sanitizer import install_log_sanitizer
from app.monitoring import (
    get_logger,
    route_label,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    UNHANDLED_ERRORS,
)
import logging
import os

logging.basicConfig(level=getattr(logging, str(settings.LOG_LEVEL).upper(), logging.INFO))
# Defence-in-depth: scrub passwords/tokens/secrets from every log record.
install_log_sanitizer()
struct_logger = get_logger("app")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast on insecure configuration and log any security warnings.
    enforce_security_on_startup()
    # Self-heal the DB schema to match the models (independent of Alembic, which
    # the deploy swallows on error) and seed demo banking data when empty, so the
    # app works out of the box instead of 500-ing on a drifted schema.
    try:
        from app.db_init import init_database

        await init_database()
    except Exception as exc:  # never let startup hard-crash on bootstrap issues
        logger.error("Database initialization failed: %s", exc)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach hardening headers (incl. HSTS) to every response.

    HSTS is always advertised — browsers ignore ``Strict-Transport-Security``
    received over plain HTTP, so it is safe in development and authoritative in
    production. The one-year ``max-age=31536000`` with ``includeSubDomains`` and
    ``preload`` is the recommended value for HSTS preload eligibility.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=31536000; includeSubDomains; preload",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response


class HTTPSRedirectInProductionMiddleware(BaseHTTPMiddleware):
    """In production, redirect any plain-HTTP request to its HTTPS equivalent.

    The original scheme is taken from the ``X-Forwarded-Proto`` header set by the
    reverse proxy (Render/NGINX) when present, otherwise from ``request.url``.
    Health checks are exempt so the platform's HTTP probe keeps working.
    """

    async def dispatch(self, request: Request, call_next):
        if settings.should_force_https():
            forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            if forwarded_proto == "http" and request.url.path != "/health":
                https_url = request.url.replace(scheme="https")
                # Redirect HTTP to HTTPS (301) so clients upgrade the connection.
                return JSONResponse(
                    status_code=status.HTTP_301_MOVED_PERMANENTLY,
                    content={"detail": "Use HTTPS"},
                    headers={"Location": str(https_url)},
                )
        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record per-request latency and volume into Prometheus metrics."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            label = route_label(request)
            REQUEST_LATENCY.labels(request.method, label, str(status_code)).observe(elapsed)
            REQUEST_COUNT.labels(request.method, label, str(status_code)).inc()


# Security + metrics middleware (order matters: redirect first, then headers).
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectInProductionMiddleware)
app.add_middleware(MetricsMiddleware)

# CORS — only the explicitly allow-listed origins may call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=settings.CORS_MAX_AGE,
)


async def unhandled_exception_handler_500(request: Request, exc: Exception):
    """Catch-all handler so unexpected errors never leak internals.

    Every unhandled error gets a unique ``error_id`` that is returned to the
    client AND logged (via stdlib + structlog ``logger.exception``) for
    correlation. In production the client sees only a generic message; in
    development the error type is surfaced to aid debugging. Sensitive values in
    the log are scrubbed by the installed :class:`SensitiveDataFilter`.
    """
    error_id = uuid.uuid4().hex
    UNHANDLED_ERRORS.inc()
    # stdlib logger (logger.exception attaches the traceback)
    logger.exception(
        "Unhandled exception error_id=%s on %s %s",
        error_id,
        request.method,
        request.url.path,
    )
    # structured log for machine ingestion / production observability
    struct_logger.error(
        "unhandled_exception",
        error_id=error_id,
        method=request.method,
        path=request.url.path,
        exc_type=type(exc).__name__,
    )
    if settings.is_production():
        message = "Internal server error"  # generic message, no internals leaked
    else:
        message = f"Internal server error: {type(exc).__name__}"
    return JSONResponse(
        status_code=500,
        content={"error_id": error_id, "message": message, "detail": message},
    )


# Register the catch-all handler (equivalent to @app.exception_handler(Exception)).
app.add_exception_handler(Exception, unhandled_exception_handler_500)


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics (request latency/volume, error count)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/simulate-unhandled-error")
async def simulate_unhandled_error():
    """Diagnostic endpoint that deliberately raises to exercise error monitoring.

    Hitting it returns the standard 500 error envelope ({error_id, message}) and
    produces a correlated server-side log entry.
    """
    raise RuntimeError("Simulated unhandled error for monitoring verification")


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# The static directory should contain the frontend build files.
static_dir = "static"


def mount_static_frontend(application: FastAPI, directory: str) -> bool:
    """Mount the built frontend, with explicit (not silent) failure feedback.

    Previously a missing static directory only produced a debug-level warning and
    the app carried on as if nothing were wrong — a broken feedback loop where a
    real deployment problem (frontend not built/copied) stayed invisible until a
    user hit a blank site. Now the severity is tied to the environment: a missing
    directory in production is logged at ERROR level so it surfaces in alerting,
    while in development it remains an informational warning (the API still runs).

    Returns True if the directory was mounted, False otherwise. Must be called
    last so the catch-all mount does not shadow the API routes.
    """
    if os.path.exists(directory):
        application.mount(
            "/", StaticFiles(directory=directory, html=True), name="static_frontend"
        )
        logger.info("Serving frontend from directory: %s", directory)
        return True

    msg = (
        "Static directory '%s' not found. Frontend will not be served. "
        "Run the frontend build and ensure it is copied into the backend."
    )
    if settings.is_production():
        # FIXME: Broken feedback loop for static dir — in production a missing
        # build is a deploy failure, so escalate it instead of swallowing it.
        logging.error(msg, directory)
    else:
        logger.warning(msg, directory)
    return False


mount_static_frontend(app, static_dir)
