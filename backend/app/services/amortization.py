"""Loan amortisation schedule generation for offer letters.

Produces a standard reducing-balance schedule (equal periodic payments) given a
principal, annual interest rate, tenor in months, an optional interest-only grace
period, and a repayment frequency. Pure functions, no DB — easy to unit test.

Tenor handling: a tenor that is not a whole multiple of the payment period gets
a final *stub* period whose interest is prorated by its actual length in
months. The legacy behavior (round the tenor to whole periods, charging a
6-month bullet a full year of interest) can be restored with the
``AMORT_LEGACY_ROUNDING=1`` environment flag.
"""
from __future__ import annotations

import calendar
import os
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

# Number of payments per year for each repayment frequency.
PERIODS_PER_YEAR = {
    "monthly": 12,
    "quarterly": 4,
    "semi_annual": 2,
    "annual": 1,
    "bullet": 1,  # single payment at maturity
}

# Approximate days between payments — used ONLY by the legacy path.
PERIOD_DAYS = {
    "monthly": 30,
    "quarterly": 91,
    "semi_annual": 182,
    "annual": 365,
    "bullet": 365,
}


def _legacy_rounding() -> bool:
    return os.getenv("AMORT_LEGACY_ROUNDING", "").strip().lower() in ("1", "true", "yes")


