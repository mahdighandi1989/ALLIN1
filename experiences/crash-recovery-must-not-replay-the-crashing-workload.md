---
title: "Crash recovery must not replay the workload that caused the crash — serialize, load lazily, cap the retries"
tags: ["memory", "oom", "background-jobs", "resilience", "crash-recovery", "backend"]
topic_canonical: "crash-recovery-must-not-replay-the-crashing-workload"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-21T12:00:00Z"
created_at: "2026-09-21T12:00:00Z"
updated_at: "2026-09-21T12:00:00Z"
merged_from: []
---

# Crash recovery must not replay the crashing workload

## 🎯 چالش / Challenge

یک سرویس روی نمونهٔ کوچک (مثلاً ۵۱۲ مگابایت) کارِ سنگینِ حافظه‌بر انجام می‌دهد —
پردازشِ فایلِ آپلودی، تبدیلِ تصویر، ساختِ گزارش. برای اینکه ری‌استارت کارِ
نیمه‌تمام را از بین نبرد، ورودی کنارِ رکوردِ job ذخیره می‌شود و در boot ادامه
داده می‌شود. نتیجهٔ ناخواسته:

1. سرویس به‌خاطرِ همان کار OOM می‌شود و پلتفرم ری‌استارتش می‌کند.
2. در boot، کدِ ریکاوری **همهٔ** jobهای نیمه‌تمام را می‌خواند — یعنی **ورودیِ همهٔ
   آن‌ها هم‌زمان در حافظه** — و همه را **هم‌زمان** دوباره راه می‌اندازد.
3. یعنی دقیقاً همان بارِ کاری‌ای که instance را کشت، بلافاصله و **چند نسخه‌ای**
   دوباره اجرا می‌شود.

ریکاوری تبدیل به **تقویت‌کنندهٔ خرابی** شده است. کاربر فقط می‌بیند «خطا داد و بعد
کلاً قفل شد»، چون سرویس بارها بالا و پایین می‌رود.

## 💡 راه‌حل / Solution

چهار قاعده که با هم بودجهٔ حافظه را **قابلِ پیش‌بینی** می‌کنند:

1. **هم‌زمانی را در خودِ کارِ سنگین ببند، نه در لایهٔ ورودی.** یک سمافورِ سراسری
   (اغلب با ظرفیتِ ۱) دورِ تابعِ سنگین. آپلودِ دوم، کلیکِ دوبارهٔ کاربر و jobِ
   resume‌شده همه پشتِ آن صف می‌کشند. این تنها چیزی است که «دو قله هم‌زمان» را
   غیرممکن می‌کند و کاربر هم متوجهش نمی‌شود (وضعیتِ job هنوز `running` است).
2. **در ریکاوری، متادیتا را از payload جدا کن.** پرس‌وجویی که ردیف‌های کاملِ ORM
   را می‌خواند، هر blob را هم می‌خواند. فقط ستون‌های لازم (و `length(blob)` برای
   دانستنِ اینکه blob وجود دارد) را select کن، و payload هر job را **درست قبل از
   نوبتِ اجرایش** بخوان و بعدش رها کن.
3. **ریکاوری را سریالی و محدود کن.** یک درایورِ پس‌زمینه که لیست را یکی‌یکی جلو
   می‌برد، به‌علاوهٔ (الف) سقفِ تعدادِ تلاش برای هر job و (ب) **سقفِ تعدادِ jobهایی
   که هر boot ادامه می‌دهد**. بدونِ (ب)، یک صفِ انباشته، نمونهٔ تازه‌ری‌استارت‌شده
   را ساعت‌ها در خطر نگه می‌دارد.
4. **هزینهٔ خودِ «ذخیره برای resume» را حساب کن.** نوشتنِ یک blobِ بزرگ در DB
   معمولاً یک بافرِ هم‌اندازهٔ دیگر در درایور می‌خواهد — آن هم روی همان requestای
   که کارِ سنگین بلافاصله بعدش شروع می‌شود. برای فایل‌های بزرگ، **نداشتنِ resume
   بهتر از OOM است**: آستانه بگذار و بالای آن فقط خطای صادقانهٔ «دوباره بفرست».

دو نکتهٔ اندازه‌گیری که معمولاً دستِ‌کم گرفته می‌شوند:

- **هر payload چند برابرِ خودش RAM می‌خواهد.** بایتِ خام + base64 (۱٫۳۳×) + بدنهٔ
  JSON سریالایزشده + کپیِ کلاینتِ HTTP ⇒ تقریباً ۴×. سقفِ chunk را با ضریبِ ۴
  انتخاب کن، نه با اندازهٔ ظاهری.
- **حلقه‌های «کوچک‌ترش کن تا جا شود» را نسبتی بنویس.** `end -= 1` که در هر قدم
  کلِ خروجی را از نو می‌سازد، ده‌ها چرخهٔ تخصیص/آزادسازیِ چندمگابایتی تولید می‌کند
  — همان آشفتگیِ تخصیص که نمونهٔ کوچک را از پا درمی‌آورد. از نسبتِ
  `budget / actual` برای جهشِ مستقیم استفاده کن.

