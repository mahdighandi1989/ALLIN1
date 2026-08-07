"""Tests for audit logging + the admin audit-log viewer."""
import pytest
from httpx import AsyncClient

from app.models.user import User


class TestAuditLog:
    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict):
        # regular user -> 403
        assert (await client.get("/api/audit/", headers=auth_headers)).status_code == 403

    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/audit/")).status_code == 401

    async def test_customer_crud_is_audited(
        self, client: AsyncClient, admin_headers: dict
    ):
        # create a customer as admin
        c = await client.post(
            "/api/customers/",
            json={"account_no": "AUDIT-X", "name": "Audited Co", "account_type": "sme"},
            headers=admin_headers,
        )
        assert c.status_code == 201
        cid = c.json()["id"]
        await client.put(f"/api/customers/{cid}", json={"name": "Renamed"}, headers=admin_headers)
        await client.delete(f"/api/customers/{cid}", headers=admin_headers)

        audit = await client.get("/api/audit/", headers=admin_headers)
        assert audit.status_code == 200
        actions = {(e["action"], e["entity_type"]) for e in audit.json()["items"]}
        assert ("create", "customer") in actions
        assert ("update", "customer") in actions
        assert ("delete", "customer") in actions
        # entries carry the actor + an IP.
        entry = next(e for e in audit.json()["items"] if e["entity_type"] == "customer")
        assert entry["username"] is not None
        assert entry["created_at"] is not None

    async def test_filter_by_action_and_entity(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "FLT-1", "name": "Filter Co", "account_type": "retail"},
            headers=admin_headers,
        )
        r = await client.get(
            "/api/audit/?action=create&entity_type=customer", headers=admin_headers
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert all(
            e["action"] == "create" and e["entity_type"] == "customer"
            for e in r.json()["items"]
        )

    async def test_user_management_is_audited(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/users/",
            json={
                "username": "audited", "email": "audited@x.ae",
                "password": "secret123", "full_name": "Audited User",
            },
            headers=admin_headers,
        )
        r = await client.get("/api/audit/?entity_type=user", headers=admin_headers)
        assert r.status_code == 200
        assert any(e["action"] == "create" for e in r.json()["items"])


class TestCustomerActivityLog:
    """Per-customer activity log (profile «Logs» tab) + the SPA activity hook."""

    async def test_action_carries_account_and_resolved_customer(
        self, client: AsyncClient, admin_headers: dict
    ):
        c = await client.post(
            "/api/customers/",
            json={"account_no": "LOG-1", "name": "Logged Co", "account_type": "sme"},
            headers=admin_headers,
        )
        assert c.status_code == 201
        cid = c.json()["id"]
        r = await client.get("/api/audit/?account_no=LOG-1", headers=admin_headers)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items and all(e["account_no"] == "LOG-1" for e in items)
        # account_no is resolved to the owning customer for deep-linking.
        e = items[0]
        assert e["customer_name"] == "Logged Co"
        assert e["customer_id"] == cid

    async def test_customer_scoped_log_visible_to_regular_user(
        self, client: AsyncClient, admin_headers: dict, auth_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "LOG-2", "name": "Scoped Co", "account_type": "retail"},
            headers=admin_headers,
        )
        # a NON-admin (who can see the profile) can read that customer's log
        r = await client.get("/api/audit/customer/LOG-2", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert all(e["account_no"] == "LOG-2" for e in r.json()["items"])

    async def test_profile_edit_is_logged_under_customer(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "LOG-3", "name": "Prof Co", "account_type": "sme"},
            headers=admin_headers,
        )
        u = await client.patch(
            "/api/crm/profile/LOG-3", json={"passport_no": "P123"}, headers=admin_headers
        )
        assert u.status_code == 200
        r = await client.get("/api/audit/customer/LOG-3", headers=admin_headers)
        assert any(e["entity_type"] == "profile" for e in r.json()["items"])

    async def test_activity_endpoint_logs_client_form(
        self, client: AsyncClient, admin_headers: dict, auth_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "LOG-4", "name": "Form Co", "account_type": "retail"},
            headers=admin_headers,
        )
        p = await client.post(
            "/api/audit/activity",
            json={"action": "print", "entity_type": "voucher",
                  "account_no": "LOG-4", "detail": "چاپِ سندِ ضمانتی"},
            headers=auth_headers,
        )
        assert p.status_code == 200
        # shows under the customer …
        r = await client.get("/api/audit/customer/LOG-4", headers=auth_headers)
        assert any(e["entity_type"] == "voucher" and e["action"] == "print" for e in r.json()["items"])
        # … and in the global log with the customer resolved.
        g = await client.get("/api/audit/?account_no=LOG-4", headers=admin_headers)
        gi = next(e for e in g.json()["items"] if e["entity_type"] == "voucher")
        assert gi["customer_name"] == "Form Co"

    async def test_activity_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/audit/activity", json={"action": "print"})
        assert r.status_code == 401

    async def test_date_range_filter_and_csv_export(
        self, client: AsyncClient, admin_headers: dict
    ):
        from datetime import date, timedelta
        await client.post(
            "/api/customers/",
            json={"account_no": "LOG-5", "name": "Dated Co", "account_type": "sme"},
            headers=admin_headers,
        )
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        # today's entry is inside [today, …] but not [tomorrow, …]
        r_in = await client.get(f"/api/audit/customer/LOG-5?date_from={today}", headers=admin_headers)
        assert r_in.status_code == 200 and r_in.json()["total"] >= 1
        r_out = await client.get(f"/api/audit/customer/LOG-5?date_from={tomorrow}", headers=admin_headers)
        assert r_out.status_code == 200 and r_out.json()["total"] == 0
        # CSV export
        csv = await client.get("/api/audit/customer/LOG-5/export.csv", headers=admin_headers)
        assert csv.status_code == 200
        assert "text/csv" in csv.headers["content-type"]
        assert "LOG-5" in csv.text and "Dated Co" in csv.text

    async def test_property_add_and_delete_are_logged(
        self, client: AsyncClient, admin_headers: dict
    ):
        await client.post(
            "/api/customers/",
            json={"account_no": "LOG-6", "name": "Prop Co", "account_type": "sme"},
            headers=admin_headers,
        )
        a = await client.post(
            "/api/crm/properties/LOG-6",
            json={"property_type": "Villa", "location": "Dubai"},
            headers=admin_headers,
        )
        assert a.status_code == 200
        pid = a.json()["id"]
        d = await client.delete(f"/api/crm/properties/{pid}", headers=admin_headers)
        assert d.status_code == 200
        r = await client.get("/api/audit/customer/LOG-6", headers=admin_headers)
        pairs = {(e["action"], e["entity_type"]) for e in r.json()["items"]}
        assert ("create", "property") in pairs
        assert ("delete", "property") in pairs

    async def test_daily_log_routed_line_appears_in_customer_log(
        self, client: AsyncClient, admin_headers: dict
    ):
        """v86 — a daily-log line mentioning an account must show up in that
        customer's «لاگِ کارها» tab (the activity log), not only as a task."""
        await client.post(
            "/api/customers/",
            json={"account_no": "445566", "name": "Daily Log Co", "account_type": "sme"},
            headers=admin_headers,
        )
        r = await client.post(
            "/api/crm/daily-log",
            json={"text": "پیگیری 445566 بابت تمدید ضمانت‌نامه", "followup_date": "2026-08-01"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["accounts_found"] == ["445566"] and body["routed"]
        log = await client.get("/api/audit/customer/445566", headers=admin_headers)
        items = log.json()["items"]
        rows = [e for e in items if e["entity_type"] == "daily_log"]
        assert rows, f"daily_log entry missing from activity log: {items}"
        assert "پیگیری" in rows[0]["detail"] and "2026-08-01" in rows[0]["detail"]

    async def test_security_cheque_release_marks_and_logs(
        self, client: AsyncClient, admin_headers: dict
    ):
        """v95 — the reversal voucher marks the cheque released (with date +
        settled facility) and the release shows in the account's activity log."""
        await client.post(
            "/api/customers/",
            json={"account_no": "778899", "name": "Rev Co", "account_type": "sme"},
            headers=admin_headers,
        )
        g = await client.post(
            "/api/crm/guarantors/778899",
            json={"guarantor_name": "NAEIMEH HASHEMI", "cheque_no": "133754",
                  "cheque_amount": 84000, "facility_id": "STF-1", "branch": "2624"},
            headers=admin_headers,
        )
        assert g.status_code == 200, g.text
        r = await client.post(
            "/api/crm/guarantors/778899/release",
            json={"cheque_no": "133754", "facility_id": "STF-1",
                  "settled_facility": "STF-1", "date": "07/08/2026"},
            headers=admin_headers,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] and body["released"] == 1
        gg = body["guarantors"][0]
        assert gg["released"] is True and gg["released_date"] == "07/08/2026"
        assert "SECURITY CHQ REVERSAL" in gg["release_note"] and "STF-1" in gg["release_note"]
        assert "LOAN SETTLED" not in gg["release_note"]   # v97 — verbatim, no auto prefix
        # idempotent second call → already_released
        r2 = await client.post(
            "/api/crm/guarantors/778899/release",
            json={"cheque_no": "133754"}, headers=admin_headers,
        )
        assert r2.json()["already_released"] == 1 and r2.json()["released"] == 0
        # v98 triage — facility known, cheque unknown ⇒ warn (likely cheque typo)
        r3 = await client.post(
            "/api/crm/guarantors/778899/release",
            json={"cheque_no": "999999", "facility_id": "STF-1"}, headers=admin_headers,
        )
        assert r3.status_code == 200 and r3.json()["ok"] is False
        assert r3.json()["error"] == "cheque_mismatch" and "133754" in r3.json()["message"]
        # v98 triage — cheque known, facility unknown ⇒ warn (likely facility typo)
        r4 = await client.post(
            "/api/crm/guarantors/778899/release",
            json={"cheque_no": "133754", "facility_id": "WRONG-9"}, headers=admin_headers,
        )
        assert r4.json()["ok"] is False and r4.json()["error"] == "facility_mismatch"
        assert "STF-1" in r4.json()["message"]
        # v98 — BOTH unknown ⇒ the facility was never recorded: create + release
        r5 = await client.post(
            "/api/crm/guarantors/778899/release",
            json={"cheque_no": "555001", "facility_id": "NEW-77",
                  "settled_facility": "O.D RENEWED", "date": "07/08/2026",
                  "guarantor_name": "NEW CO", "cheque_amount": 1000, "branch": "2900"},
            headers=admin_headers,
        )
        assert r5.status_code == 200, r5.text
        b5 = r5.json()
        assert b5["ok"] and b5["created"] is True and b5["released"] == 1
        g5 = b5["guarantors"][0]
        assert g5["released"] is True and g5["facility_id"] == "NEW-77"
        assert "O.D RENEWED" in g5["release_note"]
        lst5 = await client.get("/api/crm/guarantors/778899", headers=admin_headers)
        assert any(x["cheque_no"] == "555001" and x["released"] for x in lst5.json())
        # the release is in the account's activity log
        log = await client.get("/api/audit/customer/778899", headers=admin_headers)
        pairs = {(e["action"], e["entity_type"]) for e in log.json()["items"]}
        assert ("release", "security_cheque") in pairs
        # list endpoint carries the release fields
        lst = await client.get("/api/crm/guarantors/778899", headers=admin_headers)
        assert lst.json()[0]["released"] is True
