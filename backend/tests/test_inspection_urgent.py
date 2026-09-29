"""v155 — «همین الان برو سراغش»: the fast queue.

The supervisor runs twice a week, so a sheet can wait four days. The owner can
put one at the front of a separate queue that is checked often. Their conditions,
in their words, are what these tests are about:

    «اگر چند تا با هم زدم اول هر کدوم زودتر زدم انجام بده بعد دونه دونه به ترتیب»
    «بدون اینکه به تناقض بخوره و کرش کنه و تایم اوت بشه»

So: strict first-pressed-first order, exactly one run on a sheet at a time, and
no way for a dead run to park the queue.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.inspection import (
    STATUS_FILED, URGENT_CLAIM_TTL_S, InspectionReport,
)

SPOT = {
    "page": "/customers", "page_label": "مشتریان", "section_id": "", "section_label": "",
    "reopen": "/customers", "dom_path": "body", "covered_text": "x",
    "rect": {"x": 1, "y": 1, "w": 9, "h": 9}, "viewport": {"w": 1200, "h": 800},
}


async def _sheet(client, headers, text="یک ایراد"):
    r = await client.post("/api/inspection", headers=headers,
                          json={"text": text, "spot": SPOT})
    assert r.status_code == 200, r.text
    return r.json()["report"]


async def _rush(client, headers, rid):
    return await client.post(f"/api/inspection/{rid}/urgent", headers=headers)


class TestTheOwnerAsksForItNow:
    async def test_marking_one_puts_it_in_the_queue(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        assert rep["urgent"] is False
        r = await _rush(client, auth_headers, rep["id"])
        assert r.status_code == 200, r.text
        assert r.json()["position"] == 1
        assert r.json()["report"]["urgent"] is True

    async def test_the_queue_is_in_the_order_they_were_PRESSED(
            self, client, auth_headers):
        """«اول هر کدوم زودتر زدم» — the promise the whole feature rests on."""
        a = await _sheet(client, auth_headers, "اول")
        b = await _sheet(client, auth_headers, "دوم")
        c = await _sheet(client, auth_headers, "سوم")
        # pressed out of creation order, on purpose
        await _rush(client, auth_headers, c["id"])
        await asyncio.sleep(0.01)
        await _rush(client, auth_headers, a["id"])
        await asyncio.sleep(0.01)
        await _rush(client, auth_headers, b["id"])

        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert q["waiting"] == 3
        assert [x["number"] for x in q["reports"]] == [c["number"], a["number"], b["number"]]
        assert [x["position"] for x in q["reports"]] == [1, 2, 3]

    async def test_pressing_twice_does_not_move_it(self, client, auth_headers):
        """Re-pressing must not quietly jump the queue — or lose your place."""
        a = await _sheet(client, auth_headers, "اول")
        b = await _sheet(client, auth_headers, "دوم")
        await _rush(client, auth_headers, a["id"])
        await asyncio.sleep(0.01)
        await _rush(client, auth_headers, b["id"])
        await asyncio.sleep(0.01)
        r = await _rush(client, auth_headers, a["id"])          # again
        assert r.json()["position"] == 1, "the first request time must stand"
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert [x["number"] for x in q["reports"]] == [a["number"], b["number"]]

    async def test_it_can_be_taken_back(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        await _rush(client, auth_headers, rep["id"])
        r = await client.delete(f"/api/inspection/{rep['id']}/urgent", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["report"]["urgent"] is False
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert q["waiting"] == 0

    async def test_a_filed_sheet_cannot_be_rushed(self, client, auth_headers, db_session):
        rep = await _sheet(client, auth_headers)
        row = (await db_session.execute(select(InspectionReport).where(
            InspectionReport.id == rep["id"]))).scalar_one()
        row.status = STATUS_FILED
        await db_session.commit()
        r = await _rush(client, auth_headers, rep["id"])
        assert r.status_code == 422

    async def test_the_supervisor_cannot_rush_its_own_work(
            self, client, auth_headers, monkeypatch, test_user):
        rep = await _sheet(client, auth_headers)
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        assert (await _rush(client, auth_headers, rep["id"])).status_code == 403


class TestOneAtATimeAndNoCollision:
    @pytest.fixture(autouse=True)
    def _as_supervisor(self, monkeypatch, test_user):
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)

    async def _rushed(self, client, headers, n, monkeypatch, test_user):
        """n sheets, rushed in order, as the OWNER."""
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        out = []
        for i in range(n):
            rep = await _sheet(client, headers, f"مورد {i}")
            await _rush(client, headers, rep["id"])
            await asyncio.sleep(0.01)
            out.append(rep)
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        return out

    async def test_claim_hands_out_the_oldest_first(
            self, client, auth_headers, monkeypatch, test_user):
        reps = await self._rushed(client, auth_headers, 3, monkeypatch, test_user)
        got = []
        for _ in range(3):
            r = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                  json={"by": "run-1"})
            got.append(r.json()["report"]["number"])
        assert got == [x["number"] for x in reps]

    async def test_a_claimed_sheet_is_NOT_handed_out_twice(
            self, client, auth_headers, monkeypatch, test_user):
        """The «تناقض» this exists to prevent: two runs answering one sheet."""
        await self._rushed(client, auth_headers, 1, monkeypatch, test_user)
        first = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                  json={"by": "run-1"})
        assert first.json()["report"] is not None
        second = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                   json={"by": "run-2"})
        assert second.json()["report"] is None, "a second run must not get the same sheet"
        assert second.json()["busy"] == 1

    async def test_an_empty_queue_is_quiet_not_an_error(self, client, auth_headers):
        """The normal case on most runs — it must be cheap and silent."""
        r = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                              json={"by": "run-1"})
        assert r.status_code == 200
        assert r.json()["report"] is None and r.json()["waiting"] == 0

    async def test_a_dead_run_does_not_park_the_queue_forever(
            self, client, auth_headers, db_session, monkeypatch, test_user):
        """A run that crashed mid-answer must not hold a sheet until someone
        notices — that is the failure this queue exists to end."""
        reps = await self._rushed(client, auth_headers, 1, monkeypatch, test_user)
        await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                          json={"by": "dead-run"})
        row = (await db_session.execute(select(InspectionReport).where(
            InspectionReport.id == reps[0]["id"]))).scalar_one()
        row.urgent_claimed_at = datetime.now(timezone.utc) - timedelta(
            seconds=URGENT_CLAIM_TTL_S + 60)
        await db_session.commit()

        again = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                  json={"by": "live-run"})
        assert again.json()["report"] is not None, "the stale claim must expire"
        assert again.json()["report"]["number"] == reps[0]["number"]

    async def test_answering_discharges_the_urgency(
            self, client, auth_headers, monkeypatch, test_user):
        reps = await self._rushed(client, auth_headers, 2, monkeypatch, test_user)
        await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                          json={"by": "run-1"})
        r = await client.post(f"/api/inspection/{reps[0]['id']}/notes", headers=auth_headers,
                              json={"text": "بررسی شد", "outcome": "not-done"})
        assert r.status_code == 200, r.text
        rep = r.json()["report"]
        assert rep["urgent"] is False
        assert rep["urgent_done_at"], "the owner must see that what they rushed was answered"
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert q["waiting"] == 1, "only the unanswered one is left"

    async def test_the_owner_writing_again_puts_it_back_at_its_ORIGINAL_place(
            self, client, auth_headers, monkeypatch, test_user):
        """Asking a follow-up must not cost them their position in the queue."""
        reps = await self._rushed(client, auth_headers, 2, monkeypatch, test_user)
        await client.post(f"/api/inspection/{reps[0]['id']}/notes", headers=auth_headers,
                          json={"text": "بررسی شد", "outcome": "not-done"})
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        await client.post(f"/api/inspection/{reps[0]['id']}/notes", headers=auth_headers,
                          json={"text": "هنوز درست نشده"})
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert [x["number"] for x in q["reports"]] == [reps[0]["number"], reps[1]["number"]]

    async def test_only_the_supervisor_may_claim(
            self, client, auth_headers, monkeypatch):
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        r = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                              json={"by": "someone"})
        assert r.status_code == 403
