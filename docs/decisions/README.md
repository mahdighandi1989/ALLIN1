# Decision records (ADRs)

Per-decision records. The running summary log (with the **why/rationale**,
the **ground truth** chosen, and how the other side was **aligned**) lives in
[`../decisions.md`](../decisions.md).

- [ADR-004 — Excel `data` pipeline: fail-closed typed reader is the ground truth](ADR-004-excel-data-pipeline.md)
  — corrupt/empty/invalid-format error handling, Excel sheet/column **schema**
  validation, defined component output (rows → CSV/database), and `.xlsm`/`.xls`
  format handling.
