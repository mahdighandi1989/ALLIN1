"""Knowledge Base (پایگاه دانش) — general/educational content harvested from
letters and their attachments (and added manually), organized as TOPICS with
per-entry SOURCE references.

Design (owner requirement, 2026-07-14):
  * similar material groups UNDER ONE TOPIC — never one row per sentence;
  * every entry keeps a precise reference to where it came from (letter,
    attachment file, import) so it can be traced back;
  * the index/categories are derived live from the rows, so the KB page's
    فهرست updates the moment an entry lands (no separate index to maintain).

The static hand-curated KB (frontend/src/app/knowledge/content.ts) stays as the
seed body of the page; these rows render after it as the growing, AI-fed part.
"""
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.database import Base


def _tid() -> str:
    return "KT-" + uuid.uuid4().hex[:12]


def _eid() -> str:
    return "KE-" + uuid.uuid4().hex[:12]


class KnowledgeTopic(Base):
    """A grouped subject («عنوان») the entries live under."""

    __tablename__ = "kb_topics"

    id = Column(String(20), primary_key=True, default=_tid)
    title = Column(String(300), nullable=False)
    # normalized title for grouping/dedup (casefolded, whitespace-collapsed)
    title_norm = Column(String(300), index=True, nullable=False)
    category = Column(String(120), default="عمومی")     # درس/رویه/بخشنامه/…
    created_by = Column(String(80))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)


class KnowledgeEntry(Base):
    """One piece of content under a topic, with its exact provenance."""

    __tablename__ = "kb_entries"

    id = Column(String(20), primary_key=True, default=_eid)
    topic_id = Column(String(20), index=True, nullable=False)
    content = Column(Text, nullable=False)
    # sha-like normalized-content key for dedup (re-running the assistant on the
    # same letter must not double the entry)
    content_norm = Column(String(64), index=True)
    source_kind = Column(String(30), default="letter_ai")   # letter_ai | attachment | manual
    source_ref = Column(String(400))    # «نامهٔ ۱۸۲/۴/… — پیوست x.pdf» / letter id
    account_no = Column(String(50))
    created_by = Column(String(80))
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __init__(self, **kwargs):
        kwargs.setdefault("is_deleted", False)
        super().__init__(**kwargs)
