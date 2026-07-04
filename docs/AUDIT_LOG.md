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

## 2026-07-02 — Deep audit (کل سیستم، فرانت تا بک) + اصلاحات

- **[FINDING]** Baseline کامل شد: backend `576 passed, 7 skipped`؛ frontend
  type-check + build سبز. `backend/static` کامیت‌شده با سورس فرانت هماهنگ بود
  (فقط buildId متفاوت). اسکن secret چیزی در سورس پیدا نکرد.
- **[DECISION]** بازرسی با ۴+۲ ایجنت موازی (روترها/امنیت، سرویس‌ها + دو زیر-بازرس،
  مدل‌ها/مهاجرت/دیپلوی، فرانت‌اند) انجام شد؛ هر یافته قبل از اصلاح در کد راستی‌آزمایی شد.

### CHANGE `2aa9c8e` — استقرار گردش‌کار مستندسازی
CLAUDE.md + AUDIT_LOG + REMOVAL_CANDIDATES + Makefile واقعی؛ `cleanup_unused_files.py`
(فقط placeholder، بدون هیچ ارجاع) به `archive/quarantine/` قرنطینه شد.

### CHANGE `b2b52c2` — امنیت/RBAC (root cause: دو پیاده‌سازی موازی `get_current_user`)
- `utils/security.get_current_user` چک `is_active` نداشت (نسخه‌ی `routers/auth.py`
  داشت) → کاربر غیرفعال‌شده تا انقضای JWT دسترسی کامل داشت. اضافه شد.
- نقش viewer (فقط-خواندنی طبق سیاست صریح `tests/test_rbac.py`) می‌توانست بنویسد:
  facility status/restore، customer restore، همه‌ی mutationهای offer-letter،
  trash restore، ایمپورت اکسل/AI، stats snapshot — همگی `require_editor` گرفتند؛
  تغییر وضعیت facility و status/delete نامه‌ها audit هم می‌شوند.
- trash restore تسهیلات `cascade_restore_facility` را صدا نمی‌زد (چک‌لیست/تسک‌ها
  حذف‌شده می‌ماندند) — هم‌رفتار با restore خود روتر شد.
- لاگین JSON مدعی پذیرش `{"email"}` بود ولی فقط با username جستجو می‌کرد — حالا
  username یا email. فایل مرده‌ی `auth.py` ریشه قرنطینه شد. +۱۱ تست.

### CHANGE `<offer-widths>` — ستون‌های offer_letters (باگ production-only)
`facility_id` VARCHAR(8) بود در حالی که IDهای واقعی ۹+ کاراکترند → **هیچ نامه‌ای
هرگز نمی‌توانست به تسهیلات لینک شود** (Postgres: value too long). نرخ‌ها Numeric(5,4)
(سقف 9.9999) در حالی که API تا 100 می‌پذیرد → هر نرخ ≥۱۰٪ overflow. عرض‌ها اصلاح؛
PKهای فرزند uuid کامل؛ **db_init حالا precision عددی را هم widen می‌کند** (فقط
هم‌scale و رو به بالا). تست‌ها روی متادیتای مدل‌اند چون SQLite این‌ها را enforce
نمی‌کند — دقیقاً دلیل دیده‌نشدن باگ در CI.

### CHANGE — amortization (منطق مالی، rule 3: root cause + مسیر برگشت)
Root cause: `round(tenor_months*ppy/12)` + نرخ کاملِ هر دوره ⇒ bullet شش‌ماهه = بهره‌ی
یک سال (۲×)، ۱۸ماهه = ۲۴ ماه بهره، ۴ماههٔ فصلی = کم‌شماری. اصلاح: تجزیه به دوره‌های
کامل + stub نهایی با بهره‌ی متناسب (divmod). تاریخ‌ها تقویمی واقعی (day-clamped) شدند.
مضرب‌های کامل بیت‌به‌بیت مثل قبل. مسیر قدیمی پشت `AMORT_LEGACY_ROUNDING=1`. +۱۲ تست.

