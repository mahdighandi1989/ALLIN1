"""Static structural guards for the Facilities/Customers frontend pages.

These do not invoke ``tsc`` (the CI ``frontend`` job already runs
``npm run type-check``); instead they pin the exact, compile-relevant shape the
Facilities page must keep so the previously-broken "fragment only" state can
never regress: a real component export, a React import, and a well-formed
data-loading path built on ``Promise.allSettled``.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FACILITIES = REPO_ROOT / "frontend" / "src" / "app" / "facilities" / "page.tsx"


def _read(path: Path) -> str:
    assert path.exists(), f"expected source file missing: {path}"
    return path.read_text(encoding="utf-8")


def test_facilities_page_is_a_complete_component():
    src = _read(FACILITIES)
    # A real, exported React component (not a stray code fragment).
    assert "export default function FacilitiesPage" in src
    assert "import React from 'react'" in src
    # The page renders, returning JSX rather than ending mid-expression.
    assert "return (<div" in src


def test_facilities_data_loading_uses_allsettled():
    src = _read(FACILITIES)
    assert "Promise.allSettled" in src
    assert "facilitiesResult.status === 'fulfilled'" in src
    # The rejected branch must still be handled (no silent failure).
    assert "facilitiesResult.reason" in src


def test_facilities_does_not_start_with_orphan_fragment():
    """Guard against the original broken state: a bare ``if (...)`` block with
    no component wrapper as the first statement of the file."""
    src = _read(FACILITIES)
    first_code_line = next(
        line.strip()
        for line in src.splitlines()
        if line.strip() and not line.strip().startswith("//")
    )
    assert first_code_line.startswith("'use client'"), first_code_line
    assert not src.lstrip().startswith("if (facilitiesResult")
