"""The Offer Letter's Facility Type combobox is backed by a DB catalog:
built-in types + user-added ones (SystemSetting "custom_facility_types").
A genuinely NEW name opens its own place in the list; a name-similar entry
(case/punctuation/plural-level) is matched instead of duplicated.
"""


async def test_builtin_types_listed(client, auth_headers):
    r = await client.get("/api/crm/facility-types", headers=auth_headers)
    assert r.status_code == 200, r.text
    types = r.json()["types"]
    assert "Overdraft" in types
    assert "Personal Loan" in types
    assert "Letter of Guarantee" in types


async def test_new_type_added_and_persisted(client, auth_headers):
    r = await client.post("/api/crm/facility-types", headers=auth_headers,
                          json={"name": "Murabaha Financing"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["added"] is True
    assert "Murabaha Financing" in body["types"]

    # It is now part of the catalog for every later GET.
    r2 = await client.get("/api/crm/facility-types", headers=auth_headers)
    assert "Murabaha Financing" in r2.json()["types"]


async def test_similar_name_is_matched_not_duplicated(client, auth_headers):
    # Case/punctuation variant of a built-in → matched, list unchanged.
    r = await client.post("/api/crm/facility-types", headers=auth_headers,
                          json={"name": "personal   loan"})
    assert r.status_code == 200
    body = r.json()
    assert body["added"] is False
    assert body["matched"] == "Personal Loan"

    # Plural-level variant of a custom entry → matched too.
    await client.post("/api/crm/facility-types", headers=auth_headers,
                      json={"name": "Bridge Loan"})
    r2 = await client.post("/api/crm/facility-types", headers=auth_headers,
                           json={"name": "Bridge Loans"})
    assert r2.json()["added"] is False
    assert r2.json()["matched"] == "Bridge Loan"
    assert r2.json()["types"].count("Bridge Loan") == 1


async def test_blank_name_rejected(client, auth_headers):
    r = await client.post("/api/crm/facility-types", headers=auth_headers,
                          json={"name": "  --  "})
    assert r.status_code == 422
