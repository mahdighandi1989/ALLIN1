"""Credit-facility processing-charge calculator (term 23 of the offer letter).

Deterministic: rules come from the editable ``charge_rules`` table (seeded from
the bank's scanned Schedule of Charges, Ver C01/P01-04-2025); this module only
selects + applies them. The verified reference case from the owner's real
letter (A/C 301408): Cheque Discount 2,800,000 (line fee 4‰ = 11,200) +
Overdraft 3,500,000 fully covered by FD underlien (0.1%, capped 1,000) →
total AED 12,200 — exactly the figure printed in that letter's term 23.

Charging model (per the tariff wording):
- corporate «Credit Facility Line, New/Renewal Management Fees (Less FD
  Underlien)»: ONE line fee of 4 per 1,000 over the SUM of revolving-line
  limits (OD, cheque discount, …) that are NOT fully FD-covered; min 1,200 /
  max 20,000 applied to that single line fee.
- «OD Facility against 100% FD Underlien»: per item, 0.1% (min 200 / max 1,000).
- corporate «Commercial Loan (Processing Fees)»: per loan, 1.5% (min 500).
- corporate «Temporary Facilities»: flat 2% for OD / 1% for CD (min 500 /
  max 2,500) — used when the item is marked temporary.
- individual «Personal Loans (Processing Fees)»: per loan, 1% (min 500 /
  max 2,500); amount ≤ 10,000 → min 200.
- STAFF exemption: a facility marked as a *staff* facility on a staff account
  is free (a NON-staff facility granted to a staff member is still charged).
- Unknown facility type → charge 0 + warning (never invented).
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Dict, List, Optional

# rule_key registry — the seed rows and the picker below both use these.
RULE_KEYS = [
    "line_fee",          # revolving credit line management fee (corporate)
    "od_100fd",          # OD against 100% FD underlien (both segments)
    "commercial_loan",   # corporate loan processing
    "personal_loan",     # individual loan processing
    "temporary_od",      # corporate temporary OD
    "temporary_cd",      # corporate temporary cheque discount
]

# facility-type text → charging family
_LOAN_RE = re.compile(r"loan|وام", re.IGNORECASE)
_OD_RE = re.compile(r"overdraft|over\s*draft|اضافه\s*برداشت|\bOD\b", re.IGNORECASE)
_CD_RE = re.compile(r"cheque|check|discount|خرید\s*دین|چک", re.IGNORECASE)
_LINE_RE = re.compile(
    r"overdraft|over\s*draft|\bOD\b|cheque|check|discount|LC|letter of credit|"
    r"guarantee|\bLG\b|trust receipt|\bTR\b|اضافه\s*برداشت|اعتبار|ضمانت",
    re.IGNORECASE,
)


def _num(v: Any) -> Decimal:
    s = re.sub(r"[^0-9.]", "", str(v or ""))
    try:
        return Decimal(s) if s else Decimal(0)
    except Exception:  # noqa: BLE001
        return Decimal(0)


def classify(facility_type: str, *, segment: str, temporary: bool = False) -> Optional[str]:
    """Map a free-text facility type onto a charging rule_key (None = unknown)."""
    t = (facility_type or "").strip()
    if not t:
        return None
    if _LOAN_RE.search(t):
        return "personal_loan" if segment == "individual" else "commercial_loan"
    if temporary and _OD_RE.search(t):
        return "temporary_od"
    if temporary and _CD_RE.search(t):
        return "temporary_cd"
    if _LINE_RE.search(t):
        return "line_fee"
    return None


def _apply(rule: Dict[str, Any], base: Decimal) -> Decimal:
    method = str(rule.get("method") or "per_mille")
    rate = Decimal(str(rule.get("rate") or 0))
    if method == "flat":
        amt = rate
    elif method == "percent":
        amt = base * rate / Decimal(100)
    else:  # per_mille
        amt = base * rate / Decimal(1000)
    small_thr = rule.get("small_threshold")
    min_c = rule.get("min_charge")
    if small_thr not in (None, "") and base <= Decimal(str(small_thr)):
        sm = rule.get("small_min_charge")
        if sm not in (None, ""):
            min_c = sm
    if min_c not in (None, "") and amt < Decimal(str(min_c)):
        amt = Decimal(str(min_c))
    max_c = rule.get("max_charge")
    if max_c not in (None, "") and amt > Decimal(str(max_c)):
        amt = Decimal(str(max_c))
    return amt.quantize(Decimal("0.01"))


def compute_charges(
    rules: List[Dict[str, Any]],
    items: List[Dict[str, Any]],
    *,
    segment: str,
) -> Dict[str, Any]:
    """items: [{facility_type, amount, covered_by_fd, staff_facility, temporary}].

    Returns {total, lines: [{label, base, charge, rule_key, note}], warnings}.
    """
    seg = "corporate" if segment != "individual" else "individual"
    by_key: Dict[str, Dict[str, Any]] = {}
    for r in rules:
        if r.get("segment") == seg and r.get("enabled", True) and not r.get("is_deleted"):
            by_key.setdefault(str(r.get("rule_key")), r)

    lines: List[Dict[str, Any]] = []
    warnings: List[str] = []
    line_fee_base = Decimal(0)
    line_fee_names: List[str] = []

    for it in items:
        ftype = str(it.get("facility_type") or "").strip()
        amount = _num(it.get("amount"))
        if not ftype and amount == 0:
            continue
        if it.get("staff_facility"):
            lines.append({
                "label": ftype or "تسهیلات", "base": float(amount), "charge": 0.0,
                "rule_key": "staff_exempt",
                "note": "تسهیلاتِ کارمندی — طبق ضوابط مشمولِ کارمزدِ پردازش نیست",
            })
            continue
        if it.get("covered_by_fd"):
            rule = by_key.get("od_100fd")
            if rule is None:
                warnings.append(f"قاعدهٔ «OD با پوشش کامل سپرده» در تعرفهٔ {seg} فعال نیست")
                continue
            charge = _apply(rule, amount)
            lines.append({
                "label": f"{ftype or 'OD'} (پوشش کامل سپردهٔ underlien)",
                "base": float(amount), "charge": float(charge), "rule_key": "od_100fd",
                "note": rule.get("label") or "",
            })
            continue
        key = classify(ftype, segment=seg, temporary=bool(it.get("temporary")))
        if key is None:
            warnings.append(f"نوعِ تسهیلاتِ «{ftype}» در تعرفه شناخته نشد — کارمزدش ۰ منظور شد؛ دستی بررسی کن")
            lines.append({"label": ftype, "base": float(amount), "charge": 0.0,
                          "rule_key": "unknown", "note": "نوعِ ناشناخته"})
            continue
        if key == "line_fee":
            # accumulated: ONE management fee over the whole revolving line
            line_fee_base += amount
            line_fee_names.append(ftype)
            continue
        rule = by_key.get(key)
        if rule is None:
            warnings.append(f"قاعدهٔ «{key}» در تعرفهٔ {seg} تعریف/فعال نیست — کارمزدِ «{ftype}» ۰ منظور شد")
            lines.append({"label": ftype, "base": float(amount), "charge": 0.0,
                          "rule_key": key, "note": "قاعده غایب"})
            continue
        charge = _apply(rule, amount)
        lines.append({"label": ftype, "base": float(amount), "charge": float(charge),
                      "rule_key": key, "note": rule.get("label") or ""})

    if line_fee_base > 0:
        rule = by_key.get("line_fee")
        if rule is None:
            warnings.append(f"قاعدهٔ «کارمزدِ خطِ اعتباری» در تعرفهٔ {seg} تعریف/فعال نیست")
        else:
            charge = _apply(rule, line_fee_base)
            lines.append({
                "label": "خطِ اعتباری (" + "، ".join(line_fee_names) + ")",
                "base": float(line_fee_base), "charge": float(charge),
                "rule_key": "line_fee", "note": rule.get("label") or "",
            })

    total = sum(Decimal(str(l["charge"])) for l in lines)
    return {"total": float(total), "lines": lines, "warnings": warnings}


# ---------------------------------------------------------------------------
# Default seed — verbatim from the scanned booklet. Fill-empty-only: seeded
# ONLY when the table has no rows for that segment (never overwrites edits).
# ---------------------------------------------------------------------------
DEFAULT_RULES: List[Dict[str, Any]] = [
    # corporate — Ver C01-04-2025
    {"id": "CR-corp-line", "segment": "corporate", "rule_key": "line_fee",
     "label": "کارمزد مدیریت خط اعتباری (New/Renewal، بدون بخش زیر پوشش سپرده) — AED 4 per 1,000",
     "method": "per_mille", "rate": 4, "min_charge": 1200, "max_charge": 20000,
     "notes": "Credit Facility Line, New/Renewal Management Fees (Less FD Underlien): AED 4 per AED 1,000 (Min 1,200, Max 20,000)",
     "version": "C01-04-2025", "sort_order": 1},
    {"id": "CR-corp-od100fd", "segment": "corporate", "rule_key": "od_100fd",
     "label": "OD با پوشش ۱۰۰٪ سپردهٔ underlien — 0.1%",
     "method": "percent", "rate": 0.1, "min_charge": 200, "max_charge": 1000,
     "notes": "OD Facility against 100% FD Underlien: 0.1% (Min 200, Max 1,000)",
     "version": "C01-04-2025", "sort_order": 2},
    {"id": "CR-corp-loan", "segment": "corporate", "rule_key": "commercial_loan",
     "label": "وام تجاری (Processing) — 1.5%",
     "method": "percent", "rate": 1.5, "min_charge": 500, "max_charge": None,
     "notes": "Commercial Loan (Processing Fees): Flat 1.5% of Loan Amount (Min AED 500)",
     "version": "C01-04-2025", "sort_order": 3},
    {"id": "CR-corp-tmp-od", "segment": "corporate", "rule_key": "temporary_od",
     "label": "تسهیلات موقت OD — 2%",
     "method": "percent", "rate": 2, "min_charge": 500, "max_charge": 2500,
     "notes": "Temporary Facilities (Management Fees): Flat 2% for OD (Min 500 Max 2,500)",
     "version": "C01-04-2025", "sort_order": 4},
    {"id": "CR-corp-tmp-cd", "segment": "corporate", "rule_key": "temporary_cd",
     "label": "تسهیلات موقت Cheque Discount — 1%",
     "method": "percent", "rate": 1, "min_charge": 500, "max_charge": 2500,
     "notes": "Temporary Facilities: 1% for CD (Min 500 Max 2,500)",
     "version": "C01-04-2025", "sort_order": 5},
    # individual — Ver P01-04-2025
    {"id": "CR-ind-loan", "segment": "individual", "rule_key": "personal_loan",
     "label": "وام شخصی (Processing) — 1%",
     "method": "percent", "rate": 1, "min_charge": 500, "max_charge": 2500,
     "small_threshold": 10000, "small_min_charge": 200,
     "notes": "Personal Loans (Processing Fees): 1% of Loan Amount (Min 500 Max 2,500); Loan ≤ 10,000 → Min 200",
     "version": "P01-04-2025", "sort_order": 1},
    {"id": "CR-ind-od100fd", "segment": "individual", "rule_key": "od_100fd",
     "label": "OD با پوشش ۱۰۰٪ سپردهٔ underlien — 0.1%",
     "method": "percent", "rate": 0.1, "min_charge": 200, "max_charge": 1000,
     "notes": "OD Facility against 100% FD Underlien: 0.1% (Min 200, Max 1,000)",
     "version": "P01-04-2025", "sort_order": 2},
    {"id": "CR-ind-line", "segment": "individual", "rule_key": "line_fee",
     "label": "کارمزد خط اعتباری (حقیقی) — مطابق تعرفهٔ شرکتی مگر اصلاح شود",
     "method": "per_mille", "rate": 4, "min_charge": 1200, "max_charge": 20000,
     "notes": "برای حساب حقیقیِ دارای OD/خط اعتباریِ بدون پوشش سپرده — در بولتن حقیقی نرخ جدا نیامده؛ قابل ویرایش",
     "version": "P01-04-2025", "sort_order": 3},
]
