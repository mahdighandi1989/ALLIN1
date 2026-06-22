"""AI document import: the .docx fast-path persists across the right customer
(no AI key needed), the JSON parser is tolerant, and multi-customer persist is
deduped (re-import never duplicates guarantors)."""
from io import BytesIO

from docx import Document

from app.models.customer import Customer
from app.services import doc_ingest


async def _poll(client, headers, job_id, tries: int = 50):
    """Poll an import job to completion. Jobs run inline under ``import_inline``,
    so this returns on the first read; the loop is just defensive."""
    import asyncio
    for _ in range(tries):
        r = await client.get(f"/api/imports/jobs/{job_id}", headers=headers)
        assert r.status_code == 200, r.text
        j = r.json()
        if j["status"] != "running":
            return j
        await asyncio.sleep(0.02)
    raise AssertionError(f"job {job_id} never finished")


def test_parse_model_json_tolerant():
    assert doc_ingest.parse_model_json('```json\n{"customers":[]}\n```') == {"customers": []}
    assert doc_ingest.parse_model_json('blah {"a":1} trailing')["a"] == 1
    assert doc_ingest.parse_model_json("not json") == {}


async def test_persist_customer_multi_and_dedup(db_session):
    payload = {
        "account_no": "2624-330011-1", "name": "Multi Co", "account_type": "corporate",
        "branch": "AL MAKTOUM - 2624",
        "fields": {"aecb_score": "640", "trade_license_no": "TL-9", "business_type": "Trading"},
        "guarantors": [{"name": "Ali Guarantor", "account": "330099", "branch": "2624"}],
        "review": {"date_of_review": "01/06/2026", "purpose": "fresh loan"},
    }
    r1 = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r1["ok"] and r1["account_no"] == "330011"  # 6-digit core extracted
    assert "aecb_score" in r1["fields_saved"]
    assert r1["guarantors_added"] == 1
    await db_session.commit()

    # Re-persist the same → guarantor updated in place, not duplicated.
    r2 = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r2["guarantors_added"] == 0 and r2["guarantors_updated"] == 1
    await db_session.commit()


def _draft_docx() -> bytes:
    d = Document()
    t = d.add_table(rows=0, cols=2)
    for k, v in [("Customer Name:", "EFCO TRADING LLC"), ("Account Number:", "2624 115524 011"),
                 ("Borrower Type", "SME / Corporate")]:
        c = t.add_row().cells
        c[0].text = k
        c[1].text = v
    d.add_paragraph("fresh commercial loan facility of AED 8,000,000/- for a period of 48 months. "
                    "Interest rate to be at 12% p.a. customer request letter dated.27/04/2026.")
    buf = BytesIO()
    d.save(buf)
    return buf.getvalue()


