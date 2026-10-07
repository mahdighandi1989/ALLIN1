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
import json
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


class TestYouCanSeeWhenAClaimLapses:
    """v156 — «not claimable» and «stuck forever» must not look the same.

    A sheet in hand and a sheet parked by a dead run both report
    `urgent_in_progress`. Without the claim's timestamp there is no way to tell
    them apart except by waiting, which is precisely the thing the TTL exists to
    avoid having to do.
    """

    async def test_an_unclaimed_sheet_reports_no_claim_times(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        await _rush(client, auth_headers, rep["id"])
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        row = next(r for r in q["reports"] if r["id"] == rep["id"])
        assert row["urgent_claimed_at"] is None
        assert row["urgent_claim_expires_at"] is None

    async def test_a_claimed_sheet_says_when_it_was_taken_and_when_it_lapses(
            self, client, auth_headers, db_session, monkeypatch, test_user):
        rep = await _sheet(client, auth_headers)
        await _rush(client, auth_headers, rep["id"])
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        resp = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                 json={"by": "routine"})
        assert resp.status_code == 200, resp.text
        got = resp.json()
        assert got["report"]["id"] == rep["id"], resp.text
        one = (await client.get(f"/api/inspection/{rep['id']}", headers=auth_headers)).json()
        row = one.get("report", one)
        assert row["urgent_claimed_at"] is not None
        assert row["urgent_claim_expires_at"] is not None
        taken = datetime.fromisoformat(row["urgent_claimed_at"])
        lapses = datetime.fromisoformat(row["urgent_claim_expires_at"])
        assert (lapses - taken).total_seconds() == URGENT_CLAIM_TTL_S

    async def test_an_expired_claim_stops_reporting_a_holder(
            self, client, auth_headers, db_session, monkeypatch, test_user):
        rep = await _sheet(client, auth_headers)
        await _rush(client, auth_headers, rep["id"])
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        claimed = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                                    json={"by": "routine"})
        assert claimed.status_code == 200 and claimed.json()["report"], claimed.text
        row = (await db_session.execute(select(InspectionReport).where(
            InspectionReport.id == rep["id"]))).scalar_one()
        row.urgent_claimed_at = datetime.now(timezone.utc) - timedelta(seconds=URGENT_CLAIM_TTL_S + 60)
        await db_session.commit()
        q = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        got = next(r for r in q["reports"] if r["id"] == rep["id"])
        assert got["claimable"] is True
        assert got["urgent_claimed_by"] == ""
        assert got["urgent_claimed_at"] is None       # a lapsed claim is not a claim


class TestAFollowUpReopensTheSheet:
    """v158 — the owner wrote under an answered sheet and it stayed green.

    Their words: «ثبت گزارش مجدد ذیل اون گزارش قبلی باعث نشد که رنگ سبز هایلایت
    دوباره تغییر کنه و همچنان داره سبز نشون میده». The cause was an `elif`: a
    sheet that had been rushed AND answered took the «put it back in the queue»
    branch and never reached the «it is not answered any more» one. The colour
    said «درست شد» while they were asking for more.
    """

    async def _answered(self, client, headers, monkeypatch, test_user, rush: bool):
        rep = await _sheet(client, headers)
        if rush:
            await _rush(client, headers, rep["id"])
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=headers,
                              json={"text": "انجام شد", "outcome": "partial"})
        assert r.status_code == 200, r.text
        assert r.json()["report"]["status"] == "answered"
        return rep

    async def test_an_owner_note_reopens_an_answered_sheet(
            self, client, auth_headers, monkeypatch, test_user):
        rep = await self._answered(client, auth_headers, monkeypatch, test_user, rush=False)
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "هنوز درست نشده"})
        assert r.json()["report"]["status"] == "open"

    async def test_it_reopens_even_when_the_sheet_had_been_rushed(
            self, client, auth_headers, monkeypatch, test_user):
        """THE REGRESSION. With the old `elif` this case stayed «answered»."""
        rep = await self._answered(client, auth_headers, monkeypatch, test_user, rush=True)
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "باز هم ایراد دارد"})
        body = r.json()["report"]
        assert body["status"] == "open", "a rushed+answered sheet stayed answered"
        assert body["glow"]["tone"] == "open", "and so it was still showing green"
        assert body["urgent"] is True, "and it should be back in the fast queue"

    async def test_the_owner_can_take_their_own_tick_back(
            self, client, auth_headers, monkeypatch, test_user):
        rep = await self._answered(client, auth_headers, monkeypatch, test_user, rush=False)
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        ok = await client.post(f"/api/inspection/{rep['id']}/status", headers=auth_headers,
                               json={"status": "approved"})
        assert ok.status_code == 200, ok.text
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "ببخشید، یک چیز دیگر هم هست"})
        assert r.json()["report"]["status"] == "open"

    async def test_an_archived_sheet_stays_archived(
            self, client, auth_headers, monkeypatch, test_user):
        """FILED is terminal — the highlight is gone and the sheet is closed."""
        rep = await self._answered(client, auth_headers, monkeypatch, test_user, rush=False)
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        await client.post(f"/api/inspection/{rep['id']}/status", headers=auth_headers,
                          json={"status": "approved"})
        # Filing is the supervisor's round, not a status the owner can set.
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        filed = await client.post("/api/inspection/file", headers=auth_headers)
        assert filed.status_code == 200, filed.text
        assert filed.json()["filed"] >= 1
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "یادداشت روی بایگانی"})
        assert r.json()["report"]["status"] == "filed"


