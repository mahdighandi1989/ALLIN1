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


class TestNoDocumentOnFileDecidesTheType:
    """v148 — the class used to be «documents only one kind has». There are none.

    Every document rule here was demoted in turn, each after meeting real data:
    the trade licence (v143), the passport and Emirates ID (v145), and finally
    registered partners (v148) — the rule that had been trusted most. All three
    for one reason: the bank collects them from BOTH kinds of customer, so their
    presence cannot tell the two apart. What decides is now only what states who
    the customer IS — the account name, and a business type describing the
    customer.
    """

    def test_a_trade_licence_alone_is_not_proof_of_a_company(self):
        """v143, the owner's correction. When a RETAIL customer opens an
        account the bank collects the trade licence of the place they WORK, as
        evidence of employment and residence — so a licence on a personal file
        may be the employer's. It corroborates, it never decides."""
        # the name must carry NO corporate token, or this stops testing «alone»
        # (v145 taught the pattern «Branch», which the old fixture used)
        v = classify(name="Abu Amir Rahimi", trade_license_no="1040716")
        assert v.confidence == "low", v
        assert not disagrees("retail", v), "it must never contradict a stored value on its own"

    def test_a_trade_licence_makes_a_company_certain_once_something_else_agrees(self):
        v = classify(name="MATRIX GEN TRADING", trade_license_no="1040716")
        assert v.guess == CORPORATE and v.confidence == "high"

    def test_partners_alone_are_not_proof_of_a_company(self):
        """v148, the owner's correction, on the two accounts this rule was the
        SOLE basis for: «از اون 4 تا حساب دوتای اول حساب شخصی هستن … حساب اولی
        حساب مشترک».

        A JOINT personal account records its co-holder in the same `Partner`
        table a company records its shareholders in. «A natural person has no
        partners» was simply false.
        """
        v = classify(name="Something", partner_count=3)
        assert v.confidence == "low", v
        assert not disagrees("retail", v), v
        assert not disagrees("corporate", v), v

    def test_a_joint_personal_account_is_not_called_a_company(self):
        v = classify(name="YADOLLAH KHALILI/ASHRAFOLSADAT SAFA", partner_count=1)
        assert not disagrees("retail", v), v

    def test_a_personal_account_with_partners_and_a_licence_is_still_not_decided(self):
        """Two corroborating documents are still two weak signals, not one strong
        one — account 182428, four partners and a licence, is a person."""
        v = classify(name="AYOUB ABDULLAH AKHTARI AZAD",
                     partner_count=4, trade_license_no="1")
        assert not disagrees("retail", v), v

    def test_partners_still_STRENGTHEN_a_company_the_name_already_shows(self):
        """Demoted, not deleted: once something states this is a company, the
        partner rows corroborate it and the verdict is high confidence."""
        v = classify(name="Gulf Trading LLC", partner_count=3)
        assert v.guess == CORPORATE and v.confidence == "high"
        assert any("شریک" in r for r in v.reasons)

    def test_the_reason_no_longer_asserts_the_false_claim(self):
        """It used to read «a personal account has no partners». It does."""
        v = classify(name="X", partner_count=2)
        text = " ".join(v.reasons + v.counter_reasons)
        assert "حسابِ شخصی شریک ندارد" not in text
        assert "مشترک" in text        # says what is actually known

    def test_an_employee_with_the_employers_licence_on_file_stays_retail(self):
        """The real shape of the owner's correction: a person, their own ID, and
        a licence that belongs to where they work."""
        v = classify(name="Mr. Ali Hassan", trade_license_no="99", passport_no="A1")
        assert v.guess == RETAIL, v
        assert v.counter_reasons, "the licence must still be shown, as context"

    def test_two_personal_names_with_a_licence_are_not_called_a_company(self):
        """Account 113393 — «HARBHAJAN SINGH SAHANI & HARWANT SINGH SAHANI» with
        a licence attached. The owner refused it, and was right: it reads as a
        joint personal account. It must not be reported as a contradiction."""
        v = classify(name="HARBHAJAN SINGH SAHANI & HARWANT SINGH SAHANI",
                     trade_license_no="1040716")
        assert not disagrees("retail", v), v


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
    def test_id_documents_alone_lean_retail_but_cannot_contradict(self):
        """v145 — the mirror of the v143 licence correction.

        «Has an ID and no corporate signal ⇒ retail» leaned entirely on the
        corporate pattern being complete, and it was not. Against the real book
        that produced 64 contradictions — «ATLAS MEDICAL FZCO», «AL AZHAR MONEY
        EXCHANGE» — companies filed correctly as corporate, accused on the
        strength of their manager's passport. Every account opening collects a
        natural person's documents, so they corroborate; they never decide.
        """
        v = classify(name="Ahmad Karimi", emirates_id_no="784-1969-0685380-7")
        assert v.guess == RETAIL
        assert v.confidence == "low", v
        assert not disagrees("corporate", v), v   # the whole point
        assert not disagrees("retail", v), v

    def test_id_documents_say_nothing_once_there_is_corporate_evidence(self):
        v = classify(name="Gulf Trading LLC", emirates_id_no="784-1", passport_no="A1")
        assert v.guess == CORPORATE
        assert not any("پاسپورت" in r for r in v.reasons)

    @pytest.mark.parametrize("name", [
        # every one of these is a REAL account from the live book, filed
        # correctly as corporate, that a manager's passport used to contradict
        "ATLAS MEDICAL FZCO",
        "AL AZHAR MONEY EXCHANGE",
        "GOLD STANDARD DMCC",
        "APOLLO GOESSNIT GmbH (BRANCH)",
        "NBM GLOBAL IMPEX FZCO",
        "AL ADAB IRANIAN PRIVATE SCHOOL FOR GIRLS",
        "VALFAJR GEN TRDG",
        "FAYZA ALKHALEEJ BEAUTY SALON",
        "ECONOSTO MID EAST B.V.(DUBAI BRANCH",
        "FORUM CAFE. ( Sole Estableshment.)",
        "AL NUKHAILAT SUPER MARKET",
        "EFCO Food & Beverages",
        "Digi Training Inistitute",
        "PROGRESS AUTO REPAIRING",
        "AL KHALILI USED CARS AND SPARE PARTS TR",
        "SAMA EMIRATES REALESTATE (L L C)",
    ])
    def test_a_real_company_is_not_called_retail_because_its_manager_has_a_passport(self, name):
        v = classify(name=name, passport_no="A1", emirates_id_no="784-1")
        assert not disagrees("corporate", v), (name, v)

    def test_an_unrecognised_company_name_stays_quiet_rather_than_guessing_wrong(self):
        """v145 — the pattern will never cover every trade name. What it cannot
        recognise must come out «low», not «retail, medium»."""
        v = classify(name="MOKHTARAN G T", passport_no="A1")
        assert v.confidence == "low"
        assert not disagrees("corporate", v) and not disagrees("retail", v)


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
    def test_retail_stored_against_registered_partners_is_NOT_a_contradiction(self):
        """v148 — inverted by the owner's correction. This assertion encoded the
        claim «a natural person has no partners», which a joint account refutes.
        Measured on the whole book: exactly 2 accounts rested on this rule alone,
        and the owner confirmed both are personal. Neither had been written."""
        v = classify(name="X", partner_count=3)
        assert not disagrees("retail", v)

    def test_retail_stored_against_a_licence_alone_is_NOT_a_contradiction(self):
        v = classify(name="X", trade_license_no="1")
        assert not disagrees("retail", v)

    def test_sme_is_a_corporate_sub_type_not_a_contradiction(self):
        v = classify(name="Gulf Trading LLC")
        assert not disagrees("sme", v)
        assert not disagrees("corporate", v)

    def test_an_undecided_value_is_missing_not_contradictory(self):
        """The two problems must never be mixed: «nobody decided» is not the
        same finding as «the decision is wrong», and they need different fixes."""
        v = classify(name="X", partner_count=2)
        assert not disagrees("", v)
        assert not disagrees("unknown", v)

    def test_weak_evidence_never_calls_a_stored_value_wrong(self):
        assert not disagrees("retail", Verdict(CORPORATE, "low", ["hunch"]))
        assert not disagrees("retail", Verdict(UNKNOWN, "none"))

    def test_corporate_stored_against_an_id_document_alone_is_NOT_a_contradiction(self):
        """v145 — the symmetric twin of the licence rule above. Measured on the
        live book: this one rule produced 64 false contradictions."""
        v = classify(name="X", passport_no="A1")
        assert not disagrees("corporate", v)
        v = classify(name="X", emirates_id_no="784-1")
        assert not disagrees("corporate", v)

    def test_both_corroborating_documents_together_still_decide_nothing(self):
        """A licence AND a passport are still two weak signals, not one strong
        one — they point opposite ways and neither is proof."""
        v = classify(name="X", trade_license_no="1", passport_no="A1")
        assert v.confidence == "low", v
        assert not disagrees("retail", v) and not disagrees("corporate", v)
        # both are still REPORTED — demoted, not deleted
        assert v.reasons and v.counter_reasons


