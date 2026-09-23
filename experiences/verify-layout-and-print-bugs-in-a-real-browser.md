---
title: "Layout and print bugs need a real browser, not reasoning — render it, measure it, then fix"
tags: ["css", "flexbox", "print", "debugging", "headless-browser", "rtl"]
topic_canonical: "verify-layout-and-print-bugs-in-a-real-browser"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-23T18:00:00Z"
created_at: "2026-09-23T18:00:00Z"
updated_at: "2026-09-23T18:00:00Z"
merged_from: []
---

# Layout and print bugs need a real browser

## 🎯 چالش / Challenge

کاربر اسکرین‌شات می‌فرستد: «فیلدهای این پنل از کادر بیرون زده». نگاه می‌کنی به
CSS، و **همه‌چیز منطقی به نظر می‌رسد**: کادر عرضِ ثابت دارد، ردیف‌ها flex‌اند،
اینput‌ها `flex:1` و `min-width:0` دارند. با استدلال به این می‌رسی که «باید جا
شود» — ولی نمی‌شود. بعد شروع می‌کنی به حدس‌زدنِ علت‌های دور (تداخلِ CSSِ صفحه،
Tailwind، مرورگرِ کاربر) و هر بار یک تغییرِ حدسی می‌فرستی.

چیدمان (و پرینت) **حاصلِ اجرای یک موتورِ واقعی** است، نه نتیجهٔ استدلال از روی
قواعد. jsdom هم چیدمان ندارد و کمکی نمی‌کند.

## 💡 راه‌حل / Solution

**۱) همان CSS را در یک مرورگرِ headless رندر کن و جعبه‌ها را اندازه بگیر.**
اغلب محیط‌های توسعه یک Chromium دارند (مثلاً از Playwright). یک HTMLِ حداقلی با
**markup و CSSِ واقعی** بساز و اسکرین‌شات/اندازه بگیر:

```bash
chromium --headless --disable-gpu --no-sandbox \
         --window-size=1366,768 --screenshot=out.png "file://$PWD/harness.html"
```

**CSS را از خودِ سورس استخراج کن، دستی بازنویسی نکن** — وگرنه داری نسخهٔ
خیالی‌ات را تست می‌کنی. (اولین تلاشِ من فقط خطوطی را برداشت که با `.mv-pp` شروع
می‌شدند و قاعدهٔ چندخطی را نصفه کرد؛ نتیجه گمراه‌کننده شد.)

**۲) اول باگ را بازتولید کن، بعد اصلاح را بسنج.** اگر هارنس باگ را نشان نداد،
هارنس ناقص است — نه اینکه باگ وجود ندارد.

**۳) درسِ فنیِ خودِ این مورد (بسیار پرتکرار):** حداقلِ خودکارِ یک flex item
برابرِ `min-content` محتوایش است. `<input>` عرضِ ذاتیِ بزرگی دارد، پس
`min-width:0` روی **input** فقط خودِ input را آزاد می‌کند، نه **ردیفِ** والد را.
هر سطحِ زنجیره باید `min-width:0` بگیرد:

```css
.row        { display:flex; min-width:0 }
.cols       { display:flex; min-width:0 }
.cols .row  { flex:1 1 0;   min-width:0 }
.row input  { flex:1 1 0;   min-width:0; box-sizing:border-box }
```

و پنل‌های شناور را همیشه به viewport مقید کن:
`width:min(268px,calc(100vw - 28px)); max-height:calc(100vh - 110px); overflow:auto`.

**۴) پرینت: رنگِ پس‌زمینه به‌صورتِ پیش‌فرض چاپ نمی‌شود.** تنها راهِ درخواستش
`print-color-adjust: exact` (+ `-webkit-`) است. و اگر باید روی چاپگرِ
سیاه‌وسفید هم دیده شود، **رنگِ روشن انتخاب کن** تا خاکستری دربیاید نه سیاه —
و همین را با تستِ روشنایی قفل کن.

**۵) این قراردادها را با تستِ سورس ببند.** build سبز هیچ‌کدام را نمی‌گیرد:

```ts
expect(rule(CSS, '.row{')).toContain('min-width:0')
expect(BANNER).toContain('print-color-adjust: exact')
const lum = rgbOf(BANNER).reduce((a,b)=>a+b)/3
expect(lum).toBeGreaterThan(170)   // grey, not black, in B/W
```

## 🧪 نمونه کد (Anonymized)

استخراجِ قاعده از سورس (نه بازنویسیِ دستی):

```python
lines = open('component.tsx').read().splitlines()
i0 = next(i for i,l in enumerate(lines) if l.strip().startswith('.panel{'))
i1 = next(i for i,l in enumerate(lines) if l.strip().startswith('.panel .last{'))
css = "\n".join(l.strip() for l in lines[i0:i1+1])
assert 'min-width:0' in css          # guard: the extraction really caught it
```

پروبِ اندازه‌گیری داخلِ همان صفحه:

```js
const p = document.querySelector('.panel')
console.log(p.scrollWidth, p.clientWidth,
  [...p.querySelectorAll('.row')].map(r => r.getBoundingClientRect().left))
```

## ⚠️ نکات حیاتی / Pitfalls

- **jsdom چیدمان ندارد** — `offsetWidth` همیشه صفر است. برای منطقِ صفحه‌بندی
  می‌شود getter جعلی گذاشت، ولی برای «آیا بیرون می‌زند؟» فقط مرورگرِ واقعی.
- **CSS را دستی به هارنس کپی نکن**؛ از سورس بکش، و با یک assert مطمئن شو کامل
  کشیده شده.
- **RTL جهتِ سرریز را عوض می‌کند** — در `dir="rtl"` محتوا به **چپ** بیرون می‌زند،
  که موقعِ نگاه به اسکرین‌شات گیج‌کننده است.
- **بک‌تیک داخلِ کامنتِ CSS در یک template literal، build را می‌شکند.** اگر CSS را
  در <style>{`…`}</style> می‌نویسی، در توضیحاتت از بک‌تیک استفاده نکن.
- **`transform` باعثِ reflow نمی‌شود:** اگر ویرایشگرِ چیدمانت با translate
  جابه‌جا می‌کند، عناصر روی هم می‌افتند. اگر «بقیه باید همراه بیایند»، باید
  خودت دلتا را به آن‌ها هم اعمال کنی.
- **برای «گروهی جابه‌جا کن» ترتیبِ DOM را مرجع بگیر** (`querySelectorAll` +
  یک `data-*` id)، نه ترتیبِ mountِ React — این دو یکی نیستند.
- **همهٔ گروه را در یک state update بنویس**؛ وگرنه هر pointermove ده‌ها آپدیت
  صف می‌کند و درگ کند می‌شود.
- **یک راهِ فرار بگذار** (مثلاً Alt) تا کاربر بتواند فقط یک عنصر را جابه‌جا کند.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. اگر شکایت «ظاهری» است، اول در مرورگرِ headless بازتولیدش کن.
2. CSS/markup را از سورس بکش؛ هارنس را با دادهٔ واقعی بساز.
3. اندازه بگیر (`getBoundingClientRect`, `scrollWidth`) — حدس نزن.
4. اصلاح را در همان هارنس بسنج، بعد وارد کد کن.
5. قرارداد را با تستِ سورس قفل کن، چون build این کلاس را نمی‌گیرد.
6. برای پرینت: `print-color-adjust`، و رنگِ روشن برای خوانایی در سیاه‌وسفید.

## 🔗 References
- مرتبط: [rendering-bugs-get-ground-truth-before-theorising]
- مرتبط: [flow-long-content-across-pages-dont-shrink-to-fit-one]
