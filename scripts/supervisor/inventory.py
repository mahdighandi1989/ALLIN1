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
    try:
        r = subprocess.run([sys.executable, "-c", code], cwd=BE, capture_output=True, text=True, timeout=180)
        line = next((l for l in r.stdout.splitlines() if l.startswith("@@")), "")
        return json.loads(line[2:]) if line else []
    except Exception:
        return []
    finally:
        try:
            (BE / "_sup_inv.db").unlink()
        except Exception:
            pass


def services() -> list[str]:
    return sorted(p.stem for p in (BE / "app" / "services").glob("*.py") if p.stem != "__init__")


def models() -> list[str]:
    return sorted(p.stem for p in (BE / "app" / "models").glob("*.py") if p.stem != "__init__")


def build() -> dict:
    pg, rt = pages(), backend_routes()
    inv = {
        "pages": pg,
        "menu": menu(),
        "api_client": api_client(),
        "routes": rt,
        "services": services(),
        "models": models(),
        "totals": {
            "pages": len(pg),
            "menu_items": len(menu()),
            "buttons": sum(p["buttons"] for p in pg),
            "inputs": sum(p["inputs"] for p in pg),
            "routes": len(rt),
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
        f"| مسیرهای API | {t['routes']} |",
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
    L += ["", "## مسیرهای API", "", "| متد | مسیر |", "|---|---|"]
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
