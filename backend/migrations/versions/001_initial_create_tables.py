"""create initial tables

Revision ID: 001_initial
Revises:
Create Date: 2026-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(8), primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True)),
    )

    # Customers table
    op.create_table(
        'customers',
        sa.Column('id', sa.String(33), primary_key=True),
        sa.Column('account_no', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('name_ar', sa.String(200)),
        sa.Column('account_type', sa.Enum('retail', 'corporate', 'sme', name='accounttype'), default='retail'),
        sa.Column('status', sa.Enum('active', 'inactive', 'suspended', name='customerstatus'), default='active'),
        sa.Column('email', sa.String(100)),
        sa.Column('phone', sa.String(50)),
        sa.Column('mobile', sa.String(50)),
        sa.Column('address', sa.Text()),
        sa.Column('branch', sa.String(100)),
        sa.Column('relationship_manager', sa.String(100)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )

    # Facilities table
    op.create_table(
        'facilities',
        sa.Column('id', sa.String(8), primary_key=True),
        sa.Column('customer_id', sa.String(33), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('facility_type', sa.Enum('loan', 'overdraft', 'lc', 'lg', 'other', name='facilitytype'), nullable=False),
        sa.Column('name', sa.String(200)),
        sa.Column('status', sa.Enum('active', 'pending', 'closed', 'defaulted', name='facilitystatus'), default='active'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('outstanding', sa.Numeric(18, 2), default=0),
        sa.Column('currency', sa.String(10), default='AED'),
        sa.Column('start_date', sa.Date()),
        sa.Column('expiry_date', sa.Date()),
        sa.Column('interest_rate', sa.Numeric(5, 2)),
        sa.Column('tenor_months', sa.String(20)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )


def downgrade() -> None:
    op.drop_table('facilities')
    op.drop_table('customers')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS facilitytype")
    op.execute("DROP TYPE IF EXISTS facilitystatus")
    op.execute("DROP TYPE IF EXISTS accounttype")
    op.execute("DROP TYPE IF EXISTS customerstatus")