class TestAFollowUpKeepsItsOwnAttachments:
    """«فایل هایی که پیوستش میخوام بکنم نباید قاتی فایل های پیوست قبلی باشه»."""

    async def _upload(self, client, headers, rid, name):
        return await client.post(
            f"/api/inspection/{rid}/files", headers=headers,
            files={"file": (name, b"nemoone", "text/plain")}, data={"caption": name})

    async def test_files_sent_with_a_note_belong_to_that_note(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        a = (await self._upload(client, auth_headers, rep["id"], "aval.txt")).json()
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "یادداشت دوم", "file_ids": [a["file"]["id"]]})
        assert r.status_code == 200, r.text
        notes = r.json()["report"]["notes"]
        files = r.json()["report"]["files"]
        mine = next(f for f in files if f["id"] == a["file"]["id"])
        assert mine["note_id"] == notes[-1]["id"], "the file did not join its note"

    async def test_the_original_files_stay_with_the_original_report(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        first = (await self._upload(client, auth_headers, rep["id"], "asli.txt")).json()
        second = (await self._upload(client, auth_headers, rep["id"], "peygiri.txt")).json()
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "پیگیری", "file_ids": [second["file"]["id"]]})
        files = {f["id"]: f for f in r.json()["report"]["files"]}
        assert files[second["file"]["id"]]["note_id"], "the follow-up's file was not tagged"
        assert not files[first["file"]["id"]]["note_id"], (
            "the ORIGINAL report's file was swept into the follow-up")

    async def test_a_later_note_cannot_steal_an_earlier_note_s_file(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        up = (await self._upload(client, auth_headers, rep["id"], "male-man.txt")).json()
        fid = up["file"]["id"]
        first = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                                  json={"text": "یکم", "file_ids": [fid]})
        owner_note = first.json()["report"]["notes"][-1]["id"]
        second = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                                   json={"text": "دوم", "file_ids": [fid]})
        got = next(f for f in second.json()["report"]["files"] if f["id"] == fid)
        assert got["note_id"] == owner_note, "a later note pulled a file off an earlier one"

    async def test_a_file_from_another_sheet_cannot_be_claimed(self, client, auth_headers):
        mine = await _sheet(client, auth_headers)
        theirs = await _sheet(client, auth_headers, "برگهٔ دیگر")
        up = (await self._upload(client, auth_headers, theirs["id"], "beganeh.txt")).json()
        r = await client.post(f"/api/inspection/{mine['id']}/notes", headers=auth_headers,
                              json={"text": "تلاش", "file_ids": [up["file"]["id"]]})
        assert r.status_code == 200
        assert not any(f["id"] == up["file"]["id"] for f in r.json()["report"]["files"])


