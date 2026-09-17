"""Letter attachments + generic profile links + attachment extraction staging."""
import json

from sqlalchemy import select

from app.models.customer import Customer
from app.models.customer_link_rel import CustomerLink
from app.models.audit_log import AuditLog
from app.services.relationships import ensure_link, relationships_for_account
from app.services import letter_attachment_extract as lax


# ---------------- generic links ----------------

async def test_ensure_link_idempotent_and_bidirectional(db_session):
    db_session.add(Customer(account_no="L1", name="Alpha"))
    db_session.add(Customer(account_no="L2", name="Beta"))
    await db_session.commit()

    l1 = await ensure_link(db_session, "L1", "L2", kind="letter",
                           reason="نامهٔ ۱۸۲/۴/۳۷۹ هر دو را نام برده", source="letter", source_ref="ltr1")
    await db_session.commit()
    # same pair, same kind, REVERSED direction → the SAME row, no duplicate
    l2 = await ensure_link(db_session, "L2", "L1", kind="letter", reason="علت دیگر")
    await db_session.commit()
    assert l1.id == l2.id
    rows = (await db_session.execute(select(CustomerLink))).scalars().all()
    assert len(rows) == 1
    assert "علت دیگر" in rows[0].reason  # distinct new reason appended, first kept

    # visible on BOTH profiles with the exact reason
    r1 = await relationships_for_account(db_session, "L1")
    r2 = await relationships_for_account(db_session, "L2")
    g = [x for x in r1["given"] if x["kind"] == "link:letter"]
    rcv = [x for x in r2["received"] if x["kind"] == "link:letter"]
    assert g and g[0]["counterparty_account"] == "L2"
    assert "نامهٔ" in g[0]["detail"]["reason"]
    assert rcv and rcv[0]["counterparty_account"] == "L1"


async def test_ensure_link_rejects_self_and_blank_reason(db_session):
    assert await ensure_link(db_session, "X1", "X1", kind="other", reason="r") is None
    assert await ensure_link(db_session, "X1", "X2", kind="other", reason="  ") is None


async def test_apply_db_creates_links_stubs_and_audits(client, auth_headers, db_session):
    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={
        "items": [],
        "links": [{"account_no": "L10", "related_account": "L11", "kind": "guarantor",
                   "reason": "ضامن طبق پیوست نامه"}],
        "source_ref": "ltr-9",
    })
    assert r.status_code == 200, r.text
    assert r.json()["links_created"] == 1
    # stub customers created for both sides
    for acc in ("L10", "L11"):
        c = (await db_session.execute(select(Customer).where(Customer.account_no == acc))).scalar_one_or_none()
        assert c is not None
    # audited on BOTH profiles (global log + each profile's Logs tab)
    logs = (await db_session.execute(select(AuditLog).where(AuditLog.entity_type == "customer_link"))).scalars().all()
    assert {l.account_no for l in logs} == {"L10", "L11"}


# ---------------- letter attachments listing ----------------

async def test_letter_attachment_upload_and_list(client, auth_headers, db_session):
    db_session.add(Customer(account_no="L20", name="Att Co"))
    await db_session.commit()
    files = {"file": ("enclosure.pdf", b"%PDF-1.4 fake", "application/pdf")}
    up = await client.post("/api/crm/attachments/L20", headers=auth_headers,
                           files=files, data={"facility_id": "LTR-abc123", "notes": "پیوست نامه"})
    assert up.status_code == 200, up.text
    lst = await client.get("/api/letters/abc123/attachments", headers=auth_headers)
    assert lst.status_code == 200
    rows = lst.json()
    assert len(rows) == 1 and rows[0]["original_name"] == "enclosure.pdf"
    # a different letter sees nothing
    other = await client.get("/api/letters/zzz/attachments", headers=auth_headers)
    assert other.json() == []


# ---------------- extraction staging ----------------

def test_build_prompt_carries_letter_context():
    p = lax.build_prompt({"subject": "تمدید بیمه‌نامه", "account_no": "900", "customer_name": "Alpha"})
    assert "تمدید بیمه‌نامه" in p and "900" in p
    assert "relationships" in p and "NO summarizing" in p


