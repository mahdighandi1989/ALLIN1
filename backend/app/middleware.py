"""Custom ASGI middleware for the application.

Currently this hosts :class:`MetricsMiddleware`, which records per-request
latency and volume into the Prometheus metrics defined in :mod:`app.monitoring`,
and — for meaningful API calls — emits a structured ``user_interaction`` info
log plus an engagement counter so real product usage is measurable in
production. Keeping the middleware in its own module (rather than inline in
``main.py``) keeps the application factory small and gives observability code a
single, discoverable home.
"""
from __future__ import annotations

import time

from prometheus_client import Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.monitoring import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    is_tracked_interaction,
    log_interaction,
    route_label,
)

# The request-latency metric is a Prometheus ``Histogram``; binding it to a
# locally-typed alias documents the contract this middleware relies on (and lets
# static analysers flag an accidental type change in ``monitoring``).
_LATENCY: Histogram = REQUEST_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record per-request latency/volume and per-interaction engagement signals.

    Latency is measured around ``call_next`` and observed into the
    :data:`app.monitoring.REQUEST_LATENCY` histogram, while every request is
    counted in :data:`app.monitoring.REQUEST_COUNT`. The work happens in a
    ``finally`` block so failed requests (which surface as HTTP 500 via the
    global exception handler) are still measured — a prerequisite for computing
    a *real* error rate and latency percentiles in production.

    Additionally, for requests that represent a genuine *user interaction* (see
    :func:`app.monitoring.is_tracked_interaction`), it emits a structured
    ``user_interaction`` info log and increments ``user_interactions_total``.
    This is the engagement signal the product was missing: it makes
    "interactions per day / per user" measurable instead of inferring usage from
    raw traffic. The acting ``user_id`` is read from ``request.state`` when an
    authenticated dependency populated it (see ``get_current_user``); no request
    body is ever logged, so the signal carries no sensitive content.
    """

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
            _LATENCY.labels(request.method, label, str(status_code)).observe(elapsed)
            REQUEST_COUNT.labels(request.method, label, str(status_code)).inc()
            # Engagement signal: only emit for real user-facing API interactions
            # so health/metrics/static traffic does not inflate the usage count.
            if is_tracked_interaction(request.method, request.url.path):
                log_interaction(
                    method=request.method,
                    path=label,
                    status_code=status_code,
                    duration_ms=elapsed * 1000.0,
                    user_id=getattr(request.state, "user_id", None),
                )