def _q(value: Decimal) -> Decimal:
    """Round to 2 decimal places (currency)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _add_months(base: date, months: int) -> date:
    """Calendar-accurate month addition (day clamped to the target month)."""
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass
class Installment:
    installment_number: int
    payment_date: date
    opening_balance: Decimal
    principal_payment: Decimal
    interest_payment: Decimal
    total_payment: Decimal
    closing_balance: Decimal


def generate_schedule(
    principal: Decimal,
    annual_rate_pct: Decimal,
    tenor_months: int,
    *,
    repayment_type: str = "monthly",
    grace_period_months: int = 0,
    start: date | None = None,
) -> List[Installment]:
    """Return the amortisation schedule.

    During the grace period only interest is paid; the principal is then
    amortised over the remaining periods with equal total payments (annuity
    formula). ``bullet`` repays all principal in a single final payment.
    """
    principal = Decimal(principal)
    annual_rate = Decimal(annual_rate_pct) / Decimal(100)
    rtype = (repayment_type or "monthly").lower()
    ppy = PERIODS_PER_YEAR.get(rtype, 12)
    start = start or date.today()

    if principal <= 0 or tenor_months <= 0:
        return []

    if _legacy_rounding():
        return _generate_schedule_legacy(
            principal, annual_rate, tenor_months, rtype, ppy,
            grace_period_months, start,
        )

    # Months covered by one full payment period (integer for every supported
    # frequency: monthly=1, quarterly=3, semi_annual=6, annual/bullet=12).
    mpp = 12 // ppy

    # Split the tenor into full periods plus an optional final stub period.
    # The stub charges interest for its ACTUAL length — a 6-month bullet pays
    # 6 months of interest, not a rounded-up year; a 4-month quarterly loan
    # pays 4 months of interest, not a rounded-down quarter.
    full_periods, stub_months = divmod(int(tenor_months), mpp)
    total_periods = full_periods + (1 if stub_months else 0)
    period_rate = annual_rate / Decimal(ppy)
    stub_rate = annual_rate * Decimal(stub_months) / Decimal(12)

    def _months_elapsed(period_index: int) -> int:
        """Months from start to the END of period ``period_index`` (1-based)."""
        if period_index <= full_periods:
            return period_index * mpp
        return full_periods * mpp + stub_months

    def _rate_for(period_index: int) -> Decimal:
        """Interest rate applied over period ``period_index`` (1-based)."""
        return stub_rate if period_index > full_periods else period_rate

    # Grace periods (interest-only) expressed in payment periods.
    grace_periods = min(
        total_periods - 1 if total_periods > 1 else 0,
        round((grace_period_months or 0) * ppy / 12),
    )

    schedule: List[Installment] = []
    balance = principal

    if rtype == "bullet":
        # Interest each period, principal repaid entirely at maturity.
        for i in range(1, total_periods + 1):
            interest = _q(balance * _rate_for(i))
            is_last = i == total_periods
            principal_pay = _q(balance) if is_last else Decimal("0.00")
            total = _q(interest + principal_pay)
            closing = _q(balance - principal_pay)
            schedule.append(
                Installment(
                    i, _add_months(start, _months_elapsed(i)), _q(balance),
                    principal_pay, interest, total, closing,
                )
            )
            balance = closing
        return schedule

    # Equal-payment annuity over the amortising FULL periods (the stub, when
    # present, is settled by the final clear-the-balance payment below, with
    # its interest prorated to the stub length).
    amortising_periods = max(1, total_periods - grace_periods)
    if period_rate > 0:
        factor = (Decimal(1) + period_rate) ** amortising_periods
        annuity = principal * period_rate * factor / (factor - Decimal(1))
    else:
        annuity = principal / Decimal(amortising_periods)
    annuity = _q(annuity)

    for i in range(1, total_periods + 1):
        interest = _q(balance * _rate_for(i))
        if i <= grace_periods:
            principal_pay = Decimal("0.00")
            total = interest
        else:
            is_last = i == total_periods
            if is_last:
                principal_pay = _q(balance)  # clear any rounding remainder
                total = _q(principal_pay + interest)
            else:
                principal_pay = _q(annuity - interest)
                if principal_pay < 0:
                    principal_pay = Decimal("0.00")
                total = _q(principal_pay + interest)
        closing = _q(balance - principal_pay)
        schedule.append(
            Installment(
                i, _add_months(start, _months_elapsed(i)), _q(balance),
                principal_pay, interest, total, closing,
            )
        )
        balance = closing

    return schedule


def _generate_schedule_legacy(
    principal: Decimal,
    annual_rate: Decimal,
    tenor_months: int,
    rtype: str,
    ppy: int,
    grace_period_months: int,
    start: date,
) -> List[Installment]:
    """Pre-2026-07 behavior: whole-period rounding + fixed-day payment dates.

    Kept behind ``AMORT_LEGACY_ROUNDING`` so existing schedules can be
    reproduced exactly if ever needed for reconciliation.
    """
    pdays = PERIOD_DAYS.get(rtype, 30)
    total_periods = max(1, round(tenor_months * ppy / 12))
    period_rate = annual_rate / Decimal(ppy)
    grace_periods = min(
        total_periods - 1 if total_periods > 1 else 0,
        round((grace_period_months or 0) * ppy / 12),
    )
    amortising_periods = max(1, total_periods - grace_periods)

    schedule: List[Installment] = []
    balance = principal
    n = 0
    pay_date = start

    if rtype == "bullet":
        for i in range(total_periods):
            n += 1
            pay_date = pay_date + timedelta(days=pdays)
            interest = _q(balance * period_rate)
            is_last = i == total_periods - 1
            principal_pay = _q(balance) if is_last else Decimal("0.00")
            total = _q(interest + principal_pay)
            closing = _q(balance - principal_pay)
            schedule.append(
                Installment(n, pay_date, _q(balance), principal_pay, interest, total, closing)
            )
            balance = closing
        return schedule

    if period_rate > 0:
        factor = (Decimal(1) + period_rate) ** amortising_periods
        annuity = principal * period_rate * factor / (factor - Decimal(1))
    else:
        annuity = principal / Decimal(amortising_periods)
    annuity = _q(annuity)

    for i in range(total_periods):
        n += 1
        pay_date = pay_date + timedelta(days=pdays)
        interest = _q(balance * period_rate)
        if i < grace_periods:
            principal_pay = Decimal("0.00")
            total = interest
        else:
            is_last = i == total_periods - 1
            if is_last:
                principal_pay = _q(balance)
                total = _q(principal_pay + interest)
            else:
                principal_pay = _q(annuity - interest)
                if principal_pay < 0:
                    principal_pay = Decimal("0.00")
                total = _q(principal_pay + interest)
        closing = _q(balance - principal_pay)
        schedule.append(
            Installment(n, pay_date, _q(balance), principal_pay, interest, total, closing)
        )
        balance = closing

    return schedule


def schedule_totals(schedule: List[Installment]) -> dict:
    """Aggregate totals from a schedule (total repayment, total interest, first payment)."""
    total_repay = sum((i.total_payment for i in schedule), Decimal("0.00"))
    total_interest = sum((i.interest_payment for i in schedule), Decimal("0.00"))
    # The representative periodic instalment (first non-grace total payment).
    monthly = next((i.total_payment for i in schedule if i.principal_payment > 0), None)
    return {
        "total_repayment_amount": _q(total_repay),
        "total_interest": _q(total_interest),
        "monthly_installment": _q(monthly) if monthly is not None else None,
    }
