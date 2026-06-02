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


def route_label(request) -> str:
    """A low-cardinality label for the request (route template when available)."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path
