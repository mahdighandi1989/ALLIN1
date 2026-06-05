"""Unit tests for ``app.services.facility_authorization``.

These tests exercise the authorization policy in isolation — no router, no real
database — using lightweight stand-in user objects. They document the
ground-truth decision recorded in the service module: facility access is governed
by the global role hierarchy (pending < viewer < editor < admin), not by any
per-customer ownership the user model does not have.
"""
import pytest
from types import SimpleNamespace

from fastapi import HTTPException

from app.services.facility_authorization import (
    FORBIDDEN_READ,
    FORBIDDEN_WRITE,
    authorize_facility_read,
    authorize_facility_write,
    can_read_facilities,
    can_read_facility,
    can_write_facilities,
    require_facility_reader,
)


def _user(role="pending", is_admin=False):
    """Minimal user-like object: the service only reads ``role``/``is_admin``."""
    return SimpleNamespace(role=role, is_admin=is_admin)


class TestCanRead:
    def test_pending_cannot_read(self):
        assert can_read_facilities(_user("pending")) is False

    def test_viewer_can_read(self):
        assert can_read_facilities(_user("viewer")) is True

    def test_editor_can_read(self):
        assert can_read_facilities(_user("editor")) is True

    def test_admin_role_can_read(self):
        assert can_read_facilities(_user("admin")) is True

    def test_is_admin_flag_overrides_low_role(self):
        # The AUTH_DISABLED demo user is role-less but is_admin=True.
        assert can_read_facilities(_user("pending", is_admin=True)) is True

    def test_unknown_role_treated_as_no_access(self):
        assert can_read_facilities(_user("banana")) is False

    def test_missing_role_attr_treated_as_pending(self):
        assert can_read_facilities(SimpleNamespace(is_admin=False)) is False

    def test_none_role_treated_as_pending(self):
        assert can_read_facilities(_user(role=None)) is False

    def test_can_read_facility_ignores_facility_but_follows_role(self):
        facility = SimpleNamespace(id="fac1", customer_id="cust1")
        assert can_read_facility(_user("viewer"), facility) is True
        assert can_read_facility(_user("pending"), facility) is False


class TestCanWrite:
    def test_pending_cannot_write(self):
        assert can_write_facilities(_user("pending")) is False

    def test_viewer_cannot_write(self):
        assert can_write_facilities(_user("viewer")) is False

    def test_editor_can_write(self):
        assert can_write_facilities(_user("editor")) is True

    def test_admin_can_write(self):
        assert can_write_facilities(_user("admin")) is True

    def test_is_admin_flag_can_write(self):
        assert can_write_facilities(_user("viewer", is_admin=True)) is True


class TestAuthorizeRead:
    def test_authorized_read_does_not_raise(self):
        authorize_facility_read(_user("viewer"))  # no exception

    @pytest.mark.parametrize("role", ["pending", "banana", None])
    def test_unauthorized_read_raises_403(self, role):
        with pytest.raises(HTTPException) as exc:
            authorize_facility_read(_user(role))
        assert exc.value.status_code == 403
        assert exc.value.detail == FORBIDDEN_READ


class TestAuthorizeWrite:
    def test_authorized_write_does_not_raise(self):
        authorize_facility_write(_user("editor"))  # no exception

    @pytest.mark.parametrize("role", ["pending", "viewer"])
    def test_unauthorized_write_raises_403(self, role):
        with pytest.raises(HTTPException) as exc:
            authorize_facility_write(_user(role))
        assert exc.value.status_code == 403
        assert exc.value.detail == FORBIDDEN_WRITE


class TestRequireFacilityReaderDependency:
    async def test_returns_user_when_authorized(self):
        user = _user("viewer")
        # Dependency is called with the already-resolved current_user.
        assert await require_facility_reader(current_user=user) is user

    async def test_raises_403_for_pending(self):
        with pytest.raises(HTTPException) as exc:
            await require_facility_reader(current_user=_user("pending"))
        assert exc.value.status_code == 403
        assert exc.value.detail == FORBIDDEN_READ
