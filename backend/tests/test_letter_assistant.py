"""The AI letter-assistant's deterministic gate — the part that makes it SAFE.

The model only ever *proposes*; ``parse_and_validate`` is what decides which
proposals are safe to hand to the client. These tests lock that behavior:
- a text_replace whose ``find`` is not in the letter is DROPPED (hallucination guard),
- set_field is restricted to the scalar allow-list (never the HTML body),
- notes are always kept (advisory),
- malformed / unknown ops are dropped,
- html_to_text + build_facts produce the plain context the guard relies on.
"""
from app.services import letter_assistant as la


FIELDS = {
    "subject": "درخواست صدور ضمانت‌نامه",
    "recipientName": "جناب آقای احمدی",
    "body": "<div>با سلام و احترام،</div><div>بدین‌وسیله مبلغ ۵۰،۰۰۰ درهم بابت تسهیلات اعطا گردید.</div>"
            "<table><tr><td>ردیف</td><td>مبلغ</td></tr><tr><td>۱</td><td>۵۰۰۰۰</td></tr></table>",
    "classification": "عادی",
}


def _call(model_changes):
    import json
    raw = json.dumps({"changes": model_changes}, ensure_ascii=False)
    return la.parse_and_validate(raw, FIELDS)


def test_text_replace_present_is_kept():
    out = _call([{
        "op": "text_replace", "field": "body", "category": "spelling",
        "title": "اصلاح", "detail": "", "severity": "low",
        "find": "اعطا گردید", "replace": "اعطا شد",
    }])
    assert len(out) == 1
    assert out[0]["op"] == "text_replace"
    assert out[0]["applicable"] is True
    assert out[0]["find"] == "اعطا گردید"
    assert out[0]["after"] == "اعطا شد"


def test_text_replace_absent_is_dropped_hallucination_guard():
    out = _call([{
        "op": "text_replace", "field": "body",
        "title": "x", "find": "این عبارت در نامه وجود ندارد", "replace": "چیزی",
    }])
    assert out == []


def test_text_replace_whitespace_normalized_match():
    # ZWNJ / double-space variant of a present phrase still matches.
    out = _call([{
        "op": "text_replace", "field": "body",
        "title": "x", "find": "با  سلام و احترام", "replace": "با سلام",
    }])
    assert len(out) == 1


def test_set_field_scalar_ok_body_rejected():
    ok = _call([{
        "op": "set_field", "field": "subject",
        "title": "موضوع رساتر", "after": "درخواست صدور ضمانت‌نامهٔ بانکی",
    }])
    assert len(ok) == 1 and ok[0]["op"] == "set_field" and ok[0]["applicable"]

    body_set = _call([{"op": "set_field", "field": "body", "after": "متن کامل جدید"}])
    assert body_set == []  # body is never wholesale-set


def test_set_field_unknown_field_dropped():
    assert _call([{"op": "set_field", "field": "nonexistent", "after": "x"}]) == []


def test_note_always_kept_but_not_applicable():
    out = _call([{
        "op": "note", "field": "body", "category": "tables",
        "title": "ستون مبلغ واحد ندارد", "detail": "بهتر است واحد (درهم) به سرستون افزوده شود",
        "severity": "low",
    }])
    assert len(out) == 1
    assert out[0]["applicable"] is False
    assert out[0]["category"] == "tables"


def test_malformed_and_unknown_ops_dropped():
    out = _call([
        "not a dict",
        {"op": "delete_everything", "field": "body"},
        {"op": "text_replace", "field": "body"},  # missing find/replace
        {"op": "set_field", "field": "subject"},   # missing after
    ])
    assert out == []


def test_category_and_severity_are_sanitized():
    out = _call([{
        "op": "note", "field": "body", "category": "BOGUS", "severity": "critical",
        "title": "t",
    }])
    assert out[0]["category"] == "other"
    assert out[0]["severity"] == "medium"


def test_max_changes_cap():
    many = [{"op": "note", "field": "body", "title": f"n{i}"} for i in range(200)]
    assert len(_call(many)) == la.MAX_CHANGES


