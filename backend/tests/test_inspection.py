"""v141 — «نظارت و سرکشی».

The whole point of this feature is that the owner can trust what a sheet says
from across the room. So the tests are mostly about the REFUSALS: the three
things the sibling project learned the hard way, now enforced instead of merely
documented.
"""
import pytest
from sqlalchemy import select

from app.models.inspection import (
    OUTCOME_FIXED, STATUS_ANSWERED, STATUS_APPROVED, STATUS_FILED, STATUS_OPEN,
    InspectionReport, sheet_glow,
)

PNG = ("data:image/png;base64,"
       "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

SPOT = {
    "page": "/customers", "page_label": "مشتریان",
    "section_id": "filters", "section_label": "فیلترها",
    "reopen": "/customers#filters",
    "dom_path": "section#filters > div.row > button",
    "covered_text": "جستجو · نوع حساب · شعبه",
    "rect": {"x": 10, "y": 20, "w": 300, "h": 120},
    "viewport": {"w": 1500, "h": 900},
}


async def _file(client, headers, text="دکمهٔ جستجو کار نمی‌کند", shot=PNG):
    r = await client.post("/api/inspection", headers=headers,
                          json={"text": text, "spot": SPOT, "shot": shot})
    assert r.status_code == 200, r.text
    return r.json()["report"]


class TestFilingASheet:
    async def test_the_sheet_carries_the_way_back_not_a_pixel_position(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        assert rep["reopen"] == "/customers#filters"
        assert rep["page"] == "/customers" and rep["section_label"] == "فیلترها"
        assert rep["covered_text"].startswith("جستجو")
        assert rep["status"] == STATUS_OPEN
        assert rep["number"] == 1

    async def test_the_headline_is_the_first_line(self, client, auth_headers):
        rep = await _file(client, auth_headers, text="خط اول\nخط دوم")
        assert rep["title"] == "خط اول"

    async def test_the_image_is_stored_out_of_the_row_and_served_on_demand(
            self, client, auth_headers):
        rep = await _file(client, auth_headers)
        sid = rep["notes"][0]["shot_id"]
        assert sid, "the owner's crop must be kept"
        # the list must not carry the bytes
        lst = (await client.get("/api/inspection", headers=auth_headers)).json()
        assert "base64" not in str(lst["reports"])
        img = await client.get(f"/api/inspection/shots/{sid}", headers=auth_headers)
        assert img.status_code == 200
        assert img.headers["content-type"].startswith("image/")

    @pytest.mark.parametrize("bad", [
        "https://evil.example/x.png",          # would be an SSRF
        "data:text/html;base64,PHNjcmlwdD4=",  # not an image
        "javascript:alert(1)",
    ])
    async def test_anything_that_is_not_an_image_data_url_is_dropped(
            self, client, auth_headers, bad):
        rep = await _file(client, auth_headers, shot=bad)
        assert rep["notes"][0]["shot_id"] is None

    async def test_an_empty_report_is_refused(self, client, auth_headers):
        r = await client.post("/api/inspection", headers=auth_headers,
                              json={"text": "   ", "spot": SPOT})
        assert r.status_code == 422


class TestTheColourCannotLie:
    """The sibling's worst failure: a wall of green sheets that meant nothing."""

    def test_a_reply_alone_is_not_green(self):
        glow = sheet_glow(STATUS_ANSWERED, [{"by": "reviewer", "outcome": "not-done"}])
        assert glow["outcome"] == "not-done"

    def test_a_claimed_fix_without_the_after_picture_shows_as_partial(self):
        glow = sheet_glow(STATUS_ANSWERED, [{"by": "reviewer", "outcome": OUTCOME_FIXED}])
        assert glow["outcome"] == "partial"
        assert "بدونِ تصویر" in glow["label"]

    def test_a_fix_with_its_picture_is_the_only_green(self):
        glow = sheet_glow(STATUS_ANSWERED,
                          [{"by": "reviewer", "outcome": OUTCOME_FIXED, "after_shot_id": "s1"}])
        assert glow["outcome"] == OUTCOME_FIXED

    def test_an_answer_from_before_outcomes_existed_is_not_green(self):
        glow = sheet_glow(STATUS_ANSWERED, [{"by": "reviewer", "text": "انجام شد"}])
        assert glow["key"] == "stale"

    def test_the_owners_tick_wins_over_everything(self):
        glow = sheet_glow(STATUS_APPROVED, [{"by": "reviewer", "outcome": "not-done"}])
        assert glow["key"] == STATUS_APPROVED


class TestEditingANote:
    """v152 — «باید بشه خود گزارش ادیت زد».

    Appending a correction leaves the wrong text at the TOP of the sheet, which
    is what the supervisor reads first. Editing fixes it in place — but a sheet
    is a record, so nothing is overwritten without trace.
    """

    async def test_the_owner_can_correct_their_own_report(self, client, auth_headers):
        rep = await _file(client, auth_headers, text="دکمه کار نمی‌کنه")
        nid = rep["notes"][0]["id"]
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{nid}",
                               headers=auth_headers, json={"text": "دکمهٔ جستجو کار نمی‌کند"})
        assert r.status_code == 200, r.text
        note = r.json()["report"]["notes"][0]
        assert note["text"] == "دکمهٔ جستجو کار نمی‌کند"
        # the sheet's headline follows the first note
        assert r.json()["report"]["title"] == "دکمهٔ جستجو کار نمی‌کند"

    async def test_the_original_is_kept_not_overwritten(self, client, auth_headers):
        """Quarantine, not delete — the same instinct as rule 2."""
        rep = await _file(client, auth_headers, text="اولین متن")
        nid = rep["notes"][0]["id"]
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{nid}",
                               headers=auth_headers, json={"text": "متنِ اصلاح‌شده"})
        note = r.json()["report"]["notes"][0]
        assert note["original_text"] == "اولین متن"
        assert note["edited_at"]

    async def test_editing_twice_keeps_the_FIRST_original(self, client, auth_headers):
        rep = await _file(client, auth_headers, text="نسخهٔ یک")
        nid = rep["notes"][0]["id"]
        for t in ("نسخهٔ دو", "نسخهٔ سه"):
            r = await client.patch(f"/api/inspection/{rep['id']}/notes/{nid}",
                                   headers=auth_headers, json={"text": t})
        note = r.json()["report"]["notes"][0]
        assert note["original_text"] == "نسخهٔ یک", "the first version is the one worth keeping"
        assert note["text"] == "نسخهٔ سه"

    async def test_an_empty_edit_is_refused(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        nid = rep["notes"][0]["id"]
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{nid}",
                               headers=auth_headers, json={"text": "   "})
        assert r.status_code == 422

    async def test_a_missing_note_is_404_not_a_silent_no_op(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/NOPE",
                               headers=auth_headers, json={"text": "x"})
        assert r.status_code == 404

    async def test_a_filed_sheet_cannot_be_rewritten(self, client, auth_headers, db_session):
        rep = await _file(client, auth_headers)
        row = (await db_session.execute(select(InspectionReport).where(
            InspectionReport.id == rep["id"]))).scalar_one()
        row.status = STATUS_FILED
        await db_session.commit()
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{rep['notes'][0]['id']}",
                               headers=auth_headers, json={"text": "بعداً"})
        assert r.status_code == 422
        assert "بایگانی" in r.json()["detail"]

    async def test_the_supervisor_cannot_rewrite_the_owners_report(
            self, client, auth_headers, monkeypatch, test_user):
        """Otherwise the conversation stops being evidence of anything."""
        rep = await _file(client, auth_headers, text="متنِ مالک")
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{rep['notes'][0]['id']}",
                               headers=auth_headers, json={"text": "چیزِ دیگری"})
        assert r.status_code == 403

    async def test_the_owner_cannot_rewrite_the_supervisors_answer(
            self, client, auth_headers, monkeypatch, test_user):
        rep = await _file(client, auth_headers)
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        ans = (await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                                 json={"text": "بررسی شد", "outcome": "not-done"})).json()["report"]
        nid = ans["notes"][-1]["id"]
        monkeypatch.delenv("SUPERVISOR_API_USER")
        r = await client.patch(f"/api/inspection/{rep['id']}/notes/{nid}",
                               headers=auth_headers, json={"text": "انجام شد!"})
        assert r.status_code == 403


