"""The guarantor / security-cheque endpoint is the single source of truth shared
by the customer page and the Per-Contra voucher form. Saving the same cheque
twice must UPDATE one record (idempotent upsert), not scatter duplicates, and the
list endpoint must return it for two-way sync.
"""
from app.models.customer import Customer


async def test_guarantor_upsert_then_list(client, auth_headers, db_session):
    db_session.add(Customer(account_no="800001", name="Borrower Co"))
    await db_session.commit()
    acc = "800001"

    # First save → creates.
    r1 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "Guarantor A", "cheque_no": "CHQ100",
        "cheque_amount": 5000, "facility_id": "F-1", "branch": "2776",
    })
    assert r1.status_code == 200, r1.text
    b1 = r1.json()
    assert b1["created"] is True
    gid = b1["id"]

    # Same cheque number → updates the SAME record, not a duplicate.
    r2 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "Guarantor A (rev)", "cheque_no": "CHQ100",
        "cheque_amount": 6000, "facility_id": "F-1",
    })
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["created"] is False
    assert b2["id"] == gid

    # A different cheque → a new record.
    r3 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "Guarantor B", "cheque_no": "CHQ200", "cheque_amount": 1000,
    })
    assert r3.json()["created"] is True

    # List → two records, first one carries the updated values + branch.
    rl = await client.get(f"/api/crm/guarantors/{acc}", headers=auth_headers)
    assert rl.status_code == 200
    rows = rl.json()
    assert len(rows) == 2
    by_cheque = {r["cheque_no"]: r for r in rows}
    assert by_cheque["CHQ100"]["guarantor_name"] == "Guarantor A (rev)"
    assert by_cheque["CHQ100"]["cheque_amount"] == 6000
    assert by_cheque["CHQ100"]["branch"] == "2776"
    assert by_cheque["CHQ100"]["customer_name"] == "Borrower Co"
