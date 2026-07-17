"""The AI letter-assistant's deterministic gate — the part that makes it SAFE.

The model only ever *proposes*; ``parse_and_validate`` is what decides which
proposals are safe to hand to the client. These tests lock that behavior:
- a text_replace whose ``find`` is not in the letter is DROPPED (hallucination guard),
- set_field is restricted to the scalar allow-list (never the HTML body),
- notes are always kept (advisory),
- malformed / unknown ops are dropped,
- html_to_text + build_facts produce the plain context the guard relies on.
"""
import json

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
    assert "منابعِ مجازِ داده" in p and "«حقایقِ پایگاه‌داده»" in p
    assert "customer/facilities/guarantors/profile" in p     # where to look things up
    assert "اگر هیچ‌جا یافت نشد، خانه را «—» بگذار" in p       # missing ⇒ blank, not invented
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


def test_prose_quality_rules_reach_the_model():
    """Owner complaints (v54): repeated words in the final letter, wrong register
    toward a SUPERIOR office, and dry/unpleasant prose. The counter-rules must be
    in the guides/system prompt the model actually receives."""
    gp = la.TOOLS["professional"]["guide"]
    # anti-repetition judged on the ASSEMBLED final text, across paragraphs
    assert "متنِ نهاییِ سرهم‌شده" in gp and "بین‌پاراگرافی" in gp
    # pleasant, seasoned prose — not stacked boilerplate
    assert "دلنشین" in gp and "نامه‌نگارِ باسابقه" in gp
    # hierarchy-aware register: deferential to superiors, directive only downward
    sp = la.SYSTEM_PROMPT
    assert "سلسله‌مراتبِ مخاطب" in sp
    assert "خواهشمند است دستور فرمایید" in sp and "به استحضار می‌رساند" in sp
    assert "مقتضی است" in sp  # named as the form FORBIDDEN toward superiors
    # lexical-variety rule on the final result exists at system level too
    assert "تنوعِ واژگانی" in sp
    # v55: the craft-of-request rules with bad=>good exemplars (owner: childish
    # passive chains, empty filler, doubled request openers)
    assert "هنرِ درخواستِ اداری" in sp
    assert "اعلام گردد که" in sp            # the banned nested-passive chain, shown explicitly
    assert "جهت انجام اقدامات لازم" in sp   # the banned empty filler, shown explicitly
    assert "حداکثر یک بار" in sp            # one «خواهشمند است» per letter
    assert "بد:" in sp and "خوب:" in sp     # few-shot exemplars actually present
    # v56: punctuation / closed sentences / paragraph discipline (owner: run-on
    # sentences without periods, missing commas, paragraphs mashed together)
    assert "نقطه‌گذاری" in sp and "با نقطه بسته می‌شود" in sp
    assert "ویرگولِ فارسی" in sp
    assert "اقدامات لازم مقتضی" in sp       # stacked-filler ban, shown explicitly
    assert "ادغام نکن" in sp                # replaces must not merge paragraphs


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


def test_find_guard_accepts_arabic_yeh_kaf_and_zwnj_variants():
    """v51: the model often emits Arabic ي/ك or plain spaces where the letter
    has Persian ی/ک or ZWNJ — the find-guard must still locate the snippet."""
    from app.services.letter_assistant import _norm_ws
    letter = "بیمه‌نامه‌های املاک رهنی مرتبط با حساب‌های شعب"
    model_find = "بيمه نامه هاي املاك رهني مرتبط با حساب هاي شعب"
    assert _norm_ws(model_find) in _norm_ws(letter)


def test_build_facts_includes_account_activity_logs():
    """v66: the account's audit trail + journal lines land in the facts, capped
    and newest-first as given, so «از لاگ‌ها استخراج کن» works from the DB."""
    from app.models.crm import JournalEntry

    class C:
        name = "شرکت نمونه"; name_ar = ""; account_no = "123456"
        account_type = "corporate"; branch = "2624"

    class A:
        def __init__(self, i):
            self.created_at = f"2026-07-1{i % 5} 12:00"
            self.username = "mahdi"; self.action = "update"
            self.entity_type = "letter"; self.detail = "ویرایش   نامهٔ  رسمی" + "x" * 400

    j = JournalEntry(id="j1", account_no="123456", category="letters",
                     item="صدور نامه", status="done", date="2026-07-14",
                     user="mahdi", notes="نامهٔ ترهین")
    facts = la.build_facts(C(), {}, [], [], audit_logs=[A(i) for i in range(45)],
                           journal_entries=[j])
    log = facts["account_activity_log"]
    assert len(log) == 40  # capped
    assert log[0]["user"] == "mahdi" and log[0]["action"] == "update"
    assert "ویرایش نامهٔ رسمی" in log[0]["detail"]  # whitespace normalized
    assert len(log[0]["detail"]) <= 300  # truncated
    jl = facts["journal_log"]
    assert jl[0]["item"] == "صدور نامه" and jl[0]["status"] == "done"
    # absent logs → keys absent (facts stay compact)
    lean = la.build_facts(C(), {}, [], [])
    assert "account_activity_log" not in lean and "journal_log" not in lean


