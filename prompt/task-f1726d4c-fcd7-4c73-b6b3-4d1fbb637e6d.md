---
task_id: f1726d4c-fcd7-4c73-b6b3-4d1fbb637e6d
title: رفع 500، پیاده‌سازی OAuth و بهبود UI
type: idea
priority: medium
execution_priority: 3200
status: pending
external_status: done
verification_status: error
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-06-06T07:33:27.680004+00:00'
updated_at: '2026-06-07T17:00:41.612267+00:00'
target_files:
- backend/app/api/endpoints/auth.py
- backend/app/services/google_auth_service.py
- frontend/src/app/login/page.tsx
- backend/app/api/endpoints/users.py
---

# رفع 500، پیاده‌سازی OAuth و بهبود UI

## Raw Idea

```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره

2- باید امکان لاگین از طریق جیمیل فراهم باشه

3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
5- از منظر ظاهری خیلی آشفته اس
6- در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()


---
## 📚 پروژه‌های مرجع (الهام از پیاده‌سازی‌های موجود)
_در زیر خلاصهٔ ساختار/فایل‌های پروژه‌های زیر آمده است. از این منابع به‌عنوان الگو/الهام استفاده کن و در پرامپت نهایی به فایل‌ها/الگوهای مرتبط ارجاع بده._

## 📚 پروژه‌های مرجع (Reference Projects)

کاربر این پروژه‌ها را به‌عنوان منبع الهام برای این تسک انتخاب کرده است. هدف از این بخش: الگوها، معماری، یا منطق این پروژه‌ها را در نظر بگیر و در پیاده‌سازی **پروژهٔ فعلی** اعمال کن — نه کپی کردن صرف.

**کار درخواست‌شده روی پروژهٔ فعلی:** 
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره

2- باید امکان لاگین از طریق جیمیل فراهم باشه

3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
5- از منظر ظاهری خیلی آشفته اس
6- در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/

### 🏠 شناسنامهٔ پروژهٔ فعلی (مرجع اصلی برای پیاده‌سازی)

**هرگاه بین پروژهٔ فعلی و پروژه‌های مرجع تفاوت بود (stack، نام‌گذاری، dependency)، پروژهٔ فعلی برنده است. هرگز syntax یا dependency پروژه‌های مرجع را کورکورانه به پروژهٔ فعلی نیاور.**

- **Repo**: `mahdighandi1989/ALLIN1`
- **زبان غالب**: HTML

---

### پروژه‌های اسکن‌شده

- ✅ `mahdighandi1989/language` — 12 فایل اسکن‌شده (از 319 کل)
  - 🎯 **نقطهٔ تمرکز کاربر**: _امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد_
    (فایل‌های اسکن‌شده بالا با اولویت بر اساس همین تمرکز انتخاب شده‌اند — به بقیهٔ پروژه توجه نکن مگر برای زمینه.)

### ⚙️ سرویس‌های Backend (11 فایل)

**`backend/services/index.js`** (799 bytes)
```
LyoqCiAqIFNlcnZpY2VzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xlIHB1
YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIGRvbWFpbi9zZXJ2aWNlIGxheWVy
IHNvIGNhbGxlcnMgY2FuCiAqIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL3Nl
cnZpY2VzJ2AuIENvdmVycyBhbmFseXRpY3MgY29sbGVjdGlvbiwgZmlsZSBh
bmFseXNpcywKICogdGhlIEdlbWluaSBSRVNUICsgRmlsZSBBUEkgY2xpZW50
LCBhdWRpby92aWRlbyBmZm1wZWcgaGVscGVycywgUERGIHRleHQKICogZXh0
cmFjdGlvbiwgdGhlIExpdmUgQVBJIFdlYlNvY2tldCBwcm94eS9vYnNlcnZl
ciBhbmQgdGhlIFRlbGVncmFtCiAqIGludGVncmF0aW9uLiBOYW1lZCBleHBv
cnRzIGFyZSB0aGUgc3RhYmxlIGNvbnRyYWN0OyBwZXItZmlsZSBkZWZhdWx0
IGV4cG9ydHMKICogYXJlIG5vdCBmb3J3YXJkZWQuCiAqLwpleHBvcnQgKiBm
cm9tICcuL2FuYWx5c2lzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4v
YW5hbHl0aWNzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vYXVkaW9T
ZXJ2aWNlLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9nZW1pbmlTZXJ2aWNlLmpz
JzsKZXhwb3J0ICogZnJvbSAnLi9saXZlUHJveHlTZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi9saXZlV3NPYnNlcnZlci5qcyc7CmV4cG9ydCAqIGZy
b20gJy4vcGRmU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vcHJvbXB0
cy5qcyc7CmV4cG9ydCAqIGZyb20gJy4vdmlkZW9TZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi90ZWxlZ3JhbS9pbmRleC5qcyc7Cg==

```

**`backend/services/telegram/config.js`** (3725 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENlbnRyYWxpc2VkLCBlbnYtZHJpdmVuIGNvbmZp
Z3VyYXRpb24gZm9yIHRoZSB0d28td2F5IFRlbGVncmFtCiAqIGludGVncmF0
aW9uLiBSZWFkaW5nIHRoaXMgbW9kdWxlIG5ldmVyIHRocm93cyBhbmQgbmV2
ZXIgZXhpdHMgdGhlIHByb2Nlc3Mg4oCUCiAqIHRoZSBUZWxlZ3JhbSBib3Qg
aXMgYW4gKm9wdGlvbmFsKiBmZWF0dXJlLCBzbyB3aGVuIG5vIGJvdCB0b2tl
biBpcyBjb25maWd1cmVkCiAqIHRoZSByZXN0IG9mIHRoZSBzeXN0ZW0ga2Vl
cHMgd29ya2luZyBhbmQgdGhlIGJvdCBzaW1wbHkgc3RheXMgZG9ybWFudC4K
ICoKICogVXBzdHJlYW0gKGlucHV0cyk6IGVudmlyb25tZW50IHZhcmlhYmxl
cyAoVEVMRUdSQU1fQk9UX1RPS0VOLAogKiBURUxFR1JBTV9XRUJIT09LX1VS
TCwgVEVMRUdSQU1fQURNSU5fSURTLCBURUxFR1JBTV9BTExPV0VEX1VTRVJf
SURTLAogKiBURUxFR1JBTV9EQVRBX0RJUiwgVEVMRUdSQU1fTU9ERSwgTk9U
SUZZX1RFTEVHUkFNX0JPVF9UT0tFTi9DSEFUX0lEIGZvcgogKiBiYWNrd2Fy
ZC1jb21wYXRpYmxlIG5vdGlmaWNhdGlvbiBkZWxpdmVyeSkuCiAqIERvd25z
dHJlYW0gKG91dHB1dHMpOiBjb25zdW1lZCBieSBzZXJ2aWNlcy90ZWxlZ3Jh
bS8qIChjbGllbnQsIGJvdCwgc3RvcmUsCiAqIG5vdGlmaWNhdGlvbnMpIGFu
ZCB3aXJlZCBpbnRvIHNlcnZlci5qcyB2aWEgc2VydmljZXMvdGVsZWdyYW0v
aW5kZXguanMuCiAqLwppbXBvcnQgeyBmaWxlVVJMVG9QYXRoIH0gZnJvbSAn
dXJsJzsKaW1wb3J0IHsgZGlybmFtZSwgam9pbiB9IGZyb20gJ3BhdGgnOwoK
Y29uc3QgX19kaXJuYW1lID0gZGlybmFtZShmaWxlVVJMVG9QYXRoKGltcG9y
dC5tZXRhLnVybCkpOwoKLy8gUGFyc2UgYSBjb21tYS9zcGFjZSBzZXBhcmF0
ZWQgbGlzdCBvZiBudW1lcmljIFRlbGVncmFtIGlkcyBpbnRvIGEgU2V0IG9m
Ci8vIHN0cmluZ3MgKFRlbGVncmFtIGlkcyBhcmUgNjQtYml0IGFuZCBzYWZl
ciBjb21wYXJlZCBhcyBzdHJpbmdzKS4KZnVuY3Rpb24gcGFyc2VJZExpc3Qo
cmF3KSB7CiAgaWYgKCFyYXcpIHJldHVybiBuZXcgU2V0KCk7CiAgcmV0dXJu
IG5ldyBTZXQoCiAgICBTdHJpbmcocmF3KQog
...
```

