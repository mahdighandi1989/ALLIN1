#!/usr/bin/env python3
"""Enumerate EVERY surface of the app from source — pages, menu entries, buttons,
API routes, API-client methods — so the supervisor knows what it is supposed to
exercise, and so anything ADDED later shows up automatically without editing a
list by hand.

Writes docs/supervisor/inventory.json (machine) and docs/supervisor/INVENTORY.md
(human). Read-only with respect to the app.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FE = ROOT / "frontend" / "src"
BE = ROOT / "backend"
OUT_JSON = ROOT / "docs" / "supervisor" / "inventory.json"
OUT_MD = ROOT / "docs" / "supervisor" / "INVENTORY.md"


class MeasurementFailed(RuntimeError):
    """A count could not be TAKEN. Distinct from a count that legitimately is 0 —
    conflating the two turns an environment problem into a false report that the
    product lost a capability."""


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def pages() -> list[dict]:
    """Every Next.js App-Router page, with the interactive controls it carries."""
    out = []
    for f in sorted((FE / "app").rglob("page.tsx")):
        rel = f.relative_to(FE / "app")
        route = "/" + str(rel.parent).replace(os.sep, "/")
        if route == "/.":
            route = "/"
        src = _read(f)
        out.append({
            "route": route,
            "file": str(f.relative_to(ROOT)),
            "lines": src.count("\n") + 1,
            "buttons": len(re.findall(r"<button\b", src)),
            "onclick": len(re.findall(r"onClick=", src)),
            "inputs": len(re.findall(r"<(input|textarea|select)\b", src)),
            "forms": len(re.findall(r"<form\b", src)),
            "links": len(re.findall(r"<Link\b", src)),
            "api_calls": len(re.findall(r"\b\w+Api\.\w+\(", src)),
        })
    return out


def menu() -> list[dict]:
    """The sidebar as the user sees it — the authoritative list of entry points."""
    src = _read(FE / "components" / "Layout.tsx")
    items = re.findall(r"\{\s*href:\s*'([^']+)',\s*label:\s*'([^']+)'", src)
    return [{"href": h, "label": l} for h, l in items]


def api_client() -> list[dict]:
    """Every method the frontend can call, grouped by its api object."""
    src = _read(FE / "lib" / "api.ts")
    out, current = [], "?"
    for line in src.splitlines():
        m = re.match(r"export const (\w+)\s*=\s*\{", line)
        if m:
            current = m.group(1)
            continue
        m = re.match(r"\s{2}async\s+(\w+)\s*\(", line)
        if m:
            out.append({"group": current, "method": m.group(1)})
    return out


def backend_routes() -> list[dict]:
    """Ask FastAPI itself — never a regex over the routers, which would miss any
    route added through a decorator the pattern does not know about."""
    code = (
        "import json,os;"
        "os.environ.setdefault('DATABASE_URL','sqlite+aiosqlite:///./_sup_inv.db');"
        "os.environ.setdefault('AUTH_DISABLED','true');"
        "os.environ.setdefault('ENVIRONMENT','development');"
        "from app.main import app;"
        "print('@@'+json.dumps([{'path':r.path,'methods':sorted(getattr(r,'methods',[]) or []),"
        "'name':getattr(r,'name','')} for r in app.routes]))"
    )
    # v137 — NEVER return [] on failure. "0 routes" and "could not measure" look
    # identical in the totals, and the supervisor's own rule says a DROP in any
    # count is a serious capability-deletion alarm. A recycled container with no
    # dependencies installed therefore produced "213 → 0 API routes", i.e. the
    # loudest possible FALSE alarm about the product, from a problem in the
    # environment. Raise instead, so the caller reports «اندازه‌گیری نشد».
    try:
        try:
            r = subprocess.run([sys.executable, "-c", code], cwd=BE,
                               capture_output=True, text=True, timeout=180)
        except Exception as e:                                 # noqa: BLE001
            raise MeasurementFailed(f"could not run the app import: {e}") from e
        line = next((l for l in r.stdout.splitlines() if l.startswith("@@")), "")
        if not line:
            tail = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
            raise MeasurementFailed(
                "importing app.main produced no route list (exit=%s): %s"
                % (r.returncode, " / ".join(tail) or "no output")
            )
        try:
            return json.loads(line[2:])
        except Exception as e:                                 # noqa: BLE001
            raise MeasurementFailed(f"route list was not valid JSON: {e}") from e
    finally:
        # the throwaway probe DB is removed on EVERY path, including the ones
        # that raise — otherwise a failed measurement leaves a file behind that
        # the next run has to reason about
        try:
            (BE / "_sup_inv.db").unlink()
        except Exception:
            pass


def services() -> list[str]:
    return sorted(p.stem for p in (BE / "app" / "services").glob("*.py") if p.stem != "__init__")


def models() -> list[str]:
    return sorted(p.stem for p in (BE / "app" / "models").glob("*.py") if p.stem != "__init__")


def build() -> dict:
    pg = pages()
    errors: list[str] = []
    try:
        rt = backend_routes()
    except MeasurementFailed as e:
        rt = None                       # None = not measured; 0 would mean «deleted»
        errors.append(f"routes: {e}")
    inv = {
        "pages": pg,
        "menu": menu(),
        "api_client": api_client(),
        "errors": errors,
        "routes": rt,
        "services": services(),
        "models": models(),
        "totals": {
            "pages": len(pg),
            "menu_items": len(menu()),
            "buttons": sum(p["buttons"] for p in pg),
            "inputs": sum(p["inputs"] for p in pg),
            "routes": len(rt) if rt is not None else None,
            "api_methods": len(api_client()),
            "services": len(services()),
            "models": len(models()),
        },
    }
    return inv


def to_md(inv: dict) -> str:
    t = inv["totals"]
    L = [
        "# فهرستِ سطحِ سامانه (Inventory)",
        "",
        "> این فایل را **ناظرِ خودکار** در هر اجرا بازتولید می‌کند — دستی ویرایشش نکن.",
        "> هر صفحه/دکمه/endpointی که بعداً اضافه شود، خودکار این‌جا ظاهر می‌شود.",
        "",
        "| سنجه | تعداد |",
        "|---|---|",
        f"| صفحه‌ها | {t['pages']} |",
        f"| آیتم‌های منو | {t['menu_items']} |",
        f"| دکمه‌ها | {t['buttons']} |",
        f"| ورودی‌ها (input/select/textarea) | {t['inputs']} |",
        f"| مسیرهای API | {t['routes'] if t['routes'] is not None else '⚠️ اندازه‌گیری نشد'} |",
        f"| متدهای کلاینتِ API | {t['api_methods']} |",
        f"| سرویس‌ها | {t['services']} |",
        f"| مدل‌ها | {t['models']} |",
        "",
        "## منوی کناری",
        "",
        "| مسیر | برچسب |",
        "|---|---|",
    ]
    for m in inv["menu"]:
        L.append(f"| `{m['href']}` | {m['label']} |")
    L += ["", "## صفحه‌ها و کنترل‌هایشان", "",
          "| مسیر | خط | دکمه | ورودی | لینک | فراخوانیِ API |", "|---|---|---|---|---|---|"]
    for p in inv["pages"]:
        L.append(f"| `{p['route']}` | {p['lines']} | {p['buttons']} | {p['inputs']} | {p['links']} | {p['api_calls']} |")
    if inv.get("errors"):
        L += ["", "## ⚠️ سنجه‌هایی که اندازه‌گیری نشدند", "",
              "> این‌ها **صفر نیستند** — اندازه‌گیری‌شان شکست خورد. آن را با «حذفِ",
              "> قابلیت» اشتباه نگیر؛ اول محیط را درست کن و دوباره اجرا کن.", ""]
        for e in inv["errors"]:
            L.append(f"- {e}")
    L += ["", "## مسیرهای API", "", "| متد | مسیر |", "|---|---|"]
    if inv["routes"] is None:
        L.append("| — | ⚠️ اندازه‌گیری نشد (به بخشِ بالا نگاه کن) |")
    else:
        for r in sorted(inv["routes"], key=lambda x: x["path"]):
            if r["path"].startswith("/api") or r["path"] in ("/health", "/"):
                L.append(f"| {','.join(r['methods'])} | `{r['path']}` |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    inv = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text(to_md(inv), encoding="utf-8")
    print(json.dumps(inv["totals"], ensure_ascii=False))
    # v137 — exit NON-ZERO when something could not be measured, so run_all.sh
    # and the reading supervisor see a failed step instead of a plausible-looking
    # table with a hole in it.
    if inv.get("errors"):
        for e in inv["errors"]:
            print(f"MEASUREMENT FAILED — {e}", file=sys.stderr)
        sys.exit(2)
