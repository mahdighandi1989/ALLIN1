"""Edge cases for the DB SSL decision (stale-assumption anti-pattern).

The old code substring-matched ``'localhost' not in url`` to decide whether to
attach SSL, which mis-classified hosts like ``localhost.example.com``. These
tests pin the host-parsing behaviour and the documented CERT_NONE default.
"""
import ssl

from app.database import _should_use_ssl, _build_connect_args


def test_local_and_sqlite_urls_need_no_ssl():
    assert _should_use_ssl("sqlite+aiosqlite:///:memory:") is False
    assert _should_use_ssl("postgresql+asyncpg://u:p@127.0.0.1:5432/db") is False
    assert _should_use_ssl("postgresql+asyncpg://u:p@localhost/db") is False
    assert _should_use_ssl("postgresql+asyncpg://u:p@[::1]:5432/db") is False


def test_remote_hosts_use_ssl():
    assert _should_use_ssl("postgresql+asyncpg://u:p@db.frankfurt.render.com:5432/db") is True
    # The substring trap the old check fell into: this is a *remote* host.
    assert _should_use_ssl("postgresql+asyncpg://u:p@localhost.example.com/db") is True


def test_connect_args_default_disables_verification():
    args = _build_connect_args("postgresql+asyncpg://u:p@db.render.com/db")
    assert "ssl" in args
    assert args["ssl"].verify_mode == ssl.CERT_NONE


def test_connect_args_can_require_verification(monkeypatch):
    monkeypatch.setenv("DB_SSL_VERIFY", "true")
    args = _build_connect_args("postgresql+asyncpg://u:p@db.render.com/db")
    assert args["ssl"].verify_mode == ssl.CERT_REQUIRED


def test_local_connect_args_empty():
    assert _build_connect_args("postgresql+asyncpg://u:p@localhost/db") == {}


def test_ssl_edge_cases(monkeypatch):
    """Aggregate edge-case guard for the stale-assumption SSL anti-pattern.

    The old code decided SSL with ``'localhost' not in url`` (a substring match),
    which broke on several edge cases. This single node exercises all of them so
    the consolidated task's ``test_node`` resolves to a behaviour contract:

    * sqlite / unix-socket / loopback / IPv6-loopback → no SSL,
    * the ``localhost.example.com`` substring trap → correctly treated remote,
    * a Docker service short-host (``db``) → remote (not silently local),
    * default remote connect args disable verification (documented Render
      behaviour), and ``DB_SSL_VERIFY`` opts back into full verification.
    """
    # --- hosts that must NEVER attach SSL -------------------------------------
    for url in (
        "sqlite+aiosqlite:///:memory:",
        "sqlite:///./local.db",
        "postgresql+asyncpg://u:p@localhost/db",
        "postgresql+asyncpg://u:p@127.0.0.1:5432/db",
        "postgresql+asyncpg://u:p@[::1]:5432/db",
    ):
        assert _should_use_ssl(url) is False, url
        assert _build_connect_args(url) == {}, url

    # --- hosts that MUST attach SSL (the substring traps) ---------------------
    for url in (
        "postgresql+asyncpg://u:p@db.frankfurt.render.com:5432/db",
        "postgresql+asyncpg://u:p@localhost.example.com/db",  # remote despite 'localhost' substring
        "postgresql+asyncpg://u:p@127.0.0.1.evil.com/db",      # remote despite '127.0.0.1' substring
        "postgresql+asyncpg://u:p@db/app",                      # Docker service short-host → remote
    ):
        assert _should_use_ssl(url) is True, url

    # --- default remote connect args: TLS on, verification off ----------------
    monkeypatch.delenv("DB_SSL_VERIFY", raising=False)
    args = _build_connect_args("postgresql+asyncpg://u:p@db.render.com/db")
    assert "ssl" in args
    assert args["ssl"].verify_mode == ssl.CERT_NONE
    assert args["ssl"].check_hostname is False

    # --- DB_SSL_VERIFY opts into full verification, case/format insensitive ----
    for truthy in ("true", "1", "YES", "On"):
        monkeypatch.setenv("DB_SSL_VERIFY", truthy)
        args = _build_connect_args("postgresql+asyncpg://u:p@db.render.com/db")
        assert args["ssl"].verify_mode == ssl.CERT_REQUIRED, truthy
        assert args["ssl"].check_hostname is True, truthy

    # --- a non-truthy value keeps the relaxed default -------------------------
    monkeypatch.setenv("DB_SSL_VERIFY", "false")
    args = _build_connect_args("postgresql+asyncpg://u:p@db.render.com/db")
    assert args["ssl"].verify_mode == ssl.CERT_NONE
