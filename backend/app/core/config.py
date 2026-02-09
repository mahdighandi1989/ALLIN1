# دستورات پیشنهادی برای اعمال تغییرات

# 1. حذف فایل کانفیگ قدیمی
git rm backend/app/config.py

# 2. افزودن تغییرات به stage
git add backend/app/core/config.py
git add backend/app/main.py

# 3. کامیت کردن تغییرات
git commit -m "refactor(config): Unify backend configuration and fix main entrypoint

- Removed redundant and conflicting `backend/app/config.py`.
- Established `backend/app/core/config.py` as the single source of truth for all settings.
- Rewrote `backend/app/main.py` to correctly load settings, configure CORS, and mount the static frontend.
- Added a mock `/api/dashboard` endpoint to ensure the dashboard page receives data.

This resolves the root cause of application-wide API failures and stabilizes the system."

# 4. پوش کردن به ریپازیتوری
git push origin main