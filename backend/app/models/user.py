"""User Model"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from app.database import Base


def generate_id():
    # NOTE: 8-char UUID is sufficient for current scale (the `users` table holds
    # a small set of operator accounts). The id column is UNIQUE, so the database
    # rejects the astronomically-unlikely truncated-UUID collision rather than
    # silently overwriting — see tests/test_user_id_generation.py. If the user
    # base ever grows by orders of magnitude, switch to uuid.uuid4().hex (32 chars)
    # and widen the column accordingly.
    return str(uuid.uuid4())[:8]


class User(Base):
    __tablename__ = "users"

    id = Column(String(8), primary_key=True, default=generate_id)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    def __init__(self, **kwargs):
        # Construction-time defaults (column ``default=`` only applies on INSERT).
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_admin", False)
        super().__init__(**kwargs)
