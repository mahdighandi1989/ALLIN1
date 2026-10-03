#!/usr/bin/env python3
"""v11 — pick a ROTATING sample of accounts whose source files should be re-read.

Owner (2026-10-01, sheet 8): the supervisor should periodically go back to the
files the owner gave, look again, and check that what was extracted is right AND
sits in the right field. This script only CHOOSES and LAYS OUT the comparison;
the looking is the supervisor's job (PROMPT §2-ز) — a script cannot read a scan.

Read-only: one GET of the admin export, nothing written to production. The
export is deleted after use; the sample (which contains customer values) is
printed to stdout only and never committed.

The sample rotates by ISO week so successive runs cover different accounts
instead of re-checking the same lucky few. ``SUPERVISOR_SAMPLE_SIZE`` (default 8).
Exit 3 when production cannot be read — never «nothing to check».
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dup_audit  # noqa: E402  (reuses the GET-only download)

#: profile fields that are the usual «right value, wrong place» victims
WATCH = ("passport_no", "passport_issue", "passport_expiry", "emirates_id_no", "emirates_id_expiry",
         "visa_no", "visa_issue", "visa_expiry", "visa_type", "trade_license_no", "trade_license_issue",
         "trade_license_expiry", "tenancy_no", "tenancy_expiry", "national_id", "business_type", "account_type")


def pick(data: dict, n: int, week: str) -> list[dict]:
    """Accounts that HAVE a stored file and a profile, ordered by a week-salted hash."""
    atts: dict[str, list] = {}
    for a in data.get("attachments") or []:
        acc = str(a.get("account_no") or "").strip()
        if acc and acc != "cust-unknown" and (a.get("drive_file_id") or a.get("file_path")):
            atts.setdefault(acc, []).append(a)
    profs = {str(p.get("account_no") or ""): p for p in data.get("customer_profiles") or []}
    cands = [acc for acc in atts if acc in profs]
    cands.sort(key=lambda acc: hashlib.sha256(f"{week}:{acc}".encode()).hexdigest())
    out = []
    for acc in cands[:n]:
        p = profs[acc]
        out.append({
            "account_no": acc,
            "profile": {k: p.get(k) for k in WATCH if p.get(k) not in (None, "")},
            "files": [{"id": a["id"], "name": a.get("original_name") or a.get("file_name"),
                       "download": f"/api/crm/attachments/{a['id']}/download"} for a in atts[acc][:6]],
        })
    return out


def main() -> int:
    n = int(os.getenv("SUPERVISOR_SAMPLE_SIZE", "8"))
    week = dt.date.today().strftime("%G-W%V")
    src = os.getenv("SUPERVISOR_EXPORT_FILE")
    tmp = None
    try:
        if not src:
            fd, tmp = tempfile.mkstemp(suffix=".json", prefix="export-")
            os.close(fd)
            dup_audit._download(Path(tmp))
            src = tmp
        data = json.loads(Path(src).read_text(encoding="utf-8")).get("data") or {}
    except Exception as exc:  # noqa: BLE001
        print(f"extraction_sample: production export not readable — {exc}", file=sys.stderr)
        return 3
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    sample = pick(data, n, week)
    print(json.dumps({"week": week, "requested": n, "picked": len(sample),
                      "accounts_with_files": len({a.get("account_no") for a in data.get("attachments") or []}),
                      "sample": sample}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
