#!/usr/bin/env python3
"""EXERCISE the app — do not merely read it.

Boots the real FastAPI app on a throwaway SQLite database, then:
  1. calls every parameter-free GET endpoint and records its status;
  2. opens every page of the built frontend in a real Chromium, and for each one
     records console errors, failed network requests, whether the page actually
     rendered, and how many buttons/inputs it exposes;
  3. CLICKS every safe button on every page (anything not matching a destructive
     word) and re-checks for errors — a page that renders but throws on the first
     click is broken, and only clicking finds that.

Writes docs/supervisor/last_runtime.json. Exit code is 0 even when problems are
found: the caller decides what to do with them.
"""
from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BE = ROOT / "backend"
OUT = ROOT / "docs" / "supervisor" / "last_runtime.json"
CHROME = "/opt/pw-browsers/chromium"
# A SCHEDULED run must finish. These bound the sweep so 30+ pages stay inside
# minutes instead of the better part of an hour (measured: an unbounded sweep
# with 40 clicks/page and networkidle waits ran past 20 minutes).
MAX_CLICKS = int(os.getenv("SUPERVISOR_MAX_CLICKS", "18"))
PAGE_CLICK_BUDGET_S = float(os.getenv("SUPERVISOR_PAGE_BUDGET", "25"))
PAGE_GOTO_MS = int(os.getenv("SUPERVISOR_GOTO_MS", "15000"))

# Never click anything whose label/title suggests it destroys or sends.
# Endpoints whose whole purpose is to fail (monitoring probes). A supervisor that
# reports these every week trains the reader to ignore it.
EXPECTED_5XX = {"/api/simulate-unhandled-error"}

DESTRUCTIVE = re.compile(
    r"حذف|پاک|بازنشانی|ریست|خالی|remove|delete|clear|reset|drop|"
    r"ارسال|بفرست|send|submit|ثبت نهایی|مرج|merge|اجرا|apply|اعمال|"
    r"پرینت|print|دانلود|download|خروج|logout|sign ?out|backup|بکاپ|restore|بازیابی",
    re.I,
)


def _tail_log(n: int = 60) -> str:
    try:
        return "\n".join((ROOT / "docs" / "supervisor" / "last_server.log")
                          .read_text(encoding="utf-8", errors="replace").splitlines()[-n:])
    except Exception:
        return ""


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_server(port: int):
    db = BE / "_supervisor_run.db"
    for suffix in ("", "-wal", "-shm"):
        try:
            Path(str(db) + suffix).unlink()
        except Exception:
            pass
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///./{db.name}",
        "AUTH_DISABLED": "true",          # the supervisor tests the SURFACE, not the login wall
        "ENVIRONMENT": "development",
        "DEBUG": "false",
        "GOOGLE_DRIVE_ENABLED": "false",  # never touch the owner's real Drive from a smoke run
    }
    # The server's own output goes to a FILE, not a pipe: when a page kills the
    # backend, its traceback is the whole finding, and a pipe that nobody drains
    # can itself block the process.
    log = ROOT / "docs" / "supervisor" / "last_server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    LOG_FH = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "info"],
        cwd=BE, env=env, stdout=LOG_FH, stderr=subprocess.STDOUT, text=True,
    )
    base = f"http://127.0.0.1:{port}"
    import urllib.request
    for _ in range(120):
        if proc.poll() is not None:
            return proc, base, False
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as r:
                if r.status == 200:
                    return proc, base, True
        except Exception:
            time.sleep(1)
    return proc, base, False


