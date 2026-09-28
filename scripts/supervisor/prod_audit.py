#!/usr/bin/env python3
"""v140 — audit the REAL book, over HTTPS, through the app's own read-only API.

WHY NOT A DATABASE URL
----------------------
The obvious plan was a read-only ``SUPERVISOR_DATABASE_URL``. It does not work
from this environment and would have failed silently a session later: outbound
TCP on 5432 is refused here — only 443 goes through the egress proxy (measured:
443 connects, 5432 times out). So the supervisor reaches production the way a
browser does.

This is the better design anyway:
  * no database credentials anywhere — the app's own auth is the boundary;
  * read-only BY CONSTRUCTION: this module only ever issues GET requests;
  * it audits what the PRODUCT reports, which is what the officer sees, rather
    than a second opinion built from raw tables.

WHAT THE OWNER HAS TO SET (environment variables, new session to take effect)
    SUPERVISOR_API_BASE      https://<the production host>
    SUPERVISOR_API_TOKEN     a Bearer token          ── either this …
    SUPERVISOR_API_USER      username                ── … or this pair
    SUPERVISOR_API_PASSWORD  password
plus the host allowed under the environment's Network access.

A token is simpler but expires (7 days), which a weekly routine would outlive;
user+password is logged in fresh on every run, so it keeps working.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "supervisor" / "last_prod_audit.json"

BASE = (os.getenv("SUPERVISOR_API_BASE") or "").strip().rstrip("/")
TOKEN = (os.getenv("SUPERVISOR_API_TOKEN") or "").strip()
USER = (os.getenv("SUPERVISOR_API_USER") or "").strip()
PASSWORD = os.getenv("SUPERVISOR_API_PASSWORD") or ""
TIMEOUT = float(os.getenv("SUPERVISOR_API_TIMEOUT", "60"))

#: Only these are ever called. Kept as a literal list so a reader — and the test
#: — can see at a glance that the supervisor cannot change production.
READ_ENDPOINTS = {
    "account_type": "/api/crm/account-type-review",
    "data_quality": "/api/crm/data-quality",
}


class ProdAuditError(RuntimeError):
    """Could not audit production. Carries WHAT to fix, not just that it failed."""


def _ctx() -> ssl.SSLContext:
    return ssl.create_default_context()


def _request(url: str, *, data: bytes | None = None, headers: dict | None = None,
             method: str = "GET") -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ctx()) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError as e:
        raise ProdAuditError(
            f"به «{url}» نرسیدم ({e.reason}) — میزبان در Network access محیط مجاز است؟"
        ) from e
    except Exception as e:  # noqa: BLE001
        raise ProdAuditError(f"خطای غیرمنتظره در تماس با «{url}»: {type(e).__name__}: {e}") from e


def login() -> str:
    """A fresh Bearer token. A stored token is used as-is when one is supplied."""
    if TOKEN:
        return TOKEN
    if not (USER and PASSWORD):
        raise ProdAuditError(
            "نه SUPERVISOR_API_TOKEN تنظیم شده نه SUPERVISOR_API_USER/PASSWORD — "
            "بدونِ یکی از این دو نمی‌شود وارد شد"
        )
    body = urllib.parse.urlencode({"username": USER, "password": PASSWORD}).encode()
    status, raw = _request(f"{BASE}/api/auth/login", data=body,
                           headers={"Content-Type": "application/x-www-form-urlencoded"},
                           method="POST")
    if status != 200:
        raise ProdAuditError(
            f"ورود ناموفق بود (HTTP {status}) — نام کاربری/رمزِ SUPERVISOR_API_* درست است؟"
        )
    try:
        tok = json.loads(raw).get("access_token") or ""
    except Exception as e:  # noqa: BLE001
        raise ProdAuditError(f"پاسخِ ورود قابلِ خواندن نبود: {e}") from e
    if not tok:
        raise ProdAuditError("سرور توکنی برنگرداند")
    return tok


def fetch(token: str, path: str) -> dict:
    status, raw = _request(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    if status == 401:
        raise ProdAuditError(f"«{path}» اجازهٔ دسترسی نداد (۴۰۱) — توکن منقضی شده؟")
    if status == 404:
        raise ProdAuditError(f"«{path}» روی production وجود ندارد — هنوز دیپلوی نشده؟")
    if status != 200:
        raise ProdAuditError(f"«{path}» پاسخِ HTTP {status} داد")
    try:
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001
        raise ProdAuditError(f"پاسخِ «{path}» JSON معتبر نبود: {e}") from e


def audit() -> dict:
    if not BASE:
        raise ProdAuditError(
            "SUPERVISOR_API_BASE تنظیم نشده — بدونِ آن نمی‌دانم به کجا وصل شوم"
        )
    token = login()
    out: dict = {"base": BASE, "connected": True, "sections": {}}
    at = fetch(token, READ_ENDPOINTS["account_type"])
    dq = fetch(token, READ_ENDPOINTS["data_quality"])
    out["sections"]["account_type"] = at.get("summary", {})
    out["sections"]["data_quality"] = {
        "total_customers": dq.get("total_customers"),
        "average_percent": dq.get("average_percent"),
        "weakest_section": min(dq.get("sections") or [{"title": None, "percent": 0}],
                               key=lambda s: s.get("percent", 0)).get("title"),
        "top_gaps": [g.get("label") for g in (dq.get("common_gaps") or [])[:5]],
    }
    return out


if __name__ == "__main__":
    try:
        rep = audit()
    except ProdAuditError as e:
        rep = {"base": BASE or "(تنظیم نشده)", "connected": False, "error": str(e)[:400]}
    except Exception as e:  # noqa: BLE001
        rep = {"base": BASE or "(تنظیم نشده)", "connected": False,
               "error": f"{type(e).__name__}: {e}"[:400]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False))
    if not rep.get("connected"):
        # a run that could not see production must not look like a clean run
        sys.exit(3)
