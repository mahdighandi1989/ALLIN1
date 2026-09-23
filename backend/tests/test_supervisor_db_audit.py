"""v135 — the automated supervisor's data checks must actually catch bad data.

An auditor that silently finds nothing is worse than none, so every rule is fed
a record that violates it and a record that does not. The checks are imported
from the script the scheduled Routine runs, so this test guards the real thing.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.crm import CustomerProfile
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.models.profile_entities import Partner, MortgagedProperty

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts" / "supervisor" / "db_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("sup_db_audit", SPEC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sup_db_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def audit():
    assert SPEC.exists(), "the supervisor's data auditor must exist"
    return _load()


def _kinds(findings, table=None):
    return {f["kind"] for f in findings if table is None or f["table"] == table}


def _details(findings):
    return " | ".join(f["detail"] for f in findings)


async def _run(audit, db_session):
    """Run the auditor's checks against the test session (no second connection)."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _reuse():
        yield db_session

    return await audit.run(session_factory=_reuse)


class TestSkepticalChecks:
    async def test_clean_data_produces_no_findings(self, audit, db_session):
        db_session.add(Customer(account_no="800001", name="Clean Trading LLC",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert rep["total_findings"] == 0, _details(rep["findings"])

    async def test_catches_an_impossible_interest_rate(self, audit, db_session):
        c = Customer(account_no="800002", name="Rate Co", account_type=AccountType.CORPORATE,
                     status=CustomerStatus.ACTIVE)
        db_session.add(c)
        await db_session.flush()
        db_session.add(Facility(id="SUP-F1", customer_id=c.id, facility_type=FacilityType.LOAN,
                                status=FacilityStatus.ACTIVE, amount=100000, interest_rate=3300000))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "impossible" in _kinds(rep["findings"], "facilities"), _details(rep["findings"])

    async def test_catches_a_date_parked_in_a_name(self, audit, db_session):
        db_session.add(Customer(account_no="800003", name="2026/09/23",
                                account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "malformed" in _kinds(rep["findings"], "customers"), _details(rep["findings"])

    async def test_catches_an_expiry_before_its_own_issue_date(self, audit, db_session):
        db_session.add(Customer(account_no="800004", name="Expiry Co",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(CustomerProfile(account_no="800004", customer_name="Expiry Co",
                                       passport_issue="2025-01-10", passport_expiry="2020-01-10"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert any("انقضا" in f["detail"] for f in rep["findings"]), _details(rep["findings"])

    async def test_catches_an_orphan_record(self, audit, db_session):
        db_session.add(MortgagedProperty(id="SUP-P1", account_no="999999", prop_type="Villa"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "orphan" in _kinds(rep["findings"], "properties"), _details(rep["findings"])

    async def test_catches_partner_shares_that_do_not_add_up(self, audit, db_session):
        db_session.add(Customer(account_no="800005", name="Share Co",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(Partner(id="SUP-PA1", account_no="800005", name="A", share="30"))
        db_session.add(Partner(id="SUP-PA2", account_no="800005", name="B", share="30"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "contradictory" in _kinds(rep["findings"], "partners"), _details(rep["findings"])

    async def test_accepts_partner_shares_that_do_add_up(self, audit, db_session):
        db_session.add(Customer(account_no="800006", name="Good Share Co",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(Partner(id="SUP-PB1", account_no="800006", name="A", share="60"))
        db_session.add(Partner(id="SUP-PB2", account_no="800006", name="B", share="40"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "contradictory" not in _kinds(rep["findings"], "partners"), _details(rep["findings"])

    async def test_reports_which_database_it_audited(self, audit, db_session):
        """An audit of an empty local DB must never be mistaken for production."""
        rep = await _run(audit, db_session)
        assert rep["database"], "the audited database must be named in the report"
        assert "is_local_placeholder" in rep

    async def test_a_password_in_the_url_is_never_reported(self, audit, monkeypatch, db_session):
        monkeypatch.setattr(audit, "DB_URL", "postgresql+asyncpg://user:sup3rsecret@host/db")
        rep = await _run(audit, db_session)
        assert "sup3rsecret" not in rep["database"]
        assert "***" in rep["database"]