async def test_stage_extraction_stages_fields_and_links(db_session):
    db_session.add(Customer(account_no="L30", name="Main Co"))
    await db_session.commit()
    extraction = {
        "customers": [
            {"account_no": "L30", "name": "Main Co",
             "fields": {"Trade License No": "TL-1", "city": "Dubai"}},
            {"account_no": "L31", "name": "Other Co", "fields": {"phone": "050"},
             "guarantors": [{"guarantor_name": "Mr. G", "guarantor_account": "L32"}]},
        ],
        "relationships": [
            {"from_account": "L30", "to_account": "L31", "kind": "letter",
             "reason": "هر دو در نامه نام برده شده‌اند"},
            {"from_account": "L31", "to_account": "L30", "kind": "letter",
             "reason": "duplicate reversed — must dedup"},
        ],
    }
    staged = await lax.stage_extraction(db_session, extraction, primary_account="L30",
                                        primary_name="Main Co", source_ref="enc.pdf")
    dbw = [s for s in staged if s["op"] == "db_write"]
    links = [s for s in staged if s["op"] == "link"]
    # fields staged for BOTH named accounts (keys normalized)
    assert any(s["account_no"] == "L30" and s["key"] == "trade_license_no" for s in dbw)
    assert any(s["account_no"] == "L31" and s["key"] == "phone" for s in dbw)
    # reversed duplicate relationship collapsed to ONE link; guarantor → link too
    letter_links = [l for l in links if l["kind"] == "letter"]
    assert len(letter_links) == 1
    assert any(l["kind"] == "guarantor" and l["account_no"] == "L32" for l in links)


