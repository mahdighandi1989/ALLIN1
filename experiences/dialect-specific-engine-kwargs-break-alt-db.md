---
title: "Dialect-specific engine kwargs silently break the alternate database path"
tags: ["backend", "sqlalchemy", "config", "sqlite", "postgres"]
topic_canonical: "dialect-specific-engine-kwargs-break-alt-db"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-03T05:30:00Z"
created_at: "2026-07-03T05:30:00Z"
updated_at: "2026-07-03T05:30:00Z"
merged_from: []
---

# Dialect-specific engine kwargs break the alternate DB path

## 🎯 چالش / Challenge

پروژه رسماً دو مسیر دیتابیس داشت: Postgres در production و SQLite برای dev/test.
ولی `create_engine`/`create_async_engine` با پارامترهای pool مخصوص QueuePool
(`pool_size`, `max_overflow`, `pool_recycle`) به‌صورت بی‌شرط ساخته می‌شد.
SQLite از NullPool استفاده می‌کند و این kwargs را نمی‌پذیرد ⇒ بوتِ اپ با
`DATABASE_URL=sqlite:…` با TypeError می‌مرد. تست‌ها این را نمی‌گرفتند چون
conftest انجینِ خودش را می‌سازد — فقط اجرای واقعیِ اپ روی SQLite می‌شکست؛
یعنی «مسیر مستندشده» ماه‌ها خراب بود و کسی نفهمید.

## 💡 راه‌حل / Solution

پارامترهای وابسته به dialect را شرطی کن و kwargs را از URL مشتق کن:

```python
pool_kwargs = {} if url.startswith("sqlite") else {
    "pool_size": settings.POOL_SIZE,
    "max_overflow": settings.MAX_OVERFLOW,
    "pool_recycle": settings.POOL_RECYCLE,
}
engine = create_async_engine(url, connect_args=connect_args, **pool_kwargs)
```

## ⚠️ نکات حیاتی / Pitfalls

- conftest تست‌ها معمولاً انجین جدا می‌سازند ⇒ باگِ ساخت انجینِ اپ از دید suite پنهان است.
  یک تست/اسموک که **خود ماژول database اپ** را با URL سکیولایت import/بسازد لازم است.
- همین الگو برای `connect_args` هم صادق است (مثلاً `ssl` برای asyncpg، `check_same_thread`
  برای sqlite) — هر kwarg وابسته به درایور باید از URL مشتق شود.
- «documented dev path» را هر چند وقت یک‌بار واقعاً اجرا کن (boot smoke)، نه فقط تست‌ها.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- هرجا یک URL دیتابیسِ قابل‌تعویض داری، ساخت انجین را در یک تابع
  `build_engine(url)` جمع کن که kwargs را بر اساس scheme انتخاب می‌کند و برایش
  تست unit با هر دو scheme بنویس.
- در CI یک job سبک «app boots with sqlite» اضافه کن (uvicorn تا health check).

## 🔗 References

- ALLIN1: `backend/app/database.py` pool kwargs — AUDIT_LOG 2026-07-03
