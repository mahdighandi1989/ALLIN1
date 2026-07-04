---
title: "AI edit suggestions: propose → server-side locate-guard → human review → surgical apply"
tags: ["ai", "llm", "review-first", "safety", "contenteditable", "rtl"]
topic_canonical: "ai-edit-suggestions-review-first-with-locate-guard"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-04T08:30:00Z"
created_at: "2026-07-04T08:30:00Z"
updated_at: "2026-07-04T08:30:00Z"
merged_from: []
---

# AI edit suggestions — propose, guard, review, apply surgically

## 🎯 چالش / Challenge

می‌خواهیم یک مدلِ زبانی روی یک سندِ کاربر (متن/HTML با جدول و قالب‌بندی) «دخل و
تصرفِ زیاد» انجام دهد: اصلاح املا/نگارش، مغایرت‌ها، حرفه‌ای‌سازی، اعتبارسنجی با
پایگاه‌داده. سه خطرِ اصلی: (۱) مدل چیزهایی «توهم» می‌کند که در سند نیست، (۲) اعمالِ
مستقیمِ خروجیِ مدل، ساختارِ HTML/جدول/قالب را نابود می‌کند، (۳) کاربر کنترل را از
دست می‌دهد و تغییراتِ ناخواسته اعمال می‌شوند.

## 💡 راه‌حل / Solution

الگوی چهارمرحله‌ای **propose → guard → review → surgical apply**:

1. **Propose (سرور):** مدل فقط یک JSONِ سخت از تغییراتِ *پیشنهادی* برمی‌گرداند؛ هر
   تغییر یک `op` دارد: `text_replace` (find/replace جراحی‌وار)، `set_field`
   (فیلدِ کوتاه)، یا `note` (فقط مشاوره). به مدل «حقایقِ معتبرِ پایگاه‌داده» را می‌دهی
   تا اعتبارسنجی/مغایرت‌یابی کند — ولی او فقط پیشنهاد می‌دهد.
2. **Guard (سرور، قطعی):** گیتِ اعتبارسنجیِ کدنویسی‌شده تصمیم می‌گیرد کدام پیشنهاد امن
   است. مهم‌ترین قاعده: یک `text_replace` فقط وقتی نگه داشته می‌شود که `find` عیناً
   (یا با نرمال‌سازیِ فاصله) در متنِ فعلیِ همان فیلد **وجود داشته باشد** — ضدِ توهم.
   `set_field` فقط برای فیلدهای allow-listِ کوتاه (نه بدنه‌ی HTML).
3. **Review (کلاینت):** فهرست با چک‌باکس، دسته/شدت و diffِ before→after؛ کاربر
   تیک/برمی‌دارد. `note`ها مشاوره‌ای‌اند و اعمال نمی‌شوند.
4. **Surgical apply (کلاینت):** `text_replace` فقط محتوای **یک TEXT NODE** را
   بازنویسی می‌کند تا تگ‌ها/جدول/بولد سالم بمانند، و متنِ جایگزین literal درج می‌شود
   (نه HTML). موردی که در متنِ فعلی پیدا نشود، رد و گزارش می‌شود.

## 🧪 نمونه کد (Anonymized)

```python
# Server-side locate-guard — the anti-hallucination gate
def keep_change(ch, field_plaintext):
    if ch["op"] == "text_replace":
        find = ch.get("find", "")
        return bool(find) and (find in field_plaintext or norm(find) in norm(field_plaintext))
    if ch["op"] == "set_field":
        return ch["field"] in SCALAR_ALLOWLIST and ch.get("after") is not None
    return ch["op"] == "note"   # advisory, always kept, never applied
```

```js
// Client-side surgical apply — never touches tags, replacement is literal text
function applyTextReplace(html, find, replace) {
  const box = document.createElement('div'); box.innerHTML = html
  const w = document.createTreeWalker(box, NodeFilter.SHOW_TEXT)
  for (let n; (n = w.nextNode());) {
    const i = (n.textContent || '').indexOf(find)
    if (i !== -1) { n.textContent = n.textContent.slice(0,i) + replace + n.textContent.slice(i+find.length); break }
  }
  return box.innerHTML
}
```

## ⚠️ نکات حیاتی / Pitfalls

- **هرگز خروجی مدل را به‌عنوان HTML درج نکن** — literal-text درج کن؛ وگرنه تزریق/خرابیِ ساختار.
- گیتِ locate باید سمتِ **سرور** باشد (منبعِ حقیقت)، نه فقط UI.
- برای متنِ فارسی/RTL، در تستِ مرورگر از `insertText` (اتمیک) استفاده کن نه تایپِ
  کاراکتری؛ تایپِ سریع با re-renderِ React مسابقه می‌دهد و متنِ RTL را به‌هم می‌ریزد
  (این یک آرتیفکتِ تست است، نه باگِ محصول — با `insertText` رفع می‌شود).
- `find` را کوتاه و یکتا بخواه؛ اگر چند text-node را در بر بگیرد، match تک‌نودی رد می‌شود —
  آن را «قابلِ مکان‌یابی نبود» گزارش کن، نه اینکه بی‌صدا اعمالِ ناقص کنی.
- مدل‌ها را بر اساس اولویت لیست کن و انتخاب را به کاربر بده؛ مسیرِ «no model» باید
  friendly باشد (پیام: در تنظیمات یک مدل فعال کن)، نه ۵۰۰.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- هر جا می‌خواهی LLM روی محتوای ساختارمندِ کاربر ویرایش کند (فرم، سند، پیکربندی):
  همان چهار مرحله را پیاده کن. `op`ها را متناسب کن (`set_field`/`text_replace`/`note`).
- گیتِ سرور را با تست‌های واحد قفل کن: «find موجود بماند»، «find غایب رد شود»،
  «note همیشه بماند ولی applicable=false»، «op ناشناخته رد شود».
- برای اعمال، همیشه یک لایه‌ی «چه چیزی واقعاً اعمال شد / چه چیزی پیدا نشد» به کاربر بده.

## 🔗 References

- ALLIN1: `services/letter_assistant.py` + `routers/letter_ai.py` + `app/letter/page.tsx` — AUDIT_LOG 2026-07-04
- مرتبط: `conservative-dedup-compare-all-columns`, `upsert-keys-must-cover-every-caller`
