# ADR-004 — Excel `data` pipeline: fail-closed typed reader is the ground truth

> Per-ADR companion to the running log in [`../decisions.md`](../decisions.md).
> The PR narrative is in [`../../PR_DESCRIPTION.md`](../../PR_DESCRIPTION.md).
> Implementation:
> [`../../backend/app/services/data_pipeline.py`](../../backend/app/services/data_pipeline.py),
> covered by `backend/tests/test_data_pipeline.py::test_integration` and
> `backend/tests/test_pipeline_data.py::test_integration`.

This ADR resolves four coherence inconsistencies found in the `data` pipeline.

`merged-from: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6, fc686bb9-3172-4810-9b26-624303be2a32, e0513e78-010b-4e28-bc31-4cc597182f0b, 45d3c335-4be5-47cd-8394-997476ca53ef`

## Decision (the ground truth)

The pipeline's **typed reader/validator** — `load_rows` → `validate_schema` →
`process_file` in `app.services.data_pipeline` — is the **ground truth** for what
a valid Excel input is. The loose *"just read whatever the file has"* assumption
that lived implicitly on the source-scan side was **aligned** to it: callers go
through `process_file`, which can only ever return a structured `FileResult`,
never a half-read sheet or an unhandled crash.

## The four inconsistencies — both sides, their assumptions, and how they were aligned

### 1. Corrupt / empty / invalid format files (error handling)

- **Side A assumption:** the scanner assumed every file under `data-import/`
  opens cleanly — no error handling for a **corrupt**, **empty**, or
  **invalid format** file.
- **Side B (ground truth):** the reader treats an unreadable workbook →
  `corrupt`, a no-rows workbook/sheet → `empty`, and an unsupported extension →
  `invalid format`, and **raises** a typed `PipelineError(kind=...)`. Every read
  is wrapped in `try`/`except` (see `_read_xlsx_rows`, `_read_xls_rows`,
  `load_rows`).
- **How A was aligned:** `process_file` catches the error, logs it, emits a
  `scan_failed` notification, and **fail-closes that file** (no fallback) while
  the overall run continues. `process_file` itself never raises.

### 2. No schema for the "binary archive file" (Excel sheet / column contract)

- **Side A assumption:** an `.xlsx`/`.xlsm` was described only as a *binary
  archive file* (a zip of XML parts) with **no column contract** — no defined
  sheet names, columns, or types.
- **Side B (ground truth):** a `SheetSchema(required_columns=...)` is the
  **target schema**; `validate_schema` rejects a row set whose first row is
  missing any required **column** (case-insensitive) with
  `error_kind="schema"`.
- **How A was aligned:** downstream consumers receive only schema-valid rows; a
  structural change to the spreadsheet (renamed/removed column or sheet) now
  **fails loudly** instead of silently producing wrong data.

### 3. Undefined component output

- **Side A assumption:** the component output was only *"Preserved original
  Excel file"* — unclear whether data is extracted, and to what **output
  format**.
- **Side B (ground truth):** the output is an explicit `List[Dict]` row record
  per file (a `FileResult.rows`); the original Excel file is **preserved**
  (opened read-only, never mutated) and the extracted data can be written
  **downstream** as a **CSV** file (`export_to_csv`) or loaded into the
  **database**.
- **How A was aligned:** `run_pipeline` returns a typed `PipelineReport`; CSV
  export is the defined downstream artifact and the **target schema** for any DB
  load is the same validated row shape.

### 4. `.xlsm` vs `.xls` not distinguished (format handling)

- **Side A assumption:** the two files in the `original-excel-files` set
  (`.xlsm` and `.xls`) were handled by **one reader for every format**.
- **Side B (ground truth):** the reader dispatches by extension —
  `.xlsx`/`.xlsm` via **openpyxl** (`read_only=True, data_only=True`) and the
  legacy binary **`.xls`** via **xlrd**. `SUPPORTED_EXTENSIONS` +
  `load_rows` select the correct handler.
- **How A was aligned:** a `.xls` file on a server without `xlrd` degrades to a
  clear `invalid_format` error, **never a crash**. (`.xlsm` macros are not
  executed — only the cell data is read, which is the intended, safe behaviour
  for this data pipeline.)

## Why / rationale

A data pipeline that silently swallows a corrupt or restructured spreadsheet is
worse than one that stops: it produces plausible-but-wrong records that are
expensive to debug downstream. Making the typed reader the single **ground
truth** means every tier (CSV export, DB load) consumes the same validated
shape, and the failure mode is a logged, notified, fail-closed `FileResult` —
never a crash and never silent corruption. This is the **decision** the
behaviour-based acceptance criteria require, and the same robust-reader idea is
reused for uploaded files in `app.services.excel_import` (`parse_workbook`,
which dispatches by **magic bytes** so a mislabelled upload is still handled
correctly).

## Status

Implemented and covered by passing integration tests
(`test_data_pipeline.py::test_integration`,
`test_pipeline_data.py::test_integration`). Dependencies `openpyxl` and `xlrd`
are pinned in `backend/requirements.txt`.
