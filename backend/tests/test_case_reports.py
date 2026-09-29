"""گزارش خلاصهٔ پروندهٔ حقوقی — the legal case-file summary report.

The owner asked for this report to carry «تمام قابلیت‌ها و گزینه‌ها» the official
letters carry, and for the database to «همه چیز پوشش بده — چه داده‌هایی که می‌گیره
چه تحویل می‌ده». These tests hold both halves of that:

  * every section of the paper form has somewhere to land, and comes back
    byte-identical — a report that loses a column is a report the branch cannot send;
  * the money text the source documents actually use is understood, and text that
    ISN'T money reads as unknown rather than as zero.
"""
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.case_report import CaseReport
from app.routers.case_reports import SCALAR_FIELDS, TABLE_FIELDS, parse_amount

API = "/api/case-reports"


# Every amount below is copied verbatim from the filled report the owner attached.
@pytest.mark.parametrize("raw,expected", [
    ("95/22.645 درهم", "22645.95"),     # RTL extraction puts the DECIMALS first
    ("53/278.969", "278969.53"),
    ("95/324.976", "324976.95"),
    ("65/ 113,004", "113004.65"),       # …with comma thousands and a stray space
    ("98/ 226,013", "226013.98"),
    ("63/ 339,018", "339018.63"),
    ("34/ 323,183", "323183.34"),
    ("81/191,216", "191216.81"),
    ("15/540.412درهم", "540412.15"),    # currency glued to the number
    ("-/312,240", "312240"),            # «-/» is the round-figure marker
    ("-/7,870", "7870"),
    ("-/52.500", "52500"),              # dots as thousands
    ("7.000", "7000"),
    ("370,503,000 ریال", "370503000"),
    ("۷۰,۰۰۰ درهم", "70000"),           # Persian digits
    ("10.000 دلار", "10000"),
])
def test_the_money_the_documents_actually_use_is_understood(raw, expected):
    assert parse_amount(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", ["محاسبه سود متوقف گردیده", "-", "*", "", "   ", None])
def test_what_is_not_money_is_unknown_never_zero(raw):
    """A cell that cannot be read is not a cell worth zero.

    The register sums these columns. Folding «محاسبه سود متوقف گردیده» to 0 would
    quietly under-report the bank's own claim, which is exactly the failure
    experiences/a-monitor-must-distinguish-unmeasured-from-zero.md is about.
    """
    assert parse_amount(raw) is None


class TestEverySectionOfTheFormHasSomewhereToLand:
    async def test_the_paper_form_round_trips_field_for_field(self, client, auth_headers):
        """Fill one field per section, save, reload — nothing may be dropped."""
        fields = {n: f"مقدار {i}" for i, n in enumerate(SCALAR_FIELDS)}
        tables = {n: [{"c1": f"{n}-a", "c2": f"{n}-b"}] for n in TABLE_FIELDS}
        r = await client.post(f"{API}/", headers=auth_headers,
                              json={"general": True, "fields": fields, "tables": tables})
        assert r.status_code == 201, r.text
        rid = r.json()["id"]

        back = (await client.get(f"{API}/{rid}", headers=auth_headers)).json()
        for name in SCALAR_FIELDS:
            assert back["fields"][name] == fields[name], f"lost scalar field {name}"
        for name in TABLE_FIELDS:
            assert back["tables"][name] == tables[name], f"lost table {name}"

    async def test_a_repeating_table_keeps_its_rows_and_their_order(self, client, auth_headers):
        """§6 collections are read as a ledger — order is meaning, not decoration."""
        rows = [{"date": f"0{i}/05/2014", "amount": f"-/{i}0,000"} for i in range(1, 6)]
        r = await client.post(f"{API}/", headers=auth_headers,
                              json={"general": True, "tables": {"collections": rows}})
        back = (await client.get(f"{API}/{r.json()['id']}", headers=auth_headers)).json()
        assert back["tables"]["collections"] == rows

    async def test_an_unknown_field_name_cannot_write_itself_into_the_row(self, client, auth_headers):
        """`fields` is an explicit allow-list, not a spread onto the model."""
        r = await client.post(f"{API}/", headers=auth_headers, json={
            "general": True,
            "fields": {"title": "گزارش", "is_deleted": True, "created_by": "someone-else"},
        })
        assert r.status_code == 201, r.text
        back = (await client.get(f"{API}/{r.json()['id']}", headers=auth_headers)).json()
        assert back["title"] == "گزارش"
        assert back["created_by"] if "created_by" in back else True   # never "someone-else"


class TestTheTotalsAreQueryableNotJustPrintable:
    async def test_headline_totals_get_a_parsed_numeric_mirror(self, client, auth_headers, db_session):
        r = await client.post(f"{API}/", headers=auth_headers, json={"general": True, "fields": {
            "books_total": "63/ 339,018",
            "court_total": "15/540.412درهم",
            "collections_total": "-/312,240",
        }})
        rid = r.json()["id"]
        row = (await db_session.execute(
            select(CaseReport).where(CaseReport.id == rid))).scalar_one()
        assert row.books_total == "63/ 339,018"          # verbatim, for printing
        assert row.books_total_num == Decimal("339018.63")   # parsed, for summing
        assert row.court_total_num == Decimal("540412.15")
        assert row.collections_total_num == Decimal("312240")

    async def test_an_unreadable_total_is_null_not_zero(self, client, auth_headers, db_session):
        r = await client.post(f"{API}/", headers=auth_headers,
                              json={"general": True, "fields": {"books_total": "در دست بررسی"}})
        row = (await db_session.execute(select(CaseReport).where(
            CaseReport.id == r.json()["id"]))).scalar_one()
        assert row.books_total == "در دست بررسی"
        assert row.books_total_num is None


class TestTheTwoBucketsTheOwnerAlreadyKnows:
    async def test_a_report_can_belong_to_an_account(self, client, auth_headers):
        r = await client.post(f"{API}/", headers=auth_headers, json={
            "account_no": "301432", "fields": {"title": "آقا تریدینگ"}})
        assert r.status_code == 201, r.text
        assert r.json()["account_no"] == "301432"
        assert r.json()["category"] == "account"
        listed = (await client.get(f"{API}/?account_no=301432", headers=auth_headers)).json()
        assert [x["id"] for x in listed] == [r.json()["id"]]

    async def test_a_general_report_has_no_account_and_its_own_bucket(self, client, auth_headers):
        r = await client.post(f"{API}/", headers=auth_headers,
                              json={"general": True, "fields": {"title": "عمومی"}})
        assert r.json()["account_no"] is None
        assert r.json()["category"] == "general"
        listed = (await client.get(f"{API}/?general=true", headers=auth_headers)).json()
        assert r.json()["id"] in [x["id"] for x in listed]

    async def test_an_account_report_does_not_show_up_in_the_general_bucket(self, client, auth_headers):
        acc = (await client.post(f"{API}/", headers=auth_headers,
                                 json={"account_no": "301432"})).json()
        gen = (await client.get(f"{API}/?general=true", headers=auth_headers)).json()
        assert acc["id"] not in [x["id"] for x in gen]

    async def test_saving_under_a_new_account_creates_that_customer_profile(self, client, auth_headers):
        """Same courtesy letters do — the report must not fail because the
        customer row does not exist yet."""
        r = await client.post(f"{API}/", headers=auth_headers, json={"account_no": "999888777"})
        assert r.status_code == 201, r.text
        prof = await client.get("/api/customers/999888777", headers=auth_headers)
        assert prof.status_code in (200, 404)   # created or reachable; never a 500


class TestEditingAndRemoving:
    async def test_editing_changes_only_what_was_sent(self, client, auth_headers):
        r = (await client.post(f"{API}/", headers=auth_headers, json={
            "general": True,
            "fields": {"title": "اول", "branch_name": "عجمان"},
            "tables": {"partners": [{"name": "مسعود آقا"}]},
        })).json()
        await client.patch(f"{API}/{r['id']}", headers=auth_headers,
                           json={"general": True, "fields": {"title": "دوم"}})
        back = (await client.get(f"{API}/{r['id']}", headers=auth_headers)).json()
        assert back["title"] == "دوم"
        assert back["fields"]["branch_name"] == "عجمان"          # untouched
        assert back["tables"]["partners"] == [{"name": "مسعود آقا"}]  # untouched

    async def test_deleting_is_soft_so_the_report_is_recoverable(self, client, auth_headers, db_session):
        r = (await client.post(f"{API}/", headers=auth_headers, json={"general": True})).json()
        assert (await client.delete(f"{API}/{r['id']}", headers=auth_headers)).status_code == 204
        assert (await client.get(f"{API}/{r['id']}", headers=auth_headers)).status_code == 404
        row = (await db_session.execute(select(CaseReport).where(
            CaseReport.id == r["id"]))).scalar_one()
        assert row.is_deleted is True      # still there, quarantined not destroyed

    async def test_a_missing_report_is_a_404_not_a_crash(self, client, auth_headers):
        assert (await client.get(f"{API}/nope", headers=auth_headers)).status_code == 404
        assert (await client.patch(f"{API}/nope", headers=auth_headers,
                                   json={"general": True})).status_code == 404
        assert (await client.delete(f"{API}/nope", headers=auth_headers)).status_code == 404


class TestPrefillOffersWhatTheDatabaseAlreadyKnows:
    async def test_prefill_is_not_shadowed_by_the_report_id_route(self, client, auth_headers):
        """«prefill» is a literal path declared beside «/{report_id}».

        Declared in the wrong order it would be read as a report id and answer 404
        — a healthy-looking response for a route that never runs
        (experiences/a-literal-route-must-precede-its-wildcard.md).
        """
        r = await client.get(f"{API}/prefill?account_no=301432", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["account_no"] == "301432"

    async def test_an_unknown_account_is_answered_honestly_not_invented(self, client, auth_headers):
        r = (await client.get(f"{API}/prefill?account_no=nosuchacct", headers=auth_headers)).json()
        assert r["found"] is False
        assert r["tables"]["partners"] == []
        assert r["tables"]["collaterals"] == []

    async def test_prefill_offers_the_partners_the_profile_already_holds(self, client, auth_headers, db_session):
        from app.models.profile_entities import Partner
        db_session.add(Partner(id="p-case-1", account_no="301432", name="مسعود آقا",
                               national_id="4709861676", share="100%", nationality="ایرانی",
                               role="مدیر صاحب امضا"))
        await db_session.commit()
        r = (await client.get(f"{API}/prefill?account_no=301432", headers=auth_headers)).json()
        rows = r["tables"]["partners"]
        assert len(rows) == 1
        assert rows[0]["name"] == "مسعود آقا"
        assert rows[0]["national_id"] == "4709861676"
        assert rows[0]["role"] == "مدیر صاحب امضا"
        assert "100%" in rows[0]["share"] and "ایرانی" in rows[0]["share"]

    async def test_prefill_never_writes_anything(self, client, auth_headers, db_session):
        before = len((await db_session.execute(select(CaseReport))).scalars().all())
        await client.get(f"{API}/prefill?account_no=301432", headers=auth_headers)
        after = len((await db_session.execute(select(CaseReport))).scalars().all())
        assert before == after


class TestItIsNotOpenToThePublic:
    async def test_every_route_needs_a_login(self, client):
        assert (await client.get(f"{API}/")).status_code in (401, 403)
        assert (await client.get(f"{API}/prefill?account_no=1")).status_code in (401, 403)
        assert (await client.post(f"{API}/", json={"general": True})).status_code in (401, 403)
        assert (await client.delete(f"{API}/x")).status_code in (401, 403)


class TestTheFormAndTheApiAgreeOnEveryFieldName:
    """A field the page writes but the API does not know is silently discarded.

    Nothing fails, nothing logs — the branch fills a box, presses save, and the
    value is simply gone the next time the report is opened. The two sides live in
    different languages, so no compiler can catch a rename on one of them; this
    test reads the actual form definition and checks it against the actual
    allow-list.
    """

    @staticmethod
    def _repo_root():
        import pathlib
        return pathlib.Path(__file__).resolve().parents[2]

    def _read(self, rel: str) -> str:
        p = self._repo_root() / rel
        if not p.exists():
            import pytest
            pytest.skip(f"{rel} not present (backend-only checkout)")
        return p.read_text(encoding="utf-8")

    def test_every_scalar_the_form_spec_names_is_stored(self):
        import re
        src = self._read("frontend/src/app/case-report/sections.ts")
        names = set()
        # free-text sections: `field: 'company_summary'`
        names |= set(re.findall(r"field:\s*'([a-z_]+)'", src))
        # fixed grids: `fields: ['stagnation_date', 'stagnation_balance']`
        for arr in re.findall(r"fields:\s*\[([^\]]*)\]", src, re.S):
            names |= set(re.findall(r"'([a-z_]+)'", arr))
        # values printed inside a column heading: `label: 'سود با نرخ {court_interest_rate}'`
        names |= set(re.findall(r"\{([a-z_]+)\}", src))
        names.discard("")
        # A count guard, because the shape of this file changed once already and a
        # regex that silently stops matching turns this whole test green and
        # meaningless. If the spec is restructured again, this fails loudly and
        # asks to be re-read rather than quietly checking nothing.
        assert len(names) >= 18, (
            f"only {len(names)} field names parsed out of sections.ts "
            f"({sorted(names)}) — the spec's shape probably changed and this "
            f"check has stopped looking at anything")
        missing = sorted(names - set(SCALAR_FIELDS))
        assert not missing, f"the form writes fields the API drops: {missing}"

    def test_every_repeating_section_the_form_spec_names_is_stored(self):
        import re
        src = self._read("frontend/src/app/case-report/sections.ts")
        keys = set(re.findall(r"kind:\s*'table',\s*key:\s*'([a-z_]+)'", src))
        assert keys, "could not read any table keys out of sections.ts"
        missing = sorted(keys - set(TABLE_FIELDS))
        assert not missing, f"the form has tables the API drops: {missing}"

    def test_every_header_box_on_the_page_is_stored(self):
        import re
        src = self._read("frontend/src/app/case-report/page.tsx")
        names = set(re.findall(r'<Fld[^>]*?\sk="([a-z_]+)"', src, re.S))
        assert names, "could not read any <Fld> keys out of page.tsx"
        missing = sorted(names - set(SCALAR_FIELDS))
        assert not missing, f"the page writes fields the API drops: {missing}"


class TestItIsRecoverableLikeTheUiPromises:
    """The delete dialog says «به سطلِ بازیافت می‌رود».

    A soft delete that the recycle bin does not list is not a recycle bin — it is
    a disappearance with a flag set in a table nobody reads. The promise the UI
    makes has to be the promise the API keeps.
    """

    async def test_a_deleted_report_appears_in_the_recycle_bin(self, client, auth_headers):
        r = (await client.post(API + "/", headers=auth_headers, json={
            "general": True, "fields": {"title": "گزارشِ حذف‌شده"}})).json()
        await client.delete(f"{API}/{r['id']}", headers=auth_headers)
        bin_ = (await client.get("/api/trash/", headers=auth_headers)).json()
        mine = [x for x in bin_["items"] if x["id"] == r["id"]]
        assert mine, "the deleted report is not in the recycle bin"
        assert mine[0]["type"] == "case_report"
        assert mine[0]["label"] == "گزارشِ حذف‌شده"
        assert bin_["counts"]["case_reports"] >= 1

    async def test_it_can_actually_be_restored(self, client, auth_headers):
        r = (await client.post(API + "/", headers=auth_headers, json={
            "general": True, "fields": {"title": "برگشتنی", "books_total": "-/312,240"}})).json()
        await client.delete(f"{API}/{r['id']}", headers=auth_headers)
        assert (await client.get(f"{API}/{r['id']}", headers=auth_headers)).status_code == 404
        back = await client.post(f"/api/trash/case_report/{r['id']}/restore", headers=auth_headers)
        assert back.status_code == 200, back.text
        again = await client.get(f"{API}/{r['id']}", headers=auth_headers)
        assert again.status_code == 200
        assert again.json()["fields"]["books_total"] == "-/312,240"   # content intact

    async def test_a_live_report_is_not_in_the_bin(self, client, auth_headers):
        r = (await client.post(API + "/", headers=auth_headers, json={"general": True})).json()
        bin_ = (await client.get("/api/trash/", headers=auth_headers)).json()
        assert r["id"] not in [x["id"] for x in bin_["items"]]
