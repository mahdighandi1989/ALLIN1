"""Edge-case tests for user id generation (under-engineering anti-pattern)."""
from app.models.user import generate_id


def test_uuid_collision_prevention():
    """Generated ids are unique across a large sample and uniform in length.

    The 8-char truncated UUID gives ~4.3 billion possibilities; this guards
    against an accidental change that would shrink the space or return constant
    values, and documents that the `users.id` UNIQUE constraint is the final
    backstop against a collision.

    NOTE: with an 8-hex-char space a 5k sample has a ~0.3% birthday-paradox
    chance of a single collision, so we assert *near*-uniqueness (the DB UNIQUE
    constraint is the real guarantee) rather than absolute uniqueness, which
    would make this test flaky.
    """
    ids = [generate_id() for _ in range(5000)]
    assert all(len(i) == 8 for i in ids)
    unique = len(set(ids))
    # Effectively all unique — allow an astronomically-rare incidental collision.
    assert unique >= len(ids) - 1


def test_generate_id_is_hex_lowercase():
    for _ in range(100):
        i = generate_id()
        assert len(i) == 8
        assert all(c in "0123456789abcdef" for c in i)
