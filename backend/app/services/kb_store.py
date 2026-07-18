"""Knowledge-Base persistence: grouped-topic upsert with per-entry provenance.

The single write path for AI-harvested AND manual KB content, so the grouping
rules live in ONE place:
  * a topic is matched by its normalized title (casefold, collapsed whitespace,
    Arabic yeh/kaf → Persian) — the same normalization the letter assistant's
    find-guard uses, so «آیین نامه» and «آيين‌نامه» land under one topic;
  * an entry is deduped inside its topic by normalized content, so re-running
    the assistant over the same letter never duplicates rows;
  * categories/index need no separate maintenance — they are derived live.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb import KnowledgeTopic, KnowledgeEntry


def norm_title(s: str) -> str:
    s = (s or "").replace("‌", " ").replace(" ", " ")
    s = s.replace("ي", "ی").replace("ك", "ک")
    # combining marks that vary by typist (hamza-above in «بیمهٔ», tanwin, kasra…)
    s = re.sub("[\u064b-\u0654\u0670]", "", s)
    return re.sub(r"\s+", " ", s).strip().casefold()[:300]


def norm_content_key(s: str) -> str:
    base = norm_title(s)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:64]


async def upsert_entry(
    db: AsyncSession, *, topic_title: str, content: str,
    category: str = "", source_kind: str = "letter_ai", source_ref: str = "",
    account_no: str = "", username: str = "", global_dedupe: bool = False,
) -> dict:
    """Group ``content`` under the topic named ``topic_title`` (created if new).

    Returns {"topic_id", "entry_id", "created_topic", "created_entry"} —
    ``created_entry`` False means the identical content already existed (skip).
    """
    title = (topic_title or "").strip()
    content = (content or "").strip()
    if not title or not content:
        return {"ok": False, "reason": "empty"}

    tnorm = norm_title(title)
    topic: Optional[KnowledgeTopic] = (await db.execute(
        select(KnowledgeTopic).where(KnowledgeTopic.title_norm == tnorm,
                                     KnowledgeTopic.is_deleted == False)  # noqa: E712
    )).scalars().first()
    created_topic = False
    if topic is None:
        topic = KnowledgeTopic(title=title[:300], title_norm=tnorm,
                               category=(category or "عمومی")[:120], created_by=username)
        db.add(topic)
        await db.flush()
        created_topic = True
    elif category and (topic.category or "") in ("", "عمومی"):
        # a more specific category upgrades the default — never overwrites a
        # deliberate one (fill-empty, the profile-precedence lesson)
        topic.category = category[:120]

    ckey = norm_content_key(content)
    if global_dedupe:
        # v85 (import harvesting): the same knowledge re-uploaded over time must
        # NEVER duplicate — even if the model files it under a different topic
        # title this time. Content identity wins over topic identity.
        anywhere = (await db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.content_norm == ckey,
                                         KnowledgeEntry.is_deleted == False)  # noqa: E712
        )).scalars().first()
        if anywhere is not None:
            return {"ok": True, "topic_id": anywhere.topic_id, "entry_id": anywhere.id,
                    "created_topic": created_topic, "created_entry": False,
                    "duplicate_global": True}
    existing = (await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.topic_id == topic.id,
                                     KnowledgeEntry.content_norm == ckey,
                                     KnowledgeEntry.is_deleted == False)  # noqa: E712
    )).scalars().first()
    if existing is not None:
        return {"ok": True, "topic_id": topic.id, "entry_id": existing.id,
                "created_topic": created_topic, "created_entry": False}

    entry = KnowledgeEntry(topic_id=topic.id, content=content, content_norm=ckey,
                           source_kind=(source_kind or "letter_ai")[:30],
                           source_ref=(source_ref or "")[:400],
                           account_no=(account_no or "")[:50], created_by=username)
    db.add(entry)
    await db.flush()
    return {"ok": True, "topic_id": topic.id, "entry_id": entry.id,
            "created_topic": created_topic, "created_entry": True}
