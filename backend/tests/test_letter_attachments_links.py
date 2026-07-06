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
