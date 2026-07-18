"""v85 — conservative account resolution for import records WITHOUT a printed
account number, plus knowledge-base harvesting with GLOBAL content dedupe.

The owner's rules under test:
  * a customer NAME in the content may attribute the record — but only on a
    UNIQUE match, with Persian spelling variants folded;
  * the FILE NAME may carry the account number — used only when unambiguous;
  * a bare 6-digit number is NOT trusted as an account (deed/document numbers
    look identical) — ambiguity is reported for review, never guessed;
  * several files for several accounts resolve independently;
  * re-harvested knowledge must NEVER duplicate an entry (even across topics).
"""
import pytest

from app.models.customer import Customer
from app.services import doc_ingest, kb_store


def _cust(account_no: str, name: str) -> Customer:
    return Customer(account_no=account_no, name=name, account_type="corporate",
                    status="active")


async def _seed(db_session):
    db_session.add(_cust("115524", "شرکت پارس تجارت خاورمیانه"))
    db_session.add(_cust("330011", "EFCO TRADING LLC"))
    db_session.add(_cust("440022", "شرکت پارس تجارت جنوب"))
    await db_session.commit()


class TestNameNormalization:
    def test_arabic_variants_and_zwnj_fold_together(self):
        assert doc_ingest._norm_name_fa("شركت پارس‌تجارت") == doc_ingest._norm_name_fa("شرکت پارس تجارت")

    def test_fa_same_name_subset_needs_two_shared_tokens(self):
        assert doc_ingest._fa_same_name("پارس تجارت", "شرکت پارس تجارت خاورمیانه")
        assert not doc_ingest._fa_same_name("پارس", "شرکت پارس تجارت")

    def test_merge_key_prefers_account_then_name(self):
        assert doc_ingest.merge_key({"account_no": "115524"}) == "115524"
        assert doc_ingest.merge_key({"name": "شرکت نمونه"}).startswith("~")
        assert doc_ingest.merge_key({}) == ""


class TestResolveAccounts:
    async def test_unique_name_match_resolves_with_spelling_variant(self, db_session):
        await _seed(db_session)
        customers = [{"name": "شركت پارس‌تجارت خاورميانه", "fields": {"business_type": "Trading"}}]
        out, unmatched = await doc_ingest.resolve_accounts(db_session, customers, "گزارش.pdf")
        assert not unmatched and out[0]["account_no"] == "115524"
        assert out[0]["_match_note"]

    async def test_ambiguous_name_goes_to_review_not_guess(self, db_session):
        await _seed(db_session)
        # «شرکت پارس تجارت» matches BOTH خاورمیانه and جنوب via containment.
        customers = [{"name": "شرکت پارس تجارت"}]
        out, unmatched = await doc_ingest.resolve_accounts(db_session, customers, "x.pdf")
        assert out == [] and len(unmatched) == 1
        assert "هم‌نام" in unmatched[0]["reason"]
        cands = {c["account_no"] for c in unmatched[0]["candidates"]}
        assert cands == {"115524", "440022"}

    async def test_filename_account_used_for_single_record(self, db_session):
        await _seed(db_session)
        customers = [{"name": "", "fields": {"aecb_score": "600"}}]
        out, unmatched = await doc_ingest.resolve_accounts(
            db_session, customers, "صورتحساب 330011.pdf")
        assert not unmatched and out[0]["account_no"] == "330011"

    async def test_filename_account_not_spread_over_multiple_records(self, db_session):
        await _seed(db_session)
        customers = [{"name": "ناشناس یکم"}, {"name": "ناشناس دوم"}]
        out, unmatched = await doc_ingest.resolve_accounts(
            db_session, customers, "docs-330011.pdf")
        assert out == [] and len(unmatched) == 2

    async def test_filename_vs_name_conflict_goes_to_review(self, db_session):
        await _seed(db_session)
        # file name says 330011 but the printed name is clearly the 115524 customer…
        # name is unique → the NAME wins only if filename didn't contradict; here
        # they conflict → review, never a silent pick.
        customers = [{"name": "شرکت پارس تجارت خاورمیانه"}]
        out, unmatched = await doc_ingest.resolve_accounts(
            db_session, customers, "گزارش 330011.pdf")
        assert out == [] and len(unmatched) == 1
        assert "متفاوت" in unmatched[0]["reason"]

    async def test_six_digit_content_number_alone_never_matches(self, db_session):
        await _seed(db_session)
        # the model obeyed the caution rule and left account_no empty even though
        # the content contained a 6-digit deed number equal to a real account.
        customers = [{"name": "شرکت ناشناخته", "properties": [{"mortgage_deed_no": "115524"}]}]
        out, unmatched = await doc_ingest.resolve_accounts(db_session, customers, "سند.pdf")
        assert out == [] and len(unmatched) == 1

    async def test_explicit_accounts_pass_through_untouched(self, db_session):
        await _seed(db_session)
        customers = [{"account_no": "115524", "name": "whatever"}]
        out, unmatched = await doc_ingest.resolve_accounts(db_session, customers, "x.pdf")
        assert out == customers and unmatched == []


class TestKbGlobalDedupe:
    async def test_same_content_different_topic_title_is_skipped(self, db_session):
        r1 = await kb_store.upsert_entry(
            db_session, topic_title="بخشنامهٔ نرخ کارمزد", content="نرخ کارمزد صدور ضمانت‌نامه ۲٪ است.",
            source_kind="import_ai", global_dedupe=True)
        assert r1["ok"] and r1["created_entry"]
        r2 = await kb_store.upsert_entry(
            db_session, topic_title="کارمزدها", content="نرخ کارمزد صدور ضمانت‌نامه ۲٪ است.",
            source_kind="import_ai", global_dedupe=True)
        assert r2["ok"] and not r2["created_entry"] and r2.get("duplicate_global")

    async def test_default_path_still_per_topic(self, db_session):
        r1 = await kb_store.upsert_entry(
            db_session, topic_title="سرفصل الف", content="متن مشترک آزمایشی.")
        r2 = await kb_store.upsert_entry(
            db_session, topic_title="سرفصل ب", content="متن مشترک آزمایشی.")
        assert r1["created_entry"] and r2["created_entry"]  # legacy behavior kept


class TestImportPromptRules:
    def test_import_rules_mention_caution_and_kb(self):
        from app.routers.imports import _import_rules
        t = _import_rules("گزارش 115524.xlsx")
        assert "گزارش 115524.xlsx" in t
        assert "سند رهنی" in t and "kb_items" in t and "account_no" in t
