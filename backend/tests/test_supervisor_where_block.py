"""v171 — «کجا» has to reach the round that does the work.

The owner draws a box and writes «**در اینجا** یه باکس دستور بذار». The word
«اینجا» is carried by the box, not by the sentence. The round answered it by
putting the new control «above the form», and the owner's verdict was that it
could not do it exactly where they wanted.

The cause was not the model's reading. The URGENT brief — which is the path a
rushed sheet actually takes — carried only the page name and a pair of document
pixels: no element, no fractions. The full description existed, but inside
`cmd_pull`, so the two briefs had silently drifted apart.

These tests hold the description together and hold the fractions in it, against
the real geometry of the sheet that went wrong.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "supervisor" / "inspection.py"


@pytest.fixture(scope="module")
def mod():
    assert SRC.exists()
    spec = importlib.util.spec_from_file_location("sup_inspection", SRC)
    m = importlib.util.module_from_spec(spec)
    sys.modules["sup_inspection"] = m
    spec.loader.exec_module(m)
    return m


#: The sheet the owner said was placed wrongly — its geometry, verbatim.
SHEET = {
    "number": 2,
    "page_label": "/letter",
    "section_label": "",
    "reopen": "/letter",
    "dom_path": "body > div:nth-of-type(1) > div > main > div > div:nth-of-type(1)",
    "covered_text": "نوارِ کنترل‌های بالای ویرایشگر",
    "geometry": {
        "doc": {"x": 782, "y": 148, "w": 214, "h": 43},
        "viewport": {"w": 1352, "h": 644},
        "dpr": 1,
        "anchor": {
            "path": "body > div:nth-of-type(1) > div > main > div > div:nth-of-type(1)",
            "rect": {"x": 264, "y": 88, "w": 1049, "h": 140.38},
            "rel": {"x": 0.4938, "y": 0.4274, "w": 0.204, "h": 0.3063},
        },
    },
}


class TestItSaysWhere:
    def test_it_names_the_element_the_box_landed_on(self, mod):
        out = "\n".join(mod.where_block(SHEET))
        assert "عنصر:" in out
        assert SHEET["dom_path"] in out

    def test_it_gives_the_position_INSIDE_that_element(self, mod):
        """Document pixels say where the box was in one particular window. The
        fractions say «here», and «here» is the request."""
        out = "\n".join(mod.where_block(SHEET))
        assert "جای دقیق داخلِ همان گره" in out
        assert "49٪" in out and "43٪" in out          # x and y of the box
        assert "20٪" in out and "31٪" in out          # its width and height
        assert "1049×140" in out                      # the element's own size

    def test_it_says_what_to_do_with_them(self, mod):
        """A number nobody is told to act on is a number that gets skipped."""
        out = "\n".join(mod.where_block(SHEET))
        assert "بالای فرم" in out                     # the exact wrong answer, named
        assert "partial" in out
        assert "۰-ب-۴" in out                          # where the binding rule lives

    def test_the_document_pixels_are_still_there(self, mod):
        out = "\n".join(mod.where_block(SHEET))
        assert "x=782" in out and "y=148" in out


class TestBothBriefsAskTheSameQuestion:
    def test_the_urgent_round_gets_the_full_description_too(self, mod):
        """The regression: the round that answered this sheet was the URGENT one,
        and its brief had none of the above. One function, both callers."""
        src = SRC.read_text(encoding="utf-8")
        body = src[src.index("def cmd_urgent("):src.index("def cmd_answer(")
                   if "def cmd_answer(" in src else len(src)]
        assert "where_block(r)" in body

    def test_the_periodic_round_uses_the_same_one(self, mod):
        src = SRC.read_text(encoding="utf-8")
        body = src[src.index("def cmd_pull("):src.index("def cmd_urgent(")]
        assert "where_block(r)" in body

    def test_neither_brief_builds_its_own_copy(self, mod):
        """Two copies is how they drifted apart the first time."""
        src = SRC.read_text(encoding="utf-8")
        assert src.count("جای دقیق داخلِ همان گره") == 1
        assert src.count("- نشانیِ بازگشت:") == 1


class TestItDegradesHonestly:
    def test_a_sheet_with_no_geometry_still_says_where_it_was(self, mod):
        out = "\n".join(mod.where_block(
            {"page_label": "مشتریان", "reopen": "/customers", "section_label": "فیلترها"}))
        assert "مشتریان" in out and "/customers" in out
        assert "جای دقیق" not in out

    def test_an_unanchored_box_admits_the_place_is_approximate(self, mod):
        g = {"doc": {"x": 5, "y": 6, "w": 7, "h": 8}, "viewport": {"w": 100, "h": 100},
             "anchor": {"path": "", "rect": {"x": 0, "y": 0, "w": 0, "h": 0},
                        "rel": {"x": 0, "y": 0, "w": 0, "h": 0}}}
        out = "\n".join(mod.where_block({"page_label": "x", "reopen": "/x", "geometry": g}))
        assert "به عنصری گره نخورد" in out
        assert "جای دقیق داخلِ همان گره" not in out   # nothing to be precise about

    def test_a_zero_sized_anchor_does_not_divide_by_zero(self, mod):
        g = {"doc": {"x": 5, "y": 6, "w": 7, "h": 8}, "viewport": {"w": 100, "h": 100},
             "anchor": {"path": "div", "rect": {"x": 0, "y": 0, "w": 0, "h": 0},
                        "rel": {"x": 0, "y": 0, "w": 0, "h": 0}}}
        out = "\n".join(mod.where_block({"page_label": "x", "reopen": "/x", "geometry": g}))
        assert "جای دقیق داخلِ همان گره" not in out
