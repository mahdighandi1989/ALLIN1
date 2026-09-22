---
title: "Scrambled text is usually reversible data, not a broken font — decode it, prove it, then repair per chunk"
tags: ["encoding", "mojibake", "pdf", "text-extraction", "diagnosis", "data-repair"]
topic_canonical: "reversible-mojibake-decode-it-dont-guess-the-renderer"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-22T12:00:00Z"
created_at: "2026-09-22T12:00:00Z"
updated_at: "2026-09-22T12:00:00Z"
merged_from: []
---

# Scrambled text is reversible data, not a broken font

## 🎯 چالش / Challenge

کاربر می‌گوید متنِ یک جدول/گزارش «به‌هم‌ریخته» نشان داده می‌شود: به‌جای
`Statement NO` می‌بیند `Í¬¿¬»³»²¬ ÒÑ`. واکنشِ غریزی این است که دنبالِ **فونت**،
**charsetِ صفحه** یا **CSS** بگردیم — و معمولاً هیچ‌کدام نیست.

نکتهٔ تشخیصیِ کلیدی: در همان جدول **اعداد و تاریخ‌ها درست‌اند**. اگر مشکل فونت یا
charset بود، همه‌چیز خراب می‌شد. وقتی فقط **حروف** خراب‌اند و ارقام سالم، یعنی یک
**نگاشتِ کاراکتریِ معین** روی حروف اعمال شده — و نگاشتِ معین یعنی **برگشت‌پذیر**.

منبعِ رایجش: PDFای که فونتِ **subsetشده با encodingِ غیراستاندارد** جاسازی کرده.
صفحه بی‌عیب چاپ می‌شود، ولی **لایهٔ متنیِ زیرِ آن** کدپوینت‌های دیگری دارد. هر
چیزی که آن لایه را بخواند — استخراج‌گرِ متن، copy/paste، یا **یک مدلِ زبانی که
خودِ PDF را گرفته** — همان آشغال را وفادارانه بازتولید می‌کند.

## 💡 راه‌حل / Solution

**۱) نگاشت را کشف کن، حدس نزن.** چند رشتهٔ خراب را کنارِ حدسِ متنِ اصلی بگذار
(سرستون‌ها معمولاً قابلِ حدس‌اند: NO, Date, Amount, Name) و کدها را تفریق کن.
اگر رابطه ثابت بود، تشخیص تمام است. در موردِ PDFهای مذکور رابطه یک **بازتاب** است:

```
garbled = 0x120 - original        # involution: همان عمل، برعکسش هم می‌کند
A(0x41)..Z(0x5A) -> 0xDF..0xC6    a(0x61)..z(0x7A) -> 0xBF..0xA6
```

**۲) تشخیص را با «بازسازیِ خرابی» اثبات کن.** تستی بنویس که از **متنِ سالم**،
رشتهٔ **خراب** را می‌سازد و با آنچه واقعاً دیده شده مقایسه می‌کند. این فرق است
بینِ «به نظر می‌آید» و «ثابت شد».

**۳) ترمیم را per-chunk و محافظه‌کار کن.** بازهٔ آسیب‌دیده تقریباً همیشه با
کاراکترهای **مشروع** هم‌پوشانی دارد — اینجا گیومهٔ فارسی « (0xAB) و » (0xBB)، و
نیز ° ± ² ³ · §. پس تصمیم را برای **هر سلول/گرهٔ متنی جداگانه** بگیر با شرط‌های
سخت‌گیرانه: حداقل n کاراکترِ درون‌بازه، حداقل نسبتِ مشخصی از حروفِ آن قطعه، و
**هیچ حرفِ زبانِ بومی (فارسی/عربی/…) در آن قطعه نباشد**. یک جملهٔ فارسی با
«نقلِ‌قول» هرگز واجدِ شرایط نمی‌شود؛ یک سلولِ خراب همیشه می‌شود.

**۴) روی HTML، فقط text nodeها را بازنویسی کن.** هرگز روی رشتهٔ HTML
regex نزن: تگ، کلاس، `style`، `width` و `colspan` باید مو‌به‌مو سرِ جایشان بمانند.
`TreeWalker(SHOW_TEXT)` دقیقاً برای همین است.

**۵) در دو نقطه ببندش.**
- **جلوی ورودِ دوباره:** در تنها گلوگاهی که متن از استخراج بیرون می‌آید، ترمیم کن
  و **گزارش بده** (چند قطعه ترمیم شد) — ترمیمِ خاموش، همان خطایِ «برشِ خاموش» است.
- **دادهٔ موجود:** یک عملِ **یک‌کلیکی و برگشت‌پذیر** برای کاربر، که فقط وقتی
  چیزی واقعاً خراب است ظاهر شود. دادهٔ ذخیره‌شده را **پشتِ سرِ کاربر بازنویسی نکن**.

