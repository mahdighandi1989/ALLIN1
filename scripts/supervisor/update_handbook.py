#!/usr/bin/env python3
"""Regenerate docs/supervisor/HANDBOOK.md — the system map and the progress charts.

Everything here is DERIVED (from inventory.json + runs.jsonl), so the handbook can
never drift away from the code the way a hand-written map does. Diagrams are
Mermaid, which GitHub renders natively.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUP = ROOT / "docs" / "supervisor"
OUT = SUP / "HANDBOOK.md"


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_runs() -> list[dict]:
    p = SUP / "runs.jsonl"
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def xychart(title: str, runs: list[dict], key: str, ylabel: str) -> str:
    """A Mermaid xychart of one metric over the last runs (skipped when thin)."""
    pts = [(r.get("date", "")[:10], r.get(key)) for r in runs if isinstance(r.get(key), (int, float))]
    pts = pts[-14:]
    if len(pts) < 2:
        return f"> _نمودارِ «{title}» بعد از دومین اجرا ساخته می‌شود._\n"
    labels = ", ".join(f'"{d[5:]}"' for d, _ in pts)
    vals = ", ".join(str(v) for _, v in pts)
    hi = max(v for _, v in pts)
    return (
        "```mermaid\n"
        "xychart-beta\n"
        f'    title "{title}"\n'
        f"    x-axis [{labels}]\n"
        f'    y-axis "{ylabel}" 0 --> {max(1, int(hi * 1.2) + 1)}\n'
        f"    line [{vals}]\n"
        "```\n"
    )


def main() -> None:
    inv = load_json(SUP / "inventory.json", {"totals": {}, "menu": [], "pages": []})
    runs = load_runs()
    t = inv.get("totals", {})
    last = runs[-1] if runs else {}
    prev = runs[-2] if len(runs) > 1 else {}

    def delta(key):
        a, b = last.get(key), prev.get(key)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return ""
        d = a - b
        return "" if d == 0 else (f" (▲{d})" if d > 0 else f" (▼{abs(d)})")

    L: list[str] = []
    L += [
        "# جزوهٔ ناظرِ خودکار — نقشهٔ سامانه و روندِ پیشرفت",
        "",
        f"> ساخته‌شده به‌صورت **خودکار** در {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC — دستی ویرایش نکن.",
        f"> منبع: `inventory.json` + `runs.jsonl` · تعدادِ اجراهای ثبت‌شده: **{len(runs)}**",
        "",
        "## ۱) سامانه در یک نگاه",
        "",
        "| سنجه | مقدار |",
        "|---|---|",
        f"| صفحه‌ها | {t.get('pages', '—')} |",
        f"| آیتم‌های منو | {t.get('menu_items', '—')} |",
        f"| دکمه‌ها | {t.get('buttons', '—')} |",
        f"| ورودی‌ها | {t.get('inputs', '—')} |",
        f"| مسیرهای API | {t.get('routes', '—')} |",
        f"| متدهای کلاینتِ API | {t.get('api_methods', '—')} |",
        f"| سرویس‌های بک‌اند | {t.get('services', '—')} |",
        f"| مدل‌های داده | {t.get('models', '—')} |",
        "",
        "## ۲) معماری",
        "",
        "```mermaid",
        "flowchart RL",
        '    U["کاربر — مرورگر"] --> FE["Next.js 14<br/>static export · RTL"]',
        '    FE -->|build| ST["backend/static"]',
        '    ST --> API["FastAPI<br/>app/main.py"]',
        '    FE -->|axios · lib/api.ts| API',
        '    API --> SVC["services/<br/>excel_import · doc_ingest · amortization<br/>fx · telegram · backup · completeness"]',
        '    SVC --> DB[("PostgreSQL<br/>(dev/test: SQLite)")]',
        '    SVC --> DRV["Google Drive<br/>بکاپ و پیوست‌ها"]',
        '    SVC --> AI["مدل‌های هوش مصنوعی<br/>استخراجِ اسناد"]',
        '    API --> MT["تلگرام (دوطرفه)"]',
        "```",
        "",
        "## ۳) منوها و صفحه‌ها",
        "",
        "```mermaid",
        "flowchart TD",
        '    ROOT["منوی کناری"]',
    ]
    for i, m in enumerate(inv.get("menu", [])):
        lbl = str(m.get("label", "")).replace('"', "'")
        L.append(f'    ROOT --> M{i}["{lbl}<br/><code>{m.get("href", "")}</code>"]')
    L += ["```", ""]

    L += [
        "## ۴) چرخهٔ خودِ ناظر",
        "",
        "```mermaid",
        "flowchart LR",
        '    A["pull + خواندنِ<br/>experiences و RUNLOG"] --> B["inventory.py<br/>فهرستِ سطح"]',
        '    B --> C["تست‌ها<br/>pytest · jest · build"]',
        '    C --> D["runtime_check.py<br/>بالا آوردن + کلیکِ واقعی"]',
        '    D --> E["db_audit.py<br/>بازرسیِ بدبینانه"]',
        '    E --> F["اصلاح + تست + کامیت/پوش"]',
        '    F --> G["RUNLOG · runs.jsonl<br/>OPEN_ITEMS · HANDBOOK"]',
        '    G --> H["گزارشِ خلاصه به مالک"]',
        "```",
        "",
        "## ۵) روندِ پیشرفت",
        "",
    ]
    L += ["### سلامتِ اجرا", "", xychart("مشکلاتِ باز در هر اجرا", runs, "open_issues", "مورد")]
    L += ["### پوششِ تست", "", xychart("تعدادِ تست‌های سبز", runs, "tests_passed", "تست")]
    L += ["### کیفیتِ داده", "", xychart("میانگینِ کاملیِ پروفایل‌ها (٪)", runs, "data_quality_avg", "درصد")]
    L += ["### گسترشِ سامانه", "", xychart("تعدادِ مسیرهای API", runs, "routes", "مسیر")]

    L += ["", "## ۶) آخرین اجرا", ""]
    if last:
        L += [
            "| سنجه | مقدار |",
            "|---|---|",
            f"| تاریخ | {last.get('date', '—')} |",
            f"| وضعیت | {last.get('status', '—')} |",
            f"| تست‌های سبز | {last.get('tests_passed', '—')}{delta('tests_passed')} |",
            f"| صفحه‌های بررسی‌شده | {last.get('pages_checked', '—')} |",
            f"| دکمه‌های کلیک‌شده | {last.get('buttons_clicked', '—')} |",
            f"| endpointهای بررسی‌شده | {last.get('endpoints_checked', '—')} |",
            f"| مشکلاتِ باز | {last.get('open_issues', '—')}{delta('open_issues')} |",
            f"| دیتابیسِ بازرسی‌شده | {last.get('database', '—')} |",
            "",
        ]
    else:
        L += ["> هنوز اجرایی ثبت نشده است.", ""]

    L += [
        "## ۷) کجا چه چیزی است",
        "",
        "| فایل | نقش |",
        "|---|---|",
        "| `docs/supervisor/PROMPT.md` | دستورِ کاملِ ناظر (نسخه‌دار) |",
        "| `docs/supervisor/archive/` | نسخه‌های قبلیِ دستور |",
        "| `docs/supervisor/RUNLOG.md` | گزارشِ هر اجرا |",
        "| `docs/supervisor/OPEN_ITEMS.md` | کارهای بازِ انتقالی |",
        "| `docs/supervisor/runs.jsonl` | سنجه‌های هر اجرا (منبعِ نمودارها) |",
        "| `docs/supervisor/INVENTORY.md` | فهرستِ خودکارِ سطحِ سامانه |",
        "| `scripts/supervisor/` | اسکریپت‌هایی که ناظر اجرا می‌کند |",
        "",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"handbook updated: {OUT.relative_to(ROOT)} ({len(runs)} runs)")


if __name__ == "__main__":
    main()
