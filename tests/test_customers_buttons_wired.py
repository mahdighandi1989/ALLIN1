"""Guards that every <button> on the Customers page is wired to a handler.

Background (AC1 — why this task existed):
The automated stale_detector flagged the Customers "Add Customer" button
(`onClick={() => { setEditingCustomer(null); setShowForm(true) }}`) as a button
"without a handler". `git blame` on that line (commit 7f29d589, 2026-05-30) shows
the handler has been attached since the button was introduced — the detector
tripped on a multi-line JSX attribute and never saw the onClick. So this is
**case (a)**: the handler is present and works; no restore/removal needed.

These tests lock in that conclusion so the false positive cannot become a real
regression: if any interactive <button> in customers/page.tsx ever loses its
onClick (or a placeholder button without one is added), the suite fails.

This mirrors the repo's existing static-guard convention (see
test_all_existing_features.py) rather than introducing a Playwright/Cypress
toolchain the project does not use. It verifies the same observable contract —
each button does something when clicked — by asserting the wiring in source.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CUSTOMERS_PAGE = REPO_ROOT / "frontend" / "src" / "app" / "customers" / "page.tsx"

# A button is "wired" if its opening tag carries an onClick, or it is a native
# form-submit button (type="submit") whose behaviour comes from the enclosing
# <form onSubmit=...>.
_BUTTON_OPEN_TAG = re.compile(r"<button\b[^>]*?>", re.DOTALL)


def _button_open_tags(src: str):
    return _BUTTON_OPEN_TAG.findall(src)


def test_every_button_has_a_handler_or_is_a_submit():
    src = CUSTOMERS_PAGE.read_text(encoding="utf-8")
    tags = _button_open_tags(src)
    assert tags, "expected at least one <button> on the customers page"
    for tag in tags:
        has_onclick = "onClick=" in tag
        is_submit = 'type="submit"' in tag
        assert has_onclick or is_submit, (
            "button without onClick (and not a submit button) found on "
            f"customers page — dead UI regression:\n{tag}"
        )


def test_add_customer_button_opens_the_new_customer_form():
    """The originally-flagged button: clicking it must open a blank form."""
    src = CUSTOMERS_PAGE.read_text(encoding="utf-8")
    assert 'data-testid="add-customer-btn"' in src
    # Opens the form for a *new* customer (clears any editing target first).
    assert "setEditingCustomer(null)" in src
    assert "setShowForm(true)" in src
    # The form modal is actually rendered when showForm is set.
    assert "showForm &&" in src
    assert "<CustomerForm" in src


def test_edit_and_delete_row_buttons_are_wired():
    src = CUSTOMERS_PAGE.read_text(encoding="utf-8")
    # Edit opens the form pre-filled with the row's customer.
    assert "setEditingCustomer(customer); setShowForm(true)" in src
    # Delete invokes the delete handler.
    assert "onClick={() => handleDelete(customer)}" in src


def test_pagination_buttons_are_wired():
    src = CUSTOMERS_PAGE.read_text(encoding="utf-8")
    assert "setPage(p => Math.max(1, p - 1))" in src  # Previous
    assert "setPage(p => p + 1)" in src               # Next
