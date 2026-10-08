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
# Invisible / look-alike characters that dirty pasted text carries: ZWNJ/ZWJ/LRM/RLM/BOM,
# NBSP, and the dash / slash look-alikes (en/em dash, minus, fraction/division slash,
# fullwidth slash, Arabic decimal/thousands separators).
_NOISE = dict.fromkeys(map(ord, "\u200c\u200d\u200e\u200f\u202a\u202b\u202c\ufeff"), None)
_NOISE.update({ord(c): "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2212"})
_NOISE.update({ord(c): "/" for c in "\u2044\u2215\uff0f\u066b\u066c"})
_NOISE[0xA0] = " "
# Separator between the four parts of a 182-reference: / \\ - . or just whitespace.
_SEP = r"(?:\s*[/\\\-.]\s*|\s+)"

# 182/4/1045/2025 — tolerate spaces / dashes / backslash / dots between parts.
_OD_RE = re.compile(rf"(?<![0-9A-Za-z])182{_SEP}(\d{{1,3}}){_SEP}(\d{{1,6}}){_SEP}(\d{{4}})(?!\d)")
# PIM-1260109000001 / "STF 1251218000001" / BLC1260119000002 (11-16 digits).
_LOAN_RE = re.compile(r"(?<![0-9A-Za-z])([A-Za-z]{2,5})[\s\-_./]*(\d{11,16})(?!\d)")


def extract_offer_ref(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    s = str(text).translate(_DIGIT_MAP).translate(_NOISE)
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
