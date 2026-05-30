"""Tests for app bootstrap edge cases (broken-feedback-loop anti-pattern)."""
import os
import tempfile

from fastapi import FastAPI

from app.main import mount_static_frontend


def test_static_directory_missing_edge_case():
    """A missing static dir must not crash bootstrap; it reports False clearly."""
    app = FastAPI()
    # Missing directory -> not mounted, but no exception (graceful, logged).
    assert mount_static_frontend(app, "/nonexistent/static/dir/xyz") is False
    # No static_frontend route was mounted.
    assert not any(getattr(r, "name", "") == "static_frontend" for r in app.routes)


def test_static_directory_present_is_mounted():
    app = FastAPI()
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write("<html><body>ok</body></html>")
        assert mount_static_frontend(app, d) is True
        assert any(getattr(r, "name", "") == "static_frontend" for r in app.routes)