class TestATitleOnlyCountsWhereATitleGoes:
    """v147 — found on the FIRST full-book run (44,608 accounts), not by review.

    Four of the six «this company looks like a person» findings were wrong, and
    all four for the same reason as the SHEIKH false positive in v142: a word
    that is a personal title elsewhere is part of a TRADE NAME here.
    """

    @pytest.mark.parametrize("name", [
        "NEW MISS PARIS",              # a boutique, «MISS» mid-name
        "MISS GALLERY FASHION",
        "VIGIL ENG",                   # Engineering, not Engineer
        "AL YAQEEN ENG CONSUL TATIONS OFFICE",
    ])
    def test_a_trade_name_is_not_a_person(self, name):
        v = classify(name=name)
        assert not disagrees("corporate", v), (name, v)
        assert not disagrees("sme", v), (name, v)

    def test_a_real_title_leading_the_name_still_counts(self):
        assert disagrees("corporate", classify(name="MR:A.K.UMMER"))
        assert classify(name="Mr. Ahmad Karimi").guess == RETAIL
        assert classify(name="خانم زهرا محمدی").guess == RETAIL

    def test_a_title_in_the_middle_of_a_name_is_not_a_title(self):
        """«NEW MISS PARIS» — anchoring is the whole fix."""
        assert classify(name="NEW MISS PARIS").guess == UNKNOWN

    def test_engineering_is_corporate_evidence_now_not_a_personal_title(self):
        v = classify(name="VIGIL ENG")
        assert v.guess == CORPORATE
        assert any("ENG" in r.upper() for r in v.reasons)


