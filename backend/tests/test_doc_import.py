"""AI document import: the .docx fast-path persists across the right customer
(no AI key needed), the JSON parser is tolerant, and multi-customer persist is
deduped (re-import never duplicates guarantors)."""
from io import BytesIO

from docx import Document

from app.models.customer import Customer
from app.services import doc_ingest


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


async def test_analyze_docx_fastpath(client, auth_headers, db_session):
    db_session.add(Customer(account_no="115524", name="Old"))
    await db_session.commit()
    files = {"file": ("efco.docx", _draft_docx(),
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    r = await client.post("/api/imports/analyze", headers=auth_headers, files=files)
    assert r.status_code == 200, r.text
    b = r.json()
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


async def test_analyze_xlsx_reaches_branch(client, auth_headers):
    # No AI key in tests → the spreadsheet branch parses then reports no usable
    # model (400), proving the Excel path is wired (not a 415/500).
    files = {"file": ("book.xlsx", _xlsx_bytes(),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    r = await client.post("/api/imports/analyze", headers=auth_headers, files=files)
    assert r.status_code in (400, 502), r.text


async def test_reupload_same_file_no_duplicate_review(client, auth_headers, db_session):
    db_session.add(Customer(account_no="115524", name="X"))
    await db_session.commit()
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    for _ in range(2):  # upload + extract the SAME file twice
        r = await client.post("/api/imports/analyze", headers=auth_headers,
                              files={"file": ("efco.docx", _draft_docx(), mime)})
        assert r.status_code == 200, r.text
    rc = await client.get("/api/crm/credit-reviews/115524", headers=auth_headers)
    assert len(rc.json()) == 1  # deduped per review date — not duplicated on re-upload
