"""Loan amortisation schedule generation for offer letters.

Produces a standard reducing-balance schedule (equal periodic payments) given a
principal, annual interest rate, tenor in months, an optional interest-only grace
period, and a repayment frequency. Pure functions, no DB — easy to unit test.
"""
from __future__ import annotations

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

# Approximate days between payments, for scheduling payment dates.
PERIOD_DAYS = {
    "monthly": 30,
    "quarterly": 91,
    "semi_annual": 182,
    "annual": 365,
    "bullet": 365,
}


def _q(value: Decimal) -> Decimal:
    """Round to 2 decimal places (currency)."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
    pdays = PERIOD_DAYS.get(rtype, 30)
    start = start or date.today()

    if principal <= 0 or tenor_months <= 0:
        return []

    # Convert tenor (months) into the number of payment periods.
    total_periods = max(1, round(tenor_months * ppy / 12))
    period_rate = annual_rate / Decimal(ppy)

    # Grace periods (interest-only) expressed in payment periods.
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
        # Interest each period, principal repaid entirely at maturity.
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

    # Equal-payment annuity for the amortising periods.
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
                principal_pay = _q(balance)  # clear any rounding remainder
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
