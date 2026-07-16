"""v67 — unlimited, filterable log search for the AI surfaces.

The search must scan the WHOLE audit/journal tables (no newest-N pre-limit),
honor every filter, and report the TRUE totals whenever the returned rows are
cut by the token-safety ceiling — a cut must never be silent.
"""
from datetime import datetime

from app.models.audit_log import AuditLog
from app.models.crm import JournalEntry
from app.services import log_search


def test_sanitize_query_clamps_and_defaults():
    q = log_search.sanitize_query({"scope": "bogus", "text": "x" * 500,
                                   "evil": "1", "user": " u1 "})
    assert q["scope"] == "both"
    assert len(q["text"]) == 120
    assert q["user"] == "u1"
    assert "evil" not in q
    assert log_search.sanitize_query(None)["scope"] == "both"


async def _seed_logs(db_session):
    for i in range(5):
        db_session.add(AuditLog(
            id=f"a{i}", username="mahdi" if i % 2 == 0 else "sara",
            action="update" if i < 3 else "print", entity_type="letter",
            account_no="ACC1" if i < 4 else "ACC2",
            detail=f"ویرایش نامهٔ ترهین {i}" if i < 2 else f"کار دیگر {i}",
            created_at=datetime(2026, 7, 10 + i, 12, 0, 0),
        ))
    db_session.add(JournalEntry(id="j1", account_no="ACC1", category="letters",
                                item="صدور نامهٔ ترهین", status="done", user="mahdi",
                                notes="", created_at=datetime(2026, 7, 12, 9, 0, 0)))
    db_session.add(JournalEntry(id="j2", account_no="ACC2", category="import",
                                item="ایمپورت اکسل", status="done", user="sara",
                                notes="", created_at=datetime(2026, 7, 13, 9, 0, 0)))
    await db_session.commit()


async def test_search_logs_filters_totals_and_order(db_session):
    await _seed_logs(db_session)

    # no filter → everything, newest first, true totals
    r = await log_search.search_logs(db_session, {})
    assert r["audit_total"] == 5 and len(r["audit"]) == 5
    assert r["journal_total"] == 2 and len(r["journal"]) == 2
    assert r["audit"][0]["detail"].endswith("4")  # newest first
    assert r["warnings"] == []

    # text filter hits detail (audit) and item (journal)
    r = await log_search.search_logs(db_session, {"text": "ترهین"})
    assert r["audit_total"] == 2 and {a["detail"][-1] for a in r["audit"]} == {"0", "1"}
    assert r["journal_total"] == 1 and r["journal"][0]["item"] == "صدور نامهٔ ترهین"

    # user + action + account filters
    r = await log_search.search_logs(db_session, {"user": "mahdi", "scope": "audit"})
    assert r["audit_total"] == 3 and "journal" not in r
    r = await log_search.search_logs(db_session, {"action": "print"})
    assert r["audit_total"] == 2
    r = await log_search.search_logs(db_session, {"account_no": "ACC2", "scope": "audit"})
    assert r["audit_total"] == 1

    # date range (inclusive end date)
    r = await log_search.search_logs(db_session, {"date_from": "2026-07-11",
                                                  "date_to": "2026-07-12", "scope": "audit"})
    assert r["audit_total"] == 2


async def test_search_logs_ceiling_reports_true_total(db_session):
    await _seed_logs(db_session)
    r = await log_search.search_logs(db_session, {"scope": "audit"}, limit=2)
    assert r["audit_total"] == 5      # the SEARCH saw everything
    assert len(r["audit"]) == 2       # only the returned rows are capped
    assert any("5" in w for w in r["warnings"])  # and the cut is announced
