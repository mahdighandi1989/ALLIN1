# Security & Authentication Hardening — Decision Log

This document is the single source of truth for the JWT / authentication
hardening work tracked by the consolidated task **task_1f0f55a17f45**
("تقویت امنیت JWT و مکانیزم‌های احراز هویت" — JWT & auth hardening). It records
the **decision**, the **rationale (why)**, and — for the logic-audit
("coherence") items — which side was chosen as **ground truth** and how the
other side was **aligned** to it.

The behaviours described here are implemented and covered by the backend test
suite (`pytest backend/tests`). Each section names the files that satisfy the
acceptance criteria so a reviewer can map AC → code.

---

## 1. JWT: reject `none`, enforce a key from the environment

**Decision.** The `none` algorithm is hard-blocked and the signing key is read
exclusively from the environment.

**Why.** An attacker who can get a server to accept an `alg: none` token can
forge an admin token with no signature (the CVE-2022-23529 class of
signature-bypass). A hardcoded/weak key is brute-forceable.

**Implementation.**
- `backend/app/config.py` — `SECRET_KEY` is read from `SECRET_KEY` (alias
  `JWT_SECRET_KEY`), `min_length=32`; a `validator` rejects weak/placeholder
  values and hard-fails in production. `ALGORITHM` validator rejects `none`/empty
  and restricts to a safe allowlist.
- `backend/app/utils/security.py` — `verify_access_token()` inspects the
  unverified header and rejects `none`/out-of-allowlist algorithms *before*
  decoding (defence in depth), then decodes with an explicit `algorithms`
  allowlist that never contains `none`.

## 2. Remove the auth bypass for protected endpoints

**Decision.** Authentication is mandatory for data endpoints. Without a valid
JWT, `/api/customers` (and peers) return **401**.

**Why.** A permanent bypass is a backdoor. Tests pin `AUTH_DISABLED=False`
(`backend/tests/conftest.py`) so the real auth path is always exercised.

**Note on `AUTH_DISABLED`.** The flag still exists as an explicitly-requested,
loudly-warned *temporary* convenience toggle ("remove login for now"). It is
documented in `backend/app/config.py` and surfaced by
`enforce_security_on_startup()`, which logs an `error` when it is on in
production. Restoring mandatory login is a config change only
(`AUTH_DISABLED=false`) — no rebuild.

## 3. Authentication error-path tests

**Decision.** `tests/test_auth.py` covers expired tokens, invalid signatures,
`none`-algorithm tokens, malformed tokens, and rate limiting.

**Why.** The critical failure modes of an auth system are its *rejections*;
those must be regression-protected.

## 4. Login rate limiting — server-side is ground truth

**Coherence issue.** The frontend kept a client-side login-attempt counter; the
backend had none. A client counter is trivially bypassed.

**Ground truth & align.** The **server** is ground truth. A server-side limiter
(`backend/app/utils/rate_limit.py`, wired in `backend/app/routers/auth.py`)
returns **429** after too many failures per minute and **423** once the lockout
threshold is reached. The frontend counter
(`frontend/src/app/login/page.tsx`) is retained **only as UI feedback** and the
real enforcement is the server's response code.

## 5. Permission / authorization checks in the auth pipeline

**Decision.** A signed-in user with no granted role (`pending`) is blocked from
data endpoints (**403**) until an admin approves them; admin-only routes check
`is_admin`/`role`.

**Why.** Authentication ≠ authorization. The **permission check** lives in
`get_current_user` (`backend/app/utils/security.py`) and the RBAC tests
(`backend/tests/test_rbac.py`, `backend/tests/test_auth_pipeline.py`) lock it in.

## 6. Ownership checks — fixing the IDOR (server is ground truth)

**Coherence issue.** Profile-update / password-change endpoints could, in
principle, act on an arbitrary `user_id` from the request body (IDOR).

**Ground truth & align.** The identity is taken from the **JWT**, not the
request body; a mismatch yields **403**. Verified by
`backend/tests/integration/test_auth_pipeline.py::test_profile_update_and_password_change_secure`.

## 7. Pydantic input validation

