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
    # v149 — «are the backups fresh?» is a standing duty (PROMPT §4) that until
    # now could not be answered from outside the container. Read-only.
    "drive": "/api/crm/backup/drive/status",
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


# --- v144: walk the WHOLE book -------------------------------------------
# Both endpoints are capped (20000 / 5000 rows). A single call therefore sees a
# slice, and the earlier audit reported that slice as the book. `offset` paging
# fixes the cause; these two helpers do the walking and re-aggregate honestly.
#: how many passes we are willing to make — a runaway loop must end, and a walk
#: that stops early has to SAY so rather than look complete.
MAX_PASSES = int(os.getenv("SUPERVISOR_MAX_PASSES", "12"))


def _walk_account_type(token) -> dict:
    """Every conflict in the book, not just the first page of them."""
    path = READ_ENDPOINTS["account_type"]
    conflicts: list = []
    undecided: list = []
    summary: dict = {}
    examined = 0
    offset = 0
    passes = 0
    truncated = False
    while True:
        page = fetch(token, f"{path}?limit=20000&offset={offset}")
        sm = page.get("summary") or {}
        if not summary:
            summary = dict(sm)
        else:
            for k in ("conflicts", "undecided", "undecided_with_evidence", "agreed"):
                summary[k] = int(summary.get(k) or 0) + int(sm.get(k) or 0)
        conflicts += page.get("conflicts") or []
        undecided += page.get("undecided") or []
        got = int(sm.get("examined", sm.get("total")) or 0)
        examined += got
        passes += 1
        # `has_more` is absent on an older backend — then one pass is all we get
        if not sm.get("has_more") or got == 0:
            break
        if passes >= MAX_PASSES:
            truncated = True
            break
        offset += got
    summary["examined"] = examined
    summary["partial"] = examined < int(summary.get("book_total") or 0)
    summary["passes"] = passes
    # The first page's own paging keys describe THAT PAGE, and copying them into
    # an aggregate makes it lie: after a full walk it read «total: 20000,
    # has_more: true» over a 44,608-row book that had been read completely. A
    # per-page field has no meaning in a total, so it is restated or dropped.
    summary["total"] = examined
    summary["has_more"] = False
    for per_page_only in ("limit", "offset"):
        summary.pop(per_page_only, None)
    if truncated:
        summary["walk_truncated"] = True
    return {"summary": summary, "conflicts": conflicts, "undecided": undecided}


def _walk_data_quality(token) -> dict:
    """The book's real average and gap tally, accumulated across passes.

    The per-page `average_percent` is a page average; a book average has to be
    rebuilt from the per-customer percents, which every page carries.
    """
    path = READ_ENDPOINTS["data_quality"]
    sections: dict = {}
    gaps: dict = {}
    pct_sum = 0
    examined = 0
    book_total = 0
    offset = 0
    passes = 0
    truncated = False
    while True:
        page = fetch(token, f"{path}?limit=5000&offset={offset}")
        rows = page.get("customers") or []
        book_total = int(page.get("book_total") or book_total)
        for r in rows:
            pct_sum += int(r.get("percent") or 0)
        for sec in page.get("sections") or []:
            t = sections.setdefault(sec.get("title"),
                                    {"filled": 0, "total": 0, "_pcts": []})
            t["filled"] += int(sec.get("filled") or 0)
            t["total"] += int(sec.get("total") or 0)
            if sec.get("percent") is not None:
                t["_pcts"].append(int(sec["percent"]))
        for g in page.get("common_gaps") or []:
            gaps[g.get("label")] = gaps.get(g.get("label"), 0) + int(g.get("count") or 0)
        got = int(page.get("examined", page.get("total_customers")) or 0)
        examined += got
        passes += 1
        if not page.get("has_more") or got == 0:
            break
        if passes >= MAX_PASSES:
            truncated = True
            break
        offset += got
    def _pct(v) -> int:
        # prefer the real ratio; with no denominator, keep what the page REPORTED
        # rather than inventing 100% out of 0/0 — an unknown is not a perfect score
        if v["total"]:
            return round(100 * v["filled"] / v["total"])
        return round(sum(v["_pcts"]) / len(v["_pcts"])) if v["_pcts"] else 100

    merged = [{"title": k, "filled": v["filled"], "total": v["total"],
               "percent": _pct(v)} for k, v in sections.items()]
    out = {
        "total_customers": examined,
        "examined": examined,
        "book_total": book_total,
        "partial": examined < book_total,
        "passes": passes,
        "average_percent": round(pct_sum / examined) if examined else 0,
        "sections": merged,
        "common_gaps": [{"label": k, "count": v} for k, v in
                        sorted(gaps.items(), key=lambda kv: -kv[1])],
    }
    if truncated:
        out["walk_truncated"] = True
    return out


