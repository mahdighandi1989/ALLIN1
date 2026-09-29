"""v140 — the supervisor's production auditor.

It reaches the real book over HTTPS through the app's own API, because a direct
database connection is impossible from the environment the routine runs in:
outbound TCP on 5432 is refused there, only 443 passes the egress proxy. A
`SUPERVISOR_DATABASE_URL` would therefore have failed a session later, quietly.

The two properties that must never regress: it can only READ, and when it cannot
see production it must say so loudly instead of looking like a clean run.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts" / "supervisor" / "prod_audit.py"


def _load(**env):
    """Load the script fresh; it reads its configuration at import time."""
    import os
    saved = {k: os.environ.get(k) for k in (
        "SUPERVISOR_API_BASE", "SUPERVISOR_API_TOKEN",
        "SUPERVISOR_API_USER", "SUPERVISOR_API_PASSWORD")}
    for k in saved:
        os.environ.pop(k, None)
    os.environ.update({k: v for k, v in env.items() if v is not None})
    try:
        spec = importlib.util.spec_from_file_location("sup_prod_audit", SPEC)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sup_prod_audit"] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


#: v149 — a fresh-enough Drive, so a test about coverage is not also a test
#: about backups. Individual tests override it.
DRIVE_OK = {"configured": True, "connected": True, "mode": "oauth",
            "interval_hours": 24, "last_snapshot_at": "2026-09-29T02:00:00+00:00",
            "snapshot_age_hours": 1.2, "snapshot_overdue": False}


def _serve(payloads):
    """v144 — the audit appends `?limit=…&offset=…`, so match on the path only.

    A mock that keyed on the exact string silently KeyError'd the moment paging
    arrived; matching the path is what the real server does.
    """
    def fetch(tok, path):
        base = path.split("?", 1)[0]
        if base.endswith("/backup/drive/status") and base not in payloads:
            return dict(DRIVE_OK)
        return payloads[base]
    return fetch


class TestItCanOnlyRead:
    def test_every_endpoint_it_knows_is_a_read(self):
        mod = _load(SUPERVISOR_API_BASE="https://x")
        for name, path in mod.READ_ENDPOINTS.items():
            assert path.startswith("/api/"), (name, path)
            assert "apply" not in path and "delete" not in path, (name, path)

    def test_it_never_issues_a_write_method(self):
        """The only POST in the module is the login itself. A supervisor with
        full authority over the code must still not be able to change the book
        through this path."""
        src = SPEC.read_text(encoding="utf-8")
        posts = [ln for ln in src.splitlines() if 'method="POST"' in ln]
        assert len(posts) == 1, posts
        for verb in ('method="PUT"', 'method="DELETE"', 'method="PATCH"'):
            assert verb not in src, verb

    def test_fetch_asks_for_nothing_but_get(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        seen = []

        def fake(url, *, data=None, headers=None, method="GET"):
            seen.append((method, url, data))
            return 200, b"{}"

        mod._request = fake
        mod.fetch("t", "/api/crm/data-quality")
        assert seen == [("GET", "https://x/api/crm/data-quality", None)]


class TestItFailsLoudly:
    def test_no_base_url_is_an_error_not_an_empty_report(self):
        mod = _load()
        with pytest.raises(mod.ProdAuditError) as e:
            mod.audit()
        assert "SUPERVISOR_API_BASE" in str(e.value)

    def test_no_credentials_at_all_is_an_error(self):
        mod = _load(SUPERVISOR_API_BASE="https://x")
        with pytest.raises(mod.ProdAuditError) as e:
            mod.login()
        assert "SUPERVISOR_API_TOKEN" in str(e.value)

    @pytest.mark.parametrize("status,needle", [
        (401, "توکن"), (404, "دیپلوی"), (500, "HTTP 500"),
    ])
    def test_an_http_failure_says_what_to_fix(self, status, needle):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        mod._request = lambda *a, **k: (status, b"")
        with pytest.raises(mod.ProdAuditError) as e:
            mod.fetch("t", "/api/crm/data-quality")
        assert needle in str(e.value)

    def test_a_bad_login_names_the_variables_to_check(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_USER="u",
                    SUPERVISOR_API_PASSWORD="p")
        mod._request = lambda *a, **k: (401, b"")
        with pytest.raises(mod.ProdAuditError) as e:
            mod.login()
        assert "SUPERVISOR_API_" in str(e.value)

    def test_the_script_exits_non_zero_when_it_cannot_see_production(self):
        """A run that audited nothing must not be filed as a clean run — the
        same rule the inventory learned in v137."""
        import os
        import subprocess
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("SUPERVISOR_API_")}
        r = subprocess.run([sys.executable, str(SPEC)], capture_output=True,
                           text=True, env=env, timeout=120, cwd=str(ROOT))
        assert r.returncode == 3, (r.returncode, r.stdout[-300:])
        assert json.loads(r.stdout)["connected"] is False


class TestReport:
    def test_it_summarises_both_sections(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {"conflicts": 7, "undecided": 3}},
            "/api/crm/data-quality": {
                "total_customers": 2000, "average_percent": 41,
                "sections": [{"title": "A", "percent": 80}, {"title": "B", "percent": 12}],
                "common_gaps": [{"label": "x"}, {"label": "y"}],
            },
        }
        mod.fetch = _serve(payloads)
        rep = mod.audit()
        assert rep["connected"] is True
        assert rep["sections"]["account_type"]["conflicts"] == 7
        assert rep["sections"]["data_quality"]["weakest_section"] == "B"
        assert rep["sections"]["data_quality"]["top_gaps"] == ["x", "y"]

    def test_a_capped_sweep_is_reported_as_a_sample(self):
        """v144 — the supervisor called 3000 of 44,608 customers «the book»."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {
                "conflicts": 47, "undecided": 0, "total": 20000,
                "examined": 20000, "book_total": 44608, "partial": True}},
            "/api/crm/data-quality": {
                "total_customers": 2000, "examined": 2000, "book_total": 44608,
                "partial": True, "average_percent": 5,
                "sections": [{"title": "A", "percent": 80}],
                "common_gaps": [],
            },
        }
        mod.fetch = _serve(payloads)
        rep = mod.audit()
        cov = rep["coverage"]
        assert cov["any_partial"] is True
        assert len(cov["warnings"]) == 2
        # the real numbers, not the caps, are what a reader is handed
        by = {s["section"]: s for s in cov["sections"]}
        assert by["کیفیتِ داده"]["book_total"] == 44608
        assert by["کیفیتِ داده"]["percent"] == 4
        assert by["بازبینیِ نوعِ حساب"]["percent"] == 45
        assert all("نمونه است" in w for w in cov["warnings"])

    def test_an_aggregate_does_not_inherit_the_first_page_paging_keys(self):
        """Measured against production: after walking all 44,608 rows the report
        still read «total: 20000, has_more: true», copied from page one. A
        per-page field has no meaning in a total."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        BOOK = 3

        def fetch(tok, path):
            if "/backup/drive/status" in path:
                return dict(DRIVE_OK)
            off = 0
            if "offset=" in path:
                off = int(path.split("offset=")[1].split("&")[0])
            n = min(2, max(0, BOOK - off))
            more = off + n < BOOK
            if "account-type-review" in path:
                return {"summary": {"total": 2, "limit": 2, "offset": off,
                                    "examined": n, "book_total": BOOK, "has_more": more,
                                    "conflicts": 0, "undecided": 0, "agreed": n},
                        "conflicts": [], "undecided": []}
            return {"customers": [{"percent": 1}] * n, "examined": n,
                    "book_total": BOOK, "has_more": more,
                    "sections": [], "common_gaps": []}

        mod.fetch = fetch
        at = mod.audit()["sections"]["account_type"]
        assert at["examined"] == BOOK
        assert at["total"] == BOOK          # restated, not page one's 2
        assert at["has_more"] is False      # the walk finished
        assert "limit" not in at and "offset" not in at

    def test_a_full_sweep_raises_no_coverage_warning(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {
                "examined": 12, "book_total": 12, "partial": False}},
            "/api/crm/data-quality": {
                "examined": 12, "book_total": 12, "partial": False,
                "average_percent": 90, "sections": [], "common_gaps": []},
        }
        mod.fetch = _serve(payloads)
        cov = mod.audit()["coverage"]
        assert cov["any_partial"] is False and cov["warnings"] == []

    def test_an_old_backend_without_the_coverage_keys_is_flagged_not_assumed_full(self):
        """Missing coverage must read as «unknown», never as «saw everything»."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        mod.fetch = lambda tok, path: (
            dict(DRIVE_OK) if "/backup/drive/status" in path else
            {"summary": {"total": 3000}, "total_customers": 2000, "customers": [],
             "sections": [], "common_gaps": []})
        cov = mod.audit()["coverage"]
        assert cov["any_partial"] is False           # cannot claim partial either
        assert len(cov["warnings"]) == 2
        assert all("نمی‌داند" in w for w in cov["warnings"])

    def test_it_walks_every_page_of_the_book(self):
        """v144 — one call saw a slice; the walk must see all of it.

        Three pages of conflicts must arrive as ONE list, and the counts must be
        the book's, not the last page's.
        """
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        BOOK = 5

        def fetch(tok, path):
            base, _, qs = path.partition("?")
            if base.endswith("/backup/drive/status"):
                return dict(DRIVE_OK)
            params = dict(kv.split("=") for kv in qs.split("&") if "=" in kv)
            off = int(params.get("offset", 0))
            n = min(2, max(0, BOOK - off))
            more = off + n < BOOK
            if base.endswith("account-type-review"):
                return {
                    "summary": {"examined": n, "book_total": BOOK, "has_more": more,
                                "conflicts": n, "undecided": 0, "agreed": 0},
                    "conflicts": [{"account_no": f"a{off+i}"} for i in range(n)],
                    "undecided": [],
                }
            return {
                "customers": [{"percent": 50} for _ in range(n)],
                "examined": n, "book_total": BOOK, "has_more": more,
                "sections": [{"title": "A", "filled": n, "total": n * 2, "percent": 50}],
                "common_gaps": [{"label": "x", "count": n}],
            }

        mod.fetch = fetch
        rep = mod.audit()

        at = rep["sections"]["account_type"]
        assert at["examined"] == BOOK, at        # 2 + 2 + 1, not 2
        assert at["conflicts"] == BOOK           # summed across pages
        assert at["partial"] is False            # the whole book WAS seen
        assert at["passes"] == 3

        dq = rep["sections"]["data_quality"]
        assert dq["examined"] == BOOK and dq["partial"] is False
        assert dq["average_percent"] == 50       # rebuilt from per-customer rows
        assert rep["coverage"]["any_partial"] is False
        assert rep["coverage"]["warnings"] == []

    def test_a_walk_that_stops_early_says_so(self):
        """A truncated walk must never look like a complete one."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t",
                    SUPERVISOR_MAX_PASSES="2")

        def fetch(tok, path):
            if "/backup/drive/status" in path:
                return dict(DRIVE_OK)
            # always claims there is more — the guard must stop it and admit it
            if "account-type-review" in path:
                return {"summary": {"examined": 1, "book_total": 999, "has_more": True,
                                    "conflicts": 0, "undecided": 0, "agreed": 1},
                        "conflicts": [], "undecided": []}
            return {"customers": [{"percent": 10}], "examined": 1, "book_total": 999,
                    "has_more": True, "sections": [], "common_gaps": []}

        mod.fetch = fetch
        rep = mod.audit()
        assert rep["sections"]["account_type"]["walk_truncated"] is True
        assert rep["sections"]["account_type"]["passes"] == 2
        assert rep["sections"]["data_quality"]["walk_truncated"] is True
        # and the coverage warning still fires, because it IS partial
        assert rep["coverage"]["any_partial"] is True

    def test_a_section_with_no_denominator_is_not_scored_as_perfect(self):
        """0/0 is «unknown», not 100% — keep what the page reported."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {"examined": 1, "book_total": 1}},
            "/api/crm/data-quality": {
                "customers": [{"percent": 30}], "examined": 1, "book_total": 1,
                "sections": [{"title": "A", "percent": 80}, {"title": "B", "percent": 12}],
                "common_gaps": [],
            },
        }
        mod.fetch = _serve(payloads)
        rep = mod.audit()
        assert rep["sections"]["data_quality"]["weakest_section"] == "B"

    def test_an_older_backend_without_has_more_makes_exactly_one_pass(self):
        """No paging support must not turn into an endless loop."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        calls = []

        def fetch(tok, path):
            if "/backup/drive/status" in path:
                return dict(DRIVE_OK)
            calls.append(path)
            if "account-type-review" in path:
                return {"summary": {"total": 3000}, "conflicts": [], "undecided": []}
            return {"customers": [], "total_customers": 2000,
                    "sections": [], "common_gaps": []}

        mod.fetch = fetch
        rep = mod.audit()
        assert len(calls) == 2, calls                     # one pass each
        assert rep["sections"]["account_type"]["passes"] == 1
        assert "walk_truncated" not in rep["sections"]["account_type"]

    def test_it_reports_an_overdue_backup(self):
        """v149 — «configured and connected» says the pipe is open, not that
        anything went through it. The v136 hole lasted three days while both were
        true, and nothing outside the container could see it."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {"examined": 1, "book_total": 1}},
            "/api/crm/data-quality": {"customers": [{"percent": 50}], "examined": 1,
                                      "book_total": 1, "sections": [], "common_gaps": []},
            "/api/crm/backup/drive/status": {
                "configured": True, "connected": True, "mode": "oauth",
                "interval_hours": 24, "last_snapshot_at": "2026-09-25T00:00:00+00:00",
                "snapshot_age_hours": 96.0, "snapshot_overdue": True},
        }
        mod.fetch = _serve(payloads)
        rep = mod.audit()
        assert rep["sections"]["drive"]["snapshot_overdue"] is True
        assert any("عقب افتاده" in w for w in rep.get("warnings") or [])
        assert any("96" in w for w in rep.get("warnings") or [])

    def test_a_fresh_backup_raises_no_warning(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")
        payloads = {
            "/api/crm/account-type-review": {"summary": {"examined": 1, "book_total": 1}},
            "/api/crm/data-quality": {"customers": [], "examined": 0, "book_total": 0,
                                      "sections": [], "common_gaps": []},
        }
        mod.fetch = _serve(payloads)          # serves a fresh DRIVE_OK
        rep = mod.audit()
        assert rep["sections"]["drive"]["snapshot_overdue"] is False
        assert not [w for w in (rep.get("warnings") or []) if "بکاپ" in w]

    def test_a_drive_check_that_fails_does_not_lose_the_rest_of_the_audit(self):
        """An ADDED check must never take down the audit it was added to: the
        other findings are already gathered by then, and losing them would make
        the run worse than before the check existed."""
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_TOKEN="t")

        def fetch(tok, path):
            if "/backup/drive/status" in path:
                raise RuntimeError("403 forbidden")
            if "account-type-review" in path:
                return {"summary": {"examined": 2, "book_total": 2, "conflicts": 5},
                        "conflicts": [], "undecided": []}
            return {"customers": [{"percent": 10}] * 2, "examined": 2, "book_total": 2,
                    "sections": [], "common_gaps": []}

        mod.fetch = fetch
        rep = mod.audit()
        assert rep["connected"] is True
        assert rep["sections"]["account_type"]["conflicts"] == 5   # not lost
        assert "403 forbidden" in rep["sections"]["drive"]["error"]
        # recorded as unknown, never as fine
        assert "snapshot_overdue" not in rep["sections"]["drive"]

    def test_a_password_never_reaches_the_report(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_USER="u",
                    SUPERVISOR_API_PASSWORD="sup3rsecret")
        mod.fetch = lambda tok, path: (
            dict(DRIVE_OK) if "/backup/drive/status" in path else
            {"summary": {}, "customers": [], "sections": [], "common_gaps": []})
        mod.login = lambda: "tok"
        assert "sup3rsecret" not in json.dumps(mod.audit(), ensure_ascii=False)
