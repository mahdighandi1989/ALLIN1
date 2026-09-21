"""v125 — memory guards on the AI-import pipeline.

The instance was OOM-killed mid-import and Render restarted it. These tests pin
the three fixes so the failure modes cannot come back:

  1. only ONE extraction runs at a time per worker (uploads queue, not stack);
  2. boot-time recovery never loads every stuck job's stored upload at once, nor
     re-spawns them all concurrently — it resumes at most a few, one by one;
  3. an upload too big to keep is still imported, just not stored for resume.
"""
import asyncio
import json

import pytest

from app.models.customer import Customer
from app.models.import_job import ImportJob
from app.routers import imports as imports_router

from tests.test_doc_import import _draft_docx, _poll

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def test_only_one_extraction_runs_at_a_time(monkeypatch):
    """Two jobs launched together must NOT overlap — their peak memory would add up."""
    live = 0
    peak = 0

    async def fake_inner(job_id, data, fname, mime, model_id, username, instructions=""):
        nonlocal live, peak
        live += 1
        peak = max(peak, live)
        await asyncio.sleep(0.05)
        live -= 1

    monkeypatch.setattr(imports_router, "_run_import_job_inner", fake_inner)
    imports_router._EXTRACT_SEM = None          # rebuild on this loop
    await asyncio.gather(*[
        imports_router._run_import_job(f"j{i}", b"x", "f.pdf", "application/pdf", None, "u")
        for i in range(4)
    ])
    assert peak == 1, f"{peak} extractions overlapped — the semaphore is not holding"


async def test_boot_recovery_does_not_load_every_stored_upload_at_once(db_session, monkeypatch):
    """The old code selected whole ORM rows (every blob in RAM) and spawned them
    all concurrently — after an OOM restart that re-ran the killer workload
    several times over. Recovery must be serial and lazy."""
    blob = b"%PDF-1.4 " + b"0" * 2048
    for i in range(3):
        db_session.add(ImportJob(id=f"mem{i}", status="running", filename=f"f{i}.pdf",
                                 username="tester", mime="application/pdf", attempts=1,
                                 file_data=blob))
    await db_session.commit()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _reuse():
        yield db_session

    order: list = []
    live = 0
    peak = 0

    async def fake_run(job_id, data, fname, mime, model_id, username, instructions=""):
        nonlocal live, peak
        live += 1
        peak = max(peak, live)
        order.append(job_id)
        assert data, "the blob must be loaded for the job that is actually running"
        await asyncio.sleep(0.01)
        live -= 1

    captured: list = []

    async def capture(jobs):
        captured.append(list(jobs))
        await imports_router._run_resume_driver(jobs)

    monkeypatch.setattr(imports_router, "_job_session", _reuse)
    monkeypatch.setattr(imports_router, "_run_import_job", fake_run)
    monkeypatch.setattr(imports_router, "_spawn_resume_driver", capture)

    errored = await imports_router.fail_orphaned_jobs()

    assert errored == 0
    # the queue carries METADATA only — no file bytes ride along in memory
    assert captured and len(captured[0]) == 3
    for entry in captured[0]:
        assert not any(isinstance(x, (bytes, bytearray)) for x in entry)
    assert peak == 1, "resumed jobs ran concurrently"
    assert order == ["mem0", "mem1", "mem2"], order


async def test_boot_recovery_caps_how_many_jobs_it_resumes(db_session, monkeypatch):
    """A long backlog must not queue hours of heavy work onto a just-restarted
    instance; past the cap a job gets the honest re-upload error instead."""
    monkeypatch.setattr(imports_router, "_MAX_RESUME_PER_BOOT", 2)
    for i in range(5):
        db_session.add(ImportJob(id=f"cap{i}", status="running", filename=f"f{i}.pdf",
                                 username="tester", mime="application/pdf", attempts=1,
                                 file_data=b"%PDF-1.4 x"))
    await db_session.commit()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _reuse():
        yield db_session

    queued: list = []

    async def capture(jobs):
        queued.extend(j[0] for j in jobs)

    monkeypatch.setattr(imports_router, "_job_session", _reuse)
    monkeypatch.setattr(imports_router, "_spawn_resume_driver", capture)

    errored = await imports_router.fail_orphaned_jobs()

    assert queued == ["cap0", "cap1"]
    assert errored == 3
    row = await db_session.get(ImportJob, "cap4")
    assert row.status == "error" and row.file_data is None
    assert "سنگین" in row.detail_json


async def test_resume_driver_skips_a_job_that_finished_meanwhile(db_session, monkeypatch):
    """Between queueing and its turn a job may have been completed or pruned; its
    blob is gone and re-running it would be wrong."""
    db_session.add(ImportJob(id="gone", status="done", filename="f.pdf",
                             username="t", mime="application/pdf", attempts=1))
    await db_session.commit()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _reuse():
        yield db_session

    ran: list = []

    async def fake_run(job_id, *a, **k):
        ran.append(job_id)

    monkeypatch.setattr(imports_router, "_job_session", _reuse)
    monkeypatch.setattr(imports_router, "_run_import_job", fake_run)

    await imports_router._run_resume_driver([("gone", "f.pdf", "application/pdf", None, "t", "")])
    assert ran == []


async def test_oversized_upload_still_imports_but_is_not_stored_for_resume(
        client, auth_headers, db_session, import_inline, monkeypatch):
    """Capping the stored blob must never cost the import itself."""
    monkeypatch.setattr(imports_router, "_RESUME_STORE_MAX_BYTES", 10)   # anything real exceeds this
    db_session.add(Customer(account_no="115524", name="Old"))
    await db_session.commit()

    r = await client.post("/api/imports/analyze", headers=auth_headers,
                          files={"file": ("efco.docx", _draft_docx(), _DOCX_MIME)})
    assert r.status_code == 200, r.text
    job = await _poll(client, auth_headers, r.json()["job_id"])
    assert job["status"] == "done"           # the import itself is unaffected
    row = await db_session.get(ImportJob, r.json()["job_id"])
    assert row.file_data is None


async def test_small_upload_is_still_stored_for_resume(client, auth_headers, db_session, monkeypatch):
    """The resume capability itself must survive for normal-sized files."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _reuse():
        yield db_session

    async def _never(*a, **k):               # don't run it: we want to see the stored blob
        return None

    monkeypatch.setattr(imports_router, "_job_session", _reuse)
    monkeypatch.setattr(imports_router, "_spawn_job", _never)

    r = await client.post("/api/imports/analyze", headers=auth_headers,
                          files={"file": ("efco.docx", _draft_docx(), _DOCX_MIME)})
    assert r.status_code == 200, r.text
    row = await db_session.get(ImportJob, r.json()["job_id"])
    assert row.file_data, "a normal-sized upload must still be stored so a restart can resume it"
