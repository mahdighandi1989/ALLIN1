# Excel (Frontend_Final.xlsm) → Panel — Gap Analysis & Implementation Roadmap

> خلاصه‌ی فارسی: این سند نتیجه‌ی بررسی دقیقِ فایل اکسلِ اصلی (`Frontend_Final.xlsm`،
> نسخه‌ی آپلودیِ کاربر) در برابر سیستم فعلی است. هدف: مشخص‌کردن «چه چیزی پیاده شده و
> چه چیزی نه» و یک نقشه‌ی فازبندی‌شده برای پیاده‌سازیِ بدون‌خطا با رعایت وابستگی‌ها.
> برآورد پوشش واقعی نسبت به کل سیستم اکسل: **~۲۰–۲۵٪**. پوسته‌ی عمومیِ CRUD و
> زیرساخت آماده است؛ منطقِ عمیقِ بانکی و ۲۵ خواسته‌ی صفحه‌ی «پرامپت» عمدتاً نیست.

## ✅ Implemented in this branch (Phases 1–3)

- **Phase 1 — data infrastructure:** structured **Mortgaged Properties**, **Fixed
  Deposits** and **Partners** (models + CRUD `/api/crm/{properties,fixed-deposits,
  partners}` + editable UI in customer-detail); **KYC document sub-fields** (issue
  date, remarks, passport nationality, Emirates-ID golden, visa type, tenancy
  address); **fine-grained facility types** (cheque_discounting, trust_receipt,
  lc_sight, lc_usance, log) + loan sub-fields.
- **Phase 2 — workflow core:** **per-facility checklist** + **auto-hourglass** on
  facility creation (`FacilityChecklist`, `/api/crm/facility-checklist/{id}`);
  **profile completeness** recompute + missing-field list
  (`/api/crm/completeness/{acc}`); **cascade delete** (facility → its checklist +
  tasks, with restore).
- **Phase 3 — documents:** **real per-row / per-checklist upload + download**
  (`/api/crm/attachments/...`, files on disk under `UPLOAD_DIR`), so a scanned
  document actually opens again (A15).

Verified: backend 413 passed / 78.6% coverage; frontend type-check + build + 23
jest tests pass; all routes registered; `/health` 200. **Phase 4** (real expiry
scheduler, server-side Summary PDF, rich notes + Outlook email, general
profiles/checklists, daily-log routing, backup) is **not** in this branch.

Source of truth analysed:
- **VBA**: 6 modules, **23,256 lines** (Module1 = 20,592), **384 procedures**
  (313 Sub + 71 Function), **480 constants**, a **~290-field** `PF_*` customer
  profile model.
