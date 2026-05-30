"""Tests for in-app notifications (bell)."""
import pytest
from httpx import AsyncClient

from app.models.notification import Notification


async def _seed_notes(db_session, user_id=None):
    db_session.add_all([
        Notification(user_id=user_id, level="info", title="Hello", message="A", category="system"),
        Notification(user_id=user_id, level="warning", title="Heads up", message="B", category="facility"),
        Notification(user_id=None, level="success", title="Broadcast", message="C", category="system"),
    ])
    await db_session.commit()


class TestNotifications:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/notifications/")).status_code == 401
        assert (await client.get("/api/notifications/unread-count")).status_code == 401

    async def test_list_and_unread_count(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_notes(db_session)
        r = await client.get("/api/notifications/", headers=auth_headers)
        assert r.status_code == 200
        # All three are visible (2 broadcast-eligible + the broadcast one).
        assert r.json()["total"] >= 3
        assert r.json()["unread"] >= 3

        uc = await client.get("/api/notifications/unread-count", headers=auth_headers)
        assert uc.status_code == 200 and uc.json()["unread"] >= 3

    async def test_mark_one_read(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_notes(db_session)
        first = (await client.get("/api/notifications/", headers=auth_headers)).json()["items"][0]
        before = (await client.get("/api/notifications/unread-count", headers=auth_headers)).json()["unread"]
        r = await client.post(f"/api/notifications/{first['id']}/read", headers=auth_headers)
        assert r.status_code == 200
        after = (await client.get("/api/notifications/unread-count", headers=auth_headers)).json()["unread"]
        assert after == before - 1

    async def test_mark_all_read(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_notes(db_session)
        r = await client.post("/api/notifications/read-all", headers=auth_headers)
        assert r.status_code == 200
        assert (await client.get("/api/notifications/unread-count", headers=auth_headers)).json()["unread"] == 0

    async def test_unread_only_filter(self, client: AsyncClient, auth_headers: dict, db_session):
        await _seed_notes(db_session)
        await client.post("/api/notifications/read-all", headers=auth_headers)
        r = await client.get("/api/notifications/?unread_only=true", headers=auth_headers)
        assert r.status_code == 200 and r.json()["total"] == 0

    async def test_mark_unknown_404(self, client: AsyncClient, auth_headers: dict):
        assert (await client.post("/api/notifications/nope/read", headers=auth_headers)).status_code == 404

    async def test_offer_creation_emits_notification(self, client: AsyncClient, auth_headers: dict, test_customer):
        before = (await client.get("/api/notifications/unread-count", headers=auth_headers)).json()["unread"]
        r = await client.post(
            "/api/offer-letters/",
            json={"customer_id": test_customer.id, "expiry_date": "2027-12-31",
                  "principal_amount": 1000000, "interest_rate": 6, "tenor_months": 12},
            headers=auth_headers,
        )
        assert r.status_code == 201
        after = (await client.get("/api/notifications/unread-count", headers=auth_headers)).json()["unread"]
        assert after == before + 1

    async def test_server_side_pagination(self, client: AsyncClient, auth_headers: dict, db_session):
        for i in range(15):
            db_session.add(Notification(user_id=None, level="info", title=f"P{i}", category="system"))
        await db_session.commit()

        p1 = await client.get("/api/notifications/?page=1&page_size=10", headers=auth_headers)
        assert p1.status_code == 200
        b1 = p1.json()
        assert b1["page"] == 1 and b1["page_size"] == 10
        assert len(b1["items"]) == 10
        assert b1["total"] >= 15

        p2 = await client.get("/api/notifications/?page=2&page_size=10", headers=auth_headers)
        b2 = p2.json()
        assert b2["page"] == 2
        # No overlap between pages.
        ids1 = {i["id"] for i in b1["items"]}
        ids2 = {i["id"] for i in b2["items"]}
        assert ids1.isdisjoint(ids2)
