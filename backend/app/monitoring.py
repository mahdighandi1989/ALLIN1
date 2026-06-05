"""Observability: structured error logging + Prometheus performance metrics.

* Errors — a global exception handler assigns every unhandled error a unique
  ``error_id`` and logs it via ``structlog`` (``logger.exception``) so the same
  id appears in the client response and the server logs for correlation.
* Performance — a ``prometheus_client`` ``Histogram`` records per-request latency
  and a ``Counter`` records request/error volume; both are exposed at ``/metrics``
  so error rate and latency are observable in production.
"""
from __future__ import annotations

import logging

import structlog
from prometheus_client import Counter, Histogram

# --- structured logging ------------------------------------------------------
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)


def get_logger(name: str = "app"):
    """Return a structlog bound logger."""
    return structlog.get_logger(name)


# --- user-engagement (interaction) observability -----------------------------
# Why this exists: the foundational layers (auth, settings) are stable, but the
# product emitted almost no ``info`` logs, so there was no way to *measure*
# whether users actually engage with the core features. Request latency/volume
# metrics alone count traffic, not engagement. The helpers below emit one
# structured, machine-ingestable ``info`` log per *meaningful* user interaction
# (and increment a dedicated counter), giving production dashboards a real
# "interactions per day / per user" signal — the outcome this finding targets.
#
# Measurable outcome target: 100% of tracked API interactions emit exactly one
# ``info``-level ``user_interaction`` log and increment ``user_interactions_total``.

# A dedicated logger name so log pipelines can filter engagement events cheaply
# (``logger == "interaction"``) without parsing message bodies.
_interaction_logger = structlog.get_logger("interaction")

# Paths that are infrastructure/noise rather than a *user* interaction. Excluding
# them keeps the engagement signal honest (a Prometheus scrape or health probe is
# not a person using the product).
_INTERACTION_IGNORED_EXACT = frozenset(
    {
        "/health",
        "/metrics",
        "/favicon.ico",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/",
    }
)

# Prefixes that are static assets / framework noise, never a tracked interaction.
_INTERACTION_IGNORED_PREFIXES = (
    "/_next",
    "/static",
    "/assets",
)


def is_tracked_interaction(method: str, path: str) -> bool:
    """Return ``True`` when (method, path) represents a real user interaction.

    Only API calls that a person can trigger are tracked. CORS pre-flight
    (``OPTIONS``), health/metrics probes, the OpenAPI docs and static assets are
    excluded so the ``user_interaction`` signal reflects genuine engagement, not
    background traffic.
    """
    if method.upper() == "OPTIONS":
        return False
    if path in _INTERACTION_IGNORED_EXACT:
        return False
    if any(path.startswith(prefix) for prefix in _INTERACTION_IGNORED_PREFIXES):
        return False
    # Only first-party API surface counts as a product interaction.
    return path.startswith("/api/")


# --- Prometheus metrics ------------------------------------------------------
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "path", "status"),
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=("method", "path", "status"),
)

UNHANDLED_ERRORS = Counter(
    "http_unhandled_errors_total",
    "Total number of unhandled exceptions surfaced as HTTP 500",
)

# Authentication outcome counter. Lets production dashboards compute the auth
# success rate (and break failures down by reason) directly from the JWT layer,
# independent of the HTTP route that triggered the verification.
AUTH_OUTCOMES = Counter(
    "auth_token_verifications_total",
    "JWT access-token verifications grouped by outcome",
    labelnames=("outcome",),
)

# Engagement counter. Lets dashboards compute interactions-per-day (the finding's
# outcome metric) and break it down by route and outcome, independent of the raw
# HTTP request counter which also includes health/metrics/static traffic.
USER_INTERACTIONS = Counter(
    "user_interactions_total",
    "Meaningful user interactions with core features, grouped by route/outcome",
    labelnames=("method", "path", "outcome"),
)


def log_interaction(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str | None = None,
) -> None:
    """Record one user interaction: increment the counter and emit an info log.

    The structured log intentionally carries only *metadata* needed to analyse
    usage (route, status, latency, outcome, and the acting ``user_id`` — an
    opaque identifier, not personal content). Request/response bodies are never
    logged, so no sensitive data leaks into the engagement stream.

    ``outcome`` is ``"success"`` for any non-error status (< 400) and
    ``"error"`` otherwise, so a success *rate* is computable straight from the
    counter labels.
    """
    outcome = "success" if status_code < 400 else "error"
    USER_INTERACTIONS.labels(method, path, outcome).inc()
    _interaction_logger.info(
        "user_interaction",
        method=method,
        path=path,
        status=status_code,
        outcome=outcome,
        duration_ms=round(duration_ms, 2),
        user_id=user_id,
    )


def route_label(request) -> str:
    """A low-cardinality label for the request (route template when available)."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path
