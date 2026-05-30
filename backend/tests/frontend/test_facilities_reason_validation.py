"""Backend-contract test backing the frontend 'reason' validation fix.

The frontend anti-pattern was handling an API rejection ``reason`` with
``if (reason instanceof Response)`` and assuming a Response/`message` shape. The
robust resolution (parseApiError) relies on the backend ALWAYS returning a
structured JSON error body (``{"detail": ...}`` or ``{"message": ...}``) rather
than an opaque Response — these tests pin that contract so a non-Response reason
on the client is always a parseable object.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestErrorResponsesAreStructured:
    async def test_handle_non_response_reason(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Validation (422) and not-found (404) errors return structured JSON."""
        # 422 — invalid body (missing required amount on a facility create).
        r = await client.post(
            "/api/facilities/",
            json={"customer_id": "x", "facility_type": "loan"},
            headers=auth_headers,
        )
        assert r.status_code == 422
        assert r.headers["content-type"].startswith("application/json")
        assert "detail" in r.json()  # parseable object, never a raw Response

        # 404 — not found returns a structured detail string.
        r = await client.get("/api/facilities/does-not-exist", headers=auth_headers)
        assert r.status_code == 404
        assert isinstance(r.json().get("detail"), str)

    async def test_unauthorized_reason_is_structured(self, client: AsyncClient):
        r = await client.get("/api/facilities/")
        assert r.status_code == 401
        assert "detail" in r.json()
