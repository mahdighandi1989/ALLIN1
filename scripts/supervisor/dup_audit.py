#!/usr/bin/env python3
"""v11 — «is the same thing recorded more than once, in different places?»

Owner (2026-10-01, sheet 8): «مهمه که ناظر بره ببینه چیزهایی تکراری چند بار در
جاهای مختلف ثبت نشده باشه — این خیلی مهمه».

The in-app cleanup scan (``/api/cleanup/scan``) is a POST and works one entity at
a time; the supervisor is GET-only by construction. This reads the admin JSON
export (``GET /api/crm/backup/export.json`` — the same file the Drive backup
writes) and looks for the SAME fact appearing twice:

* inside one account (two identical cheques / deposits / deeds / partners /
  files), and
* ACROSS accounts (one cheque number, deed, deposit, file hash, licence,
  passport or Emirates ID filed under several accounts; one exact name under
  several accounts).

It is deliberately conservative (CLAUDE.md: «در شک، duplicate اعلام نکن»): a
finding is ``certain`` only where the key is a real identifier AND the scope is
one account; everything cross-account is ``review`` — a person can legitimately
be a partner of two companies, so it is a list for a human, never a licence to
delete. Nothing is written to production. Examples carry account numbers only.

Exit codes: 0 ok · 3 production unreachable (never report «no duplicates»).
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "supervisor" / "last_dup_audit.json"
EXPORT_PATH = "/api/crm/backup/export.json"
MAX_EXAMPLES = 10

_WS = re.compile(r"[\s‌]+")
_PUNCT = re.compile(r"[^\w؀-ۿ ]+", re.UNICODE)


def norm(v) -> str:
    """Case/space/punctuation-insensitive form of a name or identifier."""
    s = _PUNCT.sub(" ", str(v or "")).upper()
    return _WS.sub(" ", s).strip()


def idnorm(v) -> str:
    """Identifier form: letters+digits only, so «P-123 456» == «p123456»."""
    return re.sub(r"[\W_]+", "", str(v or ""), flags=re.UNICODE).upper()


def _live(rows):
    return [r for r in rows or [] if not r.get("is_deleted")]


def _group(rows, key):
    g = defaultdict(list)
    for r in rows:
        k = key(r)
        if k:
            g[k].append(r)
    return g


def _finding(rule, level, scope, groups, extra=""):
    dup = {k: v for k, v in groups.items() if len(v) > 1}
    return {
        "rule": rule, "level": level, "scope": scope, "note": extra,
        "groups": len(dup),
        "rows": sum(len(v) for v in dup.values()),
        "examples": [
            {"accounts": sorted({str(r.get("account_no") or "") for r in v})[:6], "count": len(v)}
            for v in list(dup.values())[:MAX_EXAMPLES]
        ],
    }


def find_duplicates(data: dict) -> dict:
    """``data`` is the export's ``data`` object (table name → rows)."""
    out = []
    cust = _live(data.get("customers"))
    # certain — one account number must be one customer
    out.append(_finding("customers: same account_no twice", "certain", "global",
                        _group(cust, lambda r: norm(r.get("account_no")))))
    # review — identical name under different accounts (min length avoids «ABC»)
    by_name = _group(cust, lambda r: norm(r.get("name")) if len(norm(r.get("name"))) >= 8 else "")
    by_name = {k: v for k, v in by_name.items() if len({norm(r.get("account_no")) for r in v}) > 1}
    out.append(_finding("customers: identical name under several accounts", "review", "cross-account", by_name,
                        "may be a genuine second account — a list for a person, not a deletion"))

    for table, field, label in (("guarantors", "cheque_no", "cheque"),
                                ("securities", "cheque_no", "security cheque")):
        rows = _live(data.get(table))
        out.append(_finding(f"{table}: same {label} twice in one account", "probable", "account",
                            _group(rows, lambda r, f=field: (norm(r.get("account_no")), idnorm(r.get(f)))
                                   if idnorm(r.get(f)) and norm(r.get("account_no")) else None)))
        cross = _group(rows, lambda r, f=field: idnorm(r.get(f)) if len(idnorm(r.get(f))) >= 4 else "")
        cross = {k: v for k, v in cross.items() if len({norm(r.get("account_no")) for r in v}) > 1}
        out.append(_finding(f"{table}: same {label} number under several accounts", "review", "cross-account", cross))

    fds = _live(data.get("fixed_deposits"))
    out.append(_finding("fixed_deposits: same deposit twice in one account", "certain", "account",
                        _group(fds, lambda r: (norm(r.get("account_no")), norm(r.get("fd_number")))
                               if norm(r.get("fd_number")) and norm(r.get("account_no")) else None)))
    cross = {k: v for k, v in _group(fds, lambda r: norm(r.get("fd_number"))).items()
             if len({norm(r.get("account_no")) for r in v}) > 1}
    out.append(_finding("fixed_deposits: same deposit number under several accounts", "review", "cross-account", cross))

    props = _live(data.get("mortgaged_properties"))
    pkey = lambda r: norm(r.get("mortgage_deed_no")) or ""  # noqa: E731
    out.append(_finding("mortgaged_properties: same deed twice in one account", "probable", "account",
                        _group(props, lambda r: (norm(r.get("account_no")), pkey(r))
                               if pkey(r) and norm(r.get("account_no")) else None)))
    cross = {k: v for k, v in _group(props, pkey).items()
             if len({norm(r.get("account_no")) for r in v}) > 1}
    out.append(_finding("mortgaged_properties: same deed under several accounts", "review", "cross-account", cross))

    partners = _live(data.get("partners"))
    out.append(_finding("partners: same person twice in one account", "probable", "account",
                        _group(partners, lambda r: (norm(r.get("account_no")), norm(r.get("name")))
                               if len(norm(r.get("name"))) >= 4 and norm(r.get("account_no")) else None),
                        "same name in one company; could be a role split — check before merging"))

    atts = [a for a in data.get("attachments") or [] if (a.get("content_sha256") or "").strip()]
    out.append(_finding("attachments: identical file twice in one account", "certain", "account",
                        _group(atts, lambda r: (norm(r.get("account_no")), r["content_sha256"]))))
    cross = {k: v for k, v in _group(atts, lambda r: r["content_sha256"]).items()
             if len({norm(r.get("account_no")) for r in v}) > 1}
    out.append(_finding("attachments: identical file under several accounts", "review", "cross-account", cross))

    profs = data.get("customer_profiles") or []
    for field in ("trade_license_no", "passport_no", "emirates_id_no"):
        g = {k: v for k, v in _group(profs, lambda r, f=field: idnorm(r.get(f)) if len(idnorm(r.get(f))) >= 5 else "").items()
             if len({norm(r.get("account_no")) for r in v}) > 1}
        out.append(_finding(f"customer_profiles: same {field} under several accounts", "review", "cross-account", g,
                            "one document number on two accounts: duplicate customer, or a shared identity"))

    return {
        "tables_seen": sorted(k for k, v in data.items() if v),
        "findings": out,
        "certain_groups": sum(f["groups"] for f in out if f["level"] == "certain"),
        "review_groups": sum(f["groups"] for f in out if f["level"] != "certain"),
    }


