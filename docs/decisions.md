# Architecture & Security Decision Log

A running log of notable decisions, each with the **why/rationale** and, for
logic-audit ("coherence") items, the **ground truth** chosen and how the other
side was **aligned**. The detailed security rationale is in
[`SECURITY.md`](SECURITY.md); the PR narrative is in
[`../PR_DESCRIPTION.md`](../PR_DESCRIPTION.md).

## ADR-001 — Server is the ground truth for authorization & sessions

**Decision.** For every backend/frontend coherence conflict in the `auth`
pipeline, the **server** is ground truth and the client is aligned to it.

**Why / rationale.**
- **Permission check / authorization:** the backend enforces role/ownership
  (403 on mismatch); the frontend only renders generic UI. A client cannot be
  trusted to enforce access control.
- **Login rate limiting:** enforced server-side (429 → 423 lockout); the client
  counter is UI feedback only.
- **Session lifetime / revocation:** the backend JWT lifetime + `jti` blacklist
  is authoritative; the frontend clears its token on any 401.

**Status:** implemented and covered by `backend/tests` (see `SECURITY.md`).

## ADR-002 — Reject `alg: none`, require an environment-supplied JWT key

**Decision.** `none` is hard-blocked and `SECRET_KEY`/`JWT_SECRET_KEY` must be a
strong env value (hard error in production).

**Why / rationale.** Prevents signature-bypass/token-forgery and brute-force of
a weak key.

## ADR-003 — `AUTH_DISABLED` is a temporary, loudly-warned toggle only

**Decision.** Keep the explicitly-requested "login off for now" toggle but
default tests to `AUTH_DISABLED=False`, warn on startup, and treat
production-on as an error-level log.

**Why / rationale.** Preserves the requested convenience without letting the
bypass become a silent backdoor; restoring auth is a config change only.

## ADR-004 — Excel `data` pipeline: fail-closed typed reader is the ground truth

> Full per-ADR record:
> [`decisions/ADR-004-excel-data-pipeline.md`](decisions/ADR-004-excel-data-pipeline.md).

This ADR resolves four coherence inconsistencies found in the `data` pipeline
(`merged-from: 93988a1c-6d13-40f8-b5a9-8c49c377c7c6,
fc686bb9-3172-4810-9b26-624303be2a32, e0513e78-010b-4e28-bc31-4cc597182f0b,
45d3c335-4be5-47cd-8394-997476ca53ef`). The implementation lives in
[`../backend/app/services/data_pipeline.py`](../backend/app/services/data_pipeline.py)
and is covered by `backend/tests/test_data_pipeline.py` and
`backend/tests/test_pipeline_data.py` (both expose `::test_integration`).

**Decision.** The pipeline's typed reader/validator
(`load_rows` → `validate_schema` → `process_file`) is the **ground truth** for
what a valid Excel input is. The loose "just read whatever the file has"
assumption that lived implicitly in the source-scan side was **aligned** to it:
callers now go through `process_file`, which can only ever return a structured
`FileResult`, never a half-read sheet.

### The four inconsistencies, both sides + their assumptions

| Inconsistency | Side A assumption | Side B (ground truth) | How A was aligned |
| --- | --- | --- | --- |
| **Corrupt / empty / invalid format files** | scanner assumed every file in `data-import/` opens cleanly | reader treats unreadable→`corrupt`, no-rows→`empty`, wrong-ext→`invalid format` and raises a typed `PipelineError` | scanner calls `process_file`, which catches the error, logs it, emits a `scan_failed` notification, and **fail-closes that file** (no fallback) while the run continues |
| **No schema for the "binary archive file"** | an `.xlsx`/`.xlsm` was described only as a binary archive file (a zip of XML parts) with no column contract | a `SheetSchema(required_columns=…)` is the **target schema**; `validate_schema` rejects missing columns with `error_kind="schema"` | downstream consumers receive only schema-valid rows; a structural change to the spreadsheet now fails loudly instead of silently producing wrong data |
| **Undefined component output** | "output = *Preserved original Excel file*" — unclear whether data is extracted, and to what | output is an explicit `List[Dict]` row record per file; the original Excel file is **preserved** (opened read-only, never mutated) and can be written downstream as **CSV** (`export_to_csv`) or loaded into the **database** | `run_pipeline` returns a typed `PipelineReport`; CSV export is the defined downstream artifact |
| **`.xlsm` vs `.xls` not distinguished** | one reader for every format | reader dispatches by extension: `.xlsx`/`.xlsm` via **openpyxl** (read-only, `data_only`), legacy binary **`.xls`** via **xlrd** | `SUPPORTED_EXTENSIONS` + `load_rows` select the correct handler; `.xls` without `xlrd` degrades to a clear `invalid_format` error, never a crash |

**Why / rationale.** A data pipeline that silently swallows a corrupt or
restructured spreadsheet is worse than one that stops: it produces plausible
but wrong records that are expensive to debug downstream. Making the typed
reader the single ground truth means every tier (CSV export, DB load) consumes
the same validated shape, and the failure mode is a logged, notified,
fail-closed `FileResult` — never a crash and never silent corruption.

**Status:** implemented and covered by passing integration tests
(`test_data_pipeline.py::test_integration`,
`test_pipeline_data.py::test_integration`). Dependencies `openpyxl` and `xlrd`
are pinned in `backend/requirements.txt`.