async def test_analyze_docx_fastpath(client, auth_headers, db_session, import_inline):
    db_session.add(Customer(account_no="115524", name="Old"))
    await db_session.commit()
    files = {"file": ("efco.docx", _draft_docx(),
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    r = await client.post("/api/imports/analyze", headers=auth_headers, files=files)
    assert r.status_code == 200, r.text
    job = await _poll(client, auth_headers, r.json()["job_id"])
    assert job["status"] == "done", job
    b = job["result"]
    assert b["ok"] and b["model"] == "Word draft parser"
    assert any(c.get("account_no") == "115524" for c in b["customers"])
    # data landed where other forms read it
    rd = await client.get("/api/crm/offer-letter-data/115524", headers=auth_headers)
    assert rd.status_code == 200
    rc = await client.get("/api/crm/credit-reviews/115524", headers=auth_headers)
    assert len(rc.json()) >= 1


def _xlsx_bytes() -> bytes:
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Account", "Name", "Nationality"])
    ws.append(["2624-440011-1", "Alpha Co", "Iran"])
    ws.append(["2624-440022-2", "Beta Co", "UAE"])
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()


def test_workbook_to_text_and_chunk():
    txt = doc_ingest.workbook_to_text(_xlsx_bytes(), "t.xlsx")
    assert "Alpha Co" in txt and "440022" in txt
    chunks = doc_ingest.chunk_text(txt, 50)
    assert len(chunks) >= 1
    # CSV path
    csv = doc_ingest.workbook_to_text(b"Account,Name\n440033,Gamma", "t.csv")
    assert "Gamma" in csv


async def test_analyze_xlsx_reaches_branch(client, auth_headers, import_inline):
    # No AI key in tests → the spreadsheet branch parses then reports no usable
    # model. The job captures that as an error with http_status 400/502, proving
    # the Excel path is wired (not a 415/500).
    files = {"file": ("book.xlsx", _xlsx_bytes(),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/imports/analyze", headers=auth_headers, files=files)
    assert r.status_code == 200, r.text
    job = await _poll(client, auth_headers, r.json()["job_id"])
    assert job["status"] == "error", job
    assert job["http_status"] in (400, 502), job


async def test_reupload_same_file_no_duplicate_review(client, auth_headers, db_session, import_inline):
    db_session.add(Customer(account_no="115524", name="X"))
    await db_session.commit()
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    for _ in range(2):  # upload + extract the SAME file twice
        r = await client.post("/api/imports/analyze", headers=auth_headers,
                              files={"file": ("efco.docx", _draft_docx(), mime)})
        assert r.status_code == 200, r.text
        job = await _poll(client, auth_headers, r.json()["job_id"])
        assert job["status"] == "done", job
    rc = await client.get("/api/crm/credit-reviews/115524", headers=auth_headers)
    assert len(rc.json()) == 1  # deduped per review date — not duplicated on re-upload


async def test_persist_properties_dedup(db_session):
    base = {"account_no": "550011", "name": "Prop Co", "account_type": "corporate",
            "properties": [{"prop_type": "Land & Building", "address": "Deira", "city": "Dubai",
                            "plate_no": "P-9", "valuation": "15,400,000", "valuation_currency": "AED"}]}
    r1 = await doc_ingest.persist_customer(db_session, base, "tester")
    assert r1["properties_added"] == 1
    await db_session.commit()
    # same property (matched by plate_no) → updated, not duplicated
    r2 = await doc_ingest.persist_customer(db_session, base, "tester")
    assert r2["properties_added"] == 0 and r2["properties_updated"] == 1
    await db_session.commit()
    from app.models.profile_entities import MortgagedProperty
    from sqlalchemy import select as _sel
    rows = (await db_session.execute(_sel(MortgagedProperty).where(MortgagedProperty.account_no == "550011"))).scalars().all()
    assert len(rows) == 1 and float(rows[0].valuation) == 15400000


def test_extraction_is_schema_driven():
    """The field list the model is asked for is derived from the CustomerProfile
    schema — so previously-missed sub-fields are covered and a future column would
    be picked up automatically (no prompt edit)."""
    fields = doc_ingest.extractable_profile_fields()
    for k in ("visa_issue", "visa_type", "tenancy_issue", "tenancy_address",
              "emirates_id_golden", "nationality", "trade_license_issue", "auditor",
              "grade", "call_report", "previous_files"):
        assert k in fields, f"{k} should be extractable"
    # housekeeping / file-path / officer-notes columns are excluded
    for k in ("data_json", "passport_doc", "profile_completeness", "account_no",
              "passport_remarks", "created_at"):
        assert k not in fields, f"{k} should NOT be extractable"
    # and they actually reach the prompt sent to the model
    for k in ("visa_type", "tenancy_address", "emirates_id_golden"):
        assert k in doc_ingest.EXTRACTION_PROMPT


async def test_persist_full_kyc_schema_driven(db_session):
    """Every recognised KYC sub-field is promoted to its real column (incl. the ones
    the old hardcoded map dropped: visa type/issue, tenancy address, golden EID)."""
    payload = {
        "account_no": "660011", "name": "KYC Co", "account_type": "corporate",
        "fields": {
            "visa_no": "V-123", "visa_issue": "01/01/2024", "visa_expiry": "01/01/2027",
            "visa_type": "Investor", "tenancy_no": "T-9", "tenancy_issue": "02/02/2025",
            "tenancy_address": "Marina, Dubai", "emirates_id_golden": "Yes",
            "nationality": "Iran", "auditor": "KPMG", "monthly_salary": "45000",
        },
    }
    r = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r["ok"]
    await db_session.commit()
    from app.models.crm import CustomerProfile
    from sqlalchemy import select as _sel
    cp = (await db_session.execute(_sel(CustomerProfile).where(CustomerProfile.account_no == "660011"))).scalar_one()
    assert cp.visa_type == "Investor" and cp.visa_no == "V-123"
    assert cp.tenancy_address == "Marina, Dubai" and cp.tenancy_no == "T-9"
    assert cp.emirates_id_golden == "Yes"
    assert cp.passport_nationality == "Iran"   # via the "nationality" alias
    assert cp.auditor == "KPMG" and cp.monthly_salary == "45000"


async def test_persist_kyc_renewal_updates_date_but_fillempty_text(db_session):
    """KYC dates update on renewal (later wins); curated text is never clobbered."""
    from app.models.crm import CustomerProfile
    from sqlalchemy import select as _sel
    cp = CustomerProfile(account_no="660022", passport_expiry="01/01/2026",
                         passport_nationality="India")
    db_session.add(cp)
    await db_session.commit()
    payload = {"account_no": "660022", "name": "X", "fields": {
        "passport_expiry": "01/01/2031",   # renewal → later date wins
        "nationality": "Pakistan",          # already set → must NOT clobber
    }}
    await doc_ingest.persist_customer(db_session, payload, "tester")
    await db_session.commit()
    row = (await db_session.execute(_sel(CustomerProfile).where(CustomerProfile.account_no == "660022"))).scalar_one()
    assert row.passport_expiry == "01/01/2031"     # updated on renewal
    assert row.passport_nationality == "India"      # curated value preserved


async def test_persist_partners_and_facilities(db_session):
    """Import now also fills the corporate credit-file form: partners (Partner
    table) and facility records (Facility table) the form reads from."""
    from app.models.customer import Customer
    from app.models.profile_entities import Partner
    from app.models.facility import Facility
    from sqlalchemy import select as _sel
    payload = {
        "account_no": "770011", "name": "Corp Co", "account_type": "corporate",
        "partners": [{"name": "Ali Partner", "nationality": "Iran", "share": "60"},
                     {"name": "Sara Partner", "nationality": "UAE", "share": "40"}],
        "facilities": [{"facility_type": "overdraft", "amount": "500,000", "interest_rate": "8%",
                        "expiry_date": "31/12/2027"},
                       {"facility_type": "loan", "amount": "2000000"}],
    }
    r = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r["ok"] and r["partners_added"] == 2 and r["facilities_added"] == 2
    await db_session.commit()
    cid = (await db_session.execute(_sel(Customer.id).where(Customer.account_no == "770011"))).scalar_one()
    parts = (await db_session.execute(_sel(Partner).where(Partner.account_no == "770011"))).scalars().all()
    assert {p.name for p in parts} == {"Ali Partner", "Sara Partner"}
    facs = (await db_session.execute(_sel(Facility).where(Facility.customer_id == cid))).scalars().all()
    od = next(f for f in facs if str(getattr(f.facility_type, "value", f.facility_type)) == "overdraft")
    assert float(od.amount) == 500000 and float(od.interest_rate) == 8
    assert od.expiry_date is not None

    # Re-import the same → no duplicate partners/facilities (deduped, fill-empty).
    r2 = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r2["partners_added"] == 0 and r2["facilities_added"] == 0
    await db_session.commit()


async def test_persist_security_and_summary_fields(db_session):
    """The credit-file summary header (grade/call report/previous files/undertaking)
    and the Security matrix are extracted and persisted (columns + data_json)."""
    import json as _j
    from app.models.crm import CustomerProfile
    from sqlalchemy import select as _sel
    payload = {
        "account_no": "880011", "name": "Sec Co", "account_type": "corporate",
        "fields": {"grade": "GOOD", "call_report": "done 01/2026", "previous_files": "2",
                   "undertaking_from": "Guarantor/s"},
        "security": [{"type": "Cheques", "for_facility": "overdraft", "aed": "100000"},
                     {"type": "Collaterals", "aed": "5000000"}],
    }
    r = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r["ok"] and r["security_added"] == 2
    await db_session.commit()
    cp = (await db_session.execute(_sel(CustomerProfile).where(CustomerProfile.account_no == "880011"))).scalar_one()
    assert cp.grade == "GOOD" and cp.call_report == "done 01/2026" and cp.previous_files == "2"
    assert cp.undertaking_from == "Guarantor/s"
    sd = _j.loads(cp.data_json)["security_details"]
    assert {row["type"] for row in sd} == {"Cheques", "Collaterals"}
    chq = next(row for row in sd if row["type"] == "Cheques")
    assert chq["aed"] == "100000" and chq["for_facility"] == "overdraft"
    # re-import the same security → no duplicate rows
    r2 = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r2["security_added"] == 0


async def test_persist_facility_rate_overflow_is_dropped(db_session):
    """A mis-extracted interest_rate (3190 into a Numeric(5,2) column) must NOT
    crash the import — it is dropped, the facility still saves with its amount."""
    from app.models.customer import Customer
    from app.models.facility import Facility
    from sqlalchemy import select as _sel
    payload = {
        "account_no": "990011", "name": "Big Co", "account_type": "corporate",
        "facilities": [{"facility_type": "overdraft", "amount": "1000000",
                        "interest_rate": "3190", "expiry_date": "30/05/2027"}],
    }
    r = await doc_ingest.persist_customer(db_session, payload, "tester")
    assert r["ok"] and r["facilities_added"] == 1
    await db_session.commit()
    cid = (await db_session.execute(_sel(Customer.id).where(Customer.account_no == "990011"))).scalar_one()
    fac = (await db_session.execute(_sel(Facility).where(Facility.customer_id == cid))).scalar_one()
    assert float(fac.amount) == 1000000
    assert fac.interest_rate is None  # the out-of-range rate was dropped, not stored


async def test_partner_reconcile_and_impossible_pct(db_session):
    """Same partner spelled differently collapses to ONE row; an impossible share
    (a capital amount as %) is dropped, not stored."""
    from app.models.profile_entities import Partner
    from sqlalchemy import select as _sel
    await doc_ingest.persist_customer(db_session, {
        "account_no": "771100", "name": "Co",
        "partners": [{"name": "Yousef Mohamed Alhammadi", "share": "11.000000%"},
                     {"name": "Capital Holder", "share": "3300000%"}],
    }, "t")
    await db_session.commit()
    # second document: same person, extra middle name → must NOT duplicate
    await doc_ingest.persist_customer(db_session, {
        "account_no": "771100", "name": "Co",
        "partners": [{"name": "Yousef Mohamed Ahmed Alhammadi", "nationality": "UAE"}],
    }, "t")
    await db_session.commit()
    rows = (await db_session.execute(_sel(Partner).where(
        Partner.account_no == "771100", Partner.is_deleted == False))).scalars().all()
    yousefs = [r for r in rows if "ousef" in r.name]
    assert len(yousefs) == 1, [r.name for r in rows]   # collapsed across spellings
    assert yousefs[0].share == "11%"                    # trailing zeros trimmed
    cap = next(r for r in rows if r.name == "Capital Holder")
    assert (cap.share or "") == ""                       # impossible % dropped


def test_same_person_and_clean_pct_units():
    assert doc_ingest._same_person("Yousef Alhammadi", "Yousef Mohamed Alhammadi")
    assert not doc_ingest._same_person("Khaled Shojae", "Valid Shojae")
    assert doc_ingest._clean_pct("45.0000000%") == "45%"
    assert doc_ingest._clean_pct("3300000%") == ""
    assert doc_ingest._clean_pct("33.33") == "33.33%"


async def test_property_consolidates_same_number_one_import(db_session):
    """The same property described several ways in ONE file (number stuffed in the
    address, different type labels) collapses to a single row with merged details."""
    from app.models.profile_entities import MortgagedProperty
    from sqlalchemy import select as _sel
    await doc_ingest.persist_customer(db_session, {
        "account_no": "453100", "name": "Co",
        "properties": [
            {"prop_type": "Property", "address": "Property no. 638/140", "city": "Shiraz"},
            {"prop_type": "FLAT", "address": "Property no. 638/140", "valuation": "458000", "valuation_currency": "AED"},
            {"prop_type": "Apartment", "address": "Property no. 638/140"},
        ],
    }, "t")
    await db_session.commit()
    rows = (await db_session.execute(_sel(MortgagedProperty).where(
        MortgagedProperty.account_no == "453100", MortgagedProperty.is_deleted == False))).scalars().all()
    assert len(rows) == 1, [r.prop_type for r in rows]   # consolidated to ONE
    assert float(rows[0].valuation) == 458000             # detail merged in


def test_prop_token_extracts_number():
    assert doc_ingest._prop_token("Property no. 638/140") == "638/140"
    assert doc_ingest._prop_token("FLAT", "", "deed 638 / 140") == "638/140"
    assert doc_ingest._prop_token("no number here") == ""


async def test_fail_orphaned_jobs_marks_error(db_session, monkeypatch):
    """A job left 'running' by a killed process is marked errored at startup so the
    browser's poll stops waiting; finished jobs are untouched."""
    from contextlib import asynccontextmanager
    from app.routers import imports as imp
    from app.models.import_job import ImportJob
    from sqlalchemy import select as _sel
    db_session.add(ImportJob(id="orphan1", status="running", filename="x.pdf"))
    db_session.add(ImportJob(id="done1", status="done", filename="y.pdf"))
    await db_session.commit()

    @asynccontextmanager
    async def _reuse():
        yield db_session
    monkeypatch.setattr(imp, "_job_session", _reuse)

    n = await imp.fail_orphaned_jobs()
    assert n == 1
    orphan = (await db_session.execute(_sel(ImportJob).where(ImportJob.id == "orphan1"))).scalar_one()
    assert orphan.status == "error" and orphan.http_status == 503
    done = (await db_session.execute(_sel(ImportJob).where(ImportJob.id == "done1"))).scalar_one()
    assert done.status == "done"  # untouched


async def test_kyc_date_field_rejects_non_date(db_session):
    """A non-date in an issue/expiry field (e.g. the place of issue 'ABU DHABI')
    is dropped, not stored; a real date is normalised and kept."""
    from app.models.crm import CustomerProfile
    from sqlalchemy import select as _sel
    await doc_ingest.persist_customer(db_session, {
        "account_no": "350994", "name": "Azoora",
        "fields": {"trade_license_issue": "ABU DHABI", "trade_license_expiry": "10/03/2027"},
    }, "t")
    await db_session.commit()
    cp = (await db_session.execute(_sel(CustomerProfile).where(
        CustomerProfile.account_no == "350994"))).scalar_one()
    assert (cp.trade_license_issue or "") == ""        # place-of-issue dropped
    assert cp.trade_license_expiry == "10/03/2027"      # real date kept


def test_merge_customer_reassembles_lists_across_chunks():
    """A record split across PDF chunks (type in one, details in another) is
    field-merged, not dropped or duplicated."""
    into = {"properties": [{"prop_type": "Land & Building"}], "partners": [{"name": "Ali"}]}
    more = {"properties": [{"prop_type": "Land & Building", "address": "Deira", "valuation": "15000000"}],
            "partners": [{"name": "Sara", "nationality": "Iran"}],
            "facilities": [{"facility_type": "overdraft", "amount": "500000"}]}
    doc_ingest.merge_customer(into, more)
    assert len(into["properties"]) == 1  # field-merged, not duplicated
    assert into["properties"][0]["address"] == "Deira" and into["properties"][0]["valuation"] == "15000000"
    assert len(into["partners"]) == 2
    assert into["facilities"][0]["facility_type"] == "overdraft"


def test_split_pdf_and_offset():
    import io
    import pytest
    PdfWriter = pytest.importorskip("pypdf").PdfWriter  # prod-only dep
    w = PdfWriter()
    for _ in range(5):
        w.add_blank_page(width=200, height=200)
    buf = io.BytesIO(); w.write(buf)
    chunks, n = doc_ingest.split_pdf(buf.getvalue(), max_bytes=10_000_000, max_pages=2)
    assert n == 5 and len(chunks) == 3 and chunks[0][0] == 1 and chunks[1][0] == 3
    assert doc_ingest.offset_pages("1-2", 2) == "3-4"
