"""v126 — repairing "custom PDF font encoding" mojibake.

A PDF whose embedded subset font uses a non-standard encoding hands every reader
of its text layer (an extractor, or an LLM given the PDF) reversibly scrambled
text. These tests pin both halves: the repair must be exact, and it must refuse
to touch anything that merely looks similar — above all Persian text using the
«…» quotation marks, whose characters sit inside the affected range.
"""
import pytest

from app.services import mojibake as mj

# Verified against a real garbled bank statement (a screenshot of the rendered
# letter): every one of these decoded to the obvious English original.
REAL_PAIRS = [
    ("Í¬¿¬»³»²¬ ÒÑ", "Statement NO"),
    ("ß½½±«²¬ Ò¿³»", "Account Name"),
    ("ß³±«²¬ (×ÎÎ)", "Amount (IRR)"),
    ("Ê¿´«» Ü¿¬»", "Value Date"),
    ("Ð®±°»®¬§ Ò±", "Property No"),
    ("ÒÑ", "NO"),
    ("ßÓ×Î ØÑÍÍÛ×Ò ÓÑÌßÙØ×", "AMIR HOSSEIN MOTAGHI"),
]


@pytest.mark.parametrize("garbled,plain", REAL_PAIRS)
def test_repairs_real_garbled_strings_exactly(garbled, plain):
    assert mj.repair_text(garbled) == plain


@pytest.mark.parametrize("garbled,plain", REAL_PAIRS)
def test_the_garbling_is_exactly_the_0x120_reflection(garbled, plain):
    """Re-derive the corruption from the plain text: every ASCII letter is
    reflected around 0x120 and everything else passes through. Reproducing the
    observed garbage from first principles is what proves the diagnosis."""
    forged = "".join(chr(0x120 - ord(c)) if c.isascii() and c.isalpha() else c for c in plain)
    assert forged == garbled
    # ...and `decode_char` inverts precisely that reflection
    assert "".join(mj.decode_char(c) for c in forged) == plain


def test_clean_latin_is_left_alone():
    for s in ["Statement NO", "Account Name", "Amount (IRR)", "AMIR HOSSEIN", "PDF 2026/09/22"]:
        assert mj.repair_text(s) == s


def test_persian_is_left_alone():
    for s in ["مشخصات املاک و صورت حساب", "شمارهٔ حساب ۲۷۱۵۲۰", "تسهیلات — ۱۴۰۵/۰۶/۳۱"]:
        assert mj.repair_text(s) == s


def test_persian_guillemets_are_never_mistaken_for_mojibake():
    """« (0xAB) and » (0xBB) sit inside the affected range and are standard
    Persian quotes — the single false positive worth designing against."""
    s = "نامِ شرکت «Alpha Trading LLC» ثبت شد"
    assert mj.repair_text(s) == s
    assert mj.count_garbled(s) == 0


def test_isolated_typographic_characters_are_not_touched():
    for s in ["۳۶°C", "±۵ درصد", "m² و m³", "بند § ۴"]:
        assert mj.repair_text(s) == s


def test_repairs_a_whole_table_block_cell_by_cell():
    block = ("Í¬¿¬»³»²¬ ÒÑ | ß½½±«²¬ Ò¿³» | ß³±«²¬ (×ÎÎ)\n"
             "4676/1570 | ßÓ×Î ØÑÍÍÛ×Ò ÓÑÌßÙØ× | 4,819,650")
    out = mj.repair_block(block)
    assert out == ("Statement NO | Account Name | Amount (IRR)\n"
                   "4676/1570 | AMIR HOSSEIN MOTAGHI | 4,819,650")
    assert mj.count_garbled(block) == 4          # the 4 garbled cells, not the numbers


def test_mixed_block_repairs_only_the_garbled_cells():
    block = "نامِ مشتری | ß½½±«²¬ Ò¿³» | ۱۲۳۴"
    assert mj.repair_block(block) == "نامِ مشتری | Account Name | ۱۲۳۴"


