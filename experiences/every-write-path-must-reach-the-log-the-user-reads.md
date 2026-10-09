---
title: هر مسیرِ نوشتن باید به همان لاگی برسد که کاربر می‌خواند
slug: every-write-path-must-reach-the-log-the-user-reads
date: 2026-10-09
severity: medium
area: [audit, backend, ux]
symptom: مالک چک‌لیست را کامل کرد ولی تبِ «لاگ‌ها» خالی ماند
root_cause: دو جدولِ شبیه‌به‌هم (JournalEntry و AuditLog)؛ endpoint فقط در اولی می‌نوشت و UI از دومی می‌خواند
binding: true
---

## درس

وقتی چند «لاگ» وجود دارد، برای هر endpoint نوشتن‌ی بپرس: **UI کدام را نشان می‌دهد؟** و تست را از همان
مسیرِ خواندنِ UI بنویس (`GET /api/audit/?account_no=…`)، نه از خودِ جدولِ نوشته‌شده. endpointهای جدید و
helperهای مشترک (مثل `_update_child`) باید پیش‌فرضِ لاگ داشته باشند، نه اختیاریِ فراموش‌شدنی.