class TestPreciseGeometry:
    """v150 — «مختصاتِ فوق‌العاده دقیقِ جایی که کادر کشیده شده و ابعاد».

    The sheet used to carry only the way back. It now also carries where the box
    was, measured so that a highlight can be drawn on the same spot later — and
    so that the supervisor knows which control the owner actually meant.
    """

    GEOM = {
        "doc": {"x": 100.5, "y": 450.25, "w": 200, "h": 80},
        "view": {"x": 100.5, "y": 50.25, "w": 200, "h": 80},
        "scroll": {"x": 0, "y": 400}, "viewport": {"w": 1200, "h": 800},
        "doc_size": {"w": 1200, "h": 5000}, "dpr": 2,
        "anchor": {"path": "body > div:nth-of-type(2) > section",
                   "rect": {"x": 50, "y": 400, "w": 400, "h": 160},
                   "rel": {"x": 0.1263, "y": 0.3141, "w": 0.5, "h": 0.5}},
    }

    async def test_the_geometry_comes_back_exactly_as_sent(self, client, auth_headers):
        r = await client.post("/api/inspection", headers=auth_headers,
                              json={"text": "اینجا", "spot": {**SPOT, "geometry": self.GEOM}})
        assert r.status_code == 200, r.text
        got = r.json()["report"]["geometry"]
        assert got == self.GEOM, "a coordinate that changes in transit is not precise"
        # floats survive — rounding 450.25 to 450 would move the highlight
        assert got["doc"]["y"] == 450.25
        assert got["anchor"]["rel"]["x"] == 0.1263

    async def test_the_old_address_fields_are_untouched(self, client, auth_headers):
        """The geometry is an ADDITION. The way back is still what a supervisor
        navigates by, and nothing about it changed."""
        r = await client.post("/api/inspection", headers=auth_headers,
                              json={"text": "x", "spot": {**SPOT, "geometry": self.GEOM}})
        rep = r.json()["report"]
        assert rep["reopen"] == "/customers#filters"
        assert rep["rect"] == SPOT["rect"] and rep["viewport"] == SPOT["viewport"]

    async def test_a_sheet_without_geometry_is_still_a_valid_sheet(
            self, client, auth_headers):
        """An older client, or a browser where no selector round-tripped."""
        rep = await _file(client, auth_headers)
        assert rep["geometry"] is None
        assert rep["reopen"] == "/customers#filters"

    async def test_the_geometry_survives_a_reply(self, client, auth_headers):
        rep = (await client.post("/api/inspection", headers=auth_headers,
                                 json={"text": "x", "spot": {**SPOT, "geometry": self.GEOM}})).json()["report"]
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "دیدم"})
        assert r.json()["report"]["geometry"] == self.GEOM

    async def test_it_is_listed_so_the_overlay_can_draw_without_extra_calls(
            self, client, auth_headers):
        await client.post("/api/inspection", headers=auth_headers,
                          json={"text": "x", "spot": {**SPOT, "geometry": self.GEOM}})
        body = (await client.get("/api/inspection", headers=auth_headers)).json()
        assert body["reports"][0]["geometry"] == self.GEOM


