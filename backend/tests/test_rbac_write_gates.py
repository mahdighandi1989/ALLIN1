"""Characterization tests: every mutating endpoint rejects the viewer role.

These lock the fixes for the write endpoints that used to be reachable by
read-only viewers (facility status/restore, customer restore, offer-letter
mutations, trash restore, imports, stats snapshot) and the ``is_active``
check in ``app.utils.security.get_current_user``.
"""
import pytest
from httpx import AsyncClient

from app.models.user import User
from app.models.customer import Customer
from app.models.facility import Facility, FacilityType, FacilityStatus
from app.utils.security import hash_password, create_access_token


async def _mk_user(db, username, role):
    u = User(
        username=username, email=f"{username}@x.ae",
        hashed_password=hash_password("Passw0rd1"), full_name=username.title(),
        is_active=True, role=role, is_admin=(role == "admin"),
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def _hdr(u):
    tok = create_access_token(data={"user_id": u.id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}


async def _mk_customer(db, account_no="RB100", deleted=False):
    c = Customer(account_no=account_no, name=f"Cust {account_no}", is_deleted=deleted)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def _mk_facility(db, customer_id, deleted=False):
    f = Facility(
        customer_id=customer_id, name="RBAC test facility",
        facility_type=FacilityType.LOAN, amount=1000,
        status=FacilityStatus.ACTIVE, is_deleted=deleted,
        risk_rating="medium",
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


class TestViewerWriteGates:
    async def test_viewer_cannot_change_facility_status(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate1", "viewer")
        c = await _mk_customer(db_session, "RB101")
        f = await _mk_facility(db_session, c.id)
        r = await client.patch(
            f"/api/facilities/{f.id}/status?new_status=written_off", headers=_hdr(viewer)
        )
        assert r.status_code == 403

    async def test_viewer_cannot_restore_facility(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate2", "viewer")
        c = await _mk_customer(db_session, "RB102")
        f = await _mk_facility(db_session, c.id, deleted=True)
        r = await client.post(f"/api/facilities/{f.id}/restore", headers=_hdr(viewer))
        assert r.status_code == 403

    async def test_viewer_cannot_restore_customer(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate3", "viewer")
        c = await _mk_customer(db_session, "RB103", deleted=True)
        r = await client.post(f"/api/customers/{c.id}/restore", headers=_hdr(viewer))
        assert r.status_code == 403

    async def test_viewer_cannot_restore_via_trash(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate4", "viewer")
        c = await _mk_customer(db_session, "RB104", deleted=True)
        r = await client.post(f"/api/trash/customer/{c.id}/restore", headers=_hdr(viewer))
        assert r.status_code == 403

    async def test_viewer_cannot_import_customers(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate5", "viewer")
        r = await client.post(
            "/api/imports/customers",
            files={"file": ("x.xlsx", b"junk", "application/vnd.ms-excel")},
            headers=_hdr(viewer),
        )
        assert r.status_code == 403

    async def test_viewer_cannot_capture_snapshot(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate6", "viewer")
        r = await client.post("/api/stats/snapshot", headers=_hdr(viewer))
        assert r.status_code == 403

    async def test_editor_can_change_facility_status(self, client: AsyncClient, db_session):
        editor = await _mk_user(db_session, "egate1", "editor")
        c = await _mk_customer(db_session, "RB105")
        f = await _mk_facility(db_session, c.id)
        r = await client.patch(
            f"/api/facilities/{f.id}/status?new_status=inactive", headers=_hdr(editor)
        )
        assert r.status_code == 200
        assert r.json()["status"] == "inactive"


class TestOfferLetterWriteGates:
    async def test_viewer_cannot_mutate_offer_letters(self, client: AsyncClient, db_session):
        viewer = await _mk_user(db_session, "vgate7", "viewer")
        # No offer needs to exist: 403 must win before the 404 lookup.
        assert (
            await client.put("/api/offer-letters/OLX", json={}, headers=_hdr(viewer))
        ).status_code == 403
        assert (
            await client.post(
                "/api/offer-letters/OLX/status?new_status=approved", headers=_hdr(viewer)
            )
        ).status_code == 403
        assert (
            await client.delete("/api/offer-letters/OLX", headers=_hdr(viewer))
        ).status_code == 403
        assert (
            await client.post("/api/offer-letters/OLX/restore", headers=_hdr(viewer))
        ).status_code == 403
        assert (
            await client.post(
                "/api/offer-letters/OLX/generate-schedule", headers=_hdr(viewer)
            )
        ).status_code == 403


class TestInactiveUserGate:
    async def test_deactivated_user_loses_access_immediately(self, client: AsyncClient, db_session):
        u = await _mk_user(db_session, "deact1", "editor")
        headers = _hdr(u)
        # Works while active…
        assert (await client.get("/api/customers/", headers=headers)).status_code == 200
        # …and is rejected as soon as the account is deactivated, even though
        # the JWT is still within its lifetime.
        u.is_active = False
        await db_session.commit()
        r = await client.get("/api/customers/", headers=headers)
        assert r.status_code in (400, 401)


class TestEmailLogin:
    async def test_login_with_email_identifier(self, client: AsyncClient, db_session):
        await _mk_user(db_session, "maillogin", "editor")
        r = await client.post(
            "/api/auth/login",
            json={"email": "maillogin@x.ae", "password": "Passw0rd1"},
        )
        assert r.status_code == 200
        assert r.json().get("access_token")

    async def test_login_with_username_still_works(self, client: AsyncClient, db_session):
        await _mk_user(db_session, "userlogin", "editor")
        r = await client.post(
            "/api/auth/login",
            json={"username": "userlogin", "password": "Passw0rd1"},
        )
        assert r.status_code == 200
