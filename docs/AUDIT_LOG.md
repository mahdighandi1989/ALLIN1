# Audit Log

Running record of every finding, decision, change, and revert. Newest entries are
appended at the end. Format:
`[date] [type: FINDING|DECISION|CHANGE|REVERT|VERIFY] — detail + rationale`.

این سند بعد از **هر** تسک به‌روزرسانی می‌شود (قانون ۵ در `CLAUDE.md`) — append-only.

---

## 2026-07-02 — Adoption of the living-documentation workflow

- **[DECISION]** گردش‌کار مستندسازی زنده (الگوبرداری از ریپوی trading-system مالک) در این
  ریپو مستقر شد: `CLAUDE.md` (قوانین الزام‌آور + دستورات دائمی مالک)، همین
  `docs/AUDIT_LOG.md` (append-only)، و ثبت درس‌ها در `experiences/` طبق فرمت موجود.
  دستور دائمی مالک: بعد از سبزِ محلی (pytest + type-check + build) **مستقیم به `main`
  مرج شود**، بدون PR و بدون پرسش مجدد؛ مستندسازی بعد از هر تسک خودکار و بدون یادآوری.
- **[FINDING]** Baseline در شروع (کامیت `67b798d`، برابر `origin/main`):
  - Frontend: `npm run type-check` + `npm run build` → ✅ سبز (static export، ۳۰+ صفحه).
  - Backend: suite کامل pytest در حال اجرا — نتیجه در ادامه ثبت می‌شود.
- **[FINDING]** `Makefile` ریشه فقط حاوی متن placeholder فارسی
  («محتوای کامل Makefile با دستور اضافه شده») است — محتوای واقعی هرگز کامیت نشده.
