"""Every table is either backed up, or deliberately not — and says which.

The owner asked, after one database extension: «آیا زیرساخت لازم برای گرفتن و دادنِ
اطلاعاتِ موارد جدید فراهم شده؟ … این باید همیشه یادت بمونه و جایی ثبت کنی که نیاز
به یادآوریِ همیشه و مکررِ من نداشته باشه». This file is that record, in the only
form that cannot be forgotten: a test that fails.

The Google Drive snapshot reads a HARD-CODED list of models. When it was written it
covered the tables that existed; every table added since then was silently left out.
By the time this was checked, 30 of 47 tables were missing — including `letters`,
`offer_letters`, `credit_reviews`, `exchange_rates`, `charge_rules` and the whole
knowledge base. A restore from such a snapshot comes back with the customers intact
and every document the branch ever wrote simply gone, with nothing anywhere saying so.

So: a new table must be added to `_targets()` or to `BACKUP_EXCLUDED` with a reason.
Adding one and doing neither fails here, at the point the table is introduced,
instead of on the day someone restores.
"""
import pytest

import app.db_init  # noqa: F401  — importing this registers every model
from app.database import Base
from app.services.backup import BACKUP_EXCLUDED, _targets


def test_every_table_is_either_backed_up_or_excluded_with_a_reason():
    covered = {m.__tablename__ for m in _targets().values()}
    unaccounted = sorted(set(Base.metadata.tables) - covered - set(BACKUP_EXCLUDED))
    assert not unaccounted, (
        "These tables are in neither the backup nor the documented exclusion list:\n  "
        + "\n  ".join(unaccounted)
        + "\n\nAdd each to app/services/backup.py — `_targets()` if the owner would "
          "want it back after a restore, or `BACKUP_EXCLUDED` with the reason why "
          "not. See docs/DATA_SURFACE_CHECKLIST.md."
    )


def test_every_exclusion_gives_a_real_reason():
    for table, reason in BACKUP_EXCLUDED.items():
        assert isinstance(reason, str) and len(reason.strip()) >= 20, (
            f"'{table}' is excluded from the backup without a usable reason. "
            f"«not needed» is not a reason; say what the data is and why losing it "
            f"is acceptable.")


def test_exclusions_name_tables_that_actually_exist():
    """A stale exclusion silently re-opens the hole it was covering."""
    unknown = sorted(set(BACKUP_EXCLUDED) - set(Base.metadata.tables))
    assert not unknown, f"BACKUP_EXCLUDED names tables that no longer exist: {unknown}"


def test_nothing_is_both_backed_up_and_excluded():
    covered = {m.__tablename__ for m in _targets().values()}
    both = sorted(covered & set(BACKUP_EXCLUDED))
    assert not both, f"listed as both backed up and excluded: {both}"


@pytest.mark.parametrize("table", [
    # The documents the branch produces. Losing any of these loses work that
    # cannot be reconstructed from anywhere else in the system.
    "letters", "case_reports", "credit_reviews", "offer_letters",
    "customers", "facilities", "customer_profiles",
    "guarantors", "securities", "mortgaged_properties", "partners",
    "attachments",
])
def test_the_irreplaceable_tables_are_in_the_snapshot(table):
    covered = {m.__tablename__ for m in _targets().values()}
    assert table in covered, (
        f"'{table}' holds work nobody can redo and is not in the backup")


def test_the_backup_can_still_name_a_model_for_every_section():
    """Each section must map to a real mapped class with a primary key, because
    the streaming writer pages by that key."""
    for name, model in _targets().items():
        assert hasattr(model, "__mapper__"), f"{name} is not a mapped model"
        assert model.__mapper__.primary_key, f"{name} has no primary key to page by"
