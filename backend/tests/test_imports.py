"""Tests for the Excel import endpoints."""
import io

import openpyxl
import pytest
from httpx import AsyncClient

from app.models.customer import Customer, AccountType, CustomerStatus


def _xlsx(header, rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _xls(header, rows) -> bytes:
    """Build a legacy binary .xls workbook (OLE2) for the xlrd read path."""
    import xlwt

    wb = xlwt.Workbook()
    ws = wb.add_sheet("Sheet1")
    for c, h in enumerate(header):
        ws.write(0, c, h)
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            ws.write(r, c, val)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _file(content: bytes, name="data.xlsx"):
    return {"file": (name, content,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


class TestCustomerImport:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.post("/api/imports/customers", files=_file(_xlsx(["a"], [])))).status_code == 401

    async def test_import_creates_and_reports(self, client: AsyncClient, auth_headers: dict):
        content = _xlsx(
            ["account_no", "name", "account_type", "email"],
            [["IMP-1", "Imported Co", "corporate", "a@b.ae"],
             ["IMP-2", "", ""],                       # missing name -> error
             ["IMP-1", "Dup", "retail"]],             # duplicate in file -> error
        )
        r = await client.post("/api/imports/customers", files=_file(content), headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["created"] == 1
        assert body["total_rows"] == 3
        assert len(body["errors"]) == 2

        # the created customer is now listed
        listing = await client.get("/api/customers/?search=IMP-1", headers=auth_headers)
        assert listing.json()["total"] == 1

    async def test_dry_run_writes_nothing(self, client: AsyncClient, auth_headers: dict):
        content = _xlsx(["account_no", "name"], [["DRY-1", "Dry Co"]])
        r = await client.post("/api/imports/customers?dry_run=true", files=_file(content), headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["created"] == 0
        assert r.json()["would_create"] == 1
        assert (await client.get("/api/customers/?search=DRY-1", headers=auth_headers)).json()["total"] == 0

    async def test_skip_existing(self, client: AsyncClient, auth_headers: dict, db_session):
        db_session.add(Customer(account_no="EXIST-1", name="Already Here",
                                account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE))
        await db_session.commit()
        content = _xlsx(["account_no", "name"], [["EXIST-1", "Dupe"]])
        r = await client.post("/api/imports/customers", files=_file(content), headers=auth_headers)
        assert r.json()["created"] == 0 and r.json()["skipped_existing"] == 1

    async def test_bad_extension_400(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/imports/customers",
                              files={"file": ("data.txt", b"hi", "text/plain")}, headers=auth_headers)
        assert r.status_code == 400

    async def test_corrupt_file_reports_clear_error(self, client: AsyncClient, auth_headers: dict):
        # Right extension, but the bytes are not a real workbook -> precise 400.
        r = await client.post("/api/imports/customers",
                              files=_file(b"this is definitely not a spreadsheet"),
                              headers=auth_headers)
        assert r.status_code == 400
        assert "Invalid spreadsheet" in r.json()["detail"]

    async def test_missing_required_column_400(self, client: AsyncClient, auth_headers: dict):
        # No account_no column at all -> fail fast with a column-level message
        # (instead of the same per-row error on every row).
        content = _xlsx(["name", "email"], [["Acme", "a@b.ae"]])
        r = await client.post("/api/imports/customers", files=_file(content), headers=auth_headers)
        assert r.status_code == 400
        assert "account_no" in r.json()["detail"]

    async def test_header_only_file_imports_nothing(self, client: AsyncClient, auth_headers: dict):
        content = _xlsx(["account_no", "name"], [])
        r = await client.post("/api/imports/customers", files=_file(content), headers=auth_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["total_rows"] == 0 and body["created"] == 0

    async def test_legacy_xls_format_supported(self, client: AsyncClient, auth_headers: dict):
        content = _xls(["account_no", "name", "account_type"], [["XLS-1", "Legacy Co", "corporate"]])
        r = await client.post("/api/imports/customers",
                              files=_file(content, name="legacy.xls"), headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["created"] == 1
        listing = await client.get("/api/customers/?search=XLS-1", headers=auth_headers)
        assert listing.json()["total"] == 1

    async def test_template_download(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/imports/customers/template", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert "account_no" in r.content.decode("utf-8")


class TestFacilityImport:
    async def test_import_links_to_customer(self, client: AsyncClient, auth_headers: dict, test_customer):
        content = _xlsx(
            ["account_no", "name", "facility_type", "amount", "interest_rate"],
            [[test_customer.account_no, "Imported Loan", "loan", "750000", "6.0"],
             ["NO-SUCH", "Orphan", "loan", "1000", ""]],
        )
        r = await client.post("/api/imports/facilities", files=_file(content), headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["created"] == 1
        assert any("no customer" in e["error"] for e in r.json()["errors"])

    async def test_invalid_amount_reported(self, client: AsyncClient, auth_headers: dict, test_customer):
        content = _xlsx(["account_no", "amount"], [[test_customer.account_no, "not-a-number"]])
        r = await client.post("/api/imports/facilities", files=_file(content), headers=auth_headers)
        assert r.json()["created"] == 0
        assert len(r.json()["errors"]) == 1

    async def test_missing_amount_column_400(self, client: AsyncClient, auth_headers: dict, test_customer):
        content = _xlsx(["account_no", "name"], [[test_customer.account_no, "No Amount"]])
        r = await client.post("/api/imports/facilities", files=_file(content), headers=auth_headers)
        assert r.status_code == 400
        assert "amount" in r.json()["detail"]
