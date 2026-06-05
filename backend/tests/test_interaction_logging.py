"""Outcome tests for the user-engagement (interaction) observability layer.

Context — this is an *effectiveness* finding: the product was stable but emitted
almost no ``info`` logs, so there was no way to measure whether users actually
engage with the core features. The fix (``app.monitoring.log_interaction`` wired
into ``MetricsMiddleware``) emits one structured ``user_interaction`` info log
and increments ``user_interactions_total`` for every meaningful API call.

These tests assert the *outcome* the finding targets — that genuine interactions
produce a measurable engagement signal — rather than the mere existence of code:

* unit: the helper emits an info-level event with usage metadata and no body,
  and increments the counter; noise paths are excluded.
* e2e: hitting a real authenticated endpoint N times raises
  ``user_interactions_total`` by exactly N (a 100% emit rate over N attempts),
  while health probes do not move the counter.
"""
import pytest
import structlog
from httpx import AsyncClient

from app.monitoring import (
    USER_INTERACTIONS,
    is_tracked_interaction,
    log_interaction,
)


def _counter_total() -> float:
    """Sum every ``user_interactions_total`` sample across all label sets."""
    total = 0.0
    for metric in USER_INTERACTIONS.collect():
        for sample in metric.samples:
            if sample.name == "user_interactions_total":
                total += sample.value
    return total


def _counter_for(method: str, path: str, outcome: str) -> float:
    """Current value of a single ``user_interactions_total`` label combination."""
    return USER_INTERACTIONS.labels(method, path, outcome)._value.get()


class TestInteractionClassification:
    """``is_tracked_interaction`` must reflect *genuine* user engagement only."""

    @pytest.mark.parametrize(
        "method,path,expected",
        [
            ("GET", "/api/auth/me", True),
            ("POST", "/api/customers", True),
            ("DELETE", "/api/facilities/123", True),
            # Infrastructure / noise — never a person using the product.
            ("GET", "/health", False),
            ("GET", "/metrics", False),
            ("GET", "/", False),
            ("GET", "/favicon.ico", False),
            ("GET", "/openapi.json", False),
            ("GET", "/_next/static/chunk.js", False),
            ("GET", "/static/logo.png", False),
            # CORS pre-flight is browser bookkeeping, not engagement.
            ("OPTIONS", "/api/customers", False),
        ],
    )
    def test_classification(self, method, path, expected):
        assert is_tracked_interaction(method, path) is expected


class TestLogInteractionHelper:
    """The helper emits a usage-only info event and increments the counter."""

    def test_emits_info_event_with_usage_metadata(self):
        with structlog.testing.capture_logs() as logs:
            log_interaction(
                method="GET",
                path="/api/customers",
                status_code=200,
                duration_ms=12.345,
                user_id="user-42",
            )

        events = [e for e in logs if e["event"] == "user_interaction"]
        assert len(events) == 1
        event = events[0]
        assert event["log_level"] == "info"
        assert event["method"] == "GET"
        assert event["path"] == "/api/customers"
        assert event["status"] == 200
        assert event["outcome"] == "success"
        assert event["duration_ms"] == 12.35  # rounded to 2 dp
        assert event["user_id"] == "user-42"
        # No request/response body — the engagement stream must stay free of
        # sensitive content.
        assert "body" not in event
        assert "password" not in event

    def test_error_status_is_classified_as_error_outcome(self):
        with structlog.testing.capture_logs() as logs:
            log_interaction(
                method="POST",
                path="/api/customers",
                status_code=422,
                duration_ms=3.0,
            )
        event = next(e for e in logs if e["event"] == "user_interaction")
        assert event["outcome"] == "error"
        assert event["user_id"] is None

    def test_increments_counter(self):
        before = _counter_for("GET", "/api/stats", "success")
        log_interaction(
            method="GET",
            path="/api/stats",
            status_code=200,
            duration_ms=1.0,
            user_id="u1",
        )
        after = _counter_for("GET", "/api/stats", "success")
        assert after == before + 1


@pytest.mark.asyncio
class TestEngagementOutcomeE2E:
    """End-to-end: real interactions must produce a measurable engagement rate."""

    async def test_n_interactions_increment_counter_by_n(
        self, client: AsyncClient, auth_headers: dict
    ):
        """100% of authenticated API calls emit an interaction signal.

        This is the measurable outcome target: over N genuine interactions the
        ``user_interactions_total`` counter rises by exactly N (emit rate = N/N).
        """
        attempts = 5
        before = _counter_total()

        with structlog.testing.capture_logs() as logs:
            for _ in range(attempts):
                response = await client.get("/api/auth/me", headers=auth_headers)
                assert response.status_code == 200

        after = _counter_total()
        assert after - before == attempts  # emit rate == 100%

        interaction_events = [e for e in logs if e["event"] == "user_interaction"]
        assert len(interaction_events) == attempts
        # The acting user id is captured for per-user engagement analysis.
        assert all(e["user_id"] is not None for e in interaction_events)
        assert all(e["path"] == "/api/auth/me" for e in interaction_events)
        assert all(e["outcome"] == "success" for e in interaction_events)

    async def test_metrics_endpoint_exposes_engagement_counter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """The engagement signal is observable in production via /metrics."""
        await client.get("/api/auth/me", headers=auth_headers)

        metrics_response = await client.get("/metrics")
        assert metrics_response.status_code == 200
        body = metrics_response.text
        assert "user_interactions_total" in body
        # The just-made interaction is present in the scrape output.
        assert 'path="/api/auth/me"' in body

    async def test_health_probe_does_not_count_as_engagement(
        self, client: AsyncClient
    ):
        """Health/metrics probes must not inflate the engagement signal."""
        before = _counter_total()
        await client.get("/health")
        await client.get("/metrics")
        after = _counter_total()
        assert after == before
