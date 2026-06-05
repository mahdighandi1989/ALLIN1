# 📚 Experiences Folder — Format Guide

این فولدر تجربیات قابل‌استفاده‌مجدد مهندسی را نگه می‌دارد. هر فایل یک
چالش حل‌شده را به شکل **project-agnostic** (مستقل از پروژهٔ خاص) ثبت
می‌کند تا بتوان آن را در پروژه‌های دیگر دوباره به کار برد.

## 📁 نام‌گذاری فایل‌ها

- یک فایل برای هر تجربه: `{topic-slug}.md` (kebab-case)
- مثال‌های خوب:
  - `google-oauth-login.md`
  - `fastapi-rate-limiting.md`
  - `nextjs-static-export-edge-cases.md`
- مثال بد: `bug-fix-in-myproject.md` (نام پروژه ممنوع)

## 📋 ساختار اجباری هر فایل

هر فایل **باید** با frontmatter YAML شروع شود:

```yaml
---
title: "عنوان کوتاه — همان slug ولی خواناتر"
tags: ["auth", "google-oauth", "frontend"]
topic_canonical: "google-oauth-login"
source:
  type: "manual" | "chat-import" | "claude-code-task"
  origin: "claude-code" | "chatgpt" | "gemini" | "user-typed"
  imported_at: "2026-06-05T10:00:00Z"
created_at: "2026-06-05T10:00:00Z"
updated_at: "2026-06-05T10:00:00Z"
merged_from: []
---
```

سپس بخش‌های markdown به این ترتیب:

```markdown
# Topic Title

## 🎯 چالش / Challenge
[چه مشکلی حل می‌شد — کلی، بدون نام پروژه]

## 💡 راه‌حل / Solution
[راه‌حل قدم‌به‌قدم، قابل تعمیم]

## 🧪 نمونه کد (Anonymized)
[snippet با نام‌های عمومی، نه مال این پروژه]

## ⚠️ نکات حیاتی / Pitfalls
[خطاهای رایج وقتی این الگو را در جای دیگر استفاده می‌کنی]

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere
[ترجمهٔ این الگو به پروژه‌های دیگر — generic checklist]

## 🔗 References
- منبع اولیه: [chat-export-2026-06-04.txt, line 42]
- مرتبط: [other-experience-slug]
```

## 🤖 دستورالعمل برای مدل‌های AI (Claude Code, GPT, Gemini, …)

وقتی کاربر از تو می‌خواهد یک تجربه را در این فولدر ثبت کنی:

1. **اول بخوان**: تمام فایل‌های موجود را چک کن. اگر `topic_canonical`
   مشابهی هست، **MERGE نه REPLACE**:
   - محتوای اصلی را نگه دار
   - بخش جدید زیر «## Update YYYY-MM-DD» اضافه کن
   - `merged_from:` در frontmatter آپدیت کن

2. **همیشه عمومی بنویس**:
   - ❌ "در پروژهٔ MyApp ما X کردیم"
   - ✅ "وقتی X را پیاده می‌کنیم..."
   - نام فایل‌های مخصوص پروژه → جایگزین با placeholder عمومی
     (مثلاً `MyApp.tsx` → `AuthPage.tsx`)

3. **بخش "How to Apply Elsewhere" اجباری است** — این مهم‌ترین بخش است
   که تجربه را reusable می‌کند.

4. **slug را canonical نگه دار**: `topic_canonical` در frontmatter باید
   یکپارچه باشد تا dedup در آینده کار کند.

5. **References صادق باشن**: اگر مطلب از یک چت import شد، منبع را در
   `source:` و در پایان فایل ذکر کن.

## 📤 سینک با Knowledge Center

این فولدر به‌صورت خودکار توسط صفحهٔ **مرکز دانش** (/knowledge-center)
خوانده می‌شود. فایل‌هایی که فرمت بالا را رعایت کنند با metadata کامل در
کاتالوگ ظاهر می‌شوند؛ فایل‌های بدفرمت در دسته «unparsed» می‌روند.

---
_این فایل توسط Knowledge Center سرویس به‌صورت خودکار ساخته شده.
ویرایش کن اگر می‌خواهی template را برای پروژهٔ خاص خودت گسترش بدهی._