- **Sheets**: `Checklist` (the core UI), `_Config` (distributed backend = ~10
  external Excel files), `پرامپت` (the user's **25 written requirements**).
- The deployed panel: FastAPI backend (`backend/app`) + Next.js SPA
  (`frontend/src/app`), with **two data layers**: clean ORM models, and the
  read-mostly legacy "CRM merge" tables.

Legend: ✅ done · 🟡 partial / shallow · 🔴 missing

---

## 1. Feature-by-feature status

| # | Feature (Excel) | Status | Evidence / Gap |
|---|---|---|---|
| 1 | Customer profile (basic) | 🟡 | `customers` table has core fields; **missing** `branch_code, business_type, rating, call_report, previous_files, open_date, updated_by` (some on `customer_profiles`). `credit-file-corporate` reads `branch_code` that doesn't exist → always blank |
| 2 | Identity docs (TL/Passport/EID/Visa/Tenancy) | 🟡 | only `*_no` + `*_expiry` on `customer_profiles`; **no issue date, no remarks, no document file path** for any; **no** Emirates-ID golden flag, **no** visa type |
| 3 | Partners / shareholders (8) | 🔴 | no table/columns; only flat keys in `customer_profiles.data_json`; read-only; print form shows 3 |
| 4 | Facilities (8 legacy types) | 🟡 | `facilities` table fine, but enum collapses **8→5** (`loan/overdraft/lc/lg/other`): no distinct Cheque-Discounting, Trust-Receipt, LC-Sight vs LC-Usance, LoG. **No** loan sub-type (Personal/Commercial/Staff), installments, maturity |
| 5 | Security matrix (AED/USD/IRR/Other) | 🔴 | only unbound `<input>`s in the print form; `securities` table is a free-text register, not the currency matrix |
| 6 | Fixed Deposits (FD ×5) | 🔴 | **no FD model** — free-text string only |
| 7 | Guarantors (6) | ✅ | `guarantors` table + `POST /api/crm/guarantors/{acc}` + detail tab |
| 8 | Mortgaged properties (3) | 🔴 | **no backend** — static `frontend/.../properties/data.ts` array; no persist/edit; missing `plate_no, insurance_no, address` |
| 9 | KYC status (OK/Expired/Warning) | 🔴 | no status record; only on-the-fly expiry calc |
| 10 | Credit-file Summary (Corp/Retail) | 🟡 | HTML print replicas; autofill ~6 fields (`branch_code` broken); **no persistence, no server PDF** — `window.print()` only |
| 11 | Checklist (per-facility, 9 items) | 🟡 | `checklist_progress` has 9 items **but keyed per-ACCOUNT (PK `account_no`)**, not per-facility; **no** auto-hourglass, **no** auto expiry row |
| 12 | Custom tasks / Pending list | 🟡 | `custom_tasks` table (imported) exists; no full pending-tasks workflow; "delete checklist also removes from pending" (req A5) absent |
| 13 | Expiry alerts → auto checklist row + pending | 🟡 | dashboard + notifications exist; **no** per-facility auto alert row, `expiry_warning_days` setting **not consumed** (30/90 hardcoded), no real scheduler |
| 14 | Attachments (per-row, per-checklist, upload+open) | 🔴 | `attachments` table is metadata-only mirror; **no upload endpoint**; req A10/A15 (open from row, "shared across checklists" tick) absent |
| 15 | Profile completeness / missing fields | 🔴 | stored string displayed only; **no recompute, no missing-field prompt** (A1/A25) |
| 16 | Summary↔Profile correlation + smart-ask-empty | 🔴 | A1/A2/A25 — "ask when left blank, fill later, summary as the data source" logic absent |
| 17 | Personal notes + reminders + Outlook email (API key, auto-send, signature) | 🔴 | basic `customer_notes` table only; the rich A8/A11/A16/A18/A20 system absent |
| 18 | General profiles & general checklists (non-account) | 🔴 | A7 — no equivalent |
| 19 | Cascade-delete facility across related DBs | 🔴 | A5 — trash exists, but no cross-entity cascade |
| 20 | Central Folder Upload (multi-file gather→copy) | 🔴 | A23 — not implemented |
| 21 | Backup system (incremental, offline resync) | 🔴 | A21 — not implemented |
| 22 | Daily journal → smart-route to account's latest checklist | 🟡 | `journal_entries` table (imported) exists; smart routing (A22) absent |
| 23 | Excel import / data pipeline | ✅ | `imports` + `data_merge` |
| 24 | Dashboard / Reports / Audit / Users / Auth / FX / Settings / Trash | ✅ | all present and solid |

### Key "correlation/dependency" gaps (what makes the system feel disjoint)
1. **Checklist is per-account, not per-facility.** Excel drives `LoadFacilityChecklist`
   off the facility id (`F5`); each facility has its own checklist. The panel stores one
   checklist per account.
2. **"Facility must exist before checklist edits"** (`RequireFacilityBeforeChange`) and
   **auto-hourglass** on facility creation (A24) — not carried over.
3. **Expiry → checklist row → pending list** (A14) — no link from a document/facility
   expiry to an auto-created alert row.
4. **Enter once, reuse everywhere** (A1/A2/A25) — data typed in Add-to-Table / KYC must
   feed Summary + Profile; today each form is an island that re-asks or leaves blanks.
5. **Per-row document upload/retrieve** (A10/A15) — the archival backbone — has no upload
   endpoint at all.

---

## 2. The 25 user requirements (sheet «پرامپت») → status

| Req | Topic | Status |
|---|---|---|
| A1 | Ask later for fields left blank (e.g. facility id not yet created) | 🔴 |
| A2 | Upgrade Summary form; make it the data source for profile/applicant entry | 🔴 |
| A3 | Remember backend file per account-type+year (don't re-ask BROWSE) | 🔴 (Excel-file specific) |
| A4 | Persist unsaved form data when backend is locked by another user; auto close/save | 🔴 |
| A5 | Delete a facility (cascade across related DBs) / delete a checklist (also from pending) | 🔴 |
| A6 | KYC add shouldn't wipe prior rows (corporate has more rows) | 🟡 (no KYC-rows model) |
| A7 | General (non-account) profiles with multiple checklists | 🔴 |
| A8 | Per-day personal task/checklist scratch area (private, not in main backend) | 🔴 |
| A9 | Clicking a pending account must actually load it into the checklist | 🟡 |
| A10 | Per-row document upload (any format), open from same row, per-checklist scoping, "share across checklists" tick | 🔴 |
| A11 | Much richer personal-notes page | 🔴 |
| A12 | Enter & store FD (amount+currency, many) and Properties (full field set, many) per profile | 🔴 |
| A13 | Checklist rows ~19–30 visible by default (not hidden) | n/a in panel |
| A14 | Expiry warning (configurable days) → auto row in that facility's checklist + pending | 🔴 |
| A15 | Uploaded doc must actually open when viewed from the row | 🔴 |
| A16 | One-button Outlook email of personal notes (formatted, API key, mark-as-sent, auto-send schedule) | 🔴 |
| A17 | Fast accounts overview → drill-down → tick to pick accounts/profiles → formatted report saved+linked | 🟡 (reports exist, not this UX) |
| A18 | Compose Persian email + attach existing/new docs, send via Outlook, link email to account profile, signature | 🔴 |
| A19 | Rows 20–30 still hidden after account switch | n/a in panel |
| A20 | Persian notes box: slow typing, RTL, default font, clear placeholder | 🔴 |
| A21 | Backup system (incremental journal-based, offline resync) | 🔴 |
| A22 | Free-text daily log → auto-route to account's latest checklist by 6-digit account no (amount vs account disambiguation) | 🔴 |
| A23 | Central Folder Upload: gather files from many folders → copy to chosen dest + customer folder, one click | 🔴 |
| A24 | New facility → auto-hourglass on its checklist items | 🔴 |
| A25 | KYC/Summary should only ask for what's actually missing; pull guarantor names/cheques already entered | 🔴 |

---

## 3. Implementation roadmap (phased, dependency-ordered)

Each phase is independently shippable and verified (backend tests + type-check).

### Phase 1 — Data infrastructure (foundation everything else needs)
- **1a. Mortgaged Properties** backend: `MortgagedProperty` model (plate_no,
  mortgage_deed_no, city, address, type, building_age, land_area, cnbc, valuation
  + currency, insurance_expiry, insurance_no, last_valuation_date, mortgage_date,
  mortgage_amount, country UAE/Iran), `POST/PATCH/DELETE /api/crm/properties/{acc}`,
  wired into `/customers/{id}/detail`.
- **1b. Fixed Deposits** backend: `FixedDeposit` model (fd_number, amount, currency,
  open_date, maturity_date, rate, remarks), CRUD by account.
- **1c. Partners** backend: `Partner` model (name, nationality, share, remarks),
  CRUD by account.
- **1d. Document fields** on `customer_profiles`: add issue-date + remarks + file-path
  for each of the 5 doc types; add Emirates-ID golden flag + visa type.
- **1e. Facility granularity**: extend `FacilityType` with the legacy set (cheque
  discounting, trust receipt, lc_sight, lc_usance, log) + loan sub-type/installments/
  maturity columns; keep tolerant mapping for old data.
- Frontend: add entry/edit forms + tabs in `customer-detail` for Properties, FDs,
  Partners; bind the credit-file Summary inputs to these.

### Phase 2 — Workflow core (the correlation engine)
- **2a. Per-facility checklist**: re-key checklist to `(account_no, facility_id)`;
  each facility gets its own 9-item checklist; migrate existing per-account rows.
- **2b. Auto-hourglass** (A24): on facility create, seed its checklist items "pending".
- **2c. Summary↔Profile single source** (A2/A25): Summary reads from + writes to the
  profile/guarantors/securities/properties/FDs; only prompt for genuinely-missing
  fields; pull guarantor names/cheques already entered.
- **2d. Profile completeness** (A15-calc/A25): server-side recompute + missing-field
  list endpoint.
- **2e. Cascade delete** (A5): deleting a facility soft-deletes its checklist, tasks,
  and alert rows, and removes them from the pending list.

### Phase 3 — Document upload/retrieval (archival backbone)
- **3a. Real upload endpoint**: `POST /api/crm/attachments/{acc}` (multipart),
  stored under a per-customer/per-checklist reference; `GET` to open/download.
- **3b. Per-row, per-checklist scoping** (A10): attachment bound to (account,
  checklist, row); "share across checklists" flag (`is_shared`).
- **3c. Fix view-from-row open** (A15): retrieval returns a working file/stream.

### Phase 4 — Alerts, summary output, notes/email, the rest
- **4a. Real expiry scheduler** (A14): consume `expiry_warning_days`; create a
  per-facility checklist alert row + a pending task + notification.
- **4b. Credit-file Summary persistence + server PDF** (Corp/Retail).
- **4c. Rich personal notes + reminders** (A8/A11/A20) + **Outlook/email send with
  signature, API key, mark-as-sent, schedule** (A16/A18).
- **4d. General profiles & general checklists** (A7).
- **4e. Daily-log smart routing** (A22), **Central Folder Upload** (A23),
  **Backup/offline resync** (A21).

---

## 4. Conventions to follow (so new code fits the codebase)
- New ORM models register on `Base.metadata`; import them in `app/db_init.py` so
  `ensure_schema()`'s `create_all` + self-healing column-add creates them on startup
  (the CRM-merge models — guarantor/security/crm — follow this; they are **not** in
  `models/__init__.py`).
- Per-account child entities follow `app/models/guarantor.py` (string PK id,
  `account_no` index, `is_deleted` flag) and the `app/routers/crm.py`
  `POST /{account_no}` pattern (`require_editor`, id like `X-{acc}-{timestamp}`).
- They surface through `GET /api/customers/{id}/detail` via the `_by_acc(Model)`
  helper — add the array + a `summary` count there.
- Tests: `backend/tests/` with `client` + `auth_headers` fixtures (in-memory SQLite).

**Status of this roadmap**: Phases 1–3 are implemented and verified on this
branch (see "Implemented in this branch" at the top). Phase 4 remains open.
