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

WHAT MAY DECIDE, AND WHAT MAY ONLY CORROBORATE (settled at v148)
---------------------------------------------------------------
Four rules here were wrong in the same way, one after another, each found by
meeting the real book rather than by review:

    v143  a trade licence          → the employer's, on a personal file
    v145  a passport / Emirates ID → the manager's, on a corporate file
    v147  «RETAIL SALE OF …»       → a line of business, not a customer type
    v148  registered partners      → a JOINT account's co-holder sits in the
                                     same table as a company's shareholder

The pattern is one question: **is this recorded for the OTHER kind of customer
too?** If yes, it cannot separate them, no matter how strong it feels. Three
one-off corrections did not stop the fourth, so the test is written down as a
checklist in ``experiences/a-default-that-looks-like-a-decision-corrupts-the-
record.md`` and every new rule must pass it.

What survives as decisive is only what states WHO THE CUSTOMER IS — the account
name, and a ``business_type`` describing the customer. Everything that merely
describes WHAT IS IN THE FILE corroborates: it can raise confidence, never
create a contradiction on its own (``disagrees`` ignores ``low``).
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

    # --- v145: added from the REAL book -----------------------------------
    # Every token below was read off an account this pattern had failed to
    # recognise, which is why a manager's passport could out-vote an obvious
    # company. Additive only — nothing above was changed or removed.
    # UAE / international legal forms the list simply did not have. Note
    # `f\.?z\.?c` above cannot match «FZCO»: the \b needs a non-word char
    # after the «c», and «O» is one — hence the explicit form here.
    r"f\.?z\.?c\.?o", r"d\.?m\.?c\.?c", r"d\.?w\.?c", r"j\.?a\.?f\.?z\.?a",
    r"d\.?a\.?f\.?z\.?a", r"r\.?a\.?k\.?e\.?z", r"gmbh", r"b\.?v",
    r"s\.?a\.?r\.?l", r"pvt", r"pty", r"offshore", r"branch",
    r"sole\s*(?:propriet\w*|establish\w*|estableshment)",
    # trade abbreviations this book uses constantly («GEN TRDG», «DIAMOND STONE
    # GEN TRD»). Bare «TR» is DELIBERATELY absent — it collides with personal
    # initials, and a wrong corporate call is the expensive direction.
    r"trdg?", r"trdng", r"impex", r"imports?", r"exports?",
    # lines of business — a natural person does not have one
    r"exchange", r"supermarket", r"super\s*market", r"salon", r"boutique",
    r"cafe", r"caf[eé]teria", r"restaurant", r"bakery", r"laundry", r"hotel",
    r"school", r"institute?", r"inistitute", r"academy", r"training",
    r"hospital", r"clinic", r"pharmacy", r"pharma", r"medical", r"laborator\w*",
    r"properties", r"realestate", r"equipment", r"spare\s*parts", r"accessories",
    r"ty[rp]es?", r"tires?", r"furniture", r"curtains", r"garage", r"workshop",
    r"repairing", r"maintenance", r"decor\w*", r"advertis\w*", r"printing",
    r"insulation", r"cables?", r"steel", r"aluminium", r"aluminum", r"glass",
    r"mirrors", r"paints?", r"plastics?", r"machinery", r"motors?", r"auto",
    r"travel", r"tourism", r"exhibition", r"catering", r"beverages?",
    r"centre", r"center", r"systems", r"exchange\s*house", r"shop",
    r"فروشگاه", r"صرافی", r"آژانس", r"خیریه",
    # --- v147: read off the whole-book run ----------------------------------
    # «ENG» moved here from the personal titles — in this book it is Engineering.
    r"eng", r"engineering", r"consultations?", r"office", r"gallery",
    r"fashions?", r"press", r"agency", r"lubrication", r"house\s*hold",
    r"household", r"tailoring", r"embroidery", r"perfume", r"mobile",
]
_CORP_RE = re.compile(r"\b(?:%s)\b" % "|".join(_CORP_TOKENS), re.IGNORECASE)

