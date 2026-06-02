"""Lightweight lint-style guards for the touched frontend pages.

The CI ``frontend`` job runs ``next lint`` / ``tsc`` for the authoritative
check; these tests pin a few structural invariants that are cheap to assert
without a Node toolchain so a regression is caught by the Python test suite too.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "frontend" / "src" / "app"

CLIENT_PAGES = [
    APP_DIR / "facilities" / "page.tsx",
    APP_DIR / "customers" / "page.tsx",
    APP_DIR / "page.tsx",
]


def _read(path: Path) -> str:
    assert path.exists(), f"expected source file missing: {path}"
    return path.read_text(encoding="utf-8")


def test_client_pages_declare_use_client():
    for page in CLIENT_PAGES:
        src = _read(page)
        assert src.lstrip().startswith("'use client'"), page


def test_pages_export_a_default_component():
    for page in CLIENT_PAGES:
        src = _read(page)
        assert "export default function" in src, page


def test_no_leftover_debugging_artifacts():
    for page in CLIENT_PAGES:
        src = _read(page)
        assert "debugger" not in src, page
        assert "console.log(" not in src, page