def test_html_to_text_strips_tags_and_tables():
    txt = la.html_to_text("<div>خط اول</div><table><tr><td>الف</td><td>ب</td></tr></table>")
    assert "خط اول" in txt
    assert "الف" in txt and "ب" in txt
    assert "<" not in txt


def test_build_facts_shape():
    class C:
        name = "شرکت نمونه"; name_ar = ""; account_no = "123456"
        account_type = "corporate"; branch = "2624"

    class F:
        name = "OD"; facility_type = "overdraft"; amount = 100000
        currency = "AED"; interest_rate = 12; tenor_months = "12"
        installments = "12"; purpose = "سرمایه در گردش"; status = "active"; expiry_date = None

    facts = la.build_facts(C(), {"POBox": "4182"}, [F()], [])
    assert facts["customer"]["account_no"] == "123456"
    assert facts["facilities"][0]["type"] == "overdraft"
    assert facts["facilities"][0]["amount"] == "100,000.00"
    assert facts["profile"]["POBox"] == "4182"


def test_build_user_prompt_includes_body_and_facts():
    p = la.build_user_prompt(FIELDS, {"customer": {"name": "x"}}, ["spelling"], instruction="کوتاه کن")
    assert "body" in p and "اعطا گردید" in p
    assert "حقایقِ پایگاه‌داده" in p
    assert "کوتاه کن" in p


def test_build_user_prompt_enumerates_multiple_selections():
    # Each gathered snippet is listed as its own numbered validation target.
    p = la.build_user_prompt(
        FIELDS, {}, ["validation"],
        selections=["مبلغ ۵۰،۰۰۰ درهم", "جناب آقای احمدی", "مبلغ ۵۰،۰۰۰ درهم"],  # dup collapses
    )
    assert "موارد انتخاب‌شده" in p
    assert "1. «مبلغ ۵۰،۰۰۰ درهم»" in p
    assert "2. «جناب آقای احمدی»" in p
    assert "3." not in p.split("موارد انتخاب‌شده")[1][:200]  # duplicate did not add a 3rd


def test_build_user_prompt_merges_legacy_selection_with_list():
    p = la.build_user_prompt(FIELDS, {}, ["validation"], selection="عبارتِ قدیمی", selections=["عبارتِ نو"])
    assert "عبارتِ قدیمی" in p and "عبارتِ نو" in p


# ---------------- table_replace (full AI table redesign, sanitized) ----------------

def test_sanitize_table_html_whitelists():
    dirty = ('<table onclick="x()"><tr data-r="r1" style="color:red;text-align:center">'
             '<th style="width:30%;background:#eee">A</th>'
             '<td colspan="2">v<script>alert(1)</script></td>'
             '<td><a href="http://evil">link</a><img src=x onerror=y><b>ok</b></td></tr></table>')
    clean = la.sanitize_table_html(dirty)
    assert clean.startswith("<table>")
    assert "script" not in clean and "onclick" not in clean and "img" not in clean and "href" not in clean
    assert 'colspan="2"' in clean
    assert "width:30%" in clean and "background:#eee" in clean
    assert "color:red" not in clean and "text-align:center" in clean  # style whitelist
    assert "<b>ok</b>" in clean
    assert "alert(1)" not in clean  # script CONTENT dropped too, not just the tag


def test_sanitize_table_html_rejects_non_tables():
    assert la.sanitize_table_html("<div>hi</div>") == ""
    assert la.sanitize_table_html("plain text") == ""
    assert la.sanitize_table_html("<table></table>") == ""  # no rows → not a real table


def test_table_replace_validated_against_range_and_sanitizer():
    import json as _json
    raw = _json.dumps({"changes": [
        {"op": "table_replace", "table_index": 1, "title": "ادغام ستون‌ها",
         "html": "<table><tr><th>الف</th></tr><tr><td>۱</td></tr></table>"},
        {"op": "table_replace", "table_index": 5, "title": "خارج از محدوده",
         "html": "<table><tr><td>x</td></tr></table>"},
        {"op": "table_replace", "table_index": 2, "title": "HTML غیرجدولی",
         "html": "<div>not a table</div>"},
    ]}, ensure_ascii=False)
    out = la.parse_and_validate(raw, FIELDS, tables_count=2)
    assert len(out) == 1
    c = out[0]
    assert c["op"] == "table_replace" and c["table_index"] == 1 and c["applicable"] is True
    assert c["html"].startswith("<table>")
    # with NO tables provided, table_replace is never accepted
    assert la.parse_and_validate(raw, FIELDS, tables_count=0) == []


