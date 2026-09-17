---
title: "Silent input truncation makes partial LLM output look complete — budget fairly and announce every cut"
tags: ["ai", "llm", "prompt", "data-integrity", "truncation", "ux"]
topic_canonical: "silent-input-truncation-makes-partial-output-look-complete"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-17T12:00:00Z"
created_at: "2026-09-17T12:00:00Z"
updated_at: "2026-09-17T12:00:00Z"
merged_from: []
---

# Silent input truncation makes partial output look complete

## 🎯 چالش / Challenge

کاربر N منبع (پیوست، ردیفِ دیتابیس، فایل) را انتخاب می‌کند و از مدل می‌خواهد
بر اساسِ **همهٔ** آن‌ها خروجی بسازد (جدول، خلاصه، نامه). خروجی می‌آید، ظاهرش
سالم است، ولی فقط بخشی از منابع در آن دیده می‌شود — و هیچ‌کس نمی‌فهمد چرا.

علتِ تقریباً همیشگی **کدِ خودِ ما** است، نه مدل: جایی در ساختِ پرامپت یک برشِ
خاموش وجود دارد —

```python
items = [...][:10]          # سقفِ تعدادی
text  = text[:20_000]       # سقفِ محتوایی
MAX_TABLES = 8              # سقفِ نوعِ سوم
```

این بدترین شکلِ شکست است: سیستم دروغ نمی‌گوید، **سکوت** می‌کند. کاربر خروجیِ
ناقص را کامل فرض می‌کند و روی آن تصمیم می‌گیرد. تازه اگر مدل هم بی‌عیب باشد،
سقفِ `max_tokens` می‌تواند همان خروجی را وسطِ کار قطع کند — شکستِ دومِ مستقل
با همان علائمِ ظاهری.

## 💡 راه‌حل / Solution

سه قاعده، به همین ترتیب:

1. **بودجهٔ مشترک به‌جای سقفِ تعدادی.** هرگز «N تای اول» را نگه ندار. یک
   بودجهٔ کلِ کاراکتری بگذار و آن را بینِ همهٔ منابع تقسیم کن
   (`share = TOTAL // n`) تا **هیچ منبعی غایب نباشد**؛ بهتر است هر منبع
   کوتاه‌شده حاضر باشد تا نصفشان کاملاً نامرئی. سقفِ تعدادی را فقط وقتی اعمال
   کن که سهم زیرِ یک کفِ قابلِ‌استفاده (مثلاً ۴ هزار کاراکتر) بیفتد.
2. **هر برش باید اعلام شود — دو بار.** تابعِ ساختِ پرامپت یک
   `warnings_out: list` بگیرد و هر کوتاه‌سازی را با **عددِ واقعی** ثبت کند.
   این هشدارها هم **داخلِ خودِ پرامپت** بروند (تا مدل نتواند نتیجه را «کامل»
   اعلام کند) و هم در پاسخِ API به کاربر برسند (نه در لاگِ سرور — کاربر لاگ
   نمی‌خواند). در UI به‌صورتِ برجسته نشان بده، نه یک خطِ خاکستری.
3. **قراردادِ کامل‌بودن را صریح در پرامپت بنویس.** عددِ دقیقِ منابع را بگو و
   بخواه که یکی‌یکی و کامل پردازش شوند، خلاصه‌سازی و «و غیره» ممنوع، و مدل
   **پیش از پایان شمارشِ خودش را چک کند**. مدل‌ها وقتی تعداد را نمی‌دانند،
   طبیعتاً خلاصه می‌کنند.

و کنارِ این‌ها: `max_tokens` را با **حجمِ واقعیِ خروجی** اندازه بگیر، نه با
پیش‌فرضِ کپی‌شده؛ خروجیِ n ردیفی به بودجهٔ n ردیفی نیاز دارد.

## 🧪 نمونه کد (Anonymized)