def test_numbers_and_dates_survive_untouched():
    """Only the 52 ASCII letters are remapped, which is why a garbled statement
    still shows correct amounts — the repair must not disturb them."""
    block = "182/4/567/2026 | 14/09/2026 | 4,819,650 | 56"
    assert mj.repair_block(block) == block
    assert mj.count_garbled(block) == 0


def test_empty_and_none_safe():
    assert mj.repair_text("") == ""
    assert mj.repair_block("") == ""
    assert mj.count_garbled("") == 0
    assert mj.looks_garbled("") is False


def test_a_single_stray_character_is_not_enough():
    assert mj.repair_text("درجه ± ۵") == "درجه ± ۵"
    assert mj.repair_text("5 ± 1") == "5 ± 1"


# --- v127: HTML / JSON aware repair -------------------------------------------

_TABLE = (
    '<table class="tblw" style="width:96%">'
    '<tr><th style="width:12%">ÒÑ</th><th style="width:30%">ß½½±«²¬ Ò¿³»</th><th>ß³±«²¬ (×ÎÎ)</th></tr>'
    '<tr><td>1</td><td colspan="2">ßÓ×Î ØÑÍÍÛ×Ò&nbsp;ÓÑÌßÙØ×</td></tr>'
    "</table>"
)


def test_repair_html_fixes_every_garbled_cell():
    out = mj.repair_html(_TABLE)
    for expected in (">NO<", ">Account Name<", ">Amount (IRR)<", "AMIR HOSSEIN&nbsp;MOTAGHI"):
        assert expected in out


def test_repair_html_never_touches_tags_attributes_or_widths():
    """Rewriting inside a tag would destroy the column widths the user set."""
    out = mj.repair_html(_TABLE)
    for kept in ('class="tblw"', "width:96%", "width:12%", "width:30%", 'colspan="2"'):
        assert kept in out
    assert out.count("<tr") == 2 and out.count("<td") == 2 and out.count("<th") == 3


def test_repair_html_keeps_entities_verbatim():
    assert "&nbsp;" in mj.repair_html(_TABLE)
    assert mj.repair_html("<p>&amp; &lt; &#1740;</p>") == "<p>&amp; &lt; &#1740;</p>"


def test_repair_html_is_idempotent():
    once = mj.repair_html(_TABLE)
    assert mj.repair_html(once) == once
    assert mj.count_garbled_html(once) == 0


def test_repair_html_leaves_a_clean_persian_table_alone():
    clean = "<table><tr><th>ردیف</th><th>شرح</th></tr><tr><td>۱</td><td>تسهیلات «ویژه»</td></tr></table>"
    assert mj.repair_html(clean) == clean
    assert mj.count_garbled_html(clean) == 0


def test_repair_json_walks_nested_letter_values():
    values = {
        "subject": "گزارشِ «شعبه»",
        "body": "<p>ÒÑ</p>",
        "attTables": [{"id": "t1", "title": "صورت حساب", "html": _TABLE}],
        "serial": 182,
        "copyTo": None,
    }
    out, n = mj.repair_json(values)
    assert n > 0
    assert out["subject"] == "گزارشِ «شعبه»"          # Persian untouched
    assert out["body"] == "<p>NO</p>"
    assert ">Account Name<" in out["attTables"][0]["html"]
    assert out["attTables"][0]["title"] == "صورت حساب"
    assert out["serial"] == 182 and out["copyTo"] is None


def test_repair_json_never_touches_dict_keys():
    out, _ = mj.repair_json({"ÒÑ": "ÒÑ"})
    assert list(out.keys()) == ["ÒÑ"]                 # a field name is not content
    assert out["ÒÑ"] == "NO"


def test_repair_json_reports_zero_for_clean_values():
    values = {"subject": "نامهٔ عمومی", "body": "<p>متنِ سالم</p>", "attTables": []}
    out, n = mj.repair_json(values)
    assert n == 0 and out == values
