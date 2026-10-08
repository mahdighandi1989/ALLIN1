"""Offer-letter reference numbers — the bank's real facility reference.

Two families (owner, 2026-10-08):
  * non-loan facilities (OD/LG/LC ...)  ->  ``182/<n>/<seq>/<year>``  e.g. 182/4/1045/2025
  * loans                               ->  letters (STF/BLC/PIM/TPL ...) + ~13 digits,
                                            e.g. PIM-1260109000001

Stored text is dirty: the separator may be a space, a dash or missing, the
number may be wrapped in words ("... OFFER LETTER"), digits may be Persian.
``extract_offer_ref`` recognises all of that and returns ONE canonical string;
anything that is not clearly a reference ('-', '???', 'OLD - CLASSIFIED')
returns None — never guess (conservative, like the de-dup engine).
"""
import re
from typing import Optional

_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_SEP = r"\s*[/\\\-.]\s*"

# 182/4/1045/2025 — tolerate spaces / dashes / backslash / dots between parts.
_OD_RE = re.compile(rf"(?<![0-9A-Za-z])182{_SEP}(\d{{1,3}}){_SEP}(\d{{1,6}}){_SEP}(\d{{4}})(?!\d)")
# PIM-1260109000001 / "STF 1251218000001" / BLC1260119000002 (11-16 digits).
_LOAN_RE = re.compile(r"(?<![0-9A-Za-z])([A-Za-z]{2,5})[\s\-_./]*(\d{11,16})(?!\d)")


def extract_offer_ref(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    s = str(text).translate(_DIGIT_MAP)
    m = _OD_RE.search(s)
    if m:
        return "182/{}/{}/{}".format(*m.groups())
    m = _LOAN_RE.search(s)
    if m:
        return f"{m.group(1).upper()}-{m.group(2)}"
    return None


def offer_ref_key(text: Optional[str]) -> Optional[str]:
    """Separator-free comparison key: equal for every spelling of one reference."""
    ref = extract_offer_ref(text)
    return re.sub(r"[^0-9A-Z]", "", ref) if ref else None
