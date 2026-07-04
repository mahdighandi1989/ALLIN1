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
