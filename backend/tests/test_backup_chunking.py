"""build_backup_payload must page through large tables with bounded memory while
still returning EVERY row exactly once — including across chunk boundaries.

Regression guard for the fix that stopped the Drive snapshot loading all ~44k
customer_profiles as ORM objects at once (which OOM-killed the 512MB instance).
"""
import io
import json

from app.models.customer import Customer
from app.services import backup


async def test_backup_pages_every_row_exactly_once(db_session, monkeypatch):
    monkeypatch.setattr(backup, "_BACKUP_CHUNK", 100)  # force several pages
    n = 250  # 2 full pages + a partial one
    for i in range(n):
        db_session.add(Customer(account_no=f"9{i:05d}", name=f"Cust {i}"))
    await db_session.commit()

    payload = await backup.build_backup_payload(db_session)

    assert payload["counts"]["customers"] == n
    accs = [r["account_no"] for r in payload["data"]["customers"]]
    assert len(accs) == n              # nothing dropped at a page boundary
    assert len(set(accs)) == n         # nothing duplicated across pages


async def test_backup_empty_table_is_empty_list(db_session):
    payload = await backup.build_backup_payload(db_session)
    assert payload["counts"]["customers"] == 0
    assert payload["data"]["customers"] == []


async def test_streaming_backup_is_valid_json_and_matches(db_session, monkeypatch):
    """stream_backup_to_file (memory-safe path) must produce valid JSON with the
    same rows as build_backup_payload — across page boundaries and with Unicode."""
    monkeypatch.setattr(backup, "_BACKUP_CHUNK", 100)
    n = 250
    for i in range(n):
        db_session.add(Customer(account_no=f"7{i:05d}", name=("شرکت" if i == 0 else f"Cust {i}")))
    await db_session.commit()

    buf = io.StringIO()
    counts = await backup.stream_backup_to_file(db_session, buf)
    streamed = json.loads(buf.getvalue())  # raises if the streamed JSON is malformed

    assert counts["customers"] == n
    assert streamed["counts"]["customers"] == n
    payload = await backup.build_backup_payload(db_session)
    assert sorted(r["account_no"] for r in streamed["data"]["customers"]) == \
        sorted(r["account_no"] for r in payload["data"]["customers"])
    assert "شرکت" in [r["name"] for r in streamed["data"]["customers"]]  # Unicode preserved


async def test_streaming_backup_empty_db_is_valid(db_session):
    buf = io.StringIO()
    counts = await backup.stream_backup_to_file(db_session, buf)
    doc = json.loads(buf.getvalue())
    assert counts["customers"] == 0
    assert doc["data"]["customers"] == []
    assert "generated" in doc and "counts" in doc
