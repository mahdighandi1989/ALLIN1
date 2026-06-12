"""build_backup_payload must page through large tables with bounded memory while
still returning EVERY row exactly once — including across chunk boundaries.

Regression guard for the fix that stopped the Drive snapshot loading all ~44k
customer_profiles as ORM objects at once (which OOM-killed the 512MB instance).
"""
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
