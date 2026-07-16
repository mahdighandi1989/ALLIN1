"""Smoke guards that every primary app route still ships a real page component.

Catches the class of regression this task fixed (a route file collapsing into a
broken fragment) across the whole App Router, not just Facilities.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "frontend" / "src" / "app"

EXPECTED_ROUTE_PAGES = [
    "page.tsx",
    "customers/page.tsx",
    "facilities/page.tsx",
    "dashboard/page.tsx",
    "login/page.tsx",
    "reports/page.tsx",
    "settings/page.tsx",
    "users/page.tsx",
    "audit/page.tsx",
    "trash/page.tsx",
    "import/page.tsx",
    "offer-letter/page.tsx",
    "customer-detail/page.tsx",
    "facility-detail/page.tsx",
    "profile/page.tsx",
]


def test_route_pages_exist_and_export_default_component():
    for rel in EXPECTED_ROUTE_PAGES:
        page = APP_DIR / rel
        assert page.exists(), f"route page missing: {rel}"
        src = page.read_text(encoding="utf-8")
        assert "export default" in src, f"no default export in {rel}"


def test_customers_route_is_reachable_from_navigation():
    """/customers is not orphaned: the sidebar nav links to it and the
    customer-detail page routes back to it."""
    layout = (REPO_ROOT / "frontend" / "src" / "components" / "Layout.tsx").read_text(
        encoding="utf-8"
    )
    assert "href: '/customers'" in layout
    detail = (APP_DIR / "customer-detail" / "page.tsx").read_text(encoding="utf-8")
    assert "router.push('/customers')" in detail


def test_list_pages_have_root_testids():
    customers = (APP_DIR / "customers" / "page.tsx").read_text(encoding="utf-8")
    facilities = (APP_DIR / "facilities" / "page.tsx").read_text(encoding="utf-8")
    assert 'data-testid="customers-page"' in customers
    assert 'data-testid="facilities-page"' in facilities
