"""widen users.id from truncated 8-char to full 32-char UUID

Revision ID: 003_widen_user_id
Revises: 002_add_columns
Create Date: 2026-06-05

Resolves the stale-assumption anti-pattern in ``app/models/user.py``: the
``users.id`` column used to be ``String(8)`` (an 8-char *truncated* UUID),
justified by a "small scale" assumption that grows unsafe as the user base
expands (birthday-paradox collisions -> IntegrityError on insert).

This migration widens the column to ``VARCHAR(36)`` so it can hold the full
32-char ``uuid4().hex`` produced by ``app.models.user.generate_id``. Widening is
backward compatible: existing 8-char ids remain valid values in the wider
column. PostgreSQL ``ALTER COLUMN ... TYPE VARCHAR(36)`` is a metadata-only
change for a widen and does not rewrite the table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003_widen_user_id'
down_revision: Union[str, None] = '002_add_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' not in inspector.get_table_names():
        return

    id_col = next((c for c in inspector.get_columns('users') if c['name'] == 'id'), None)
    if id_col is None:
        return

    # Only widen on backends that carry a meaningful VARCHAR length and where the
    # current width is narrower than a full UUID. SQLite ignores VARCHAR lengths
    # entirely, so this is effectively a Postgres-only operation.
    current_len = getattr(id_col['type'], 'length', None)
    if conn.dialect.name == 'postgresql' and (current_len is None or current_len < 36):
        op.alter_column(
            'users',
            'id',
            existing_type=sa.String(length=current_len or 8),
            type_=sa.String(length=36),
            existing_nullable=False,
        )


def downgrade() -> None:
    # Not safely reversible: narrowing back to VARCHAR(8) would truncate any
    # full-length ids written after the upgrade. Intentionally a no-op.
    pass
