"""Every live facility must have a fully ticked own checklist; the bell names
what is missing and links to that facility's checklist."""
from sqlalchemy import select

from app.models.crm import FacilityChecklist
from app.models.customer import Customer
from app.models.facility import Facility
from app.models.notification import Notification
from app.services.checklist import scan_incomplete_checklists, missing_steps


async def _mk(db, acc, fid, status="active"):
    c = Customer(account_no=acc, name=f"C{acc}")
    db.add(c)
    await db.flush()
    db.add(Facility(id=fid, customer_id=c.id, name="OD", amount=100, status=status))
    await db.commit()
    return c


async def test_scan_alerts_missing_checklist_and_resolves(db_session):
    c = await _mk(db_session, "A1", "F-1")
    await _mk(db_session, "A2", "F-2", status="closed")
    r = await scan_incomplete_checklists(db_session)
    assert r["incomplete"] == 1 and r["alerts_created"] == 1
    n = (await db_session.execute(select(Notification).where(Notification.category == "checklist:F-1"))).scalar_one()
    assert "Offer Letter" in n.message and "Archive" in n.message
    assert n.link == f"/customer-detail/?id={c.id}&tab=checklist&chk=F-1"
    # idempotent
    r = await scan_incomplete_checklists(db_session)
    assert r["alerts_created"] == 0 and r["alerts_refreshed"] == 1
    # complete it -> alert retired
    db_session.add(FacilityChecklist(id="FC-F-1", account_no="A1", facility_id="F-1",
                                     is_deleted=False, **{f"item{i}": "✓" for i in range(1, 10)}))
    await db_session.commit()
    r = await scan_incomplete_checklists(db_session)
    assert r["incomplete"] == 0 and r["alerts_resolved"] == 1


def test_missing_steps_partial():
    class FC: item1 = "✓"; item2 = "⌛"
    assert "Offer Letter" not in missing_steps(FC())
    assert "Document Verification" in missing_steps(FC())
