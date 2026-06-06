"""User Model"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import validates, synonym
from sqlalchemy.sql import func
import uuid

from app.database import Base

# Role model: pending (signed in, no access yet) < viewer (read-only) <
# editor (create/edit data) < admin (everything + user management + backups).
ROLE_PENDING = "pending"
ROLE_VIEWER = "viewer"
ROLE_EDITOR = "editor"
ROLE_ADMIN = "admin"
ALL_ROLES = (ROLE_PENDING, ROLE_VIEWER, ROLE_EDITOR, ROLE_ADMIN)
ROLE_RANK = {ROLE_PENDING: 0, ROLE_VIEWER: 1, ROLE_EDITOR: 2, ROLE_ADMIN: 3}


def generate_id():
    # Full 32-char UUID4 hex. This deliberately replaces the previous 8-char
    # *truncated* UUID, whose "8 chars is enough for the current small scale"
    # rationale was a stale assumption: as the user base grows the truncated
    # space (~4.3e9 values) makes birthday-paradox collisions increasingly
    # likely, turning an otherwise-rare event into an IntegrityError on insert.
    # uuid4().hex uses the full 122-bit space, so collisions are not a practical
    # concern at any realistic scale and no future migration to widen the id is
    # needed. The column is String(36) (32 hex chars, with headroom) and any
    # existing 8-char ids remain valid, so this widening is backward compatible.
    # See tests/backend/app/models/test_user_uuid.py for the collision-resistance
    # edge case and tests/test_user_id_generation.py for format/uniqueness.
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_id)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    # Access level (see ROLE_* above). New Google sign-ins start as 'pending'.
    role = Column(String(20), nullable=False, default=ROLE_PENDING)
    # Google identity (null for local username/password accounts).
    auth_provider = Column(String(20), nullable=False, default="local")
    google_sub = Column(String(64), unique=True, index=True)
    # ``google_id`` is the OAuth-standard name for Google's stable subject id;
    # it is an alias of the underlying ``google_sub`` column so either name can
    # be read/written interchangeably.
    google_id = synonym("google_sub")
    picture = Column(String(500))
    # Stored only for the account that connects Google Drive for backups.
    google_refresh_token = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    @validates("role")
    def _validate_role(self, key, value):
        """Constrain role to the known set; blank/None -> 'pending'."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return ROLE_PENDING
        v = str(value).strip().lower()
        return v if v in ROLE_RANK else ROLE_PENDING

    @property
    def role_rank(self) -> int:
        return ROLE_RANK.get((self.role or ROLE_PENDING), 0)

    def has_role(self, minimum: str) -> bool:
        """True if this user's role is at least ``minimum`` in the hierarchy."""
        return self.role_rank >= ROLE_RANK.get(minimum, 99)

    def __init__(self, **kwargs):
        # Construction-time defaults (column ``default=`` only applies on INSERT).
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("is_admin", False)
        kwargs.setdefault("role", ROLE_PENDING)
        kwargs.setdefault("auth_provider", "local")
        super().__init__(**kwargs)
