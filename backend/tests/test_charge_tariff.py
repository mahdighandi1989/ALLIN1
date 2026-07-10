"""The editable Schedule-of-Charges tariff + the processing-charge calculator.

The calculator's reference truth is the owner's REAL letter (A/C 301408):
Cheque Discount 2,800,000 (corporate line fee 4‰ = 11,200) + Overdraft
3,500,000 fully covered by FD underlien (0.1% capped at 1,000) → term 23 says
AED 12,200. That exact case is locked here, plus the tariff's floors/caps,
the retail small-loan override, the staff exemption, the unknown-type warning,
and the CRUD endpoints (fill-empty seed, edit, quarantine)."""
from decimal import Decimal

from app.services import charge_calc


RULES = [dict(r, enabled=True) for r in charge_calc.DEFAULT_RULES]


def _compute(items, segment="corporate"):
    return charge_calc.compute_charges(RULES, items, segment=segment)


# ---------------- calculator ----------------

def test_owner_reference_letter_total_12200():
    out = _compute([
        {"facility_type": "Overdraft", "amount": "3,500,000/-", "covered_by_fd": True},
        {"facility_type": "Cheque Discount", "amount": "2,800,000/-"},
    ])
    assert out["total"] == 12200.0
    by = {l["rule_key"]: l for l in out["lines"]}
    assert by["od_100fd"]["charge"] == 1000.0     # 3,500 capped at 1,000
    assert by["line_fee"]["charge"] == 11200.0    # 2.8M × 4‰
    assert out["warnings"] == []


def test_line_fee_min_and_max():
    # tiny line → floor 1,200
    out = _compute([{"facility_type": "Overdraft", "amount": "100000"}])
    assert out["total"] == 1200.0
    # huge line → cap 20,000
    out = _compute([{"facility_type": "Overdraft", "amount": "10,000,000"}])
    assert out["total"] == 20000.0
    # several line facilities accumulate into ONE line fee (single min/max)
    out = _compute([
        {"facility_type": "Overdraft", "amount": "1,000,000"},
        {"facility_type": "Cheque Discount", "amount": "2,000,000"},
    ])
    assert out["total"] == 12000.0                 # 3M × 4‰, one fee line
    assert len([l for l in out["lines"] if l["rule_key"] == "line_fee"]) == 1


def test_commercial_and_personal_loans():
    out = _compute([{"facility_type": "Commercial Loan", "amount": "200,000"}])
    assert out["total"] == 3000.0                  # 1.5%
    out = _compute([{"facility_type": "Term Loan", "amount": "10,000"}])
    assert out["total"] == 500.0                   # 1.5% = 150 → min 500
    # retail: 1% min 500 max 2,500; ≤10,000 → min 200
    out = _compute([{"facility_type": "Personal Loan", "amount": "80,000"}], segment="individual")
    assert out["total"] == 800.0
    out = _compute([{"facility_type": "Personal Loan", "amount": "8,000"}], segment="individual")
    assert out["total"] == 200.0                   # small-loan override
    out = _compute([{"facility_type": "Personal Loan", "amount": "500,000"}], segment="individual")
    assert out["total"] == 2500.0                  # cap


def test_staff_facility_exempt_but_non_staff_charged():
    out = _compute([
        {"facility_type": "Staff Loan", "amount": "100,000", "staff_facility": True},
        {"facility_type": "Commercial Loan", "amount": "100,000"},   # non-staff facility → charged
    ])
    assert out["total"] == 1500.0
    staff_line = [l for l in out["lines"] if l["rule_key"] == "staff_exempt"][0]
    assert staff_line["charge"] == 0.0


def test_temporary_facilities():
    out = _compute([{"facility_type": "Overdraft", "amount": "50,000", "temporary": True}])
    assert out["total"] == 1000.0                  # 2% OD temp
    out = _compute([{"facility_type": "Cheque Discount", "amount": "400,000", "temporary": True}])
    assert out["total"] == 2500.0                  # 1% = 4,000 → cap 2,500


def test_unknown_type_warns_never_invents():
    out = _compute([{"facility_type": "Something Weird", "amount": "1,000,000"}])
    assert out["total"] == 0.0
    assert out["warnings"] and "شناخته نشد" in out["warnings"][0]


# ---------------- endpoints ----------------

async def test_tariff_crud_and_compute_endpoint(client, auth_headers):
    # first GET seeds the defaults (fill-empty-only)
    r = await client.get("/api/charge-tariff", headers=auth_headers)
    assert r.status_code == 200, r.text
    rules = r.json()["rules"]
    assert any(x["id"] == "CR-corp-line" for x in rules)

    # compute the reference case through the endpoint
    rc = await client.post("/api/charge-tariff/compute", headers=auth_headers, json={
        "segment": "corporate",
        "items": [
            {"facility_type": "Overdraft", "amount": "3,500,000/-", "covered_by_fd": True},
            {"facility_type": "Cheque Discount", "amount": "2,800,000/-"},
        ],
    })
    assert rc.status_code == 200 and rc.json()["total"] == 12200.0

    # the owner edits a rate (tariffs change yearly) → compute follows
    line = next(x for x in rules if x["id"] == "CR-corp-line")
    line["rate"] = 5
    ru = await client.post("/api/charge-tariff", headers=auth_headers, json=line)
    assert ru.status_code == 200 and ru.json()["created"] is False
    rc2 = await client.post("/api/charge-tariff/compute", headers=auth_headers, json={
        "segment": "corporate",
        "items": [{"facility_type": "Cheque Discount", "amount": "2,800,000"}],
    })
    assert rc2.json()["total"] == 14000.0          # 2.8M × 5‰

    # quarantine (soft delete) → rule vanishes from the list, compute warns
    rd = await client.delete("/api/charge-tariff/CR-corp-line", headers=auth_headers)
    assert rd.status_code == 200
    r2 = await client.get("/api/charge-tariff", headers=auth_headers)
    assert not any(x["id"] == "CR-corp-line" for x in r2.json()["rules"])
    rc3 = await client.post("/api/charge-tariff/compute", headers=auth_headers, json={
        "segment": "corporate",
        "items": [{"facility_type": "Overdraft", "amount": "1,000,000"}],
    })
    assert rc3.json()["total"] == 0.0 and rc3.json()["warnings"]
