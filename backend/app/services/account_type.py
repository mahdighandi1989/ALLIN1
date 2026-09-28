"""v139 — decide whether an account belongs to a PERSON or a COMPANY, from the
evidence the database already holds.

WHY THIS EXISTS
---------------
`account_type` had no «we don't know» state. The column defaulted to
``retail`` (models/customer.py), the bulk listing import invented ``retail``
for any record without the column, and two more call sites fell back to
``retail`` as well. So the database could not tell apart:

    * "this is an individual"        (somebody decided)
    * "nobody ever said"             (a default that looks identical)

Consequences the owner actually hit: the Credit File chooser reads the stored
type and opens the **Retail** form for a company without ever asking — its
"type not recorded → ask the operator" branch was dead code, because the type
was never empty. This is the same failure the supervisor itself had: a sentinel
for «unknown» stored as if it were a real measurement.

WHAT THIS MODULE DOES — AND DOES NOT DO
---------------------------------------
It reads evidence and returns an OPINION with its reasons. It never writes.
Nothing in this system may silently reclassify a customer: a wrong flip changes
which KYC fields are required, which form opens and how completeness is scored.
The opinion is shown to a human, who decides — the same review-first rule the
de-dup engine follows.

Positive evidence only. No evidence ⇒ ``unknown`` ⇒ ask. Guessing is what
created the problem.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

RETAIL = "retail"
CORPORATE = "corporate"
SME = "sme"
UNKNOWN = "unknown"

#: Stored values that mean «nobody has decided». An empty column means the same.
UNDECIDED = {"", UNKNOWN, "none", "null", "-"}

# Legal-form and trade-name markers. Word-boundary matched, so "Estate" never
# matches "EST" and a person called "Ali Trading" is still caught deliberately —
# a trade name IS corporate evidence.
_CORP_TOKENS = [
    r"l\.?l\.?c", r"f\.?z\.?e", r"f\.?z\.?c", r"f\.?z\s*-?\s*l\.?l\.?c",
    r"w\.?l\.?l", r"p\.?j\.?s\.?c", r"p\.?s\.?c", r"s\.?a\.?o\.?[gc]",
    r"ltd", r"limited", r"plc", r"inc", r"corp", r"corporation",
    r"co", r"company", r"est", r"establishment", r"enterprises?",
    r"trading", r"traders?", r"general\s+trading", r"contracting", r"contractors?",
    r"group", r"holdings?", r"industries", r"industrial", r"factory", r"manufactur\w*",
    r"services", r"solutions", r"technologies", r"international", r"invest\w*",
    r"partners", r"brothers", r"bros", r"sons", r"foodstuff", r"real\s+estate",
    r"transport", r"logistics", r"cargo", r"shipping", r"marine", r"engineering",
    r"consultan\w*", r"pharmac\w*", r"garments?", r"textiles?", r"electronics",
    r"شرکت", r"موسسه", r"مؤسسه", r"بازرگانی", r"تجارت", r"صنایع", r"گروه",
]
_CORP_RE = re.compile(r"\b(?:%s)\b" % "|".join(_CORP_TOKENS), re.IGNORECASE)

# Personal titles. Weak on their own — a company record may carry its manager's
# name — so they only speak when there is no corporate evidence at all.
_PERSON_RE = re.compile(
    r"\b(?:mr|mrs|ms|miss|mister|sheikh|shaikh|dr|eng|engineer|"
    r"آقای|خانم|جناب|سرکار)\b\.?", re.IGNORECASE)

_CORP_BTYPE = re.compile(
    r"corporate|company|sme|commercial|trading|industrial|institution|"
    r"partnership|شرکت|حقوقی", re.IGNORECASE)
_RETAIL_BTYPE = re.compile(
    r"\bretail\b|individual|personal|salaried|employee|حقیقی|شخصی", re.IGNORECASE)


@dataclass
class Verdict:
    """An opinion about one account, with the evidence that produced it."""
    guess: str = UNKNOWN
    #: high = a document only one kind of customer has; medium = naming/other
    #: signals; none = no evidence at all, which must NOT be turned into a guess.
    confidence: str = "none"
    reasons: list = field(default_factory=list)
    #: evidence pointing the OTHER way, kept so a human sees the conflict
    counter_reasons: list = field(default_factory=list)

    @property
    def decided(self) -> bool:
        return self.guess in (RETAIL, CORPORATE, SME)

    def as_dict(self) -> dict:
        return {"guess": self.guess, "confidence": self.confidence,
                "reasons": self.reasons, "counter_reasons": self.counter_reasons}


def is_undecided(value) -> bool:
    """True when the stored type carries no decision — empty or «unknown»."""
    return str(getattr(value, "value", value) or "").strip().lower() in UNDECIDED


def normalize(value) -> str:
    """The stored type as a plain string; anything undecided becomes UNKNOWN."""
    v = str(getattr(value, "value", value) or "").strip().lower()
    if v in UNDECIDED:
        return UNKNOWN
    return v if v in (RETAIL, CORPORATE, SME) else UNKNOWN


def classify(
    *,
    name: str = "",
    business_type: str = "",
    trade_license_no: str = "",
    passport_no: str = "",
    emirates_id_no: str = "",
    partner_count: int = 0,
    facility_types: Optional[list] = None,
) -> Verdict:
    """Read the evidence; return an opinion and why. Never writes anything."""
    name = str(name or "").strip()
    btype = str(business_type or "").strip()
    corp: list[str] = []
    retail: list[str] = []

    # --- documents only one kind of customer has -------------------------
    if str(trade_license_no or "").strip():
        corp.append("جوازِ تجاری (Trade License) ثبت شده — فقط شخصیتِ حقوقی دارد")
    if (partner_count or 0) > 0:
        corp.append(f"{partner_count} شریک ثبت شده — حسابِ شخصی شریک ندارد")

    # --- naming --------------------------------------------------------------
    m = _CORP_RE.search(name)
    if m:
        corp.append(f"نامِ حساب نشانهٔ شرکتی دارد: «{m.group(0)}»")
    if _CORP_BTYPE.search(btype):
        corp.append(f"نوعِ کسب‌وکار شرکتی است: «{btype[:60]}»")

    if _RETAIL_BTYPE.search(btype):
        retail.append(f"نوعِ کسب‌وکار شخصی است: «{btype[:60]}»")
    p = _PERSON_RE.search(name)
    if p:
        retail.append(f"عنوانِ شخصی در نام: «{p.group(0)}»")

    # Identity documents are RETAIL evidence only when nothing corporate is
    # present: the corporate form itself has «Passport» and «Manager Emirates
    # ID» fields, so on a company record these belong to its manager.
    has_id = bool(str(passport_no or "").strip() or str(emirates_id_no or "").strip())
    if has_id and not corp:
        retail.append("پاسپورت/اماراتی‌آیدی دارد و هیچ نشانهٔ شرکتی ندارد")

    # --- verdict -------------------------------------------------------------
    if corp and not retail:
        strong = any("Trade License" in r or "شریک" in r for r in corp)
        return Verdict(CORPORATE, "high" if strong else "medium", corp, retail)
    if retail and not corp:
        return Verdict(RETAIL, "medium", retail, corp)
    if corp and retail:
        # A trade license or a partner outranks a name/ID hint: a company may
        # carry its manager's documents, a person never carries a trade licence.
        strong = any("Trade License" in r or "شریک" in r for r in corp)
        return Verdict(CORPORATE, "medium" if strong else "low", corp, retail)
    return Verdict(UNKNOWN, "none", [], [])


def disagrees(stored, verdict: Verdict) -> bool:
    """Does a DECIDED stored value contradict confident evidence?

    'sme' counts as corporate — it is a corporate sub-type, not a conflict.
    An undecided stored value is not a contradiction; it is simply missing, and
    is reported separately so the two problems never get mixed up.
    """
    cur = normalize(stored)
    if cur == UNKNOWN or not verdict.decided or verdict.confidence in ("none", "low"):
        return False
    fam = lambda v: CORPORATE if v in (CORPORATE, SME) else v
    return fam(cur) != fam(verdict.guess)
