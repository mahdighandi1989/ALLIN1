"""Lightweight lint-style guards for the touched frontend pages.

The CI ``frontend`` job runs ``next lint`` / ``tsc`` for the authoritative
check; these tests pin a few structural invariants that are cheap to assert
without a Node toolchain so a regression is caught by the Python test suite too.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "frontend" / "src" / "app"


def _discover_pages():
    """Every route entrypoint under the App Router.

    The previous version hard-coded three pages; this enumerates *all* of them
    so that "implement pages" stays honest — a newly added route page is held to
    the same structural invariants automatically, and an incomplete/broken page
    can never slip in unguarded.
    """
    return sorted(APP_DIR.rglob("page.tsx"))


# Every App Router page is a client component in this project.
CLIENT_PAGES = _discover_pages()


def _read(path: Path) -> str:
    assert path.exists(), f"expected source file missing: {path}"
    return path.read_text(encoding="utf-8")


def test_pages_were_discovered():
    # Guard against a silently-empty sweep (e.g. APP_DIR moved): an empty list
    # would make every per-page loop below vacuously pass.
    assert CLIENT_PAGES, f"no page.tsx files found under {APP_DIR}"


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