### CHANGE `13aca82` — سرویس‌ها (فلسفه‌ی conservative/review-first تثبیت شد)
- db_cleanup: طبقه‌بندی certain/probable حالا **همه‌ی ستون‌های داده** را مقایسه می‌کند
  (کمکی مرده‌ی `_conflict` دقیقاً برای همین بود) — ضامنِ متفاوت با چکِ هم‌شماره دیگر
  auto-remove نمی‌شود؛ همان قانون در `dup_status` (گاردهای ورود).
- data_merge: enrich تسهیلات fill-empty-only شد و مرده را زنده نمی‌کند (قبلاً هر
  استارتاپ/دیپلوی حذف/اصلاحِ اپراتور را برمی‌گرداند!). +۴ تست.
- customer_link.ensure_customer: مشتری soft-delete با همان account_no را restore
  می‌کند به‌جای IntegrityError (ذخیره‌ی نامه/ملک/ضامن ۵۰۰ می‌داد).
- excel_import: سقف ۵۰۰۰ ردیف حالا خطای صریح است نه truncation خاموش؛ هدر تکراری
  fail-fast (قبلاً ستون راست‌تر بی‌صدا برنده می‌شد).
- exporters: صفر ابتدای شماره‌حساب/تلفن در XLSX حفظ می‌شود؛ CSV تزریق فرمول اکسل
  را خنثی می‌کند.
- fx: تبدیل ۱:۱ ارز ناشناخته باقی است (fail-open) ولی حالا **یک‌بار به‌ازای هر ارز
  WARN** می‌شود؛ جدول خالی نرخ‌ها → پیش‌فرض‌ها با لاگ.
- telegram: `TELEGRAM_CHAT_ID` چند-آی‌دی («111,222») همه‌ی اعلان‌ها را 400 می‌کرد —
  اولین id مقصد پیش‌فرض شد (مطابق مستند config)؛ `save_prefs` دیگر شکست DB را
  نمی‌بلعد (allow-list امنیتی بی‌صدا برنمی‌گردد) و روت prefs از session درخواست
  می‌نویسد.
- دو باگ `\b` داخل رشته/کلاس کاراکتر (backspace واقعی!) در draft_extract و imports.

### CHANGE `5f8d06e` — بک‌اند (اعلان‌ها، هشدارها، ingest، سخت‌سازی)
- جدول جدید `notification_reads`: خواندن broadcast per-user شد — اولین خواننده
  دیگر زنگوله‌ی بقیه را خالی نمی‌کند (broadcastهای قدیمیِ خوانده، خوانده می‌مانند).
- expiry: اسکن حالا هشدارهای برطرف‌شده (تمدید/حذف) را deactivate می‌کند
  (`tasks_resolved`) — قبلاً تسک ALERT-* برای همیشه می‌ماند.
- doc_ingest: `account_type` فقط از پیش‌فرض retail ارتقا می‌یابد (sme کیوریت‌شده
  دیگر پاک نمی‌شود)؛ تسهیلات بی‌نوع به‌عنوان OTHER مچ می‌شود (re-import دیگر
  duplicate و دوبرابرشماری exposure نمی‌سازد)؛ آنتروپی PK از ۲ به ۸ کاراکتر hex.
- آپلودها bounded-read شدند (بدنه‌ی چندگیگی دیگر قبل از چک سایز، RAM را پر نمی‌کند)؛
  Content-Disposition دانلود Drive با RFC6266/5987؛ برچسب متریک مسیرهای unmatched
  ثابت شد (اسکن بات‌ها سری نامحدود نمی‌سازد)؛ `/api/simulate-unhandled-error`
  admin-only شد؛ gunicorn به requirements اضافه شد.