# Personal titles. Weak on their own — a company record may carry its manager's
# name — so they only speak when there is no corporate evidence at all.
#
# «SHEIKH» IS DELIBERATELY NOT HERE (v142). It looks like a personal title and it
# is one, but in this region it is overwhelmingly part of a TRADE name — «Al
# Sheikh Trading», «Al Sheikh Est». The first live run against the real book
# proved it: account 110221 «AL SHEIKH A.E.G», correctly filed as a company,
# was reported as a contradiction on the strength of that word alone, and the
# owner was right to hesitate. A person named Sheikh with no other signal now
# comes out `unknown` — which asks, instead of guessing wrong.
# v147 — A TITLE ONLY COUNTS WHERE A TITLE GOES: at the FRONT of the name.
#
# Measured on the whole book (44,608 accounts): «NEW MISS PARIS» and «MISS
# GALLERY FASHION» were reported as personal accounts because the word «MISS»
# appeared somewhere in a boutique's trade name. A real title leads the name —
# «MR:A.K.UMMER» — so anchoring the match removes the mid-name trade use without
# losing the genuine case.
#
# «ENG» IS GONE (v147), for the same reason «SHEIKH» went in v142: here it is
# overwhelmingly «Engineering», not «Engineer» — «VIGIL ENG», «AL YAQEEN ENG
# CONSULTATIONS OFFICE». It is now CORPORATE evidence instead (see _CORP_TOKENS).
# A person written «Eng. Ahmad» with nothing else now comes out `unknown`, which
# asks, instead of guessing wrong.
_PERSON_RE = re.compile(
    r"^\s*(?:mr|mrs|ms|miss|mister|dr|"
    r"آقای|خانم|جناب|سرکار)\b[.:\s]", re.IGNORECASE)

_CORP_BTYPE = re.compile(
    r"corporate|company|sme|commercial|trading|industrial|institution|"
    r"partnership|شرکت|حقوقی", re.IGNORECASE)