class TestTheSupervisorSide:
    @pytest.fixture(autouse=True)
    def _as_supervisor(self, monkeypatch, test_user):
        """The supervisor signs in as its own account; notes it writes are
        `reviewer` notes and it is refused the owner's tick."""
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)

    async def test_its_note_is_a_reviewer_note_and_moves_the_sheet_on(
            self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "بررسی شد", "outcome": "not-done"})
        assert r.status_code == 200, r.text
        got = r.json()["report"]
        assert got["notes"][-1]["by"] == "reviewer"
        assert got["status"] == STATUS_ANSWERED

    async def test_claiming_fixed_without_the_after_picture_is_refused(
            self, client, auth_headers):
        """Being wrong about a fix is worse than being slow: the owner stops
        looking at a green sheet."""
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "درستش کردم", "outcome": OUTCOME_FIXED})
        assert r.status_code == 422
        assert "تصویرِ بعدش" in r.json()["detail"]

    async def test_claiming_fixed_with_the_picture_is_accepted(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "درستش کردم", "outcome": OUTCOME_FIXED,
                                    "after_shot": PNG, "commits": ["abc1234"]})
        assert r.status_code == 200, r.text
        note = r.json()["report"]["notes"][-1]
        assert note["after_shot_id"] and note["commits"] == ["abc1234"]
        assert r.json()["report"]["glow"]["outcome"] == OUTCOME_FIXED

    async def test_it_cannot_tick_its_own_work(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/status", headers=auth_headers,
                              json={"status": STATUS_APPROVED})
        assert r.status_code == 403
        assert "فقط دستِ مالک" in r.json()["detail"]

    async def test_it_cannot_delete_a_sheet(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.delete(f"/api/inspection/{rep['id']}", headers=auth_headers)
        assert r.status_code == 403

    async def test_its_dependency_walk_is_kept_on_the_sheet(self, client, auth_headers):
        """The owner asked for this by name: «وقتی هر کاری بخواد بکنه
        وابستگی‌ها رو چک کنه». An answer with no dependency walk is an
        unreviewed answer."""
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "بررسی شد", "outcome": "partial",
                                    "dependencies": [
                                        {"name": "GET /api/customers", "status": "ok"},
                                        {"name": "صفحهٔ گزارش‌ها", "status": "missing",
                                         "note": "این فیلتر آنجا وجود ندارد"}]})
        assert r.status_code == 200, r.text
        deps = r.json()["report"]["dependencies"]
        assert len(deps) == 2 and deps[1]["status"] == "missing"


