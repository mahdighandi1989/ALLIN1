"""v105 — voucher Excel template export: the spec becomes a real .xlsx laid out
like the printed slip (banner, OUR REF box, signatures, thick frame) with an A4
fit-to-one-page print setup, so filling it later in Excel prints the same."""
import base64
import io

from openpyxl import load_workbook

# a 1x1 red PNG — stands in for the bundled bank logo
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)
_LOGO = "data:image/png;base64," + base64.b64encode(_PNG).decode()


def _payload():
    return {
        "mode": "irr",
        "logo_png": _LOGO,
        "slips": [
            {"kind": "DEBIT", "title": "SECURITY DOC IRR TD", "date": "07/08/2026",
             "ac_no": "2624-800016-901-090", "amount": "1", "amount_boxed": True,
             "our_ref": "271520 _ STF1260603000001",
             "description": "CHQ NO 536001/237986  FOR IRR 6,383,360,000,000/-   RATE@ IRR 398,960/-",
             "ac_name": "SATIN STAR TRADING LLC",
             "extra_lines": ["LOAN AMOUNT AED 8,000,000/- FOR 48 MONTHS @ 200% LOAN AMOUNT",
                              "IRR CHQ FOR M/s Hani pokht iraninan (karafarin bank - 5300114)"]},
            {"kind": "CREDIT", "title": "SECURITIES", "date": "07/08/2026",
             "ac_no": "2624-869999-901-590", "amount": "1", "amount_boxed": True,
             "our_ref": "271520 _ STF1260603000001",
             "description": "CHQ NO 536001/237986", "ac_name": "SATIN STAR TRADING LLC",
             "extra_lines": []},
        ],
    }


async def test_voucher_excel_export(client, auth_headers):
    r = await client.post("/api/vouchers/export-excel", headers=auth_headers, json=_payload())
    assert r.status_code == 200, r.text
    assert "spreadsheetml" in r.headers["content-type"]
    wb = load_workbook(io.BytesIO(r.content))
    ws = wb["Voucher"]

    # both slips landed with their content
    vals = [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]
    for needle in ("DEBIT", "CREDIT", "SECURITY DOC IRR TD", "SECURITIES",
                   "2624-800016-901-090", "2624-869999-901-590",
                   "AMOUNT / QUANTITY", "OUR REF :", "Prepared By.", "Authorized Signatures"):
        assert any(needle in v for v in vals), f"missing: {needle}"
    # digit-for-digit IRR line survived
    assert any("6,383,360,000,000" in v for v in vals)
    assert any("karafarin bank - 5300114" in v for v in vals)

    # banner is the lavender merged row
    banner = next(c for row in ws.iter_rows() for c in row if c.value == "SECURITY DOC IRR TD")
    assert banner.fill.fgColor.rgb.endswith("CCCCFF")

    # A4 fit-to-one-page print setup mirroring the web print
    assert str(ws.page_setup.paperSize) == str(ws.PAPERSIZE_A4)
    assert ws.page_setup.orientation == "portrait"
    assert int(ws.page_setup.fitToWidth) == 1 and int(ws.page_setup.fitToHeight) == 1
    assert ws.print_area

    # the logo image is embedded once per slip
    assert len(ws._images) == 2


async def test_voucher_excel_requires_auth(client):
    r = await client.post("/api/vouchers/export-excel", json=_payload())
    assert r.status_code in (401, 403)


async def test_voucher_excel_rejects_bad_logo(client, auth_headers):
    p = _payload()
    p["logo_png"] = "data:text/html;base64,PGh0bWw+"   # not an image → silently no logo
    r = await client.post("/api/vouchers/export-excel", headers=auth_headers, json=p)
    assert r.status_code == 200
    ws = load_workbook(io.BytesIO(r.content))["Voucher"]
    assert len(ws._images) == 0
