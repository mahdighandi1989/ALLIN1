"""v106 — import jobs survive instance restarts: the upload is stored WITH the
job row, boot-time reconciliation RESUMES interrupted jobs from those bytes
(attempt-capped so a killer file can't crash-loop the instance), and the blob is
cleared the moment a job finishes."""
import json

from app.models.customer import Customer
from app.models.import_job import ImportJob
from app.routers import imports as imports_router

from tests.test_doc_import import _draft_docx, _poll

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def test_orphaned_job_with_stored_upload_resumes(db_session, import_inline):
    db_session.add(Customer(account_no="115524", name="Old"))
    db_session.add(ImportJob(id="rjob1", status="running", filename="efco.docx",
                             username="tester", mime=_DOCX_MIME, attempts=1,
                             file_data=_draft_docx()))
    await db_session.commit()

    errored = await imports_router.fail_orphaned_jobs()
    assert errored == 0

    row = await db_session.get(ImportJob, "rjob1")
    assert row.status == "done", (row.status, row.detail_json)
    assert row.attempts == 2
    assert row.file_data is None            # finished ⇒ stored upload cleared
    result = json.loads(row.result_json)
    assert result["ok"] and result["model"] == "Word draft parser"


async def test_orphaned_job_beyond_attempt_cap_errors_honestly(db_session, import_inline):
    db_session.add(ImportJob(id="rjob2", status="running", filename="big.pdf",
                             username="tester", mime="application/pdf", attempts=2,
                             file_data=b"%PDF-1.4 fake"))
    await db_session.commit()

    errored = await imports_router.fail_orphaned_jobs()
    assert errored == 1

    row = await db_session.get(ImportJob, "rjob2")
    assert row.status == "error" and row.http_status == 503
    assert "سنگین" in row.detail_json       # the honest split-the-file message
    assert row.file_data is None


async def test_legacy_orphan_without_blob_keeps_old_error(db_session, import_inline):
    db_session.add(ImportJob(id="rjob3", status="running", filename="x.pdf",
                             username="tester"))
    await db_session.commit()

    errored = await imports_router.fail_orphaned_jobs()
    assert errored == 1
    row = await db_session.get(ImportJob, "rjob3")
    assert row.status == "error"
    assert "دوباره فایل را بارگذاری" in row.detail_json


async def test_analyze_stores_upload_and_clears_on_finish(client, auth_headers, db_session, import_inline):
    db_session.add(Customer(account_no="115524", name="Old"))
    await db_session.commit()
    r = await client.post("/api/imports/analyze", headers=auth_headers,
                          files={"file": ("efco.docx", _draft_docx(), _DOCX_MIME)})
    assert r.status_code == 200, r.text
    job_id = r.json()["job_id"]
    job = await _poll(client, auth_headers, job_id)
    assert job["status"] == "done"
    row = await db_session.get(ImportJob, job_id)
    assert row.attempts == 1 and row.mime == _DOCX_MIME
    assert row.file_data is None            # cleared after the inline run finished