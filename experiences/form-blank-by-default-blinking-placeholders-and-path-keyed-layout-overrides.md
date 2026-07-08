---
title: "فرم سندساز: خالیِ پیش‌فرض، متغیرهای چشمک‌زن تا پرشدن، و چینشِ path-keyed با دبل‌کلیک"
tags: ["forms", "document-generator", "ux", "react", "print", "layout-overrides", "bidi"]
topic_canonical: "form-blank-by-default-blinking-placeholders-and-path-keyed-layout-overrides"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-08T00:00:00Z"
created_at: "2026-07-08T00:00:00Z"
updated_at: "2026-07-08T00:00:00Z"
merged_from: []
---

# Document-form UX: blank by default, blink until filled, dblclick layout overrides

## 🎯 چالش / Challenge

فرمِ تولیدِ سندِ رسمی (نامه/قرارداد) سه مشکلِ UX داشت:
1. مقادیرِ پیش‌فرضِ «راحتی» (شهر، کارمزد، نوعِ تسهیلات، تاریخِ امروز…) قبل از
   انتخابِ مشتری روی سند می‌نشستند — سندِ «خالی» عملاً حاوی داده بود و خطرِ چاپِ
   دادهٔ اشتباه برای مشتریِ دیگر داشت.
2. معلوم نبود کدام جاهای سند هنوز پر نشده‌اند.
3. کاربر می‌خواست چینشِ هر بخشِ سندِ رندرشده را نقطه‌ای تنظیم کند بدونِ تغییرِ کد.

## 💡 راه‌حل / Solution

1. **دو مجموعه پیش‌فرض:** `EMPTY` (همهٔ فیلدها خالی — حالتِ آغازینِ state) و
   `INITIAL` (پیش‌فرض‌های راحتی — فقط پایهٔ عملِ «بارگیریِ رکورد»). پیش‌فرض‌ها
   نه حذف می‌شوند نه زود ظاهر؛ فقط به لحظهٔ بارگیریِ دادهٔ واقعی منتقل می‌شوند.
2. **متغیرِ چشمک‌زن:** یک کمکیِ واحد `V(key, placeholder)` که مقدارِ خالی را به
   `span` با انیمیشنِ پس‌زمینه و `title` = برچسبِ فیلد تبدیل می‌کند؛ برای
   متن‌های قالبی (`{Key}` در رشته‌ها) نسخهٔ node-ساز (`split` روی regex و
   Fragment). چاپ: `@media print { animation:none; background:none }`.
3. **Overrideهای چینش با کلیدِ مسیرِ DOM:** دبل‌کلیک → نزدیک‌ترین بلوکِ معنادار →
   کلید = `pageIndex|childIndexChain`؛ پنلِ شناور مقادیر (فونت/تراز/جهت/فاصله/
   آفست/عرض) را در `Record<key, Box>` می‌نویسد؛ یک effect بعد از **هر** رندر
   اول استایل‌های قبلی را پاک و بعد جدیدها را اعمال می‌کند (React نودها را
   بازمی‌سازد). ماندگاری: localStorage به تفکیکِ قالب + داخلِ snapshotِ رکورد.

## 🧪 نمونه کد (Anonymized)

```tsx
const V = (k: string, ph = '____') => f[k]?.trim()
  ? <>{f[k]}</>
  : <span className="blink-empty" title={LABELS[k]}>{ph}</span>

const elPath = (el: HTMLElement, page: HTMLElement) => {
  const chain = []; let cur = el
  while (cur !== page) { chain.unshift([...cur.parentElement.children].indexOf(cur)); cur = cur.parentElement }
  return `${pageIndex(page)}|${chain.join('.')}`
}
useEffect(() => {   // after EVERY render: clear previous, apply current, refit
  prevKeys.forEach((k) => clearStyles(elFromPath(k)))
  Object.entries(overrides).forEach(([k, b]) => applyStyles(elFromPath(k), b))
  prevKeys = Object.keys(overrides); refitPages()
})
```

## ⚠️ نکات حیاتی / Pitfalls

- **placeholder فارسی داخلِ سندِ LTR ممنوع** — قانونِ bidi: عبارتِ فارسی در متنِ
  LTR درهم می‌ریزد؛ placeholder فقط خط‌چین/نقطه‌چین باشد و توضیح در `title`.
- placeholderِ چشمک‌زن نباید شبیهِ دادهٔ واقعی باشد (مثلاً «Overdraft») — در تستِ
  «سندِ خالی» مثبتِ کاذب می‌سازد و کاربر هم ممکن است آن را داده بپندارد.
- **پاک‌سازی قبل از اعمال:** استایل‌هایی که خارج از React روی DOM می‌گذاری با
  رندر بعدی خودکار پاک نمی‌شوند؛ فهرستِ کلیدهای قبلی را نگه دار و اول صفر کن،
  وگرنه «بازنشانی» کار نمی‌کند.
- کلیدهای مسیرِ DOM به ساختارِ رندر حساس‌اند — به تفکیکِ قالب ذخیره‌شان کن و
  بدان که تغییرِ ساختاریِ بزرگِ قالب، overrideهای قدیمی را بی‌اثر می‌کند (نه خطا).
- سنجشِ headless: `getComputedStyle().borderTopStyle` با preflightِ Tailwind
  همیشه `solid` است (عرضِ صفر) — عرض را چک کن؛ و برای «متن سمتِ چپ است» جعبهٔ
  full-width گمراه‌کننده است — با `Range` خودِ متن را اندازه بگیر.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- [ ] state آغازینِ فرم را از پیش‌فرض‌های راحتی جدا کن (`EMPTY` جدا از `INITIAL`).
- [ ] همهٔ نقاطِ رندرِ متغیر را از `value || 'ph'` به کمکیِ واحدِ blink مهاجرت بده
  (شاملِ سربرگ/پانوشت/سلول‌های جدول/رشته‌های قالبی).
- [ ] قاعدهٔ چاپِ تمیز را همان اول بنویس و در تست چک کن.
- [ ] برای چینشِ کاربری، الگوی path-keyed overrides + پاک‌سازی-قبل-از-اعمال +
  ماندگاریِ per-template را بردار.
- [ ] تستِ headless: سندِ خالی هیچ دادهٔ واقعی نداشته باشد؛ پرشدنِ فیلد چشمکش را
  ببرد؛ override اعمال/ماندگار/بازنشانی شود.

## 🔗 References

- مرتبط: [paginated-doc-fixed-footer-cliff-slide-dont-push]
- مرتبط: [form-state-reset-on-entity-switch]