def test_build_user_prompt_explains_log_keys():
    p = la.build_user_prompt(FIELDS, {"account_activity_log": [{"action": "update"}]},
                             ["validation"], instruction="")
    assert "account_activity_log" in p and "لاگِ کارهای همین حساب" in p


def test_parse_need_logs_and_rule15():
    """v67: the model can ask for a FULL log search instead of a changes payload."""
    assert "need_logs" in la.SYSTEM_PROMPT and "15)" in la.SYSTEM_PROMPT
    q = la.parse_need_logs('{"need_logs": {"scope": "audit", "text": "ترهین", "junk": "x"}}')
    assert q == {"scope": "audit", "text": "ترهین"}
    # a normal changes reply is NOT a need_logs request
    assert la.parse_need_logs('{"changes": []}') is None
    assert la.parse_need_logs("garbage") is None
    # the facts header advertises the protocol
    p = la.build_user_prompt(FIELDS, {}, ["validation"], instruction="")
    assert "need_logs" in p


def test_table_insert_validation_and_sanitizer():
    """v68: the model can CREATE a new table (op=table_insert) — no pre-existing
    or selected table needed; HTML passes the same whitelist sanitizer."""
    raw = json.dumps({"changes": [
        {"op": "table_insert", "category": "tables", "title": "جدول اقساط",
         "html": "<table><tr><th>ماه</th></tr><tr><td>فروردین<script>x()</script></td></tr></table>",
         "table_title": "ج" * 200, "placement": "attachment"},
        {"op": "table_insert", "title": "پیش‌فرض بدنه",
         "html": "<table><tr><td>الف</td></tr></table>", "placement": "بی‌معنا"},
        {"op": "table_insert", "title": "غیرجدول", "html": "<div>نه جدول</div>"},
    ]}, ensure_ascii=False)
    out = la.parse_and_validate(raw, {"body": "<div>متن</div>"}, tables_count=0)
    ins = [c for c in out if c["op"] == "table_insert"]
    assert len(ins) == 2  # the non-table html is dropped
    att, body = ins[0], ins[1]
    assert att["placement"] == "attachment"
    assert "<script>" not in att["html"] and "فروردین" in att["html"]
    assert len(att["table_title"]) == 120  # clamped
    assert att["applicable"] is True and "پیوستِ نامه" in att["after"]
    assert body["placement"] == "body"  # unknown placement → body


def test_table_insert_and_attachment_source_rules_reach_prompt():
    """v68 prompt wiring: creation rules ride with ANY non-empty instruction
    (zero tables needed), and attachment content is a legit fill source."""
    assert "table_insert" in la.SYSTEM_PROMPT
    assert "table_insert" in la.TOOLS["tables"]["guide"]
    p = la.build_user_prompt(FIELDS, {}, ["tables"], instruction="یک جدول اقساط بساز",
                             attachments_text=[{"name": "sanction.pdf", "text": "مبلغ ۵۰۰۰۰"}])
    assert "ساختِ جدولِ جدید" in p and "table_insert" in p
    assert "منبعِ مجازِ داده" in p            # attachments section grants fill access
    # without an instruction the creation block stays out (no op advertised for free)
    p2 = la.build_user_prompt(FIELDS, {}, ["tables"], instruction="")
    assert "ساختِ جدولِ جدید" not in p2
    # the fill rules (selected tables) now allow the attachments as a source
    p3 = la.build_user_prompt(FIELDS, {}, ["tables"], instruction="جدول را پر کن",
                              tables=["<table><tr><td>x</td></tr></table>"])
    assert "محتوای پیوست‌های نامه» (اگر در همین پیام هست)" in p3


