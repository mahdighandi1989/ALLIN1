"""v135 — guards on the automated supervisor itself.

The supervisor clicks real buttons in a real browser with full authority to
commit and push. Two things must therefore be true and stay true: it must never
click a destructive control, and it must not report as a fault something that is
supposed to fail. Both are pinned here.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RC = ROOT / "scripts" / "supervisor" / "runtime_check.py"
INV = ROOT / "scripts" / "supervisor" / "inventory.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rc():
    assert RC.exists()
    return _load(RC, "sup_runtime_check")


DESTRUCTIVE_LABELS = [
    "حذف", "حذفِ این جدولِ پیوست", "پاک‌کردن", "بازنشانی", "↺ بازنشانی",
    "ارسال", "🖨 پرینت", "دانلود PDF", "خروج", "Delete", "Remove all", "Reset layout",
    "Clear", "Send", "Download", "Backup now", "restore", "اجرا", "اعمال", "مرج",
]
SAFE_LABELS = [
    "ذخیره", "ذخیرۀ چیدمان", "✥ چیدمان", "بستن", "جست‌وجو", "به‌روزرسانی",
    "نامۀ جدید", "دستیارِ هوشمند", "پیوست‌ها", "↩ برگشت", "Save", "Search",
    "Open", "Next", "جدول", "تصویر",
]


class TestDestructiveGuard:
    @pytest.mark.parametrize("label", DESTRUCTIVE_LABELS)
    def test_never_clicks_a_destructive_control(self, rc, label):
        assert rc.DESTRUCTIVE.search(label), f"the supervisor would CLICK «{label}»"

    @pytest.mark.parametrize("label", SAFE_LABELS)
    def test_still_exercises_the_harmless_ones(self, rc, label):
        assert not rc.DESTRUCTIVE.search(label), f"«{label}» is safe but would be skipped"

    def test_an_empty_label_is_treated_as_safe_to_click(self, rc):
        # icon-only buttons carry no text; skipping them all would gut the sweep
        assert not rc.DESTRUCTIVE.search("")


class TestExpectedFailures:
    def test_the_deliberate_error_probe_is_not_reported_as_a_fault(self, rc):
        assert "/api/simulate-unhandled-error" in rc.EXPECTED_5XX

    def test_the_allowlist_stays_tiny(self, rc):
        # every entry here is a fault the supervisor will never tell anyone about
        assert len(rc.EXPECTED_5XX) <= 3


class TestBudgets:
    def test_the_sweep_is_bounded_so_a_scheduled_run_finishes(self, rc):
        assert 0 < rc.MAX_CLICKS <= 40
        assert 0 < rc.PAGE_CLICK_BUDGET_S <= 60
        assert 0 < rc.PAGE_GOTO_MS <= 60000

    def test_slow_is_not_reported_as_dead(self, rc):
        """A single tight probe once reported 14 healthy pages as fatal."""
        src = RC.read_text(encoding="utf-8")
        assert "proc.poll() is not None" in src, "must distinguish an exited process"
        assert 'entry["severity"] = "warning"' in src, "unresponsive-but-running is a warning"


class TestInventory:
    def test_it_finds_a_real_surface(self):
        inv = _load(INV, "sup_inventory")
        pages = inv.pages()
        assert len(pages) > 20
        assert sum(p["buttons"] for p in pages) > 100
        assert any(p["route"] == "/voucher" for p in pages)

    def test_the_menu_is_read_from_the_layout_the_user_sees(self):
        inv = sys.modules.get("sup_inventory") or _load(INV, "sup_inventory")
        menu = inv.menu()
        assert len(menu) > 10
        assert any(m["href"] == "/import" for m in menu)
        assert all(m["label"] for m in menu)
