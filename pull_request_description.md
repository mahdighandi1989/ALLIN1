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
