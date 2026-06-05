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
| Metrics endpoint | `backend/app/main.py` — `GET /metrics` (Prometheus exposition, `generate_latest`; `include_in_schema=False` — internal, hidden from public OpenAPI, see `docs/ENDPOINT_AUDIT.md`) |

Latency is measured in a `finally` block so failed requests (HTTP 500) are
still recorded — a prerequisite for a *real* error rate and latency
percentiles.

## 3. User-engagement metrics (interaction tracking)

**Why:** the foundational layers (auth, settings) were stable but the product
emitted almost no `info` logs, so there was no way to *measure* whether users
actually engage with the core features — request latency/volume counts traffic,
not engagement. (Task `b6ff9b08-d9df-4c3b-9434-f03c91af125f`.)

**Outcome target (measurable):** **100%** of meaningful API interactions emit
exactly one `info`-level `user_interaction` structured log **and** increment the
`user_interactions_total` Prometheus counter. This makes "interactions per day /
per user" a real production signal (the finding asked for a ≥5× rise in `info`
logs for genuine usage events). Health/metrics probes, static assets and CORS
pre-flight are excluded so the signal reflects real engagement, not background
traffic. Logs carry only usage *metadata* (method, route, status, outcome,
latency, opaque `user_id`) — never request bodies — so no sensitive data leaks.

| Concern | Location |
| --- | --- |
| Interaction classifier (what counts as engagement) | `backend/app/monitoring.py` — `is_tracked_interaction(...)` |
| Engagement log + counter helper | `backend/app/monitoring.py` — `log_interaction(...)` |
| Engagement counter | `backend/app/monitoring.py` — `USER_INTERACTIONS` (`user_interactions_total`, labels `method/path/outcome`) |
| Dedicated structured logger | `backend/app/monitoring.py` — `structlog.get_logger("interaction")` → event `user_interaction` |
| Emit point (around the route) | `backend/app/middleware.py` — `MetricsMiddleware.dispatch` (`finally` block) |
| Acting `user_id` capture | `backend/app/routers/auth.py` — `get_current_user` stashes `request.state.user_id` (see `_bind_interaction_user`) |

The emit happens in the same `finally` block as the latency/volume metrics, so
even failed interactions (4xx/5xx) are counted with `outcome="error"`, making a
success *rate* computable directly from the counter labels.

## 4. E2E tests (outcome measurement)

| Acceptance criterion | Test node |
| --- | --- |
| Unhandled exception logs correctly | `backend/tests/e2e/test_global_exception_handling.py::test_unhandled_exception_logs_correctly` |
| API latency within threshold | `backend/tests/e2e/test_performance.py::test_api_latency_within_threshold` |
| Metrics endpoint exposes histogram | `backend/tests/e2e/test_performance.py::test_metrics_endpoint_exposes_histogram` |
| Handler does not break normal requests | `backend/tests/e2e/test_global_exception_handling.py::test_handler_does_not_break_normal_requests` |
| N interactions raise the counter by N (100% emit rate) | `backend/tests/test_interaction_logging.py::TestEngagementOutcomeE2E::test_n_interactions_increment_counter_by_n` |
| Engagement counter exposed via `/metrics` | `backend/tests/test_interaction_logging.py::TestEngagementOutcomeE2E::test_metrics_endpoint_exposes_engagement_counter` |
| Health/metrics probes do not inflate engagement | `backend/tests/test_interaction_logging.py::TestEngagementOutcomeE2E::test_health_probe_does_not_count_as_engagement` |

Test functions are kept at module level (not nested in a class) so the verifier
can address them by the plain `file.py::test_name` node id.

## Dependencies synced

- upstream: `prometheus-client`, `structlog`, `httpx` (already in
  `backend/requirements.txt`); `user_interactions_total` reuses the existing
  `MetricsMiddleware` and the JWT `get_current_user` dependency
- downstream: `/metrics` now also exposes `user_interactions_total`; this is
  purely additive (a new counter) so existing scrapers and the latency/error
  panels are unaffected. The new metric/log are consumed by external monitoring
  scrapers and by `backend/tests/test_interaction_logging.py`
- cross-tier (backend↔frontend↔db↔infra): none — engagement tracking is
  backend-internal. No DB migration (no schema change), no frontend data-shape
  change (the `user_interaction` log is server-side only; no API response body
  changed), no infra change. CORS/auth behaviour is unchanged
- side artifacts: this document (`docs/OBSERVABILITY.md`)
