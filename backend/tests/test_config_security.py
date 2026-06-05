"""Security-focused tests for application configuration defaults.

Covers the under-engineering anti-pattern where the default ``DATABASE_URL``
ships with placeholder ``user:password`` credentials: that default is acceptable
for local development but must never be silently used in production. Also guards
the SECRET_KEY production hardening so weak/placeholder keys cannot be deployed.
"""
import pytest

from app.config import Settings, validate_environment_security

# A strong, non-placeholder secret so constructing a production ``Settings`` does
# not trip the (separate) SECRET_KEY production guard while we exercise the
# DATABASE_URL behaviour.
STRONG_SECRET = "x" * 48


def _settings(**overrides) -> Settings:
    """Build a Settings instance with a strong SECRET_KEY plus overrides.

    Init kwargs have the highest priority in pydantic-settings, so this is
    deterministic regardless of any ambient environment variables or .env file.
    """
    base = {"SECRET_KEY": STRONG_SECRET}
    base.update(overrides)
    return Settings(**base)


def test_production_config_defaults():
    """In production the insecure placeholder DATABASE_URL must be flagged.

    The default DATABASE_URL uses generic ``user:password`` credentials intended
    only for local development. Shipping it to production unchanged is a security
    risk, so ``validate_environment_security`` must surface a warning about it —
    while a real, overridden credential set must produce no such warning, and a
    development environment must not be warned at all.
    """
    # 1) Development with the default placeholder URL is fine — no DB warning.
    dev = _settings(ENVIRONMENT="development")
    dev_warnings = validate_environment_security(dev)
    assert not any("DATABASE_URL" in w for w in dev_warnings), dev_warnings

    # 2) Production still using the insecure placeholder credentials -> warned.
    prod_default = _settings(ENVIRONMENT="production")
    prod_warnings = validate_environment_security(prod_default)
    assert any(
        "DATABASE_URL" in w and "user:password" in w for w in prod_warnings
    ), f"expected an insecure-DATABASE_URL warning, got: {prod_warnings}"

    # 3) Production with a real overridden DATABASE_URL -> no DB warning.
    prod_ok = _settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+asyncpg://realuser:s3cr3t-pw@db.internal:5432/allin1",
    )
    ok_warnings = validate_environment_security(prod_ok)
    assert not any("DATABASE_URL" in w for w in ok_warnings), ok_warnings


# A weak placeholder that is long enough to pass the Field ``min_length`` check
# but is still rejected by the SECRET_KEY validator's weak-value blocklist.
WEAK_PLACEHOLDER = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_BASE64_32"


def test_production_requires_strong_secret_key():
    """A weak/placeholder SECRET_KEY is a hard error in production."""
    with pytest.raises(Exception):
        Settings(ENVIRONMENT="production", SECRET_KEY=WEAK_PLACEHOLDER)


def test_development_tolerates_default_secret_key():
    """Development generates a secure ephemeral key instead of failing."""
    s = Settings(ENVIRONMENT="development", SECRET_KEY=WEAK_PLACEHOLDER)
    # The weak placeholder is replaced by a strong generated value (>= 32 chars).
    assert s.SECRET_KEY != WEAK_PLACEHOLDER
    assert len(s.SECRET_KEY) >= 32
