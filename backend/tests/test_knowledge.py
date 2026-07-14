"""Knowledge Base (v61): grouped-topic upsert with provenance, dedup, live
index — and the letter-assistant kb_write path that feeds it."""
import pytest
from sqlalchemy import select

from app.services import kb_store
from app.services import letter_assistant as la
from app.models.kb import KnowledgeTopic, KnowledgeEntry


CONTENT_A = "برای ترهین ملک ابتدا ارزیابی رسمی انجام می‌شود و سپس سند رهنی در دفترخانه تنظیم می‌گردد."
CONTENT_B = "پس از تنظیم سند رهنی، بیمه‌نامهٔ ملک باید به نفع بانک صادر و هر سال تمدید شود."


@pytest.mark.asyncio
async def test_kb_store_groups_similar_topics_and_dedups_content(db_session):
    # two spellings of the SAME topic (Arabic yeh + ZWNJ variants) → ONE topic
    r1 = await kb_store.upsert_entry(db_session, topic_title="قواعد ترهين املاک",
                                     content=CONTENT_A, category="وثایق",
                                     source_ref="نامهٔ ۱۸۲/۴/۴۰۰", username="t")
    r2 = await kb_store.upsert_entry(db_session, topic_title="قواعد ترهین املاک",
                                     content=CONTENT_B, category="وثایق",
                                     source_ref="پیوست valuation.pdf", username="t")
    await db_session.commit()
    assert r1["ok"] and r2["ok"]
    assert r1["created_topic"] is True and r2["created_topic"] is False
    assert r1["topic_id"] == r2["topic_id"]

    # identical content again → deduped (no new entry)
    r3 = await kb_store.upsert_entry(db_session, topic_title="قواعد ترهین املاک",
                                     content=CONTENT_A, source_ref="دوباره", username="t")
    await db_session.commit()
    assert r3["ok"] and r3["created_entry"] is False

    topics = (await db_session.execute(select(KnowledgeTopic))).scalars().all()
    entries = (await db_session.execute(select(KnowledgeEntry))).scalars().all()
    assert len(topics) == 1 and len(entries) == 2
    # provenance survives on each entry
    refs = {e.source_ref for e in entries}
    assert "نامهٔ ۱۸۲/۴/۴۰۰" in refs and "پیوست valuation.pdf" in refs


@pytest.mark.asyncio
async def test_kb_endpoint_lists_grouped_with_live_index(client, auth_headers, db_session):
    await kb_store.upsert_entry(db_session, topic_title="محاسبهٔ کارمزد LG",
                                content=CONTENT_A, category="محاسبات", username="t")
    await db_session.commit()
    r = await client.get("/api/knowledge/", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["categories"] == ["محاسبات"]
    t0 = data["topics"][0]
    assert t0["title"] == "محاسبهٔ کارمزد LG" and len(t0["entries"]) == 1


@pytest.mark.asyncio
async def test_apply_db_persists_kb_items(client, auth_headers, db_session):
    r = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={
        "items": [], "links": [],
        "kb_items": [{"topic": "قواعد بیمهٔ املاک رهنی", "content": CONTENT_B,
                      "category": "وثایق", "source_note": "بند ۲ نامه"}],
        "source_ref": "L-100",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["kb_added"] == 1
    entries = (await db_session.execute(select(KnowledgeEntry))).scalars().all()
    assert len(entries) == 1 and "L-100" in (entries[0].source_ref or "")

    # applying the SAME item again is a no-op (dedup), not a duplicate row
    r2 = await client.post("/api/letter-ai/apply-db", headers=auth_headers, json={
        "items": [], "kb_items": [{"topic": "قواعد بیمه املاک رهنی", "content": CONTENT_B}],
    })
    assert r2.status_code == 200 and r2.json()["kb_added"] == 0


# ---------------- v61 prompt characterization ----------------

def test_v61_rules_and_tools_reach_the_model():
    sp = la.SYSTEM_PROMPT
    # sender-correctness rule: external ⇒ سرپرستی, internal ⇒ دایره تسهیلات
    assert "درستیِ امضاکننده" in sp
    assert "سرپرستی منطقه خلیج فارس" in sp and "دایره تسهیلات اعطایی" in sp
    # kb_write is described (and bound to the extraction tool)
    assert "kb_write" in sp
    # the full-check tool exists with DB-mismatch + letter↔attachment conformity
    assert "full_check" in la.TOOLS
    g = la.TOOLS["full_check"]["guide"]
    assert "بازرسِ مغایرت" in g and "انطباقِ نامه با پیوست‌ها" in g
    assert "شماره‌نامه‌ها" in g or "شماره و تاریخِ نامهٔ ارجاع‌شده" in g
    # db_extract now covers the Knowledge Base too
    assert "پایگاه دانش" in la.TOOLS["db_extract"]["label"]
    assert "kb_write" in la.TOOLS["db_extract"]["guide"]


def test_v61_prompt_carries_attachment_content():
    p = la.build_user_prompt({}, {}, ["full_check"],
                             attachments_text=[{"name": "x.pdf", "text": "متن پیوست"}],
                             attachment_tables=["<table><tr><td>۱</td></tr></table>"])
    assert "محتوای پیوست‌های نامه" in p and "x.pdf" in p and "متن پیوست" in p
    assert "جدولِ پیوست 1" in p


def test_parse_kb_writes_filters_and_dedups():
    raw = ('{"changes":['
           '{"op":"kb_write","topic":"قواعد ترهین املاک","category":"وثایق",'
           f'"content":"{CONTENT_A}","source_note":"نامه ۱۸۲/۴/۴۰۰"}},'
           '{"op":"kb_write","topic":"","content":"کوتاه"},'
           '{"op":"kb_write","topic":"قواعد ترهین املاک",'
           f'"content":"{CONTENT_A}"}}'
           ']}')
    out = la.parse_kb_writes(raw)
    assert len(out) == 1
    assert out[0]["topic"] == "قواعد ترهین املاک" and out[0]["category"] == "وثایق"
