"""Offer Letter ↔ guarantors integration:

1. /offer-letter-data returns the customer's recorded guarantors (name + A/C)
   so the letter's item-7 guarantee line prefills.
2. A cheque-less guarantor (as saved from the Offer Letter) upserts by NAME —
   re-saving the same person must not scatter duplicates.
3. A cheque-less re-save must NOT wipe an existing cheque number.
"""
from app.models.customer import Customer
from app.models.guarantor import Guarantor


async def test_offer_letter_data_includes_guarantors(client, auth_headers, db_session):
    db_session.add(Customer(account_no="910100", name="Borrower One", account_type="retail"))
    db_session.add(Guarantor(id="G-1", account_no="910100",
                             guarantor_name="Mr. MUHAMMAD EBRAHIM", guarantor_account="124076"))
    # A duplicate row (same name+account) and a deleted one must not leak in.
    db_session.add(Guarantor(id="G-2", account_no="910100",
                             guarantor_name="mr. muhammad ebrahim", guarantor_account="124076"))
    db_session.add(Guarantor(id="G-3", account_no="910100",
                             guarantor_name="Ms. GONE", is_deleted=True))
    await db_session.commit()

    r = await client.get("/api/crm/offer-letter-data/910100", headers=auth_headers)
    assert r.status_code == 200, r.text
    guars = r.json()["Guarantors"]
    assert guars == [{"name": "Mr. MUHAMMAD EBRAHIM", "account": "124076"}]


async def test_chequeless_guarantor_upserts_by_name(client, auth_headers, db_session):
    db_session.add(Customer(account_no="910200", name="Borrower Two"))
    await db_session.commit()
    acc = "910200"

    r1 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Mr. ALI HASSAN", "guarantor_account": "555001"})
    assert r1.status_code == 200, r1.text
    assert r1.json()["created"] is True
    gid = r1.json()["id"]

    # Saving the same person again (Offer Letter re-save) → same record.
    r2 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "mr. ali  hassan", "guarantor_account": "555001"})
    assert r2.json()["created"] is False
    assert r2.json()["id"] == gid

    # A different person → a new record.
    r3 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Ms. SARA KARIM"})
    assert r3.json()["created"] is True

    rl = await client.get(f"/api/crm/guarantors/{acc}", headers=auth_headers)
    assert len(rl.json()) == 2


async def test_chequeless_resave_keeps_cheque_no(client, auth_headers, db_session):
    db_session.add(Customer(account_no="910300", name="Borrower Three"))
    await db_session.commit()
    acc = "910300"

    # Recorded first from the voucher form WITH a cheque.
    r1 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Mr. OMID RAAD", "cheque_no": "CHQ900",
                                 "cheque_amount": 12000})
    assert r1.json()["created"] is True

    # Re-saved from the Offer Letter (no cheque) → matches by name, cheque kept.
    r2 = await client.post(f"/api/crm/guarantors/{acc}", headers=auth_headers,
                           json={"guarantor_name": "Mr. OMID RAAD", "guarantor_account": "777123"})
    assert r2.json()["created"] is False
    assert r2.json()["cheque_no"] == "CHQ900"
    assert r2.json()["guarantor_account"] == "777123"


async def test_offer_letter_data_returns_all_facilities_for_multi_row_sync(
    client, auth_headers, db_session,
):
    """A multi-facility sanction imported into the DB must reach the Offer
    Letter as MULTIPLE rows: /offer-letter-data returns a Facilities array
    (largest first — row 1) with type label, formatted amount and rate."""
    from app.models.facility import Facility

    db_session.add(Customer(account_no="910500", name="Multi Fac LLC", account_type="corporate"))
    await db_session.commit()
    cust_id = (await client.get("/api/crm/offer-letter-data/910500", headers=auth_headers)).json()
    # seed two facilities like the owner's sample letter (OD 3.5M + CD 2.8M)
    from sqlalchemy import select as _sel
    from app.models.customer import Customer as _C
    cid = (await db_session.execute(_sel(_C).where(_C.account_no == "910500"))).scalar_one().id
    db_session.add(Facility(id="F-910500-1", customer_id=cid, facility_type="overdraft",
                            amount=3500000, currency="AED", interest_rate=5.25, status="active"))
    db_session.add(Facility(id="F-910500-2", customer_id=cid, facility_type="loan",
                            amount=2800000, currency="AED", interest_rate=11, status="active"))
    await db_session.commit()

    r = await client.get("/api/crm/offer-letter-data/910500", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    facs = body["Facilities"]
    assert len(facs) == 2
    # largest first (matches the legacy single-facility row-1 behavior)
    assert facs[0]["amount"] == "3,500,000" and "5.25%" in facs[0]["rate"]
    assert facs[1]["amount"] == "2,800,000" and "11%" in facs[1]["rate"]
    assert facs[0]["type"] and facs[1]["type"]
    assert body["facilities_count"] == 2


async def test_offer_letter_data_hides_legacy_phantom_deposit_rows(client, auth_headers, db_session):
    """Pre-v36 imports left OTHER-typed «deposit» rows in production. The letter
    must not surface them (display guard) while the DB row stays untouched."""
    from app.models.facility import Facility

    db_session.add(Customer(account_no="910600", name="Guarded Co", account_type="corporate"))
    await db_session.commit()
    from sqlalchemy import select as _sel
    cid = (await db_session.execute(_sel(Customer).where(Customer.account_no == "910600"))).scalar_one().id
    db_session.add(Facility(id="F-910600-1", customer_id=cid, facility_type="overdraft",
                            amount=3500000, currency="AED", interest_rate=5.25, status="active"))
    db_session.add(Facility(id="F-910600-2", customer_id=cid, facility_type="other",
                            amount=3500000, currency="AED", interest_rate=3.25, status="active",
                            notes="Fixed Deposit 365 days, Ref AJMN FD-2025-73, start 29NOV25"))
    await db_session.commit()

    r = await client.get("/api/crm/offer-letter-data/910600", headers=auth_headers)
    assert r.status_code == 200, r.text
    facs = r.json()["Facilities"]
    assert [f["type"] for f in facs] == ["Overdraft"]      # phantom hidden from the letter
    assert r.json()["facilities_count"] == 2               # DB row untouched (review-first)
