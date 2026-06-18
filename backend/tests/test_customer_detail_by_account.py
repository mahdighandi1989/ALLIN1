"""GET /api/customers/{id}/detail must resolve by account number, not only the
internal "C…" primary key — the credit-file summary forms look customers up by
their 6-digit account number, so that must not 404 for a real account.
"""
from app.models.customer import Customer


async def test_detail_resolves_by_account_no(client, auth_headers, db_session):
    db_session.add(Customer(account_no="909090", name="Account Lookup Co"))
    await db_session.commit()

    # By account number (what the summary forms send) — must succeed.
    r = await client.get("/api/customers/909090/detail", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["customer"]["account_no"] == "909090"
    assert body["customer"]["name"] == "Account Lookup Co"
    # The aggregate sections are present (facilities etc.), keyed off the account.
    assert "facilities" in body and "profile" in body


async def test_detail_still_resolves_by_internal_id(client, auth_headers, db_session):
    c = Customer(account_no="909091", name="By Id Co")
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)

    r = await client.get(f"/api/customers/{c.id}/detail", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["customer"]["account_no"] == "909091"


async def test_detail_unknown_account_404(client, auth_headers):
    r = await client.get("/api/customers/000000/detail", headers=auth_headers)
    assert r.status_code == 404
