"""User Model"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from app.database import Base


def generate_id():
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
