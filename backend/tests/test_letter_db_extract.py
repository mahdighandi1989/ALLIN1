"""The AI extract-to-DB path — the sensitive one that WRITES to customer profiles.

Locks the careful behavior the owner asked for:
- facts are attributed to the RIGHT customer (primary / account-cited / name-match),
- an unresolved customer (name only, no account, no match) is surfaced, NOT guessed,
- apply de-dups (same value → skip), respects date-staleness (older date → skip),
- a cited-but-missing customer gets a profile created,
- every write is audited against the account (global log + profile «Logs» tab).
"""
import json

import pytest
from sqlalchemy import select

from app.models.customer import Customer
from app.models.crm import CustomerProfile
from app.models.audit_log import AuditLog
from app.services import letter_assistant as la
from app.services import letter_db_extract as dbx


# ---------------- parse_db_writes (pure) ----------------

def test_parse_db_writes_extracts_and_dedups():
    raw = json.dumps({"changes": [
        {"op": "db_write", "account_no": "111", "customer_name": "A", "key": "Trade License No", "value": "TL-9"},
        {"op": "db_write", "account_no": "111", "customer_name": "A", "key": "trade_license_no", "value": "TL-9"},  # dup (key normalizes)
        {"op": "text_replace", "field": "body", "find": "x", "replace": "y"},  # not a db_write
        {"op": "db_write", "account_no": "", "customer_name": "B", "key": "city", "value": "Dubai"},
    ]}, ensure_ascii=False)
    out = la.parse_db_writes(raw)
    assert len(out) == 2
    assert out[0]["key"] == "trade_license_no" and out[0]["value"] == "TL-9"
    assert out[1]["customer_name"] == "B" and out[1]["account_no"] == ""


def test_parse_db_writes_skips_empty_key_or_value():
    raw = json.dumps({"changes": [
        {"op": "db_write", "account_no": "1", "key": "", "value": "x"},
        {"op": "db_write", "account_no": "1", "key": "city", "value": ""},
    ]})
    assert la.parse_db_writes(raw) == []


# ---------------- staging (read-only resolution) ----------------

async def test_stage_resolves_primary_and_flags_unresolved(db_session):
    db_session.add(Customer(account_no="900500", name="Primary Co", account_type="corporate"))
    await db_session.commit()
    raw = [
        {"account_no": "", "customer_name": "Primary Co", "key": "city", "value": "Dubai", "title": "", "detail": ""},
        {"account_no": "", "customer_name": "Unknown Person", "key": "phone", "value": "050", "title": "", "detail": ""},
        {"account_no": "", "customer_name": "", "key": "email", "value": "a@b.c", "title": "", "detail": ""},
    ]
    staged = await dbx.stage_db_writes(db_session, "900500", "Primary Co", raw)
    by = {s["key"]: s for s in staged}
    # matched the primary by name → applicable add
    assert by["city"]["op"] == "db_write" and by["city"]["account_no"] == "900500" and by["city"]["action"] == "add"
    # no customer, no account cited → defaults to the primary account
    assert by["email"]["account_no"] == "900500"
    # named someone unknown with no account → NOT guessed; surfaced as a note
    assert by["phone"]["op"] == "note" and by["phone"]["applicable"] is False


