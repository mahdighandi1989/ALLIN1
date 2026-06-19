"""The Credit Approval (مصوبه) form persists a first-class credit_reviews row plus
promoted profile columns, deduped per review date (re-saving updates in place; a
new review date adds history)."""
from app.models.customer import Customer


def _payload(date="13/06/2026", amount_note="AED 80,000"):
    return {
        "snapshot": {
            "CustomerName": "NAEIMEH GHARABI HASHEMI", "AccountNumber": "2624-127987-006",
            "BranchName": "AL MAKTOUM - 2624", "BorrowerType": "Retail", "DateOfReview": date,
            "AECBScore": "471", "MonthlySalary": "6110", "Purpose": amount_note,
            "ProposedRating": "B*", "CreditAppNo": "PLA/2624/127987/076",
        },
        "limits": [{"type": "Personal Loan - II", "existing": "-", "os": "", "pb": "80,000", "pc": "80,000"}],
        "guars": [{"desc": "Muhammad Ebrahim", "branch": "2624", "account": "124076"}],
        "recip": [], "fin": [], "banks": [],
    }


async def test_sanction_save_dedup_and_promote(client, auth_headers, db_session):
    db_session.add(Customer(account_no="127987", name="NAEIMEH"))
    await db_session.commit()

    r1 = await client.post("/api/crm/sanction/127987", headers=auth_headers, json=_payload())
    assert r1.status_code == 200, r1.text
    assert r1.json()["created"] is True

    # Same review date → updates in place (no duplicate row).
    r2 = await client.post("/api/crm/sanction/127987", headers=auth_headers, json=_payload(amount_note="updated"))
    assert r2.json()["created"] is False

    # A different review date → a new history row.
    r3 = await client.post("/api/crm/sanction/127987", headers=auth_headers, json=_payload(date="20/06/2026"))
    assert r3.json()["created"] is True

    rc = await client.get("/api/crm/credit-reviews/127987", headers=auth_headers)
    assert rc.status_code == 200
    rows = rc.json()
    assert len(rows) == 2  # two distinct review dates, not four
    assert {r["date_of_review"] for r in rows} == {"13/06/2026", "20/06/2026"}

    # Promoted profile columns are readable via offer-letter-data.
    rd = await client.get("/api/crm/offer-letter-data/127987", headers=auth_headers)
    assert rd.json()["ProfileData"].get("sanction")  # exact snapshot kept for restore