### CHANGE `068456b` — فرانت‌اند (خطرناک‌ترین: نشت داده بین حساب‌ها)
چهار فرم credit-file-retail/corporate، sanction و offer-letter هنگام بارگیری حساب
جدید state حسابِ قبلی را نگه می‌داشتند (fallback `s.X`، مپ روی ردیف‌های قبلی، جایگزینی
مشروط ماتریس وثایق/شرکا) → «ذخیره» داده‌ی مشتری A را روی مشتری B می‌نوشت و حتی
تسهیلاتِ A را آپدیت می‌کرد. همگی حالا از state تمیز reset می‌شوند. + رفع race جستجو
(الگوی صفحه‌ی audit)، جستجوی سرورساید مشتری در مودال New Facility (سقف ۱۰۰ مشتری
آخر برداشته شد)، لینک Google login با `NEXT_PUBLIC_API_URL`، هم‌ترازی نتایج import
بعد از حذف فایل، اعتبارسنجی per-field نرخ ارز، رفع bidi در ۶ صفحه، پروکسی `/api`
در nginx فرانت (مسیر داکر). `backend/static` + `frontend/out` بازساخته و کامیت شد.

### CHANGE — مسیر دیپلوی docker/alembic (مسیر Render دست‌نخورده)
mount فایل ناموجود init.sql حذف؛ alembic در compose هم best-effort؛ مهاجرت 001 از
enum بومیِ ناموجود به VARCHAR (alembic روی DB تازه همیشه می‌مرد)؛ escape کردن `%` در
env.py؛ stage «development» فرانت + `NEXT_PUBLIC_API_URL` به‌عنوان build ARG؛
`SECRET_KEY` غایب در production حالا خطای سخت است (قبلاً هر worker کلید تصادفی
خودش را می‌گرفت → 401های تصادفی و مرگ همه‌ی sessionها در هر دیپلوی).

### [FINDING — ثبت‌شده، عمداً اصلاح‌نشده در این نوبت]
- `docker-compose.prod.yml`: پورت 443 بدون TLS در nginx؛ bind-mount کد از base
  در prod هم فعال است (با read_only تضاد دارد). مسیر داکر ثانویه است — تصمیم با مالک.
- `render.yaml` مقدار `CORS_ORIGINS` را خالی می‌کند (same-origin فعلی امن است ولی
  جداکردن فرانت آن را می‌شکند)؛ `/docs` و `/openapi.json` در prod باز است
  (validate_environment_security هر بوت هشدار می‌دهد).
- pdf/workbook split در `doc_ingest` روی event loop اجرا می‌شود (CPU-bound) — برای
  فایل‌های بزرگ چند ثانیه بلاک می‌کند؛ کاندید انتقال به thread.
- `record_audit(db=…)` تراکنش caller را commit می‌کند — امروز همه‌ی call-siteها بعد
  از commit خودشان صدا می‌زنند (بازرسی شد، باگ زنده نیست) ولی الگوی خطرناکی است.
- `customers.account_no` روی DBهای قدیمی/heal-شده unique-constraint واقعی ندارد
  (db_init ایندکس non-unique می‌سازد) — نیازمند پاکسازی داده قبل از افزودن قید.
- **[VERIFY — نهایی، قبل از مرج به main]** backend: `607 passed, 7 skipped`
  (baseline: 576 → +۳۱ تست جدید، صفر شکست)؛ frontend: `npm run type-check` +
  `npm run build` سبز؛ `backend/static` از build تازه سینک و کامیت شده.
  طبق دستور دائمی مالک، مرج مستقیم به `main` (بدون PR) انجام شد — Render
  خودکار دیپلوی می‌کند.

## 2026-07-03 — Offer Letter هوشمندسازی (درخواست مالک) + کاتالوگ نوع تسهیلات + ضامن‌ها

