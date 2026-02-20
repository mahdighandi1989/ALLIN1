"""add missing columns to existing tables

Revision ID: 002_add_columns
Revises: 001_initial
Create Date: 2026-02-20

Handles the case where tables were created by an older version of the code
and are missing columns that the current models expect.
Uses ADD COLUMN IF NOT EXISTS (PostgreSQL 9.6+) for safety.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_add_columns'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to facilities table
    # Using raw SQL with IF NOT EXISTS for idempotent execution
    columns_to_add = [
        ("facilities", "amount", "NUMERIC(15,2) NOT NULL DEFAULT 0"),
        ("facilities", "outstanding", "NUMERIC(15,2) DEFAULT 0"),
        ("facilities", "currency", "VARCHAR(10) DEFAULT 'AED'"),
        ("facilities", "facility_type", "VARCHAR(20)"),
        ("facilities", "name", "VARCHAR(200)"),
        ("facilities", "status", "VARCHAR(20) DEFAULT 'active'"),
        ("facilities", "start_date", "DATE"),
        ("facilities", "expiry_date", "DATE"),
        ("facilities", "end_date", "DATE"),
        ("facilities", "interest_rate", "NUMERIC(5,2)"),
        ("facilities", "tenor_months", "VARCHAR(20)"),
        ("facilities", "notes", "VARCHAR(1000)"),
        ("facilities", "customer_id", "VARCHAR"),
        ("facilities", "created_at", "TIMESTAMP NOT NULL DEFAULT now()"),
        ("facilities", "updated_at", "TIMESTAMP"),
        ("facilities", "is_deleted", "BOOLEAN DEFAULT false"),
        # Add missing columns to customers table
        ("customers", "account_no", "VARCHAR(50)"),
        ("customers", "name", "VARCHAR(200)"),
        ("customers", "name_ar", "VARCHAR(200)"),
        ("customers", "account_type", "VARCHAR(20) DEFAULT 'retail'"),
        ("customers", "status", "VARCHAR(20) DEFAULT 'active'"),
        ("customers", "email", "VARCHAR(100)"),
        ("customers", "phone", "VARCHAR(50)"),
        ("customers", "mobile", "VARCHAR(50)"),
        ("customers", "address", "TEXT"),
        ("customers", "branch", "VARCHAR(100)"),
        ("customers", "relationship_manager", "VARCHAR(100)"),
        ("customers", "notes", "TEXT"),
        ("customers", "created_at", "TIMESTAMP WITH TIME ZONE DEFAULT now()"),
        ("customers", "updated_at", "TIMESTAMP WITH TIME ZONE"),
        ("customers", "is_deleted", "BOOLEAN DEFAULT false"),
        # Add missing columns to users table
        ("users", "username", "VARCHAR(50)"),
        ("users", "email", "VARCHAR(100)"),
        ("users", "hashed_password", "VARCHAR(255)"),
        ("users", "full_name", "VARCHAR(100)"),
        ("users", "is_active", "BOOLEAN DEFAULT true"),
        ("users", "is_admin", "BOOLEAN DEFAULT false"),
        ("users", "created_at", "TIMESTAMP WITH TIME ZONE DEFAULT now()"),
        ("users", "last_login", "TIMESTAMP WITH TIME ZONE"),
    ]

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    for table, column, col_type in columns_to_add:
        if table in existing_tables:
            existing_columns = [c['name'] for c in inspector.get_columns(table)]
            if column not in existing_columns:
                op.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')


def downgrade() -> None:
    # Not reversible - columns added to existing tables
    pass