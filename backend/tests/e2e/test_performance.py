"""E2E: API performance metrics and latency threshold."""
import time

import pytest
from httpx import AsyncClient

# Generous CI-safe upper bound for a trivial request (seconds).
LATENCY_THRESHOLD_SECONDS = 2.0


class TestPerformance:
    async def test_api_latency_within_threshold(self, client: AsyncClient):
        """A lightweight endpoint responds well within the latency threshold."""
        samples = []
        for _ in range(5):
            start = time.perf_counter()
            resp = await client.get("/health")
            elapsed = time.perf_counter() - start
            assert resp.status_code == 200
            samples.append(elapsed)

        avg = sum(samples) / len(samples)
        assert avg < LATENCY_THRESHOLD_SECONDS, f"avg latency {avg:.3f}s too high"
        assert max(samples) < LATENCY_THRESHOLD_SECONDS * 2

    async def test_metrics_endpoint_exposes_histogram(self, client: AsyncClient):
        """/metrics exposes the Prometheus request-latency histogram."""
        # Generate at least one measured request first.
        await client.get("/health")
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text
        assert "http_request_duration_seconds" in text
        assert "http_requests_total" in text
