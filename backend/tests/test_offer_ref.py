import pytest
from app.utils.offer_ref import extract_offer_ref, offer_ref_key
from app.schemas.facility import FacilityResponse


@pytest.mark.parametrize("raw,want", [
    ("182/4/1045/2025 OFFER LETTER", "182/4/1045/2025"),
    ("182/4/52/2026", "182/4/52/2026"),
    ("182 / 4 / 52 / 2026", "182/4/52/2026"),
    ("182-4-52-2026", "182/4/52/2026"),
    ("۱۸۲/۴/۵۲/۲۰۲۶", "182/4/52/2026"),
    ("STF 1251218000001", "STF-1251218000001"),
    ("pim-1260109000001", "PIM-1260109000001"),
    ("BLC1260119000002", "BLC-1260119000002"),
    ("Tpl  1260109000001", "TPL-1260109000001"),
])
def test_recognised(raw, want):
    assert extract_offer_ref(raw) == want


@pytest.mark.parametrize("raw", [None, "", "-", "???", "OLD - CLASSIFIED",
                                 "A/C CLOSED - TEST PROFILE", "F-354476-20251216111534",
                                 "182/4/52", "1260109000001"])
def test_not_a_reference(raw):
    assert extract_offer_ref(raw) is None


def test_key_equal_across_spellings():
    assert offer_ref_key("STF 1251218000001") == offer_ref_key("stf-1251218000001")
    assert offer_ref_key("182/4/52/2026") == offer_ref_key("182 - 4 - 52 - 2026")
    assert offer_ref_key("182/4/52/2026") != offer_ref_key("182/4/53/2026")


def test_facility_response_exposes_offer_ref():
    r = FacilityResponse(id="F1", name="PIM 1260109000001")
    assert r.model_dump()["offer_ref"] == "PIM-1260109000001"
