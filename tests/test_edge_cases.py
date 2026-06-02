"""Edge-case guards for the root redirect shim (frontend/src/app/page.tsx).

The home page redirects to /dashboard or /login based on client-only auth
state. A naive implementation breaks in three edge cases; these tests pin that
the source keeps handling all three.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_PAGE = REPO_ROOT / "frontend" / "src" / "app" / "page.tsx"


def _read(path: Path) -> str:
    assert path.exists(), f"expected source file missing: {path}"
    return path.read_text(encoding="utf-8")


def test_redirect_edge_cases():
    src = _read(HOME_PAGE)

    # Edge case 1: auth still loading -> must bail out before redirecting so we
    # don't bounce an authenticated user to /login on first paint.
    assert "if (loading) return" in src

    # Edge case 2: server-side render / no window -> localStorage access guarded.
    assert "typeof window !== 'undefined'" in src
    assert "localStorage.getItem('token')" in src

    # Edge case 3: authDisabled (demo mode) or an existing user/token is treated
    # as authenticated and sent to the dashboard; everyone else to login.
    assert "authDisabled || user || token" in src
    assert "router.replace('/dashboard')" in src
    assert "router.replace('/login')" in src


def test_redirect_uses_replace_not_push():
    """Redirect must not leave the transient landing page in history."""
    src = _read(HOME_PAGE)
    # router.replace is used for the actual navigation...
    assert "router.replace(" in src
    # ...and there is no live router.push call (only referenced in the comment
    # that documents the deliberate replace-vs-push choice).
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        assert "router.push(" not in stripped, stripped