**Decision.** Request models constrain length, apply regex/`SafeText` patterns
for sensitive fields, and bound numeric ranges, so invalid input is rejected
with **422** before it reaches the database.

**Why.** Defends against corrupt data and stored-XSS via text fields.
Implementation: `backend/app/schemas/validators.py`,
`backend/app/schemas/facility.py`, `backend/app/schemas/__init__.py`.

## 8. Brute-force protection + optional Redis accounting

**Decision.** The login limiter is authoritative in-memory; when `REDIS_URL` is
set, attempts are additionally recorded in **Redis** for cross-process
accounting/auditing (best-effort, never required for correctness). See
`backend/app/routers/auth.py`.

## 9. No sensitive-data leakage in logs or errors

**Decision.** A catch-all `Exception` handler returns a **generic** 500 message
in production (`backend/app/main.py`,
`unhandled_exception_handler_500`, registered via
`app.add_exception_handler(Exception, ...)`). Logs are routed through
`backend/app/utils/log_sanitizer.py` so passwords/tokens are never written.

## 10. Conditional-inconsistency anti-pattern (issuer/audience)

**Decision.** The `if payload.get('iss')` / `if payload.get('aud')` guards in
`verify_access_token` are **intentional and documented**: issuer/audience are
validated whenever present, preserving backward-compatibility with legacy
tokens minted before those claims existed. New tokens always include both, so
validation is unconditional in practice. Covered by
`tests/test_security.py::test_verify_access_token_edge_cases`.

## 11. No permission/identity leakage in the frontend

**Coherence issue.** Verbose auth errors and a dev `AUTH_DISABLED` mode could
leak role/permission structure.

**Ground truth & align.** The **server** owns authorization; the client shows
**generic** errors only ("Invalid username or password", "Too many requests")
— `frontend/src/app/login/page.tsx`. `frontend/src/lib/auth.tsx` logs only
generic messages and never prints tokens/roles.

## 12. Backend ⇄ frontend session synchronisation

**Coherence issue.** The backend session (`AsyncSession`, JWT lifetime, token
revocation) and the frontend session (`localStorage` token) could drift.

**Ground truth & align.** The **backend** token lifetime + blacklist
(`backend/app/utils/token_blacklist.py`) is ground truth. The frontend clears
its stored token whenever the backend rejects it (401), so logout/expiry/revoke
on the server immediately ends the client session.

## 13. Login input validation (both sides)

**Decision.** The frontend constrains the login fields (e.g. `maxLength`) for UX
and the backend validates the login payload with Pydantic — server validation is
authoritative. Covered by `backend/tests/test_auth.py`.

## 14. HTTPS / HSTS / CORS

**Decision.** `should_force_https()` (`backend/app/config.py`) redirects HTTP→
HTTPS and emits HSTS (enabled by default in production); CORS origins are an
explicit allowlist with localhost filtered out in production.

## 15. Refresh + token blacklist

**Decision.** Access tokens carry a unique `jti`; logout/revoke adds the `jti`
to `token_blacklist`, and `verify_access_token` rejects revoked tokens until
they naturally expire. A refresh endpoint issues new access tokens. See
`backend/app/routers/auth.py`, `backend/app/utils/token_blacklist.py`.

## 16. Database error handling in the auth pipeline

**Decision.** Auth DB operations roll back and surface generic errors on failure
rather than leaking driver internals, keeping the pipeline robust to schema
drift (see `_get_or_create_demo_user`’s defensive fallback).

---

### Test mapping (high level)

| Area | Tests |
| --- | --- |
| JWT / token lifecycle | `tests/test_auth.py`, `tests/test_security.py` |
| Auth enforcement / bypass off | `tests/test_auth_enforcement.py`, `tests/test_auth_disabled.py` |
| Pipeline (rate-limit, ownership, permission) | `tests/test_auth_pipeline.py`, `tests/integration/test_auth_pipeline.py` |
| RBAC | `tests/test_rbac.py` |
| Profile / password ownership | `tests/test_profile.py` |
| Schema validation | `tests/test_schemas.py` |
