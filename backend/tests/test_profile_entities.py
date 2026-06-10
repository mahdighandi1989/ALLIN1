"""Profile child entities — mortgaged properties, fixed deposits, partners.

They are added/edited/removed via /api/crm/* and surfaced (with summary counts)
through GET /api/customers/{id}/detail. Mirrors requirement A12 of the legacy
Excel system: capture FD + property details per customer profile, many each.
"""
import pytest
from httpx import AsyncClient

from app.models.customer import Customer


class TestProfileEntities:
    async def test_property_crud_and_detail(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id

        # add
        r = await client.post(
            f"/api/crm/properties/{acc}", headers=auth_headers,
            json={"plate_no": "PL-123", "city": "Dubai", "mortgage_amount": 1500000,
                  "valuation": 2000000, "valuation_currency": "AED", "insurance_no": "INS-9"},
        )
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        assert r.json()["plate_no"] == "PL-123"
        assert r.json()["mortgage_amount"] == 1500000

        # surfaced in detail with summary counts
        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.status_code == 200, d.text
        body = d.json()
        assert len(body["properties"]) == 1
        assert body["summary"]["total_properties"] == 1
        assert body["summary"]["total_mortgage_amount"] == 1500000

        # edit
        u = await client.patch(f"/api/crm/properties/{pid}", headers=auth_headers, json={"city": "Abu Dhabi"})
        assert u.status_code == 200
        assert u.json()["city"] == "Abu Dhabi"
        assert u.json()["plate_no"] == "PL-123"  # untouched field preserved

        # soft-delete -> gone from detail
        x = await client.delete(f"/api/crm/properties/{pid}", headers=auth_headers)
        assert x.status_code == 200
        d2 = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d2.json()["summary"]["total_properties"] == 0

    async def test_fixed_deposit_crud(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        r = await client.post(
            f"/api/crm/fixed-deposits/{acc}", headers=auth_headers,
            json={"fd_number": "FD-1", "amount": 500000, "currency": "USD", "rate": "4.5%"},
        )
        assert r.status_code == 200, r.text
        fid = r.json()["id"]
        assert r.json()["amount"] == 500000
        assert r.json()["currency"] == "USD"

        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.json()["summary"]["total_fixed_deposits"] == 1
        assert d.json()["summary"]["total_fd_amount"] == 500000

        assert (await client.patch(f"/api/crm/fixed-deposits/{fid}", headers=auth_headers,
                                   json={"rate": "5%"})).json()["rate"] == "5%"
        assert (await client.delete(f"/api/crm/fixed-deposits/{fid}", headers=auth_headers)).status_code == 200

    async def test_partner_crud(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        r = await client.post(
            f"/api/crm/partners/{acc}", headers=auth_headers,
            json={"name": "Ali Reza", "nationality": "IR", "share": "60%"},
        )
        assert r.status_code == 200, r.text
        ptid = r.json()["id"]

        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert d.json()["summary"]["total_partners"] == 1
        assert d.json()["partners"][0]["name"] == "Ali Reza"
        assert d.json()["partners"][0]["share"] == "60%"
        assert (await client.delete(f"/api/crm/partners/{ptid}", headers=auth_headers)).status_code == 200

    async def test_partner_name_required(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        r = await client.post(f"/api/crm/partners/{test_customer.account_no}", headers=auth_headers, json={"nationality": "IR"})
        assert r.status_code == 422

    async def test_requires_auth(self, client: AsyncClient, test_customer: Customer):
        r = await client.post(f"/api/crm/properties/{test_customer.account_no}", json={"city": "X"})
        assert r.status_code == 401

    async def test_update_missing_returns_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.patch("/api/crm/properties/NOPE", headers=auth_headers, json={"city": "X"})
        assert r.status_code == 404


class TestFacilityGranularity:
    async def test_fine_grained_facility_types(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc = test_customer.account_no
        for raw, expected in [
            ("Cheque Discounting", "cheque_discounting"),
            ("TR", "trust_receipt"),
            ("LC Usance", "lc_usance"),
            ("LC Sight", "lc_sight"),
            ("LoG", "log"),
            ("OD", "overdraft"),
        ]:
            r = await client.post(f"/api/crm/facilities/{acc}", headers=auth_headers,
                                  json={"facility_type": raw, "amount": 1000})
            assert r.status_code == 200, r.text
            assert r.json()["facility_type"] == expected, f"{raw} -> {r.json()['facility_type']}"

    async def test_loan_subfields_persist(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        r = await client.post(f"/api/crm/facilities/{test_customer.account_no}", headers=auth_headers,
                              json={"facility_type": "loan", "amount": 5000, "loan_type": "Staff", "installments": "36"})
        assert r.status_code == 200, r.text
        assert r.json()["loan_type"] == "Staff"
        assert r.json()["installments"] == "36"


class TestFacilityChecklist:
    async def test_seeded_with_hourglasses_and_toggle(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        r = await client.post(f"/api/crm/facilities/{acc}", headers=auth_headers,
                              json={"facility_type": "loan", "amount": 1000})
        fid = r.json()["id"]
        # auto-seeded with an hourglass on every step (A24)
        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        mine = [fc for fc in d.json()["facility_checklists"] if fc["facility_id"] == fid]
        assert len(mine) == 1
        assert mine[0]["item1"] == "⌛" and mine[0]["item9"] == "⌛"
        assert mine[0]["total"] == "0"
        # toggle step 1 done -> ✓, total 1
        t = await client.patch(f"/api/crm/facility-checklist/{fid}", headers=auth_headers, json={"step": 1, "done": True})
        assert t.status_code == 200, t.text
        assert t.json()["item1"] == "✓"
        assert t.json()["total"] == "1"
        # un-toggle -> back to hourglass, total 0
        t2 = await client.patch(f"/api/crm/facility-checklist/{fid}", headers=auth_headers, json={"step": 1, "done": False})
        assert t2.json()["item1"] == "⌛"
        assert t2.json()["total"] == "0"

    async def test_main_facility_create_seeds_checklist(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        r = await client.post("/api/facilities/", headers=auth_headers,
                              json={"customer_id": test_customer.id, "facility_type": "lc", "amount": 2000, "currency": "AED"})
        assert r.status_code == 201, r.text
        fid = r.json()["id"]
        d = await client.get(f"/api/customers/{test_customer.id}/detail", headers=auth_headers)
        assert any(fc["facility_id"] == fid and fc["item1"] == "⌛" for fc in d.json()["facility_checklists"])


class TestKycDocFields:
    async def test_extended_kyc_fields_persist_and_surface(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        body = {
            "passport_issue": "2020-01-01", "passport_nationality": "Iran", "passport_remarks": "renewed",
            "emirates_id_golden": "Yes", "visa_type": "Investor", "tenancy_address": "Dubai Marina",
            "trade_license_remarks": "free zone licence",
        }
        r = await client.patch(f"/api/crm/profile/{acc}", headers=auth_headers, json=body)
        assert r.status_code == 200, r.text
        for k, v in body.items():
            assert r.json()[k] == v, k
        # surfaced in detail.profile
        prof = (await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)).json()["profile"]
        assert prof["passport_nationality"] == "Iran"
        assert prof["emirates_id_golden"] == "Yes"
        assert prof["visa_type"] == "Investor"
        assert prof["tenancy_address"] == "Dubai Marina"


class TestCompleteness:
    async def test_recompute_and_missing(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc = test_customer.account_no
        r0 = await client.get(f"/api/crm/completeness/{acc}", headers=auth_headers)
        assert r0.status_code == 200, r0.text
        assert r0.json()["percent"] < 100
        assert "Trade licence no" in r0.json()["missing"]
        base_missing = len(r0.json()["missing"])

        # fill some fields -> percent rises, fewer missing
        await client.patch(f"/api/crm/profile/{acc}", headers=auth_headers, json={"trade_license_no": "TL1", "rating": "A"})
        r1 = await client.get(f"/api/crm/completeness/{acc}", headers=auth_headers)
        assert r1.json()["percent"] >= r0.json()["percent"]
        assert len(r1.json()["missing"]) < base_missing
        assert "Trade licence no" not in r1.json()["missing"]

        # the profile PATCH itself returns the freshly stored completeness %
        upd = await client.patch(f"/api/crm/profile/{acc}", headers=auth_headers, json={"business_type": "Trading"})
        assert "%" in (upd.json().get("profile_completeness") or "")


class TestExpiryScan:
    async def test_scan_raises_facility_alert_task(self, client: AsyncClient, auth_headers: dict, admin_headers: dict, test_customer: Customer, test_facility):
        # test_facility expires 2024-12-31 (past) -> inside the alert window
        r = await client.post("/api/crm/run-expiry-scan", headers=admin_headers)
        assert r.status_code == 200, r.text
        assert r.json()["facilities"] >= 1 and r.json()["total"] >= 1

        d = await client.get(f"/api/customers/{test_customer.id}/detail", headers=auth_headers)
        alerts = [t for t in d.json()["tasks"] if "expire" in (t["task_name"] or "").lower() and t["priority"] == "High"]
        assert alerts, "expiry alert task not found on the customer"

        # idempotent — a second scan refreshes, never duplicates
        await client.post("/api/crm/run-expiry-scan", headers=admin_headers)
        d2 = await client.get(f"/api/customers/{test_customer.id}/detail", headers=auth_headers)
        alerts2 = [t for t in d2.json()["tasks"] if "expire" in (t["task_name"] or "").lower()]
        assert len(alerts2) == len(alerts)

    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict):
        r = await client.post("/api/crm/run-expiry-scan", headers=auth_headers)
        assert r.status_code == 403


class TestAttachments:
    async def test_upload_download_delete(self, client: AsyncClient, auth_headers: dict, test_customer: Customer, tmp_path, monkeypatch):
        from app.services import attachments as store
        monkeypatch.setattr(store, "UPLOAD_DIR", tmp_path)
        acc, cid = test_customer.account_no, test_customer.id

        files = {"file": ("doc.txt", b"hello world", "text/plain")}
        data = {"facility_id": "F-1", "row_index": "11", "is_shared": "false", "notes": "scan"}
        r = await client.post(f"/api/crm/attachments/{acc}", headers=auth_headers, files=files, data=data)
        assert r.status_code == 200, r.text
        aid = r.json()["id"]
        assert r.json()["original_name"] == "doc.txt"
        assert r.json()["facility_id"] == "F-1"
        assert r.json()["row_index"] == "11"

        # appears in detail.attachments
        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert any(a["id"] == aid for a in d.json()["attachments"])

        # download streams the real bytes back (fixes the Excel A15 'nothing opens')
        dl = await client.get(f"/api/crm/attachments/{aid}/download", headers=auth_headers)
        assert dl.status_code == 200
        assert dl.content == b"hello world"

        # delete removes the record (and the file)
        x = await client.delete(f"/api/crm/attachments/{aid}", headers=auth_headers)
        assert x.status_code == 200
        d2 = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert not any(a["id"] == aid for a in d2.json()["attachments"])

    async def test_download_missing_returns_404(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/crm/attachments/NOPE/download", headers=auth_headers)
        assert r.status_code == 404

    async def test_upload_requires_auth(self, client: AsyncClient, test_customer: Customer):
        files = {"file": ("x.txt", b"x", "text/plain")}
        r = await client.post(f"/api/crm/attachments/{test_customer.account_no}", files=files)
        assert r.status_code == 401


class TestFacilityCascade:
    async def test_delete_and_restore_cascade(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        acc, cid = test_customer.account_no, test_customer.id
        f = await client.post(f"/api/crm/facilities/{acc}", headers=auth_headers, json={"facility_type": "loan", "amount": 1000})
        fid = f.json()["id"]
        await client.post(f"/api/crm/tasks/{acc}", headers=auth_headers, json={"task_name": "do it", "facility_id": fid})

        d = await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)
        assert any(fc["facility_id"] == fid for fc in d.json()["facility_checklists"])

        dele = await client.delete(f"/api/facilities/{fid}", headers=auth_headers)
        assert dele.status_code == 204
        d2 = (await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)).json()
        assert not any(fc["facility_id"] == fid for fc in d2["facility_checklists"])
        tsk = [t for t in d2["tasks"] if t["facility_id"] == fid]
        assert tsk and tsk[0]["is_active"] == "0"

        await client.post(f"/api/facilities/{fid}/restore", headers=auth_headers)
        d3 = (await client.get(f"/api/customers/{cid}/detail", headers=auth_headers)).json()
        assert any(fc["facility_id"] == fid for fc in d3["facility_checklists"])
