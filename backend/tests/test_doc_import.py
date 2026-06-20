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
              "emirates_id_golden", "nationality", "trade_license_issue", "auditor"):
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
