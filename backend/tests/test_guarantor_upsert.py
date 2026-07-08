"""The guarantor / security-cheque endpoint is the single source of truth shared
by the customer page and the Per-Contra voucher form. Saving the same cheque
twice must UPDATE one record (idempotent upsert), not scatter duplicates, and the
list endpoint must return it for two-way sync.
"""
from app.models.customer import Customer
from app.routers.crm import _acct_core, _name_similar, _name_tokens


def test_acct_core_and_name_similarity():
    # account core ignores branch prefix + suffix formatting
    assert _acct_core("2624-131757-006") == "131757"
    assert _acct_core("131757") == "131757"
    assert _acct_core("") == ""
    assert _acct_core("2624 131757 006") == "131757"
    assert _acct_core("345678-901234") == ""               # two 6-groups → ambiguous → strict fallback
    # the owner's real near-duplicate must read as the same person…
    a = _name_tokens("SALWA MOHD YOUSIF JUMA")
    b = _name_tokens("SALWA MOHAMED YOUSIF JUMA AL MAAZMI")
    assert _name_similar(a, b) is True
    # …but genuinely different guarantors must NOT
    assert _name_similar(a, _name_tokens("AYESHA IBRAHIM MOHD AL SEYED")) is False


async def test_guarantor_dedup_by_account_core_and_similar_name(client, auth_headers, db_session):
    """Owner report: the SAME guarantor recorded twice — "131757" vs
    "2624-131757-006" with "MOHD" vs "MOHAMED" — escaped dedup. The forward-fix
    collapses them onto ONE record when the account CORE matches and the names
    are similar; a truly different guarantor on the same account stays separate."""
    db_session.add(Customer(account_no="800009", name="Borrower Co"))
    await db_session.commit()
    acc = "800009"

    r1 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "SALWA MOHD YOUSIF JUMA", "guarantor_account": "131757",
    })
    assert r1.status_code == 200 and r1.json()["created"] is True

    # different spelling + fuller account format → SAME person, updates the record
    r2 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "SALWA MOHAMED YOUSIF JUMA AL MAAZMI",
        "guarantor_account": "2624-131757-006",
    })
    assert r2.status_code == 200 and r2.json()["created"] is False

    # a genuinely different guarantor is NOT merged
    r3 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers, json={
        "guarantor_name": "AYESHA IBRAHIM MOHD AL SEYED", "guarantor_account": "129167",
    })
    assert r3.json()["created"] is True

    rows = (await client.get(f"/api/crm/guarantors/{acc}", headers=auth_headers)).json()
    assert len(rows) == 2   # SALWA collapsed to one, AYESHA separate


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
