---
title: "انتخاب‌گر فقط نسلِ جاری را نشان دهد، نه هرچه ارائه‌دهنده فهرست می‌کند"
tags: ["ai-models", "sync", "ui", "picker"]
topic_canonical: "a-picker-shows-the-current-generation-not-everything-the-provider-lists"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-10-06T00:00:00Z"
created_at: "2026-10-06T00:00:00Z"
updated_at: "2026-10-06T00:00:00Z"
merged_from: []
---

# انتخاب‌گر فقط نسلِ جاری را نشان دهد

## 🎯 چالش
حتی با sync و رتبه‌بندیِ درست، مالک «مدل‌های قدیمی» را در dropdown می‌دید: ارائه‌دهنده نسخه‌های قدیمی را هنوز فهرست می‌کند و sync فقط مدل‌های حذف‌شده را برمی‌دارد.

## 💡 راه‌حل
در لایهٔ نمایش (نه DB) برای هر ارائه‌دهنده+رده فقط جدیدترین نسخهٔ قابلِ‌رتبه را نگه دار و هم‌نام‌ها را یکی کن؛ ناشناخته/preview/custom بمانند. داده حذف نمی‌شود و Settings همه را نشان می‌دهد.

## ⚠️ نکات
- «به‌روز» را از دید کاربرِ picker بسنج، نه فقط وضعیتِ جدول.
