"""Knowledge-Base chat («گفت‌وگو با دانش‌نامه») — sessions, messages, files.

Owner request (2026-10-07): ask banking questions on the دانش‌نامه page; the AI
answers from EVERYTHING in the KB (static tabs + the growing dynamic entries). If
the KB has no answer it says so and answers from the web; the owner can approve a
web answer and the AI files it in the KB under the right tab/category/topic.
Questions and answers persist as history and show up in the activity log. Files
may be attached; they are read in full (never summarised), kept in the session
and mirrored to Google Drive under a coded name.

Three tables, deliberately plain:
  * kb_chat_sessions — one conversation (owner = who started it);
  * kb_chat_messages — every turn; an assistant turn records WHERE the answer
    came from (``source``: kb | web | none), which model, and — for web answers —
    the sources and whether it has been filed into the KB;
  * kb_chat_files    — an attachment: verbatim extracted text + where the bytes
    live (Drive id/link, or the container disk with the reason).
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def _sid() -> str:
    return "KC-" + uuid.uuid4().hex[:12]


def _mid() -> str:
    return "KM-" + uuid.uuid4().hex[:12]


def _fid() -> str:
    return "KF-" + uuid.uuid4().hex[:12]


# Where an assistant answer came from — never collapsed into one another.
SOURCE_KB = "kb"          # answered from the دانش‌نامه (and/or the attached files)
SOURCE_WEB = "web"        # KB had nothing; answered from the web (needs approval to file)
SOURCE_NONE = "none"      # neither (no web-capable model, or the call failed)

# Filing state of a WEB answer.
KB_NONE = ""              # nothing to file (user turn, KB answer, error)
KB_PENDING = "pending"    # web answer, waiting for the owner's «تأیید»
KB_FILED = "filed"        # analysed by AI and stored in the KB


class KbChatSession(Base):
    __tablename__ = "kb_chat_sessions"

    id = Column(String(20), primary_key=True, default=_sid)
    title = Column(String(300), default="")
    created_by = Column(String(80), index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class KbChatMessage(Base):
    __tablename__ = "kb_chat_messages"

    id = Column(String(20), primary_key=True, default=_mid)
    session_id = Column(String(20), index=True, nullable=False)
    role = Column(String(12), nullable=False)             # user | assistant
    content = Column(Text, nullable=False)
    source = Column(String(10), default="")               # kb | web | none (assistant only)
    model_name = Column(String(160))
    web_model_name = Column(String(160))                  # model that did the web step, if different
    sources = Column(JSONType, default=list)              # [{title,url}] for web answers
    meta = Column(JSONType, default=dict)                 # kb context size, warnings, file ids, …
    kb_state = Column(String(10), default="")             # "" | pending | filed
    kb_topic_id = Column(String(20))
    kb_entry_id = Column(String(20))
    kb_placement = Column(String(500))                    # «تب › دسته › عنوان» for the UI
    error = Column(Text)
    created_by = Column(String(80))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KbChatFile(Base):
    __tablename__ = "kb_chat_files"

    id = Column(String(20), primary_key=True, default=_fid)
    session_id = Column(String(20), index=True, nullable=False)
    message_id = Column(String(20), index=True)
    filename = Column(String(300), nullable=False)
    mime = Column(String(120))
    byte_size = Column(Integer, default=0)
    sha256 = Column(String(64))
    extract_status = Column(String(12), default="")       # ok|empty|unsupported|failed|image
    extract_note = Column(Text)
    text = Column(Text)                                   # the file's FULL text, verbatim
    text_chars = Column(Integer, default=0)
    truncated = Column(Boolean, default=False)
    store = Column(String(10), default="")                # drive | local
    drive_id = Column(String(120))
    drive_link = Column(String(500))
    local_path = Column(String(500))
    store_note = Column(Text)
    created_by = Column(String(80))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
