"""Entry-time de-dup guards: adding / importing must never create duplicates.

These mirror the cleanup engine's matchers, applied at the point of entry so a
re-import, a repeated row, or a manual/AI add can't introduce the very
duplicates the cleanup engine would later have to remove.
"""
import io

import openpyxl
import pytest
from sqlalchemy import select

from app.models.facility import Facility
from app.models.guarantor import Guarantor
from app.models.profile_entities import MortgagedProperty
from app.models.audit_log import AuditLog


def _xlsx(header, rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _file(content: bytes, name="facilities.xlsx"):
    return {"file": (name, content,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


@pytest.mark.asyncio
async def test_add_property_guard_merges_duplicate(client, auth_headers, test_customer, db_session):
    """Adding a property that matches an existing one enriches it in place."""
    acc = test_customer.account_no
    r1 = await client.post(f"/api/crm/properties/{acc}", headers=auth_headers,
                           json={"plate_no": "A-1", "address": "Zayed Rd"})
    assert r1.status_code == 200, r1.text
    # duplicate by plate_no, carrying extra data → must MERGE into the existing row
    r2 = await client.post(f"/api/crm/properties/{acc}", headers=auth_headers,
                           json={"plate_no": "A-1", "city": "Dubai", "valuation": 100})
    assert r2.status_code == 200, r2.text
    assert r2.json().get("deduped") is True

    props = (await db_session.execute(
        select(MortgagedProperty).where(MortgagedProperty.account_no == acc,
                                        MortgagedProperty.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(props) == 1                    # NOT duplicated
    assert props[0].city == "Dubai"           # empty → filled
    assert float(props[0].valuation) == 100   # empty → filled
    assert props[0].address == "Zayed Rd"     # populated field kept (no contradiction)


@pytest.mark.asyncio
async def test_add_distinct_property_not_merged(client, auth_headers, test_customer, db_session):
    """A genuinely different property is still added (guard is not over-eager)."""
    acc = test_customer.account_no
    await client.post(f"/api/crm/properties/{acc}", headers=auth_headers, json={"plate_no": "A-1"})
    r = await client.post(f"/api/crm/properties/{acc}", headers=auth_headers, json={"plate_no": "B-2"})
    assert r.json().get("deduped") is not True
    props = (await db_session.execute(
        select(MortgagedProperty).where(MortgagedProperty.account_no == acc,
                                        MortgagedProperty.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(props) == 2


@pytest.mark.asyncio
async def test_add_guarantor_guard_merges_same_person(client, auth_headers, test_customer, db_session):
    """Adding the same guarantor (person + amount) without a cheque_no merges into
    the existing record — the full _guar_match rule — and never blanks the
    existing cheque number."""
    acc = test_customer.account_no
    r1 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Ali Hammadi", "cheque_no": "CH1", "cheque_amount": 5000})
    assert r1.status_code == 200, r1.text
    assert r1.json()["created"] is True
    # same person + same amount, NO cheque_no → must MERGE (not duplicate)
    r2 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Ali Hammadi", "cheque_amount": 5000, "issuing_bank": "ADCB"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["created"] is False

    guars = (await db_session.execute(
        select(Guarantor).where(Guarantor.account_no == acc,
                                Guarantor.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(guars) == 1                    # NOT duplicated
    assert guars[0].cheque_no == "CH1"        # existing cheque number preserved
    assert guars[0].issuing_bank == "ADCB"    # new field applied


@pytest.mark.asyncio
async def test_import_facilities_skips_duplicates(client, auth_headers, test_customer, db_session):
    """Facility import skips exact duplicates (same type & amount), in-file and on
    re-import, and logs each skip under the customer."""
    acc = test_customer.account_no
    content = _xlsx(
        ["account_no", "name", "facility_type", "amount"],
        [[acc, "Loan A", "loan", "100000"],
         [acc, "Loan A again", "loan", "100000"],   # exact dup of row 1 → skipped
         [acc, "Loan B", "loan", "50000"]],         # different amount → created
    )
    r = await client.post("/api/imports/facilities", files=_file(content), headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 2
    assert body["skipped_existing"] == 1

    facs = (await db_session.execute(
        select(Facility).where(Facility.customer_id == test_customer.id,
                               Facility.is_deleted == False))).scalars().all()  # noqa: E712
    assert len(facs) == 2

    # re-import the same file → all three now match existing rows → nothing created
    r2 = await client.post("/api/imports/facilities", files=_file(content), headers=auth_headers)
    b2 = r2.json()
    assert b2["created"] == 0
    assert b2["skipped_existing"] == 3

    # skips are logged under the customer (visible in the Logs tab)
    logs = (await db_session.execute(
        select(AuditLog).where(AuditLog.account_no == acc, AuditLog.action == "skip"))).scalars().all()
    assert len(logs) >= 1
