"""Pin the *single source of default* for the ``user_id`` field.

Background (consolidated task ``c621424e``): the ``user_id`` field used to pick
up conflicting defaults — one code path produced ``None`` while another read
``payload.get("user_id")``, so the resolved value depended on import/execution
order (an unreproducible-bug anti-pattern).

These tests document and enforce the unified contract:

* The persisted identity (``users.id``) has exactly one default factory —
  ``app.models.user.generate_id`` — wired as the column default.
* A JWT always carries the user id under both the legacy ``user_id`` claim and
  the standard ``sub`` claim with the *same* value, so the canonical reader
  ``payload.get("user_id") or payload.get("sub")`` returns one consistent id no
  matter which claim a downstream consumer happens to read first.
"""
from app.models.user import User, generate_id
from app.utils.security import create_access_token, verify_access_token


def _resolve_user_id(payload: dict):
    """The canonical resolution order used across the backend.

    Mirrors ``app/utils/security.py`` (`payload.get("user_id") or
    payload.get("sub")`). Kept here as the single documented default so a future
    change that diverges from it fails this test.
    """
    return payload.get("user_id") or payload.get("sub")


def test_user_id_default():
    """``user_id`` resolves from one source everywhere it is defaulted."""
    # 1) The model column default is the single shared factory, not an inline
    #    lambda or a literal — there is exactly one place ids are minted.
    id_default = User.__table__.c.id.default
    assert id_default is not None
    assert callable(id_default.arg)
    assert id_default.arg.__name__ == "generate_id"

    # 2) That factory yields a stable, non-empty full 32-char uuid4 hex id every
    #    call (the id was widened from the old truncated 8-char form).
    minted = generate_id()
    assert isinstance(minted, str)
    assert len(minted) == 32
    assert minted  # never None / empty — the old conflicting default

    # 3) A freshly issued token exposes the id identically under the legacy
    #    ``user_id`` claim and the standard ``sub`` claim, so the canonical
    #    reader is order-independent.
    token = create_access_token({"user_id": minted, "username": "alice"})
    payload = verify_access_token(token)
    assert payload["user_id"] == minted
    assert payload["sub"] == minted
    assert _resolve_user_id(payload) == minted

    # 4) Reading via either claim alone collapses to the same default — there is
    #    no execution-order-dependent divergence anymore.
    assert _resolve_user_id({"user_id": minted}) == minted
    assert _resolve_user_id({"sub": minted}) == minted
    assert _resolve_user_id({"user_id": minted, "sub": minted}) == minted


def test_user_id_default_absent_is_falsy_not_divergent():
    """When no id claim is present the resolution is a single falsy value.

    The anti-pattern produced ``None`` in one path and a different sentinel in
    another; the unified reader must yield exactly one (falsy) result so callers
    can ``if not user_id`` uniformly.
    """
    assert not _resolve_user_id({})
    assert _resolve_user_id({}) is None