- **[OWNER REPORT]** فرم Offer Letter هوشمند نیست: (۱) برای هر قالب همه‌ی فیلدها نمایش
  داده می‌شوند حتی نامرتبط‌ها؛ (۲) عنوان فیلدها گیج‌کننده است؛ (۳) فیلد «نوع تسهیلات» باید
  هم لیست انتخابی باشد هم تایپ آزاد، و نوع کاملاً جدید باید خودش در دیتابیس جا باز کند و
  به لیست اضافه شود؛ (۴) بخش ضامن‌ها که در نمونه‌ی امضاشده‌ی بانک هست در فرم جایی ندارد؛
  (۵) نمونه‌ی docx پیوست کامل پوشش داده نشده (یادداشت‌های زیر جدول مدارک).
- **[CHANGE — فرم هوشمند]** `frontend/src/app/offer-letter/page.tsx`: فیلدها بر اساس قالبِ
  مؤثر گروه‌بندی و شرطی شدند — گروه مشترک (گیرنده/شعبه/سریال/نوع تسهیلات)، گروه English
  (RequestDate/CreditLimit/InterestRate/ValidUntil/ProcessingFee/AccountSuffix/Remarks/
  RequiredSecurities) فقط در قالب English، و گروه وام (SubjectDate/LoanAmount/…/LienAmount/
  NotesPersonal/ضامن‌ها) فقط در قالب دوزبانه. لیبل‌ها فارسی-اول با زیرنویس انگلیسی و اشاره
  به این‌که هر فیلد کجای نامه چاپ می‌شود.
- **[BUG FIXED ضمنی]** ورودی `RequestDate` اصلاً وجود نداشت درحالی‌که متن صفحه‌ی ۱ قالب
  English به آن ارجاع می‌دهد («letter Dated: …») — هرگز قابل پر کردن نبود. اضافه شد.
  همچنین `ProcessingFee`/`AccountSuffix`/`RequestDate` هنگام بارگیریِ snapshot ذخیره‌شده
  restore نمی‌شدند — اضافه شدند.
- **[CHANGE — کاتالوگ نوع تسهیلات]** بک‌اند `routers/crm.py`: `GET/POST /api/crm/facility-types`
  — built-in ها + موارد سفارشی در `SystemSetting("custom_facility_types")`. افزودن با گارد
  مشابهت نام (نرمال‌سازی حروف/فاصله/علائم + difflib ratio ≥0.9): مشابه ⇒ match بدون درج،
  جدید ⇒ درج و از این به بعد در لیست. فرانت: combobox (input + datalist) و ثبت خودکار نوع
  جدید هنگام «ذخیره».
- **[CHANGE — ضامن‌ها]** پاسخ `offer-letter-data` حالا `Guarantors` (نام + حساب، بدون تکرار)
  می‌دهد؛ بخش ضامن‌ها در فرم (قالب وام): ردیف‌های قابل‌ویرایش، prefill از پرونده، درج در بند ۷
  «مدارک موردنیاز» دقیقاً مثل نمونه‌ی پرشده‌ی بانک («… borrower(s) / -Mr. NAME- A/C NO.…»)،
  و هنگام ذخیره upsert به رکوردهای ضامن مشتری.
- **[BUG FIXED — upsert ضامن]** `add_guarantor` فقط با `cheque_no` مطابقت می‌داد ⇒ ضامنِ
  بدون چک (مسیر Offer Letter) در هر ذخیره رکورد تکراری می‌ساخت. مطابقت نام (case-insensitive
  + حساب در صورت وجود) اضافه شد؛ و ارسال cheque_no خالی دیگر چکِ ذخیره‌شده را پاک نمی‌کند
  (مطابق قرارداد مستند خود endpoint).
- **[BUG FIXED — بوت SQLite]** `app/database.py` پارامترهای pool (`pool_size`/`max_overflow`/
  `pool_recycle`) را بدون شرط پاس می‌داد ⇒ بوتِ dev با `DATABASE_URL=sqlite+aiosqlite:…`
  (مسیر مستندشده) TypeError می‌داد. حالا فقط برای غیر-SQLite ارسال می‌شوند. (در وریفای E2E
  همین تسک کشف شد.)
