"""v139 — telling a person's account from a company's.

This decides which Credit File form opens, which KYC fields are required and how
completeness is scored, so a wrong answer is not cosmetic. The rule the tests
enforce is: **positive evidence only, and no evidence means «ask», never a
guess** — guessing is what put the wrong type on the records in the first place.
"""
import pytest

from app.services.account_type import (
    CORPORATE, RETAIL, SME, UNKNOWN, Verdict, classify, disagrees, is_undecided, normalize,
)


class TestDocumentsOnlyOneKindHas:
    def test_a_trade_licence_means_a_company(self):
        v = classify(name="Abu Amir Furnishing Branch", trade_license_no="1040716")
        assert v.guess == CORPORATE and v.confidence == "high"
        assert any("Trade License" in r for r in v.reasons)

    def test_partners_mean_a_company(self):
        v = classify(name="Something", partner_count=3)
        assert v.guess == CORPORATE and v.confidence == "high"

    def test_a_person_never_carries_a_trade_licence_so_it_outranks_a_name_hint(self):
        """A company record legitimately holds its MANAGER's passport — the
        corporate form has a «Manager Emirates ID» field. The licence wins."""
        v = classify(name="Mr. Ali Hassan", trade_license_no="99", passport_no="A1")
        assert v.guess == CORPORATE
        assert v.counter_reasons, "the conflicting evidence must still be shown"


class TestNaming:
    @pytest.mark.parametrize("name", [
        "FUTURE DEAL GENERAL TRADING LLC",
        "CASTELO NERO FOODSTUFF TRADING",
        "Al Noor Contracting Est",
        "Gulf Marine Services FZE",
        "شرکت بازرگانی پارس",
    ])
    def test_a_trade_name_reads_as_corporate(self, name):
        assert classify(name=name).guess == CORPORATE, name

    @pytest.mark.parametrize("name", ["Mr. Ali Hassan", "Mrs. Fatima", "آقای رضایی"])
    def test_a_personal_title_reads_as_retail(self, name):
        assert classify(name=name).guess == RETAIL, name

    def test_a_word_is_matched_whole_not_as_a_fragment(self):
        """'EST' inside 'Estate' or 'CO' inside 'Cotton' must not make a company
        out of a person — a substring match would misclassify at scale."""
        assert classify(name="Ernesto Silva").guess == UNKNOWN
        assert classify(name="Nicolas Incera").guess == UNKNOWN


class TestIdentityDocumentsAreWeak:
    def test_id_documents_alone_read_as_retail(self):
        v = classify(name="Ahmad Karimi", emirates_id_no="784-1969-0685380-7")
        assert v.guess == RETAIL

    def test_id_documents_say_nothing_once_there_is_corporate_evidence(self):
        v = classify(name="Gulf Trading LLC", emirates_id_no="784-1", passport_no="A1")
        assert v.guess == CORPORATE
        assert not any("پاسپورت" in r for r in v.reasons)


class TestNoEvidenceMeansAsk:
    def test_a_bare_name_is_unknown_not_retail(self):
        """The whole bug: an unknown account was stored as «retail», so the
        chooser silently opened the individual's form for a company."""
        v = classify(name="Ahmad")
        assert v.guess == UNKNOWN and v.confidence == "none"
        assert not v.decided

    def test_an_empty_record_is_unknown(self):
        assert classify().guess == UNKNOWN

    def test_business_type_alone_can_decide_either_way(self):
        assert classify(business_type="Corporate").guess == CORPORATE
        assert classify(business_type="Individual / Salaried").guess == RETAIL


class TestStoredValues:
    @pytest.mark.parametrize("v", ["", None, "unknown", "  ", "-"])
    def test_an_undecided_value_is_recognised(self, v):
        assert is_undecided(v)

    @pytest.mark.parametrize("v", ["retail", "corporate", "sme"])
    def test_a_decided_value_is_recognised(self, v):
        assert not is_undecided(v)

    def test_normalize_maps_anything_unrecognised_to_unknown(self):
        assert normalize("RETAIL") == RETAIL
        assert normalize("garbage") == UNKNOWN
        assert normalize(None) == UNKNOWN


class TestDisagreement:
    def test_retail_stored_against_a_trade_licence_is_a_contradiction(self):
        v = classify(name="X", trade_license_no="1")
        assert disagrees("retail", v)

    def test_sme_is_a_corporate_sub_type_not_a_contradiction(self):
        v = classify(name="Gulf Trading LLC")
        assert not disagrees("sme", v)
        assert not disagrees("corporate", v)

    def test_an_undecided_value_is_missing_not_contradictory(self):
        """The two problems must never be mixed: «nobody decided» is not the
        same finding as «the decision is wrong», and they need different fixes."""
        v = classify(name="X", trade_license_no="1")
        assert not disagrees("", v)
        assert not disagrees("unknown", v)

    def test_weak_evidence_never_calls_a_stored_value_wrong(self):
        assert not disagrees("retail", Verdict(CORPORATE, "low", ["hunch"]))
        assert not disagrees("retail", Verdict(UNKNOWN, "none"))


class TestItNeverWrites:
    def test_classify_is_pure(self):
        """It returns an opinion. Nothing in this system may silently
        reclassify a customer — a human decides."""
        import inspect
        from app.services import account_type as mod
        src = inspect.getsource(mod)
        for forbidden in ("session", "db.add", "commit", "update(", "delete("):
            assert forbidden not in src, forbidden


class TestRegionalFalsePositives:
    """v142 — words that look personal but are trade names here.

    Found on the FIRST live run against the real book, not by review: the owner
    hesitated over a genuine finding, and the hesitation was right.
    """

    @pytest.mark.parametrize("name", [
        "AL SHEIKH A.E.G",          # the real account 110221
        "AL SHEIKH TRADING",
        "SHEIKH ZAYED EST",
    ])
    def test_sheikh_alone_no_longer_calls_a_company_an_individual(self, name):
        v = classify(name=name)
        assert v.guess != RETAIL, (name, v.reasons)

    def test_a_real_person_is_still_recognised_by_a_title(self):
        assert classify(name="Mr. Ali Hassan").guess == RETAIL

    def test_a_person_with_no_signal_at_all_is_asked_about_not_guessed(self):
        """Safer to ask than to be wrong: an unrecognised name produces no
        finding, so it can never contradict a correct stored value."""
        assert classify(name="Sheikh Ahmed").guess == UNKNOWN
