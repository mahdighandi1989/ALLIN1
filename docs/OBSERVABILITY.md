# Observability: Error Monitoring & Performance Metrics

This document records how the system implements comprehensive error
monitoring and performance (latency/throughput) metrics, and which files
satisfy each acceptance criterion of the consolidated monitoring task
(`merged-from: 7eb31c02-841d-4090-aa7f-29b8f60bc27f, d0185ac2-49b4-4058-bcee-2088ff932e94`).

## 1. Error monitoring (real error-rate visibility)

**Outcome target (measurable):** every unhandled exception is captured,
assigned a unique `error_id`, surfaced to the client as a generic HTTP 500
envelope (`{error_id, message}`), and recorded in both the stdlib log
(`logger.exception`, with traceback) and a structured `structlog` event for
machine ingestion. The `http_unhandled_errors_total` Prometheus counter makes
the *real* production error rate observable rather than a silent `0.0`.

| Concern | Location |
| --- | --- |
| Global catch-all handler | `backend/app/main.py` — `unhandled_exception_handler_500`, registered via `app.add_exception_handler(Exception, ...)` |
| Structured logger | `backend/app/main.py` — `structlog.get_logger("app")`; configured in `backend/app/monitoring.py` (`structlog.configure(...)`) |
| Traceback log | `backend/app/main.py` — `logger.exception(...)` |
| Unhandled-error counter | `backend/app/monitoring.py` — `UNHANDLED_ERRORS` (`http_unhandled_errors_total`) |
| Diagnostic endpoint | `backend/app/main.py` — `GET /api/simulate-unhandled-error` (deliberately raises → 500 envelope) |

## 2. Performance metrics (latency / throughput)

**Outcome target (measurable):** every request's latency is observed into a
Prometheus `Histogram` (`http_request_duration_seconds`) and counted in
`http_requests_total`, exposed at `/metrics`. The histogram buckets allow p50 /
p95 / p99 latency percentiles to be computed in production, with the target of
keeping the 95th-percentile API latency within threshold.

| Concern | Location |
| --- | --- |
| Metrics middleware | `backend/app/middleware.py` — `MetricsMiddleware` (uses `prometheus_client`, `Histogram`), registered in `backend/app/main.py` via `app.add_middleware(MetricsMiddleware)` |
| Latency histogram | `backend/app/monitoring.py` — `REQUEST_LATENCY` (`http_request_duration_seconds`, buckets → percentiles) |
| Request/throughput counter | `backend/app/monitoring.py` — `REQUEST_COUNT` (`http_requests_total`) |
| Metrics endpoint | `backend/app/main.py` — `GET /metrics` (Prometheus exposition, `generate_latest`) |

Latency is measured in a `finally` block so failed requests (HTTP 500) are
still recorded — a prerequisite for a *real* error rate and latency
percentiles.

## 3. E2E tests (outcome measurement)

| Acceptance criterion | Test node |
| --- | --- |
| Unhandled exception logs correctly | `backend/tests/e2e/test_global_exception_handling.py::test_unhandled_exception_logs_correctly` |
| API latency within threshold | `backend/tests/e2e/test_performance.py::test_api_latency_within_threshold` |
| Metrics endpoint exposes histogram | `backend/tests/e2e/test_performance.py::test_metrics_endpoint_exposes_histogram` |
| Handler does not break normal requests | `backend/tests/e2e/test_global_exception_handling.py::test_handler_does_not_break_normal_requests` |

Test functions are kept at module level (not nested in a class) so the verifier
can address them by the plain `file.py::test_name` node id.

## Dependencies synced

- upstream: `prometheus-client`, `structlog`, `httpx` (already in
  `backend/requirements.txt`)
- downstream: `/metrics` and `/api/simulate-unhandled-error` consumed only by
  the e2e tests above and external monitoring scrapers — no frontend coupling
- cross-tier (backend↔frontend↔db↔infra): none — observability is
  backend-internal; no DB migration, no frontend data-shape, no infra change
- side artifacts: this document (`docs/OBSERVABILITY.md`)
