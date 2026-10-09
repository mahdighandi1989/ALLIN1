---
title: "seed موقع startup نباید چیزی را که sync بعدی ساخته پاک کند"
tags: ["ai-models", "startup", "seed", "sync"]
topic_canonical: "a-startup-seed-must-not-prune-what-a-later-sync-created"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-10-09T00:00:00Z"
created_at: "2026-10-09T00:00:00Z"
updated_at: "2026-10-09T00:00:00Z"
merged_from: []
---

# seed موقع startup نباید چیزی را که sync بعدی ساخته پاک کند

## 🎯 چالش
مدل‌های جدید با sync اضافه می‌شدند و «یه مدت» درست بود، بعد به قدیمی‌های هاردکد برمی‌گشت. seed کاتالوگ در هر
deploy ردیف‌های «غیرِ کاتالوگ» را هرس می‌کرد؛ شرطش فقط `source != custom` بود، پس ردیف‌های discovered هم می‌رفتند و
sync بعدی (marker ۲۴ساعته) دیر می‌رسید.

## 💡 راه‌حل
هر لایه فقط ردیف‌های **خودش** را هرس کند (`source == "catalog"`). و اگر state مشتق‌شده خالی ولی marker «تازه» است،
marker را نادیده بگیر (خودترمیمی) به‌جای انتظار.

## ⚠️ نکات
- «یه مدت درست می‌شود و برمی‌گردد» = چیزی در چرخهٔ restart/deploy آن را بازنویسی می‌کند؛ اول seed/startup را بخوان.
- تست: seed را دو بار اجرا کن با یک ردیف discovered بینشان.