async def test_extract_attachment_endpoint_stages(client, auth_headers, db_session, monkeypatch):
    db_session.add(Customer(account_no="L40", name="Host Co"))
    await db_session.commit()
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    up = await client.post("/api/crm/attachments/L40", headers=auth_headers,
                           files=files, data={"facility_id": "LTR-xyz"})
    att_id = up.json()["id"]

    async def fake_extract(db, **kw):
        assert kw["letter_ctx"]["subject"] == "موضوع تست"
        return {"ok": True, "model": "Stub", "chunk_errors": [],
                "customers": [{"account_no": "L40", "name": "Host Co", "fields": {"email": "a@b.c"}}],
                "relationships": [{"from_account": "L40", "to_account": "L41",
                                   "kind": "letter", "reason": "ذکر در پیوست"}]}

    import app.services.letter_attachment_extract as mod
    monkeypatch.setattr(mod, "extract_attachment", fake_extract)

    r = await client.post(f"/api/letter-ai/extract-attachment/{att_id}", headers=auth_headers,
                          json={"account_no": "L40", "customer_name": "Host Co", "subject": "موضوع تست"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    ops = {c["op"] for c in body["changes"]}
    assert "db_write" in ops and "link" in ops
    # ids are namespaced per attachment + source file recorded
    assert all(c["id"].startswith(att_id[-6:]) for c in body["changes"])
    assert all(c.get("source_file") == "doc.pdf" for c in body["changes"])


async def test_general_letter_attachment_never_attributes_to_general(client, auth_headers, db_session, monkeypatch):
    """A general letter's attachments live under the 'general' bucket — that must
    NEVER become a customer: unattributed facts are dropped, cited ones stage."""
    files = {"file": ("g.pdf", b"%PDF-1.4 fake", "application/pdf")}
    up = await client.post("/api/crm/attachments/general", headers=auth_headers,
                           files=files, data={"facility_id": "LTR-gen1"})
    att_id = up.json()["id"]

    async def fake_extract(db, **kw):
        assert kw["letter_ctx"]["account_no"] == ""   # general → no primary
        return {"ok": True, "model": "Stub", "chunk_errors": [],
                "customers": [
                    {"account_no": "", "name": "", "fields": {"city": "Dubai"}},      # unattributed → dropped
                    {"account_no": "G77", "name": "Cited Co", "fields": {"phone": "050"}},  # cited → staged
                ], "relationships": []}

    import app.services.letter_attachment_extract as mod
    monkeypatch.setattr(mod, "extract_attachment", fake_extract)

    r = await client.post(f"/api/letter-ai/extract-attachment/{att_id}", headers=auth_headers, json={})
    assert r.status_code == 200, r.text
    changes = r.json()["changes"]
    accounts = {c.get("account_no") for c in changes if c["op"] == "db_write"}
    assert "general" not in accounts and "" not in accounts
    assert "G77" in accounts


async def test_text_attachment_extraction_path(db_session, monkeypatch):
    """Plain-text attachments extract through the chunked text path; the prompt
    carries the strengthened relationship rules (explicit-only, quoted reason)."""
    import json as _json
    from app.ai import inference as inf

    captured = {}

    async def fake_complete(db, prompt, **kw):
        captured["prompt"] = prompt
        return {"ok": True, "model": "Stub", "error": None, "text": _json.dumps({
            "customers": [{"account_no": "T90", "name": "Text Co", "fields": {"city": "Ajman"}}],
            "relationships": [],
        }, ensure_ascii=False)}

    monkeypatch.setattr(inf, "complete", fake_complete)
    res = await lax.extract_attachment(
        db_session, data="متن نامه دربارهٔ حساب T90".encode("utf-8"),
        filename="notes.txt", mimetype="text/plain",
        letter_ctx={"subject": "s", "account_no": "T90", "customer_name": ""},
    )
    assert res["ok"] is True
    assert res["customers"][0]["account_no"] == "T90"
    p = captured["prompt"]
    assert "PLAIN-TEXT" in p
    assert "Record ONLY relationships the document explicitly states" in p
    assert "QUOTE or precisely restate" in p


async def test_extraction_kb_items_staged_and_no_account_data(db_session):
    """v69: a file with NO account-keyed rows is not a scary model error —
    its general/reference knowledge is staged as kb_write items instead, and
    the truly-empty case gets the specific no_account_data code."""
    from app.services import letter_attachment_extract as lax

    staged = await lax.stage_extraction(
        db_session,
        {"customers": [], "relationships": [], "kb_items": [
            {"topic": "بخشنامهٔ نرخ کارمزد", "category": "بخشنامه",
             "content": "بر اساس بخشنامهٔ ۱۴۰۵/۱۲۳ نرخ کارمزد صدور ضمانت‌نامه ۲٪ تعیین شد.",
             "source_note": "صفحهٔ ۱"},
            {"topic": "بخشنامهٔ نرخ کارمزد", "category": "بخشنامه",
             "content": "بر اساس بخشنامهٔ ۱۴۰۵/۱۲۳ نرخ کارمزد صدور ضمانت‌نامه ۲٪ تعیین شد.",
             "source_note": "تکراری"},
            {"topic": "x", "category": "", "content": "کوتاه", "source_note": ""},
        ]},
        primary_account="", primary_name="", source_ref="گزارش شعب.xlsx",
    )
    kb = [s for s in staged if s["op"] == "kb_write"]
    assert len(kb) == 1  # deduped + too-short dropped
    assert kb[0]["applicable"] is True and kb[0]["topic"] == "بخشنامهٔ نرخ کارمزد"
    assert "گزارش شعب.xlsx" in kb[0]["detail"]

    # kb_items instruction + the "no data is not an error" line reach the prompt
    p = lax.build_prompt({"subject": "س", "account_no": "1", "customer_name": "ش"})
    assert "kb_items" in p and "NOT an error" in p


# ---------------- v121: nested collections reach the DB (Import parity) ----------------

async def test_stage_extraction_stages_nested_collections(db_session):
    """Facilities / mortgaged properties / partners / security used to be read by
    the shared import prompt and then dropped (only scalars survived). They must
    now come back as their own reviewable `entity_write` rows."""
    db_session.add(Customer(account_no="L40", name="Nested Co"))
    await db_session.commit()
    extraction = {"customers": [{
        "account_no": "L40", "name": "Nested Co",
        "fields": {"city": "Dubai"},
        "facilities": [{"facility_type": "overdraft", "amount": "500000", "currency": "AED"}],
        "properties": [{"prop_type": "apartment", "mortgage_deed_no": "638/140",
                        "plate_no": "1/16553", "address": "Tehran"}],
        "partners": [{"name": "Ms. P", "role": "shareholder", "share_pct": "40"}],
        "security": [{"type": "Underlien Deposits", "for_facility": "OD", "amount": "100000"}],
    }]}
    staged = await lax.stage_extraction(db_session, extraction, primary_account="L40",
                                        primary_name="Nested Co", source_ref="sanction.pdf")
    ents = [s for s in staged if s["op"] == "entity_write"]
    kinds = {e["entity"] for e in ents}
    assert kinds == {"facility", "property", "partner", "security"}
    # every row is account-scoped, carries the raw payload and a readable summary
    assert all(e["account_no"] == "L40" and e["payload"] and e["applicable"] for e in ents)
    fac = next(e for e in ents if e["entity"] == "facility")
    assert "overdraft" in fac["title"] and "500000" in fac["title"]
    assert fac["entity_key"] == "facilities"
    prop = next(e for e in ents if e["entity"] == "property")
    assert prop["payload"]["mortgage_deed_no"] == "638/140"
    # the flat field still goes through the ordinary gate — unchanged behaviour
    assert any(s["op"] == "db_write" and s["key"] == "city" for s in staged)


async def test_stage_extraction_never_guesses_an_owner_for_nested_records(db_session):
    """With no account on the entry AND no primary account (a «general» letter),
    a facility/property must NOT be attributed to anyone."""
    extraction = {"customers": [{
        "name": "Unknown Co", "fields": {},
        "facilities": [{"facility_type": "loan", "amount": "1000"}],
    }]}
    staged = await lax.stage_extraction(db_session, extraction, primary_account="",
                                        primary_name="", source_ref="x.pdf")
    assert not [s for s in staged if s["op"] == "entity_write"]


async def test_apply_db_writes_nested_collections(client, auth_headers, db_session):
    """The approved rows are persisted by the IMPORT page's own writer, so the
    facility/property really land in their tables."""
    from app.models.facility import Facility
    from app.models.profile_entities import MortgagedProperty

    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={
        "items": [], "source_ref": "ltr-9",
        "entities": [
            {"account_no": "L41", "customer_name": "Apply Co", "entity_key": "facilities",
             "payload": {"facility_type": "loan", "amount": "250000", "currency": "AED"}},
            {"account_no": "L41", "customer_name": "Apply Co", "entity_key": "properties",
             "payload": {"prop_type": "villa", "mortgage_deed_no": "12/9", "address": "Dubai"}},
        ],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] and not body.get("entity_errors")
    assert body["entity_counts"].get("facilities_added") == 1
    assert body["entity_counts"].get("properties_added") == 1

    cust = (await db_session.execute(select(Customer).where(Customer.account_no == "L41"))).scalar_one()
    facs = (await db_session.execute(select(Facility).where(Facility.customer_id == cust.id))).scalars().all()
    assert len(facs) == 1 and str(facs[0].facility_type.value if hasattr(facs[0].facility_type, "value") else facs[0].facility_type) == "loan"
    props = (await db_session.execute(select(MortgagedProperty).where(MortgagedProperty.account_no == "L41"))).scalars().all()
    assert len(props) == 1 and props[0].mortgage_deed_no == "12/9"


async def test_apply_db_ignores_unknown_entity_keys(client, auth_headers):
    """Only the whitelisted collections may be written — a made-up key is a no-op,
    never an error and never a stray table write."""
    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={
        "items": [],
        "entities": [{"account_no": "L42", "entity_key": "customers",
                      "payload": {"name": "nope"}}],
    })
    assert r.status_code == 200
    assert r.json()["entity_counts"] == {}


# ---------------- v121 (ب): batch extraction as a background job ----------------

async def test_attachment_batch_job_queues_and_polls(client, auth_headers, monkeypatch, import_inline):
    """The batch endpoint returns a job id immediately; the poll endpoint reports
    live progress and finally the accumulated staged changes."""
    from app.routers import letter_ai as la_router

    calls: list = []

    async def fake_extract(att_id, payload, request, db, user):
        calls.append(att_id)
        return {"ok": True, "file": f"{att_id}.pdf",
                "changes": [{"id": f"c-{att_id}", "op": "db_write", "category": "db_extract",
                             "field": "city", "account_no": "B1", "key": "city",
                             "value": "Dubai", "applicable": True}],
                "chunk_errors": []}

    monkeypatch.setattr(la_router, "_extract_one_attachment", fake_extract)

    async def _inline(job_id, ids, data, username):
        await la_router._run_attachment_batch(job_id, ids, data, username)

    monkeypatch.setattr(la_router, "_spawn_attachment_batch", _inline)

    r = await client.post("/api/letter-ai/extract-attachments-job", headers=auth_headers,
                          json={"attachment_ids": ["a1", "a2", "a3"], "account_no": "B1"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] and body["total"] == 3
    job_id = body["job_id"]

    p = await client.get(f"/api/letter-ai/attachment-job/{job_id}", headers=auth_headers)
    assert p.status_code == 200
    st = p.json()
    assert st["status"] == "done", st
    assert st["done"] == 3 and st["total"] == 3
    assert len(st["changes"]) == 3
    assert calls == ["a1", "a2", "a3"]          # strictly sequential, in order
    assert all(c["source_file"] for c in st["changes"])


async def test_attachment_batch_job_isolates_one_bad_file(client, auth_headers, monkeypatch, import_inline):
    """A file that blows up becomes ONE error line — the rest still extract."""
    from app.routers import letter_ai as la_router

    async def flaky(att_id, payload, request, db, user):
        if att_id == "bad":
            raise RuntimeError("boom")
        return {"ok": True, "file": att_id, "changes": [], "chunk_errors": []}

    monkeypatch.setattr(la_router, "_extract_one_attachment", flaky)

    async def _inline(job_id, ids, data, username):
        await la_router._run_attachment_batch(job_id, ids, data, username)

    monkeypatch.setattr(la_router, "_spawn_attachment_batch", _inline)
    r = await client.post("/api/letter-ai/extract-attachments-job", headers=auth_headers,
                          json={"attachment_ids": ["ok1", "bad", "ok2"]})
    job_id = r.json()["job_id"]
    st = (await client.get(f"/api/letter-ai/attachment-job/{job_id}", headers=auth_headers)).json()
    assert st["status"] == "done"          # the batch itself did NOT fail
    assert st["done"] == 3
    assert any("boom" in e for e in st["errors"])


async def test_attachment_batch_job_rejects_empty_and_unknown(client, auth_headers):
    r = await client.post("/api/letter-ai/extract-attachments-job", headers=auth_headers,
                          json={"attachment_ids": []})
    assert r.status_code == 422
    r = await client.get("/api/letter-ai/attachment-job/NOPE", headers=auth_headers)
    assert r.status_code == 404
