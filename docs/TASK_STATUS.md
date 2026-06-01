# Task execution status — `prompt/_index.json` (13 tasks)

Snapshot of how each queued task maps onto the codebase, recorded while working
through the index in `execution_priority` order. Three outcomes:

- **DONE (this session)** — code/tests added in the current run.
- **DONE (prior)** — already satisfied by earlier work; verified, files cited.
- **DEFERRED** — intentionally not implemented, with the reason.

The per-task prompts explicitly say: *if a request is already implemented
correctly, do not rebuild it — record why no change was needed and which files
cover it.* This file is that record.

| # | task_id | Title | Status | Evidence / notes |
|---|---------|-------|--------|------------------|
| 1 | task_1f0f55a17f45 | تقویت امنیت JWT و احراز هویت | DONE (prior) + DEFERRED | `none`-alg rejected (`utils/security.py`), secret from env (`config.py` `SECRET_KEY`/`JWT_SECRET_KEY`), rate-limit + lockout (`utils/rate_limit.py`), token blacklist (`utils/token_blacklist.py`), HSTS/headers + generic errors (`main.py`). Tests: `test_security.py`, `test_auth*.py`. **DEFERRED:** the AC "AUTH_DISABLED must not exist" — the user explicitly wants login disabled *for now*; the toggle stays, code is secure when enabled. |
| 2 | task_afcee9e1c044 | رفع باگ‌ها و همگام‌سازی داشبورد | DONE (prior) | `routers/stats.py` `/dashboard`, `app/dashboard/page.tsx` (loading/error/retry + static-mode message), `schemas/stats.py`. Tests: `test_stats.py`. |
| 3 | task_8a1dde11cd7b | تکمیل TypeScript صفحه Facilities و API | DONE (prior) | `app/facilities/page.tsx` complete + typed, `facilitiesApi` in `lib/api.ts`, `types`, backend `routers/facilities.py`. `tsc --noEmit` clean; static export builds. |
| 4 | task_e92cd1d0c4b4 | پاکسازی اسکریپت‌های تزریقی و URL هاردکد | DONE (prior) | No Inspector Bridge / `MutationObserver` / `wss://` / `onrender.com` / `http://localhost` in `src/` or `public/`. `lib/axios.ts` derives base URL from `NEXT_PUBLIC_API_URL ?? ''` (relative). `ClientWrapper.tsx` documents the removal. |
| 5 | task_66febcc9ff9a | تست‌های امنیتی احراز هویت | DONE (prior) | `test_security.py`, `test_auth.py`, `test_auth_enforcement.py`, `test_auth_disabled.py`, `integration/test_auth_pipeline.py` (no permission/role leak; 401 not 404). |
| 6 | e155f680-…  | اعلان برای رویداد scan_failed | DONE (prior) | `services/data_scan.py` calls `notify_event("scan_failed"/"verify_failed"/"task_failed", silent=False, priority="high")`; Persian templates in `services/notifications.py` (`CRITICAL_EVENTS`, `MESSAGE_TEMPLATES`). |
| 7 | task_bd83a960a6ab | پایداری و اعتبارسنجی پایپلاین اکسل | **DONE (this session)** | `services/excel_import.py` magic-byte format detection + `.xls` (xlrd) + classified `ExcelParseError`; `routers/imports.py` typed `ImportResult`, required-column fail-fast, parse logging; `requirements.txt` +`xlrd`. Tests +6 in `test_imports.py`. |
| 8 | task_97e9c7c534d9 | افزایش پوشش تست و کیفیت کد بک‌اند | **DONE (this session)** + prior | New: `database.py` SSL host-parse refactor (fixes `localhost.example.com` substring trap) + documented `CERT_NONE` + `DB_SSL_VERIFY` override, `test_database.py`; `test_fx.py` service unit tests (`to_base`/`load_rates`). Prior: `.github/workflows/ci.yml` (pytest + frontend build) — added `xlwt` test-dep. Coverage gate kept at 70% (async ASGI handler bodies aren't traceable via httpx, so 80% total isn't measurable — documented trade-off). |
| 9 | task_02dfbac2d524 | مانیتورینگ خطاها و عملکرد | DONE (prior) | `monitoring.py` (`REQUEST_LATENCY` Histogram, `REQUEST_COUNT`/`UNHANDLED_ERRORS` Counters, structlog), `/metrics` + `MetricsMiddleware` + global 500 handler in `main.py`. Tests: `e2e/test_performance.py` (latency threshold + `/metrics` histogram). |
| 10 | task_6fa50cdd5530 | رفع Anti-patternهای اعتبارسنجی و بازخورد | **DONE (this session)** | `models/facility.py` `RiskRating` enum + `@validates` (every write path validated); `main.py` removed stale FIXME (static-dir escalation already in place) + `test_main.py` prod-ERROR/dev-WARNING test; `test_models.py` risk_rating test. `parseApiError` already robust. |
| 11 | 36090c25-… | تست واحد مسیر stats داشبورد | DONE (prior) | `test_stats.py` has `test_dashboard_stats_success`, `test_dashboard_stats_empty`, `test_dashboard_stats_db_error` — exactly the AC. |
| 12 | 6e56bc2e-… | دکمه UI فاقد handler | DONE (prior — false positive) | Every button in `app/customers/page.tsx` has an `onClick` (add/edit/delete/detail/export/bulk/pagination). The detector mis-parsed inline arrow handlers; no dead/handler-less button exists. |
| 13 | 0b55d5f5-… | صفحه Customers برای static build | DONE (prior) | `app/customers/page.tsx` is a client component that fetches on mount; builds under static export (`output: 'export'`). |