def test_build_user_prompt_table_rules():
    p = la.build_user_prompt(FIELDS, {}, ["tables"], instruction="ستون مبلغ را جدا کن",
                             tables=["<table><tr><td>a</td></tr></table>"])
    assert "[جدول 1]" in p
    assert "table_replace" in p
    assert "رفتارِ پیش‌فرضِ ابزارِ جداول" in p          # default when no table instruction
    assert "بخش‌های غیرمرتبط با جدول" in p             # mixed-instruction routing


def test_build_user_prompt_table_fill_is_db_aware():
    # Filling a table's CONTENT must be sourced ONLY from the DB-facts block:
    # found items copied verbatim, missing items left «—» + reported in a note,
    # nothing ever invented — and no fabrication on general (fact-less) letters.
    p = la.build_user_prompt(FIELDS, {"customer": {"name": "x"}}, ["tables"],
                             instruction="جدول را با مشخصات تسهیلات پر کن",
                             tables=["<table><tr><td>a</td></tr></table>"])
    assert "پر کردن/تکمیلِ محتوای جدول" in p
    assert "تنها منبعِ مجازِ داده" in p and "«حقایقِ پایگاه‌داده»" in p
    assert "customer/facilities/guarantors/profile" in p     # where to look things up
    assert "اگر یافت نشد، خانه را «—» بگذار" in p            # missing ⇒ blank, not invented
    assert "هرگز عدد، تاریخ، نام یا مبلغی را حدس نزن" in p   # anti-hallucination
    assert "نامهٔ عمومی/بدونِ حساب" in p                     # fact-less letters ⇒ say so
    # the tables tool guide itself also carries the DB-only rule
    assert "حقایقِ پایگاه‌داده" in la.TOOLS["tables"]["guide"]


# ---------------- new tools: complete / inline_prompts (owner request) ----------------

def test_new_tools_registered_with_binding_guides():
    """The formalize/complete/inline-prompt behaviors the owner asked for are
    encoded in the tool guides the model actually receives."""
    assert "complete" in la.TOOLS and "inline_prompts" in la.TOOLS
    # professional now explicitly covers FULL and PARTIAL colloquial rewriting
    assert "عامیانه" in la.TOOLS["professional"]["guide"]
    assert "وسطِ متنِ رسمی" in la.TOOLS["professional"]["guide"]
    # complete recognizes the lone «؟» as a stuck-sentence placeholder
    g = la.TOOLS["complete"]["guide"]
    assert "؟" in g and "نیمه‌کاره" in g and "تکرار" in g
    # inline prompts: execute in-text instructions, DB-facts-only, db_write on «ثبت»
    gi = la.TOOLS["inline_prompts"]["guide"]
    assert "دستور" in gi and "حقایقِ پایگاه‌داده" in gi and "db_write" in gi


def test_new_categories_survive_validation():
    out = _call([
        {"op": "text_replace", "field": "body", "category": "complete",
         "title": "تکمیل جمله", "find": "اعطا گردید", "replace": "اعطا گردیده است."},
        {"op": "text_replace", "field": "body", "category": "inline_prompts",
         "title": "اجرای دستور", "find": "با سلام و احترام،", "replace": "با سلام و احترام؛"},
    ])
    assert [c["category"] for c in out] == ["complete", "inline_prompts"]
    assert all(c["applicable"] for c in out)


def test_build_user_prompt_carries_new_tool_guides():
    p = la.build_user_prompt(FIELDS, {}, ["complete", "inline_prompts"])
    assert "علامتِ سؤالِ تنها" in p or "علامتِ سؤال" in p
    assert "دستورِ نویسنده خطاب به تو" in p or "دستور" in p