def test_paragraph_merge_validation_and_guard():
    """v69: scattered pieces of one topic can be stitched across paragraph
    boundaries — every part must exist (verbatim or normalized) or the whole
    change is dropped; fewer than 2 parts is not a merge."""
    body = "<div>بانک مرکزی اعلام کرد.</div><div>موضوع دیگری.</div><div>که نرخ جدید ابلاغ شد.</div>"
    ok_raw = json.dumps({"changes": [
        {"op": "paragraph_merge", "category": "paragraphs", "title": "دوختن",
         "parts": ["بانک مرکزی اعلام کرد.", "که نرخ جدید ابلاغ شد."],
         "replace": "بانک مرکزی اعلام کرد که نرخ جدید ابلاغ شد."},
        {"op": "paragraph_merge", "title": "توهم",
         "parts": ["بانک مرکزی اعلام کرد.", "عبارتی که وجود ندارد"], "replace": "x"},
        {"op": "paragraph_merge", "title": "تک‌تکه", "parts": ["بانک مرکزی اعلام کرد."], "replace": "x"},
    ]}, ensure_ascii=False)
    out = la.parse_and_validate(ok_raw, {"body": body})
    pm = [c for c in out if c["op"] == "paragraph_merge"]
    assert len(pm) == 1  # hallucinated part + single-part merges are dropped
    assert pm[0]["field"] == "body" and len(pm[0]["parts"]) == 2
    assert pm[0]["applicable"] is True and "بدوز" not in pm[0]["replace"]
    # normalized matching (Arabic yeh / extra spaces) still locates the parts
    norm_raw = json.dumps({"changes": [
        {"op": "paragraph_merge", "title": "نرمال",
         "parts": ["بانك مركزي اعلام كرد.", "كه نرخ جديد ابلاغ شد."],
         "replace": "بانک مرکزی اعلام کرد که نرخ جدید ابلاغ شد."},
    ]}, ensure_ascii=False)
    assert len(la.parse_and_validate(norm_raw, {"body": body})) == 1


def test_paragraph_merge_and_holistic_rules_reach_prompt():
    assert "paragraph_merge" in la.SYSTEM_PROMPT
    assert "paragraph_merge" in la.TOOLS["paragraphs"]["guide"]
    assert "کل‌نگر" in la.TOOLS["paragraphs"]["guide"]
    assert "ابتر" in la.TOOLS["paragraphs"]["guide"]      # incomplete sentences named explicitly
    assert "جملهٔ ناتمام/ابتر" in la.SYSTEM_PROMPT        # rule 8 holistic re-read


def test_find_guard_tolerates_heh_hamza_forms():
    """v70: the editor stores the precomposed «ۀ» (U+06C0 — B Nazanin lacks the
    combining U+0654) while models often emit ه+hamza; the locate guard folds
    both to bare heh so neither form gets dropped as a hallucination."""
    body = "<div>گزارش سه‌ماهۀ نخست بانک</div>"
    raw = json.dumps({"changes": [{
        "op": "text_replace", "field": "body", "title": "ت", "category": "spelling",
        "find": "سه‌ماههٔ نخست", "replace": "سه‌ماهۀ اول"}]},
        ensure_ascii=False)
    out = la.parse_and_validate(raw, {"body": body})
    assert len(out) == 1 and out[0]["applicable"] is True
    # and the reverse direction (letter has the combining form, model the precomposed)
    body2 = "<div>گزارش سه‌ماههٔ نخست</div>"
    raw2 = json.dumps({"changes": [{
        "op": "text_replace", "field": "body", "title": "ت", "category": "spelling",
        "find": "سه‌ماهۀ نخست", "replace": "x"}]}, ensure_ascii=False)
    assert len(la.parse_and_validate(raw2, {"body": body2})) == 1


def test_inline_prompts_route_to_table_ops_and_aggregation_rules():
    """v72: an in-text instruction about a TABLE routes to the table ops with the
    same data sources; explicit aggregation is allowed with provenance; page-fit
    requests get an explanatory note (pagination is automatic, not a model op)."""
    g = la.TOOLS["inline_prompts"]["guide"]
    assert "table_replace" in g and "table_insert" in g
    assert "محتوای پیوست‌های نامه" in g
    assert "صفحه‌بندی" in g and "خودکار" in g
    # aggregation rules ride with the selected-tables block
    p = la.build_user_prompt(FIELDS, {}, ["tables", "inline_prompts"],
                             instruction="جدول را با جمعِ همهٔ شعب پر کن",
                             tables=["<table><tr><td>x</td></tr></table>"])
    assert "جمع/تجمیع فقط به‌درخواستِ صریحِ کاربر" in p
    assert "دو بار مستقل" in p and "قابلِ راستی‌آزمایی" in p