- **[CHANGE — پوشش نمونه]** یادداشت‌های زیر جدول مدارک (`NotesPersonal`) قابل‌ویرایش شد با
  متن پیش‌فرض عینِ نمونه (Note 1: balance confirmation، Note 2: تسویه‌ی وام قبلی)؛ دکمه‌ی
  «محاسبه» قسط ماهانه با فرمول مانده‌ی نزولی — خروجی برای نمونه‌ی ۸۰٬۰۰۰/۱۲٪/۴۸ماه دقیقاً
  `2,106/71` مطابق فرم بانک. گزینه‌های قالب فارسیِ شفاف + `dir="rtl"` (قانون bidi).
- **[VERIFY]** تست‌های جدید: `test_facility_type_catalog.py` (۴) + `test_offer_letter_guarantors.py`
  (۳)؛ E2E واقعی با Playwright روی بیلد سرو-شده: بارگیری حساب، prefill ضامن‌ها (۲ ردیف)،
  EMI=2,106/71، combobox با ۱۰ گزینه، بند ۷ با نام ضامن‌ها، فیلدهای English در قالب وام مخفی
  (و برعکس)، ذخیره → facility-types 200 + دو upsert ضامن 200 بدون تکرار. suite کامل + build
  نتیجه‌اش پایین‌تر ثبت می‌شود.
- **[VERIFY — نهایی، قبل از مرج به main]** backend: `614 passed, 7 skipped`
  (+۷ تست جدید نسبت به ۶۰۷؛ صفر شکست — run کامل بعد از همه‌ی تغییرات از جمله
  fix انجین SQLite)؛ frontend: type-check + build سبز؛ `backend/static` و
  `frontend/out` از همین سورس بازساخته و کامیت شدند. E2E مرورگر روی بیلد
  سرو-شده انجام و اسکرین‌شات‌ها برای مالک ارسال شد. مرج مستقیم به `main`.

## 2026-07-04 — دستیارِ هوشمندِ نامه (AI Letter Assistant) — درخواست مالک

- **[OWNER REQUEST]** ابزاری در بخش «نامه‌ها» که با مدل‌های هوش مصنوعیِ فعال (لیست‌شده بر اساس
  اولویت و قابلِ انتخاب توسط کاربر) روی متنِ نامه با تسلط به دیتابیس و همه‌ی فیلدها کار کند:
  اصلاح املا/نگارش، چینش پاراگراف، ظاهر جداول، یافتن مغایرت‌ها، حرفه‌ای‌سازی، و اعتبارسنجیِ
  موردِ انتخاب‌شده با دیتابیس. حتماً پیش از اعمال، فهرست پیشنهادها با تیک نمایش داده شود و فقط
  موارد تیک‌خورده اعمال شوند. «با دقت و وسواسِ زیاد» چون قرار است به بخش‌های دیگر هم سرایت کند.
- **[DECISION — فلسفه: review-first، سرور ground truth]** مدل فقط «پیشنهاد» می‌دهد؛ هیچ‌چیز
  خودکار اعمال نمی‌شود و بک‌اند هیچ رکوردی را نمی‌نویسد. یک گیتِ اعتبارسنجیِ قطعی سمتِ سرور
  تصمیم می‌گیرد کدام پیشنهاد امن است؛ اعمال سمتِ کلاینت و فقط روی state نامه، و نامه صرفاً از
  مسیرِ Save موجود ذخیره می‌شود. این با ADR-001 و فلسفه‌ی محافظه‌کاریِ پروژه هم‌راستاست.