def check_endpoints(base: str, routes: list[dict]) -> list[dict]:
    import urllib.error
    import urllib.request
    out = []
    for r in routes:
        path = r["path"]
        if "{" in path or "GET" not in r["methods"]:
            continue
        if not (path.startswith("/api") or path in ("/health",)):
            continue
        try:
            req = urllib.request.Request(base + path, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                code, body = resp.status, resp.read(2000)
        except urllib.error.HTTPError as e:
            code, body = e.code, e.read(2000)
        except Exception as e:  # connection died = a real failure, record it
            out.append({"path": path, "status": 0, "error": f"{type(e).__name__}: {e}"[:200]})
            continue
        # 401/403 are legitimate answers (a guarded route), 404 on an optional
        # resource is not necessarily a fault; 5xx always is.
        out.append({"path": path, "status": code, "bytes": len(body)})
    return out


def _alive(base: str, proc=None) -> dict:
    """SLOW is not DEAD. A single tight probe reported "this page killed the
    backend" for a server that was merely busy — a supervisor that cries wolf
    gets ignored, so this retries with backoff and separates the two cases:
    a process that has EXITED is critical; one that is just late is a warning."""
    import time as _t
    import urllib.request
    if proc is not None and proc.poll() is not None:
        return {"alive": False, "exited": True, "returncode": proc.returncode}
    for attempt, timeout in enumerate((8, 12, 20)):
        try:
            with urllib.request.urlopen(base + "/health", timeout=timeout) as r:
                return {"alive": r.status == 200, "exited": False, "attempts": attempt + 1}
        except Exception:
            _t.sleep(1.5)
    return {"alive": False, "exited": False, "attempts": 3}


PROC: list = [None]   # set by main() so page checks can tell slow from dead


def check_pages(base: str, page_routes: list[str]) -> list[dict]:
    """One FRESH context per page: a page that leaks timers, opens a modal or
    wedges its tab must not be able to fail the pages after it — the first run
    of this sweep showed exactly that pattern (17 pages fine, then every
    remaining page timing out), and a shared context cannot tell the two apart.
    Liveness of the SERVER is probed between pages, so "this page takes the
    backend down" is reported as the finding it is."""
    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-gpu"])
        for route in page_routes:
            ctx = browser.new_context(viewport={"width": 1366, "height": 900}, ignore_https_errors=True)
            errs: list[str] = []
            failed: list[str] = []
            page = ctx.new_page()
            page.on("console", lambda m: errs.append(m.text[:300]) if m.type == "error" else None)
            page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"[:300]))
            page.on("requestfailed", lambda r: failed.append(f"{r.method} {r.url.split('?')[0]}"[:200]))
            entry = {"route": route}
            try:
                page.goto(base + route, wait_until="domcontentloaded", timeout=PAGE_GOTO_MS)
                page.wait_for_timeout(900)
                body = (page.inner_text("body") or "").strip()
                entry["rendered"] = len(body) > 40
                entry["text_len"] = len(body)
                entry["buttons"] = page.locator("button:visible").count()
                entry["inputs"] = page.locator("input:visible, select:visible, textarea:visible").count()
                # --- CLICK every safe visible button, then re-check ---
                clicked = skipped = 0
                n = min(entry["buttons"], MAX_CLICKS)
                deadline = time.time() + PAGE_CLICK_BUDGET_S
                for i in range(n):
                    if time.time() > deadline:
                        entry["click_budget_hit"] = True
                        break
                    b = page.locator("button:visible").nth(i)
                    try:
                        label = ((b.inner_text(timeout=800) or "") + " " + (b.get_attribute("title") or "")).strip()
                    except Exception:
                        continue
                    if DESTRUCTIVE.search(label):
                        skipped += 1
                        continue
                    try:
                        b.click(timeout=1200, no_wait_after=True)
                        clicked += 1
                        page.wait_for_timeout(60)
                        # a click may open a modal that covers the rest; close it
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
                entry["clicked"] = clicked
                entry["skipped_destructive"] = skipped
                page.wait_for_timeout(400)
            except Exception as e:
                entry["rendered"] = False
                entry["error"] = f"{type(e).__name__}: {e}"[:300]
            # the app's own axios noise against a bare DB is expected; keep the
            # raw list so a human can judge, but count only the loud ones
            entry["console_errors"] = errs[:12]
            entry["console_error_count"] = len(errs)
            entry["request_failures"] = sorted(set(failed))[:12]
            health = _alive(base, PROC[0])
            entry["server_alive_after"] = health["alive"]
            if health.get("exited"):
                entry["severity"] = "critical"          # this page took the backend DOWN
                entry["server_exited_rc"] = health.get("returncode")
            elif not health["alive"]:
                entry["severity"] = "warning"           # unresponsive, but still running
            results.append(entry)
            try:
                page.close()
                ctx.close()
            except Exception:
                pass
        browser.close()
    return results


def main() -> int:
    inv_path = ROOT / "docs" / "supervisor" / "inventory.json"
    if not inv_path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "supervisor" / "inventory.py")], check=False)
    inv = json.loads(inv_path.read_text(encoding="utf-8"))
    page_routes = [p["route"] for p in inv["pages"] if p["route"] not in ("/",)]

    port = free_port()
    proc, base, up = start_server(port)
    PROC[0] = proc
    report: dict = {"base": base, "server_started": up}
    try:
        if not up:
            report["server_log"] = _tail_log()
        else:
            report["endpoints"] = check_endpoints(base, inv["routes"])
            report["pages"] = check_pages(base, page_routes)
    finally:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=20)
        except Exception:
            proc.kill()
        for suffix in ("", "-wal", "-shm"):
            try:
                Path(str(BE / "_supervisor_run.db") + suffix).unlink()
            except Exception:
                pass

    # If a page took the backend down, the server's last words are the evidence.
    pgs_dead = [p for p in report.get("pages", []) if p.get("severity") == "critical"]
    if pgs_dead:
        report["killed_by"] = pgs_dead[0]["route"]
        report["server_exit_code"] = proc.returncode
        report["server_log_tail"] = _tail_log()

    eps = report.get("endpoints", [])
    pgs = report.get("pages", [])
    report["summary"] = {
        "endpoints_checked": len(eps),
        "endpoints_5xx": sum(1 for e in eps if (e.get("status") or 0) >= 500 and e["path"] not in EXPECTED_5XX),
        "endpoints_5xx_expected": sum(1 for e in eps if e["path"] in EXPECTED_5XX),
        "endpoints_dead": sum(1 for e in eps if e.get("status") == 0),
        "pages_checked": len(pgs),
        "pages_blank": sum(1 for p in pgs if not p.get("rendered")),
        "pages_with_console_errors": sum(1 for p in pgs if p.get("console_error_count")),
        "pages_that_killed_the_server": sum(1 for p in pgs if p.get("severity") == "critical"),
        "pages_after_which_server_was_slow": sum(1 for p in pgs if p.get("severity") == "warning"),
        "buttons_clicked": sum(p.get("clicked", 0) for p in pgs),
        "buttons_skipped_destructive": sum(p.get("skipped_destructive", 0) for p in pgs),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
