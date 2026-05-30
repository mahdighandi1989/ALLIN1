"""Parse an uploaded Excel workbook into customer/facility rows.

Reuses the robust reader idea from app.services.data_pipeline but works on
in-memory bytes (an uploaded file). Returns parsed dict rows + a header list so
the import router can map and validate them. Pure parsing — no DB access.
"""
from __future__ import annotations

import io
from typing import Dict, List, Tuple


class ExcelParseError(Exception):
    """Raised when the uploaded file cannot be read as a spreadsheet."""


def parse_workbook(content: bytes, *, max_rows: int = 5000) -> Tuple[List[str], List[Dict]]:
    """Read the first sheet of an .xlsx/.xlsm byte stream into (headers, rows).

    The first non-empty row is treated as the header. Header cells are lowercased
    and stripped so callers can match columns case-insensitively. Empty trailing
    rows are skipped; at most ``max_rows`` data rows are returned.
    """
    try:
        import openpyxl

        wb = openpyxl.load_workbook(
            io.BytesIO(content), read_only=True, data_only=True
        )
    except Exception as exc:
        raise ExcelParseError(f"could not read workbook: {exc}")

    try:
        if not wb.sheetnames:
            raise ExcelParseError("workbook has no sheets")
        ws = wb[wb.sheetnames[0]]
        rows_iter = ws.iter_rows(values_only=True)

        # Find the first non-empty row as the header.
        header = None
        for row in rows_iter:
            if row and any(c is not None and str(c).strip() != "" for c in row):
                header = row
                break
        if header is None:
            return [], []

        headers = [
            (str(h).strip().lower() if h is not None else f"col_{i}")
            for i, h in enumerate(header)
        ]

        records: List[Dict] = []
        for row in rows_iter:
            if row is None or all(c is None for c in row):
                continue
            rec = {}
            for i, key in enumerate(headers):
                rec[key] = row[i] if i < len(row) else None
            records.append(rec)
            if len(records) >= max_rows:
                break
        return headers, records
    finally:
        wb.close()


def cell_str(value) -> str:
    """Normalise a cell value to a trimmed string ('' for None)."""
    if value is None:
        return ""
    return str(value).strip()