class TestWhenWillItComeForThisOne:
    """v168 — «وقتی دکمه فوری میزنم باید ناظر بگه چند دقیقه دیگه میره سراغش».

    The countdown is measured from the round's own knocks, not written into the
    code, because the schedule lives in a Routine this server cannot read. These
    tests are about the WIRING — that the knock is really recorded and that the
    answer really follows it; the arithmetic has its own pure tests in
    `test_supervisor_rounds.py`.
    """

    async def test_pressing_urgent_answers_with_when(self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/urgent", headers=auth_headers)
        assert r.status_code == 200, r.text
        nxt = r.json()["next_round"]
        # An instant, not a duration: the page renders it in the owner's OWN
        # local time, which is the thing they asked for.
        assert datetime.fromisoformat(nxt["at"]).tzinfo is not None
        assert nxt["in_minutes"] == pytest.approx(nxt["in_seconds"] / 60, abs=1)
        assert nxt["in_seconds"] >= 0

    async def test_with_nothing_watched_yet_it_admits_it_is_assuming(
            self, client, auth_headers):
        rep = await _sheet(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/urgent", headers=auth_headers)
        assert r.json()["next_round"]["basis"] == "assumed"

    async def test_the_round_claiming_the_queue_is_what_records_a_knock(
            self, client, auth_headers, monkeypatch, test_user, db_session):
        """The claim is made on EVERY run, empty queue included — that is what
        makes it a clock. An empty queue must still count as «it came»."""
        from app.models.system_setting import SystemSetting
        from app.routers.inspection import ROUND_LOG_KEY
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        r = await client.post("/api/inspection/urgent/claim", headers=auth_headers,
                              json={"by": "routine"})
        assert r.status_code == 200 and r.json()["report"] is None      # empty queue
        row = (await db_session.execute(select(SystemSetting).where(
            SystemSetting.key == ROUND_LOG_KEY))).scalar_one_or_none()
        assert row is not None and json.loads(row.value)

    async def test_the_owner_opening_the_page_does_not_count_as_a_round(
            self, client, auth_headers, db_session):
        """Only the supervisor's claim is a knock. If merely reading the queue
        counted, the owner refreshing the board would forge a heartbeat and the
        countdown would point at a round that never happens."""
        from app.models.system_setting import SystemSetting
        from app.routers.inspection import ROUND_LOG_KEY
        await client.get("/api/inspection/urgent", headers=auth_headers)
        row = (await db_session.execute(select(SystemSetting).where(
            SystemSetting.key == ROUND_LOG_KEY))).scalar_one_or_none()
        assert row is None

    async def test_once_watched_the_estimate_says_so(
            self, client, auth_headers, monkeypatch, test_user, db_session):
        from app.models.system_setting import SystemSetting
        from app.routers.inspection import ROUND_LOG_KEY
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        seen = [now - timedelta(hours=3), now - timedelta(hours=2), now - timedelta(hours=1)]
        db_session.add(SystemSetting(
            key=ROUND_LOG_KEY, value=json.dumps([s.isoformat() for s in seen])))
        await db_session.commit()
        rep = await _sheet(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/urgent", headers=auth_headers)
        nxt = r.json()["next_round"]
        # v179 — the last knock was exactly one hour ago, so this very minute IS the
        # slot and nothing has knocked yet: «در راه» (due) is the honest answer, not
        # «next hour». Either way it is a measured estimate on the observed minute.
        assert nxt["basis"] in ("observed", "due")
        assert nxt["every_minutes"] == 60
        # the next one lands on the minute the round has been landing on
        assert datetime.fromisoformat(nxt["at"]).minute == now.minute

    async def test_the_fast_queue_carries_it_too(self, client, auth_headers):
        """So the board can show «ناظر ساعت … می‌آید» without a second call."""
        body = (await client.get("/api/inspection/urgent", headers=auth_headers)).json()
        assert "next_round" in body and body["next_round"]["in_seconds"] >= 0