**`backend/services/telegram/index.js`** (5893 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENvbXBvc2l0aW9uIHJvb3QgKyBFeHByZXNzIHdp
cmluZyBmb3IgdGhlIFRlbGVncmFtIGludGVncmF0aW9uLiBJdAogKiBhc3Nl
bWJsZXMgdGhlIGNsaWVudCwgc3RvcmUsIGxvZ2dlciwgbm90aWZpY2F0aW9u
IHNlcnZpY2UsIHByYWN0aWNlIG1hbmFnZXIsCiAqIGNvbW1hbmRzIGFuZCBi
b3QgZnJvbSBjb25maWcsIGV4cG9zZXMgdGhlIGFzc2VtYmxlZCBzZXJ2aWNl
IGFzIGEgc2luZ2xldG9uIHNvCiAqIHJlcXVlc3QgaGFuZGxlcnMgZWxzZXdo
ZXJlIGNhbiBlbWl0IG5vdGlmaWNhdGlvbnMsIGFuZCByZWdpc3RlcnMgdGhl
IEhUVFAKICogc3VyZmFjZTogdGhlIGluYm91bmQgd2ViaG9vayBhbmQgdGhl
IHdlYnNpdGUtc2lkZSBhY2NvdW50LWxpbmsgZW5kcG9pbnQuCiAqCiAqIFVw
c3RyZWFtIChpbnB1dHMpOiBlbnZpcm9ubWVudCB2aWEgc2VydmljZXMvdGVs
ZWdyYW0vY29uZmlnLmpzOyB0aGUgZXhpc3RpbmcKICogR2VtaW5pIGNvbmZp
ZyAoZm9yIHRoZSBwcmFjdGljZSBwcm92aWRlciArIHN0YXR1cykgYW5kIHRo
ZSBFeHByZXNzIGFwcCBmcm9tCiAqIHNlcnZlci5qcy4KICogRG93bnN0cmVh
bSAob3V0cHV0cyk6IHdoZW4gYSBib3QgdG9rZW4gaXMgY29uZmlndXJlZCwg
c3RhcnRzIHBvbGxpbmcgb3Igc2V0cyBhCiAqIHdlYmhvb2s7IHJlZ2lzdGVy
cyBQT1NUIC9hcGkvdGVsZWdyYW0vd2ViaG9vaywgUE9TVCAvYXBpL3RlbGVn
cmFtL2xpbmsgYW5kCiAqIEdFVCAvYXBpL3RlbGVncmFtL3N0YXR1cy4gV2hl
biBubyB0b2tlbiBpcyBjb25maWd1cmVkIGV2ZXJ5IGV4cG9ydCBkZWdyYWRl
cyB0bwogKiBhIHNhZmUgbm8tb3Agc28gdGhlIHNlcnZlciBib290cyBub3Jt
YWxseSAoZS5nLiBpbiBDSS90ZXN0cykuCiAqLwppbXBvcnQgeyBsb2FkVGVs
ZWdyYW1Db25maWcgfSBmcm9tICcuL2NvbmZpZy5qcyc7CmltcG9ydCB7IFRl
bGVncmFtQ2xpZW50IH0gZnJvbSAnLi9jbGllbnQuanMnOwppbXBvcnQgeyBU
ZWxlZ3JhbVN0b3JlIH0gZnJvbSAnLi9zdG9yZS5qcyc7CmltcG9ydCB7IFRl
bGVncmFtTG9nZ2VyIH0gZnJvbSAnLi9sb2dnZXIuanMnOwppbXBvcnQgeyBO
b3RpZmljYXRpb25TZXJ2aWNlLCBFdmVudEJ1
...
```

**`backend/services/prompts.js`** (649 bytes)
```
Ly8gQmFja3dhcmQtY29tcGF0aWJsZSByZS1leHBvcnQgc2hpbS4KLy8KLy8g
VGhlIGNhbm9uaWNhbCBwcm9tcHQgZGVmaW5pdGlvbnMgbm93IGxpdmUgaW4g
YmFja2VuZC9tb2RlbHMvcHJvbXB0cy5qcyBhcwovLyBwYXJ0IG9mIHRoZSBs
YXllcmVkLWFyY2hpdGVjdHVyZSByZXN0cnVjdHVyZSAoc3RhdGljIGRvbWFp
biBkYXRhIGJlbG9uZ3MgaW4KLy8gbW9kZWxzLykuIFNlcnZpY2UtbGF5ZXIg
Y29kZSBoaXN0b3JpY2FsbHkgaW1wb3J0ZWQgdGhlc2UgZnJvbQovLyBzZXJ2
aWNlcy9wcm9tcHRzLmpzLCBzbyB0aGlzIG1vZHVsZSByZS1leHBvcnRzIHRo
ZW0gdG8ga2VlcCB0aG9zZSBpbXBvcnRzCi8vIHdvcmtpbmcgd2l0aG91dCB0
b3VjaGluZyBldmVyeSBjYWxsIHNpdGUuCi8vCi8vIE5hbWVkIHN5bWJvbHMg
KExFQkFORVNFX0NPUlJFQ1RJT05fUFJPTVBULCBBTkFMWVNJU19TWVNURU1f
UFJPTVBULAovLyBkZWZhdWx0TGl2ZVByb21wdHMpIGFyZSBmb3J3YXJkZWQg
dmVyYmF0aW0gZnJvbSAuLi9tb2RlbHMvcHJvbXB0cy5qcy4KZXhwb3J0IHsK
ICBMRUJBTkVTRV9DT1JSRUNUSU9OX1BST01QVCwKICBBTkFMWVNJU19TWVNU
RU1fUFJPTVBULAogIGRlZmF1bHRMaXZlUHJvbXB0cywKfSBmcm9tICcuLi9t
b2RlbHMvcHJvbXB0cy5qcyc7Cg==

```

**`backend/services/pdfService.js`** (704 bytes)
```
Ly8gRXh0cmFjdCB0ZXh0IGZyb20gYSBQREYgYnVmZmVyIHVzaW5nIHBkZi1w
YXJzZSAoaW1wb3J0ZWQgZHluYW1pY2FsbHkgc28gYQovLyBtaXNzaW5nIG9w
dGlvbmFsIGRlcGVuZGVuY3kgc3VyZmFjZXMgYXMgYSBjbGVhciBtZXNzYWdl
IHJhdGhlciB0aGFuIGEgY3Jhc2gpLgpleHBvcnQgYXN5bmMgZnVuY3Rpb24g
ZXh0cmFjdFBkZlRleHQoYnVmZmVyKSB7CiAgdHJ5IHsKICAgIGNvbnN0IHBk
ZlBhcnNlID0gKGF3YWl0IGltcG9ydCgncGRmLXBhcnNlJykpLmRlZmF1bHQ7
CiAgICBjb25zdCBkYXRhID0gYXdhaXQgcGRmUGFyc2UoYnVmZmVyKTsKICAg
IHJldHVybiBkYXRhLnRleHQ7CiAgfSBjYXRjaCAoZXJyb3IpIHsKICAgIGNv
bnNvbGUuZXJyb3IoJ1BERiBleHRyYWN0aW9uIGVycm9yOicsIGVycm9yKTsK
ICAgIGlmIChlcnJvci5jb2RlID09PSAnRVJSX01PRFVMRV9OT1RfRk9VTkQn
KSB7CiAgICAgIHRocm93IG5ldyBFcnJvcign2YXYp9qY2YjZhCBwZGYtcGFy
c2Ug2YbYtdioINmG24zYs9iqLiDZhNi32YHYp9mLIG5wbSBpbnN0YWxsIHBk
Zi1wYXJzZSDYsdinINin2KzYsdinINqp2YbbjNivLicpOwogICAgfQogICAg
dGhyb3cgbmV3IEVycm9yKCfYrti32Kcg2K/YsSDYp9iz2KrYrtix2KfYrCDZ
hdiq2YYg2KfYsiBQREY6ICcgKyBlcnJvci5tZXNzYWdlKTsKICB9Cn0KCmV4
cG9ydCBkZWZhdWx0IGV4dHJhY3RQZGZUZXh0Owo=

```

**`backend/services/languageService.js`** (2045 bytes)
```
LyoqCiAqIExhbmd1YWdlLW1hbmFnZW1lbnQgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIE1vZGVscyB0aGUgc21h
bGwgY2F0YWxvZ3VlIG9mIHN1cHBvcnRlZCBsYW5ndWFnZXMgcGx1cyBzaW1w
bGUsIG9mZmxpbmUKICogaGV1cmlzdGljcyBmb3IgbGFuZ3VhZ2UgZGV0ZWN0
aW9uIChzY3JpcHQtYmFzZWQpIGFuZCBJU08gNjM5LTEgdmFsaWRhdGlvbi4K
ICogTm8gZGF0YWJhc2UsIG5vIGV4dGVybmFsIHRyYW5zbGF0aW9uL2RldGVj
dGlvbiBBUEkuCiAqLwoKY29uc3QgSVNPXzYzOV8xX1JFID0gL15bYS16XXsy
fSQvOwoKY29uc3QgREVGQVVMVF9MQU5HVUFHRVMgPSBbCiAgeyBjb2RlOiAn
YXInLCBuYW1lOiAnQXJhYmljJyB9LAogIHsgY29kZTogJ2VuJywgbmFtZTog
J0VuZ2xpc2gnIH0sCiAgeyBjb2RlOiAnZmEnLCBuYW1lOiAnUGVyc2lhbicg
fSwKXTsKCi8qKiBWYWxpZGF0ZSBhbiBJU08gNjM5LTEgY29kZTogZXhhY3Rs
eSB0d28gbG93ZXJjYXNlIGxldHRlcnMuICovCmV4cG9ydCBmdW5jdGlvbiBp
c1ZhbGlkSVNPQ29kZShjb2RlKSB7CiAgcmV0dXJuIHR5cGVvZiBjb2RlID09
PSAnc3RyaW5nJyAmJiBJU09fNjM5XzFfUkUudGVzdChjb2RlKTsKfQoKLyoq
IEZyZXNoIGNhdGFsb2d1ZSBzdG9yZSwgc2VlZGVkIHdpdGggdGhlIGRlZmF1
bHQgbGFuZ3VhZ2VzLiAqLwpleHBvcnQgZnVuY3Rpb24gbmV3X3N0b3JlKCkg
ewogIHJldHVybiBuZXcgTWFwKERFRkFVTFRfTEFOR1VBR0VTLm1hcCgobCkg
PT4gW2wuY29kZSwgeyAuLi5sIH1dKSk7Cn0KCi8qKiBBZGQgYSBsYW5ndWFn
ZS4gUmVqZWN0cyBpbnZhbGlkIGNvZGVzIGFuZCBkdXBsaWNhdGVzLiAqLwpl
eHBvcnQgZnVuY3Rpb24gYWRkX2xhbmd1YWdlKHN0b3JlLCB7IGNvZGUsIG5h
bWUgfSkgewogIGlmICghaXNWYWxpZElTT0NvZGUoY29kZSkpIHRocm93IG5l
dyBFcnJvcignaW52YWxpZCBJU08gNjM5LTEgY29kZScpOwogIGlmICghbmFt
ZSB8fCAhbmFtZS50cmltKCkpIHRocm93IG5ldyBFcnJvcignbmFtZSBpcyBy
ZXF1aXJlZCcpOwogIGlmIChzdG9yZS5oYXMoY29kZSkpIHRocm93IG5ldyBF
cnJvcignbGFuZ3VhZ2UgYWxyZWFkeSBleGlz
...
```

**`backend/services/statistics.js`** (2305 bytes)
```
LyoqCiAqIExlYXJuaW5nLXN0YXRpc3RpY3MgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIFB1cmUgZnVuY3Rpb25z
IG92ZXIgcGxhaW4gInJldmlldyByZWNvcmQiIGFycmF5cyBzbyB0aGUgdW5p
dCBzdWl0ZSBjYW4KICogYXNzZXJ0IHRoZSBtYXRocyAoYXZlcmFnZXMsIHBy
b2dyZXNzICUsIHdlYWstd29yZCBzZWxlY3Rpb24pIHdpdGggbW9jayBkYXRh
CiAqIGFuZCBubyBkYXRhYmFzZSBvciBuZXR3b3JrLgogKgogKiBBIHJldmll
dyByZWNvcmQgbG9va3MgbGlrZToKICogICB7IHdvcmRJZCwgc2NvcmUgKDAu
LjEwMCksIHJldmlld2VkQXQgKElTTyBzdHJpbmcgb3IgZXBvY2ggbXMpIH0K
ICovCgovKiogQXZlcmFnZSBvZiBhIG51bWVyaWMgYXJyYXksIDAgZm9yIGVt
cHR5IGlucHV0LiAqLwpmdW5jdGlvbiBfYXZnKG51bXMpIHsKICBpZiAobnVt
cy5sZW5ndGggPT09IDApIHJldHVybiAwOwogIHJldHVybiBudW1zLnJlZHVj
ZSgoYSwgYikgPT4gYSArIGIsIDApIC8gbnVtcy5sZW5ndGg7Cn0KCi8qKgog
KiBBZ2dyZWdhdGUgcGVyLXVzZXIgc3RhdHMgZnJvbSB0aGVpciByZXZpZXcg
cmVjb3Jkcy4KICogQHJldHVybnMge3t0b3RhbFJldmlld3M6bnVtYmVyLCBs
ZWFybmVkV29yZHM6bnVtYmVyLCBhdmVyYWdlU2NvcmU6bnVtYmVyfX0KICov
CmV4cG9ydCBmdW5jdGlvbiBnZXRfdXNlcl9zdGF0cyhyZWNvcmRzID0gW10p
IHsKICBpZiAoIUFycmF5LmlzQXJyYXkocmVjb3JkcykpIHRocm93IG5ldyBF
cnJvcigncmVjb3JkcyBtdXN0IGJlIGFuIGFycmF5Jyk7CiAgY29uc3QgdG90
YWxSZXZpZXdzID0gcmVjb3Jkcy5sZW5ndGg7CiAgLy8gQSB3b3JkIGlzICJs
ZWFybmVkIiBvbmNlIGFueSByZXZpZXcgc2NvcmVzIGl0ID49IDgwLgogIGNv
bnN0IGxlYXJuZWQgPSBuZXcgU2V0KAogICAgcmVjb3Jkcy5maWx0ZXIoKHIp
ID0+IHIuc2NvcmUgPj0gODApLm1hcCgocikgPT4gci53b3JkSWQpLAogICk7
CiAgcmV0dXJuIHsKICAgIHRvdGFsUmV2aWV3cywKICAgIGxlYXJuZWRXb3Jk
czogbGVhcm5lZC5zaXplLAogICAgYXZlcmFnZVNjb3JlOiBNYXRoLnJvdW5k
KF9hdmcocmVjb3Jkcy5tYXAoKHIpID0+IHIu
...
```

**`backend/services/audioService.js`** (2864 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENyZWRlbnRpYWwtZnJlZSBhdWRpbyBwcm9jZXNz
aW5nIGJ1aWx0IG9uIHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcKICogYmlu
YXJ5LiBQb3dlcnMgUE9TVCAvYXBpL2F1ZGlvL3Byb2Nlc3MuIFVubGlrZSB0
aGUgR2VtaW5pLWJhY2tlZCBUVFMvY2hhdAogKiByb3V0ZXMsIGF1ZGlvIHBy
b2JpbmcvdHJhbnNjb2RpbmcgaGVyZSBuZWVkcyBubyBleHRlcm5hbCBBUEkg
a2V5LCBzbyB0aGUKICogZW5kcG9pbnQgYWx3YXlzIHdvcmtzIGFzIGxvbmcg
YXMgdGhlIHJ1bnRpbWUgZGVwcyAoZmx1ZW50LWZmbXBlZyArCiAqIGZmbXBl
Zy1zdGF0aWMpIGRlY2xhcmVkIGluIGJhY2tlbmQvcGFja2FnZS5qc29uIGFy
ZSBpbnN0YWxsZWQuCiAqCiAqIFVwc3RyZWFtIChpbnB1dHMpOiBhbiBvcHRp
b25hbCB1cGxvYWRlZCBhdWRpbyBmaWxlIChwYXRoIG9uIGRpc2spIGFuZCB0
aGUKICogYGZsdWVudC1mZm1wZWdgIC8gYGZmbXBlZy1zdGF0aWNgIHBhY2th
Z2VzLgogKiBEb3duc3RyZWFtIChvdXRwdXRzKTogYSBwbGFpbiBgeyBzdGF0
dXMsIHJlc3VsdCB9YCBvYmplY3QgY29uc3VtZWQgYnkKICogY29udHJvbGxl
cnMvYXVkaW9Db250cm9sbGVyLmpzIGFuZCwgaW4gdHVybiwgdGhlIGZyb250
ZW5kIGF1ZGlvIHRvb2xpbmcuCiAqLwppbXBvcnQgZnMgZnJvbSAnZnMnOwpp
bXBvcnQgb3MgZnJvbSAnb3MnOwppbXBvcnQgeyBqb2luIH0gZnJvbSAncGF0
aCc7CmltcG9ydCBmZm1wZWcgZnJvbSAnZmx1ZW50LWZmbXBlZyc7CmltcG9y
dCBmZm1wZWdTdGF0aWMgZnJvbSAnZmZtcGVnLXN0YXRpYyc7CgovLyBQb2lu
dCBmbHVlbnQtZmZtcGVnIGF0IHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcg
YmluYXJ5IHNvIG5vIHN5c3RlbSBpbnN0YWxsCi8vIGlzIHJlcXVpcmVkICht
aXJyb3JzIHNlcnZpY2VzL3ZpZGVvU2VydmljZS5qcykuCmlmIChmZm1wZWdT
dGF0aWMpIHsKICBmZm1wZWcuc2V0RmZtcGVnUGF0aChmZm1wZWdTdGF0aWMp
Owp9CgovLyBBdWRpbyBjb250YWluZXIvY29kZWMgZmFtaWxpZXMgdGhlIHBp
cGVsaW5lIGFjY2VwdHMgZm9yIHByb2JpbmcvdHJhbnNjb2RpbmcuCmV4cG9y
dCBjb25zdCBTVVBQT1JURURfQVVESU9fRk9S
...
```

### 🔗 Route ها و Endpoint ها (1 فایل)

**`backend/controllers/index.js`** (718 bytes)
```
LyoqCiAqIENvbnRyb2xsZXJzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xl
IHB1YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIEhUVFAgaGFuZGxlciBsYXll
ciBzbyB0aGUgcmVzdCBvZiB0aGUgYXBwCiAqIChyb3V0ZXMsIHNlcnZlciBj
b21wb3NpdGlvbikgY2FuIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL2NvbnRy
b2xsZXJzJ2AgaW5zdGVhZAogKiBvZiByZWFjaGluZyBpbnRvIGluZGl2aWR1
YWwgaGFuZGxlciBmaWxlcy4gRWFjaCBjb250cm9sbGVyIG93bnMgdGhlCiAq
IHJlcXVlc3QvcmVzcG9uc2Ugc2hhcGUgZm9yIG9uZSBzbGljZSBvZiB0aGUg
QVBJOyB0aGlzIGluZGV4IHNpbXBseSByZS1leHBvcnRzCiAqIHRoZWlyIHB1
YmxpYyBoYW5kbGVycy4gRGVmYXVsdCBleHBvcnRzIGFyZSBpbnRlbnRpb25h
bGx5IG5vdCBmb3J3YXJkZWQg4oCUIHRoZQogKiBuYW1lZCBoYW5kbGVycyBh
cmUgdGhlIHN0YWJsZSBjb250cmFjdC4KICovCmV4cG9ydCAqIGZyb20gJy4v
YW5hbHlzaXNDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hbmFs
eXRpY3NDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hdWRpb0Nv
bnRyb2xsZXIuanMnOwpleHBvcnQgKiBmcm9tICcuL2ZhbGxiYWNrQ29udHJv
bGxlci5qcyc7CmV4cG9ydCAqIGZyb20gJy4vZ2VtaW5pQ29udHJvbGxlci5q
cyc7CmV4cG9ydCAqIGZyb20gJy4vdXBsb2FkQ29udHJvbGxlci5qcyc7Cg==

```

---

### 💡 دستورالعمل ادغام

- الگوهای بالا را **شناسایی** کن: ساختار فایل‌ها، نام‌گذاری، patternهای معماری، روش‌های handle errors، …
- اما **در پروژهٔ فعلی** پیاده‌سازی کن — با stack، نام‌گذاری، و سبک کد همان پروژه. نه stack پروژه‌های مرجع.
- اگر پروژه‌های مرجع stack متفاوت دارند (مثلاً Vue ولی پروژه فعلی React)، **منطق** را منتقل کن نه syntax را.

---

## Prompt

## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

📖 **خواندن کامل + اجرای مو-به-مو (بسیار مهم):**

این پرامپت — از این یادداشت تا انتها — یک سند واحد است که هر بخشش
حاوی الزام یا context منحصربه‌فرد است. خواندن سطحی یا skim کردن **ممنوع**
است.

- پرامپت را **سطر به سطر** بخوان، نه head/tail/فقط-بخش-اصلی.
- اگر بخشی به‌نظر طولانی یا تکراری آمد، **حتماً** بخوان — تفاوت‌های
  ریز ممکن است در آن جا اساسی باشند.
- هر جمله، URL، نام فایل، نام تابع، یا مقدار عددی که در پرامپت آمده،
  دقیقاً همان است که کاربر می‌خواهد — تغییرش نده، رندش نکن، خلاصه‌اش
  نکن.
- اگر پرامپت چندین درخواست/مرحله/زیرتسک دارد، **همه** را پیاده کن. حتی
  یکی را نه به‌عنوان "خارج از scope" حذف کن.

❌ ممنوعات صریح:
- خلاصه‌سازی متن کاربر در commit message یا response
- "این بخش اصلی نیست، رد می‌کنم"
- "کاربر احتمالاً منظورش این بود..." — منظورش همان است که نوشته
- "این URL/نام به نظر قدیمی است، آپدیتش کردم" — تغییر بدون درخواست ممنوع
- پیاده‌سازی فقط بخشی از پرامپت و تظاهر به کامل بودن
- "همه آیتم‌های لیست A را بررسی کردم، B و C مشابه بودند" — نه؛
  هرکدام را جداگانه

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

🔗 **وابستگی‌ها و همگام‌سازی (بسیار حیاتی — هرگز skip نکن):**

این بخش از همهٔ بخش‌های دیگرِ این یادداشت **مهم‌تر** است. اگر نقض شود،
نتیجهٔ کار ممکن است مشروع به‌نظر برسد ولی در عمل بخش‌های دیگر سیستم را عقب
بیندازد، broken reference تولید کند، یا منجر به data corruption شود.

پیش از و حین تغییر، تمام وابستگی‌ها را در **چهار جهت** به‌طور **کامل و
بدون هیچ خلاصه‌سازی** شناسایی و همگام کن:

**۱. وابستگی‌های upstream (این تسک به چه چیزهایی متکی است):**
- چه فایل‌ها، توابع، کلاس‌ها، API endpoint ها، schema های دیتابیس،
  env vars، یا config هایی که این تسک نیاز دارد؟
- آیا قرار است چیزی را ویرایش/حذف کنی که جای دیگر (signature، رفتار،
  return type، side effect) از آن انتظار خاصی می‌رود؟
- اگر dependency جدیدی اضافه می‌کنی، آیا با dependencyهای موجود تداخل
  دارد (نسخه، compat، lock file)؟

**۲. وابستگی‌های downstream (چه چیزهایی به این تسک متکی‌اند):**
- چه فایل‌ها، توابع، تست‌ها، migrations، docs، یا UI component هایی از
  کدی که داری ویرایش/اضافه/حذف می‌کنی **استفاده می‌کنند**؟
- با grep و reference search **همه‌ی** call sites، importها، subclassها،
  reference های مستقیم و غیرمستقیم را پیدا کن — نه فقط چند مورد اصلی.
- خصوصاً برای حذف یا rename: هیچ broken reference نباید باقی بماند.

**۳. وابستگی‌های cross-tier (بسیار مهم — هرگز فقط یک لایه را نبین):**

تسک شما ممکن است از backend، frontend، database، worker، یا هر tier
دیگری شروع شده باشد. ولی تغییرات تقریباً همیشه روی tier های دیگر هم
اثر می‌گذارند. **مستقل از اینکه تسک از کدام tier است**، این چک‌های دو
طرفه را همیشه انجام بده:

🔁 **اگر backend را تغییر دادی** (API، service، model، route):
  → frontend: کدام component/page/hook این endpoint یا data shape را
    مصرف می‌کند؟ type definition، state shape، error handling، loading
    state، form validation، URL routing همگی باید همگام شوند.
  → mobile/SDK/client library (اگر پروژه دارد): همان داستان frontend.
  → database: آیا migration لازم است؟ آیا rollback امن است؟
  → background workers: آیا event producer/consumer ها تحت تأثیرند؟
  → rate limit، auth، CORS، CSP: آیا رفتار جدید پشتیبانی می‌شود؟

🔁 **اگر frontend را تغییر دادی** (component، form، state، route):
  → backend: آیا endpoint جدید/تغییریافته لازم است؟ آیا data shape ای
    که ارسال می‌شود با schema سرور سازگار است؟
  → backend validation: آیا برای ورودی‌های جدید UI کافی است؟
  → permissions/RBAC: آیا feature جدید نیاز به role check جدید دارد؟
  → analytics/tracking: آیا event های جدید باید در backend log شوند؟
  → SEO/SSR: آیا تغییر route نیاز به sitemap/meta tags جدید دارد؟

🔁 **اگر database/migration را تغییر دادی**:
  → backend models (ORM، Pydantic، dataclasses) همگی به‌روزند؟
  → query های raw SQL یا ORM queries با schema جدید سازگارند؟
  → seed data، fixtures، factory functions تست‌ها به‌روزند؟
  → frontend: آیا data shape جدید در UI به‌درستی render می‌شود؟
  → rollback migration نوشته شده و امن است؟

🔁 **اگر API contract یا event schema را تغییر دادی** (REST، GraphQL،
   WebSocket، gRPC، Kafka، …):
  → OpenAPI/GraphQL schema/proto file آپدیت شد؟
  → همه‌ی consumer ها (client، subscriber، webhook، external API
    user) با version جدید سازگارند؟
  → backward compatibility حفظ شده یا migration path روشن است؟
  → versioning header/path اگر breaking change است؟

🔁 **اگر infrastructure یا config را تغییر دادی** (Dockerfile، CI، Render
   config، env، secrets):
  → README setup/installation section به‌روزه؟
  → `.env.example` با env vars جدید آپدیت شد؟
  → deploy script یا CI workflow هم تغییر کرد؟
  → docs/architecture یا diagram های infrastructure به‌روزند؟

⚠️ **هرگز فقط یک tier را تغییر نده و فرض کنی بقیه خودکار همگام می‌شوند.**
   حتی برای تغییرات به‌ظاهر «کوچک»، چک کن.

**۴. وابستگی‌های جانبی (artifacts که همیشه چک شوند):**

تغییرات کد همیشه روی این artifact ها اثر دارند. **همه را** بررسی و
به‌روز کن — مستندات اولویت **بالا** دارد چون فراموش‌شدنی‌ترین است.

  📝 **مستندات** (همیشه چک کن — حتی برای تغییر کوچک کد):
    - README.md (شرح، setup، نمونه‌های استفاده، badge ها)
    - CHANGELOG.md / RELEASE_NOTES.md
    - docs/ folder (architecture، API reference، user guides، runbooks)
    - inline docstrings/کامنت‌های توابع و کلاس‌های تغییریافته
    - OpenAPI/Swagger annotations، JSDoc/TSDoc
    - architecture diagrams (اگر component اضافه/حذف شد)
    - migration guides (اگر breaking change است)

  🌍 **مستندات کاربر**:
    - i18n files و translation keys
    - UI labels، tooltip ها، help text، error messages
    - in-app onboarding (اگر flow جدید است)

  🧪 **تست‌ها**:
    - unit tests (همه‌ی فایل‌های مرتبط — حتی اگر «بی‌ربط» به‌نظر می‌رسد)
    - integration tests
    - e2e tests (Playwright/Cypress/Selenium)
    - snapshot tests (اگر UI تغییر کرد)
    - contract tests (Pact یا مشابه)
    - performance benchmarks (اگر behavior performance-sensitive تغییر کرد)

  🧬 **type definitions و contracts**:
    - .d.ts files
    - Pydantic models، dataclasses
    - Protobuf/Avro/Thrift schemas
    - GraphQL schema definitions
    - JSON Schemas

  🏗 **infrastructure و config**:
    - Dockerfile، docker-compose.yml
    - Kubernetes manifests
    - Render/Vercel/Netlify config
    - GitHub Actions / GitLab CI workflows
    - environment templates (.env.example، .env.sample)
    - feature flags (LaunchDarkly، GrowthBook، config)

  📊 **monitoring و observability**:
    - logging keys (اگر اضافه/حذف شد، log parser ها هم به‌روز شوند)
    - metric names (Prometheus، Datadog)
    - tracing spans
    - alert rules و dashboards
    - error tracking (Sentry rules، groupings)

  🔐 **security**:
    - auth rules (rate limit، CORS، CSP، HSTS)
    - permissions/RBAC config
    - secrets rotation policies
    - audit log events (اگر action جدید اضافه شد)

  💾 **caches و serialization**:
    - cache keys و TTL (اگر data shape یا lifecycle تغییر کرد)
    - serializer formats (Redis، session storage)
    - browser storage (localStorage، IndexedDB schemas)

**قانون مطلق همگام‌سازی:**
- هر چیزی که در (۱)، (۲)، (۳)، یا (۴) شناسایی شد، در **همان workflow
  این تسک** همگام و به‌روز شود. هرگز برای بعد رها نکن.
- اگر یک فایل/تست/docs نسبت به تغییر شما عقب بماند، در بهترین حالت bug،
  در بدترین حالت مشکل امنیتی یا data corruption تولید می‌کند.
- تغییرات همگام‌سازی می‌توانند در commit جداگانه باشند (در همان task)،
  ولی نباید skip شوند یا به «refactor آینده» سپرده شوند.

**هرگز این جمله‌ها قابل قبول نیست:**
- ❌ «بعداً پیداش می‌کنم»
- ❌ «احتمالاً جای دیگه‌ای استفاده نمی‌شه»
- ❌ «این یه refactor جداگانه‌ست — out of scope»
- ❌ «فقط فایل‌های اصلی رو بررسی کردم»
- ❌ «حدس می‌زنم چیزی بهش وابسته نیست»
- ❌ «دامنه‌ی وابستگی‌ها رو خلاصه کردم» — هرگز خلاصه نکن
- ❌ «این task فقط backend است؛ frontend مشکل خودش» — هرگز
- ❌ «این task فقط frontend است؛ backend از قبل کار می‌کند» — هرگز ثابت نکرده
- ❌ «مستندات بعداً به‌روز می‌شن» — همیشه same-task همگام شوند
- ❌ «testها رو نگاه نکردم چون فقط یه تغییر کوچیک بود»

**در commit message یا PR description**، دامنهٔ وابستگی‌های شناسایی‌شده و
همگام‌شده را به‌طور explicit و **per-tier** بنویس. مثال:
```
Dependencies synced:
- upstream: User model schema, auth middleware
- downstream: 3 API endpoints, 5 frontend components, 12 tests
- cross-tier (backend → frontend): UserProfile.tsx, useUser.ts hook,
  api-types.ts (TS definitions)
- cross-tier (backend → infra): .env.example added NEW_AUTH_SCOPES
- side artifacts: OpenAPI spec, README API section, i18n keys for
  new errors, Sentry alert rule for new error code
```
اگر هیچ وابستگی پیدا نکردی در هر کدام از چهار جهت، صریحاً بنویس:
«بررسی شد — هیچ وابستگی upstream / downstream / cross-tier (backend↔
frontend↔db↔infra) / side شناسایی نشد» تا مشخص باشد بررسی **انجام شده**
نه اینکه فراموش شده.

📋 **مدیریت TO-DO برای اقدامات دستی کاربر (همیشه چک کن):**

⚠️ **هشدار بحرانی — قاعدهٔ ضد-فرار:** TO-DO فقط برای کارهایی است که
**واقعاً غیرممکن** برای agent است (نیاز به انسان مطلق)، نه برای کارهایی
که «بزرگ‌اند»، «وقت می‌برند»، یا «نیازمند fixture/setup» هستند. اگر یک
agent در یک سشن بیش از **۲۰٪ از تسک‌ها** را با TO-DO ببندد، یعنی از کار
فرار می‌کند — این الگو در سشن‌های قبلی **مشاهده** شده و الان ممنوع است.

✅ **فقط برای این موارد TO-DO بساز** (لیست بسته — هرچه خارج این لیست
ممنوع است):

  ۱. **Credential/secret که فقط کاربر دارد**:
     - تنظیم API key واقعی در پنل ادمین خارجی (Render، AWS، Stripe، …)
     - تأیید OAuth client روی console آن سرویس
     - paste کردن webhook secret که فقط بعد از ساخت در dashboard ظاهر می‌شود

  ۲. **Account/billing روی سرویس خارجی که کاربر باید عضو شود**:
     - ساخت account جدید روی Stripe/SendGrid/Twilio/Google Cloud
     - تأیید verification شماره یا ID
     - فعال‌سازی subscription پولی

  ۳. **داده/asset خصوصی که فقط کاربر دارد**:
     - آپلود لوگو/تصویر/فونت برند
     - paste کردن داده‌ای که در محل کار کاربر است
     - import داده‌ای که فقط روی device کاربر است

  ۴. **تصمیم سلیقه‌ای/حقوقی/کسب‌وکار**:
     - انتخاب رنگ‌بندی نهایی یا تم
     - متن دقیق Terms of Service / Privacy Policy
     - تعرفهٔ قیمت‌گذاری
     - نام نهایی برند یا دامنه

⛔ **هرگز TO-DO نکن برای** (لیست سیاه — هر چیزی که در این لیست است
**قابل اجرا** توسط agent است، حتی اگر بزرگ یا چندبخشی باشد):

  ❌ UI component / page / dashboard (هر فریم‌ورک: React, Vue, Angular,
     Svelte، حتی اگر معماری بزرگ دارد) — می‌توانی stub اولیه + state
     management + layout + استایل بسازی
  ❌ "نیازمند Google Drive / Stripe / Twilio API" — می‌توانی **client
     stub** با abstraction layer بسازی که با env var واقعی plug-in شود؛
     کد integration یعنی پیاده‌سازی، نه TO-DO
  ❌ "feature بزرگ، چند روز کار می‌برد" — اندازه دلیل defer نیست؛ کوچک
     شروع کن، iterate کن، در همین سشن کامل کن
  ❌ Celery / background worker / scheduler — یک task ساده + register
     می‌توانی بسازی
  ❌ Migration / model / schema — حتی اگر فیلد جدید نیاز دارد، اضافه کن
  ❌ REST endpoint / GraphQL resolver / WebSocket route — هرگز TO-DO
  ❌ test (unit/integration/e2e) — همیشه قابل نوشتن
  ❌ Documentation / README / API docs — همیشه قابل نوشتن
  ❌ Config file / .env.example / Dockerfile / CI workflow — همیشه قابل
     نوشتن
  ❌ "می‌توانستی .tsx ولی repo .jsx است" — از .jsx استفاده کن، TO-DO نکن
  ❌ "نیازمند فیلد X در مدل دیگر" — اضافه کن فیلد را، TO-DO نکن
  ❌ "تصمیم admin-vs-user-scoped" — پرامپت اولیه scope را معلوم کرده،
     یا با محتاطانه‌ترین تفسیر پیش برو
  ❌ "credential در production هنوز ست نیست" — این TO-DO ساده برای
     تنظیم env var است (مورد ۱ بالا)، نه دلیل برای defer کردن کد
  ❌ "نیازمند verification از کاربر" — اگر اقدام واقعی غیرممکن نیست،
     پیش برو
  ❌ هر چیزی که در یک کامنت `# TODO` معمولی نوشته می‌شد — این فایل
     TO-DO نیست، کامنت inline است

🔬 **قاعدهٔ «حداقل تلاش» قبل از TO-DO**: قبل از TO-DO کردن یک AC، **اثبات
کن** که قابل انجام نیست:

  ۱. آیا می‌توانم یک stub/placeholder بسازم که با env واقعی plug-in شود؟
     → اگر بله، بساز و TO-DO نکن
  ۲. آیا می‌توانم برای این بخش یک test (حتی mock-based) بنویسم؟
     → اگر بله، بنویس و TO-DO نکن
  ۳. آیا می‌توانم abstraction/interface را تعریف کنم، حتی اگر backend
     واقعی نیست؟ → اگر بله، تعریف کن و TO-DO نکن
  ۴. آیا فقط یک حالت سلیقه‌ای/decision کاربر در میان است؟
     → فقط آن یک decision را TO-DO کن، نه کل feature را

اگر یکی از این چهار راه‌حل ممکن بود ولی به TO-DO رفتی، **اعتبار شما از
بین می‌رود**.

📊 **آستانهٔ TO-DO per session**: در یک حلقهٔ اجرای N تسک، اگر بیشتر از
**۲۰٪** تسک‌ها فایل TO-DO ساختی، خودت در گزارش پایانی صریحاً اعلام کن:

  "⚠️ نسبت TO-DO من {K}/{N} = {%} است که از آستانهٔ ۲۰٪ بالاتر است.
   احتمالاً برخی از این TO-DO ها قابل اجرا بودند ولی من فرار کردم.
   لیست TO-DO ها را کاربر باید بازبینی کند که آیا واقعاً Manual-required
   بودند یا agent ضعیف کار کرده."

**یادآوری همیشگی:** اگر در آینده قابلیت‌های شما گسترش پیدا کرد و توانستید
یکی از موارد لیست سفید را خودکار انجام دهید (مثلاً managed credential
injection، یا integration پولی automate شود)، انجام دهید و TO-DO نسازید.
لیست سفید بسته است ولی **بسته از پایین** (می‌تواند کوچک‌تر شود اگر
قابلیت‌ها رشد کنند، ولی هرگز بزرگ‌تر نشود برای فرار).

**اگر هیچ بخش Manual-required نبود (تمام تسک Auto-capable است)**:
  → فایل TO-DO **نساز**. فولدر TO-DO/ باید پاک و معنادار بماند.
  → اگر برای این task از قبل `TO-DO/todo-task-{task_id_first_8}.md` بود
     (یعنی در run قبلی نیاز به دخالت کاربر بود ولی الان نه): فایل قدیمی
     را پاک کن و entry را از `TO-DO/_index.json` حذف کن.

**اگر بخش Manual-required دارد** (همه‌جانبه یا hybrid):
  1. فولدر TO-DO/ را در ریشه ریپو ایجاد کن اگر نیست
  2. فایل `TO-DO/todo-task-{task_id_first_8}.md` بساز با front-matter
     شامل: task_id, task_title, execution_priority, created_at,
     updated_at, status: "pending"
     و در بدنه: «چرا این فایل ساخته شد»، «وضعیت بخش‌های خودکار»
     (commit ها reference)، «کارهایی که باید انجام دهی» با اولویت
     بالا/متوسط/پایین به ترتیب، «وقتی این کارها را تمام کردی»
  3. `TO-DO/_index.json` را با **merge** آپدیت کن (نه overwrite):
     - فایل موجود را بخوان
     - entry های orphan (فایلشان پاک شده) را حذف کن
     - entry این task را اضافه/replace کن
     - بر اساس execution_priority صعودی مرتب کن
     - ساختار: `{"version":1, "generated_at": ISO, "total": N, "items": [...]}`
  4. این تغییرات TO-DO را در **همان commit کد** شامل کن (نه commit جداگانه)

⛔ **ممنوعات مطلق TO-DO**:
  ❌ ساختن TO-DO برای کاری که می‌توانستی خودت انجام دهی (شلوغی فولدر)
  ❌ overwrite کردن `TO-DO/_index.json` بدون merge (data loss)
  ❌ نگه‌داشتن entry هایی که فایل‌شان پاک شده (broken reference)
  ❌ فراموش کردن نوشتن «خروجی مورد انتظار» در هر آیتم TO-DO

این بخش الزامی است. حتی اگر فکر می‌کنی "این تسک کاملاً auto است و نیازی
به TO-DO نیست"، صریحاً در commit message یا report بنویس:
"بررسی شد — این تسک هیچ بخش Manual-required ندارد، TO-DO ساخته نشد."

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

🔁 **Commit + Push فوری per-task (بسیار مهم برای جریان کار صحیح):**

پس از اتمام پیاده‌سازی این تسک، **بلافاصله** commit کن و **همان موقع**
به default branch (main/master) push کن. سپس به تسک بعدی برو.

✓ چرا این قانون حیاتی است:
  - تسک‌های بعدی ممکن است به فایل‌ها/تغییراتی که این تسک ایجاد کرده
    نیاز داشته باشند. اگر push نکنی، `git pull` بعدی آن‌ها را نمی‌بیند.
  - جمع‌کردن تغییرات چند تسک منجر به conflict های بزرگ می‌شود.
  - اگر در میانه fail کنی، task های push شده ضایع نمی‌شوند.

⛔ ممنوع: "همه task ها را تمام می‌کنم بعد یک‌جا push می‌زنم"
⛔ ممنوع: branch جدا برای task — مستقیم به default branch
⛔ ممنوع: task بعدی بدون push کامل task قبلی

---


## 📥 درخواست خام کاربر (verbatim — همان متنی که کاربر نوشت)
_(همهٔ URL ها، آدرس‌ها، نام‌ها، و کلمات کلیدی در این متن دست‌نخورده هستند. بخش‌های بعدی توسط AI ساختار داده شده‌اند و ممکن است ناقص باشند — این متن مرجع اصلی است.)_

```
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره

2- باید امکان لاگین از طریق جیمیل فراهم باشه

3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
5- از منظر ظاهری خیلی آشفته اس
6- در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()


---
## 📚 پروژه‌های مرجع (الهام از پیاده‌سازی‌های موجود)
_در زیر خلاصهٔ ساختار/فایل‌های پروژه‌های زیر آمده است. از این منابع به‌عنوان الگو/الهام استفاده کن و در پرامپت نهایی به فایل‌ها/الگوهای مرتبط ارجاع بده._

## 📚 پروژه‌های مرجع (Reference Projects)

کاربر این پروژه‌ها را به‌عنوان منبع الهام برای این تسک انتخاب کرده است. هدف از این بخش: الگوها، معماری، یا منطق این پروژه‌ها را در نظر بگیر و در پیاده‌سازی **پروژهٔ فعلی** اعمال کن — نه کپی کردن صرف.

**کار درخواست‌شده روی پروژهٔ فعلی:** 
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره

2- باید امکان لاگین از طریق جیمیل فراهم باشه

3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
5- از منظر ظاهری خیلی آشفته اس
6- در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/

### 🏠 شناسنامهٔ پروژهٔ فعلی (مرجع اصلی برای پیاده‌سازی)

**هرگاه بین پروژهٔ فعلی و پروژه‌های مرجع تفاوت بود (stack، نام‌گذاری، dependency)، پروژهٔ فعلی برنده است. هرگز syntax یا dependency پروژه‌های مرجع را کورکورانه به پروژهٔ فعلی نیاور.**

- **Repo**: `mahdighandi1989/ALLIN1`
- **زبان غالب**: HTML

---

### پروژه‌های اسکن‌شده

- ✅ `mahdighandi1989/language` — 12 فایل اسکن‌شده (از 319 کل)
  - 🎯 **نقطهٔ تمرکز کاربر**: _امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد_
    (فایل‌های اسکن‌شده بالا با اولویت بر اساس همین تمرکز انتخاب شده‌اند — به بقیهٔ پروژه توجه نکن مگر برای زمینه.)

### ⚙️ سرویس‌های Backend (11 فایل)

**`backend/services/index.js`** (799 bytes)
```
LyoqCiAqIFNlcnZpY2VzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xlIHB1
YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIGRvbWFpbi9zZXJ2aWNlIGxheWVy
IHNvIGNhbGxlcnMgY2FuCiAqIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL3Nl
cnZpY2VzJ2AuIENvdmVycyBhbmFseXRpY3MgY29sbGVjdGlvbiwgZmlsZSBh
bmFseXNpcywKICogdGhlIEdlbWluaSBSRVNUICsgRmlsZSBBUEkgY2xpZW50
LCBhdWRpby92aWRlbyBmZm1wZWcgaGVscGVycywgUERGIHRleHQKICogZXh0
cmFjdGlvbiwgdGhlIExpdmUgQVBJIFdlYlNvY2tldCBwcm94eS9vYnNlcnZl
ciBhbmQgdGhlIFRlbGVncmFtCiAqIGludGVncmF0aW9uLiBOYW1lZCBleHBv
cnRzIGFyZSB0aGUgc3RhYmxlIGNvbnRyYWN0OyBwZXItZmlsZSBkZWZhdWx0
IGV4cG9ydHMKICogYXJlIG5vdCBmb3J3YXJkZWQuCiAqLwpleHBvcnQgKiBm
cm9tICcuL2FuYWx5c2lzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4v
YW5hbHl0aWNzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vYXVkaW9T
ZXJ2aWNlLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9nZW1pbmlTZXJ2aWNlLmpz
JzsKZXhwb3J0ICogZnJvbSAnLi9saXZlUHJveHlTZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi9saXZlV3NPYnNlcnZlci5qcyc7CmV4cG9ydCAqIGZy
b20gJy4vcGRmU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vcHJvbXB0
cy5qcyc7CmV4cG9ydCAqIGZyb20gJy4vdmlkZW9TZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi90ZWxlZ3JhbS9pbmRleC5qcyc7Cg==

```

**`backend/services/telegram/config.js`** (3725 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENlbnRyYWxpc2VkLCBlbnYtZHJpdmVuIGNvbmZp
Z3VyYXRpb24gZm9yIHRoZSB0d28td2F5IFRlbGVncmFtCiAqIGludGVncmF0
aW9uLiBSZWFkaW5nIHRoaXMgbW9kdWxlIG5ldmVyIHRocm93cyBhbmQgbmV2
ZXIgZXhpdHMgdGhlIHByb2Nlc3Mg4oCUCiAqIHRoZSBUZWxlZ3JhbSBib3Qg
aXMgYW4gKm9wdGlvbmFsKiBmZWF0dXJlLCBzbyB3aGVuIG5vIGJvdCB0b2tl
biBpcyBjb25maWd1cmVkCiAqIHRoZSByZXN0IG9mIHRoZSBzeXN0ZW0ga2Vl
cHMgd29ya2luZyBhbmQgdGhlIGJvdCBzaW1wbHkgc3RheXMgZG9ybWFudC4K
ICoKICogVXBzdHJlYW0gKGlucHV0cyk6IGVudmlyb25tZW50IHZhcmlhYmxl
cyAoVEVMRUdSQU1fQk9UX1RPS0VOLAogKiBURUxFR1JBTV9XRUJIT09LX1VS
TCwgVEVMRUdSQU1fQURNSU5fSURTLCBURUxFR1JBTV9BTExPV0VEX1VTRVJf
SURTLAogKiBURUxFR1JBTV9EQVRBX0RJUiwgVEVMRUdSQU1fTU9ERSwgTk9U
SUZZX1RFTEVHUkFNX0JPVF9UT0tFTi9DSEFUX0lEIGZvcgogKiBiYWNrd2Fy
ZC1jb21wYXRpYmxlIG5vdGlmaWNhdGlvbiBkZWxpdmVyeSkuCiAqIERvd25z
dHJlYW0gKG91dHB1dHMpOiBjb25zdW1lZCBieSBzZXJ2aWNlcy90ZWxlZ3Jh
bS8qIChjbGllbnQsIGJvdCwgc3RvcmUsCiAqIG5vdGlmaWNhdGlvbnMpIGFu
ZCB3aXJlZCBpbnRvIHNlcnZlci5qcyB2aWEgc2VydmljZXMvdGVsZWdyYW0v
aW5kZXguanMuCiAqLwppbXBvcnQgeyBmaWxlVVJMVG9QYXRoIH0gZnJvbSAn
dXJsJzsKaW1wb3J0IHsgZGlybmFtZSwgam9pbiB9IGZyb20gJ3BhdGgnOwoK
Y29uc3QgX19kaXJuYW1lID0gZGlybmFtZShmaWxlVVJMVG9QYXRoKGltcG9y
dC5tZXRhLnVybCkpOwoKLy8gUGFyc2UgYSBjb21tYS9zcGFjZSBzZXBhcmF0
ZWQgbGlzdCBvZiBudW1lcmljIFRlbGVncmFtIGlkcyBpbnRvIGEgU2V0IG9m
Ci8vIHN0cmluZ3MgKFRlbGVncmFtIGlkcyBhcmUgNjQtYml0IGFuZCBzYWZl
ciBjb21wYXJlZCBhcyBzdHJpbmdzKS4KZnVuY3Rpb24gcGFyc2VJZExpc3Qo
cmF3KSB7CiAgaWYgKCFyYXcpIHJldHVybiBuZXcgU2V0KCk7CiAgcmV0dXJu
IG5ldyBTZXQoCiAgICBTdHJpbmcocmF3KQog
...
```

**`backend/services/telegram/index.js`** (5893 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENvbXBvc2l0aW9uIHJvb3QgKyBFeHByZXNzIHdp
cmluZyBmb3IgdGhlIFRlbGVncmFtIGludGVncmF0aW9uLiBJdAogKiBhc3Nl
bWJsZXMgdGhlIGNsaWVudCwgc3RvcmUsIGxvZ2dlciwgbm90aWZpY2F0aW9u
IHNlcnZpY2UsIHByYWN0aWNlIG1hbmFnZXIsCiAqIGNvbW1hbmRzIGFuZCBi
b3QgZnJvbSBjb25maWcsIGV4cG9zZXMgdGhlIGFzc2VtYmxlZCBzZXJ2aWNl
IGFzIGEgc2luZ2xldG9uIHNvCiAqIHJlcXVlc3QgaGFuZGxlcnMgZWxzZXdo
ZXJlIGNhbiBlbWl0IG5vdGlmaWNhdGlvbnMsIGFuZCByZWdpc3RlcnMgdGhl
IEhUVFAKICogc3VyZmFjZTogdGhlIGluYm91bmQgd2ViaG9vayBhbmQgdGhl
IHdlYnNpdGUtc2lkZSBhY2NvdW50LWxpbmsgZW5kcG9pbnQuCiAqCiAqIFVw
c3RyZWFtIChpbnB1dHMpOiBlbnZpcm9ubWVudCB2aWEgc2VydmljZXMvdGVs
ZWdyYW0vY29uZmlnLmpzOyB0aGUgZXhpc3RpbmcKICogR2VtaW5pIGNvbmZp
ZyAoZm9yIHRoZSBwcmFjdGljZSBwcm92aWRlciArIHN0YXR1cykgYW5kIHRo
ZSBFeHByZXNzIGFwcCBmcm9tCiAqIHNlcnZlci5qcy4KICogRG93bnN0cmVh
bSAob3V0cHV0cyk6IHdoZW4gYSBib3QgdG9rZW4gaXMgY29uZmlndXJlZCwg
c3RhcnRzIHBvbGxpbmcgb3Igc2V0cyBhCiAqIHdlYmhvb2s7IHJlZ2lzdGVy
cyBQT1NUIC9hcGkvdGVsZWdyYW0vd2ViaG9vaywgUE9TVCAvYXBpL3RlbGVn
cmFtL2xpbmsgYW5kCiAqIEdFVCAvYXBpL3RlbGVncmFtL3N0YXR1cy4gV2hl
biBubyB0b2tlbiBpcyBjb25maWd1cmVkIGV2ZXJ5IGV4cG9ydCBkZWdyYWRl
cyB0bwogKiBhIHNhZmUgbm8tb3Agc28gdGhlIHNlcnZlciBib290cyBub3Jt
YWxseSAoZS5nLiBpbiBDSS90ZXN0cykuCiAqLwppbXBvcnQgeyBsb2FkVGVs
ZWdyYW1Db25maWcgfSBmcm9tICcuL2NvbmZpZy5qcyc7CmltcG9ydCB7IFRl
bGVncmFtQ2xpZW50IH0gZnJvbSAnLi9jbGllbnQuanMnOwppbXBvcnQgeyBU
ZWxlZ3JhbVN0b3JlIH0gZnJvbSAnLi9zdG9yZS5qcyc7CmltcG9ydCB7IFRl
bGVncmFtTG9nZ2VyIH0gZnJvbSAnLi9sb2dnZXIuanMnOwppbXBvcnQgeyBO
b3RpZmljYXRpb25TZXJ2aWNlLCBFdmVudEJ1
...
```

**`backend/services/prompts.js`** (649 bytes)
```
Ly8gQmFja3dhcmQtY29tcGF0aWJsZSByZS1leHBvcnQgc2hpbS4KLy8KLy8g
VGhlIGNhbm9uaWNhbCBwcm9tcHQgZGVmaW5pdGlvbnMgbm93IGxpdmUgaW4g
YmFja2VuZC9tb2RlbHMvcHJvbXB0cy5qcyBhcwovLyBwYXJ0IG9mIHRoZSBs
YXllcmVkLWFyY2hpdGVjdHVyZSByZXN0cnVjdHVyZSAoc3RhdGljIGRvbWFp
biBkYXRhIGJlbG9uZ3MgaW4KLy8gbW9kZWxzLykuIFNlcnZpY2UtbGF5ZXIg
Y29kZSBoaXN0b3JpY2FsbHkgaW1wb3J0ZWQgdGhlc2UgZnJvbQovLyBzZXJ2
aWNlcy9wcm9tcHRzLmpzLCBzbyB0aGlzIG1vZHVsZSByZS1leHBvcnRzIHRo
ZW0gdG8ga2VlcCB0aG9zZSBpbXBvcnRzCi8vIHdvcmtpbmcgd2l0aG91dCB0
b3VjaGluZyBldmVyeSBjYWxsIHNpdGUuCi8vCi8vIE5hbWVkIHN5bWJvbHMg
KExFQkFORVNFX0NPUlJFQ1RJT05fUFJPTVBULCBBTkFMWVNJU19TWVNURU1f
UFJPTVBULAovLyBkZWZhdWx0TGl2ZVByb21wdHMpIGFyZSBmb3J3YXJkZWQg
dmVyYmF0aW0gZnJvbSAuLi9tb2RlbHMvcHJvbXB0cy5qcy4KZXhwb3J0IHsK
ICBMRUJBTkVTRV9DT1JSRUNUSU9OX1BST01QVCwKICBBTkFMWVNJU19TWVNU
RU1fUFJPTVBULAogIGRlZmF1bHRMaXZlUHJvbXB0cywKfSBmcm9tICcuLi9t
b2RlbHMvcHJvbXB0cy5qcyc7Cg==

```

**`backend/services/pdfService.js`** (704 bytes)
```
Ly8gRXh0cmFjdCB0ZXh0IGZyb20gYSBQREYgYnVmZmVyIHVzaW5nIHBkZi1w
YXJzZSAoaW1wb3J0ZWQgZHluYW1pY2FsbHkgc28gYQovLyBtaXNzaW5nIG9w
dGlvbmFsIGRlcGVuZGVuY3kgc3VyZmFjZXMgYXMgYSBjbGVhciBtZXNzYWdl
IHJhdGhlciB0aGFuIGEgY3Jhc2gpLgpleHBvcnQgYXN5bmMgZnVuY3Rpb24g
ZXh0cmFjdFBkZlRleHQoYnVmZmVyKSB7CiAgdHJ5IHsKICAgIGNvbnN0IHBk
ZlBhcnNlID0gKGF3YWl0IGltcG9ydCgncGRmLXBhcnNlJykpLmRlZmF1bHQ7
CiAgICBjb25zdCBkYXRhID0gYXdhaXQgcGRmUGFyc2UoYnVmZmVyKTsKICAg
IHJldHVybiBkYXRhLnRleHQ7CiAgfSBjYXRjaCAoZXJyb3IpIHsKICAgIGNv
bnNvbGUuZXJyb3IoJ1BERiBleHRyYWN0aW9uIGVycm9yOicsIGVycm9yKTsK
ICAgIGlmIChlcnJvci5jb2RlID09PSAnRVJSX01PRFVMRV9OT1RfRk9VTkQn
KSB7CiAgICAgIHRocm93IG5ldyBFcnJvcign2YXYp9qY2YjZhCBwZGYtcGFy
c2Ug2YbYtdioINmG24zYs9iqLiDZhNi32YHYp9mLIG5wbSBpbnN0YWxsIHBk
Zi1wYXJzZSDYsdinINin2KzYsdinINqp2YbbjNivLicpOwogICAgfQogICAg
dGhyb3cgbmV3IEVycm9yKCfYrti32Kcg2K/YsSDYp9iz2KrYrtix2KfYrCDZ
hdiq2YYg2KfYsiBQREY6ICcgKyBlcnJvci5tZXNzYWdlKTsKICB9Cn0KCmV4
cG9ydCBkZWZhdWx0IGV4dHJhY3RQZGZUZXh0Owo=

```

**`backend/services/languageService.js`** (2045 bytes)
```
LyoqCiAqIExhbmd1YWdlLW1hbmFnZW1lbnQgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIE1vZGVscyB0aGUgc21h
bGwgY2F0YWxvZ3VlIG9mIHN1cHBvcnRlZCBsYW5ndWFnZXMgcGx1cyBzaW1w
bGUsIG9mZmxpbmUKICogaGV1cmlzdGljcyBmb3IgbGFuZ3VhZ2UgZGV0ZWN0
aW9uIChzY3JpcHQtYmFzZWQpIGFuZCBJU08gNjM5LTEgdmFsaWRhdGlvbi4K
ICogTm8gZGF0YWJhc2UsIG5vIGV4dGVybmFsIHRyYW5zbGF0aW9uL2RldGVj
dGlvbiBBUEkuCiAqLwoKY29uc3QgSVNPXzYzOV8xX1JFID0gL15bYS16XXsy
fSQvOwoKY29uc3QgREVGQVVMVF9MQU5HVUFHRVMgPSBbCiAgeyBjb2RlOiAn
YXInLCBuYW1lOiAnQXJhYmljJyB9LAogIHsgY29kZTogJ2VuJywgbmFtZTog
J0VuZ2xpc2gnIH0sCiAgeyBjb2RlOiAnZmEnLCBuYW1lOiAnUGVyc2lhbicg
fSwKXTsKCi8qKiBWYWxpZGF0ZSBhbiBJU08gNjM5LTEgY29kZTogZXhhY3Rs
eSB0d28gbG93ZXJjYXNlIGxldHRlcnMuICovCmV4cG9ydCBmdW5jdGlvbiBp
c1ZhbGlkSVNPQ29kZShjb2RlKSB7CiAgcmV0dXJuIHR5cGVvZiBjb2RlID09
PSAnc3RyaW5nJyAmJiBJU09fNjM5XzFfUkUudGVzdChjb2RlKTsKfQoKLyoq
IEZyZXNoIGNhdGFsb2d1ZSBzdG9yZSwgc2VlZGVkIHdpdGggdGhlIGRlZmF1
bHQgbGFuZ3VhZ2VzLiAqLwpleHBvcnQgZnVuY3Rpb24gbmV3X3N0b3JlKCkg
ewogIHJldHVybiBuZXcgTWFwKERFRkFVTFRfTEFOR1VBR0VTLm1hcCgobCkg
PT4gW2wuY29kZSwgeyAuLi5sIH1dKSk7Cn0KCi8qKiBBZGQgYSBsYW5ndWFn
ZS4gUmVqZWN0cyBpbnZhbGlkIGNvZGVzIGFuZCBkdXBsaWNhdGVzLiAqLwpl
eHBvcnQgZnVuY3Rpb24gYWRkX2xhbmd1YWdlKHN0b3JlLCB7IGNvZGUsIG5h
bWUgfSkgewogIGlmICghaXNWYWxpZElTT0NvZGUoY29kZSkpIHRocm93IG5l
dyBFcnJvcignaW52YWxpZCBJU08gNjM5LTEgY29kZScpOwogIGlmICghbmFt
ZSB8fCAhbmFtZS50cmltKCkpIHRocm93IG5ldyBFcnJvcignbmFtZSBpcyBy
ZXF1aXJlZCcpOwogIGlmIChzdG9yZS5oYXMoY29kZSkpIHRocm93IG5ldyBF
cnJvcignbGFuZ3VhZ2UgYWxyZWFkeSBleGlz
...
```

**`backend/services/statistics.js`** (2305 bytes)
```
LyoqCiAqIExlYXJuaW5nLXN0YXRpc3RpY3MgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIFB1cmUgZnVuY3Rpb25z
IG92ZXIgcGxhaW4gInJldmlldyByZWNvcmQiIGFycmF5cyBzbyB0aGUgdW5p
dCBzdWl0ZSBjYW4KICogYXNzZXJ0IHRoZSBtYXRocyAoYXZlcmFnZXMsIHBy
b2dyZXNzICUsIHdlYWstd29yZCBzZWxlY3Rpb24pIHdpdGggbW9jayBkYXRh
CiAqIGFuZCBubyBkYXRhYmFzZSBvciBuZXR3b3JrLgogKgogKiBBIHJldmll
dyByZWNvcmQgbG9va3MgbGlrZToKICogICB7IHdvcmRJZCwgc2NvcmUgKDAu
LjEwMCksIHJldmlld2VkQXQgKElTTyBzdHJpbmcgb3IgZXBvY2ggbXMpIH0K
ICovCgovKiogQXZlcmFnZSBvZiBhIG51bWVyaWMgYXJyYXksIDAgZm9yIGVt
cHR5IGlucHV0LiAqLwpmdW5jdGlvbiBfYXZnKG51bXMpIHsKICBpZiAobnVt
cy5sZW5ndGggPT09IDApIHJldHVybiAwOwogIHJldHVybiBudW1zLnJlZHVj
ZSgoYSwgYikgPT4gYSArIGIsIDApIC8gbnVtcy5sZW5ndGg7Cn0KCi8qKgog
KiBBZ2dyZWdhdGUgcGVyLXVzZXIgc3RhdHMgZnJvbSB0aGVpciByZXZpZXcg
cmVjb3Jkcy4KICogQHJldHVybnMge3t0b3RhbFJldmlld3M6bnVtYmVyLCBs
ZWFybmVkV29yZHM6bnVtYmVyLCBhdmVyYWdlU2NvcmU6bnVtYmVyfX0KICov
CmV4cG9ydCBmdW5jdGlvbiBnZXRfdXNlcl9zdGF0cyhyZWNvcmRzID0gW10p
IHsKICBpZiAoIUFycmF5LmlzQXJyYXkocmVjb3JkcykpIHRocm93IG5ldyBF
cnJvcigncmVjb3JkcyBtdXN0IGJlIGFuIGFycmF5Jyk7CiAgY29uc3QgdG90
YWxSZXZpZXdzID0gcmVjb3Jkcy5sZW5ndGg7CiAgLy8gQSB3b3JkIGlzICJs
ZWFybmVkIiBvbmNlIGFueSByZXZpZXcgc2NvcmVzIGl0ID49IDgwLgogIGNv
bnN0IGxlYXJuZWQgPSBuZXcgU2V0KAogICAgcmVjb3Jkcy5maWx0ZXIoKHIp
ID0+IHIuc2NvcmUgPj0gODApLm1hcCgocikgPT4gci53b3JkSWQpLAogICk7
CiAgcmV0dXJuIHsKICAgIHRvdGFsUmV2aWV3cywKICAgIGxlYXJuZWRXb3Jk
czogbGVhcm5lZC5zaXplLAogICAgYXZlcmFnZVNjb3JlOiBNYXRoLnJvdW5k
KF9hdmcocmVjb3Jkcy5tYXAoKHIpID0+IHIu
...
```

**`backend/services/audioService.js`** (2864 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENyZWRlbnRpYWwtZnJlZSBhdWRpbyBwcm9jZXNz
aW5nIGJ1aWx0IG9uIHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcKICogYmlu
YXJ5LiBQb3dlcnMgUE9TVCAvYXBpL2F1ZGlvL3Byb2Nlc3MuIFVubGlrZSB0
aGUgR2VtaW5pLWJhY2tlZCBUVFMvY2hhdAogKiByb3V0ZXMsIGF1ZGlvIHBy
b2JpbmcvdHJhbnNjb2RpbmcgaGVyZSBuZWVkcyBubyBleHRlcm5hbCBBUEkg
a2V5LCBzbyB0aGUKICogZW5kcG9pbnQgYWx3YXlzIHdvcmtzIGFzIGxvbmcg
YXMgdGhlIHJ1bnRpbWUgZGVwcyAoZmx1ZW50LWZmbXBlZyArCiAqIGZmbXBl
Zy1zdGF0aWMpIGRlY2xhcmVkIGluIGJhY2tlbmQvcGFja2FnZS5qc29uIGFy
ZSBpbnN0YWxsZWQuCiAqCiAqIFVwc3RyZWFtIChpbnB1dHMpOiBhbiBvcHRp
b25hbCB1cGxvYWRlZCBhdWRpbyBmaWxlIChwYXRoIG9uIGRpc2spIGFuZCB0
aGUKICogYGZsdWVudC1mZm1wZWdgIC8gYGZmbXBlZy1zdGF0aWNgIHBhY2th
Z2VzLgogKiBEb3duc3RyZWFtIChvdXRwdXRzKTogYSBwbGFpbiBgeyBzdGF0
dXMsIHJlc3VsdCB9YCBvYmplY3QgY29uc3VtZWQgYnkKICogY29udHJvbGxl
cnMvYXVkaW9Db250cm9sbGVyLmpzIGFuZCwgaW4gdHVybiwgdGhlIGZyb250
ZW5kIGF1ZGlvIHRvb2xpbmcuCiAqLwppbXBvcnQgZnMgZnJvbSAnZnMnOwpp
bXBvcnQgb3MgZnJvbSAnb3MnOwppbXBvcnQgeyBqb2luIH0gZnJvbSAncGF0
aCc7CmltcG9ydCBmZm1wZWcgZnJvbSAnZmx1ZW50LWZmbXBlZyc7CmltcG9y
dCBmZm1wZWdTdGF0aWMgZnJvbSAnZmZtcGVnLXN0YXRpYyc7CgovLyBQb2lu
dCBmbHVlbnQtZmZtcGVnIGF0IHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcg
YmluYXJ5IHNvIG5vIHN5c3RlbSBpbnN0YWxsCi8vIGlzIHJlcXVpcmVkICht
aXJyb3JzIHNlcnZpY2VzL3ZpZGVvU2VydmljZS5qcykuCmlmIChmZm1wZWdT
dGF0aWMpIHsKICBmZm1wZWcuc2V0RmZtcGVnUGF0aChmZm1wZWdTdGF0aWMp
Owp9CgovLyBBdWRpbyBjb250YWluZXIvY29kZWMgZmFtaWxpZXMgdGhlIHBp
cGVsaW5lIGFjY2VwdHMgZm9yIHByb2JpbmcvdHJhbnNjb2RpbmcuCmV4cG9y
dCBjb25zdCBTVVBQT1JURURfQVVESU9fRk9S
...
```

### 🔗 Route ها و Endpoint ها (1 فایل)

**`backend/controllers/index.js`** (718 bytes)
```
LyoqCiAqIENvbnRyb2xsZXJzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xl
IHB1YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIEhUVFAgaGFuZGxlciBsYXll
ciBzbyB0aGUgcmVzdCBvZiB0aGUgYXBwCiAqIChyb3V0ZXMsIHNlcnZlciBj
b21wb3NpdGlvbikgY2FuIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL2NvbnRy
b2xsZXJzJ2AgaW5zdGVhZAogKiBvZiByZWFjaGluZyBpbnRvIGluZGl2aWR1
YWwgaGFuZGxlciBmaWxlcy4gRWFjaCBjb250cm9sbGVyIG93bnMgdGhlCiAq
IHJlcXVlc3QvcmVzcG9uc2Ugc2hhcGUgZm9yIG9uZSBzbGljZSBvZiB0aGUg
QVBJOyB0aGlzIGluZGV4IHNpbXBseSByZS1leHBvcnRzCiAqIHRoZWlyIHB1
YmxpYyBoYW5kbGVycy4gRGVmYXVsdCBleHBvcnRzIGFyZSBpbnRlbnRpb25h
bGx5IG5vdCBmb3J3YXJkZWQg4oCUIHRoZQogKiBuYW1lZCBoYW5kbGVycyBh
cmUgdGhlIHN0YWJsZSBjb250cmFjdC4KICovCmV4cG9ydCAqIGZyb20gJy4v
YW5hbHlzaXNDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hbmFs
eXRpY3NDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hdWRpb0Nv
bnRyb2xsZXIuanMnOwpleHBvcnQgKiBmcm9tICcuL2ZhbGxiYWNrQ29udHJv
bGxlci5qcyc7CmV4cG9ydCAqIGZyb20gJy4vZ2VtaW5pQ29udHJvbGxlci5q
cyc7CmV4cG9ydCAqIGZyb20gJy4vdXBsb2FkQ29udHJvbGxlci5qcyc7Cg==

```

---

### 💡 دستورالعمل ادغام

- الگوهای بالا را **شناسایی** کن: ساختار فایل‌ها، نام‌گذاری، patternهای معماری، روش‌های handle errors، …
- اما **در پروژهٔ فعلی** پیاده‌سازی کن — با stack، نام‌گذاری، و سبک کد همان پروژه. نه stack پروژه‌های مرجع.
- اگر پروژه‌های مرجع stack متفاوت دارند (مثلاً Vue ولی پروژه فعلی React)، **منطق** را منتقل کن نه syntax را.

---

---
## 📚 پروژه‌های مرجع (الهام از پیاده‌سازی‌های موجود)
_در زیر خلاصهٔ ساختار/فایل‌های پروژه‌های زیر آمده است. از این منابع به‌عنوان الگو/الهام استفاده کن و در پرامپت نهایی به فایل‌ها/الگوهای مرتبط ارجاع بده._

## 📚 پروژه‌های مرجع (Reference Projects)

کاربر این پروژه‌ها را به‌عنوان منبع الهام برای این تسک انتخاب کرده است. هدف از این بخش: الگوها، معماری، یا منطق این پروژه‌ها را در نظر بگیر و در پیاده‌سازی **پروژهٔ فعلی** اعمال کن — نه کپی کردن صرف.

**کار درخواست‌شده روی پروژهٔ فعلی:** ```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره

2- باید امکان لاگین از طریق جیمیل فراهم باشه

3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
5- از منظر ظاهری خیلی آشفته اس
6- در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?

### 🏠 شناسنامهٔ پروژهٔ فعلی (مرجع اصلی برای پیاده‌سازی)

**هرگاه بین پروژهٔ فعلی و پروژه‌های مرجع تفاوت بود (stack، نام‌گذاری، dependency)، پروژهٔ فعلی برنده است. هرگز syntax یا dependency پروژه‌های مرجع را کورکورانه به پروژهٔ فعلی نیاور.**

- **Repo**: `mahdighandi1989/ALLIN1`
- **زبان غالب**: HTML

---

### پروژه‌های اسکن‌شده

- ✅ `mahdighandi1989/language` — 12 فایل اسکن‌شده (از 359 کل)
  - 🎯 **نقطهٔ تمرکز کاربر**: _امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد_
    (فایل‌های اسکن‌شده بالا با اولویت بر اساس همین تمرکز انتخاب شده‌اند — به بقیهٔ پروژه توجه نکن مگر برای زمینه.)

### ⚙️ سرویس‌های Backend (11 فایل)

**`backend/services/index.js`** (799 bytes)
```
LyoqCiAqIFNlcnZpY2VzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xlIHB1
YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIGRvbWFpbi9zZXJ2aWNlIGxheWVy
IHNvIGNhbGxlcnMgY2FuCiAqIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL3Nl
cnZpY2VzJ2AuIENvdmVycyBhbmFseXRpY3MgY29sbGVjdGlvbiwgZmlsZSBh
bmFseXNpcywKICogdGhlIEdlbWluaSBSRVNUICsgRmlsZSBBUEkgY2xpZW50
LCBhdWRpby92aWRlbyBmZm1wZWcgaGVscGVycywgUERGIHRleHQKICogZXh0
cmFjdGlvbiwgdGhlIExpdmUgQVBJIFdlYlNvY2tldCBwcm94eS9vYnNlcnZl
ciBhbmQgdGhlIFRlbGVncmFtCiAqIGludGVncmF0aW9uLiBOYW1lZCBleHBv
cnRzIGFyZSB0aGUgc3RhYmxlIGNvbnRyYWN0OyBwZXItZmlsZSBkZWZhdWx0
IGV4cG9ydHMKICogYXJlIG5vdCBmb3J3YXJkZWQuCiAqLwpleHBvcnQgKiBm
cm9tICcuL2FuYWx5c2lzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4v
YW5hbHl0aWNzU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vYXVkaW9T
ZXJ2aWNlLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9nZW1pbmlTZXJ2aWNlLmpz
JzsKZXhwb3J0ICogZnJvbSAnLi9saXZlUHJveHlTZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi9saXZlV3NPYnNlcnZlci5qcyc7CmV4cG9ydCAqIGZy
b20gJy4vcGRmU2VydmljZS5qcyc7CmV4cG9ydCAqIGZyb20gJy4vcHJvbXB0
cy5qcyc7CmV4cG9ydCAqIGZyb20gJy4vdmlkZW9TZXJ2aWNlLmpzJzsKZXhw
b3J0ICogZnJvbSAnLi90ZWxlZ3JhbS9pbmRleC5qcyc7Cg==

```

**`backend/services/telegram/config.js`** (3725 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENlbnRyYWxpc2VkLCBlbnYtZHJpdmVuIGNvbmZp
Z3VyYXRpb24gZm9yIHRoZSB0d28td2F5IFRlbGVncmFtCiAqIGludGVncmF0
aW9uLiBSZWFkaW5nIHRoaXMgbW9kdWxlIG5ldmVyIHRocm93cyBhbmQgbmV2
ZXIgZXhpdHMgdGhlIHByb2Nlc3Mg4oCUCiAqIHRoZSBUZWxlZ3JhbSBib3Qg
aXMgYW4gKm9wdGlvbmFsKiBmZWF0dXJlLCBzbyB3aGVuIG5vIGJvdCB0b2tl
biBpcyBjb25maWd1cmVkCiAqIHRoZSByZXN0IG9mIHRoZSBzeXN0ZW0ga2Vl
cHMgd29ya2luZyBhbmQgdGhlIGJvdCBzaW1wbHkgc3RheXMgZG9ybWFudC4K
ICoKICogVXBzdHJlYW0gKGlucHV0cyk6IGVudmlyb25tZW50IHZhcmlhYmxl
cyAoVEVMRUdSQU1fQk9UX1RPS0VOLAogKiBURUxFR1JBTV9XRUJIT09LX1VS
TCwgVEVMRUdSQU1fQURNSU5fSURTLCBURUxFR1JBTV9BTExPV0VEX1VTRVJf
SURTLAogKiBURUxFR1JBTV9EQVRBX0RJUiwgVEVMRUdSQU1fTU9ERSwgTk9U
SUZZX1RFTEVHUkFNX0JPVF9UT0tFTi9DSEFUX0lEIGZvcgogKiBiYWNrd2Fy
ZC1jb21wYXRpYmxlIG5vdGlmaWNhdGlvbiBkZWxpdmVyeSkuCiAqIERvd25z
dHJlYW0gKG91dHB1dHMpOiBjb25zdW1lZCBieSBzZXJ2aWNlcy90ZWxlZ3Jh
bS8qIChjbGllbnQsIGJvdCwgc3RvcmUsCiAqIG5vdGlmaWNhdGlvbnMpIGFu
ZCB3aXJlZCBpbnRvIHNlcnZlci5qcyB2aWEgc2VydmljZXMvdGVsZWdyYW0v
aW5kZXguanMuCiAqLwppbXBvcnQgeyBmaWxlVVJMVG9QYXRoIH0gZnJvbSAn
dXJsJzsKaW1wb3J0IHsgZGlybmFtZSwgam9pbiB9IGZyb20gJ3BhdGgnOwoK
Y29uc3QgX19kaXJuYW1lID0gZGlybmFtZShmaWxlVVJMVG9QYXRoKGltcG9y
dC5tZXRhLnVybCkpOwoKLy8gUGFyc2UgYSBjb21tYS9zcGFjZSBzZXBhcmF0
ZWQgbGlzdCBvZiBudW1lcmljIFRlbGVncmFtIGlkcyBpbnRvIGEgU2V0IG9m
Ci8vIHN0cmluZ3MgKFRlbGVncmFtIGlkcyBhcmUgNjQtYml0IGFuZCBzYWZl
ciBjb21wYXJlZCBhcyBzdHJpbmdzKS4KZnVuY3Rpb24gcGFyc2VJZExpc3Qo
cmF3KSB7CiAgaWYgKCFyYXcpIHJldHVybiBuZXcgU2V0KCk7CiAgcmV0dXJu
IG5ldyBTZXQoCiAgICBTdHJpbmcocmF3KQog
...
```

**`backend/services/telegram/index.js`** (5893 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENvbXBvc2l0aW9uIHJvb3QgKyBFeHByZXNzIHdp
cmluZyBmb3IgdGhlIFRlbGVncmFtIGludGVncmF0aW9uLiBJdAogKiBhc3Nl
bWJsZXMgdGhlIGNsaWVudCwgc3RvcmUsIGxvZ2dlciwgbm90aWZpY2F0aW9u
IHNlcnZpY2UsIHByYWN0aWNlIG1hbmFnZXIsCiAqIGNvbW1hbmRzIGFuZCBi
b3QgZnJvbSBjb25maWcsIGV4cG9zZXMgdGhlIGFzc2VtYmxlZCBzZXJ2aWNl
IGFzIGEgc2luZ2xldG9uIHNvCiAqIHJlcXVlc3QgaGFuZGxlcnMgZWxzZXdo
ZXJlIGNhbiBlbWl0IG5vdGlmaWNhdGlvbnMsIGFuZCByZWdpc3RlcnMgdGhl
IEhUVFAKICogc3VyZmFjZTogdGhlIGluYm91bmQgd2ViaG9vayBhbmQgdGhl
IHdlYnNpdGUtc2lkZSBhY2NvdW50LWxpbmsgZW5kcG9pbnQuCiAqCiAqIFVw
c3RyZWFtIChpbnB1dHMpOiBlbnZpcm9ubWVudCB2aWEgc2VydmljZXMvdGVs
ZWdyYW0vY29uZmlnLmpzOyB0aGUgZXhpc3RpbmcKICogR2VtaW5pIGNvbmZp
ZyAoZm9yIHRoZSBwcmFjdGljZSBwcm92aWRlciArIHN0YXR1cykgYW5kIHRo
ZSBFeHByZXNzIGFwcCBmcm9tCiAqIHNlcnZlci5qcy4KICogRG93bnN0cmVh
bSAob3V0cHV0cyk6IHdoZW4gYSBib3QgdG9rZW4gaXMgY29uZmlndXJlZCwg
c3RhcnRzIHBvbGxpbmcgb3Igc2V0cyBhCiAqIHdlYmhvb2s7IHJlZ2lzdGVy
cyBQT1NUIC9hcGkvdGVsZWdyYW0vd2ViaG9vaywgUE9TVCAvYXBpL3RlbGVn
cmFtL2xpbmsgYW5kCiAqIEdFVCAvYXBpL3RlbGVncmFtL3N0YXR1cy4gV2hl
biBubyB0b2tlbiBpcyBjb25maWd1cmVkIGV2ZXJ5IGV4cG9ydCBkZWdyYWRl
cyB0bwogKiBhIHNhZmUgbm8tb3Agc28gdGhlIHNlcnZlciBib290cyBub3Jt
YWxseSAoZS5nLiBpbiBDSS90ZXN0cykuCiAqLwppbXBvcnQgeyBsb2FkVGVs
ZWdyYW1Db25maWcgfSBmcm9tICcuL2NvbmZpZy5qcyc7CmltcG9ydCB7IFRl
bGVncmFtQ2xpZW50IH0gZnJvbSAnLi9jbGllbnQuanMnOwppbXBvcnQgeyBU
ZWxlZ3JhbVN0b3JlIH0gZnJvbSAnLi9zdG9yZS5qcyc7CmltcG9ydCB7IFRl
bGVncmFtTG9nZ2VyIH0gZnJvbSAnLi9sb2dnZXIuanMnOwppbXBvcnQgeyBO
b3RpZmljYXRpb25TZXJ2aWNlLCBFdmVudEJ1
...
```

**`backend/services/prompts.js`** (649 bytes)
```
Ly8gQmFja3dhcmQtY29tcGF0aWJsZSByZS1leHBvcnQgc2hpbS4KLy8KLy8g
VGhlIGNhbm9uaWNhbCBwcm9tcHQgZGVmaW5pdGlvbnMgbm93IGxpdmUgaW4g
YmFja2VuZC9tb2RlbHMvcHJvbXB0cy5qcyBhcwovLyBwYXJ0IG9mIHRoZSBs
YXllcmVkLWFyY2hpdGVjdHVyZSByZXN0cnVjdHVyZSAoc3RhdGljIGRvbWFp
biBkYXRhIGJlbG9uZ3MgaW4KLy8gbW9kZWxzLykuIFNlcnZpY2UtbGF5ZXIg
Y29kZSBoaXN0b3JpY2FsbHkgaW1wb3J0ZWQgdGhlc2UgZnJvbQovLyBzZXJ2
aWNlcy9wcm9tcHRzLmpzLCBzbyB0aGlzIG1vZHVsZSByZS1leHBvcnRzIHRo
ZW0gdG8ga2VlcCB0aG9zZSBpbXBvcnRzCi8vIHdvcmtpbmcgd2l0aG91dCB0
b3VjaGluZyBldmVyeSBjYWxsIHNpdGUuCi8vCi8vIE5hbWVkIHN5bWJvbHMg
KExFQkFORVNFX0NPUlJFQ1RJT05fUFJPTVBULCBBTkFMWVNJU19TWVNURU1f
UFJPTVBULAovLyBkZWZhdWx0TGl2ZVByb21wdHMpIGFyZSBmb3J3YXJkZWQg
dmVyYmF0aW0gZnJvbSAuLi9tb2RlbHMvcHJvbXB0cy5qcy4KZXhwb3J0IHsK
ICBMRUJBTkVTRV9DT1JSRUNUSU9OX1BST01QVCwKICBBTkFMWVNJU19TWVNU
RU1fUFJPTVBULAogIGRlZmF1bHRMaXZlUHJvbXB0cywKfSBmcm9tICcuLi9t
b2RlbHMvcHJvbXB0cy5qcyc7Cg==

```

**`backend/services/pdfService.js`** (704 bytes)
```
Ly8gRXh0cmFjdCB0ZXh0IGZyb20gYSBQREYgYnVmZmVyIHVzaW5nIHBkZi1w
YXJzZSAoaW1wb3J0ZWQgZHluYW1pY2FsbHkgc28gYQovLyBtaXNzaW5nIG9w
dGlvbmFsIGRlcGVuZGVuY3kgc3VyZmFjZXMgYXMgYSBjbGVhciBtZXNzYWdl
IHJhdGhlciB0aGFuIGEgY3Jhc2gpLgpleHBvcnQgYXN5bmMgZnVuY3Rpb24g
ZXh0cmFjdFBkZlRleHQoYnVmZmVyKSB7CiAgdHJ5IHsKICAgIGNvbnN0IHBk
ZlBhcnNlID0gKGF3YWl0IGltcG9ydCgncGRmLXBhcnNlJykpLmRlZmF1bHQ7
CiAgICBjb25zdCBkYXRhID0gYXdhaXQgcGRmUGFyc2UoYnVmZmVyKTsKICAg
IHJldHVybiBkYXRhLnRleHQ7CiAgfSBjYXRjaCAoZXJyb3IpIHsKICAgIGNv
bnNvbGUuZXJyb3IoJ1BERiBleHRyYWN0aW9uIGVycm9yOicsIGVycm9yKTsK
ICAgIGlmIChlcnJvci5jb2RlID09PSAnRVJSX01PRFVMRV9OT1RfRk9VTkQn
KSB7CiAgICAgIHRocm93IG5ldyBFcnJvcign2YXYp9qY2YjZhCBwZGYtcGFy
c2Ug2YbYtdioINmG24zYs9iqLiDZhNi32YHYp9mLIG5wbSBpbnN0YWxsIHBk
Zi1wYXJzZSDYsdinINin2KzYsdinINqp2YbbjNivLicpOwogICAgfQogICAg
dGhyb3cgbmV3IEVycm9yKCfYrti32Kcg2K/YsSDYp9iz2KrYrtix2KfYrCDZ
hdiq2YYg2KfYsiBQREY6ICcgKyBlcnJvci5tZXNzYWdlKTsKICB9Cn0KCmV4
cG9ydCBkZWZhdWx0IGV4dHJhY3RQZGZUZXh0Owo=

```

**`backend/services/languageService.js`** (2045 bytes)
```
LyoqCiAqIExhbmd1YWdlLW1hbmFnZW1lbnQgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIE1vZGVscyB0aGUgc21h
bGwgY2F0YWxvZ3VlIG9mIHN1cHBvcnRlZCBsYW5ndWFnZXMgcGx1cyBzaW1w
bGUsIG9mZmxpbmUKICogaGV1cmlzdGljcyBmb3IgbGFuZ3VhZ2UgZGV0ZWN0
aW9uIChzY3JpcHQtYmFzZWQpIGFuZCBJU08gNjM5LTEgdmFsaWRhdGlvbi4K
ICogTm8gZGF0YWJhc2UsIG5vIGV4dGVybmFsIHRyYW5zbGF0aW9uL2RldGVj
dGlvbiBBUEkuCiAqLwoKY29uc3QgSVNPXzYzOV8xX1JFID0gL15bYS16XXsy
fSQvOwoKY29uc3QgREVGQVVMVF9MQU5HVUFHRVMgPSBbCiAgeyBjb2RlOiAn
YXInLCBuYW1lOiAnQXJhYmljJyB9LAogIHsgY29kZTogJ2VuJywgbmFtZTog
J0VuZ2xpc2gnIH0sCiAgeyBjb2RlOiAnZmEnLCBuYW1lOiAnUGVyc2lhbicg
fSwKXTsKCi8qKiBWYWxpZGF0ZSBhbiBJU08gNjM5LTEgY29kZTogZXhhY3Rs
eSB0d28gbG93ZXJjYXNlIGxldHRlcnMuICovCmV4cG9ydCBmdW5jdGlvbiBp
c1ZhbGlkSVNPQ29kZShjb2RlKSB7CiAgcmV0dXJuIHR5cGVvZiBjb2RlID09
PSAnc3RyaW5nJyAmJiBJU09fNjM5XzFfUkUudGVzdChjb2RlKTsKfQoKLyoq
IEZyZXNoIGNhdGFsb2d1ZSBzdG9yZSwgc2VlZGVkIHdpdGggdGhlIGRlZmF1
bHQgbGFuZ3VhZ2VzLiAqLwpleHBvcnQgZnVuY3Rpb24gbmV3X3N0b3JlKCkg
ewogIHJldHVybiBuZXcgTWFwKERFRkFVTFRfTEFOR1VBR0VTLm1hcCgobCkg
PT4gW2wuY29kZSwgeyAuLi5sIH1dKSk7Cn0KCi8qKiBBZGQgYSBsYW5ndWFn
ZS4gUmVqZWN0cyBpbnZhbGlkIGNvZGVzIGFuZCBkdXBsaWNhdGVzLiAqLwpl
eHBvcnQgZnVuY3Rpb24gYWRkX2xhbmd1YWdlKHN0b3JlLCB7IGNvZGUsIG5h
bWUgfSkgewogIGlmICghaXNWYWxpZElTT0NvZGUoY29kZSkpIHRocm93IG5l
dyBFcnJvcignaW52YWxpZCBJU08gNjM5LTEgY29kZScpOwogIGlmICghbmFt
ZSB8fCAhbmFtZS50cmltKCkpIHRocm93IG5ldyBFcnJvcignbmFtZSBpcyBy
ZXF1aXJlZCcpOwogIGlmIChzdG9yZS5oYXMoY29kZSkpIHRocm93IG5ldyBF
cnJvcignbGFuZ3VhZ2UgYWxyZWFkeSBleGlz
...
```

**`backend/services/statistics.js`** (2305 bytes)
```
LyoqCiAqIExlYXJuaW5nLXN0YXRpc3RpY3MgZG9tYWluIGxvZ2ljIChpbi1t
ZW1vcnksIGRlcGVuZGVuY3ktZnJlZSkuCiAqCiAqIFB1cmUgZnVuY3Rpb25z
IG92ZXIgcGxhaW4gInJldmlldyByZWNvcmQiIGFycmF5cyBzbyB0aGUgdW5p
dCBzdWl0ZSBjYW4KICogYXNzZXJ0IHRoZSBtYXRocyAoYXZlcmFnZXMsIHBy
b2dyZXNzICUsIHdlYWstd29yZCBzZWxlY3Rpb24pIHdpdGggbW9jayBkYXRh
CiAqIGFuZCBubyBkYXRhYmFzZSBvciBuZXR3b3JrLgogKgogKiBBIHJldmll
dyByZWNvcmQgbG9va3MgbGlrZToKICogICB7IHdvcmRJZCwgc2NvcmUgKDAu
LjEwMCksIHJldmlld2VkQXQgKElTTyBzdHJpbmcgb3IgZXBvY2ggbXMpIH0K
ICovCgovKiogQXZlcmFnZSBvZiBhIG51bWVyaWMgYXJyYXksIDAgZm9yIGVt
cHR5IGlucHV0LiAqLwpmdW5jdGlvbiBfYXZnKG51bXMpIHsKICBpZiAobnVt
cy5sZW5ndGggPT09IDApIHJldHVybiAwOwogIHJldHVybiBudW1zLnJlZHVj
ZSgoYSwgYikgPT4gYSArIGIsIDApIC8gbnVtcy5sZW5ndGg7Cn0KCi8qKgog
KiBBZ2dyZWdhdGUgcGVyLXVzZXIgc3RhdHMgZnJvbSB0aGVpciByZXZpZXcg
cmVjb3Jkcy4KICogQHJldHVybnMge3t0b3RhbFJldmlld3M6bnVtYmVyLCBs
ZWFybmVkV29yZHM6bnVtYmVyLCBhdmVyYWdlU2NvcmU6bnVtYmVyfX0KICov
CmV4cG9ydCBmdW5jdGlvbiBnZXRfdXNlcl9zdGF0cyhyZWNvcmRzID0gW10p
IHsKICBpZiAoIUFycmF5LmlzQXJyYXkocmVjb3JkcykpIHRocm93IG5ldyBF
cnJvcigncmVjb3JkcyBtdXN0IGJlIGFuIGFycmF5Jyk7CiAgY29uc3QgdG90
YWxSZXZpZXdzID0gcmVjb3Jkcy5sZW5ndGg7CiAgLy8gQSB3b3JkIGlzICJs
ZWFybmVkIiBvbmNlIGFueSByZXZpZXcgc2NvcmVzIGl0ID49IDgwLgogIGNv
bnN0IGxlYXJuZWQgPSBuZXcgU2V0KAogICAgcmVjb3Jkcy5maWx0ZXIoKHIp
ID0+IHIuc2NvcmUgPj0gODApLm1hcCgocikgPT4gci53b3JkSWQpLAogICk7
CiAgcmV0dXJuIHsKICAgIHRvdGFsUmV2aWV3cywKICAgIGxlYXJuZWRXb3Jk
czogbGVhcm5lZC5zaXplLAogICAgYXZlcmFnZVNjb3JlOiBNYXRoLnJvdW5k
KF9hdmcocmVjb3Jkcy5tYXAoKHIpID0+IHIu
...
```

**`backend/services/audioService.js`** (2864 bytes)
```
LyoqCiAqIFB1cnBvc2U6IENyZWRlbnRpYWwtZnJlZSBhdWRpbyBwcm9jZXNz
aW5nIGJ1aWx0IG9uIHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcKICogYmlu
YXJ5LiBQb3dlcnMgUE9TVCAvYXBpL2F1ZGlvL3Byb2Nlc3MuIFVubGlrZSB0
aGUgR2VtaW5pLWJhY2tlZCBUVFMvY2hhdAogKiByb3V0ZXMsIGF1ZGlvIHBy
b2JpbmcvdHJhbnNjb2RpbmcgaGVyZSBuZWVkcyBubyBleHRlcm5hbCBBUEkg
a2V5LCBzbyB0aGUKICogZW5kcG9pbnQgYWx3YXlzIHdvcmtzIGFzIGxvbmcg
YXMgdGhlIHJ1bnRpbWUgZGVwcyAoZmx1ZW50LWZmbXBlZyArCiAqIGZmbXBl
Zy1zdGF0aWMpIGRlY2xhcmVkIGluIGJhY2tlbmQvcGFja2FnZS5qc29uIGFy
ZSBpbnN0YWxsZWQuCiAqCiAqIFVwc3RyZWFtIChpbnB1dHMpOiBhbiBvcHRp
b25hbCB1cGxvYWRlZCBhdWRpbyBmaWxlIChwYXRoIG9uIGRpc2spIGFuZCB0
aGUKICogYGZsdWVudC1mZm1wZWdgIC8gYGZmbXBlZy1zdGF0aWNgIHBhY2th
Z2VzLgogKiBEb3duc3RyZWFtIChvdXRwdXRzKTogYSBwbGFpbiBgeyBzdGF0
dXMsIHJlc3VsdCB9YCBvYmplY3QgY29uc3VtZWQgYnkKICogY29udHJvbGxl
cnMvYXVkaW9Db250cm9sbGVyLmpzIGFuZCwgaW4gdHVybiwgdGhlIGZyb250
ZW5kIGF1ZGlvIHRvb2xpbmcuCiAqLwppbXBvcnQgZnMgZnJvbSAnZnMnOwpp
bXBvcnQgb3MgZnJvbSAnb3MnOwppbXBvcnQgeyBqb2luIH0gZnJvbSAncGF0
aCc7CmltcG9ydCBmZm1wZWcgZnJvbSAnZmx1ZW50LWZmbXBlZyc7CmltcG9y
dCBmZm1wZWdTdGF0aWMgZnJvbSAnZmZtcGVnLXN0YXRpYyc7CgovLyBQb2lu
dCBmbHVlbnQtZmZtcGVnIGF0IHRoZSBidW5kbGVkIHN0YXRpYyBmZm1wZWcg
YmluYXJ5IHNvIG5vIHN5c3RlbSBpbnN0YWxsCi8vIGlzIHJlcXVpcmVkICht
aXJyb3JzIHNlcnZpY2VzL3ZpZGVvU2VydmljZS5qcykuCmlmIChmZm1wZWdT
dGF0aWMpIHsKICBmZm1wZWcuc2V0RmZtcGVnUGF0aChmZm1wZWdTdGF0aWMp
Owp9CgovLyBBdWRpbyBjb250YWluZXIvY29kZWMgZmFtaWxpZXMgdGhlIHBp
cGVsaW5lIGFjY2VwdHMgZm9yIHByb2JpbmcvdHJhbnNjb2RpbmcuCmV4cG9y
dCBjb25zdCBTVVBQT1JURURfQVVESU9fRk9S
...
```

### 🔗 Route ها و Endpoint ها (1 فایل)

**`backend/controllers/index.js`** (718 bytes)
```
LyoqCiAqIENvbnRyb2xsZXJzIGxheWVyIGJhcnJlbC4KICoKICogU2luZ2xl
IHB1YmxpYyBlbnRyeSBwb2ludCBmb3IgdGhlIEhUVFAgaGFuZGxlciBsYXll
ciBzbyB0aGUgcmVzdCBvZiB0aGUgYXBwCiAqIChyb3V0ZXMsIHNlcnZlciBj
b21wb3NpdGlvbikgY2FuIGBpbXBvcnQgeyDigKYgfSBmcm9tICcuL2NvbnRy
b2xsZXJzJ2AgaW5zdGVhZAogKiBvZiByZWFjaGluZyBpbnRvIGluZGl2aWR1
YWwgaGFuZGxlciBmaWxlcy4gRWFjaCBjb250cm9sbGVyIG93bnMgdGhlCiAq
IHJlcXVlc3QvcmVzcG9uc2Ugc2hhcGUgZm9yIG9uZSBzbGljZSBvZiB0aGUg
QVBJOyB0aGlzIGluZGV4IHNpbXBseSByZS1leHBvcnRzCiAqIHRoZWlyIHB1
YmxpYyBoYW5kbGVycy4gRGVmYXVsdCBleHBvcnRzIGFyZSBpbnRlbnRpb25h
bGx5IG5vdCBmb3J3YXJkZWQg4oCUIHRoZQogKiBuYW1lZCBoYW5kbGVycyBh
cmUgdGhlIHN0YWJsZSBjb250cmFjdC4KICovCmV4cG9ydCAqIGZyb20gJy4v
YW5hbHlzaXNDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hbmFs
eXRpY3NDb250cm9sbGVyLmpzJzsKZXhwb3J0ICogZnJvbSAnLi9hdWRpb0Nv
bnRyb2xsZXIuanMnOwpleHBvcnQgKiBmcm9tICcuL2ZhbGxiYWNrQ29udHJv
bGxlci5qcyc7CmV4cG9ydCAqIGZyb20gJy4vZ2VtaW5pQ29udHJvbGxlci5q
cyc7CmV4cG9ydCAqIGZyb20gJy4vdXBsb2FkQ29udHJvbGxlci5qcyc7Cg==

```

---

### 💡 دستورالعمل ادغام

- الگوهای بالا را **شناسایی** کن: ساختار فایل‌ها، نام‌گذاری، patternهای معماری، روش‌های handle errors، …
- اما **در پروژهٔ فعلی** پیاده‌سازی کن — با stack، نام‌گذاری، و سبک کد همان پروژه. نه stack پروژه‌های مرجع.
- اگر پروژه‌های مرجع stack متفاوت دارند (مثلاً Vue ولی پروژه فعلی React)، **منطق** را منتقل کن نه syntax را.

---
```

## 🎯 هدف (خلاصه ساختاریافته)
بهبود UI ورود، افزودن لاگین گوگل، و رفع خطای 500 API کاربران

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/api/endpoints/auth.py:20-40` — `login_access_token` — این فایل برای افزودن endpointهای جدید Google OAuth (مانند /auth/google/login و /auth/google/callback) استفاده خواهد شد. snippet موجود نشان‌دهنده ساختار فعلی endpointهای احراز هویت است. بر اساس ساختار سطحی — توسط مجری تأیید شود.
  ```python
  @router.post("/login/access-token", response_model=schemas.Token)
      def login_access_token(
          db: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()
      ) -> Any:
          """
          OAuth2 compatible token login, get an access token for future requests
          """
          user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
          if not user:
              raise HTTPException(status_code=400, detail="Incorrect email or password")
  ```
- `backend/app/services/google_auth_service.py:1-30` — `GoogleAuthService` — این یک فایل جدید پیشنهادی برای پیاده‌سازی منطق Google OAuth است که از الگوی سرویس‌محور پروژه مرجع الهام گرفته شده است. این سرویس مسئول مدیریت جریان OAuth و دریافت اطلاعات کاربر خواهد بود. بر اساس ساختار سطحی — توسط مجری تأیید شود.
  ```python
  # Proposed new file content
  from google.oauth2 import credentials
  from google_auth_oauthlib.flow import Flow
  from googleapiclient.discovery import build
  from starlette.requests import Request
  from starlette.responses import RedirectResponse
  from backend.app.core.config import settings
  
  class GoogleAuthService:
      def __init__(self):
          self.flow = Flow.from_client_secrets_file(
              settings.GOOGLE_CLIENT_SECRETS_FILE,
              scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
              redirect_uri=settings.GOOGLE_REDIRECT_URI
          )
  
      def get_authorization_url(self, request: Request):
          authorization_url, state = self.flow.authorization_url(
              access_type='offline',
              include_granted_scopes='true'
          )
          request.session['oauth_state'] = state
          return authorization_url
  ```
- `frontend/src/app/login/page.tsx:10-40` — `LoginPage` — این فایل صفحه ورود فعلی است که نیاز به بازطراحی بصری و افزودن دکمه "Login with Google" دارد. snippet موجود نشان‌دهنده ساختار اولیه کامپوننت صفحه ورود است. بر اساس ساختار سطحی — توسط مجری تأیید شود.
  ```tsx
  import { useState } from 'react';
  import { useRouter } from 'next/navigation';
  import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
  import { Input } from '@/components/ui/input';
  import { Button } from '@/components/ui/button';
  
  export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const router = useRouter();
  
    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      // Login logic here
      console.log('Attempting login with', email, password);
      // On success, router.push('/dashboard');
    };
  
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <Card className="w-full max-w-md">
          <CardHeader>
            <h2 className="text-2xl font-bold text-center">Login</h2>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
  ```
- `backend/app/api/endpoints/users.py:15-25` — `read_users` — این endpoint مسئول واکشی لیست کاربران است و خطای 500 را ایجاد می‌کند. snippet موجود نشان‌دهنده پیاده‌سازی فعلی آن است. بر اساس ساختار سطحی — توسط مجری تأیید شود.
  ```python
  @router.get("/", response_model=list[schemas.User])
      def read_users(
          db: SessionDep,
          skip: int = 0,
          limit: int = 100,
          current_user: CurrentUser = Depends(get_current_active_superuser),
      ) -> Any:
          """
          Retrieve users.
          """
          users = crud.user.get_multi(db, skip=skip, limit=limit)
          return users
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
پروژه فعلی از FastAPI (پایتون 3.11+) برای بک‌اند و Next.js 14 (React 18) با Tailwind CSS برای فرانت‌اند استفاده می‌کند. احراز هویت با JWT و رفرش توکن‌ها انجام می‌شود و از Google OAuth 2.0 برای پشتیبان‌گیری در گوگل درایو استفاده شده است. پروژه مرجع `mahdighandi1989/language` از JavaScript (احتمالاً Node.js/Express) برای بک‌اند استفاده می‌کند. این تفاوت در استک فناوری به این معنی است که در حالی که *الگوی* یک لایه سرویس اختصاصی برای یکپارچه‌سازی‌های خارجی (مانند تلگرام در پروژه مرجع) الهام‌بخش است، *جزئیات پیاده‌سازی* (سینتکس، کتابخانه‌ها، ساختار فایل) باید با پایتون/FastAPI و Next.js/React تطبیق داده شود. برای مثال، منطق پیکربندی و یکپارچه‌سازی سرویس‌های خارجی که در `backend/services/telegram/config.js` و `backend/services/telegram/index.js` پروژه مرجع دیده می‌شود، باید به `backend/app/services/google_auth_service.py` با استفاده از کتابخانه‌های پایتون منتقل شود. خطای 500 در `api/users` باید در چارچوب FastAPI، بررسی کوئری‌های SQLAlchemy و سریال‌سازی Pydantic اشکال‌زدایی شود.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/core/config.py` (سطر -1) — نیاز به اضافه کردن متغیرهای محیطی برای Google OAuth (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI).
- `backend/app/crud/crud_user.py` (سطر -1) — نیاز به به‌روزرسانی توابع CRUD برای مدیریت کاربران احراز هویت شده از طریق گوگل (یافتن/ایجاد کاربر بر اساس google_id).
- `backend/app/models/user.py` (سطر -1) — مدل SQLAlchemy کاربر نیاز به فیلد جدیدی مانند `google_id` برای ذخیره شناسه منحصر به فرد گوگل دارد.
- `backend/app/schemas/user.py` (سطر -1) — شمای Pydantic کاربر باید به‌روزرسانی شود تا فیلد `google_id` را شامل شود.
- `frontend/src/components/layout/Navbar.tsx` (سطر -1) — برای پیاده‌سازی یک منوی ناوبری یکپارچه در سراسر برنامه، که به بهبود سازماندهی صفحات کمک می‌کند (در صورت وجود یا ایجاد).
- `frontend/src/app/dashboard/page.tsx` (سطر -1) — پس از ورود، کاربران به این صفحه هدایت می‌شوند و ممکن است نیاز به بهبود UI/UX بر اساس نقاط 3، 4 و 5 داشته باشد.

## 🌐 نقشهٔ وابستگی‌ها
پیاده‌سازی Google OAuth در بک‌اند نیازمند نصب کتابخانه‌های `google-auth-oauthlib` و `google-api-python-client` است. این ویژگی به شدت به `backend/app/core/config.py` برای مدیریت اعتبارنامه‌ها، `backend/app/core/security.py` برای تولید توکن‌های JWT و `backend/app/crud/crud_user.py` برای عملیات پایگاه داده کاربران وابسته خواهد بود. تغییرات فرانت‌اند مستقیماً بر `frontend/src/app/login/page.tsx` و سایر کامپوننت‌های UI در `frontend/src/components/` و منطق مسیریابی در `frontend/src/app/` تأثیر می‌گذارد. رفع خطای 500 در `api/users` شامل بررسی و اصلاح `backend/app/api/endpoints/users.py`، `backend/app/crud/crud_user.py` و احتمالاً مدل `backend/app/models/user.py` است. الگوی سرویس‌محور از پروژه مرجع `mahdighandi1989/language` (مانند `backend/services/telegram/index.js`) به ایجاد `backend/app/services/google_auth_service.py` کمک می‌کند.

## 🔍 Context و وضعیت فعلی
کاربر چندین مشکل حیاتی را شناسایی کرده و درخواست ویژگی‌های جدیدی برای سیستم عملیات بانکی دارد. این موارد شامل بهبود تجربه کاربری (UX) و رابط کاربری (UI) صفحه ورود، پیاده‌سازی قابلیت ورود با جیمیل، و رفع یک خطای بحرانی 500 در API کاربران است.

**مشکلات و درخواست‌های کاربر:**
1.  **صفحه ورود:** کاربر اظهار داشته که "صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره". این نشان‌دهنده نیاز به بازطراحی بصری، بهبود دسترسی به گزینه‌های دیگر (مانند ثبت‌نام یا فراموشی رمز عبور) و احتمالاً افزودن یک منوی ناوبری (یا هدایت به داشبورد با ناوبری کامل پس از ورود) است.
2.  **لاگین با جیمیل:** درخواست صریح برای "امکان لاگین از طریق جیمیل فراهم باشه" وجود دارد. این نیازمند ادغام Google OAuth 2.0 برای احراز هویت کاربران است.
3.  **صفحات ناقص/نامنظم:** "خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن". این مشکل به عدم تکمیل، عملکرد نادرست، یا سازماندهی ضعیف صفحات فرانت‌اند اشاره دارد که نیازمند بررسی و بازسازی ساختار صفحات و کامپوننت‌ها است.
4.  **ارتباط اجزا و صفحات:** "ارتباط اجزا و صفحات خیلی به هم ریخته س". این نشان‌دهنده مشکلات در معماری فرانت‌اند، مدیریت وضعیت (state management) و جریان داده بین کامپوننت‌ها و صفحات است.
5.  **آشفتگی ظاهری:** "از منظر ظاهری خیلی آشفته اس". این یک نقد کلی به طراحی بصری و نیاز به یکپارچگی و تمیزی بیشتر در UI با استفاده از Tailwind CSS است.
6.  **خطای سرور 500:** یک خطای بحرانی در کنسول مرورگر گزارش شده است: `Failed to load resource: the server responded with a status of 500 ()` برای `api/users/?page=1&page_size=100:1`. این خطا نشان‌دهنده یک مشکل در بک‌اند هنگام واکشی لیست کاربران است که می‌تواند مربوط به کوئری پایگاه داده، سریال‌سازی، یا مدیریت خطا باشد. این خطا در چندین درخواست متوالی برای `api/users/?page=1&page_size=100` مشاهده شده است.

**📚 پروژه‌های مرجع (Reference Projects):**
کاربر پروژه `mahdighandi1989/language` را به‌عنوان منبع الهام برای این تسک انتخاب کرده است، به‌ویژه با تمرکز بر "امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد". این پروژه دارای ساختار سرویس‌محور در بک‌اند خود است (مانند `backend/services/telegram/config.js` و `backend/services/telegram/index.js` که مدیریت یکپارچه‌سازی تلگرام را نشان می‌دهند). این الگو می‌تواند به‌عنوان الهام‌بخش برای ایجاد یک سرویس اختصاصی Google OAuth در پروژه فعلی استفاده شود. با این حال، باید توجه داشت که پروژه مرجع از JavaScript (احتمالاً Node.js/Express) استفاده می‌کند، در حالی که پروژه فعلی از Python/FastAPI برای بک‌اند و Next.js/React برای فرانت‌اند بهره می‌برد. بنابراین، تنها منطق و الگوهای معماری باید اقتباس شوند، نه سینتکس یا وابستگی‌های مستقیم.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحه ورود (`frontend/src/app/login/page.tsx`) دارای طراحی بصری بهبود یافته، بدون آشفتگی، و شامل یک دکمه "Login with Google" است.
- [ ] با کلیک بر روی دکمه "Login with Google"، کاربر به صفحه احراز هویت گوگل هدایت می‌شود.
- [ ] پس از احراز هویت موفقیت‌آمیز با گوگل، کاربر به برنامه بازگردانده شده و با دریافت یک توکن JWT معتبر، وارد سیستم می‌شود.
- [ ] endpoint `GET /api/users?page=1&page_size=100` وضعیت 200 OK را با لیستی از کاربران برمی‌گرداند و هیچ خطای 500 رخ نمی‌دهد.
- [ ] ساختار کلی ناوبری و صفحات فرانت‌اند بهبود یافته، صفحات به‌درستی دسته‌بندی شده و عملکردی هستند.
- [ ] الگوی معماری برای Google OAuth، الهام گرفته از لایه سرویس پروژه مرجع، با استفاده از قراردادهای Python/FastAPI پیاده‌سازی شده است (مثلاً `backend/app/services/google_auth_service.py` وجود دارد).
- [ ] الگوی برداشت‌شده از پروژهٔ مرجع با dependency و naming پروژهٔ فعلی سازگار است (نه copy-paste صرف).
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. این تسک شامل چندین بخش اصلی است:

1.  **بازطراحی UI/UX فرانت‌اند:**
    *   **صفحه ورود:** فایل `frontend/src/app/login/page.tsx` باید بازطراحی شود تا ظاهر جذاب‌تری داشته باشد، گزینه‌های دیگر (مانند ثبت‌نام یا بازیابی رمز عبور) به‌وضوح نمایش داده شوند و در صورت لزوم، یک کامپوننت ناوبری (یا لینک به داشبورد پس از ورود) اضافه شود. از Tailwind CSS برای استایل‌دهی استفاده شود.
    *   **ساختار صفحات و کامپوننت‌ها:** ساختار دایرکتوری `frontend/src/app/` و `frontend/src/components/` باید بازبینی و بازسازی شود تا صفحات ناقص تکمیل گردند، عملکرد صحیح داشته باشند و دسته‌بندی منطقی‌تری پیدا کنند. ارتباط بین اجزا و صفحات باید شفاف‌تر و سازمان‌یافته‌تر شود.

2.  **پیاده‌سازی لاگین با جیمیل (Google OAuth 2.0):**
    *   **بک‌اند (FastAPI):**
        *   یک سرویس جدید به نام `backend/app/services/google_auth_service.py` ایجاد شود. این سرویس مسئول مدیریت جریان Google OAuth (شروع احراز هویت، تبادل کد با توکن، و دریافت اطلاعات کاربر) خواهد بود. این الگو از ساختار سرویس‌محور پروژه مرجع `mahdighandi1989/language` الهام گرفته شده است، اما با استفاده از کتابخانه‌های Python مانند `google-auth-oauthlib` و `google-api-python-client` پیاده‌سازی می‌شود.
        *   دو endpoint جدید در `backend/app/api/endpoints/auth.py` اضافه شود: `/auth/google/login` برای شروع فرآیند OAuth (هدایت به گوگل) و `/auth/google/callback` برای دریافت پاسخ از گوگل و پردازش آن.
        *   مدل کاربر در `backend/app/models/user.py` و شمای Pydantic در `backend/app/schemas/user.py` به‌روزرسانی شوند تا فیلدی مانند `google_id` برای ذخیره شناسه گوگل کاربر اضافه شود.
        *   منطق احراز هویت و ایجاد/به‌روزرسانی کاربر در `backend/app/crud/crud_user.py` به‌روزرسانی شود تا کاربران گوگل را مدیریت کند و از `backend/app/core/security.py` برای تولید JWT استفاده کند.
        *   اطلاعات محرمانه Google OAuth (Client ID, Client Secret, Redirect URI) در `backend/app/core/config.py` پیکربندی شوند.
    *   **فرانت‌اند (Next.js):**
        *   یک دکمه "Login with Google" به `frontend/src/app/login/page.tsx` اضافه شود.
        *   منطق فرانت‌اند برای شروع جریان OAuth (هدایت به endpoint `/auth/google/login` بک‌اند) و مدیریت بازگشت از callback گوگل پیاده‌سازی شود.

3.  **رفع خطای 500 در API کاربران:**
    *   فایل `backend/app/api/endpoints/users.py` و تابع مربوط به endpoint `GET /users` بررسی شود.
    *   منطق واکشی کاربران در `backend/app/crud/crud_user.py` (تابع `get_multi` یا مشابه) و کوئری‌های SQLAlchemy مربوطه برای یافتن علت خطای 500 (احتمالاً در pagination، فیلترینگ، یا سریال‌سازی) بررسی و اصلاح شود.
    *   لاگ‌های سرور برای دریافت جزئیات بیشتر از traceback خطای 500 تحلیل شوند.

## 💡 نمونه‌های قبل/بعد
**افزودن دکمه لاگین گوگل به صفحه ورود**

_قبل:_
```
<div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <Button type="submit" className="w-full">Login</Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          {/* Other options / navigation links */}
        </CardFooter>
```

_بعد:_
```
<div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <Button type="submit" className="w-full">Login</Button>
          </form>
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-500">Or continue with</span>
            </div>
          </div>
          <Button data-testid="google-login-button" variant="outline" className="w-full flex items-center justify-center space-x-2">
            <img src="/google-icon.svg" alt="Google" className="h-5 w-5" />
            <span>Login with Google</span>
          </Button>
        </CardContent>
        <CardFooter className="flex justify-center">
          {/* Other options / navigation links */}
        </CardFooter>
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest backend/app/tests/`
- `npm run test -- frontend/src/app/login/page.test.tsx`

## ⚠️ ریسک‌ها و موارد احتیاط
1.  **پیکربندی Google OAuth**: تنظیم نادرست اعتبارنامه‌های Google API (Client ID, Client Secret, Redirect URI) در `backend/app/core/config.py` می‌تواند منجر به شکست احراز هویت شود.
2.  **ادغام/لینک کردن داده‌های کاربر**: اگر کاربران موجود نیاز به لینک کردن حساب‌های گوگل خود داشته باشند، یک استراتژی مهاجرت یا یک جریان UI برای لینک کردن مورد نیاز است که در این تسک پوشش داده نشده است. پیاده‌سازی `google_id` در `backend/app/models/user.py` بدون مدیریت صحیح برای کاربران موجود می‌تواند مشکل‌ساز باشد.
3.  **رگرسیون‌های فرانت‌اند**: بازطراحی گسترده UI/UX در `frontend/src/app/` و `frontend/src/components/` در صورت عدم مدیریت دقیق، به‌ویژه در مورد مدیریت وضعیت سراسری و ناوبری، ممکن است رگرسیون‌هایی را ایجاد کند.
4.  **ریشه خطای 500**: خطای 500 در `api/users` می‌تواند پیچیده باشد (مثلاً یک مشکل ظریف ORM، خرابی داده‌ها، یا یک استثنای مدیریت‌نشده در یک وابستگی). یک راه‌حل سریع ممکن است مشکل اساسی عمیق‌تری را پنهان کند.
5.  **خطر ترکیب وابستگی‌ها/نام‌گذاری/استک**: اگر توسعه‌دهنده الگوی احراز هویت از پروژه مرجع `mahdighandi1989/language` را بدون تطبیق با استک فعلی (Python/FastAPI به جای JavaScript/Node.js) پیاده‌سازی کند، ممکن است منجر به خطاهای سینتکسی، وابستگی‌های ناسازگار یا مشکلات معماری شود. هرگز import یا syntax کورکورانه از مرجع کپی نشود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: feature_request
- اولویت: high
- تخمین زمان: large

## Acceptance Criteria

1. صفحه ورود (`frontend/src/app/login/page.tsx`) دارای طراحی بصری بهبود یافته، بدون آشفتگی، و شامل یک دکمه "Login with Google" است. _(verify: ui_interaction)_
2. با کلیک بر روی دکمه "Login with Google"، کاربر به صفحه احراز هویت گوگل هدایت می‌شود. _(verify: ui_interaction)_
3. پس از احراز هویت موفقیت‌آمیز با گوگل، کاربر به برنامه بازگردانده شده و با دریافت یک توکن JWT معتبر، وارد سیستم می‌شود. _(verify: api_response)_
4. endpoint `GET /api/users?page=1&page_size=100` وضعیت 200 OK را با لیستی از کاربران برمی‌گرداند و هیچ خطای 500 رخ نمی‌دهد. _(verify: api_response)_
5. ساختار کلی ناوبری و صفحات فرانت‌اند بهبود یافته، صفحات به‌درستی دسته‌بندی شده و عملکردی هستند. _(verify: manual_only)_
6. الگوی معماری برای Google OAuth، الهام گرفته از لایه سرویس پروژه مرجع، با استفاده از قراردادهای Python/FastAPI پیاده‌سازی شده است (مثلاً `backend/app/services/google_auth_service.py` وجود دارد). _(verify: static)_
7. الگوی برداشت‌شده از پروژهٔ مرجع با dependency و naming پروژهٔ فعلی سازگار است (نه copy-paste صرف). _(verify: manual_only)_

## Task Steps

### Step 1: رفع خطای 500 در endpoint لیست کاربران (api/users)
**Status:** `partial` (50%)
**Scope:** این مرحله شامل دیباگ و رفع خطای سرور 500 روی endpoint `api/users/?page=1&page_size=100` است که در کنسول مرورگر چندین بار تکرار می‌شود. باید علت خطا (مثلاً مشکل در pagination با پارامتر `page_size`، خطای کوئری دیتابیس، یا handler ناقص controller) شناسایی و اصلاح شود. خارج از این مرحله: تغییرات UI یا طراحی صفحه. نکتهٔ حیاتی: این خطا foundation است — تا زمانی که endpoint کاربران کار نکند، صفحات وابسته به لیست کاربران بارگذاری نمی‌شوند، پس باید اول حل شود.
**Excerpt:**
```
در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
```

### Step 2: افزودن امکان لاگین از طریق Gmail (Google OAuth)
**Status:** `partial` (50%)
**Scope:** این مرحله شامل پیاده‌سازی احراز هویت از طریق حساب Gmail/Google است تا کاربران بتوانند با گزینهٔ «Login with Google» وارد شوند. باید جریان OAuth (redirect، callback، صدور session/token) در backend و دکمهٔ مربوطه در صفحهٔ ورود فراهم شود. می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز روی لاگین جیمیل و دادن دسترسی و میزان دسترسی به افراد) الهام گرفت اما منطق را در stack پروژهٔ فعلی پیاده کرد. خارج از این مرحله: مدیریت سطوح دسترسی پیشرفته. نکتهٔ حیاتی: امنیت callback و ذخیرهٔ امن credentials.
**Excerpt:**
```
2- باید امکان لاگین از طریق جیمیل فراهم باشه

🎯 نقطهٔ تمرکز کاربر: امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد
```

### Step 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر
**Status:** `partial` (50%)
**Scope:** این مرحله شامل بهبود ظاهر و کارکرد صفحهٔ ورود است: صفحهٔ ورود فعلی جذاب نیست، گزینه‌های دیگر در آن دیده نمی‌شوند و منوی ناوبری ندارد. باید طراحی صفحهٔ ورود بهبود یابد، گزینه‌های دیگر (مثل ورود با Gmail که در مرحلهٔ ۲ اضافه شد) به‌وضوح نمایش داده شوند و یک منوی ناوبری (nav bar) اضافه شود. خارج از این مرحله: رفع خطای backend و طراحی کلی سایر صفحات. نکتهٔ حیاتی: گزینه‌های ورود باید قابل کشف و دیده‌شدنی باشند.
**Excerpt:**
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره
```

### Step 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها
**Status:** `partial` (50%)
**Scope:** این مرحله شامل بررسی، تکمیل و اصلاح صفحاتی است که کاربر گفته ناقص هستند، کار نمی‌کنند یا درست دسته‌بندی نشده‌اند. باید هر صفحهٔ معیوب شناسایی، تکمیل و در ساختار/دسته‌بندی منطقی قرار گیرد (مثلاً گروه‌بندی منطقی صفحات در منو). خارج از این مرحله: رفع خطای endpoint کاربران و طراحی بصری کلی. نکتهٔ حیاتی: باید فهرستی از صفحات معیوب تهیه شود و هرکدام به وضعیت کارکردی برسد.
**Excerpt:**
```
3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
```

### Step 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)
**Status:** `partial` (50%)
**Scope:** این مرحله شامل ساماندهی ارتباط بین اجزا و صفحات است؛ کاربر گفته ارتباط اجزا و صفحات به‌هم‌ریخته است. باید جریان ناوبری بین صفحات، لینک‌ها و انتقال‌ها منسجم و قابل پیش‌بینی شود (information architecture منظم، breadcrumb یا منوی یکپارچه). خارج از این مرحله: استایل بصری صرف و رفع backend. نکتهٔ حیاتی: کاربر باید بتواند به‌صورت منطقی بین صفحات و اجزای مرتبط حرکت کند بدون سردرگمی.
**Excerpt:**
```
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
```

### Step 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)
**Status:** `partial` (50%)
**Scope:** این مرحله شامل رفع آشفتگی بصری کلی برنامه است؛ کاربر گفته از منظر ظاهری خیلی آشفته است. باید یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها، تایپوگرافی، کامپوننت‌های مشترک) در سراسر صفحات اعمال شود تا ظاهر یکدست و تمیز شود. خارج از این مرحله: منطق backend و کارکرد صفحات. نکتهٔ حیاتی: consistency در همهٔ صفحات و کامپوننت‌ها باید رعایت شود تا حس آشفتگی برطرف گردد.
**Excerpt:**
```
5- از منظر ظاهری خیلی آشفته اس
```

## Followup Prompt

## ⚠️ یادداشت مهم برای مدل اجراکننده — قبل از شروع بخوان

این پرامپت بر اساس یک **بررسی اولیهٔ خودکار** از repo ساخته شده — ممکن است
حاوی اشتباه، تشخیص نادرست، یا حذف موارد مهم باشد. به‌عنوان منبع نهایی به
آن استناد نکن.

📖 **خواندن کامل + اجرای مو-به-مو (بسیار مهم):**

این پرامپت — از این یادداشت تا انتها — یک سند واحد است که هر بخشش
حاوی الزام یا context منحصربه‌فرد است. خواندن سطحی یا skim کردن **ممنوع**
است.

- پرامپت را **سطر به سطر** بخوان، نه head/tail/فقط-بخش-اصلی.
- اگر بخشی به‌نظر طولانی یا تکراری آمد، **حتماً** بخوان — تفاوت‌های
  ریز ممکن است در آن جا اساسی باشند.
- هر جمله، URL، نام فایل، نام تابع، یا مقدار عددی که در پرامپت آمده،
  دقیقاً همان است که کاربر می‌خواهد — تغییرش نده، رندش نکن، خلاصه‌اش
  نکن.
- اگر پرامپت چندین درخواست/مرحله/زیرتسک دارد، **همه** را پیاده کن. حتی
  یکی را نه به‌عنوان "خارج از scope" حذف کن.

❌ ممنوعات صریح:
- خلاصه‌سازی متن کاربر در commit message یا response
- "این بخش اصلی نیست، رد می‌کنم"
- "کاربر احتمالاً منظورش این بود..." — منظورش همان است که نوشته
- "این URL/نام به نظر قدیمی است، آپدیتش کردم" — تغییر بدون درخواست ممنوع
- پیاده‌سازی فقط بخشی از پرامپت و تظاهر به کامل بودن
- "همه آیتم‌های لیست A را بررسی کردم، B و C مشابه بودند" — نه؛
  هرکدام را جداگانه

♻️ **احتمال پیاده‌سازی قبلی (مهم):**
- ممکن است **بخشی یا تمامِ** این درخواست قبلاً (به صورت کامل یا ناقص) در
  repo پیاده‌سازی شده باشد. پیش از شروع، با grep/search و خواندن فایل‌های
  مرتبط بررسی کن که چه چیزی **از قبل وجود دارد**.
- اگر یک قابلیت/فایل/تابع از قبل موجود است: آن را **دوباره نساز**؛ فقط
  موارد ناقص یا اشتباه را اصلاح/تکمیل کن.
- اگر همه چیز از قبل به‌درستی انجام شده: یک کامیت توضیحی (no-op) ثبت کن که
  چرا تغییری لازم نبود و دقیقاً کدام فایل‌ها این درخواست را پوشش می‌دهند.

🔍 **مسئولیت تو (مدل اجراکننده):**
- پیش از هر تغییر، خودت ساختار repo، فایل‌های ذکرشده، و وابستگی‌های آن‌ها را
  مستقل بررسی کن.
- اگر تشخیص دادی موقعیت ذکرشده در پرامپت اشتباه است یا فایل دیگری مناسب‌تر
  است، بر اساس قضاوت خودت عمل کن — این پرامپت نمی‌تواند بهانهٔ کار اشتباه
  باشد ("خودت گفتی" قابل قبول نیست).
- اگر معیارهای پذیرش (AC) مبهم/ناقص بودند، بهترین تفسیر را انتخاب کن و در
  commit message توضیح بده.

🔗 **وابستگی‌ها و همگام‌سازی (بسیار حیاتی — هرگز skip نکن):**

این بخش از همهٔ بخش‌های دیگرِ این یادداشت **مهم‌تر** است. اگر نقض شود،
نتیجهٔ کار ممکن است مشروع به‌نظر برسد ولی در عمل بخش‌های دیگر سیستم را عقب
بیندازد، broken reference تولید کند، یا منجر به data corruption شود.

پیش از و حین تغییر، تمام وابستگی‌ها را در **چهار جهت** به‌طور **کامل و
بدون هیچ خلاصه‌سازی** شناسایی و همگام کن:

**۱. وابستگی‌های upstream (این تسک به چه چیزهایی متکی است):**
- چه فایل‌ها، توابع، کلاس‌ها، API endpoint ها، schema های دیتابیس،
  env vars، یا config هایی که این تسک نیاز دارد؟
- آیا قرار است چیزی را ویرایش/حذف کنی که جای دیگر (signature، رفتار،
  return type، side effect) از آن انتظار خاصی می‌رود؟
- اگر dependency جدیدی اضافه می‌کنی، آیا با dependencyهای موجود تداخل
  دارد (نسخه، compat، lock file)؟

**۲. وابستگی‌های downstream (چه چیزهایی به این تسک متکی‌اند):**
- چه فایل‌ها، توابع، تست‌ها، migrations، docs، یا UI component هایی از
  کدی که داری ویرایش/اضافه/حذف می‌کنی **استفاده می‌کنند**؟
- با grep و reference search **همه‌ی** call sites، importها، subclassها،
  reference های مستقیم و غیرمستقیم را پیدا کن — نه فقط چند مورد اصلی.
- خصوصاً برای حذف یا rename: هیچ broken reference نباید باقی بماند.

**۳. وابستگی‌های cross-tier (بسیار مهم — هرگز فقط یک لایه را نبین):**

تسک شما ممکن است از backend، frontend، database، worker، یا هر tier
دیگری شروع شده باشد. ولی تغییرات تقریباً همیشه روی tier های دیگر هم
اثر می‌گذارند. **مستقل از اینکه تسک از کدام tier است**، این چک‌های دو
طرفه را همیشه انجام بده:

🔁 **اگر backend را تغییر دادی** (API، service، model، route):
  → frontend: کدام component/page/hook این endpoint یا data shape را
    مصرف می‌کند؟ type definition، state shape، error handling، loading
    state، form validation، URL routing همگی باید همگام شوند.
  → mobile/SDK/client library (اگر پروژه دارد): همان داستان frontend.
  → database: آیا migration لازم است؟ آیا rollback امن است؟
  → background workers: آیا event producer/consumer ها تحت تأثیرند؟
  → rate limit، auth، CORS، CSP: آیا رفتار جدید پشتیبانی می‌شود؟

🔁 **اگر frontend را تغییر دادی** (component، form، state، route):
  → backend: آیا endpoint جدید/تغییریافته لازم است؟ آیا data shape ای
    که ارسال می‌شود با schema سرور سازگار است؟
  → backend validation: آیا برای ورودی‌های جدید UI کافی است؟
  → permissions/RBAC: آیا feature جدید نیاز به role check جدید دارد؟
  → analytics/tracking: آیا event های جدید باید در backend log شوند؟
  → SEO/SSR: آیا تغییر route نیاز به sitemap/meta tags جدید دارد؟

🔁 **اگر database/migration را تغییر دادی**:
  → backend models (ORM، Pydantic، dataclasses) همگی به‌روزند؟
  → query های raw SQL یا ORM queries با schema جدید سازگارند؟
  → seed data، fixtures، factory functions تست‌ها به‌روزند؟
  → frontend: آیا data shape جدید در UI به‌درستی render می‌شود؟
  → rollback migration نوشته شده و امن است؟

🔁 **اگر API contract یا event schema را تغییر دادی** (REST، GraphQL،
   WebSocket، gRPC، Kafka، …):
  → OpenAPI/GraphQL schema/proto file آپدیت شد؟
  → همه‌ی consumer ها (client، subscriber، webhook، external API
    user) با version جدید سازگارند؟
  → backward compatibility حفظ شده یا migration path روشن است؟
  → versioning header/path اگر breaking change است؟

🔁 **اگر infrastructure یا config را تغییر دادی** (Dockerfile، CI، Render
   config، env، secrets):
  → README setup/installation section به‌روزه؟
  → `.env.example` با env vars جدید آپدیت شد؟
  → deploy script یا CI workflow هم تغییر کرد؟
  → docs/architecture یا diagram های infrastructure به‌روزند؟

⚠️ **هرگز فقط یک tier را تغییر نده و فرض کنی بقیه خودکار همگام می‌شوند.**
   حتی برای تغییرات به‌ظاهر «کوچک»، چک کن.

**۴. وابستگی‌های جانبی (artifacts که همیشه چک شوند):**

تغییرات کد همیشه روی این artifact ها اثر دارند. **همه را** بررسی و
به‌روز کن — مستندات اولویت **بالا** دارد چون فراموش‌شدنی‌ترین است.

  📝 **مستندات** (همیشه چک کن — حتی برای تغییر کوچک کد):
    - README.md (شرح، setup، نمونه‌های استفاده، badge ها)
    - CHANGELOG.md / RELEASE_NOTES.md
    - docs/ folder (architecture، API reference، user guides، runbooks)
    - inline docstrings/کامنت‌های توابع و کلاس‌های تغییریافته
    - OpenAPI/Swagger annotations، JSDoc/TSDoc
    - architecture diagrams (اگر component اضافه/حذف شد)
    - migration guides (اگر breaking change است)

  🌍 **مستندات کاربر**:
    - i18n files و translation keys
    - UI labels، tooltip ها، help text، error messages
    - in-app onboarding (اگر flow جدید است)

  🧪 **تست‌ها**:
    - unit tests (همه‌ی فایل‌های مرتبط — حتی اگر «بی‌ربط» به‌نظر می‌رسد)
    - integration tests
    - e2e tests (Playwright/Cypress/Selenium)
    - snapshot tests (اگر UI تغییر کرد)
    - contract tests (Pact یا مشابه)
    - performance benchmarks (اگر behavior performance-sensitive تغییر کرد)

  🧬 **type definitions و contracts**:
    - .d.ts files
    - Pydantic models، dataclasses
    - Protobuf/Avro/Thrift schemas
    - GraphQL schema definitions
    - JSON Schemas

  🏗 **infrastructure و config**:
    - Dockerfile، docker-compose.yml
    - Kubernetes manifests
    - Render/Vercel/Netlify config
    - GitHub Actions / GitLab CI workflows
    - environment templates (.env.example، .env.sample)
    - feature flags (LaunchDarkly، GrowthBook، config)

  📊 **monitoring و observability**:
    - logging keys (اگر اضافه/حذف شد، log parser ها هم به‌روز شوند)
    - metric names (Prometheus، Datadog)
    - tracing spans
    - alert rules و dashboards
    - error tracking (Sentry rules، groupings)

  🔐 **security**:
    - auth rules (rate limit، CORS، CSP، HSTS)
    - permissions/RBAC config
    - secrets rotation policies
    - audit log events (اگر action جدید اضافه شد)

  💾 **caches و serialization**:
    - cache keys و TTL (اگر data shape یا lifecycle تغییر کرد)
    - serializer formats (Redis، session storage)
    - browser storage (localStorage، IndexedDB schemas)

**قانون مطلق همگام‌سازی:**
- هر چیزی که در (۱)، (۲)، (۳)، یا (۴) شناسایی شد، در **همان workflow
  این تسک** همگام و به‌روز شود. هرگز برای بعد رها نکن.
- اگر یک فایل/تست/docs نسبت به تغییر شما عقب بماند، در بهترین حالت bug،
  در بدترین حالت مشکل امنیتی یا data corruption تولید می‌کند.
- تغییرات همگام‌سازی می‌توانند در commit جداگانه باشند (در همان task)،
  ولی نباید skip شوند یا به «refactor آینده» سپرده شوند.

**هرگز این جمله‌ها قابل قبول نیست:**
- ❌ «بعداً پیداش می‌کنم»
- ❌ «احتمالاً جای دیگه‌ای استفاده نمی‌شه»
- ❌ «این یه refactor جداگانه‌ست — out of scope»
- ❌ «فقط فایل‌های اصلی رو بررسی کردم»
- ❌ «حدس می‌زنم چیزی بهش وابسته نیست»
- ❌ «دامنه‌ی وابستگی‌ها رو خلاصه کردم» — هرگز خلاصه نکن
- ❌ «این task فقط backend است؛ frontend مشکل خودش» — هرگز
- ❌ «این task فقط frontend است؛ backend از قبل کار می‌کند» — هرگز ثابت نکرده
- ❌ «مستندات بعداً به‌روز می‌شن» — همیشه same-task همگام شوند
- ❌ «testها رو نگاه نکردم چون فقط یه تغییر کوچیک بود»

**در commit message یا PR description**، دامنهٔ وابستگی‌های شناسایی‌شده و
همگام‌شده را به‌طور explicit و **per-tier** بنویس. مثال:
```
Dependencies synced:
- upstream: User model schema, auth middleware
- downstream: 3 API endpoints, 5 frontend components, 12 tests
- cross-tier (backend → frontend): UserProfile.tsx, useUser.ts hook,
  api-types.ts (TS definitions)
- cross-tier (backend → infra): .env.example added NEW_AUTH_SCOPES
- side artifacts: OpenAPI spec, README API section, i18n keys for
  new errors, Sentry alert rule for new error code
```
اگر هیچ وابستگی پیدا نکردی در هر کدام از چهار جهت، صریحاً بنویس:
«بررسی شد — هیچ وابستگی upstream / downstream / cross-tier (backend↔
frontend↔db↔infra) / side شناسایی نشد» تا مشخص باشد بررسی **انجام شده**
نه اینکه فراموش شده.

📋 **مدیریت TO-DO برای اقدامات دستی کاربر (همیشه چک کن):**

⚠️ **هشدار بحرانی — قاعدهٔ ضد-فرار:** TO-DO فقط برای کارهایی است که
**واقعاً غیرممکن** برای agent است (نیاز به انسان مطلق)، نه برای کارهایی
که «بزرگ‌اند»، «وقت می‌برند»، یا «نیازمند fixture/setup» هستند. اگر یک
agent در یک سشن بیش از **۲۰٪ از تسک‌ها** را با TO-DO ببندد، یعنی از کار
فرار می‌کند — این الگو در سشن‌های قبلی **مشاهده** شده و الان ممنوع است.

✅ **فقط برای این موارد TO-DO بساز** (لیست بسته — هرچه خارج این لیست
ممنوع است):

  ۱. **Credential/secret که فقط کاربر دارد**:
     - تنظیم API key واقعی در پنل ادمین خارجی (Render، AWS، Stripe، …)
     - تأیید OAuth client روی console آن سرویس
     - paste کردن webhook secret که فقط بعد از ساخت در dashboard ظاهر می‌شود

  ۲. **Account/billing روی سرویس خارجی که کاربر باید عضو شود**:
     - ساخت account جدید روی Stripe/SendGrid/Twilio/Google Cloud
     - تأیید verification شماره یا ID
     - فعال‌سازی subscription پولی

  ۳. **داده/asset خصوصی که فقط کاربر دارد**:
     - آپلود لوگو/تصویر/فونت برند
     - paste کردن داده‌ای که در محل کار کاربر است
     - import داده‌ای که فقط روی device کاربر است

  ۴. **تصمیم سلیقه‌ای/حقوقی/کسب‌وکار**:
     - انتخاب رنگ‌بندی نهایی یا تم
     - متن دقیق Terms of Service / Privacy Policy
     - تعرفهٔ قیمت‌گذاری
     - نام نهایی برند یا دامنه

⛔ **هرگز TO-DO نکن برای** (لیست سیاه — هر چیزی که در این لیست است
**قابل اجرا** توسط agent است، حتی اگر بزرگ یا چندبخشی باشد):

  ❌ UI component / page / dashboard (هر فریم‌ورک: React, Vue, Angular,
     Svelte، حتی اگر معماری بزرگ دارد) — می‌توانی stub اولیه + state
     management + layout + استایل بسازی
  ❌ "نیازمند Google Drive / Stripe / Twilio API" — می‌توانی **client
     stub** با abstraction layer بسازی که با env var واقعی plug-in شود؛
     کد integration یعنی پیاده‌سازی، نه TO-DO
  ❌ "feature بزرگ، چند روز کار می‌برد" — اندازه دلیل defer نیست؛ کوچک
     شروع کن، iterate کن، در همین سشن کامل کن
  ❌ Celery / background worker / scheduler — یک task ساده + register
     می‌توانی بسازی
  ❌ Migration / model / schema — حتی اگر فیلد جدید نیاز دارد، اضافه کن
  ❌ REST endpoint / GraphQL resolver / WebSocket route — هرگز TO-DO
  ❌ test (unit/integration/e2e) — همیشه قابل نوشتن
  ❌ Documentation / README / API docs — همیشه قابل نوشتن
  ❌ Config file / .env.example / Dockerfile / CI workflow — همیشه قابل
     نوشتن
  ❌ "می‌توانستی .tsx ولی repo .jsx است" — از .jsx استفاده کن، TO-DO نکن
  ❌ "نیازمند فیلد X در مدل دیگر" — اضافه کن فیلد را، TO-DO نکن
  ❌ "تصمیم admin-vs-user-scoped" — پرامپت اولیه scope را معلوم کرده،
     یا با محتاطانه‌ترین تفسیر پیش برو
  ❌ "credential در production هنوز ست نیست" — این TO-DO ساده برای
     تنظیم env var است (مورد ۱ بالا)، نه دلیل برای defer کردن کد
  ❌ "نیازمند verification از کاربر" — اگر اقدام واقعی غیرممکن نیست،
     پیش برو
  ❌ هر چیزی که در یک کامنت `# TODO` معمولی نوشته می‌شد — این فایل
     TO-DO نیست، کامنت inline است

🔬 **قاعدهٔ «حداقل تلاش» قبل از TO-DO**: قبل از TO-DO کردن یک AC، **اثبات
کن** که قابل انجام نیست:

  ۱. آیا می‌توانم یک stub/placeholder بسازم که با env واقعی plug-in شود؟
     → اگر بله، بساز و TO-DO نکن
  ۲. آیا می‌توانم برای این بخش یک test (حتی mock-based) بنویسم؟
     → اگر بله، بنویس و TO-DO نکن
  ۳. آیا می‌توانم abstraction/interface را تعریف کنم، حتی اگر backend
     واقعی نیست؟ → اگر بله، تعریف کن و TO-DO نکن
  ۴. آیا فقط یک حالت سلیقه‌ای/decision کاربر در میان است؟
     → فقط آن یک decision را TO-DO کن، نه کل feature را

اگر یکی از این چهار راه‌حل ممکن بود ولی به TO-DO رفتی، **اعتبار شما از
بین می‌رود**.

📊 **آستانهٔ TO-DO per session**: در یک حلقهٔ اجرای N تسک، اگر بیشتر از
**۲۰٪** تسک‌ها فایل TO-DO ساختی، خودت در گزارش پایانی صریحاً اعلام کن:

  "⚠️ نسبت TO-DO من {K}/{N} = {%} است که از آستانهٔ ۲۰٪ بالاتر است.
   احتمالاً برخی از این TO-DO ها قابل اجرا بودند ولی من فرار کردم.
   لیست TO-DO ها را کاربر باید بازبینی کند که آیا واقعاً Manual-required
   بودند یا agent ضعیف کار کرده."

**یادآوری همیشگی:** اگر در آینده قابلیت‌های شما گسترش پیدا کرد و توانستید
یکی از موارد لیست سفید را خودکار انجام دهید (مثلاً managed credential
injection، یا integration پولی automate شود)، انجام دهید و TO-DO نسازید.
لیست سفید بسته است ولی **بسته از پایین** (می‌تواند کوچک‌تر شود اگر
قابلیت‌ها رشد کنند، ولی هرگز بزرگ‌تر نشود برای فرار).

**اگر هیچ بخش Manual-required نبود (تمام تسک Auto-capable است)**:
  → فایل TO-DO **نساز**. فولدر TO-DO/ باید پاک و معنادار بماند.
  → اگر برای این task از قبل `TO-DO/todo-task-{task_id_first_8}.md` بود
     (یعنی در run قبلی نیاز به دخالت کاربر بود ولی الان نه): فایل قدیمی
     را پاک کن و entry را از `TO-DO/_index.json` حذف کن.

**اگر بخش Manual-required دارد** (همه‌جانبه یا hybrid):
  1. فولدر TO-DO/ را در ریشه ریپو ایجاد کن اگر نیست
  2. فایل `TO-DO/todo-task-{task_id_first_8}.md` بساز با front-matter
     شامل: task_id, task_title, execution_priority, created_at,
     updated_at, status: "pending"
     و در بدنه: «چرا این فایل ساخته شد»، «وضعیت بخش‌های خودکار»
     (commit ها reference)، «کارهایی که باید انجام دهی» با اولویت
     بالا/متوسط/پایین به ترتیب، «وقتی این کارها را تمام کردی»
  3. `TO-DO/_index.json` را با **merge** آپدیت کن (نه overwrite):
     - فایل موجود را بخوان
     - entry های orphan (فایلشان پاک شده) را حذف کن
     - entry این task را اضافه/replace کن
     - بر اساس execution_priority صعودی مرتب کن
     - ساختار: `{"version":1, "generated_at": ISO, "total": N, "items": [...]}`
  4. این تغییرات TO-DO را در **همان commit کد** شامل کن (نه commit جداگانه)

⛔ **ممنوعات مطلق TO-DO**:
  ❌ ساختن TO-DO برای کاری که می‌توانستی خودت انجام دهی (شلوغی فولدر)
  ❌ overwrite کردن `TO-DO/_index.json` بدون merge (data loss)
  ❌ نگه‌داشتن entry هایی که فایل‌شان پاک شده (broken reference)
  ❌ فراموش کردن نوشتن «خروجی مورد انتظار» در هر آیتم TO-DO

این بخش الزامی است. حتی اگر فکر می‌کنی "این تسک کاملاً auto است و نیازی
به TO-DO نیست"، صریحاً در commit message یا report بنویس:
"بررسی شد — این تسک هیچ بخش Manual-required ندارد، TO-DO ساخته نشد."

📦 **اگر کار طولانی است:**
- **خلاصه‌اش نکن.** همه را به‌طور کامل انجام بده.
- اگر یک کامیت گنجایش ندارد، در **چندین کامیت متوالی** انجام بده — ولی
  هیچ بخشی را skip نکن.
- ترتیب کامیت‌ها را منطقی نگه‌دار (foundation → core → integration → tests).
- در آخر یک checklist از همه‌ی کامیت‌ها در PR description بنویس.

🔁 **Commit + Push فوری per-task (بسیار مهم برای جریان کار صحیح):**

پس از اتمام پیاده‌سازی این تسک، **بلافاصله** commit کن و **همان موقع**
به default branch (main/master) push کن. سپس به تسک بعدی برو.

✓ چرا این قانون حیاتی است:
  - تسک‌های بعدی ممکن است به فایل‌ها/تغییراتی که این تسک ایجاد کرده
    نیاز داشته باشند. اگر push نکنی، `git pull` بعدی آن‌ها را نمی‌بیند.
  - جمع‌کردن تغییرات چند تسک منجر به conflict های بزرگ می‌شود.
  - اگر در میانه fail کنی، task های push شده ضایع نمی‌شوند.

⛔ ممنوع: "همه task ها را تمام می‌کنم بعد یک‌جا push می‌زنم"
⛔ ممنوع: branch جدا برای task — مستقیم به default branch
⛔ ممنوع: task بعدی بدون push کامل task قبلی

---


## 🎯 هدف (خلاصه ساختاریافته)
ادامه (دور 3): رفع خطای 500 و بازطراحی UI

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:191` — `include_router(users.router)`
- `backend/app/routers/users.py` — `list users handler (GET /)`
- `backend/app/main.py:122-155` — `unhandled_exception_handler_500`
- `backend/app/schemas/user.py` — `User / UserList schema`
- `backend/app/routers/google_auth.py`
- `backend/static/_next/static/chunks/app/login/page-24881fa424a45d34.js`
- `backend/static/_next/static/chunks/app/layout-d38f6f11bf5727d1.js`
- `backend/tests/integration/test_users.py`
- `backend/app/db_init.py` — از evidence verifier در دور 2

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🔍 Context و وضعیت فعلی
این پرامپت برای **دور 3** ادامهٔ کار است. verifier در دور قبلی نشان داد کار به‌طور کامل انجام نشده.

📋 وضعیت چک‌لیست مراحل (0/6 انجام‌شده) — پیشرفت کلی: **50%**:
  - [~] **مرحله 1: رفع خطای 500 در endpoint لیست کاربران (api/users)** — باقی‌مانده: خطای 500 در endpoint `/api/users` در محیط deployed همچنان وجود دارد و صفحه مدیریت کاربران (UI) قابل دسترسی نیست.
  - [~] **مرحله 2: افزودن امکان لاگین از طریق Gmail (Google OAuth)** — باقی‌مانده: دکمه ورود با Google در صفحه لاگین دیده نمی‌شود و جریان OAuth در UI قابل تأیید نیست.
  - [~] **مرحله 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر** — باقی‌مانده: بازطراحی صفحه ورود و منوی ناوبری از نظر بصری تأیید نشده و عناصر UI مربوطه دیده نمی‌شوند.
  - [~] **مرحله 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها** — باقی‌مانده: تکمیل و دسته‌بندی صفحات ناقص به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست.
  - [~] **مرحله 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)** — باقی‌مانده: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture) از نظر بصری تأیید نشده است.
  - [~] **مرحله 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)** — باقی‌مانده: یکدست‌سازی و بهبود ظاهر کلی برنامه به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست.

🎯 **در این دور، فقط روی مراحل بالا که `[ ]` یا `[~]` دارند تمرکز کن.** مراحلی که `[x]` خورده‌اند قبلاً تأیید شده‌اند — نگران آن‌ها نباش، ولی regression نکن.

✅ بخش‌هایی که در دور قبل انجام شد:
  - کد رفع خطای 500 در endpoint `/api/users` (مدیریت NULL و serialization) پیاده‌سازی شده است.
  - کد مربوط به افزودن امکان لاگین با Google OAuth در backend پیاده‌سازی شده است.
  - کد بازطراحی صفحه ورود و افزودن منوی ناوبری در frontend پیاده‌سازی شده است.
  - کد برای تکمیل و دسته‌بندی صفحات ناقص و بهبود IA در frontend پیاده‌سازی شده است.
  - کد برای یکدست‌سازی ظاهر کلی برنامه در frontend پیاده‌سازی شده است.
  - لینتر بدون warning عبور می‌کند (بر اساس code analysis).

⏳ بخش‌هایی که هنوز باقی مانده (تمرکز روی این‌ها):
  - خطای 500 در endpoint `/api/users/?page=1&page_size=100` همچنان در محیط deployed وجود دارد.
  - صفحه مدیریت کاربران (UI) به دلیل خطای 404 قابل دسترسی نیست.
  - بازطراحی صفحه ورود و منوی ناوبری از نظر بصری تأیید نشده و عناصر UI مربوطه دیده نمی‌شوند.
  - دکمه ورود با Google در صفحه لاگین دیده نمی‌شود و جریان OAuth در UI قابل تأیید نیست.
  - تست‌های backend رگرسیون برای endpoint کاربران fail می‌شوند (pytest internal error).
  - تست‌های پروژه (npm run test / pytest) fail می‌شوند.
  - type-check موفق نیست (هیچ شواهدی از اجرای موفقیت‌آمیز type-check یافت نشد).

📝 خلاصهٔ verifier:
```json
{
  "status": "partial",
  "done_parts": [
    "کد رفع خطای 500 در endpoint `/api/users` (مدیریت NULL و serialization) پیاده‌سازی شده است.",
    "کد مربوط به افزودن امکان لاگین با Google OAuth در backend پیاده‌سازی شده است.",
    "کد بازطراحی صفحه ورود و افزودن منوی ناوبری در frontend پیاده‌سازی شده است.",
    "کد برای تکمیل و دسته‌بندی صفحات ناقص و بهبود IA در frontend پیاده‌سازی شده است.",
    "کد برای یکدست‌سازی ظاهر کلی برنامه در frontend پیاده‌سازی شده است.",
    "لینتر بدون warning

🪜 اقدامات بعدی پیشنهادی verifier:
  - بررسی علت خطای 500 در endpoint `/api/users` در محیط deployed.
  - دیباگ و رفع خطای 404 برای صفحه `/users-management`.
  - بررسی علت عدم نمایش عناصر UI بازطراحی شده در صفحات ورود و ناوبری.
  - بررسی علت خطای `pytest internal error` و اطمینان از اجرای موفقیت‌آمیز تست‌ها.
  - اطمینان از اجرای موفقیت‌آمیز type-check.
  - بررسی وضعیت deploy و اطمینان از اعمال صحیح تغییرات کد در محیط Render.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] [مرحله 1 — رفع خطای 500 در endpoint لیست کاربران (api/users)] باقی‌مانده: خطای 500 در endpoint `/api/users` در محیط deployed همچنان وجود دارد و صفحه مدیریت کاربران (UI) قابل دسترسی نیست.
- [ ] [مرحله 2 — افزودن امکان لاگین از طریق Gmail (Google OAuth)] باقی‌مانده: دکمه ورود با Google در صفحه لاگین دیده نمی‌شود و جریان OAuth در UI قابل تأیید نیست.
- [ ] [مرحله 3 — بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر] باقی‌مانده: بازطراحی صفحه ورود و منوی ناوبری از نظر بصری تأیید نشده و عناصر UI مربوطه دیده نمی‌شوند.
- [ ] [مرحله 4 — تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها] باقی‌مانده: تکمیل و دسته‌بندی صفحات ناقص به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست.
- [ ] [مرحله 5 — بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)] باقی‌مانده: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture) از نظر بصری تأیید نشده است.
- [ ] [مرحله 6 — یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)] باقی‌مانده: یکدست‌سازی و بهبود ظاهر کلی برنامه به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست.
- [ ] خطای 500 در endpoint `/api/users/?page=1&page_size=100` همچنان در محیط deployed وجود دارد.
- [ ] صفحه مدیریت کاربران (UI) به دلیل خطای 404 قابل دسترسی نیست.
- [ ] بازطراحی صفحه ورود و منوی ناوبری از نظر بصری تأیید نشده و عناصر UI مربوطه دیده نمی‌شوند.
- [ ] دکمه ورود با Google در صفحه لاگین دیده نمی‌شود و جریان OAuth در UI قابل تأیید نیست.
- [ ] تست‌های backend رگرسیون برای endpoint کاربران fail می‌شوند (pytest internal error).
- [ ] تست‌های پروژه (npm run test / pytest) fail می‌شوند.
- [ ] type-check موفق نیست (هیچ شواهدی از اجرای موفقیت‌آمیز type-check یافت نشد).
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. پیاده‌سازی AC های باقی‌مانده با حفظ کارهای انجام‌شدهٔ دور قبل.

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd backend && pytest tests/integration/test_users.py -v`
- `cd backend && pytest --cov=app --cov-report=term-missing`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
موارد زیر در دور قبل ناقص ماندند — مراقب رگرشن باش:
  - بررسی علت خطای 500 در endpoint `/api/users` در محیط deployed.
  - دیباگ و رفع خطای 404 برای صفحه `/users-management`.
  - بررسی علت عدم نمایش عناصر UI بازطراحی شده در صفحات ورود و ناوبری.
  - بررسی علت خطای `pytest internal error` و اطمینان از اجرای موفقیت‌آمیز تست‌ها.
  - اطمینان از اجرای موفقیت‌آمیز type-check.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: idea
- اولویت: medium
- تخمین زمان: medium

## 📋 چک‌لیست مراحل (دور 3)

این مراحل از پرامپت اصلی نگه داشته شده‌اند تا verifier در هر دور وضعیت هر مرحله را به‌روز کند. `[x]` = انجام‌شده، `[~]` = ناقص، `[ ]` = هنوز انجام نشده.

- [~] **مرحله 1: رفع خطای 500 در endpoint لیست کاربران (api/users)** — این مرحله شامل دیباگ و رفع خطای سرور 500 روی endpoint `api/users/?page=1&page_size=100` است که در کنسول مرورگر چندین بار تکرار می‌شود. باید علت خطا (مثلاً مشکل در pagination با پارامتر `page_size`، خطای کوئری دیتابیس، یا handler ناقص controller) شناسایی و اصلاح شود. خارج از این مرحله: تغییرات UI یا 
      _باقی‌مانده: خطای 500 در endpoint `/api/users` در محیط deployed همچنان وجود دارد و صفحه مدیریت کاربران (UI) قابل دسترسی نیست._
- [~] **مرحله 2: افزودن امکان لاگین از طریق Gmail (Google OAuth)** — این مرحله شامل پیاده‌سازی احراز هویت از طریق حساب Gmail/Google است تا کاربران بتوانند با گزینهٔ «Login with Google» وارد شوند. باید جریان OAuth (redirect، callback، صدور session/token) در backend و دکمهٔ مربوطه در صفحهٔ ورود فراهم شود. می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز ر
      _باقی‌مانده: دکمه ورود با Google در صفحه لاگین دیده نمی‌شود و جریان OAuth در UI قابل تأیید نیست._
- [~] **مرحله 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر** — این مرحله شامل بهبود ظاهر و کارکرد صفحهٔ ورود است: صفحهٔ ورود فعلی جذاب نیست، گزینه‌های دیگر در آن دیده نمی‌شوند و منوی ناوبری ندارد. باید طراحی صفحهٔ ورود بهبود یابد، گزینه‌های دیگر (مثل ورود با Gmail که در مرحلهٔ ۲ اضافه شد) به‌وضوح نمایش داده شوند و یک منوی ناوبری (nav bar) اضافه شود. خارج از این
      _باقی‌مانده: بازطراحی صفحه ورود و منوی ناوبری از نظر بصری تأیید نشده و عناصر UI مربوطه دیده نمی‌شوند._
- [~] **مرحله 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها** — این مرحله شامل بررسی، تکمیل و اصلاح صفحاتی است که کاربر گفته ناقص هستند، کار نمی‌کنند یا درست دسته‌بندی نشده‌اند. باید هر صفحهٔ معیوب شناسایی، تکمیل و در ساختار/دسته‌بندی منطقی قرار گیرد (مثلاً گروه‌بندی منطقی صفحات در منو). خارج از این مرحله: رفع خطای endpoint کاربران و طراحی بصری کلی. نکتهٔ حیاتی:
      _باقی‌مانده: تکمیل و دسته‌بندی صفحات ناقص به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست._
- [~] **مرحله 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)** — این مرحله شامل ساماندهی ارتباط بین اجزا و صفحات است؛ کاربر گفته ارتباط اجزا و صفحات به‌هم‌ریخته است. باید جریان ناوبری بین صفحات، لینک‌ها و انتقال‌ها منسجم و قابل پیش‌بینی شود (information architecture منظم، breadcrumb یا منوی یکپارچه). خارج از این مرحله: استایل بصری صرف و رفع backend. نکتهٔ حیاتی: 
      _باقی‌مانده: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture) از نظر بصری تأیید نشده است._
- [~] **مرحله 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)** — این مرحله شامل رفع آشفتگی بصری کلی برنامه است؛ کاربر گفته از منظر ظاهری خیلی آشفته است. باید یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها، تایپوگرافی، کامپوننت‌های مشترک) در سراسر صفحات اعمال شود تا ظاهر یکدست و تمیز شود. خارج از این مرحله: منطق backend و کارکرد صفحات. نکتهٔ حیاتی: consistency در همهٔ صفح
      _باقی‌مانده: یکدست‌سازی و بهبود ظاهر کلی برنامه به دلیل عدم بارگذاری صحیح UI قابل تأیید نیست._
