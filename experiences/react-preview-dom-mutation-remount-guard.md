---
title: "React preview over mutated DOM: remount guard scoped to state changes, not every render"
tags: ["react", "dom-mutation", "error-boundary", "selection", "rich-text", "ux"]
topic_canonical: "react-preview-dom-mutation-remount-guard"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-29T14:00:00Z"
created_at: "2026-07-29T14:00:00Z"
updated_at: "2026-07-29T14:00:00Z"
---

# گاردِ remount برای پیش‌نمایشی که DOMاش را خودمان دستکاری می‌کنیم

وقتی افکتِ بعدِ رندر، متنِ زیرِ دستِ React را span-wrap می‌کند (هایلایت/
markهای انتخابی)، React ممکن است هنگامِ diff به removeChild-crash بخورد.
ضدحملهٔ اولیه (کلیدِ remount که «هر رندر» عوض می‌شود) کرَش را می‌بندد ولی
تعاملِ کاربر را می‌کشد. نسخهٔ پایدارِ الگو در به‌روزرسانیِ زیر.

## Update 2026-07-29 (v87) — remount گارد را به «تغییرِ وضعیت» ببند، نه «هر رندر»

remountِ هر-رندر (گاردِ v38) ضدحملهٔ درستی بود ولی عوارضش UX را کشت:
هر رندرِ نامرتبط سلکتِ کاربر را می‌کشد و کنترل‌ها «بی‌اثر» به نظر
می‌رسند. الگوی درست: کلید را useMemo روی خودِ وضعیتِ قالب‌بندی بگذار
(remount فقط وقتی markها/متن عوض شدند) و کرَشِ نادرِ diff-روی-DOMِ
دستکاری‌شده را ErrorBoundary با gen-remount جذب کند — بدونِ دورریختنِ
دادهٔ کاربر؛ wipe فقط برای کرَشِ تکرارشونده (قطعی). و mark-spanهای
تزریقی هرگز نباید hostِ کلیدِ path شوند — selection داخلِ متنِ
استایل‌خورده باید به والدِ واقعی بالا برود وگرنه toggle/undo کور می‌شود.
