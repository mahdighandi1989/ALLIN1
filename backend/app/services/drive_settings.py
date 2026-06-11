"""Resolve + persist the OAuth refresh token used for Google Drive sync.

In OAuth mode the sync runs as a real Google user. The refresh token is stored
server-side (so the background scheduler and the Telegram bot can sync without a
live web session), with this lookup order:

  1. the ``google_drive_refresh_token`` row in ``system_settings`` — set by the
     one-time "Connect Google Drive" flow (the authoritative, explicit choice);
  2. otherwise the newest admin user's ``google_refresh_token`` captured when they
     signed in with Google (a zero-setup fallback).

Storing it in ``system_settings`` means connecting Drive needs no redeploy and no
secret pasted into the environment.
"""
from __future__ import annotations

import logging

import sqlalchemy as sa

from app.database import AsyncSessionLocal
from app.models.system_setting import SystemSetting
from app.models.user import User, ROLE_ADMIN

logger = logging.getLogger(__name__)

REFRESH_TOKEN_KEY = "google_drive_refresh_token"
# Records which account connected, for display on the status panel.
ACCOUNT_KEY = "google_drive_account_email"


async def get_setting(key: str) -> str | None:
    async with AsyncSessionLocal() as session:
        row = (
            await session.execute(select_setting(key))
        ).scalar_one_or_none()
        return row.value if row and row.value else None


def select_setting(key: str):
    return sa.select(SystemSetting).where(SystemSetting.key == key)


async def set_setting(key: str, value: str) -> None:
    async with AsyncSessionLocal() as session:
        row = (await session.execute(select_setting(key))).scalar_one_or_none()
        if row:
            row.value = value
        else:
            session.add(SystemSetting(key=key, value=value))
        await session.commit()


async def clear_setting(key: str) -> None:
    async with AsyncSessionLocal() as session:
        row = (await session.execute(select_setting(key))).scalar_one_or_none()
        if row:
            await session.delete(row)
            await session.commit()


async def resolve_refresh_token() -> str | None:
    """Return the refresh token to use for Drive sync, or None if not connected."""
    explicit = await get_setting(REFRESH_TOKEN_KEY)
    if explicit:
        return explicit
    # Fallback: an admin who signed in with Google already granted drive.file.
    async with AsyncSessionLocal() as session:
        admin = (
            await session.execute(
                sa.select(User)
                .where(User.role == ROLE_ADMIN, User.google_refresh_token.isnot(None))
                .order_by(User.last_login.desc().nullslast())
                .limit(1)
            )
        ).scalar_one_or_none()
        if admin and admin.google_refresh_token:
            return admin.google_refresh_token
    return None


async def store_connection(refresh_token: str, account_email: str | None) -> None:
    """Persist a freshly obtained refresh token (+ the connecting account email)."""
    await set_setting(REFRESH_TOKEN_KEY, refresh_token)
    if account_email:
        await set_setting(ACCOUNT_KEY, account_email)


async def connected_account() -> str | None:
    return await get_setting(ACCOUNT_KEY)
