# PR: JWT & Authentication Hardening (task_1f0f55a17f45)

This PR description explains the **decision** and the **why** behind the
consolidated security/auth hardening work. Full rationale lives in
[`docs/SECURITY.md`](docs/SECURITY.md).

## Why this change

A coherence audit of the `auth` pipeline found several places where the
**session** and authorization assumptions of the backend and frontend
disagreed (client-side-only rate limiting, possible IDOR on profile/password,
verbose permission errors, and backend↔frontend session drift). Each was
resolved by picking the **server as ground truth** and aligning the client.

## Key decisions

- **JWT `none` rejected, key from env.** Blocks signature-bypass/forgery; no
  hardcoded secret. (`config.py`, `utils/security.py`)
- **Auth mandatory.** Protected endpoints return 401 without a valid JWT; tests
  pin `AUTH_DISABLED=False`. The flag remains only as an explicit, loudly-warned
  temporary toggle.
- **Login rate limiting — server is ground truth.** 429 then 423 lockout
  server-side; the frontend counter is UI feedback only.
- **Ownership / permission checks.** Identity from JWT (not request body) → 403
  on mismatch; `pending` users blocked until admin approval.
- **Input validation.** Pydantic constraints reject invalid input with 422.
- **No leakage.** Generic 500s in production + sanitized logs (no password/token).
- **Session sync.** Backend token lifetime + blacklist (`jti`) is ground truth;
  the frontend clears its `localStorage` token on any 401.

## Coherence resolutions (ground truth → align)

| Inconsistency | Ground truth | How the other side was aligned |
| --- | --- | --- |
| Login attempt limit | Backend rate limiter | Frontend counter is UI-only |
| Profile/password ownership | JWT identity | Body `user_id` ignored; 403 on mismatch |
| Permission error verbosity | Backend authorization | Frontend shows generic errors |
| Session lifetime/revocation | Backend JWT + blacklist | Frontend clears token on 401 |

## Verification

`pytest backend/tests` — the auth/security suite passes (JWT, enforcement,
pipeline, RBAC, profile, schema). See the test mapping in `docs/SECURITY.md`.

---

## Follow-up: automated auth tests, customer-form validation & no-leak (task_66febcc9ff9a)

`merged-from: 3b6da420-9914-4d33-aaa8-3d169dc50e69, f7c14bb3-904f-4da1-b5a0-e8691ee049a4, 6ec6ac9a-3418-48bc-a124-46ca50b1a03d`

A consolidated security task covering three findings. All three were already
implemented by the hardening work above; this follow-up **closes the remaining
verification gaps** and documents the decisions the manual-review ACs require.

### 1 — Automated authentication & security tests (was: no coverage)

- **Measurable outcome target (rewritten):** the JWT auth layer is observable in
  production and every credentialed path is exercised by tests. Concretely:
  100% of the auth scenarios called out by the finding — *valid login, wrong
  password, expired token, tampered/invalid signature, `alg:none` forgery,
  revoked (logged-out) token, brute-force lockout* — are covered by passing
  tests, and `utils/security.py` emits a low-cardinality
  `auth.token.verify outcome=<…>` log line plus increments the
  `AUTH_OUTCOMES{outcome}` Prometheus counter so the production
  `success / total` rate is computable.
- Coverage lives in `backend/tests/test_security.py`
  (`test_hash_password`, `test_create_access_token`, `test_verify_token`,
  parametrized, with `jwt.encode`/`jwt.decode`) — **23 tests pass** together
  with the integration pipeline below.
- Metric/log: `_record_auth_outcome()` in `backend/app/utils/security.py`;
  counter defined in `backend/app/monitoring.py` (`AUTH_OUTCOMES`).

### 2 — Customer-form input validation (frontend, first line of defence)

- `frontend/src/app/customers/page.tsx` validates **every** field client-side
  (`validateCustomerForm`): required + length bounds on `account_no`/`name`,
  email + phone format, and `hasUnsafeChars`/`sanitizeInput` to reject `<`/`>`
  (XSS) payloads before they reach the API. Backend Pydantic validation remains
  authoritative (422); this is immediate UX feedback and defence-in-depth.
- **Linter/type-check now clean without suppressions.** Removed the lone
  `eslint-disable react-hooks/exhaustive-deps` on the customers list effect by
  making `loadCustomers` a `useCallback` whose identity tracks
  `page/sortBy/sortOrder`, with the free-text/account-type filters read from a
  ref at fetch time. Behaviour is identical (typing still doesn't auto-reload;
  the filter form applies via `handleSearch`). `tsc --noEmit` and `next lint`
  both pass with **no warnings or errors**, and there are no `@ts-ignore` /
  `@ts-expect-error` / `eslint-disable` in `customers/`.

### 3 — No permission-detail leak in API errors (logic/coherence)

- **Both sides of the inconsistency + their assumptions:**
  *Frontend (`login/page.tsx` + toast handling)* assumed it could surface
  whatever message the API returned. *Backend authorization* assumed callers
  should learn only *that* they are unauthorized, not the role/permission map.
  Verbose permission strings (e.g. "you are not an admin") let an attacker
  enumerate the authorization model and aid brute-force / privilege-escalation.
- **Ground truth = backend authorization.** The server returns a **generic**
  authorization error to the client; the specific reason is recorded only in
  server logs. The frontend was aligned to render that generic message.
- **Regression guard:**
  `backend/tests/integration/test_auth_pipeline.py::test_no_permission_leak_in_errors`
  asserts error bodies expose no role/permission detail. It passes.

### Dependencies synced

- upstream: `utils/security.py` (JWT verify/hash), `monitoring.py` counter,
  `config.py` settings — all already present, no signature changes.
- downstream / cross-tier (backend → frontend): `customers/page.tsx` validation
  + effect refactor; login error rendering already generic.
- side artifacts: this PR description (decisions + measurable target),
  `docs/SECURITY.md` test mapping unchanged.
- Checked — no further upstream / downstream / cross-tier (db, infra) / side
  dependencies were affected by the frontend-only code change.

### Verification (this follow-up)

- `pytest backend/tests/test_security.py backend/tests/integration/test_auth_pipeline.py`
  → **23 passed**.
- `pytest tests/test_frontend_lint.py tests/test_frontend_typecheck.py tests/test_all_existing_features.py`
  → **passed**.
- `cd frontend && npm run type-check && npm run lint` → **no warnings or errors**.
