"""Characterization tests: non-whole-period tenors charge interest for the
ACTUAL tenor, not a rounded period count.

Before the fix, ``total_periods = round(tenor_months * ppy / 12)`` meant a
6-month bullet at 10% on 100k charged 10,000 (a full year, 2x) and an
18-month bullet charged 24 months of interest (+33%). The legacy behavior
stays available behind AMORT_LEGACY_ROUNDING=1.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.services.amortization import generate_schedule, schedule_totals, _add_months


def _total_interest(schedule):
    return sum(i.interest_payment for i in schedule)


class TestBulletStubTenor:
    def test_six_month_bullet_charges_six_months_interest(self):
        s = generate_schedule(
            Decimal("100000"), Decimal("10"), 6, repayment_type="bullet",
            start=date(2026, 1, 15),
        )
        assert len(s) == 1
        # 100000 * 10% * 6/12 = 5000 — NOT 10000.
        assert s[0].interest_payment == Decimal("5000.00")
        assert s[0].principal_payment == Decimal("100000.00")
        assert s[0].closing_balance == Decimal("0.00")
        assert s[0].payment_date == date(2026, 7, 15)

    def test_eighteen_month_bullet_charges_eighteen_months_interest(self):
        s = generate_schedule(
            Decimal("100000"), Decimal("10"), 18, repayment_type="bullet",
            start=date(2026, 1, 15),
        )
        # One full annual period + one 6-month stub.
        assert len(s) == 2
        assert _total_interest(s) == Decimal("15000.00")  # 18 months, not 24
        assert s[-1].payment_date == date(2027, 7, 15)
        assert s[-1].closing_balance == Decimal("0.00")

    def test_whole_multiple_tenor_unchanged(self):
        s = generate_schedule(
            Decimal("100000"), Decimal("10"), 12, repayment_type="bullet",
            start=date(2026, 1, 15),
        )
        assert len(s) == 1
        assert s[0].interest_payment == Decimal("10000.00")


class TestQuarterlyStubTenor:
    def test_four_month_quarterly_not_rounded_down_to_one_quarter(self):
        s = generate_schedule(
            Decimal("100000"), Decimal("12"), 4, repayment_type="quarterly",
            start=date(2026, 1, 31),
        )
        # One full quarter + a 1-month stub; interest covers 4 months total.
        assert len(s) == 2
        assert s[-1].closing_balance == Decimal("0.00")
        total_int = _total_interest(s)
        # Full quarter on 100k at 3% = 3000; stub 1 month at 1% on the
        # remaining balance — strictly between 3000 (1 quarter only) and
        # 4000 (upper bound: full principal for 4 months).
        assert Decimal("3000") < total_int < Decimal("4000")

    def test_schedule_balances_to_zero(self):
        s = generate_schedule(
            Decimal("50000"), Decimal("9"), 14, repayment_type="quarterly",
        )
        assert s[-1].closing_balance == Decimal("0.00")
        assert sum(i.principal_payment for i in s) == Decimal("50000.00")


class TestCalendarDates:
    def test_monthly_dates_follow_calendar_months(self):
        s = generate_schedule(
            Decimal("12000"), Decimal("0"), 12, start=date(2026, 1, 31),
        )
        assert [i.payment_date for i in s[:3]] == [
            date(2026, 2, 28),  # clamped — 2026 not a leap year
            date(2026, 3, 31),
            date(2026, 4, 30),
        ]
        assert s[-1].payment_date == date(2027, 1, 31)

    def test_add_months_clamps_day(self):
        assert _add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
        assert _add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)


class TestLegacyFlag:
    def test_legacy_rounding_restorable(self, monkeypatch):
        monkeypatch.setenv("AMORT_LEGACY_ROUNDING", "1")
        s = generate_schedule(
            Decimal("100000"), Decimal("10"), 6, repayment_type="bullet",
            start=date(2026, 1, 15),
        )
        # Old behavior: 6-month bullet rounded to one ANNUAL period.
        assert len(s) == 1
        assert s[0].interest_payment == Decimal("10000.00")


class TestTotalsStillConsistent:
    def test_totals_sum_matches_installments(self):
        s = generate_schedule(Decimal("100000"), Decimal("8.5"), 24)
        t = schedule_totals(s)
        assert t["total_repayment_amount"] == sum(i.total_payment for i in s)
        assert t["total_interest"] == _total_interest(s)
