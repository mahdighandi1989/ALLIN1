#!/usr/bin/env python3
"""v141 — the supervisor's half of «نظارت و سرکشی».

The owner files a sheet from any screen in the app. The supervisor cannot walk
over and look at it, so this tool is the bridge: it PULLS the queue, writes each
owner screenshot to a real image file the supervisor can OPEN WITH ITS OWN EYES,
renders the text + the exact address into one briefing, POSTS the answer back
under the sheet, and on the next round FILES the sheets the owner has ticked.

    python3 scripts/supervisor/inspection.py pull
    python3 scripts/supervisor/inspection.py answer 7 --text-file /tmp/a.md \
        --outcome fixed --after /tmp/after.png --commit abc1234 \
        --dep "GET /api/customers=ok" --dep "صفحهٔ گزارش‌ها=missing:این فیلتر آنجا نیست"
    python3 scripts/supervisor/inspection.py file

THE FOUR RULES IT ENFORCES (all four were learned the hard way in the sibling
project, where a weak supervisor made the whole board untrustworthy):

  1. **No sheet is left unanswered** — «نشد» is an answer; silence is not. `pull`
     prints what is OWED and exits non-zero while any sheet is still open, so a
     round that ignored the queue cannot look like a clean round.
  2. **`fixed` needs the after-picture.** The API refuses it without one; this
     tool refuses it earlier, with a clearer message.
  3. **The tick is the owner's.** There is deliberately no `approve` command.
  4. **Every answer carries its dependency walk** (`--dep`). The owner asked for
     this by name: «وقتی هر کاری بخواد بکنه وابستگی‌ها رو چک کنه». An answer with
     no dependencies recorded is refused unless `--no-deps` says why.

Authentication is the same as `prod_audit.py`: SUPERVISOR_API_BASE plus either
SUPERVISOR_API_USER/PASSWORD or SUPERVISOR_API_TOKEN.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inspection_view as view  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "supervisor" / "inspection"
SHOTS = OUT_DIR / "shots"
#: v146 — the owner's attached samples, pulled as TEXT so «it is too big» never
#: becomes a reason not to read one. The bytes themselves stay in Drive; what
#: lands here is what the supervisor has to actually read.
FILES = OUT_DIR / "files"
#: v155 — the one urgent sheet this run has claimed.
URGENT = OUT_DIR / "URGENT.md"
BRIEF = OUT_DIR / "QUEUE.md"

BASE = (os.getenv("SUPERVISOR_API_BASE") or "").strip().rstrip("/")
TOKEN = (os.getenv("SUPERVISOR_API_TOKEN") or "").strip()
USER = (os.getenv("SUPERVISOR_API_USER") or "").strip()
PASSWORD = os.getenv("SUPERVISOR_API_PASSWORD") or ""
TIMEOUT = float(os.getenv("SUPERVISOR_API_TIMEOUT", "60"))

OUTCOMES = ("fixed", "partial", "needs-owner", "not-done")


class InspectionError(RuntimeError):
    """Carries WHAT to fix, not just that something failed."""


def _req(path: str, *, data: bytes | None = None, headers: dict | None = None,
         method: str = "GET", timeout: float = TIMEOUT) -> tuple:
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except urllib.error.URLError as e:
        raise InspectionError(
            f"به «{url}» نرسیدم ({e.reason}) — میزبان در Network access محیط مجاز است؟") from e


def login() -> str:
    if TOKEN:
        return TOKEN
    if not (USER and PASSWORD):
        raise InspectionError(
            "نه SUPERVISOR_API_TOKEN تنظیم شده نه SUPERVISOR_API_USER/PASSWORD")
    body = urllib.parse.urlencode({"username": USER, "password": PASSWORD}).encode()
    st, raw = _req("/api/auth/login", data=body,
                   headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    if st != 200:
        raise InspectionError(f"ورود ناموفق بود (HTTP {st}) — SUPERVISOR_API_* درست است؟")
    tok = (json.loads(raw) or {}).get("access_token") or ""
    if not tok:
        raise InspectionError("سرور توکنی برنگرداند")
    return tok


def api(tok: str, path: str, *, body: dict | None = None, method: str = "GET") -> dict:
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {tok}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    st, raw = _req(path, data=data, headers=headers, method=method)
    if st == 404:
        raise InspectionError(f"«{path}» پیدا نشد — هنوز دیپلوی نشده؟")
    if st == 403:
        raise InspectionError(f"«{path}» رد شد (۴۰۳): {_detail(raw)}")
    if st not in (200, 201):
        raise InspectionError(f"«{path}» پاسخِ HTTP {st} داد: {_detail(raw)}")
    return json.loads(raw or b"{}")


def _detail(raw: bytes) -> str:
    try:
        return str((json.loads(raw) or {}).get("detail") or raw[:200])
    except Exception:  # noqa: BLE001
        return str(raw[:200])


def _save_shot(tok: str, shot_id: str, name: str) -> str | None:
    """Write one image to disk so the supervisor can actually look at it."""
    if not shot_id:
        return None
    st, raw = _req(f"/api/inspection/shots/{shot_id}", headers={"Authorization": f"Bearer {tok}"})
    if st != 200 or not raw:
        return None
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / name
    path.write_bytes(raw)
    return str(path.relative_to(ROOT))


def _rel(p: Path) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def ensure_extracted(tok: str, r: dict) -> dict:
    """Every attachment still `pending` (audio/video awaiting its FULL transcript,
    or an archive holding some) is extracted NOW, before the brief is written —
    then the sheet is re-read. An hour of audio takes minutes; that is fine."""
    pending = [f for f in r.get("files") or [] if f.get("extract_status") == "pending"]
    for f in pending:
        st, raw = _req(f"/api/inspection/files/{f['id']}/extract", method="POST",
                       headers={"Authorization": f"Bearer {tok}"}, timeout=1800)
        if st != 200:
            print(json.dumps({"extract_failed": f.get("filename"), "http": st,
                              "detail": _detail(raw)[:300]}, ensure_ascii=False), file=sys.stderr)
    if pending:
        r = api(tok, f"/api/inspection/{r['id']}").get("report") or r
    return r


def _read_file_fully(tok: str, f: dict, report_number: int) -> dict:
    """Pull ONE attached sample completely, and write it where it can be read.

    «کامل» is the operative word. The text arrives in slices and the server counts
    what it served, so a partial pull leaves a debt that blocks the answer — which
    is the point. This walks to the end, and says so.

    For a file with no text (image, scanned PDF, .doc) the bytes are fetched
    instead: fetching them IS «looked at it», and the server records that too.
    """
    FILES.mkdir(parents=True, exist_ok=True)
    fid = f.get("id") or ""
    name = f.get("filename") or fid
    status = f.get("extract_status") or ""
    safe = re.sub(r"[^\w.\-() ]+", "_", name)[:120]
    out = {"filename": name, "extract_status": status, "chars": 0, "path": "",
           "complete": False, "note": f.get("extract_note") or ""}

    if status == "ok":
        text = ""
        offset = 0
        # big bites on purpose: this is a machine reading, and 40k-char slices
        # turned a 20M-character sample into 500 round trips
        step = int(os.getenv("SUPERVISOR_READ_SLICE", "2000000"))
        for _ in range(500):          # bounded: a runaway loop must end
            st, raw = _req(f"/api/inspection/files/{fid}/text?offset={offset}&limit={step}",
                           headers={"Authorization": f"Bearer {tok}"})
            if st != 200:
                out["note"] = f"خواندنِ متن شکست خورد: HTTP {st}"
                break
            page = json.loads(raw.decode("utf-8"))
            text += page.get("text") or ""
            if not page.get("has_more"):
                out["complete"] = bool(page.get("fully_read"))
                break
            offset = int(page.get("next_offset") or 0)
        path = FILES / f"r{report_number}-{safe}.txt"
        path.write_text(text, encoding="utf-8")
        out.update(chars=len(text), path=str(path.relative_to(ROOT)))
        # complete text — but an archive's pictures/videos, a video's picture and
        # a PDF's pages must ALSO be looked at, so those fetch the bytes too
        if not f.get("text_truncated") and not view.needs_bytes(name):
            return out
        # The text was cut at a ceiling, so it is NOT the whole file. Reading it
        # all does not discharge the duty — the file itself has to be opened,
        # and that is what the server counts. Fall through and fetch it.
        out["note"] = ((out["note"] + " | ") if out["note"] else "") + \
            "متنش بریده شده بود، پس خودِ فایل هم گرفته شد — بقیه‌اش فقط در آن است"
        out["complete"] = False

    # No text to read — so OPEN it, which is what «read it» means for these.
    st, raw = _req(f"/api/inspection/files/{fid}/raw",
                   headers={"Authorization": f"Bearer {tok}"}, timeout=600)
    if st == 200 and raw:
        path = FILES / f"r{report_number}-{safe}"
        path.write_bytes(raw)
        out.update(raw_path=str(path.relative_to(ROOT)), complete=True)
        out.setdefault("path", "")
        if not out["path"]:
            out.update(path=str(path.relative_to(ROOT)), chars=len(raw))
        extra, better = view.look_notes(path, name, status, _rel)
        if better is not None:
            out["raw_path"] = _rel(better)
        if extra:
            out["note"] = (out["note"] + " | " if out["note"] else "") + " | ".join(extra)
    else:
        out["note"] = (out["note"] + " | " if out["note"] else "") + \
            f"گرفتنِ خودِ فایل نشد: HTTP {st}"
    return out


def where_block(r: dict) -> list:
    """WHERE the owner pointed — the same answer in every brief.

    v171 — this existed only inside `cmd_pull`, and the URGENT brief (which is
    the path a rushed sheet actually takes) carried nothing but the page name and
    a pair of document pixels. So a round answering «**در اینجا** یه باکس دستور
    بذار» never saw which element the box landed on, let alone where inside it,
    and put the new control «above the form». One description, used by both
    briefs, is the fix — a second copy is how they drifted apart in the first
    place.
    """
    out = []
    out.append(f"- کجا: **{r.get('page_label')}**"
               + (f" ← {r['section_label']}" if r.get("section_label") else ""))
    out.append(f"- نشانیِ بازگشت: `{r.get('reopen')}`")
    if r.get("dom_path"):
        out.append(f"- عنصر: `{r['dom_path']}`")
    if r.get("covered_text"):
        out.append(f"- آنچه در کادر بود: {r['covered_text']}")
    g = r.get("geometry") or {}
    if not g:
        return out
    d = g.get("doc") or {}
    vp = g.get("viewport") or {}
    a = g.get("anchor") or {}
    anch = a.get("path") or ""
    rel, arect = a.get("rel") or {}, a.get("rect") or {}
    out.append(
        f"- **مختصات:** {round(d.get('w', 0))}×{round(d.get('h', 0))} پیکسل در "
        f"x={round(d.get('x', 0))} y={round(d.get('y', 0))} (مختصاتِ سند) · "
        f"پنجره {vp.get('w')}×{vp.get('h')}"
        + (f" · dpr {g.get('dpr')}" if g.get("dpr") not in (None, 1) else ""))
    out.append(
        f"- **گره:** `{anch}` — با تغییرِ چیدمان هم همان‌جا می‌ماند"
        if anch else
        "- **گره:** به عنصری گره نخورد؛ فقط مختصاتِ سند معتبر است "
        "(اگر چیدمان عوض شده باشد، جای کادر تقریبی است)")
    # THE PART THAT WAS RECORDED AND NEVER READ.
    #
    # Document pixels say where the box was in a 1352-pixel window last Tuesday.
    # They do NOT say «here», and «here» is the whole reason for drawing a box.
    # The fractions do: the box's place INSIDE the element it landed on, which
    # survives every resize and reflow and is the only form of this that can be
    # acted on. They were measured, stored and shipped — and left out of the
    # brief.
    if anch and (rel.get("w") or rel.get("h")):
        pc = lambda v: f"{round(float(v or 0) * 100)}٪"
        # `rel.x` is measured from the element's LEFT edge, because that is how
        # every browser coordinate is measured — the page being RTL changes what
        # the reader sees, not what x means. Calling it «from the right» (as the
        # first version of this line did) mirrors every box that is not centred.
        out.append(
            f"- **جای دقیق داخلِ همان گره:** از **لبهٔ چپِ** گره {pc(rel.get('x'))}، "
            f"از **بالای** گره {pc(rel.get('y'))} · اندازهٔ کادر {pc(rel.get('w'))} "
            f"عرض و {pc(rel.get('h'))} ارتفاعِ گره "
            f"(خودِ گره {round(float(arect.get('w') or 0))}×"
            f"{round(float(arect.get('h') or 0))} پیکسل بود)")
        out.append(
            f"  - یعنی روی خودِ صفحه: از لبهٔ چپِ گره "
            f"{round(float(rel.get('x') or 0) * float(arect.get('w') or 0))} پیکسل و "
            f"از بالای گره {round(float(rel.get('y') or 0) * float(arect.get('h') or 0))} "
            f"پیکسل — صفحه راست‌به‌چپ است ولی مختصات مثلِ همیشه از چپ شمرده می‌شود.")
        out.append(
            "  > این کسرها «همان‌جا» را می‌گویند و با تغییرِ اندازهٔ پنجره هم "
            "معتبرند. اگر خواسته «این را اینجا بگذار» است، جایش **همین** است — "
            "نه «بالای فرم»، نه «کنارِ نزدیک‌ترین دکمه». اگر واقعاً همان‌جا ممکن "
            "نیست، در جواب بنویس کجا گذاشتی و **چرا نشد**، و نتیجه را `partial` "
            "بگذار نه `fixed`. (قاعدهٔ کامل: بخشِ ۰-ب-۴ در PROMPT.md)")
    return out


def cmd_pull() -> int:
    tok = login()
    q = api(tok, "/api/inspection/queue")
    reports = [ensure_extracted(tok, r) for r in q.get("reports") or []]
    import shutil
    for d in (SHOTS, FILES):          # unpacked archives and video frames are folders
        if d.exists():
            shutil.rmtree(d)
    lines = [
        "# کارتابلِ «نظارت و سرکشی»",
        "",
        f"- بدهیِ این دور (**باید همین دور جواب بگیرند**): **{q.get('owed', 0)}**",
        f"  - تازه و بی‌پاسخ: {q.get('unanswered', q.get('owed', 0))}",
        f"  - **نیمه‌کاره/درست‌نشده — ادامهٔ کارِ دورِ قبل**: {q.get('unfinished', 0)}"
        + (f" (برگه‌های {'، '.join(str(n) for n in q.get('unfinished_numbers') or [])})"
           if q.get('unfinished_numbers') else ""),
        f"- پاسخ‌داده‌شده و تمام، منتظرِ تیکِ مالک: {q.get('waiting_for_owner', 0)}",
        f"- تأییدشده و آمادهٔ بایگانی: {q.get('to_file', 0)}",
        "",
        "> **برگهٔ نیمه‌کاره تمام‌شده نیست.** `partial` یعنی «بقیه‌اش مانده» و",
        "> `not-done` یعنی «هنوز کارِ نکرده دارد» — هر دو همین دور برمی‌گردند و",
        "> باید ادامه پیدا کنند، نه اینکه دوباره همان توضیح نوشته شود. اگر واقعاً",
        "> راهی نیست، `needs-owner` با گزینه‌های مشخص بگذار تا بماند دستِ مالک.",
        "",
        "> تصویرها در `shots/` هستند. **بازشان کن و نگاه کن** — تمامِ نکتهٔ این",
        "> سامانه این است که مالک چیزی را *دیده* که تست‌ها نمی‌بینند.",
        "",
        f"- فایل‌های نمونه‌ای که باید خوانده شوند: **{q.get('files_to_read', 0)}**",
        "",
        "> فایل‌های پیوست در `files/` نوشته شده‌اند — متنِ **کاملشان**، نه خلاصه.",
        "> «حجمش زیاد است» عذر نیست: متن تکه‌تکه خوانده شد و سرور شمرد. تا صفر",
        "> نشدنِ این عدد، API جوابِ برگه را نمی‌پذیرد.",
        "",
    ]
    for r in reports:
        lines += [
            f"## گزارشِ {r['number']} — {r['title']}",
            "",
            f"- وضعیت: `{r['status']}` · {r.get('glow', {}).get('label', '')}",
        ]
        lines += where_block(r)
        lines.append("")
        for i, n in enumerate(r.get("notes") or []):
            who = "🤖 ناظر" if n.get("by") == "reviewer" else "👤 مالک"
            lines += [f"**{who}** — {n.get('at', '')}", "", n.get("text", ""), ""]
            for key, tag in (("shot_id", "before"), ("after_shot_id", "after")):
                sid = n.get(key)
                if sid:
                    p = _save_shot(tok, sid, f"r{r['number']}-n{i}-{tag}.img")
                    if p:
                        lines.append(f"تصویر: `{p}`")
            if n.get("commits"):
                lines.append("کامیت‌ها: " + " · ".join(n["commits"]))
            lines.append("")
        if r.get("files"):
            lines.append("**فایل‌های نمونهٔ مالک — متنِ کاملشان خوانده شد:**")
            lines.append("")
            for f in r["files"]:
                got = _read_file_fully(tok, f, r["number"])
                mark = "✅" if got["complete"] else "⚠️"
                lines.append(
                    f"- {mark} `{got['filename']}` ({f.get('size_label', '')}, "
                    f"{f.get('extract_label') or got['extract_status']})")
                if f.get("caption"):
                    lines.append(f"  - توضیحِ مالک: {f['caption']}")
                if got["path"]:
                    lines.append(f"  - محتوا: `{got['path']}`"
                                 + (f" — {got['chars']} نویسه" if got["chars"] else ""))
                if got.get("raw_path") and got.get("raw_path") != got["path"]:
                    lines.append(f"  - خودِ فایل: `{got['raw_path']}` — **بازش کن**")
                if got["note"]:
                    lines.append(f"  - {got['note']}")
                if not f.get("durable", True):
                    lines.append("  - ⚠️ روی درایو ذخیره نشده (با دیپلویِ بعدی پاک می‌شود) — "
                                 "همین دور بخوانش و به مالک بگو درایو تنظیم نیست")
            lines.append("")
        if r.get("dependencies"):
            lines.append("**وابستگی‌های بررسی‌شده:**")
            for d in r["dependencies"]:
                lines.append(f"- {d.get('status')} — {d.get('name')} {d.get('note') or ''}")
            lines.append("")
        lines.append("---")
        lines.append("")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BRIEF.write_text("\n".join(lines), encoding="utf-8")
    # Re-ask after the reads: `files_to_read` from before the pull is the DEBT,
    # and what matters afterwards is whether anything is still outstanding.
    left = api(tok, "/api/inspection/queue").get("files_to_read", 0)
    print(json.dumps({"owed": q.get("owed", 0),
                      "unanswered": q.get("unanswered", q.get("owed", 0)),
                      "unfinished": q.get("unfinished", 0),
                      "unfinished_numbers": q.get("unfinished_numbers") or [],
                      "waiting_for_owner": q.get("waiting_for_owner", 0),
                      "to_file": q.get("to_file", 0),
                      "files_read": q.get("files_to_read", 0), "files_still_unread": left,
                      "brief": str(BRIEF.relative_to(ROOT))},
                     ensure_ascii=False))
    # A round that leaves the queue untouched must not look like a clean round.
    return 4 if q.get("owed", 0) else 0


def cmd_urgent() -> int:
    """v155 — the fast queue: what the owner asked for OUT of turn.

    Prints one sheet at a time, oldest request first, and CLAIMS it so a second
    run does not answer the same sheet — the owner's «بدون اینکه به تناقض بخوره».
    Exits 0 with nothing to say when the queue is empty, which is the normal case
    and must stay cheap: this runs often.

    EXIT CODES — and the distinction that matters:
        0  the queue is EMPTY. Nothing to do, say nothing.
        5  a sheet is claimed and waiting for an answer.
        3  the queue could NOT BE READ (server down, mid-deploy, bad credentials).

    3 is deliberately not 0. «I could not look» and «there was nothing there»
    produce the same silence if they share an exit code, and an hourly routine
    that cannot reach the queue would then look exactly like an hourly routine
    finding it empty — for as long as it stayed broken. Same lesson as
    `experiences/a-monitor-must-distinguish-unmeasured-from-zero.md`.
    """
    tok = login()
    got = api(tok, "/api/inspection/urgent/claim", body={"by": "routine"}, method="POST")
    r = got.get("report")
    if r:
        r = ensure_extracted(tok, r)
    if not r:
        busy = got.get("busy", 0)
        print(json.dumps({"claimed": None, "waiting": got.get("waiting", 0),
                          "in_progress_elsewhere": busy}, ensure_ascii=False))
        return 0
    FILES.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# فوری — گزارشِ {r['number']}: {r['title']}",
        "",
        "> مالک این را **خارج از نوبت** خواسته است. همین حالا انجامش بده، بعد",
        "> جوابش را با `inspection.py answer` بنویس. تا جواب ندهی از صفِ فوری",
        "> بیرون نمی‌رود، و بقیهٔ صف پشتِ آن منتظرند.",
        "",
        f"- وضعیت: `{r['status']}` · {r.get('glow', {}).get('label', '')}",
    ]
    lines += where_block(r)
    lines += [f"- در صف: {got.get('waiting', 1)} برگه", ""]
    for i, n in enumerate(r.get("notes") or []):
        who = "🤖 ناظر" if n.get("by") == "reviewer" else "👤 مالک"
        lines += [f"**{who}** — {n.get('at', '')}", "", n.get("text", ""), ""]
        for key, tag in (("shot_id", "before"), ("after_shot_id", "after")):
            sid = n.get(key)
            if sid:
                pth = _save_shot(tok, sid, f"urgent-r{r['number']}-n{i}-{tag}.img")
                if pth:
                    lines.append(f"تصویر: `{pth}` — **بازش کن و نگاه کن**")
        lines.append("")
    for f in r.get("files") or []:
        got_f = _read_file_fully(tok, f, r["number"])
        mark = "✅" if got_f["complete"] else "⚠️"
        lines.append(f"- {mark} `{got_f['filename']}` — محتوا: `{got_f['path']}`")
        if f.get("caption"):
            lines.append(f"  - توضیحِ مالک: {f['caption']}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    URGENT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"claimed": r["number"], "waiting": got.get("waiting", 1),
                      "brief": str(URGENT.relative_to(ROOT))}, ensure_ascii=False))
    return 5


def _parse_dep(raw: str) -> dict:
    """`name=status` or `name=status:note`."""
    name, _, rest = raw.partition("=")
    status, _, note = rest.partition(":")
    return {"name": name.strip(), "status": (status or "ok").strip(), "note": note.strip()}


def _data_url(path: str) -> str:
    raw = Path(path).read_bytes()
    ext = Path(path).suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp"}.get(ext)
    if not mime:
        raise InspectionError(f"فرمتِ «{ext}» پشتیبانی نمی‌شود (png/jpg/webp)")
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


#: Words an owner uses when the REQUEST IS ABOUT A PLACE. A sheet whose text
#: contains one of these, and which carries an anchored box, cannot be closed
#: with «fixed» until the answer says where the thing was actually put.
PLACE_WORDS = (
    "در اینجا", "اینجا", "همین‌جا", "همینجا", "در این قسمت", "این قسمت",
    "این محل", "در این محل", "همین قسمت", "همین بخش", "این نقطه",
)


def asks_for_a_place(report: dict) -> bool:
    """v172 — is this sheet about WHERE, and does it actually point somewhere?

    Both halves matter. «اینجا» with no anchored box is a sentence the round
    cannot act on precisely, and an anchored box on a request that never mentions
    a place (a wording fix, a calculation) must not drag this guard in.
    """
    anchored = bool((((report.get("geometry") or {}).get("anchor") or {}).get("path")))
    if not anchored:
        return False
    said = " ".join(n.get("text", "") for n in (report.get("notes") or [])
                    if n.get("by") != "reviewer")
    return any(w in said for w in PLACE_WORDS)


def cmd_answer(args) -> int:
    tok = login()
    text = args.text or (Path(args.text_file).read_text(encoding="utf-8") if args.text_file else "")
    if not text.strip():
        raise InspectionError("متنِ جواب خالی است — «نشد» هم باید نوشته شود")
    if args.outcome not in OUTCOMES:
        raise InspectionError(f"نتیجه باید یکی از این‌ها باشد: {', '.join(OUTCOMES)}")
    if args.outcome == "fixed" and not args.after:
        raise InspectionError(
            "«fixed» بدونِ تصویرِ بعدش پذیرفته نیست. یا `--after <عکس>` بده، "
            "یا نتیجه را `partial`/`not-done` بگذار. ادعای بی‌مدرک، برگه را سبزِ دروغین می‌کند.")
    deps = [_parse_dep(d) for d in (args.dep or [])]
    if not deps and not args.no_deps:
        raise InspectionError(
            "هیچ وابستگی‌ای ثبت نشد. برای هر کاری باید زنجیرهٔ وابستگی‌اش بررسی شود "
            "(`--dep 'نام=ok|missing|risk:توضیح'`). اگر واقعاً وابستگی ندارد، `--no-deps` بده.")

    lst = api(tok, "/api/inspection?include_filed=true")
    target = next((r for r in lst.get("reports", []) if r["number"] == args.number), None)
    if target is None:
        raise InspectionError(f"گزارشِ {args.number} پیدا نشد")

    # v172 — «دقیقاً در محلی که خواستم کار انجام نشده و سلیقه رفتی».
    #
    # A round once closed a «put it HERE» sheet as `fixed` and admitted a round
    # later that it had not looked at the coordinates at all. The existing guard
    # only asks for a picture, and a picture of the wrong place still passes. So
    # when the sheet both names a place and carries an anchored box, the answer
    # has to SAY where it put the thing, in its own words, before `fixed` is
    # allowed. It is one short line, it goes into the answer the owner reads, and
    # it cannot be produced without having decided the question.
    place = (getattr(args, "place", "") or "").strip()
    if args.outcome == "fixed" and asks_for_a_place(target) and not place:
        raise InspectionError(
            "این برگه «جا» خواسته (کادر کشیده شده و متن می‌گوید «اینجا»). "
            "برای «fixed» باید `--place \"…\"` بدهی و در یک جمله بنویسی دقیقاً "
            "کجا گذاشتی‌اش — مثلاً «داخلِ همان ردیفِ دکمه‌ها، بعد از پاک‌کردن». "
            "اگر همان‌جا ممکن نشد، نتیجه `partial` است و دلیلش را بنویس. "
            "«یک جای نزدیک» با نتیجهٔ fixed یعنی گزارشِ غلط.")

    if place:
        text = f"{text.rstrip()}\n\n**جایی که گذاشته شد:** {place}"

    body = {"text": text.strip(), "outcome": args.outcome,
            "commits": args.commit or [], "dependencies": deps}
    if args.after:
        body["after_shot"] = _data_url(args.after)
    res = api(tok, f"/api/inspection/{target['id']}/notes", body=body, method="POST")
    print(json.dumps({"ok": True, "number": args.number,
                      "status": res["report"]["status"],
                      "glow": res["report"]["glow"]["label"]}, ensure_ascii=False))
    return 0


def cmd_file() -> int:
    tok = login()
    res = api(tok, "/api/inspection/file", body={}, method="POST")
    print(json.dumps({"filed": res.get("filed", 0)}, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="«نظارت و سرکشی» — the supervisor's side")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pull", help="کارتابل + تصویرها")
    a = sub.add_parser("answer", help="جواب زیرِ یک برگه")
    a.add_argument("number", type=int)
    a.add_argument("--text")
    a.add_argument("--text-file")
    a.add_argument("--outcome", required=True, choices=OUTCOMES)
    a.add_argument("--after", help="تصویرِ بعد از اصلاح — برای «fixed» اجباری")
    a.add_argument("--commit", action="append")
    a.add_argument("--dep", action="append",
                   help="'نام=ok|missing|risk:توضیح' — تکرارشدنی")
    a.add_argument("--no-deps", action="store_true",
                   help="فقط وقتی واقعاً هیچ وابستگی‌ای ندارد")
    a.add_argument("--place", default="",
                   help="یک جمله: دقیقاً کجا گذاشته شد — برای برگه‌ای که «جا» خواسته "
                        "و «fixed» می‌گیرد اجباری است")
    sub.add_parser("file", help="تیک‌خورده‌ها → زونکن")
    sub.add_parser("urgent", help="یک برگهٔ فوری را بردار (صفِ خارج از نوبت)")
    args = ap.parse_args()

    if not BASE:
        print(json.dumps({"error": "SUPERVISOR_API_BASE تنظیم نشده"}, ensure_ascii=False))
        return 3
    try:
        if args.cmd == "pull":
            return cmd_pull()
        if args.cmd == "answer":
            return cmd_answer(args)
        if args.cmd == "urgent":
            return cmd_urgent()
        return cmd_file()
    except InspectionError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
