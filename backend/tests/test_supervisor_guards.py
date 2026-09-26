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


@pytest.fixture()
def inv():
    """The inventory script, loaded as a module (same pattern as `rc`)."""
    assert INV.exists()
    return sys.modules.get("sup_inventory") or _load(INV, "sup_inventory")


class TestMeasurementFailureIsNotZero:
    """v137 — a count that could not be TAKEN must never be reported as 0.

    The supervisor's own rule is that any drop in an inventory count is a serious
    capability-deletion alarm (project rule 2). `backend_routes()` used to catch
    every exception and return `[]`, so a container whose dependencies were not
    installed produced «213 → 0 API routes»: the loudest possible FALSE alarm
    about the product, caused entirely by the environment. A supervisor that
    cries wolf is not read — the run-0 lesson, in the opposite direction.
    """

    def test_import_failure_raises_instead_of_returning_empty(self, inv, monkeypatch):
        class _R:
            returncode = 1
            stdout = ""
            stderr = "ModuleNotFoundError: No module named 'fastapi'"

        monkeypatch.setattr(inv.subprocess, "run", lambda *a, **k: _R())
        with pytest.raises(inv.MeasurementFailed) as e:
            inv.backend_routes()
        # the reason must travel with the error — otherwise the next reader
        # re-diagnoses it from scratch
        assert "fastapi" in str(e.value)

    def test_subprocess_blowing_up_also_raises(self, inv, monkeypatch):
        def _boom(*a, **k):
            raise OSError("no such executable")

        monkeypatch.setattr(inv.subprocess, "run", _boom)
        with pytest.raises(inv.MeasurementFailed):
            inv.backend_routes()

    def test_garbage_payload_raises(self, inv, monkeypatch):
        class _R:
            returncode = 0
            stdout = "@@not json at all"
            stderr = ""

        monkeypatch.setattr(inv.subprocess, "run", lambda *a, **k: _R())
        with pytest.raises(inv.MeasurementFailed):
            inv.backend_routes()

    def test_build_records_the_failure_and_leaves_routes_unmeasured(self, inv, monkeypatch):
        def _fail():
            raise inv.MeasurementFailed("boom")

        monkeypatch.setattr(inv, "backend_routes", _fail)
        built = inv.build()
        assert built["routes"] is None, "None = not measured; 0 would read as «deleted»"
        assert built["totals"]["routes"] is None
        assert built["errors"] and "boom" in built["errors"][0]

    def test_the_markdown_says_unmeasured_rather_than_a_number(self, inv, monkeypatch):
        monkeypatch.setattr(inv, "backend_routes", lambda: (_ for _ in ()).throw(inv.MeasurementFailed("boom")))
        md = inv.to_md(inv.build())
        assert "اندازه‌گیری نشد" in md
        assert "| مسیرهای API | 0 |" not in md

    def test_a_real_zero_is_still_rendered_as_zero(self, inv, monkeypatch):
        """The guard must not swing the other way: an app that genuinely exposes
        no routes still reports 0, because that IS a measurement."""
        monkeypatch.setattr(inv, "backend_routes", lambda: [])
        built = inv.build()
        assert built["routes"] == []
        assert built["totals"]["routes"] == 0
        assert not built["errors"]


class TestRunAllReportsFailures:
    """v137 — `cmd | tail` reports tail's status, which is always 0. Every piped
    step in run_all.sh therefore filed a RED result as green; a pytest that never
    ran ("No module named pytest") was recorded as «exit=0» by the very script
    whose job is to catch red."""

    RUN_ALL = ROOT / "scripts" / "supervisor" / "run_all.sh"

    def test_every_piped_step_sets_pipefail(self):
        for line in self.RUN_ALL.read_text(encoding="utf-8").splitlines():
            if line.startswith("step ") and "|" in line:
                assert "$PF" in line or "pipefail" in line, (
                    f"piped step without pipefail — its exit code is tail's: {line}"
                )

    def test_pipefail_is_actually_defined(self):
        assert "PF='set -o pipefail;'" in self.RUN_ALL.read_text(encoding="utf-8")

    def test_dependencies_are_checked_before_anything_is_measured(self):
        txt = self.RUN_ALL.read_text(encoding="utf-8")
        assert "preflight" in txt
        # preflight must come BEFORE the first measuring step, or it explains
        # nothing about the numbers already printed
        assert txt.index("preflight") < txt.index('step "inventory"')
