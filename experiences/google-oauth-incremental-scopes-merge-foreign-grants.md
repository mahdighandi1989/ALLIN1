---
title: "OAuth گوگل: include_granted_scopes گرنت‌های بی‌ربطِ همان client را به درخواستت می‌چسباند و می‌تواند لاگین را قفل کند"
tags: ["auth", "google", "oauth", "scopes", "reliability"]
topic_canonical: "google-oauth-incremental-scopes-merge-foreign-grants"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-01T00:00:00Z"
created_at: "2026-09-01T00:00:00Z"
updated_at: "2026-09-01T00:00:00Z"
merged_from: []
---

# Google OAuth: incremental authorization merges FOREIGN grants into your request — and can hard-block login

## 🎯 چالش / Challenge

لاگینِ گوگلِ production یک‌باره برای مالک به‌کل قفل شد: «Access blocked —
Error 400: invalid_request … scopes that cannot be requested together:
[drive.file, youtube.force-ssl, youtube, youtube.upload]». اپِ ما اصلاً
scope یوتیوبی نمی‌خواست؛ درخواستِ خودِ ما فقط openid/email/profile +
drive.file بود. مقصر `include_granted_scopes=true` بود: گوگل با این پارامتر
«همهٔ scopeهایی که این حساب قبلاً به همین client_id داده» را در گرنتِ جاری
ادغام می‌کند — و حسابِ مالک از یک ابزارِ بیرونی که همان client را استفاده
می‌کرد گرنتِ YouTube داشت. سیاستِ گوگل ترکیبِ drive.file + YouTube را در یک
درخواست رد می‌کند ⇒ هر بار 400، بدونِ هیچ تغییری در کدِ ما.

## 💡 راه‌حل / Solution

- اگر اپ هر بار **همهٔ** scopeهای لازمش را صریح می‌خواهد (الگوی این اپ)،
  incremental authorization هیچ سودی ندارد — `include_granted_scopes` را
  نفرست. refresh token با `access_type=offline` + `prompt=consent` تضمین
  می‌شود، نه با این پارامتر.
- طبق قانون ۳ (auth حساس است): حذف نکن — پشتِ فلگِ config بگذار
  (`GOOGLE_INCLUDE_GRANTED_SCOPES`، پیش‌فرض False) تا رفتارِ قبلی با یک env
  برگردد.
- تستِ قفل‌کننده: URL لاگین به‌طورِ پیش‌فرض پارامتر را ندارد ولی scopeهای
  لازم + offline/consent را دارد؛ با فلگ روشن پارامتر برمی‌گردد.

## ⚠️ نکات حیاتی / Pitfalls

- خطا در کنسولِ گوگل ظاهر می‌شود نه در لاگِ سرورِ ما — کاربر فقط «Access
  blocked» می‌بیند؛ جزئیاتِ واقعی در «error details» صفحهٔ گوگل است و
  فهرستِ scopeها آن‌جا لو می‌دهد که گرنتِ خارجی ادغام شده.
- **client_id مشترک بینِ چند ابزار = ریسکِ پنهان:** هر گرنتی که ابزارِ دیگر
  می‌گیرد، با include_granted_scopes واردِ درخواست‌های تو می‌شود. اگر ادغامِ
  افزایشی واقعاً لازم است، هر ابزار client جدا بگیرد.
- راهِ نجاتِ بدونِ دیپلوی (برای کاربرِ قفل‌شده): حذفِ دسترسیِ همان client در
  myaccount.google.com/connections — ولی fix واقعی در کد است، وگرنه اولین
  گرنتِ خارجیِ بعدی دوباره قفلش می‌کند.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- [ ] در هر فلوی OAuth، پارامترهای «میان‌بر» (incremental scopes، هر چیزی که
  state خارج از درخواستِ جاری را وارد می‌کند) را فقط با دلیلِ مکتوب نگه دار.
- [ ] برای هر خطای «Access blocked»ِ گوگل، اول فهرستِ scopeهای داخلِ error
  details را با scopeهای کدت مقایسه کن — اضافه‌ها از گرنت‌های قبلی می‌آیند.