class TestTheOwnerSide:
    async def test_the_owner_ticks_and_the_next_round_archives_it(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        ok = await client.post(f"/api/inspection/{rep['id']}/status", headers=auth_headers,
                               json={"status": STATUS_APPROVED})
        assert ok.status_code == 200, ok.text
        filed = await client.post("/api/inspection/file", headers=auth_headers)
        assert filed.status_code == 200
        assert filed.json()["filed"] == 1
        one = (await client.get(f"/api/inspection/{rep['id']}", headers=auth_headers)).json()
        assert one["report"]["status"] == STATUS_FILED
        assert one["report"]["binder"]["number"] == 1

    async def test_a_filed_sheet_leaves_the_wall_but_is_still_readable(
            self, client, auth_headers):
        rep = await _file(client, auth_headers)
        await client.post(f"/api/inspection/{rep['id']}/status", headers=auth_headers,
                          json={"status": STATUS_APPROVED})
        await client.post("/api/inspection/file", headers=auth_headers)
        wall = (await client.get("/api/inspection", headers=auth_headers)).json()
        assert not wall["reports"]
        all_ = (await client.get("/api/inspection?include_filed=true",
                                 headers=auth_headers)).json()
        assert len(all_["reports"]) == 1

    async def test_writing_again_on_an_answered_sheet_re_opens_it(
            self, client, auth_headers, monkeypatch, test_user):
        """«اگر دستور اضافه‌تر داشتم می‌نویسم تا دوباره ببینه» — the sheet must
        go back into the supervisor's queue, not sit as «answered»."""
        rep = await _file(client, auth_headers)
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                          json={"text": "بررسی شد", "outcome": "partial"})
        monkeypatch.setenv("SUPERVISOR_API_USER", "somebody-else")
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "این هم اضافه کن"})
        assert r.json()["report"]["status"] == STATUS_OPEN

    async def test_an_owner_cannot_record_an_outcome(self, client, auth_headers):
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "درست شد", "outcome": OUTCOME_FIXED,
                                    "after_shot": PNG})
        assert r.status_code == 422


class TestTheQueue:
    async def test_it_separates_what_is_owed_from_what_waits_on_the_owner(
            self, client, auth_headers, monkeypatch, test_user):
        """v167 — this test used to answer the sheet with `not-done` and expect
        it to count as «waiting for the owner». That was the bug, not the
        contract: a sheet whose own hint reads «این برگه هنوز کارِ نکرده دارد»
        was not waiting on anybody, it was UNFINISHED, and nothing brought it
        back. `needs-owner` is the outcome that genuinely waits on a decision,
        so it is what this test uses now; the old shape is covered from the
        other side by `TestHalfDoneWorkComesBack`.
        """
        a = await _file(client, auth_headers, text="یک")
        await _file(client, auth_headers, text="دو")
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)
        await client.post(f"/api/inspection/{a['id']}/notes", headers=auth_headers,
                          json={"text": "با ساختار نمی‌خواند؛ گزینه‌ها: …",
                                "outcome": "needs-owner"})
        q = (await client.get("/api/inspection/queue", headers=auth_headers)).json()
        assert q["owed"] == 1 and q["waiting_for_owner"] == 1

    async def test_a_section_can_ask_for_only_its_own_sheets(self, client, auth_headers):
        await _file(client, auth_headers)
        mine = (await client.get("/api/inspection?reopen=/customers%23filters",
                                 headers=auth_headers)).json()
        other = (await client.get("/api/inspection?reopen=/facilities",
                                  headers=auth_headers)).json()
        assert len(mine["reports"]) == 1 and not other["reports"]

    async def test_it_requires_a_logged_in_user(self, client):
        assert (await client.get("/api/inspection")).status_code in (401, 403)


