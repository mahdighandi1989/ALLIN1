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
from app.models.crm import CustomerProfile, Attachment
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


class TestUnattributedAttachments:
    """v137 — a document the bank holds but cannot attribute to a customer.

    An import that confirms NO account still archives its source file under the
    reserved «unknown» marker (deliberately — losing it would be worse). Those
    files were invisible: nothing in the database referenced them, so they piled
    up in Drive unseen until the supervisor happened to look at the folder.
    """

    async def test_flags_the_unattributed_pile(self, audit, db_session):
        db_session.add(Attachment(id="SUP-A1", account_no="unknown",
                                  file_name="f1.pdf", original_name="f1.pdf",
                                  drive_file_id="d1", content_sha256="h1"))
        db_session.add(Attachment(id="SUP-A2", account_no="unknown",
                                  file_name="f2.pdf", original_name="f2.pdf",
                                  drive_file_id="d2", content_sha256="h2"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "orphan" in _kinds(rep["findings"], "attachments"), _details(rep["findings"])
        assert rep["counts"]["attachments_unattributed"] == 2

    async def test_the_pile_is_one_finding_not_one_per_file(self, audit, db_session):
        for i in range(12):
            db_session.add(Attachment(id=f"SUP-B{i}", account_no="unknown",
                                      file_name=f"f{i}.pdf", original_name=f"f{i}.pdf",
                                      drive_file_id=f"d{i}", content_sha256=f"hh{i}"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        att = [f for f in rep["findings"] if f["table"] == "attachments"]
        assert len(att) == 1, f"a per-file flood would bury every other finding: {att}"
        assert "12" in att[0]["detail"]

    async def test_flags_an_attachment_pointing_at_a_customer_that_is_gone(self, audit, db_session):
        db_session.add(Attachment(id="SUP-C1", account_no="999999",
                                  file_name="x.pdf", original_name="x.pdf",
                                  drive_file_id="dx", content_sha256="hx"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        det = _details(rep["findings"])
        assert "999999" in det, det

    async def test_flags_an_attachment_with_no_account_at_all(self, audit, db_session):
        db_session.add(Attachment(id="SUP-D1", account_no="",
                                  file_name="y.pdf", original_name="y.pdf",
                                  drive_file_id="dy", content_sha256="hy"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "orphan" in _kinds(rep["findings"], "attachments"), _details(rep["findings"])

    async def test_an_attachment_on_a_real_customer_is_not_flagged(self, audit, db_session):
        db_session.add(Customer(account_no="800077", name="Attached Co",
                                account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE))
        db_session.add(Attachment(id="SUP-E1", account_no="800077",
                                  file_name="ok.pdf", original_name="ok.pdf",
                                  drive_file_id="do", content_sha256="ho"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "attachments" not in {f["table"] for f in rep["findings"]}, _details(rep["findings"])
        assert rep["counts"]["attachments"] == 1
        assert rep["counts"]["attachments_unattributed"] == 0

    async def test_a_general_letter_attachment_is_reachable_and_not_an_orphan(self, audit, db_session):
        """A «نامهٔ عمومی» attachment has no account BY DESIGN — the letter owns it
        through fac-LTR-<id>, and the letters API finds it that way. Counting
        those would bury the genuinely unreachable ones (Drive holds dozens)."""
        db_session.add(Attachment(id="SUP-F1", account_no="general",
                                  facility_id="LTR-9d8fbc24e3594b0495c9e87ff0828117",
                                  file_name="g.pdf", original_name="g.pdf",
                                  drive_file_id="dg", content_sha256="hg"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "attachments" not in {f["table"] for f in rep["findings"]}, _details(rep["findings"])
        assert rep["counts"]["attachments_unattributed"] == 0

    async def test_an_attachment_with_neither_account_nor_letter_is_flagged(self, audit, db_session):
        db_session.add(Attachment(id="SUP-G1", account_no="", facility_id="",
                                  file_name="n.pdf", original_name="n.pdf",
                                  drive_file_id="dn", content_sha256="hn"))
        await db_session.commit()
        rep = await _run(audit, db_session)
        assert "orphan" in _kinds(rep["findings"], "attachments"), _details(rep["findings"])