```python
TOTAL_CAP, FILE_CAP, MIN_CHARS = 360_000, 60_000, 4_000

def fit_sources(sources: list[tuple[str, str]]) -> tuple[list, list[str]]:
    """همه‌ی منابع را در بودجه جا بده — هیچ‌کدام را کاملاً حذف نکن."""
    warns: list[str] = []
    n = len(sources)
    if n == 0:
        return [], warns

    share = max(TOTAL_CAP // n, 0)
    if share < MIN_CHARS:                     # آخرین چاره، و با صدای بلند
        keep = max(TOTAL_CAP // MIN_CHARS, 1)
        warns.append(
            f"{n} source(s) selected; only the first {keep} fit. "
            f"Send the remaining {n - keep} in a second pass."
        )
        sources, n, share = sources[:keep], keep, MIN_CHARS

    fitted = []
    for name, text in sources:
        cap = min(share, FILE_CAP)
        if len(text) > cap:
            warns.append(f"'{name}': {len(text):,} → {cap:,} chars (trimmed).")
            text = text[:cap]
        fitted.append((name, text))
    return fitted, warns


def build_prompt(sources, warnings_out: list[str] | None = None) -> str:
    fitted, warns = fit_sources(sources)
    if warnings_out is not None:
        warnings_out.extend(warns)

    parts = [
        f"Exact number of sources below: {len(fitted)}.",
        f"MANDATORY: process ALL {len(fitted)}, one by one, completely. "
        f"Never summarize, never write 'etc.', never skip one. "
        f"Before finishing, count your own output and verify it covers all {len(fitted)}.",
    ]
    parts += [f"[source: {n}]\n{t}" for n, t in fitted]
    if warns:
        parts.append(
            "NOTE: some sources were trimmed (see below). Do NOT present the "
            "result as complete; state what was missing.\n- " + "\n- ".join(warns)
        )
    return "\n\n".join(parts)
```

سمتِ API و UI:

```python
warns: list[str] = []
prompt = build_prompt(sources, warnings_out=warns)
...
return {"result": result, "input_warnings": warns}   # کاربر باید ببیند
```

## ⚠️ نکات حیاتی / Pitfalls

- **`[:N]` روی یک لیست، یک باگِ داده است، نه یک بهینه‌سازی.** هر `[:` در مسیرِ
  ساختِ پرامپت را مشکوک بدان و دنبالِ اعلامش بگرد.
- **لاگِ سرور اعلام نیست.** اگر هشدار به چشمِ کاربری که خروجی را باور می‌کند
  نرسد، عملاً وجود ندارد.
- **عددِ واقعی بنویس**، نه «برخی موارد حذف شدند». کاربر باید بتواند تصمیم بگیرد
  (دسته‌بندی کند، فایل را بشکند، دوباره بفرستد).
- **دو سقفِ مستقل با یک علامتِ ظاهری:** ورودیِ بریده و خروجیِ بریده هر دو
  «ناقص» به نظر می‌رسند. هر دو را جدا بررسی کن.
- **الگو معمولاً جایِ دیگری در همان مخزن درست پیاده شده.** پیش از طراحیِ دوباره،
  مسیرهای مشابه را بگرد؛ کپیِ الگوی درست، هم ارزان‌تر است و هم سازگار.
- تقسیمِ منصفانه با بودجهٔ ثابت یعنی اضافه‌شدنِ یک منبع، سهمِ بقیه را کم می‌کند —
  همین درست است، ولی سهمِ فایلِ کوچک را بی‌دلیل هدر نده (`min(share, FILE_CAP)`).

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. همهٔ برش‌های ثابت (`[:N]`, `MAX_*`) را در مسیرِ ساختِ ورودیِ مدل فهرست کن.
2. هر سقفِ **تعدادی** را به بودجهٔ **مشترکِ** تقسیم‌شده تبدیل کن.
3. به تابعِ ساختِ پرامپت یک `warnings_out` اضافه کن و هر برش را با عدد ثبت کن.
4. هشدارها را هم داخلِ پرامپت و هم در پاسخِ API منتشر کن؛ در UI برجسته نشان بده.
5. تعدادِ دقیقِ منابع + قاعدهٔ «همه را پردازش کن، خلاصه نکن، خودت بشمار» را به
   پرامپت اضافه کن.
6. `max_tokens` را با بزرگ‌ترین خروجیِ معقول اندازه بگیر.
7. تست بنویس که **هر N منبع** در پرامپت دیده می‌شود و هر برش در `warnings` هست.

## 🔗 References
- مرتبط: [ai-call-deadlines-match-the-workload-and-retry-once]
- مرتبط: [ai-extract-to-db-attribute-dedup-log]
- مرتبط: [ai-generated-artifacts-spec-render-and-provenance-guard]