class TestTheSupervisorIsNamedOnTheSERVER:
    """The guard must not depend on the supervisor's own environment.

    `SUPERVISOR_API_USER` lives wherever the supervisor RUNS. If the guard read
    only that, then a server that had never heard of it would treat the
    supervisor as an ordinary user — fail-closed for outcomes (fine) but
    fail-OPEN for the owner's tick (not fine). So the server carries the name.
    """

    async def test_the_editable_setting_wins_over_the_environment(
            self, client, auth_headers, db_session, monkeypatch, test_user):
        from app.models.system_setting import SystemSetting

        monkeypatch.setenv("SUPERVISOR_API_USER", "someone-who-is-not-here")
        db_session.add(SystemSetting(key="supervisor_username", value=test_user.username))
        await db_session.commit()
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "بررسی شد", "outcome": "not-done"})
        assert r.status_code == 200, r.text
        assert r.json()["report"]["notes"][-1]["by"] == "reviewer"

    async def test_with_nobody_named_no_outcome_can_be_recorded(
            self, client, auth_headers, monkeypatch):
        """Fail-closed: an unconfigured server cannot be talked into accepting a
        verdict from just anyone."""
        monkeypatch.delenv("SUPERVISOR_API_USER", raising=False)
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "درست شد", "outcome": "fixed", "after_shot": PNG})
        assert r.status_code == 422


class TestHalfDoneWorkComesBack:
    """v167 — «نیمه‌کاره» یعنی بقیه‌اش مانده، پس باید برگردد.

    The owner asked it plainly: «ایا این نیمه کاره یعنی سیستم و ناظر بعدا ادامه
    کارها رو روش انجام خواهند داد؟ ... یادش میمونه؟» It did not. The moment the
    supervisor wrote `partial`, the sheet left `owed`, the round exited clean,
    and the remainder was owed to nobody — the label remembered, the queue did
    not. A sheet is finished only when the work is DONE WITH PROOF, or parked on
    the owner's decision.
    """

    @pytest.fixture(autouse=True)
    def _as_supervisor(self, monkeypatch, test_user):
        monkeypatch.setenv("SUPERVISOR_API_USER", test_user.username)

    async def _answered(self, client, headers, **note):
        rep = await _file(client, headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=headers, json=note)
        assert r.status_code == 200, r.text
        return rep

    async def _queue(self, client, headers):
        return (await client.get("/api/inspection/queue", headers=headers)).json()

    async def test_a_half_done_sheet_is_still_owed_next_round(self, client, auth_headers):
        rep = await self._answered(client, auth_headers,
                                   text="نیمی‌اش شد", outcome="partial")
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 1
        assert q["unfinished"] == 1 and q["unanswered"] == 0
        assert q["unfinished_numbers"] == [rep["number"]]
        assert q["waiting_for_owner"] == 0

    async def test_a_sheet_that_was_not_done_comes_back_too(self, client, auth_headers):
        await self._answered(client, auth_headers, text="نشد چون…", outcome="not-done")
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 1 and q["unfinished"] == 1

    async def test_a_reply_with_no_outcome_at_all_is_not_finished_either(
            self, client, auth_headers):
        """A bare reply is not evidence of anything — the same rule `sheet_glow`
        already applies to the colour."""
        await self._answered(client, auth_headers, text="نگاه کردم")
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 1 and q["unfinished"] == 1

    async def test_a_proven_fix_is_finished_and_waits_for_the_owner(
            self, client, auth_headers):
        await self._answered(client, auth_headers, text="درست شد",
                             outcome=OUTCOME_FIXED, after_shot=PNG)
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 0 and q["unfinished"] == 0
        assert q["waiting_for_owner"] == 1

    async def test_a_claim_of_fixed_without_proof_never_reaches_the_queue(
            self, client, auth_headers):
        """Belt and braces: the API refuses it outright (see the sibling test),
        so «fixed» in the queue always means «fixed with a picture»."""
        rep = await _file(client, auth_headers)
        r = await client.post(f"/api/inspection/{rep['id']}/notes", headers=auth_headers,
                              json={"text": "شد", "outcome": OUTCOME_FIXED})
        assert r.status_code == 422
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 1 and q["unanswered"] == 1

    async def test_a_sheet_parked_on_the_owner_is_not_chased_every_round(
            self, client, auth_headers):
        """`needs-owner` is the ONE answer that stops the loop — otherwise a
        question the owner has not answered would be re-asked forever."""
        await self._answered(client, auth_headers,
                             text="با ساختار نمی‌خواند؛ دو گزینه: …",
                             outcome="needs-owner")
        q = await self._queue(client, auth_headers)
        assert q["owed"] == 0 and q["unfinished"] == 0
        assert q["waiting_for_owner"] == 1

    async def test_the_numbers_still_add_up(self, client, auth_headers):
        """Three sheets, one of each kind — the three counters must partition
        the live queue, or a round reports a total nobody can act on."""
        await self._answered(client, auth_headers, text="نیمه", outcome="partial")
        await self._answered(client, auth_headers, text="با مالک", outcome="needs-owner")
        await _file(client, auth_headers)                      # untouched
        q = await self._queue(client, auth_headers)
        assert q["unanswered"] == 1 and q["unfinished"] == 1 and q["waiting_for_owner"] == 1
        assert q["owed"] == 2
        assert len(q["reports"]) == q["unanswered"] + q["unfinished"] + q["waiting_for_owner"]