## 🧪 نمونه کد (Anonymized)

```ts
const PIVOT = 0x120
const inRange = (c: number) =>
  (c >= PIVOT - 0x7A && c <= PIVOT - 0x61) ||   // a..z
  (c >= PIVOT - 0x5A && c <= PIVOT - 0x41)      // A..Z
const NATIVE = /[؀-ۿ]/                // the local script — a veto

export function looksGarbled(s: string, minChars = 2, minRatio = 0.5) {
  if (!s || NATIVE.test(s)) return false        // never touch native-script text
  let mapped = 0, letters = 0
  for (const ch of s) {
    const m = inRange(ch.codePointAt(0)!)
    if (m) mapped++
    if (m || /\p{L}/u.test(ch)) letters++
  }
  return letters > 0 && mapped >= minChars && mapped / letters >= minRatio
}

export const repairText = (s: string) =>
  looksGarbled(s)
    ? [...s].map((ch) => (inRange(ch.codePointAt(0)!) ? String.fromCodePoint(PIVOT - ch.codePointAt(0)!) : ch)).join('')
    : s

/** structure-preserving: only text nodes are rewritten */
export function repairHtml(html: string) {
  const host = document.createElement('div')
  host.innerHTML = html
  const w = document.createTreeWalker(host, NodeFilter.SHOW_TEXT)
  let fixed = 0
  const nodes: Text[] = []
  for (let n = w.nextNode(); n; n = w.nextNode()) nodes.push(n as Text)
  for (const n of nodes) {
    const after = repairText(n.nodeValue || '')
    if (after !== n.nodeValue) { n.nodeValue = after; fixed++ }
  }
  return { html: fixed ? host.innerHTML : html, fixed }
}
```

و تستی که تشخیص را **اثبات** می‌کند:

```ts
const forged = plain.split('').map((c) => /[A-Za-z]/.test(c) ? String.fromCodePoint(0x120 - c.charCodeAt(0)) : c).join('')
expect(forged).toBe(theGarbledStringWeActuallySaw)
```

## ⚠️ نکات حیاتی / Pitfalls

- **«اعداد سالم‌اند» یعنی مشکل فونت نیست.** این اولین چیزی است که باید ببینی.
- **«فایلِ قبلی هم خراب شد» لزوماً یعنی رگرسیونِ رندر نیست** — اغلب یعنی آن فایل
  هم از همان منبعِ خراب ساخته شده و کاربر تازه متوجه شده. قبل از متهم‌کردنِ آخرین
  دیپلوی، **داده** را رمزگشایی کن.
- **regex روی رشتهٔ HTML ممنوع.** یک `style="width:30%"` قربانی‌شده، یعنی جدولِ
  کاربر خراب شد و ترمیم بدتر از خرابی شد.
- **نگاشت را کورکورانه روی کلِ سند اعمال نکن.** بازهٔ Latin-1 پر از کاراکترهای
  مشروع است؛ تصمیمِ per-chunk با وتویِ زبانِ بومی، تنها راهِ امن است.
- **ترمیم باید idempotent باشد** — کاربر دکمه را دوبار می‌زند.
- **حروفِ لهجه‌دارِ اروپایی (é ü ñ ç à) معمولاً ≥0xE0 هستند**، یعنی بیرونِ بازه —
  خوش‌شانسی‌ای که باید آگاهانه بررسی شود، نه فرض.
- **راهِ‌حلِ ریشه‌ای برای کاربر:** اگر منبع PDFِ خراب است، همان سند به‌صورت
  **تصویر/اسکن** یا **Excel/CSV** بدون این مشکل خوانده می‌شود (تصویر، خواننده را
  مجبور می‌کند از پیکسل بخواند نه از لایهٔ متنی). این را به کاربر بگو.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. بررسی کن کدام دسته‌ها خراب‌اند (حروف؟ ارقام؟ همه؟) — دامنه، منبع را لو می‌دهد.
2. چند جفتِ (خراب، سالمِ حدس‌زده) بساز و اختلافِ کدها را حساب کن.
3. اگر رابطه ثابت بود، تستی بنویس که خرابی را **بازتولید** کند.
4. یک تشخیصِ per-chunk با وتویِ زبانِ بومی و آستانه‌های صریح بنویس.
5. روی ساختار (HTML/DOCX/…) فقط گره‌های متنی را دست بزن.
6. در گلوگاهِ ورودی ترمیم کن **و گزارش بده**؛ برای دادهٔ موجود یک عملِ
   یک‌کلیکیِ برگشت‌پذیر بگذار.
7. علتِ ریشه‌ای را به صاحبِ داده اطلاع بده تا منبع را عوض کند.

## 🔗 References
- مرتبط: [silent-input-truncation-makes-partial-output-look-complete]
- مرتبط: [ai-extract-to-db-attribute-dedup-log]