## 🧪 نمونه کد (Anonymized)

```python
_SEM = None

def _sem():
    global _SEM
    if _SEM is None:                      # lazily: needs a running loop
        _SEM = asyncio.Semaphore(int(os.getenv("MAX_CONCURRENT", "1")))
    return _SEM

async def run_job(job_id, payload, *meta):
    async with _sem():                    # (1) one heavy run at a time
        await _run_job_inner(job_id, payload, *meta)


async def recover_interrupted():
    async with session() as db:
        rows = (await db.execute(
            select(Job.id, Job.filename, Job.attempts, func.length(Job.payload))   # (2) metadata ONLY
            .where(Job.status == "running").order_by(Job.started_at.asc()))).all()
        queue, errored = [], 0
        for jid, fname, attempts, size in rows:
            if size and (attempts or 0) < MAX_ATTEMPTS and len(queue) < MAX_RESUME_PER_BOOT:
                (await db.get(Job, jid)).attempts = (attempts or 0) + 1
                queue.append((jid, fname))                                          # (3) capped
                continue
            row = await db.get(Job, jid)
            row.status, row.payload = "error", None
            row.detail = "interrupted by a restart — please upload again"
            errored += 1
        await db.commit()
    if queue:
        spawn(_drive(queue))              # fire-and-forget; boot must not block
    return errored


async def _drive(queue):
    for jid, fname in queue:              # strictly one at a time
        payload = b""
        try:
            async with session() as db:
                row = await db.get(Job, jid)
                if row is None or row.status != "running" or not row.payload:
                    continue              # finished/pruned meanwhile
                payload = bytes(row.payload)
            await run_job(jid, payload, fname)
        except Exception:
            log.exception("resume of %s failed", jid)
        finally:
            payload = b""                 # never hold two payloads at once
```

تست‌کردنش ساده است و ارزشش را دارد — تابعِ سنگین را با یک جایگزینِ شمارنده عوض
کن و ادعا کن که **قلهٔ هم‌زمانی ۱ بوده**:

```python
async def fake(*a, **k):
    nonlocal live, peak
    live += 1; peak = max(peak, live)
    await asyncio.sleep(0.05)
    live -= 1
...
assert peak == 1
```

## ⚠️ نکات حیاتی / Pitfalls

- **سمافور را در سطحِ ماژول و با loopِ زنده بساز.** `asyncio.Semaphore()` در
  زمانِ import ممکن است به loopِ اشتباه بچسبد؛ تنبل بسازش.
- **ظرفیتِ سمافور را از env بخوان** تا روی نمونهٔ بزرگ‌تر بدونِ دیپلوی باز شود.
- **صف‌کشیدن را به کاربر نشان بده یا حداقل خرابش نکن** — وضعیتِ job باید همچنان
  `running` بماند تا poll کار کند؛ وگرنه انتظارِ بی‌خطر شبیهِ شکست می‌شود.
- **`select(Model)` در کدِ ریکاوری یعنی «همهٔ ستون‌ها، همهٔ ردیف‌ها»** — همین یک
  خط، الگوی «چند blob هم‌زمان در RAM» را می‌سازد.
- **سقفِ تلاش بدونِ سقفِ تعداد کافی نیست.** اولی حلقهٔ بی‌نهایت را می‌بندد، دومی
  انفجارِ لحظه‌ایِ بعد از boot را.
- **اگر پروسه، UI را هم سرو می‌کند، OOMِ کارِ پس‌زمینه کلِ محصول را می‌خواباند.**
  کاربر آن را «قفل‌شدنِ مرورگر» گزارش می‌کند، نه «خطای سرور» — این را در تشخیص
  در نظر بگیر.
- **ایمیلِ هشدارِ پلتفرم را جدی بگیر:** «exceeded its memory limit» یعنی OOM
  واقعاً رخ داده؛ دنبالِ باگِ منطقی در لاگ نگرد.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. بودجهٔ واقعیِ حافظهٔ نمونه و تعدادِ workerها را از فایلِ استقرار دربیاور.
2. بزرگ‌ترین شیء در هر مسیرِ سنگین را پیدا کن و در ضریبِ واقعی‌اش ضرب کن (~۴ برای
   payloadهایی که base64/JSON می‌شوند).
3. سمافور را دورِ کارِ سنگین بگذار (نه دورِ endpoint).
4. کدِ ریکاوری را بازخوانی کن: چند payload هم‌زمان بار می‌شود؟ چند تا هم‌زمان اجرا؟
5. سقفِ «هر boot چند تا» و سقفِ «هر job چند تلاش» را جدا بگذار.
6. آستانهٔ ذخیرهٔ payload برای resume را تعیین کن؛ بالای آن خطای صادقانه بده.
7. تستی بنویس که peakِ هم‌زمانی را می‌سنجد — نه فقط «کار می‌کند».

## 🔗 References
- مرتبط: [ai-call-deadlines-match-the-workload-and-retry-once]
- مرتبط: [silent-input-truncation-makes-partial-output-look-complete]
