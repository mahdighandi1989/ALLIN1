# Unused-Endpoint Audit

Audit of 10 backend API endpoints flagged by automated analysis as "unused"
(no frontend `fetch`/`axios`/`apiClient` caller detected). Each endpoint was
manually re-verified against the frontend (`frontend/src`), tests and docs, then
categorised as **connected** (false positive), **internal** (intentionally not
SPA-facing → hidden from the public OpenAPI schema via `include_in_schema=False`)
or **deprecated** (dead code → removed).

> Production access-log review (the 30-day check called out in the task risk
> notes) is **not available to this automated change**. Because of that, the
> only endpoint *removed* is one that is both provably unreferenced *and* a
> security liability if left live (`POST /register`). Every other genuinely
> unused-but-valid endpoint was tagged `internal` rather than deleted, which is
> non-destructive and avoids silent failures for any out-of-band consumer.

## Summary

| # | Endpoint | File | Verdict | Action |
|---|----------|------|---------|--------|
| 1 | `POST /api/auth/register` | `backend/app/routers/auth.py` | deprecated / security risk | **Removed** (endpoint, `UserRegister` schema, 4 tests) |
| 2 | `GET /metrics` | `backend/app/main.py` | internal (observability) | `include_in_schema=False` |
| 3 | `GET /api/customers/export.csv` | `backend/app/routers/customers.py` | **connected** (false positive) | none — confirmed wired |
| 4 | `GET /api/facilities/search/advanced` | `backend/app/routers/facilities.py` | internal (extended search, not yet wired) | `include_in_schema=False` |
| 5 | `GET /api/imports/customers/template` | `backend/app/routers/imports.py` | **connected** (false positive) | none — confirmed wired |
| 6 | `GET /api/offer-letters/{offer_id}` | `backend/app/routers/offer_letters.py` | **connected** (false positive) | none — confirmed wired |
| 7 | `POST /api/notifications/{notification_id}/read` | `backend/app/routers/notifications.py` | **connected** (false positive) | none — confirmed wired |
| 8 | `GET /api/reports/portfolio/export.pdf` | `backend/app/routers/reports.py` | **connected** (false positive) | none — confirmed wired |
| 9 | `POST /api/trash/{entity}/{item_id}/restore` | `backend/app/routers/trash.py` | **connected** (false positive) | none — confirmed wired |
| 10 | `GET /api/users/{user_id}` | `backend/app/routers/users.py` | internal (admin CRUD member, not consumed) | `include_in_schema=False` |

## Per-endpoint detail

### 1. `POST /api/auth/register` — **REMOVED**
- **Category:** deprecated / dead code + unauthenticated attack surface.
- **Evidence:** No frontend caller (`authApi` exposes only `config`, `login`,
  `me`, `updateProfile`, `changePassword`, `logout`, `refresh` — no register).
  The bootstrap admin is seeded from environment by `seed_admin_user()` in
  `backend/app/db_init.py`, not via `/register`. Day-to-day accounts are created
  by admins via `POST /api/users/`.
- **Why removed (not tagged internal):** the handler created active users with
  no authentication. Hiding it from the schema would leave anonymous account
  creation reachable, so removal is the only action that actually closes the
  hole.
- **Synced:** removed the `register` handler and the now-unused `UserRegister`
  Pydantic model from `auth.py`; removed the 4 `test_register_*` tests from
  `backend/tests/test_auth.py`. OpenAPI is generated from code, so dropping the
  route removes it from the spec automatically.

### 2. `GET /metrics` — **internal**
- Prometheus exposition endpoint (`generate_latest()`), scraped by the metrics
  stack, never by the SPA. Documented in `docs/OBSERVABILITY.md` and covered by
  `backend/tests/test_interaction_logging.py`. Marked `include_in_schema=False`
  so it stays functional but no longer clutters the public API docs.

### 3. `GET /api/customers/export.csv` — **connected (false positive)**
- Called from `frontend/src/app/customers/page.tsx` via
  `downloadFile('/api/customers/export.${fmt}')` with `fmt='csv'`. No change.

### 4. `GET /api/facilities/search/advanced` — **internal**
- Richer search than the main `GET /api/facilities/` list (adds start-date range
  and customer-name filtering) but not wired to the SPA, which uses the list
  endpoint's filters. Kept functional for API/admin consumers, tagged
  `include_in_schema=False`.

### 5. `GET /api/imports/customers/template` — **connected (false positive)**
- Called from `frontend/src/app/import/page.tsx` via
  `downloadFile('/api/imports/${kind}/template')` with `kind='customers'`. No change.

### 6. `GET /api/offer-letters/{offer_id}` — **connected (false positive)**
- Called by `offerLettersApi.get()` (`frontend/src/lib/api.ts`). No change.

### 7. `POST /api/notifications/{notification_id}/read` — **connected (false positive)**
- Called by `notificationsApi.markRead()` (`frontend/src/lib/api.ts`). No change.

### 8. `GET /api/reports/portfolio/export.pdf` — **connected (false positive)**
- Called from `frontend/src/app/reports/page.tsx` via `downloadFile(...)`. No change.

### 9. `POST /api/trash/{entity}/{item_id}/restore` — **connected (false positive)**
- Called by `trashApi.restore()` (`frontend/src/lib/api.ts`), used by the trash
  page restore button. No change.

### 10. `GET /api/users/{user_id}` — **internal**
- Valid REST member of the admin users resource; the SPA uses the
  list/create/update/deactivate siblings but not single-fetch. Kept for API/admin
  completeness, tagged `include_in_schema=False`.

## Dependency sync check
- **upstream:** none broken — removed `register` used only `UserRegister`
  (also removed) and shared helpers (`hash_password`, `create_access_token`)
  that remain in use by other handlers.
- **downstream:** the only callers of `/register` were the 4 removed tests; no
  frontend, script or doc referenced it. The `include_in_schema=False` flags are
  documentation-only and change no runtime behaviour or call contract.
- **cross-tier (backend ↔ frontend ↔ db ↔ infra):** no frontend change required
  (no SPA code called any removed/tagged route); no DB/migration impact; `/metrics`
  scrape path is unchanged for the infra/Prometheus side.
- **side artifacts:** OpenAPI regenerates from code; this audit doc and
  `docs/OBSERVABILITY.md` updated; no i18n/env/CI impact.

## Re-verification (2026-06-05)

All 10 verdicts were independently re-verified against the live tree:

- **Removed** — `auth.py` no longer defines `register`/`UserRegister`;
  `backend/tests/test_auth.py` has no `register` tests (only an explanatory
  note remains).
- **Internal flags present** — `GET /metrics`
  (`backend/app/main.py:162`), `GET /api/facilities/search/advanced`
  (`facilities.py:220-222`) and `GET /api/users/{user_id}`
  (`users.py:68`) all carry `include_in_schema=False`.
- **Connected (false positives) confirmed wired** — frontend callers verified:
  `customers/page.tsx` (`/api/customers/export.${fmt}`),
  `import/page.tsx` (`/api/imports/${kind}/template`),
  `offerLettersApi.get` (`/api/offer-letters/${id}`),
  `notificationsApi.markRead` (`/api/notifications/${id}/read`),
  `reports/page.tsx` (`/api/reports/portfolio/export.pdf`),
  `trashApi.restore` (`/api/trash/${entity}/${id}/restore`).
- **Tests** — `pytest backend/tests/test_auth.py test_users.py
  test_facilities.py` → 48 passed. `py_compile` of all changed modules clean.

No code change was required; this entry records the audit was re-run end to end.
