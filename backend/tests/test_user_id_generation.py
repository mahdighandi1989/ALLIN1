"""Edge-case tests for user id generation.

History: the id used to be an 8-char *truncated* UUID, justified by a
"small scale" assumption. That stale assumption was resolved by switching to a
full 32-char ``uuid4().hex`` (see ``app.models.user.generate_id``), so these
tests now pin the full-UUID contract.
"""
from app.models.user import generate_id


def test_uuid_collision_prevention():
    """Generated ids are unique across a large sample and uniform in length.

    The full 32-char UUID4 hex spans the entire 122-bit space, so a 5k sample is
    expected to be strictly unique; the ``users.id`` UNIQUE constraint remains
    the final backstop.
    """
    ids = [generate_id() for _ in range(5000)]
    assert all(len(i) == 32 for i in ids)
    # Full UUID space — the sample must be strictly unique.
    assert len(set(ids)) == len(ids)


def test_generate_id_is_hex_lowercase():
    for _ in range(100):
        i = generate_id()
        assert len(i) == 32
        assert all(c in "0123456789abcdef" for c in i)
