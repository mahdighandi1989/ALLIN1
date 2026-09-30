---
title: "در JS عملگر repeat فقط به آخرین رشته می‌چسبد"
tags: ["javascript", "templates", "tables"]
topic_canonical: "js-repeat-binds-tighter-than-plus"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-30T00:00:00Z"
created_at: "2026-09-30T00:00:00Z"
updated_at: "2026-09-30T00:00:00Z"
merged_from: []
---

# `'<td>' + X + '</td>'.repeat(6)` یک سلول می‌سازد، نه شش

## 🎯 چالش
جدول‌های شش‌ستونیِ قالب فقط یک سلول در بدنه داشتند؛ `.repeat` قبل از `+` اعمال می‌شود و فقط `'</td>'` را تکرار کرد. تست و build سبز ماندند.

## 💡 راه‌حل
هر جا قطعهٔ HTML تکرار می‌شود، آن را در template literal بگذار: `` `<td>${X}</td>`.repeat(n) ``. برای قالب‌های جدول، تعدادِ سلولِ هر سطر را در تست با تعدادِ ستونِ سرتیتر مقایسه کن.
