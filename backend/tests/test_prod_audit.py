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
        mod.fetch = lambda tok, path: payloads[path]
        rep = mod.audit()
        assert rep["connected"] is True
        assert rep["sections"]["account_type"]["conflicts"] == 7
        assert rep["sections"]["data_quality"]["weakest_section"] == "B"
        assert rep["sections"]["data_quality"]["top_gaps"] == ["x", "y"]

    def test_a_password_never_reaches_the_report(self):
        mod = _load(SUPERVISOR_API_BASE="https://x", SUPERVISOR_API_USER="u",
                    SUPERVISOR_API_PASSWORD="sup3rsecret")
        mod.fetch = lambda tok, path: {"summary": {}, "sections": [], "common_gaps": []}
        mod.login = lambda: "tok"
        assert "sup3rsecret" not in json.dumps(mod.audit(), ensure_ascii=False)
