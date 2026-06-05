"""Facility authorization service.

Authentication (``app.utils.security.get_current_user``) proves *who* the caller
is. This service answers the separate question of *what* an authenticated user is
allowed to do with facility data, so the policy lives in one reusable place
instead of being implied by whichever dependency a route happens to declare.

----------------------------------------------------------------------------
Ground-truth decision (recorded for the logic-audit task that created this file)
----------------------------------------------------------------------------
The coherence audit flagged that ``app/routers/facilities.py`` requires
*authentication* but appeared to have no explicit *authorization* controlling
which facilities an authenticated user may view.

Resolving the inconsistency required deciding which side is the ground truth:

* Side A — the router: every facility endpoint sits behind ``get_current_user``;
  read endpoints carry no extra authorization, write endpoints add
  ``require_editor``.
* Side B — the audit's suggestion: per-customer / per-organisation scoping so a
  user only sees "their" facilities.

**Ground truth is the application's role-based access model (Side A is correct,
Side B is not yet supported by the data model).** The ``User`` model
(``app/models/user.py``) has *no* organisation / customer association — a user is
not "owned" by a customer — so per-customer row filtering is not expressible
today and inventing it would contradict the real schema. What the application
*does* model is a global role hierarchy:

    pending < viewer < editor < admin   (see ROLE_RANK in app/models/user.py)

The genuine gap the audit detected is that this authorization rule was only
*implicitly* enforced for reads (``get_current_user`` happens to 403 a
``pending`` user). This service makes the rule **explicit and centralised**:

* Reading facility data requires an *approved* account — ``viewer`` or above.
* Mutating facility data requires ``editor`` or above (unchanged; the write
  endpoints keep ``require_editor``).
* A ``pending`` (signed-in but not-yet-approved) account is authenticated but
  **not** authorized and must receive ``403 Forbidden`` — never facility data.

The service is intentionally decoupled from FastAPI routing details (it works on
a plain user object) so it can be reused by exports, background jobs, or a future
per-customer scoping layer. When/if users gain a customer/organisation
association, ``can_read_facility`` already accepts the target facility so
row-level scoping can be added here without touching the router.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from fastapi import Depends, HTTPException, status

from app.models.user import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_PENDING,
    ROLE_RANK,
    ROLE_VIEWER,
)
from app.utils.security import get_current_user

if TYPE_CHECKING:  # avoid heavy/circular imports at runtime
    from app.models.facility import Facility
    from app.models.user import User

# Stable, user-facing messages (kept as constants so tests and clients can rely
# on them and so they are not duplicated across call sites).
FORBIDDEN_READ = "You are not authorized to view facility data."
FORBIDDEN_WRITE = "Editor or admin privileges are required to modify facilities."

# Minimum role rank required for each kind of access.
_READ_MIN_RANK = ROLE_RANK[ROLE_VIEWER]
_WRITE_MIN_RANK = ROLE_RANK[ROLE_EDITOR]


def _role_rank(user: "User") -> int:
    """Effective role rank for ``user``.

    ``is_admin`` is treated as the top of the hierarchy regardless of the
    free-text ``role`` column — this mirrors ``_role_at_least`` in
    ``app/routers/auth.py`` and keeps the AUTH_DISABLED demo user (an admin)
    fully authorized.
    """
    if getattr(user, "is_admin", False):
        return ROLE_RANK[ROLE_ADMIN]
    role = getattr(user, "role", ROLE_PENDING) or ROLE_PENDING
    return ROLE_RANK.get(role, 0)


def can_read_facilities(user: "User") -> bool:
    """True if ``user`` is approved to read facility data (viewer or above)."""
    return _role_rank(user) >= _READ_MIN_RANK


def can_write_facilities(user: "User") -> bool:
    """True if ``user`` may create/update/delete facilities (editor or above)."""
    return _role_rank(user) >= _WRITE_MIN_RANK


def can_read_facility(user: "User", facility: "Optional[Facility]" = None) -> bool:
    """True if ``user`` may read a *specific* facility.

    Today this is governed purely by role (``facility`` is unused), because the
    user model has no per-customer association. The ``facility`` parameter is part
    of the contract so future per-customer/per-tenant scoping can be added here —
    and enforced everywhere the service is used — without changing call sites.
    """
    return can_read_facilities(user)


def authorize_facility_read(
    user: "User", facility: "Optional[Facility]" = None
) -> None:
    """Raise ``403`` unless ``user`` may read facility data."""
    if not can_read_facility(user, facility):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_READ
        )


def authorize_facility_write(user: "User") -> None:
    """Raise ``403`` unless ``user`` may modify facility data."""
    if not can_write_facilities(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_WRITE
        )


async def require_facility_reader(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """FastAPI dependency: authenticate, then authorize facility *read* access.

    Used as the facilities router's gate. ``get_current_user`` resolves identity
    (and already rejects unauthenticated / pending-non-admin callers); this layer
    makes the authorization decision explicit and centralised so every facility
    endpoint enforces the same policy.
    """
    authorize_facility_read(current_user)
    return current_user
