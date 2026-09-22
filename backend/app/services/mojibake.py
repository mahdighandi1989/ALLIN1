"""v126 — repair of "custom PDF font encoding" mojibake.

Some PDF writers (old report generators are the usual source) embed a SUBSET font
whose internal encoding is not the standard one. The page looks perfect on screen,
but the text LAYER underneath holds different code points, so every tool that
reads the text — a PDF text extractor, or an LLM handed the PDF, which reads that
same layer — faithfully reproduces garbage:

    "Statement NO"  ->  "Í¬¿¬»³»²¬ ÒÑ"
    "Amount (IRR)"  ->  "ß³±«²¬ (×ÎÎ)"

The substitution is exact and reversible: a letter's code point is reflected
around 0x120, i.e. ``garbled = 0x120 - original``. Only the 52 ASCII letters are
affected — digits, spaces and punctuation come through untouched, which is why a
garbled statement still shows correct dates and amounts.

    A(0x41)..Z(0x5A) -> 0xDF..0xC6      a(0x61)..z(0x7A) -> 0xBF..0xA6

Repair therefore maps 0xA6-0xBF and 0xC6-0xDF back. Those two ranges contain a
few characters that occur legitimately — most importantly the Persian quotation
marks « (0xAB) and » (0xBB), plus ° ± ² ³ · §. So the decision is made PER TEXT
CHUNK and deliberately conservative: a chunk is only repaired when it is
overwhelmingly made of these characters AND contains no Persian/Arabic letter.
A Persian sentence with «quotes» can never qualify; a garbled cell always does.
"""
from __future__ import annotations

import re

# The reflection point: garbled = 0x120 - original (an involution, so the same
# arithmetic undoes it).
_PIVOT = 0x120
_UPPER = (0x120 - ord("Z"), 0x120 - ord("A"))   # 0xC6..0xDF
_LOWER = (0x120 - ord("z"), 0x120 - ord("a"))   # 0xA6..0xBF

_PERSIAN = re.compile(r"[؀-ۿﭐ-﷿ﹰ-﻿]")


def _is_mapped(ch: str) -> bool:
    o = ord(ch)
    return _LOWER[0] <= o <= _LOWER[1] or _UPPER[0] <= o <= _UPPER[1]


def decode_char(ch: str) -> str:
    """The raw reflection for one mapped character (no policy applied)."""
    return chr(_PIVOT - ord(ch)) if _is_mapped(ch) else ch


def looks_garbled(text: str, *, min_chars: int = 2, min_ratio: float = 0.5) -> bool:
    """True when this chunk is almost certainly a garbled Latin string.

    Requires (a) at least ``min_chars`` mapped characters, (b) mapped characters
    to be at least ``min_ratio`` of the chunk's letters, and (c) NO Persian or
    Arabic letter anywhere — real Persian text using «…» quotes is the one
    false positive worth designing against, and this rules it out completely.
    """
    if not text:
        return False
    if _PERSIAN.search(text):
        return False
    mapped = sum(1 for ch in text if _is_mapped(ch))
    if mapped < min_chars:
        return False
    letters = sum(1 for ch in text if ch.isalpha() or _is_mapped(ch))
    if not letters:
        return False
    return mapped / letters >= min_ratio


def repair_text(text: str) -> str:
    """Repair a chunk if it qualifies; otherwise return it untouched."""
    if not looks_garbled(text):
        return text
    return "".join(decode_char(ch) for ch in text)


# A chunk = a run between line breaks / tab / pipe / the usual table separators,
# so one garbled cell in a pipe-separated transcription is judged on its own.
_CHUNK = re.compile(r"[^\n\r\t|]+")


def repair_block(text: str) -> str:
    """Repair a multi-line block, judging each cell/line separately."""
    if not text:
        return text
    return _CHUNK.sub(lambda m: repair_text(m.group()), text)


def count_garbled(text: str) -> int:
    """How many chunks of this block would be repaired (0 = nothing to do)."""
    if not text:
        return 0
    return sum(1 for m in _CHUNK.finditer(text) if looks_garbled(m.group()))


# --- HTML / JSON aware repair -------------------------------------------------
# A letter's body and its tables are stored as HTML, so the repair must never see
# a tag: rewriting inside `<td style="width:30%">` would destroy the column widths
# the user set. Splitting on tags AND entities keeps both verbatim — entities also
# stay out of the ratio test, so a cell full of `&nbsp;` is still judged on its
# real letters.
_TAG_OR_ENTITY = re.compile(r"<[^>]*>|&[#0-9A-Za-z]+;")


def repair_html(html: str) -> str:
    """Repair the TEXT between tags only; tags, attributes and entities verbatim."""
    if not html:
        return html
    out, pos = [], 0
    for m in _TAG_OR_ENTITY.finditer(html):
        out.append(repair_block(html[pos:m.start()]))
        out.append(m.group())
        pos = m.end()
    out.append(repair_block(html[pos:]))
    return "".join(out)


def count_garbled_html(html: str) -> int:
    """How many text runs between tags would be repaired (0 = clean)."""
    if not html:
        return 0
    n, pos = 0, 0
    for m in _TAG_OR_ENTITY.finditer(html):
        n += count_garbled(html[pos:m.start()])
        pos = m.end()
    return n + count_garbled(html[pos:])


def repair_json(value):
    """Repair every string inside a nested dict/list structure (HTML-aware).

    Returns ``(repaired_value, n_fixed)``. Dict KEYS are never touched — they are
    field names, not content.
    """
    if isinstance(value, str):
        fixed = count_garbled_html(value)
        return (repair_html(value) if fixed else value), fixed
    if isinstance(value, list):
        out, n = [], 0
        for v in value:
            rv, rn = repair_json(v)
            out.append(rv)
            n += rn
        return out, n
    if isinstance(value, dict):
        out, n = {}, 0
        for k, v in value.items():
            rv, rn = repair_json(v)
            out[k] = rv
            n += rn
        return out, n
    return value, 0
