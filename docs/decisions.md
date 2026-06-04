# Architecture & Security Decision Log

A running log of notable decisions, each with the **why/rationale** and, for
logic-audit ("coherence") items, the **ground truth** chosen and how the other
side was **aligned**. The detailed security rationale is in
[`SECURITY.md`](SECURITY.md); the PR narrative is in
[`../PR_DESCRIPTION.md`](../PR_DESCRIPTION.md).

## ADR-001 — Server is the ground truth for authorization & sessions

**Decision.** For every backend/frontend coherence conflict in the `auth`
pipeline, the **server** is ground truth and the client is aligned to it.

**Why / rationale.**
- **Permission check / authorization:** the backend enforces role/ownership
  (403 on mismatch); the frontend only renders generic UI. A client cannot be
  trusted to enforce access control.
- **Login rate limiting:** enforced server-side (429 → 423 lockout); the client
  counter is UI feedback only.
- **Session lifetime / revocation:** the backend JWT lifetime + `jti` blacklist
  is authoritative; the frontend clears its token on any 401.

**Status:** implemented and covered by `backend/tests` (see `SECURITY.md`).

## ADR-002 — Reject `alg: none`, require an environment-supplied JWT key

**Decision.** `none` is hard-blocked and `SECRET_KEY`/`JWT_SECRET_KEY` must be a
strong env value (hard error in production).

**Why / rationale.** Prevents signature-bypass/token-forgery and brute-force of
a weak key.

## ADR-003 — `AUTH_DISABLED` is a temporary, loudly-warned toggle only

**Decision.** Keep the explicitly-requested "login off for now" toggle but
default tests to `AUTH_DISABLED=False`, warn on startup, and treat
production-on as an error-level log.

**Why / rationale.** Preserves the requested convenience without letting the
bypass become a silent backdoor; restoring auth is a config change only.