class TestALineOfBusinessIsNotACustomerType:
    """v147 — the trade-licence mistake for the THIRD time.

    v143: a licence is collected from retail customers too.
    v145: a passport is collected from corporate customers too.
    Here: `business_type` «RETAIL SALE OF WARE AND TOOLS» describes what the
    shop SELLS, not who owns the account — and a shop is a company.
    """

    def test_retail_sale_activity_is_corporate_not_retail(self):
        v = classify(name="Naser House Hold",
                     business_type="RETAIL SALE OF WARE AND TOOLS")
        assert not disagrees("corporate", v), v
        assert v.guess == CORPORATE

    @pytest.mark.parametrize("btype", [
        "RETAIL SALE OF WARE AND TOOLS", "Retail Trading",
        "retail shop", "RETAIL STORE", "retail business",
    ])
    def test_every_line_of_business_phrasing_reads_as_activity(self, btype):
        v = classify(name="Something", business_type=btype)
        assert not disagrees("corporate", v), (btype, v)

    def test_a_plain_retail_business_type_still_means_a_person(self):
        """The narrow fix must not swallow the real signal."""
        assert classify(business_type="Retail").guess == RETAIL
        assert classify(business_type="Individual / Salaried").guess == RETAIL

    def test_the_reason_says_it_is_an_activity_not_a_customer_type(self):
        v = classify(name="X", business_type="RETAIL SALE OF TOOLS")
        assert any("نوعِ فعالیت" in r for r in v.reasons), v


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
