"""The Offer Letter form is two-way synced with the customer's profile: P.O. Box,
salutation and a full snapshot are saved into the shared profile record and read
back on the next load, so other forms/reports can reuse them.
"""
from app.models.customer import Customer


async def test_offer_letter_data_save_then_read(client, auth_headers, db_session):
    db_session.add(Customer(account_no="900100", name="Faraz Kaif", account_type="retail", branch="2900"))
    await db_session.commit()
    acc = "900100"

    # Nothing saved yet → salutation derives from the (retail) account type.
    r0 = await client.get(f"/api/crm/offer-letter-data/{acc}", headers=auth_headers)
    assert r0.status_code == 200, r0.text
    assert r0.json()["Salutation"] == "Mr."
    assert r0.json()["AccountType"] == "retail"

    # Save reusable fields + a snapshot.
    rs = await client.post(f"/api/crm/offer-letter-data/{acc}", headers=auth_headers, json={
        "POBox": "77777", "CityCountry": "AJMAN, U.A.E.", "Salutation": "Mr.",
        "Branch": "AJMAN - 2900",
        "snapshot": {"RefSerial": "202", "RefYear": "2026", "LoanAmount": "18,000/-",
                     "securitiesChecked": [True, False, True]},
    })
    assert rs.status_code == 200, rs.text
    assert "POBox" in rs.json()["saved_keys"]

    # Read back → the lifted fields + the full snapshot return.
    r1 = await client.get(f"/api/crm/offer-letter-data/{acc}", headers=auth_headers)
    body = r1.json()
    assert body["POBox"] == "77777"
    assert body["CityCountry"] == "AJMAN, U.A.E."
    assert body["Saved"]["RefSerial"] == "202"
    assert body["Saved"]["securitiesChecked"] == [True, False, True]


async def test_offer_letter_data_corporate_salutation(client, auth_headers, db_session):
    db_session.add(Customer(account_no="900200", name="Party Time LLC", account_type="corporate"))
    await db_session.commit()
    r = await client.get("/api/crm/offer-letter-data/900200", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["Salutation"] == "M/S."
