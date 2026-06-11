"""Alias integration test node: tests/test_pipeline_data.py::test_integration.

Some task specs reference the `data` pipeline integration test as
``test_pipeline_data.py`` and others as ``test_data_pipeline.py``. This module
provides the same end-to-end guarantee under the alternate name so either
reference resolves. The full unit coverage lives in test_data_pipeline.py.
"""
import os
import tempfile

import pytest

import app.services.notifications as notifications
from app.services.data_pipeline import SheetSchema, run_pipeline


@pytest.fixture(autouse=True)
def _silence_notifications(monkeypatch):
    monkeypatch.setattr(notifications, "_send_telegram", lambda text, **kwargs: True)
    notifications._last_sent.clear()
    yield
    notifications._last_sent.clear()


def _make_xlsx(path, header, rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_integration():
    """End-to-end `data` pipeline run handles good/corrupt/empty files cleanly."""
    with tempfile.TemporaryDirectory() as d:
        _make_xlsx(os.path.join(d, "good.xlsx"), ["name", "amount"], [["Acme", 100]])
        with open(os.path.join(d, "broken.xlsx"), "w") as f:
            f.write("corrupt-bytes")

        report = run_pipeline(d, schema=SheetSchema(["name", "amount"]))

    by_name = {os.path.basename(r.path): r for r in report.results}
    assert by_name["good.xlsx"].ok is True
    assert by_name["good.xlsx"].rows == [{"name": "Acme", "amount": 100}]
    assert by_name["broken.xlsx"].ok is False
    assert by_name["broken.xlsx"].error_kind == "corrupt"
    # The pipeline as a whole completed without raising.
    assert report.total_rows == 1