- **[CHANGE — بک‌اند]** روترِ جدید `routers/letter_ai.py` روی `/api/letter-ai`:
  - `GET /models`: مدل‌های فعال+پیکربندی‌شده به‌ترتیبِ اولویت (برای انتخابِ کاربر) + کاتالوگِ ابزارها.
  - `POST /analyze`: حقایقِ پایگاه‌داده‌ی حساب (مشتری/تسهیلات/ضامن‌ها/برشی از پروفایل) را جمع می‌کند،
    مدلِ انتخابی/خودکار را با قراردادِ خروجیِ JSONِ سخت اجرا می‌کند، و فقط تغییراتی را برمی‌گرداند که
    از اعتبارسنجی عبور کنند. read-only مطلق؛ gated به `require_editor` و audit می‌شود.
  - سرویسِ `services/letter_assistant.py`: ساختِ prompt + parse مقاوم + **گیتِ ضدِ توهم** —
    یک `text_replace` فقط وقتی می‌ماند که `find` عیناً (یا با نرمال‌سازیِ فاصله/نیم‌فاصله) در متنِ
    فعلیِ همان فیلد وجود داشته باشد؛ `set_field` فقط برای فیلدهای کوتاهِ allow-list (نه body)؛ `note`
    صرفاً مشاوره‌ای. سقفِ ۶۰ تغییر؛ category/severity سنجیده می‌شوند.
  - `ai_manager.list_usable()` اضافه شد (همه‌ی مدل‌های فعال+کلیددارِ قابلِ استفاده، بهترین-اول) —
    برخلافِ `capable_models` که فقط doc/vision می‌داد.
- **[CHANGE — فرانت‌اند]** در `app/letter/page.tsx` دکمهٔ «دستیارِ هوشمند» + یک مودالِ کامل RTL:
  انتخابِ مدل (پیش‌فرض خودکار/اولویت‌دار)، چک‌باکسِ ابزارها، ثبتِ متنِ انتخاب‌شده (برای اعتبارسنجی)،
  دستورِ اختصاصی. پس از «بررسیِ نامه»: فهرستِ پیشنهادها با badgeِ دسته/شدت و diffِ before→after؛
  تیک/برداشتنِ تیک؛ «اعمالِ N موردِ انتخاب‌شده». اعمالِ سمتِ کلاینت **جراحی‌وار و امن**:
  `applyTextReplaceHtml` فقط محتوای یک TEXT NODE را بازنویسی می‌کند (تگ‌ها/جداول/بولد سالم می‌مانند)
  و متنِ جایگزین به‌صورتِ literal درج می‌شود (نه HTML)؛ `set_field` روی فیلدهای rich با escape.
  موردی که در متنِ فعلی پیدا نشود رد و گزارش می‌شود. `lib/api.ts`: `letterAiApi` + تایپ‌ها.
- **[VERIFY]** تست‌های جدید: `test_letter_assistant.py` (۱۲ — گیتِ اعتبارسنجی/توهم، html_to_text،
  build_facts/prompt) + `test_letter_ai_endpoints.py` (۴ — models، analyze با مدلِ mock، فیلترِ
  توهم، مسیرِ friendlyِ no_model). E2E واقعی با مرورگر روی بیلدِ سرو-شده (مدل stub، بدونِ کلید):
  بارگیریِ حساب، تایپِ متن، ۷ ابزار، ۳ پیشنهاد (۱ توهمی توسطِ گیت حذف شد)، اعمالِ ۲ موردِ
  applicable (نه noteِ مشاوره‌ای) روی body و subject، toast و به‌روزشدنِ فهرست. suite کامل + build
  سبز (نتیجهٔ نهایی پایین‌تر).
- **[NEXT/EXTENSIBLE]** همین الگو (پیشنهاد→گیت→بازبینیِ تیک‌دار→اعمالِ جراحی‌وار) قابلِ سرایت به
  offer-letter/sanction/credit-file است؛ عمداً ابتدا فقط روی «نامه‌ها» پیاده شد تا با دقت تثبیت شود.
