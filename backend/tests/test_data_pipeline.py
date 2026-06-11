"""Tests for the robust Excel data pipeline (app.services.data_pipeline)."""
import os
import tempfile

import pytest

import app.services.notifications as notifications
from app.services import data_pipeline as dp
from app.services.data_pipeline import (
    PipelineError,
    SheetSchema,
    load_rows,
    process_file,
    run_pipeline,
    export_to_csv,
)


@pytest.fixture(autouse=True)
def _silence_notifications(monkeypatch):
    """Don't hit Telegram and don't rate-limit across pipeline tests."""
    monkeypatch.setattr(notifications, "_send_telegram", lambda text, **kwargs: True)
    notifications._last_sent.clear()
    yield
    notifications._last_sent.clear()


def _make_xlsx(path: str, header, data_rows):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for r in data_rows:
        ws.append(r)
    wb.save(path)


def test_load_valid_xlsx_returns_records():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "good.xlsx")
        _make_xlsx(p, ["name", "amount"], [["Acme", 100], ["Beta", 200]])
        rows = load_rows(p)
    assert rows == [
        {"name": "Acme", "amount": 100},
        {"name": "Beta", "amount": 200},
    ]


def test_corrupt_file_raises_pipeline_error():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "broken.xlsx")
        with open(p, "w") as f:
            f.write("not really a spreadsheet")
        with pytest.raises(PipelineError) as ei:
            load_rows(p)
    assert ei.value.kind == "corrupt"


def test_empty_workbook_detected():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "empty.xlsx")
        _make_xlsx(p, [], [])  # no header row
        with pytest.raises(PipelineError) as ei:
            load_rows(p)
    assert ei.value.kind == "empty"


def test_invalid_format_rejected():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "data.txt")
        with open(p, "w") as f:
            f.write("nope")
        with pytest.raises(PipelineError) as ei:
            load_rows(p)
    assert ei.value.kind == "invalid_format"


def test_schema_validation_flags_missing_columns():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "s.xlsx")
        _make_xlsx(p, ["name"], [["Acme"]])
        result = process_file(p, schema=SheetSchema(required_columns=["name", "amount"]))
    assert result.ok is False
    assert result.error_kind == "schema"


def test_process_file_never_raises_and_reports():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "broken.xlsm")
        with open(p, "w") as f:
            f.write("garbage")
        result = process_file(p)
    assert result.ok is False
    assert result.error_kind == "corrupt"


def test_export_to_csv_preserves_source_and_writes_output():
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "good.xlsx")
        _make_xlsx(src, ["name", "amount"], [["Acme", 100]])
        before = os.path.getmtime(src)
        rows = load_rows(src)
        out = export_to_csv(rows, os.path.join(d, "out", "good.csv"))
        # Original Excel file is preserved (untouched).
        assert os.path.exists(src)
        assert os.path.getmtime(src) == before
        with open(out, encoding="utf-8") as fh:
            content = fh.read()
    assert "name,amount" in content
    assert "Acme,100" in content


def test_integration():
    """End-to-end pipeline run over a mixed directory must not crash.

    A good file extracts rows; corrupt/empty files are reported (not raised);
    originals are preserved; CSV output is produced for good files.
    """
    with tempfile.TemporaryDirectory() as d:
        good = os.path.join(d, "good.xlsx")
        _make_xlsx(good, ["name", "amount"], [["Acme", 100], ["Beta", 200]])
        good2 = os.path.join(d, "good2.xlsm")
        _make_xlsx(good2, ["name", "amount"], [["Gamma", 300]])
        with open(os.path.join(d, "broken.xlsx"), "w") as f:
            f.write("corrupt")
        _make_xlsx(os.path.join(d, "empty.xlsx"), [], [])
        with open(os.path.join(d, "ignore.txt"), "w") as f:
            f.write("not a spreadsheet")  # skipped (unsupported ext)

        out_dir = os.path.join(d, "csv")
        report = run_pipeline(d, schema=SheetSchema(["name", "amount"]), output_dir=out_dir)
        # CSV output must exist while the temp dir is still alive.
        csv_written = os.path.exists(os.path.join(out_dir, "good.xlsx.csv"))
        source_preserved = os.path.exists(good) and os.path.exists(good2)

    # Pipeline processed the supported files without crashing.
    processed = {os.path.basename(r.path): r for r in report.results}
    assert processed["good.xlsx"].ok is True
    assert len(processed["good.xlsx"].rows) == 2
    assert processed["good2.xlsm"].ok is True
    assert processed["broken.xlsx"].ok is False
    assert processed["broken.xlsx"].error_kind == "corrupt"
    assert processed["empty.xlsx"].ok is False
    assert processed["empty.xlsx"].error_kind == "empty"
    # .txt is unsupported and not part of the pipeline.
    assert "ignore.txt" not in processed
    # Good files produced CSV output downstream; originals preserved.
    assert csv_written
    assert source_preserved
    assert report.total_rows == 3