# v147 — «RETAIL SALE OF WARE AND TOOLS» is a LINE OF BUSINESS, not a kind of
# customer. A shop whose activity is retail selling is a company; the word says
# what it trades in, not who owns the account. This is the trade-licence mistake
# a third time (v143 licence → v145 passport → here), so the same test applies:
# does this value occur for BOTH kinds of customer? «retail sale/trade/shop» does.
_RETAIL_ACTIVITY = re.compile(
    r"\bretail\s+(?:sale|sales|selling|trade|trading|shop|store|outlet|business)",
    re.IGNORECASE)
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

    # --- documents ---------------------------------------------------------
    # A TRADE LICENCE IS NOT PROOF OF A COMPANY (v143, owner's correction).
    #
    # It was the strongest rule here, and it was wrong: when a RETAIL customer
    # opens an account, the bank collects the trade licence of the place they
    # WORK as evidence of employment and residence. So the licence on a personal
    # file may belong to the employer, not the customer. The owner caught this on
    # account 113393 — two personal names with a licence attached — and was right
    # to refuse it: «شاید به خاطر اینه که در افتتاح حساب صرفاً مستنداتِ جایی که
    # کار می‌کنه ازش گرفتن».
    #
    # It is therefore CORROBORATING, never decisive: on its own it cannot make a
    # contradiction (see `disagrees`, which ignores `low`). It only reaches
    # «high» when something else already says company.
    has_licence = bool(str(trade_license_no or "").strip())

    # REGISTERED PARTNERS ARE NOT PROOF OF A COMPANY EITHER (v148, owner's
    # correction — the FOURTH time this same shape has been wrong).
    #
    # This was the last decisive document rule, and the one most trusted: «the
    # bank records partners for an entity, and a natural person has none». The
    # second half is false. A JOINT personal account records its co-holder in the
    # same `Partner` table a company records its shareholders in. The owner
    # settled it on the two accounts this rule was the sole basis for:
    #   182255  YADOLLAH KHALILI/ASHRAFOLSADAT SAFA  1 partner  → personal, JOINT
    #   182428  AYOUB ABDULLAH AKHTARI AZAD          4 partners → personal
    #
    # The checklist written after v147 answers it in one step: «is this value
    # recorded for the OTHER kind of customer too?» — yes. So it corroborates.
    # The reason text no longer ASSERTS the false half; it says what is actually
    # known, which is that co-holders exist and could be either.
    has_partners = (partner_count or 0) > 0
    partner_note = (
        f"{partner_count} شریک/دارندهٔ مشترک ثبت شده — به‌تنهایی دلیل نیست: "
        "حسابِ مشترکِ شخصی هم دارندهٔ دومش در همین جدول ثبت می‌شود")

    # --- naming --------------------------------------------------------------
    m = _CORP_RE.search(name)
    if m:
        corp.append(f"نامِ حساب نشانهٔ شرکتی دارد: «{m.group(0)}»")
    if _CORP_BTYPE.search(btype):
        corp.append(f"نوعِ کسب‌وکار شرکتی است: «{btype[:60]}»")

    # a line-of-business phrase is not a customer type — check it FIRST
    if _RETAIL_BTYPE.search(btype) and not _RETAIL_ACTIVITY.search(btype):
        retail.append(f"نوعِ کسب‌وکار شخصی است: «{btype[:60]}»")
    elif _RETAIL_ACTIVITY.search(btype):
        corp.append(f"نوعِ فعالیت، کسب‌وکار است (نه نوعِ مشتری): «{btype[:60]}»")
    p = _PERSON_RE.search(name)
    if p:
        retail.append(f"عنوانِ شخصی در نام: «{p.group(0)}»")

    # A PASSPORT / EMIRATES ID IS NOT PROOF OF A PERSONAL ACCOUNT (v145).
    #
    # This was the mirror image of the trade-licence mistake the owner caught in
    # v143, and it was doing MORE damage — 64 contradictions against the real
    # book versus 5. The rule read «has an ID and no corporate signal ⇒ retail»,
    # which leans entirely on `_CORP_RE` being complete. It is not: the live book
    # is full of `FZCO`, `GEN TRDG`, `TR.`, `EXCHANGE`, `B.V.`, `SOLE
    # PROPRIETORSHIP` — none of which the pattern knew. So plainly corporate
    # records («ATLAS MEDICAL FZCO», «AL AZHAR MONEY EXCHANGE», «GOLD STANDARD
    # DMCC»), correctly filed as corporate, were reported as contradictions on
    # the strength of a passport number.
    #
    # The deeper point is the owner's own, generalised: EVERY account opening
    # collects a natural person's identity documents. The corporate form itself
    # has «Passport» and «Manager Emirates ID» fields. A document proves that a
    # person was identified — never whose account it is.
    #
    # So it is CORROBORATING, never decisive: `low` confidence, which `disagrees`
    # ignores. Nothing is lost — the signal is still reported, as a note.
    has_id = bool(str(passport_no or "").strip() or str(emirates_id_no or "").strip())
    id_note = ("پاسپورت/اماراتی‌آیدی روی پرونده هست، ولی به‌تنهایی دلیل نیست — "
               "در افتتاحِ حسابِ شرکتی هم مدارکِ هویتیِ مدیر/صاحبِ امضا گرفته می‌شود")

    # --- verdict -------------------------------------------------------------
    #
    # WHAT IS LEFT AS DECISIVE, AND WHY (audited in full at v148)
    # ----------------------------------------------------------
    # Every DOCUMENT rule has now been demoted in turn — licence (v143), passport
    # and Emirates ID (v145), registered partners (v148) — each for the same
    # reason: the bank collects it from both kinds of customer, so its presence
    # cannot tell them apart. Applying that test to the rules that remain:
    #
    #   * the account NAME carrying a legal form or trade word — a statement of
    #     identity, not a document on file. A sole establishment filed under a
    #     trade name IS a business (owner, on «HAMID AKBAR LUBRICATION SHOP»).
    #   * `business_type` describing the CUSTOMER (corporate / individual /
    #     salaried) — also a statement about who this is. The line-of-business
    #     phrasing that is NOT about the customer was carved out in v147.
    #
    # So the surviving decisive signals are the two that describe WHO THE
    # CUSTOMER IS; everything that merely describes WHAT IS IN THE FILE now
    # corroborates. Any new rule must pass the same test before it decides —
    # see experiences/a-default-that-looks-like-a-decision-corrupts-the-record.md
    corroborating: list[str] = []
    if has_licence:
        corroborating.append("جوازِ تجاری هم روی پرونده هست (مؤیّد، نه دلیلِ مستقل)")
    if has_partners:
        corroborating.append(partner_note)

    if corp:
        # something already says company → the documents back it up
        corp.extend(corroborating)
        if not retail:
            return Verdict(CORPORATE,
                           "high" if (has_partners or has_licence) else "medium",
                           corp, retail)
        # Conflicting signals, and no document can break the tie any more.
        return Verdict(CORPORATE, "low", corp, retail)

    licence_note = ("جوازِ تجاری روی پرونده هست، ولی به‌تنهایی دلیل نیست — "
                    "در افتتاحِ حسابِ حقیقی هم جوازِ محلِ کارِ مشتری گرفته می‌شود")

    if retail:
        # Real retail evidence (a personal title, or a personal business type).
        # No document on file overturns it: the licence may be the employer's and
        # the partner rows may be a joint account's co-holders.
        notes = ([licence_note] if has_licence else [])
        if has_partners:
            notes.append(partner_note)
        return Verdict(RETAIL, "medium", retail, notes + corp)

    # No statement of identity either way. Everything left is CORROBORATING only,
    # so whatever it suggests comes out «low» — visible to a human, incapable of
    # contradicting what is stored (see `disagrees`).
    if has_licence or has_partners:
        why = ([licence_note] if has_licence else []) + ([partner_note] if has_partners else [])
        return Verdict(CORPORATE, "low", why, [id_note] if has_id else [])
    if has_id:
        return Verdict(RETAIL, "low", [id_note], [])
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
