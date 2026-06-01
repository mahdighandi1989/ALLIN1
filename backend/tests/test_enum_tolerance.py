"""A legacy/dirty enum value in the DB must not 500 reads (TolerantEnum).

Regression for the production incident where a facility row with
``facility_type='OD'`` made every endpoint that loads facilities (customer list,
facility list, reports, exports) return 500.
"""
import pytest
from sqlalchemy import select, text
from httpx import AsyncClient

from app.models.customer import Customer, AccountType, CustomerStatus
from app.models.facility import Facility, FacilityType, FacilityStatus


async def _set_raw(db_session, table, col, value, row_id):
    """Set a column to an arbitrary value via raw SQL (bypasses ORM/validators)."""
    await db_session.execute(
        text(f"UPDATE {table} SET {col} = :v WHERE id = :i").bindparams(v=value, i=row_id)
    )
    await db_session.commit()


class TestEnumTolerance:
    async def test_dirty_facility_type_read_falls_back(self, db_session):
        """Reading a row with an unknown stored value yields the fallback, not an error."""
        c = Customer(account_no="ENUM-1", name="Enum Co",
                     account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE)
        db_session.add(c)
        await db_session.flush()
        f = Facility(customer_id=c.id, facility_type=FacilityType.LOAN,
                     amount=1000, status=FacilityStatus.ACTIVE)
        db_session.add(f)
        await db_session.commit()

        # Corrupt the stored value to a legacy code the enum doesn't define.
        await _set_raw(db_session, "facilities", "facility_type", "OD", f.id)

        # Selecting the column applies the TolerantEnum result processor.
        val = (await db_session.execute(
            select(Facility.facility_type).where(Facility.id == f.id)
        )).scalar_one()
        assert val == FacilityType.OTHER  # coerced fallback, no LookupError

    async def test_facilities_list_endpoint_survives_dirty_row(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        c = Customer(account_no="ENUM-2", name="Enum Co 2",
                     account_type=AccountType.CORPORATE, status=CustomerStatus.ACTIVE)
        db_session.add(c)
        await db_session.flush()
        f = Facility(customer_id=c.id, facility_type=FacilityType.LOAN,
                     amount=1000, status=FacilityStatus.ACTIVE)
        db_session.add(f)
        await db_session.commit()
        await _set_raw(db_session, "facilities", "facility_type", "OD", f.id)

        r = await client.get("/api/facilities/?page=1&page_size=50", headers=auth_headers)
        # The core regression: a dirty row must not 500 the whole listing.
        assert r.status_code == 200
        assert isinstance(r.json()["items"], list)

    async def test_dirty_customer_status_read_falls_back(self, db_session):
        c = Customer(account_no="ENUM-3", name="Enum Co 3",
                     account_type=AccountType.RETAIL, status=CustomerStatus.ACTIVE)
        db_session.add(c)
        await db_session.commit()
        await _set_raw(db_session, "customers", "status", "ARCHIVED", c.id)

        val = (await db_session.execute(
            select(Customer.status).where(Customer.id == c.id)
        )).scalar_one()
        assert val == CustomerStatus.ACTIVE  # fallback for customerstatus


class TestDirtyValueResponses:
    """A response model must serialize legacy/dirty rows, never reject them.

    Regression: a facility with amount=0 / currency='-', or a customer with a
    blank name / non-RFC email, used to 500 the whole list at response time
    because the response schema enforced *input* constraints (gt=0, min_length,
    EmailStr).
    """

    async def test_facilities_list_survives_dirty_amount_and_currency(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        # Raw insert (bypasses ORM/Pydantic) to mimic real legacy data.
        await db_session.execute(text(
            "INSERT INTO customers (id, account_no, name, account_type, status, is_deleted) "
            "VALUES ('CDIRTY1','ADIRTY1','Dirty Co','retail','active', 0)"
        ))
        await db_session.execute(text(
            "INSERT INTO facilities (id, customer_id, name, amount, currency, "
            "facility_type, status, outstanding, risk_rating, is_deleted) "
            "VALUES ('FDIRTY1','CDIRTY1','Bad Row',0,'-','loan','active',0,'low', 0)"
        ))
        await db_session.commit()

        r = await client.get("/api/facilities/?page=1&page_size=50", headers=auth_headers)
        assert r.status_code == 200
        match = [it for it in r.json()["items"] if it["id"] == "FDIRTY1"]
        assert match and float(match[0]["amount"]) == 0.0 and match[0]["currency"] == "-"

    async def test_customers_list_survives_blank_name_and_bad_email(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        await db_session.execute(text(
            "INSERT INTO customers (id, account_no, name, account_type, status, email, is_deleted) "
            "VALUES ('CDIRTY2','ADIRTY2','','retail','active','not-an-email', 0)"
        ))
        await db_session.commit()

        r = await client.get("/api/customers/?page=1&page_size=50", headers=auth_headers)
        assert r.status_code == 200
        assert any(it["id"] == "CDIRTY2" for it in r.json()["items"])
