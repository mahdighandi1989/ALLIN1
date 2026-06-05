"""Dependency-consistency tests.

These guard the bcrypt/passlib version pin that keeps password hashing working.
passlib 1.7.4 is incompatible with bcrypt >= 4.1 (which removed the
``__about__`` module and hard-errors on > 72-byte inputs), so bcrypt must be
pinned to exactly ``4.0.1`` and that pin must be declared identically in every
place dependencies are resolved from (``pyproject.toml`` and
``backend/requirements.txt``). A drift between those files lets CI/Docker
install a divergent, broken version — the failure mode this suite prevents.
"""
import re
from pathlib import Path

import pytest

# backend/tests/test_dependencies.py -> backend/tests -> backend -> repo root
_THIS = Path(__file__).resolve()
_BACKEND_DIR = _THIS.parents[1]
_REPO_ROOT = _THIS.parents[2]

PYPROJECT = _REPO_ROOT / "pyproject.toml"
BACKEND_REQUIREMENTS = _BACKEND_DIR / "requirements.txt"

# The single source of truth for the required pin.
EXPECTED_BCRYPT_VERSION = "4.0.1"


def _read(path: Path) -> str:
    assert path.exists(), f"expected dependency manifest missing: {path}"
    return path.read_text(encoding="utf-8")


def test_pyproject_pins_bcrypt_exactly():
    """pyproject.toml must declare ``bcrypt==4.0.1`` (no open range)."""
    text = _read(PYPROJECT)
    # Match the declared dependency string, e.g.  "bcrypt==4.0.1"
    assert re.search(
        r'["\']bcrypt==' + re.escape(EXPECTED_BCRYPT_VERSION) + r'["\']', text
    ), "pyproject.toml must pin bcrypt to ==%s" % EXPECTED_BCRYPT_VERSION
    # Defensive: the old open range must be gone so the resolver cannot drift.
    assert "bcrypt>=4.0,<4.1" not in text


def test_backend_requirements_pins_bcrypt_exactly():
    """backend/requirements.txt must pin the same bcrypt version."""
    text = _read(BACKEND_REQUIREMENTS)
    assert re.search(
        r'(?m)^\s*bcrypt==' + re.escape(EXPECTED_BCRYPT_VERSION) + r'\s*$', text
    ), "backend/requirements.txt must pin bcrypt to ==%s" % EXPECTED_BCRYPT_VERSION


def test_install_dependencies_no_error():
    """The installed dependency set must import and work without error.

    This is the behavioural proxy for "``pip install -e .`` installs cleanly":
    the security-critical libraries (bcrypt + passlib) must import, agree with
    the declared pin, and successfully hash + verify a password end-to-end. If
    an incompatible bcrypt had been installed, importing passlib's bcrypt
    backend or hashing would raise here.
    """
    # 1) The declared pins must be consistent across manifests.
    assert EXPECTED_BCRYPT_VERSION in _read(PYPROJECT)
    assert EXPECTED_BCRYPT_VERSION in _read(BACKEND_REQUIREMENTS)

    # 2) bcrypt imports and is the pinned, passlib-compatible major.minor (4.0.x).
    try:
        import bcrypt
    except Exception as exc:  # pragma: no cover - import must succeed
        pytest.fail(f"bcrypt failed to import — dependency install is broken: {exc}")

    version = getattr(bcrypt, "__version__", "")
    assert version.startswith("4.0"), (
        f"installed bcrypt {version!r} is incompatible with passlib 1.7.4; "
        f"expected the pinned 4.0.x line"
    )

    # 3) passlib imports and its bcrypt backend hashes + verifies without error.
    try:
        from passlib.context import CryptContext
    except Exception as exc:  # pragma: no cover - import must succeed
        pytest.fail(f"passlib failed to import — dependency install is broken: {exc}")

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("dependency-smoke-test")
    assert hashed.startswith("$2")
    assert pwd_context.verify("dependency-smoke-test", hashed) is True
    assert pwd_context.verify("wrong", hashed) is False
