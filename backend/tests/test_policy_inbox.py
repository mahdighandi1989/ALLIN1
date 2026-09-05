"""v117 — Drive policy inbox: mapping-Excel parsing (flexible Persian headers,
Persian digits), UNIQUE matching (ambiguity is refused, never guessed), the
{branch}-{account}-{original} rename rule, and the endpoints' clean failure
when Drive isn't configured."""
import io

import openpyxl

from app.services import policy_inbox as box


def _xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parse_mapping_workbook_flexible_headers_and_persian_digits():
    data = _xlsx([
        ["جدول وثایق ۱۴۰۵"],  # title row above the header must not confuse it
        ["ردیف", "نام مشتری", "شماره حساب", "شعبه", "کد رایانه بیمه نامه", "شماره بیمه نامه"],
        [1, "WORLDSTAR TRADING", "۲۶۲۴-۱۱۵۵۲۴-۰۱۱", "2624", "۴۹۸۸۵۲۹", "05/2/2/60/2216"],
        [2, "Beta Co", "330011", "2624", 5011223, "05/2/2/60/9999"],
        [3, "بدون حساب", "", "2624", "777", ""],
    ])
    r = box.parse_mapping_workbook(data)
    assert r["ok"], r
    assert len(r["rows"]) == 2                    # the account-less row dropped…
    assert any("بدونِ شماره حساب" in w for w in r["warnings"])  # …loudly
    assert box.norm_digits(r["rows"][0]["account"]) == "2624115524011"
    assert box.norm_digits(r["rows"][0]["computer_code"]) == "4988529"
    assert box.norm_digits(r["rows"][1]["computer_code"]) == "5011223"  # int cell


def test_parse_mapping_workbook_rejects_headerless_sheet():
    r = box.parse_mapping_workbook(_xlsx([["فقط متن"], ["الف", "ب"]]))
    assert not r["ok"] and "سطرِ عنوان" in r["error"]


def test_match_row_precedence_ambiguity_and_no_guess():
    rows = [
        {"account": "115524", "branch": "2624", "computer_code": "4988529", "policy_no": "2216", "national_id": ""},
        {"account": "330011", "branch": "2624", "computer_code": "5011223", "policy_no": "2216", "national_id": ""},
    ]
    # computer_code decides even though policy_no is ambiguous
    row, how = box.match_row({"computer_code": "۴۹۸۸۵۲۹", "policy_no": "2216"}, rows)
    assert row["account"] == "115524" and how == "computer_code"
    # ambiguous-only ⇒ refused with the tried keys in the reason
    row, why = box.match_row({"policy_no": "2216"}, rows)
    assert row is None and "policy_no" in why
    # nothing readable ⇒ refused
    row, why = box.match_row({"computer_code": "12"}, rows)  # under min length
    assert row is None
    # national_id as the last-resort key
    rows[0]["national_id"] = "0053281144"
    row, how = box.match_row({"national_id": "۰۰۵۳۲۸۱۱۴۴"}, rows)
    assert row["account"] == "115524" and how == "national_id"


def test_build_new_name_and_idempotence():
    n = box.build_new_name("۲۶۲۴", "2624-115524-011", "CamScanner 31-08.pdf")
    assert n == "2624-2624115524011-CamScanner 31-08.pdf"
    assert box.already_named(n)
    assert not box.already_named("CamScanner 31-08.pdf")
    # no branch column ⇒ account-only prefix still attributes the import (v85)
    assert box.build_new_name("", "115524", "x.pdf") == "115524-x.pdf"


async def test_endpoints_fail_clean_without_drive(client, auth_headers, monkeypatch):
    from app.services import drive_sync
    monkeypatch.setattr(drive_sync, "is_enabled", lambda: False)
    for path in ("/api/policy-inbox/ensure", "/api/policy-inbox/scan"):
        r = await client.post(path, headers=auth_headers, json={})
        assert r.status_code == 503, (path, r.status_code, r.text)
        assert "Drive" in r.json()["detail"]
    r = await client.post("/api/policy-inbox/apply", headers=auth_headers, json={})
    assert r.status_code == 503
    r = await client.post("/api/policy-inbox/import-file", headers=auth_headers,
                          json={"file_id": "x"})
    assert r.status_code == 503
