---
title: "یک شناسه با املاهای متعدد را با کلیدِ بدون‌جداکننده تطبیق بده، نه با نوع/مبلغ"
tags: ["dedup", "identifiers", "normalization", "import"]
topic_canonical: "same-identifier-many-spellings-match-on-a-separator-free-key"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-10-08T00:00:00Z"
created_at: "2026-10-08T00:00:00Z"
updated_at: "2026-10-08T00:00:00Z"
merged_from: []
---
# درس
شناسهٔ کسب‌وکاری (مثلاً شمارهٔ آفرلتر) با فاصله/خط‌تیره/نویسهٔ نامرئی/ارقام فارسی
متفاوت تایپ می‌شود. (۱) یک canonicalizer واحد که چیزِ نامطمئن را حدس نزند؛ (۲) مقایسه با
کلیدِ حذف‌جداکننده؛ (۳) همهٔ مسیرهای ورودی (AI، اکسل، دستی) همان کلید را بزنند؛
(۴) دو شناسهٔ متفاوت هرگز به‌خاطر هم‌نوعی ادغام نشوند؛ (۵) فیلدِ نام فقط fill‑empty پر شود.
