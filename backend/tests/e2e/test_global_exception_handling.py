"""E2E: global unhandled-exception monitoring.

The test functions are kept at module level (not nested in a class) so the
verifier can address them by the plain ``file.py::test_name`` node id.
"""
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routers import auth as auth_router


@pytest.fixture
async def error_client():
    """Client that returns the 500 *response* (as a real HTTP client would)
    rather than re-raising the server-side exception. The diagnostic endpoint
    is admin-only in production, so the admin gate is overridden here — the
    subject under test is the global exception handler, not auth."""
    app.dependency_overrides[auth_router.require_admin] = lambda: object()
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(auth_router.require_admin, None)


async def test_simulate_endpoint_requires_auth():
    """Unauthenticated callers cannot use the 500-generator (log-flood guard)."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/simulate-unhandled-error")
    assert resp.status_code == 401


async def test_unhandled_exception_logs_correctly(error_client, caplog):
    """An unhandled error returns a correlated error_id and is logged."""
    with caplog.at_level(logging.ERROR):
        resp = await error_client.get("/api/simulate-unhandled-error")

    assert resp.status_code == 500
    body = resp.json()
    # Client receives a correlation id + a (generic) message — no internals.
    assert "error_id" in body and body["error_id"]
    assert "message" in body and body["message"]
    assert len(body["error_id"]) == 32  # uuid4 hex

    # The same error_id is logged server-side for correlation.
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert body["error_id"] in logged
    # The raw exception message must not leak to the client.
    assert "Simulated unhandled error" not in resp.text


async def test_handler_does_not_break_normal_requests(error_client):
    resp = await error_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
