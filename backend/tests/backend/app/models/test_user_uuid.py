"""Edge-case tests for the resolved ``User.id`` stale-assumption anti-pattern.

Background (``backend/app/models/user.py``): the ``id`` column previously used
an 8-char *truncated* UUID, justified by a "small scale is enough for now"
assumption. That is a textbook *stale assumption* anti-pattern — as the user
base grows, the truncated key space makes birthday-paradox collisions
(``IntegrityError`` on insert) increasingly likely.

The fix widens the id to a full 32-char ``uuid4().hex`` and the column to
``String(36)``. These tests pin the collision-resistance guarantee so a future
regression that re-truncates the id (or otherwise shrinks the key space) fails
loudly.
"""
import uuid

from app.models.user import User, generate_id


def test_uuid_collision_resistance():
    """A large batch of generated ids is collision-free and full-width.

    With the full 122-bit UUID4 space the probability of even a single collision
    in 50k samples is ~1e-28, so we can assert *strict* uniqueness (unlike the
    old 8-char id, whose birthday-paradox odds forced a near-uniqueness
    assertion). This is the behavioural proof that the stale "8 chars is enough"
    assumption has been retired.
    """
    sample = [generate_id() for _ in range(50_000)]

    # Every id must be the full 32 hex chars and fit the String(36) column.
    assert all(len(i) == 32 for i in sample)
    assert all(len(i) <= 36 for i in sample)

    # No collisions across the whole batch.
    assert len(set(sample)) == len(sample)

    # Each id is a valid hex UUID (parseable back into a uuid.UUID).
    for i in sample[:200]:
        assert uuid.UUID(hex=i)


def test_user_id_column_is_widened():
    """The mapped ``users.id`` column is wide enough for a full UUID."""
    col = User.__table__.c.id
    assert col.primary_key is True
    # String(36) holds the 32-char hex id with headroom; reject any re-truncation.
    assert col.type.length is not None and col.type.length >= 32


def test_default_factory_wired():
    """The column default is the single ``generate_id`` factory (full UUID)."""
    default = User.__table__.c.id.default
    assert default is not None
    produced = default.arg(None) if callable(default.arg) else default.arg
    assert isinstance(produced, str) and len(produced) == 32
