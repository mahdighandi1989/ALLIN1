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