async def test_stage_add_update_skip(db_session):
    db_session.add(Customer(account_no="900600", name="Acme", account_type="corporate"))
    db_session.add(CustomerProfile(account_no="900600", customer_name="Acme",
                                   data_json=json.dumps({"city": "Dubai", "trade_license_expiry": "2026-01-01"})))
    await db_session.commit()
    raw = [
        {"account_no": "900600", "customer_name": "Acme", "key": "email", "value": "new@a.c", "title": "", "detail": ""},   # add
        {"account_no": "900600", "customer_name": "Acme", "key": "city", "value": "Dubai", "title": "", "detail": ""},      # skip_same
        {"account_no": "900600", "customer_name": "Acme", "key": "city", "value": "Sharjah", "title": "", "detail": ""},    # NOTE: dup key vs prev? different value → but parse dedups by key; here staging handles each
        {"account_no": "900600", "customer_name": "Acme", "key": "trade_license_expiry", "value": "2025-06-01", "title": "", "detail": ""},  # older → skip_stale
    ]
    staged = await dbx.stage_db_writes(db_session, "900600", "Acme", raw)
    ops = [(s["key"], s["op"], s.get("action")) for s in staged]
    assert ("email", "db_write", "add") in ops
    # same-value city → note (already present)
    assert any(s["key"] == "" and "از قبل ثبت شده" in s["title"] for s in staged) or any("از قبل" in s["title"] for s in staged)
    # older license expiry → not applied (note)
    assert any("به‌روزتر" in s["title"] for s in staged)


# ---------------- apply (writes + dedup + staleness + audit + profile create) ----------------

async def test_apply_creates_profile_writes_and_audits(client, auth_headers, db_session):
    # account NOT in DB yet → apply must create the customer/profile
    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={"items": [
        {"account_no": "900700", "customer_name": "Fresh Co", "key": "city", "value": "Abu Dhabi"},
        {"account_no": "900700", "customer_name": "Fresh Co", "key": "trade_license_no", "value": "TL-123"},
    ]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["counts"]["added"] == 2
    assert body["counts"]["profiles_created"] >= 1

    prof = (await db_session.execute(select(CustomerProfile).where(CustomerProfile.account_no == "900700"))).scalar_one()
    data = json.loads(prof.data_json)
    assert data["city"] == "Abu Dhabi" and data["trade_license_no"] == "TL-123"
    assert prof.trade_license_no == "TL-123"   # mirrored to the structured column

    # audited against the account (→ shows in the profile Logs tab + global log)
    logs = (await db_session.execute(select(AuditLog).where(AuditLog.account_no == "900700", AuditLog.entity_type == "profile_extract"))).scalars().all()
    assert len(logs) == 2


async def test_apply_dedups_and_respects_staleness(client, auth_headers, db_session):
    db_session.add(Customer(account_no="900800", name="Dedup Co"))
    db_session.add(CustomerProfile(account_no="900800", customer_name="Dedup Co",
                                   data_json=json.dumps({"city": "Dubai", "passport_expiry": "2027-01-01"})))
    await db_session.commit()

    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={"items": [
        {"account_no": "900800", "customer_name": "Dedup Co", "key": "city", "value": "Dubai"},           # same → skip
        {"account_no": "900800", "customer_name": "Dedup Co", "key": "passport_expiry", "value": "2025-01-01"},  # older → skip
        {"account_no": "900800", "customer_name": "Dedup Co", "key": "email", "value": "x@y.z"},          # new → add
    ]})
    body = r.json()
    assert body["counts"]["added"] == 1
    assert body["counts"]["skipped"] == 2

    prof = (await db_session.execute(select(CustomerProfile).where(CustomerProfile.account_no == "900800"))).scalar_one()
    data = json.loads(prof.data_json)
    assert data["passport_expiry"] == "2027-01-01"   # NOT regressed to the older date
    assert data["email"] == "x@y.z"


async def test_apply_newer_date_updates(client, auth_headers, db_session):
    db_session.add(Customer(account_no="900900", name="Renew Co"))
    db_session.add(CustomerProfile(account_no="900900", customer_name="Renew Co",
                                   data_json=json.dumps({"trade_license_expiry": "2025-01-01"})))
    await db_session.commit()
    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={"items": [
        {"account_no": "900900", "customer_name": "Renew Co", "key": "trade_license_expiry", "value": "2027-12-31"},
    ]})
    assert r.json()["counts"]["updated"] == 1
    prof = (await db_session.execute(select(CustomerProfile).where(CustomerProfile.account_no == "900900"))).scalar_one()
    assert json.loads(prof.data_json)["trade_license_expiry"] == "2027-12-31"