class TestABigPictureIsNotRefused:
    """v175 — «این خطایی که موقع ثبت گزارش میزنم و ریشه‌ای درست کن که محدودیتی نباشه».

    The owner pasted their own screenshot and the report came back «shot: String
    should have at most 1400000 characters» — about a megabyte of base64, smaller
    than an ordinary full-screen PNG. The best evidence this system can get was
    the one thing it turned away.

    The real fix is on the page (every picture is re-encoded before it is sent).
    What is held here is the server's half: a ceiling high enough that nothing
    the page sends can reach it, a refusal written in words if it ever does, and
    — the dangerous one — oversize never passing silently.
    """

    def _url(self, chars: int) -> str:
        head = "data:image/png;base64,"
        return head + "A" * (chars - len(head))

    async def test_a_picture_far_bigger_than_the_old_ceiling_is_accepted(
            self, client, auth_headers):
        """4 MB — three times what used to be refused, and an ordinary screenshot."""
        r = await client.post("/api/inspection", headers=auth_headers,
                              json={"text": "درستش کن", "spot": SPOT,
                                    "shot": self._url(4_000_000)})
        assert r.status_code == 200, r.text[:300]

    def test_the_ceiling_is_high_enough_that_the_page_cannot_reach_it(self):
        from app.routers.inspection import MAX_SHOT_BYTES
        # the page aims to stay under 3_000_000 (SHOT_MAX_CHARS); the server must
        # be comfortably above that, or the two race each other
        assert MAX_SHOT_BYTES >= 3_000_000 * 2

    async def test_past_the_ceiling_it_says_so_in_words_the_owner_can_act_on(
            self, client, auth_headers):
        from app.routers.inspection import MAX_SHOT_BYTES
        r = await client.post("/api/inspection", headers=auth_headers,
                              json={"text": "x", "spot": SPOT,
                                    "shot": self._url(MAX_SHOT_BYTES + 50)})
        assert r.status_code == 422
        body = r.text
        assert "تصویر بیش از حد بزرگ است" in body
        assert "String should have at most" not in body      # the old message

    async def test_oversize_is_never_dropped_in_silence(self, client, auth_headers):
        """THE DANGEROUS ONE. `_split_data_url` used to return None for a picture
        that was too big — exactly as it does for «this is not an image» — so a
        shot that got past the schema was thrown away without a word: the sheet
        filed with no picture and nobody was told."""
        from fastapi import HTTPException
        from app.routers.inspection import MAX_SHOT_BYTES, _split_data_url
        with pytest.raises(HTTPException) as e:
            _split_data_url(self._url(MAX_SHOT_BYTES + 10))
        assert e.value.status_code == 413

    def test_something_that_is_not_an_image_is_still_dropped_quietly(self):
        """Unchanged on purpose: «there was nothing to store» is not an error."""
        from app.routers.inspection import _split_data_url
        for junk in (None, "", "hello", "data:text/html;base64,AAA", 42):
            assert _split_data_url(junk) is None

    async def test_the_picture_really_is_stored_and_served_back(
            self, client, auth_headers):
        """A ceiling that accepts the request but loses the bytes would pass every
        test above and still fail the owner."""
        rep = (await client.post("/api/inspection", headers=auth_headers,
                                 json={"text": "با عکس", "spot": SPOT, "shot": PNG})).json()["report"]
        sid = rep["notes"][0]["shot_id"]
        assert sid
        got = await client.get(f"/api/inspection/shots/{sid}", headers=auth_headers)
        assert got.status_code == 200
        assert got.headers["content-type"].startswith("image/")
        assert len(got.content) > 0