def _download(dest: Path) -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    import prod_audit  # same login + proxy handling; GET-only

    token = prod_audit.login()
    req = urllib.request.Request(prod_audit.BASE + EXPORT_PATH,
                                 headers={"Authorization": f"Bearer {token}"}, method="GET")
    with urllib.request.urlopen(req, timeout=600, context=prod_audit._ctx()) as resp, open(dest, "wb") as fh:  # noqa: S310
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)


def main() -> int:
    src = os.getenv("SUPERVISOR_EXPORT_FILE")
    tmp = None
    try:
        if not src:
            fd, tmp = tempfile.mkstemp(suffix=".json", prefix="export-")
            os.close(fd)
            _download(Path(tmp))
            src = tmp
        data = json.loads(Path(src).read_text(encoding="utf-8")).get("data") or {}
    except Exception as exc:  # noqa: BLE001 - unreachable must never read as «clean»
        OUT.write_text(json.dumps({"reachable": False, "error": f"{type(exc).__name__}: {exc}"[:300]},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dup_audit: production export not readable — {exc}", file=sys.stderr)
        return 3
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)  # the export holds customer data — never leave it on disk
    result = find_duplicates(data)
    result["reachable"] = True
    result["row_counts"] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"certain_groups": result["certain_groups"], "review_groups": result["review_groups"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
