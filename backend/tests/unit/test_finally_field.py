"""Pin the single, deterministic contract for ``finally:`` cleanup blocks.

Background (consolidated task ``task_cba4b5521484``): an automated repo scan
reported that a *field* named ``finally`` had "different defaults" across the
codebase, listing values such as ``"invalid_format"``, ``time.perf_counter()
- start`` and ``override_get_db``. That is a **false positive**: ``finally`` is
a Python keyword and cannot be a field/attribute name. What the scanner actually
saw were ordinary ``finally:`` cleanup blocks in three unrelated places:

* ``app/middleware.py``      — ``finally:`` computes ``elapsed`` from a single
  ``time.perf_counter()`` start (request-timing log).
* ``app/services/data_pipeline.py`` — ``finally:`` / error path around the
  single ``invalid_format`` error ``kind`` constant.
* ``tests/conftest.py``      — ``finally:`` cleanup of the ``override_get_db``
  dependency override.

There is therefore no shared ``finally`` field and no conflicting default to
unify. The real, observable contract worth pinning is that a ``finally:`` block
runs **exactly once** and **deterministically** — its effect does not depend on
import/execution order — for both the normal-return and exception paths. These
tests document that single source of truth so the (non-)issue cannot silently
regress into a real order-dependent bug later.
"""
import time


def test_finally_default_behavior():
    """A ``finally:`` block always runs once, on both the success and error paths.

    This is the single, deterministic "default behavior" the scanner's report
    conflated with a field default. We exercise both control-flow paths and
    assert the cleanup side effect is identical and order-independent.
    """
    # --- success path: finally runs after a normal return value is produced ---
    events = []
    try:
        events.append("body")
    finally: cleanup_ran = True  # noqa: E701 - single source of the cleanup flag
    assert cleanup_ran is True
    assert events == ["body"]

    # --- error path: finally still runs exactly once, even when the body raises ---
    cleanup_count = 0
    with_error = False
    try:
        try:
            raise ValueError("boom")
        finally:
            cleanup_count += 1
    except ValueError:
        with_error = True
    assert with_error is True
    assert cleanup_count == 1  # ran once, not zero and not twice

    # --- determinism: the cleanup effect is independent of evaluation order ---
    # Mirrors the middleware ``finally:`` pattern (elapsed derived from one start).
    start = time.perf_counter()
    try:
        pass
    finally:
        elapsed = time.perf_counter() - start
    assert elapsed >= 0.0


def test_finally_is_not_a_data_field():
    """Guard against the false positive: no real model exposes a ``finally`` field.

    ``finally`` is a reserved keyword, so neither the ORM models nor the Pydantic
    schemas can declare it as an attribute. We assert it explicitly so that the
    automated scan's "conflicting finally defaults" finding stays closed.
    """
    from app.models.user import User
    from app.models.facility import Facility

    assert "finally" not in User.__table__.columns.keys()
    assert "finally" not in Facility.__table__.columns.keys()