def audit() -> dict:
    if not BASE:
        raise ProdAuditError(
            "SUPERVISOR_API_BASE تنظیم نشده — بدونِ آن نمی‌دانم به کجا وصل شوم"
        )
    token = login()
    out: dict = {"base": BASE, "connected": True, "sections": {}}
    at = _walk_account_type(token)
    dq = _walk_data_quality(token)
    out["sections"]["account_type"] = at.get("summary", {})
    out["sections"]["data_quality"] = {
        "total_customers": dq.get("total_customers"),
        "book_total": dq.get("book_total"),
        "examined": dq.get("examined"),
        "partial": dq.get("partial"),
        "passes": dq.get("passes"),
        "walk_truncated": dq.get("walk_truncated", False),
        "average_percent": dq.get("average_percent"),
        "weakest_section": min(dq.get("sections") or [{"title": None, "percent": 0}],
                               key=lambda s: s.get("percent", 0)).get("title"),
        "top_gaps": [g.get("label") for g in (dq.get("common_gaps") or [])[:5]],
    }
    # v144 — a capped sweep is a SAMPLE. The supervisor reported «3000 customers,
    # 14 conflicts» as the state of the book when the book held 44,608; the number
    # it read was the endpoint's own row limit. Coverage now travels WITH the
    # numbers as an explicit warning, so no later reader can mistake one for the
    # other. See experiences/a-cap-is-not-a-total.md.
    out["coverage"] = _coverage(at.get("summary") or {}, dq)
    # Drive freshness — «configured and connected» says the pipe is open, not that
    # anything went through it. The v136 hole happened while both were true.
    try:
        dr = fetch(token, READ_ENDPOINTS["drive"])
        out["sections"]["drive"] = {
            "configured": dr.get("configured"), "connected": dr.get("connected"),
            "mode": dr.get("mode"), "interval_hours": dr.get("interval_hours"),
            "last_snapshot_at": dr.get("last_snapshot_at"),
            "snapshot_age_hours": dr.get("snapshot_age_hours"),
            "snapshot_overdue": dr.get("snapshot_overdue"),
        }
        if dr.get("snapshot_overdue"):
            age = dr.get("snapshot_age_hours")
            out.setdefault("warnings", []).append(
                "بکاپِ درایو عقب افتاده است — "
                + (f"آخرین snapshot {age} ساعت پیش بود" if age is not None
                   else "هیچ snapshotی ثبت نشده"))
    except Exception as exc:  # noqa: BLE001
        # An ADDED check must never take down the audit it was added to: the
        # account-type and data-quality findings are already gathered by here, and
        # losing them because an optional endpoint is missing or unauthorised
        # would make the run worse than before this check existed. Recorded as
        # «unknown», never as «fine».
        out["sections"]["drive"] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
    return out


def _coverage(at_sum: dict, dq: dict) -> dict:
    """How much of the book each section actually saw, and a warning if partial."""
    def one(label: str, examined, book_total) -> dict:
        ex = int(examined or 0)
        bt = int(book_total or 0)
        item = {"section": label, "examined": ex, "book_total": bt,
                "percent": round(100 * ex / bt) if bt else None,
                "partial": bool(bt and ex < bt)}
        if item["partial"]:
            item["warning"] = (
                f"«{label}» فقط {ex} از {bt} مشتری را دید "
                f"({item['percent']}٪) — این عدد نمونه است، نه کلِ پرونده"
            )
        elif not bt:
            item["warning"] = f"«{label}» اندازهٔ پرونده را نمی‌داند (بک‌اندِ قدیمی؟)"
        return item

    sections = [
        one("بازبینیِ نوعِ حساب", at_sum.get("examined", at_sum.get("total")),
            at_sum.get("book_total")),
        one("کیفیتِ داده", dq.get("examined", dq.get("total_customers")),
            dq.get("book_total")),
    ]
    return {"sections": sections,
            "any_partial": any(s["partial"] for s in sections),
            "warnings": [s["warning"] for s in sections if s.get("warning")]}


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
