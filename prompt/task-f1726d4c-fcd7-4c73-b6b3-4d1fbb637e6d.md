---
task_id: f1726d4c-fcd7-4c73-b6b3-4d1fbb637e6d
title: '``` (6 مرحله)'
type: idea
priority: medium
execution_priority: 3050
status: pending
external_status: done
verification_status: applied_externally_pending_verify
watched_id: b2586b68-22f8-4e8e-a7a8-9b513c5f70fe
project: mahdighandi1989/ALLIN1
created_at: '2026-06-06T07:33:27.680004+00:00'
updated_at: '2026-06-06T07:52:11.707514+00:00'
target_files:
- backend/app/main.py
- backend/app/routers/users.py
- backend/app/schemas/user.py
---

# ``` (6 مرحله)

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


---

## 📥 درخواست خام کاربر (verbatim — همان متنی که کاربر نوشت)
_(همهٔ URL ها، آدرس‌ها، نام‌ها، و کلمات کلیدی در این متن دست‌نخورده هستند.)_

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
```

## 📋 چک‌لیست مراحل (6 مرحله)

این تسک به مراحل کوچک‌تر تقسیم شده. **در هر verify خودکار، وضعیت هر مرحله به‌صورت `[ ]` (انجام نشده)، `[~]` (ناقص)، یا `[x]` (انجام شده) به‌روز می‌شود.**
وقتی تمام مراحل `[x]` شدند، تسک به‌طور خودکار به «انجام شده» منتقل می‌شود.

- [ ] **مرحله 1: رفع خطای 500 در endpoint لیست کاربران (api/users)** — این مرحله شامل دیباگ و رفع خطای سرور 500 روی endpoint `api/users/?page=1&page_size=100` است که در کنسول مرورگر چندین بار تکرار می‌شود. باید علت خطا (مثلاً مشکل در pagination با پارامتر `page_size`، خطای کوئری دیتابیس، یا handler ناقص controller) شناسایی و اصلاح شود. خارج از این مرحله: تغییرات UI یا 
- [ ] **مرحله 2: افزودن امکان لاگین از طریق Gmail (Google OAuth)** — این مرحله شامل پیاده‌سازی احراز هویت از طریق حساب Gmail/Google است تا کاربران بتوانند با گزینهٔ «Login with Google» وارد شوند. باید جریان OAuth (redirect، callback، صدور session/token) در backend و دکمهٔ مربوطه در صفحهٔ ورود فراهم شود. می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز ر
- [ ] **مرحله 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر** — این مرحله شامل بهبود ظاهر و کارکرد صفحهٔ ورود است: صفحهٔ ورود فعلی جذاب نیست، گزینه‌های دیگر در آن دیده نمی‌شوند و منوی ناوبری ندارد. باید طراحی صفحهٔ ورود بهبود یابد، گزینه‌های دیگر (مثل ورود با Gmail که در مرحلهٔ ۲ اضافه شد) به‌وضوح نمایش داده شوند و یک منوی ناوبری (nav bar) اضافه شود. خارج از این
- [ ] **مرحله 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها** — این مرحله شامل بررسی، تکمیل و اصلاح صفحاتی است که کاربر گفته ناقص هستند، کار نمی‌کنند یا درست دسته‌بندی نشده‌اند. باید هر صفحهٔ معیوب شناسایی، تکمیل و در ساختار/دسته‌بندی منطقی قرار گیرد (مثلاً گروه‌بندی منطقی صفحات در منو). خارج از این مرحله: رفع خطای endpoint کاربران و طراحی بصری کلی. نکتهٔ حیاتی:
- [ ] **مرحله 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)** — این مرحله شامل ساماندهی ارتباط بین اجزا و صفحات است؛ کاربر گفته ارتباط اجزا و صفحات به‌هم‌ریخته است. باید جریان ناوبری بین صفحات، لینک‌ها و انتقال‌ها منسجم و قابل پیش‌بینی شود (information architecture منظم، breadcrumb یا منوی یکپارچه). خارج از این مرحله: استایل بصری صرف و رفع backend. نکتهٔ حیاتی: 
- [ ] **مرحله 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)** — این مرحله شامل رفع آشفتگی بصری کلی برنامه است؛ کاربر گفته از منظر ظاهری خیلی آشفته است. باید یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها، تایپوگرافی، کامپوننت‌های مشترک) در سراسر صفحات اعمال شود تا ظاهر یکدست و تمیز شود. خارج از این مرحله: منطق backend و کارکرد صفحات. نکتهٔ حیاتی: consistency در همهٔ صفح

---

# 🔹 مرحله 1: رفع خطای 500 در endpoint لیست کاربران (api/users)

**Scope:** این مرحله شامل دیباگ و رفع خطای سرور 500 روی endpoint `api/users/?page=1&page_size=100` است که در کنسول مرورگر چندین بار تکرار می‌شود. باید علت خطا (مثلاً مشکل در pagination با پارامتر `page_size`، خطای کوئری دیتابیس، یا handler ناقص controller) شناسایی و اصلاح شود. خارج از این مرحله: تغییرات UI یا طراحی صفحه. نکتهٔ حیاتی: این خطا foundation است — تا زمانی که endpoint کاربران کار نکند، صفحات وابسته به لیست کاربران بارگذاری نمی‌شوند، پس باید اول حل شود.
**Key terms:** api/users/, page_size, page, backend/controllers/index.js, backend/controllers/index.js

**بخش مربوط از متن کاربر:**
```
در کنسول نیز خطای ارتباط با سرور مشاهده میشه:
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
```

## 🎯 هدف (خلاصه ساختاریافته)
رفع خطای 500 در endpoint لیست کاربران GET /api/users

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:191` — `include_router(users.router)` — ثبت روتر کاربران با prefix /api/users — controller واقعی این پروژه (نه backend/controllers/index.js که کاربر اشتباهاً ذکر کرده). نقطهٔ ورود endpoint مشکل‌دار.
  ```python
  app.include_router(users.router, prefix="/api/users", tags=["users"])
  ```
- `backend/app/routers/users.py` — `list users handler (GET /)` — این فایل deep-read نشده — مجری باید مسیر را خود تأیید کند. handler واقعی GET فهرست کاربران با پارامترهای page/page_size اینجاست؛ منشأ اصلی خطای 500 (کوئری pagination یا serialization) باید همین‌جا دیباگ شود.
- `backend/app/main.py:122-155` — `unhandled_exception_handler_500` — این handler هر exception را به پاسخ 500 با error_id تبدیل می‌کند و جزئیات را پنهان می‌کند. برای دیباگ باید traceback را با همین error_id از لاگ سرور خواند.
  ```python
  error_id = uuid.uuid4().hex
      UNHANDLED_ERRORS.inc()
      # stdlib logger (logger.exception attaches the traceback)
      logger.exception(
          "Unhandled exception error_id=%s on %s %s",
          error_id,
          request.method,
          request.url.path,
      )
  ```
- `backend/app/schemas/user.py` — `User / UserList schema` — این فایل deep-read نشده — مجری باید مسیر را خود تأیید کند. اگر علت 500 خطای serialization باشد (فیلد nullable/enum mismatch بین مدل و schema)، اصلاح اینجا لازم است.

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Backend: FastAPI 0.104.1 + SQLAlchemy 2.0.23 (async با asyncpg) + Pydantic 2.5. Frontend: Next.js 14 + Axios. توجه: کاربر به `backend/controllers/index.js` اشاره کرده که با stack این پروژه (Python/FastAPI) ناسازگار است؛ controller واقعی `backend/app/routers/users.py` است. تست‌ها با pytest + pytest-asyncio + aiosqlite اجرا می‌شوند (طبق `.github/workflows/ci.yml`).

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/src/app/facilities/page.tsx` (سطر 362) — در FacilityFormModal فهرست را fetch می‌کند (customersApi.list) و الگوی pagination مشابه users دارد؛ صفحات وابسته به لیست از این خطای 500 متأثر می‌شوند
- `frontend/src/app/customers/page.tsx` (سطر 37) — الگوی مرجع برای فراخوانی list با page/page_size/sort_by/sort_order — ساختار درخواست مشابه endpoint کاربران است و می‌تواند معیار مقایسهٔ payload صحیح باشد
- `backend/app/models/user.py` (سطر 1) — مدل SQLAlchemy کاربر که در روتر users query می‌شود؛ به‌گفتهٔ نقشهٔ import، توسط backend/app/routers/auth.py و سایر فایل‌ها استفاده می‌شود — هر mismatch فیلد با schema منجر به 500 می‌شود
- `backend/app/schemas/admin_user.py` (سطر 1) — schema احتمالی خروجی فهرست کاربران؛ اگر serialization اینجا fail کند، پاسخ 500 تولید می‌شود

## 🌐 نقشهٔ وابستگی‌ها
روتر کاربران در `backend/app/main.py` خط 191 با `app.include_router(users.router, prefix="/api/users")` ثبت شده و وابسته به مدل `backend/app/models/user.py` است. طبق «نقشهٔ Importهای داخلی»، `backend/app/models/user.py` توسط ۵ فایل import می‌شود (`backend/app/utils/security.py`, `backend/app/models/__init__.py`, `backend/app/services/facility_authorization.py`, `backend/app/db_init.py`, `backend/app/routers/auth.py`) — پس تغییر مدل پرخطر است و باید فقط در لایهٔ schema/router محدود بماند. روتر users همچنین به `backend/app/database.py` (که ۱۶ فایل import می‌کنند) برای async session وابسته است. خطای 500 از مسیر `unhandled_exception_handler_500` در `backend/app/main.py` (خط 122-159) عبور می‌کند که برای همهٔ روترها مشترک است. در frontend، هم صفحهٔ users و هم FacilityFormModal (در `frontend/src/app/facilities/page.tsx` خط 360-365) از این endpoint برای پر کردن لیست استفاده می‌کنند.

## 🔍 Context و وضعیت فعلی
کاربر گزارش می‌دهد که در کنسول مرورگر، endpoint `api/users/?page=1&page_size=100` چندین بار خطای 500 برمی‌گرداند:

```
Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
api/users/?page=1&page_size=100:1  Failed to load resource: the server responded with a status of 500 ()
```

این خطا روی صفحهٔ کاربران (frontend) و همچنین در FacilityFormModal که برای پر کردن dropdown مشتری/کاربر فهرست را fetch می‌کند، اثر می‌گذارد. نکتهٔ حیاتی که کاربر تأکید کرده: این خطا **foundation** است — تا زمانی که endpoint کاربران درست کار نکند، صفحات وابسته به لیست کاربران بارگذاری نمی‌شوند، پس باید اول حل شود.

کلیدواژه‌های ذکرشده توسط کاربر: `api/users/`, `page_size`, `page`, `backend/controllers/index.js`. **توجه مهم:** کاربر به `backend/controllers/index.js` اشاره کرده ولی این پروژه یک backend مبتنی بر **FastAPI (Python)** است، نه Node/Express. مسیر `backend/controllers/index.js` در ساختار پروژه وجود ندارد — controller واقعی این پروژه `backend/app/routers/users.py` است که در `backend/app/main.py` خط 191 با prefix `/api/users` ثبت شده: `app.include_router(users.router, prefix="/api/users", tags=["users"])`.

بر اساس الگوی سایر روترها (مثلاً صفحهٔ مشتریان در `frontend/src/app/customers/page.tsx` خط 37-43 که با پارامترهای `page`, `page_size`, `sort_by`, `sort_order` فهرست می‌گیرد)، خطای 500 معمولاً ناشی از یکی از این موارد است: (الف) خطای کوئری pagination/sort در روتر users، (ب) خطای serialization در schema کاربر (مثلاً فیلد nullable یا enum mismatch)، (ج) عدم رعایت سقف `page_size` یا offset محاسبه‌شده. هر unhandled exception نیز توسط `unhandled_exception_handler_500` در `backend/app/main.py` خط 122-155 به پاسخ 500 با `error_id` تبدیل می‌شود — پس برای دیباگ باید لاگ سرور با همان `error_id` بررسی شود.

خارج از scope این تسک: هرگونه تغییر UI یا طراحی صفحه.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] درخواست GET /api/users/?page=1&page_size=100 پاسخ 200 با ساختار pagination (items, page, page_size, total) برمی‌گرداند، نه 500
- [ ] روتر users در backend/app/main.py با prefix /api/users ثبت شده و handler فهرست در backend/app/routers/users.py پارامترهای page و page_size را به‌درستی پردازش می‌کند (offset/limit صحیح)
- [ ] تست backend رگرسیون برای endpoint کاربران اضافه شده و pass می‌شود
- [ ] schema خروجی کاربران (backend/app/schemas/user.py یا admin_user.py) همهٔ فیلدهای nullable مدل User را به‌درستی نگاشت می‌کند تا serialization منجر به 500 نشود
- [ ] در کنسول مرورگر هنگام بارگذاری صفحهٔ کاربران، دیگر خطای 'Failed to load resource: status 500' برای api/users تکرار نمی‌شود
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) ابتدا فایل واقعی روتر `backend/app/routers/users.py` و schema مربوط در `backend/app/schemas/user.py` و `backend/app/schemas/admin_user.py` را باز کن (در deep-context خوانده نشده‌اند، مجری باید مسیر را تأیید کند — هر دو در «ساختار کامل پروژه» موجودند).

۲) هندلر GET فهرست کاربران را پیدا کن (handler متناظر با `/api/users/` که پارامترهای `page` و `page_size` را می‌گیرد) و کوئری SQLAlchemy آن را بررسی کن: محاسبهٔ `offset = (page - 1) * page_size`، اعمال `limit(page_size)`، و serialization خروجی به Pydantic schema.

۳) سرور را لوکال اجرا کن و دقیقاً همان درخواست `GET /api/users/?page=1&page_size=100` را بزن؛ traceback را از لاگ بخوان. چون `unhandled_exception_handler_500` (خط 122-155 در `backend/app/main.py`) جزئیات را پنهان می‌کند، با `logger.exception` و `error_id` در لاگ سرور علت اصلی را پیدا کن.

۴) علت‌های محتمل را برطرف کن: enum/nullable mismatch در schema، نبودن guard برای `page_size` بزرگ، خطای async session، یا فیلدی که در مدل User هست ولی در schema نگاشت نشده.

۵) یک تست backend در `backend/tests/` اضافه کن که `GET /api/users/?page=1&page_size=100` را بزند و انتظار status 200 با ساختار pagination (`items`, `page`, `page_size`, `total`) داشته باشد — مشابه الگوی `backend/tests/integration/test_auth.py`.

۶) verify کن که صفحات وابسته (لیست کاربران و dropdown مشتری در FacilityFormModal خط 360-365 در `frontend/src/app/facilities/page.tsx`) دیگر خطای 500 نمی‌گیرند.

## 💡 نمونه‌های قبل/بعد
**افزودن تست رگرسیون برای endpoint کاربران (الگوی pytest async موجود در پروژه)**

_قبل:_
```
# هیچ تستی برای GET /api/users/?page=1&page_size=100 وجود ندارد؛ خطای 500 بدون تست رد می‌شود
```

_بعد:_
```
import pytest

@pytest.mark.asyncio
async def test_list_users_pagination(async_client):
    resp = await async_client.get('/api/users/?page=1&page_size=100')
    assert resp.status_code == 200
    body = resp.json()
    assert 'items' in body
    assert body['page'] == 1
    assert body['page_size'] == 100
    assert 'total' in body
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd backend && pytest tests/integration/test_users.py -v`
- `cd backend && pytest --cov=app --cov-report=term-missing`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
مدل `backend/app/models/user.py` توسط ۵ فایل import می‌شود (`utils/security.py`, `models/__init__.py`, `services/facility_authorization.py`, `db_init.py`, `routers/auth.py`)؛ هر تغییر در ستون‌های مدل روی auth و bootstrap admin اثر می‌گذارد — پس اصلاح باید در لایهٔ schema/router محدود بماند نه مدل. همچنین `unhandled_exception_handler_500` در `backend/app/main.py` جزئیات خطا را در production پنهان می‌کند (خط 148-151)، پس دیباگ فقط با خواندن لاگ سرور (error_id) ممکن است نه از پاسخ HTTP. توجه: کاربر مسیر اشتباه `backend/controllers/index.js` را داده که در این پروژهٔ FastAPI وجود ندارد — مجری نباید دنبال فایل Node بگردد.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: bug
- اولویت: high
- تخمین زمان: medium

---

# 🔹 مرحله 2: افزودن امکان لاگین از طریق Gmail (Google OAuth)

**Scope:** این مرحله شامل پیاده‌سازی احراز هویت از طریق حساب Gmail/Google است تا کاربران بتوانند با گزینهٔ «Login with Google» وارد شوند. باید جریان OAuth (redirect، callback، صدور session/token) در backend و دکمهٔ مربوطه در صفحهٔ ورود فراهم شود. می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز روی لاگین جیمیل و دادن دسترسی و میزان دسترسی به افراد) الهام گرفت اما منطق را در stack پروژهٔ فعلی پیاده کرد. خارج از این مرحله: مدیریت سطوح دسترسی پیشرفته. نکتهٔ حیاتی: امنیت callback و ذخیرهٔ امن credentials.
**Key terms:** Gmail, Google OAuth, mahdighandi1989/language, login, backend/controllers/index.js

**بخش مربوط از متن کاربر:**
```
2- باید امکان لاگین از طریق جیمیل فراهم باشه

🎯 نقطهٔ تمرکز کاربر: امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد
```

## 🎯 هدف (خلاصه ساختاریافته)
افزودن لاگین با Google OAuth به صفحهٔ ورود

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `backend/app/main.py:184-197` — `include_router calls` — روتر google_auth از قبل با prefix /api/auth/google ثبت شده (برای drive backup). endpoint های login/callback باید به همین روتر افزوده شوند یا یک روتر جدید ثبت گردد.
  ```python
  app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
  app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])
  app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
  ```
- `backend/app/routers/google_auth.py` — `router` — این فایل deep-read نشده — مجری باید آن را بخواند تا ببیند آیا login/callback endpoint دارد یا فقط drive OAuth. دو endpoint جدید GET /login و GET /callback برای جریان احراز هویت ورود باید اینجا اضافه شود.
- `backend/app/services/google_oauth.py` — `GoogleOAuthService` — این فایل deep-read نشده — مجری باید بخواند تا منطق token exchange/userinfo موجود (برای drive.file) را reuse یا توسعه دهد برای scope های openid email profile.
- `backend/app/models/user.py` — `User model` — این فایل deep-read نشده اما توسط ۱۰ فایل import می‌شود. باید فیلدهای google_id و auth_provider و nullable بودن password برای کاربر OAuth بررسی/افزوده شود.

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Backend: FastAPI 0.104.1 + SQLAlchemy 2.0 (async) + python-jose/PyJWT برای JWT + httpx 0.26 برای فراخوانی Google token/userinfo endpoints. زیرساخت Google OAuth (google_oauth.py + روتر google_auth) برای drive.file از قبل موجود است. Frontend: Next.js 14 + React 18 + Tailwind + axios. احراز هویت فعلی JWT با refresh token است.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/utils/security.py` (سطر 1) — توابع صدور JWT و هش پسورد اینجاست؛ callback OAuth برای صدور session token از آن استفاده می‌کند. توسط ۵ فایل import می‌شود.
- `backend/app/routers/auth.py` (سطر 1) — روتر احراز هویت اصلی (/api/auth) — جریان login موجود؛ باید با OAuth callback همخوان باشد و الگوی صدور توکن یکسان حفظ شود.
- `backend/app/config.py` (سطر 1) — تنظیمات app؛ باید متغیرهای GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI خوانده شوند. توسط ۱۱ فایل import می‌شود.
- `backend/.env.example` (سطر 1) — نمونهٔ env؛ AUTH_DISABLED=true پیش‌فرض است و باید متغیرهای OAuth login اضافه شود.
- `frontend/src/app/login/page.tsx` (سطر 1) — صفحهٔ ورود frontend؛ دکمهٔ Login with Google اینجا اضافه می‌شود.

## 🌐 نقشهٔ وابستگی‌ها
روتر `google_auth.router` در `backend/app/main.py` خط 185 با prefix `/api/auth/google` ثبت شده و سرویس `backend/app/services/google_oauth.py` را استفاده می‌کند که خود `backend/app/config.py` (هاب با ۱۱ importer) را import می‌کند. callback OAuth برای صدور توکن به `backend/app/utils/security.py` (هاب با ۵ importer شامل routers/auth.py و db_init.py) وابسته است. مدل `backend/app/models/user.py` که توسط ۱۰ فایل (شامل security.py, routers/auth.py, db_init.py, services/facility_authorization.py) import می‌شود، نیاز به فیلدهای جدید (google_id, auth_provider) دارد که تغییر آن روی همهٔ این importerها و schema دیتابیس اثر می‌گذارد و migration در `backend/migrations/versions/` لازم است. صفحهٔ frontend `frontend/src/app/login/page.tsx` (build در `backend/static/login/index.html`) به endpoint جدید redirect می‌کند.

## 🔍 Context و وضعیت فعلی
کاربر درخواست کرده است که «امکان لاگین از طریق جیمیل فراهم باشه» — یعنی افزودن گزینهٔ «Login with Google» در سیستم احراز هویت. این تسک شامل پیاده‌سازی کامل جریان Google OAuth برای ورود کاربران است: redirect به Google، دریافت callback، استخراج اطلاعات کاربر (email/profile)، یافتن یا ساخت user متناظر در دیتابیس، و صدور JWT session/token طبق همان الگوی فعلی پروژه. کاربر اشاره کرده می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز روی لاگین جیمیل و دادن دسترسی و میزان دسترسی به افراد، فایل `backend/controllers/index.js`) الهام گرفت، ولی منطق باید در stack فعلی (FastAPI + Next.js 14) پیاده شود.

نکتهٔ بسیار مهم: پروژه از قبل زیرساخت Google OAuth دارد اما **فقط برای Google Drive Backup** (scope `drive.file`) — نه برای login. در `backend/app/main.py` خط 13 و خط 185 روتر `google_auth` با prefix `/api/auth/google` ثبت شده است (`app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])`) و سرویس `backend/app/services/google_oauth.py` موجود است. بنابراین این تسک باید جریان OAuth جدیدی برای **login** (نه drive backup) اضافه کند یا سرویس موجود را توسعه دهد. همچنین در `backend/.env.example` تنظیمات SMTP و auth موجود است ولی متغیرهای `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GOOGLE_REDIRECT_URI` برای OAuth باید بررسی/افزوده شوند.

در سمت backend، روتر احراز هویت اصلی `backend/app/routers/auth.py` است (با prefix `/api/auth`) و سرویس امنیتی `backend/app/utils/security.py` که توابع صدور JWT و هش پسورد را دارد و توسط ۵ فایل import می‌شود. مدل کاربر `backend/app/models/user.py` (که توسط ۱۰ فایل import می‌شود) باید بررسی شود که آیا فیلدهای لازم برای کاربر OAuth (مثلاً `google_id`, `auth_provider`, password nullable) را دارد یا نیاز به migration دارد.

در سمت frontend، صفحهٔ ورود در `backend/static/login/index.html` (build خروجی Next.js) و سورس آن در `frontend/src/app/login/page.tsx` است؛ باید دکمهٔ «Login with Google» اضافه شود که به endpoint شروع OAuth redirect کند. توجه: در `.env.example` پرچم `AUTH_DISABLED=true` به‌صورت پیش‌فرض فعال است که login را bypass می‌کند — برای تست واقعی این فلگ باید false شود.

خارج از scope این مرحله: مدیریت سطوح دسترسی پیشرفته (RBAC). نکتهٔ حیاتی امنیتی که کاربر تأکید کرده: امنیت callback (validate state/nonce برای جلوگیری از CSRF) و ذخیرهٔ امن credentials.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] endpoint جدید GET /api/auth/google/login وجود دارد و یک redirect (302/307) به authorization URL گوگل با scope های openid/email/profile و پارامتر state برمی‌گرداند
- [ ] endpoint callback GET /api/auth/google/callback در روتر google_auth تعریف شده و state را validate می‌کند (محافظت CSRF)
- [ ] مدل User در backend/app/models/user.py فیلدهای google_id و auth_provider را دارد
- [ ] دکمهٔ Login with Google با data-testid='btn-google-login' در صفحهٔ ورود frontend موجود است
- [ ] متغیرهای GOOGLE_CLIENT_ID، GOOGLE_CLIENT_SECRET و redirect URI برای login در config و .env.example تعریف شده‌اند
- [ ] callback پس از موفقیت، با تابع صدور JWT از backend/app/utils/security.py توکن می‌سازد (نه پیاده‌سازی موازی)
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) فایل `backend/app/services/google_oauth.py` را کامل بخوان تا بفهمی جریان OAuth موجود (برای drive.file) چگونه است و آیا قابل توسعه برای login است یا باید مسیر جدید ساخته شود. ۲) در `backend/app/routers/google_auth.py` دو endpoint اضافه کن: `GET /api/auth/google/login` که یک authorization URL با scope های `openid email profile` و یک `state` تصادفی امن (ذخیره در session/redis برای CSRF) می‌سازد و کاربر را redirect می‌کند؛ و `GET /api/auth/google/callback` که `code` و `state` را می‌گیرد، state را verify می‌کند، token exchange با Google انجام می‌دهد، userinfo (email) می‌گیرد، در `backend/app/models/user.py` کاربر متناظر را find-or-create می‌کند، سپس با تابع صدور JWT در `backend/app/utils/security.py` توکن می‌سازد و کاربر را به frontend با token redirect می‌کند. ۳) در `backend/app/models/user.py` در صورت نبود، فیلدهای `google_id` (nullable, unique) و `auth_provider` اضافه کن و یک migration در `backend/migrations/versions/` بنویس. ۴) متغیرهای `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_LOGIN_REDIRECT_URI` را به `backend/.env.example` و `backend/app/config.py` اضافه کن. ۵) در `frontend/src/app/login/page.tsx` دکمهٔ «Login with Google» با `data-testid='btn-google-login'` اضافه کن که به `/api/auth/google/login` redirect کند. ۶) برای الهام‌گیری از منطق `mahdighandi1989/language` (فایل `backend/controllers/index.js`) فقط الگوی جریان را بردار، نه کد JS را — معادل آن را در FastAPI بنویس. امنیت callback: حتماً `state` validation و استفاده از HTTPS redirect (که در `backend/app/main.py` خط 82-101 با HTTPSRedirectInProductionMiddleware enforce می‌شود) را رعایت کن.

## 💡 نمونه‌های قبل/بعد
**ثبت روترها در main.py — افزودن جریان login (در صورت روتر جدا)**

_قبل:_
```
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])
```

_بعد:_
```
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# google_auth router now also serves login (GET /login, GET /callback) in
# addition to the existing Drive-backup OAuth flow.
app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `pytest backend/tests/integration/test_auth.py -v`
- `pytest backend/tests/ -k google -v`
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`

## ⚠️ ریسک‌ها و موارد احتیاط
۱) مدل `backend/app/models/user.py` توسط ۱۰ فایل import می‌شود (security.py, routers/auth.py, db_init.py, facility_authorization.py و ...)؛ افزودن فیلد یا nullable کردن password بدون migration درست باعث خطای schema در startup می‌شود (init_database در main.py خط 40-44 سعی در self-heal دارد ولی روی drift شکست می‌خورد). ۲) روتر `google_auth` از قبل برای drive.file استفاده می‌شود؛ افزودن scope های login نباید جریان backup موجود را بشکند — باید جریان جداگانه باشد. ۳) عدم validate کردن `state` در callback یک حفرهٔ CSRF است (تأکید صریح کاربر بر امنیت callback). ۴) فلگ AUTH_DISABLED=true در .env.example باعث می‌شود تست واقعی login bypass شود؛ مجری باید برای تست آن را false کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: feature_request
- اولویت: medium
- تخمین زمان: large

---

# 🔹 مرحله 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر

**Scope:** این مرحله شامل بهبود ظاهر و کارکرد صفحهٔ ورود است: صفحهٔ ورود فعلی جذاب نیست، گزینه‌های دیگر در آن دیده نمی‌شوند و منوی ناوبری ندارد. باید طراحی صفحهٔ ورود بهبود یابد، گزینه‌های دیگر (مثل ورود با Gmail که در مرحلهٔ ۲ اضافه شد) به‌وضوح نمایش داده شوند و یک منوی ناوبری (nav bar) اضافه شود. خارج از این مرحله: رفع خطای backend و طراحی کلی سایر صفحات. نکتهٔ حیاتی: گزینه‌های ورود باید قابل کشف و دیده‌شدنی باشند.
**Key terms:** صفحه ورود, منوی ناوبری, navigation menu, login page, Gmail

**بخش مربوط از متن کاربر:**
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره
```

## 🎯 هدف (خلاصه ساختاریافته)
بازطراحی صفحهٔ ورود + افزودن nav bar و نمایش ورود با Gmail

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/login/page.tsx` — `LoginPage` — منبع اصلی صفحهٔ ورود. build آن در backend/static/login/index.html سرو می‌شود. تغییرات UI باید اینجا اعمال و سپس npm run build اجرا شود.
  ```tsx
  این فایل deep-read شده ولی محتوای TSX آن در blob نمایش داده نشده — مجری باید فرم فعلی (Username/Password + دکمهٔ Sign In) را اینجا پیدا و دکمهٔ Google + nav bar را اضافه کند.
  ```
- `backend/static/login/index.html:1` — `login form` — صفحهٔ login فعلی رندرشده — نبود nav bar و گزینهٔ Gmail اینجا قابل مشاهده است.
  ```
  <form class="space-y-6"><div><label for="username" ...>Username</label>...<input id="username" type="text" .../></div><div><label for="password" ...>Password</label>...<input id="password" type="password" .../></div><button type="submit" class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 ...">Sign In</button></form>
  ```
- `backend/static/audit/index.html:1` — `header/nav` — الگوی nav bar موجود در سایر صفحات — می‌توان برای صفحهٔ login نسخهٔ سبک‌تر آن را اقتباس کرد.
  ```
  <header class="bg-white border-b shadow-sm"><div class="container mx-auto px-4 flex items-center justify-between h-16"><div class="flex items-center gap-8"><span class="text-lg font-bold text-blue-600">Banking Ops</span><nav class="flex items-center gap-1">...Dashboard...Customers...Facilities...</nav></div>...</header>
  ```
- `backend/app/main.py:184-186` — `include_router(google_auth)` — روتر Google OAuth از قبل تحت /api/auth/google ثبت شده — endpoint موردنیاز دکمهٔ «ورود با Gmail» آماده است.
  ```python
  app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
  app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])
  app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi (backend Python 3.11) + nextjs 14 (React 18, App Router, TypeScript). UI با Tailwind CSS، آیکن‌ها از lucide-react، نوتیفیکیشن با react-hot-toast/sonner، HTTP با axios. Google OAuth 2.0 برای login با Gmail (scope drive.file در backup، login flow جدا). build فرانت با `npm run build` (tsc --noEmit && next build) و خروجی به backend/static کپی می‌شود.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/app/services/google_oauth.py` (سطر 1) — سرویس Google OAuth که endpoint /api/auth/google از آن استفاده می‌کند؛ دکمهٔ جدید Gmail به این flow وصل می‌شود
- `backend/app/routers/google_auth.py` (سطر 1) — روتر مقصد دکمهٔ ورود با Gmail — باید مسیر redirect/authorize آن بررسی شود تا دکمه به URL درست لینک شود
- `backend/app/routers/auth.py` (سطر 1) — روتر اصلی auth که endpoint /api/auth/config و login فعلی را سرو می‌کند؛ صفحهٔ login برای حالت AUTH_DISABLED از آن می‌خواند
- `frontend/out/login/index.html` (سطر 1) — خروجی build فرانت در پوشهٔ out — پس از تغییر TSX و build باید بازتولید و در backend/static کپی شود

## 🌐 نقشهٔ وابستگی‌ها
صفحهٔ login منبع آن `frontend/src/app/login/page.tsx` است و خروجی build در `backend/static/login/index.html` و `frontend/out/login/index.html` سرو می‌شود (mount استاتیک در `backend/app/main.py` خط ۲۶۵ via mount_static_frontend). دکمهٔ «ورود با Gmail» به روتر `backend/app/routers/google_auth.py` (ثبت‌شده در main.py خط ۱۸۵ تحت prefix /api/auth/google) وصل می‌شود که خود به سرویس `backend/app/services/google_oauth.py` وابسته است. صفحهٔ login همچنین به endpoint `GET /api/auth/config` از `backend/app/routers/auth.py` وابسته است تا حالت AUTH_DISABLED را تشخیص دهد. nav bar الگوبرداری‌شده از header موجود در سایر صفحات (audit/customers/...) است که در layout مشترک Next.js تعریف شده — افزودن آن به login نباید با layout اصلی تداخل کند.

## 🔍 Context و وضعیت فعلی
کاربر درخواست داده که صفحهٔ ورود (login page) بازطراحی شود چون «صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره». سه خواستهٔ مشخص وجود دارد: (۱) بهبود ظاهر و کارکرد صفحهٔ ورود، (۲) نمایش واضح و قابل‌کشف گزینه‌های دیگر ورود — به‌خصوص «ورود با Gmail» که در مرحلهٔ ۲ پروژه اضافه شده (Google OAuth)، و (۳) افزودن یک منوی ناوبری (navigation menu / nav bar) به صفحهٔ ورود. نکتهٔ حیاتی تأکیدشده توسط کاربر: «گزینه‌های ورود باید قابل کشف و دیده‌شدنی باشند». خارج از scope این مرحله: رفع خطای backend و طراحی کلی سایر صفحات.

شواهد در کد واقعی: صفحهٔ ورود فعلی در منبع Next.js در `frontend/src/app/login/page.tsx` پیاده شده و build آن در `backend/static/login/index.html` سرو می‌شود. در HTML رندرشده (خط ۱) فقط یک فرم ساده با دو فیلد Username/Password و یک دکمهٔ «Sign In» دیده می‌شود — هیچ دکمهٔ «ورود با Gmail / Sign in with Google» و هیچ nav bar در آن نیست؛ کل صفحه فقط یک کارت وسط‌چین با کلاس `bg-white p-8 rounded-xl shadow-lg w-full max-w-md` است. در مقابل، صفحات دیگر مثل `backend/static/audit/index.html` (خط ۱) یک header کامل با nav bar دارند (`<header class="bg-white border-b shadow-sm">` به‌همراه لینک‌های Dashboard/Customers/Facilities/...). پشتیبانی Google OAuth در backend موجود است: روتر `app.include_router(google_auth.router, prefix="/api/auth/google", ...)` در `backend/app/main.py` خط ۱۸۵ ثبت شده و سرویس `backend/app/services/google_oauth.py` نیز وجود دارد؛ پس endpoint لازم برای دکمهٔ «ورود با Gmail» از قبل آماده است و فقط UI آن در صفحهٔ login غایب است. همچنین `backend/app/.env.example` نشان می‌دهد `AUTH_DISABLED=true` به‌صورت پیش‌فرض فعال است و فرانت‌اند از `GET /api/auth/config` وضعیت auth را در runtime می‌خواند — این رفتار باید در بازطراحی حفظ شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] صفحهٔ /login شامل یک دکمه/لینک «Sign in with Google» با data-testid='btn-google-login' است که به /api/auth/google اشاره می‌کند
- [ ] صفحهٔ /login دارای یک header/nav bar با برند 'Banking Ops' است (مشابه سایر صفحات)
- [ ] endpoint /api/auth/google در backend در دسترس است و redirect/پاسخ معتبر می‌دهد (روتر ثبت‌شده در main.py)
- [ ] در source TSX صفحهٔ login، دکمهٔ Google و یک جداکنندهٔ 'OR' بین فرم و دکمهٔ Google وجود دارد
- [ ] ظاهر کلی صفحهٔ ورود بهبود یافته و گزینه‌های ورود قابل کشف و واضح هستند
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) فایل منبع `frontend/src/app/login/page.tsx` را باز کن (build در `backend/static/login/index.html` است؛ تغییر باید روی source TSX انجام و سپس `npm run build` اجرا شود). ۲) یک هدر/nav bar سبک به بالای صفحهٔ login اضافه کن — می‌توان از همان الگوی header موجود در صفحات دیگر (`backend/static/audit/index.html` خط ۱: `<header class="bg-white border-b shadow-sm">` با برند «Banking Ops») استفاده کرد، ولی نسخهٔ سبک‌تر مناسب صفحهٔ ورود (مثلاً فقط لوگو/برند + لینک‌های عمومی). ۳) یک دکمهٔ مشخص «Sign in with Google / ورود با Gmail» با آیکن Google زیر یا کنار دکمهٔ «Sign In» اضافه کن که کاربر را به `/api/auth/google` (روتر ثبت‌شده در `backend/app/main.py` خط ۱۸۵) هدایت می‌کند؛ از سرویس موجود `backend/app/services/google_oauth.py` استفاده شود. ۴) جداکنندهٔ بصری «یا / OR» بین فرم username/password و دکمهٔ Google قرار بده تا گزینه‌ها «قابل کشف» باشند (خواستهٔ حیاتی کاربر). ۵) ظاهر کارت را بهبود بده (spacing، فاصله، آیکن‌ها). ۶) سازگاری با `GET /api/auth/config` و حالت `AUTH_DISABLED` را حفظ کن. ۷) فقط همین مرحله — به رفع backend یا سایر صفحات دست نزن.

## 💡 نمونه‌های قبل/بعد
**صفحهٔ login — افزودن دکمهٔ Google + جداکننده**

_قبل:_
```
<button type="submit" class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 ...">Sign In</button></form>
```

_بعد:_
```
<button type="submit" class="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 ...">Sign In</button></form>
<div class="flex items-center gap-3 my-6"><div class="flex-1 h-px bg-gray-200"></div><span class="text-xs text-gray-400">OR</span><div class="flex-1 h-px bg-gray-200"></div></div>
<a href="/api/auth/google" data-testid="btn-google-login" class="w-full flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 rounded-lg hover:bg-gray-50"><img src="/google-icon.svg" class="w-5 h-5" alt=""/>Sign in with Google</a>
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd backend && pytest tests/integration/test_auth.py -q`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر `frontend/src/app/login/page.tsx` نیازمند rebuild و کپی خروجی به `backend/static/login/index.html` است؛ اگر فقط HTML build دستی ویرایش شود، در deploy بعدی overwrite می‌شود. افزودن nav bar به login نباید با layout مشترک Next.js (که در سایر صفحات header را تزریق می‌کند) تداخل ایجاد کند — صفحهٔ login ممکن است layout متفاوتی داشته باشد. دکمهٔ Google به `backend/app/routers/google_auth.py` و سرویس `google_oauth.py` وابسته است؛ اگر redirect URI یا OAuth scope درست پیکربندی نشده باشد، دکمه کار نمی‌کند. همچنین حالت AUTH_DISABLED=true (پیش‌فرض در .env.example) می‌تواند رفتار login را تغییر دهد و باید در تست لحاظ شود.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: feature_request
- اولویت: medium
- تخمین زمان: medium

---

# 🔹 مرحله 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها

**Scope:** این مرحله شامل بررسی، تکمیل و اصلاح صفحاتی است که کاربر گفته ناقص هستند، کار نمی‌کنند یا درست دسته‌بندی نشده‌اند. باید هر صفحهٔ معیوب شناسایی، تکمیل و در ساختار/دسته‌بندی منطقی قرار گیرد (مثلاً گروه‌بندی منطقی صفحات در منو). خارج از این مرحله: رفع خطای endpoint کاربران و طراحی بصری کلی. نکتهٔ حیاتی: باید فهرستی از صفحات معیوب تهیه شود و هرکدام به وضعیت کارکردی برسد.
**Key terms:** صفحات ناقص, دسته‌بندی, pages, navigation, routing

**بخش مربوط از متن کاربر:**
```
3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
```

## 🎯 هدف (خلاصه ساختاریافته)
تکمیل و دسته‌بندی صفحات ناقص و غیرفعال Next.js در منوی ناوبری

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/customers/page.tsx:115-138` — `CustomersPage (header + Layout)` — این صفحهٔ «کامل و سالم» الگوی استاندارد برای تکمیل صفحات ناقص است (Layout + header + data-testid + actions).
  ```tsx
  return (<div data-testid="customers-page">
      <Layout>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Customers</h2>
  ```
- `frontend/src/app/customers/page.tsx:189-302` — `loading/empty-state pattern` — الگوی loading spinner + empty-state «No X found» که هر صفحهٔ ناقص باید داشته باشد.
  ```tsx
  {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : data && data.items.length > 0 ? (
  ```
- `frontend/src/app/facilities/page.tsx:45-76` — `loadFacilities (Promise.allSettled + parseApiError)` — الگوی صحیح error-handling برای صفحاتی که فعلاً خطا را silently swallow می‌کنند یا روی spinner گیر می‌کنند.
  ```tsx
  const loadFacilities = async () => {
      setLoading(true)
      const [facilitiesResult] = await Promise.allSettled([
        facilitiesApi.list({
          page,
          page_size: 20,
  ```
- `backend/app/main.py:184-197` — `app.include_router(...)` — مرجع تطبیق صفحات frontend با endpointهای backend — هر صفحه باید به یک router فعال وصل باشد. توجه: notifications router (خط ۱۹۴) ثبت شده ولی صفحهٔ frontend متناظر باید بررسی شود.
  ```python
  app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
  app.include_router(google_auth.router, prefix="/api/auth/google", tags=["google-auth"])
  app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
  app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
  ```
- `frontend/src/components/Layout.tsx` — `Layout / nav menu` — این فایل deep-read نشده — مجری باید مسیر را خود تأیید کند. کامپوننت Layout که در همهٔ صفحات import می‌شود (frontend/src/app/customers/page.tsx خط ۵) و منوی ناوبری اینجا تعریف شده؛ گروه‌بندی منطقی صفحات اینجا اعمال می‌شود.

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi (backend Python 3.11, SQLAlchemy 2.0, JWT) + nextjs (Next.js 14 App Router, React 18, TypeScript, Tailwind CSS, axios, lucide-react icons, react-hot-toast). صفحات frontend از الگوی 'use client' + Layout component + useState/useEffect استفاده می‌کنند.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/src/lib/api.ts` (سطر 6) — همهٔ صفحات از این فایل (customersApi, facilitiesApi, parseApiError, downloadFile) برای فراخوانی endpoint استفاده می‌کنند؛ صفحهٔ ناقص ممکن است به API method موجود وصل نباشد
- `frontend/src/app/facilities/page.tsx` (سطر 23) — الگوی دوم صفحهٔ سالم برای استانداردسازی صفحات ناقص (جدول، فیلتر پیشرفته، bulk action، export)
- `backend/app/main.py` (سطر 184) — تعریف routerهای فعال backend که هر صفحهٔ frontend باید با یکی از آن‌ها تطبیق داشته باشد
- `frontend/src/types/index.ts` (سطر 1) — تایپ‌های Customer/Facility/CustomerList که صفحات برای render داده استفاده می‌کنند؛ صفحهٔ ناقص ممکن است type نداشته باشد
- `FEATURE_BACKLOG.md` (سطر 1) — محل ثبت فهرست صفحات معیوب و وضعیت هرکدام طبق نکتهٔ حیاتی کاربر

## 🌐 نقشهٔ وابستگی‌ها
منوی ناوبری در `frontend/src/components/Layout.tsx` متمرکز است و توسط همهٔ صفحات App Router (از جمله `frontend/src/app/customers/page.tsx` خط ۵ و `frontend/src/app/facilities/page.tsx` خط ۶) import می‌شود — هر تغییر در ساختار منو روی navigation کل اپ اثر می‌گذارد. صفحات برای داده از `frontend/src/lib/api.ts` (customersApi/facilitiesApi/parseApiError/downloadFile) استفاده می‌کنند، که خود به axios و JWT auth وابسته است. سمت backend، صحت هر صفحه به فعال‌بودن router متناظر در `backend/app/main.py` (خط ۱۸۴-۱۹۷: auth, customers, facilities, stats, offer_letters, reports, users, trash, audit, notifications, imports, settings, fx, google_auth) بستگی دارد. تغییر گروه‌بندی منو هیچ state سمت backend را تغییر نمی‌دهد ولی روی e2e تست‌های navigation و data-testidها اثر می‌گذارد. صفحاتی که router-only هستند (notifications, google-auth) بدون صفحهٔ frontend، حذف یا ساخته شوند.

## 🔍 Context و وضعیت فعلی
کاربر در بند ۳ درخواست اصلی خود گفته است: «خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن». این تسک یک ممیزی سیستماتیک از تمام صفحات frontend (App Router در Next.js 14) است تا هر صفحهٔ معیوب، ناقص یا فاقد دسته‌بندی منطقی شناسایی، تکمیل و در ساختار منوی ناوبری به‌شکل گروه‌بندی‌شدهٔ منطقی قرار گیرد. کلیدواژه‌های اصلی کاربر: «صفحات ناقص، دسته‌بندی، pages، navigation، routing». از روی ساختار پروژه، صفحات موجود در App Router از روی خروجی build در `backend/static/` و `frontend/out/` قابل تشخیص هستند: dashboard, customers, customer-detail, facilities, facility-detail, offer-letters, fx (نرخ ارز), reports, import, audit, trash, users, settings, profile, login. نکتهٔ مهم اینکه در `backend/app/main.py` خط ۱۸۴-۱۹۷ همهٔ routerهای backend ثبت شده‌اند (auth, customers, facilities, stats, offer_letters, reports, users, trash, audit, notifications, imports, settings, fx, google_auth) — اما توجه کن که router `fx` در backend ثبت شده (خط ۱۹۷) درحالی‌که router `google_auth` هم mount شده ولی صفحهٔ frontend متناظر آن لزوماً وجود ندارد؛ همچنین صفحه‌ای برای `notifications` یا تنظیمات گوگل‌درایو ممکن است ناقص باشد. صفحات کامل و سالم مانند `frontend/src/app/customers/page.tsx` (۵۶۰ خط، شامل جدول، فیلتر، فرم، صفحه‌بندی، اعتبارسنجی) و `frontend/src/app/facilities/page.tsx` (۵۴۶ خط) به‌عنوان «الگوی صفحهٔ کامل و سالم» استفاده می‌شوند تا صفحات ناقص با همین استاندارد (Layout، loading spinner، data-testid، toast، pagination، empty-state «No X found») تکمیل شوند. خارج از scope این تسک: رفع خطای endpoint کاربران و طراحی بصری کلی (طبق گفتهٔ کاربر). خروجی نهایی باید شامل: (۱) فهرست مستند صفحات معیوب با وضعیت هرکدام، (۲) رساندن هر صفحه به وضعیت کارکردی، (۳) گروه‌بندی منطقی صفحات در منوی ناوبری (مثلاً گروه «مشتریان و تسهیلات»، گروه «مالی/FX و گزارش‌ها»، گروه «سیستم/کاربران/تنظیمات/سطل بازیافت»).

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] فهرست مستند صفحات معیوب و وضعیت کارکردی هرکدام در FEATURE_BACKLOG.md یا یک فایل TO-DO ثبت شده باشد
- [ ] منوی ناوبری در Layout.tsx به گروه‌های منطقی دسته‌بندی شده باشد (حداقل ۲ گروه با عنوان)
- [ ] هر صفحهٔ تکمیل‌شده شامل کامپوننت Layout و الگوی loading spinner و empty-state باشد (مطابق customers/page.tsx خط ۱۹۰-۳۰۱)
- [ ] هیچ لینک منو به صفحهٔ ۴۰۴ منتهی نشود — همهٔ مسیرهای منو به page.tsx واقعی در App Router یا router فعال backend متصل باشند
- [ ] build فرانت‌اند بدون خطای TypeScript و بدون route ناقص کامل شود (npm run build)
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) ابتدا کامپوننت `frontend/src/components/Layout.tsx` (که در همهٔ صفحات import می‌شود — خط ۵ در customers/page.tsx و facilities/page.tsx) را باز کن و فهرست آیتم‌های منوی ناوبری فعلی + لینک‌های routing را استخراج کن. ۲) یک ممیزی روی تمام مسیرهای موجود در `frontend/src/app/*/page.tsx` انجام بده و آن‌ها را با routerهای backend در `backend/app/main.py` خط ۱۸۴-۱۹۷ تطبیق بده؛ هر صفحه‌ای که (الف) فقط placeholder/خالی است، (ب) به endpoint موجود وصل نیست، یا (ج) loading/empty-state/error-handling ندارد را به‌عنوان «معیوب» علامت بزن و در یک فایل مستند `FEATURE_BACKLOG.md` یا یک TO-DO ثبت کن. ۳) برای هر صفحهٔ ناقص، الگوی صفحهٔ سالم `customers/page.tsx` را پیاده کن: استفاده از `Layout`, `useState` برای loading/data، فراخوانی API از `@/lib/api`, نمایش spinner هنگام loading (خط ۱۹۰-۱۹۳)، empty-state «No X found» (خط ۳۰۱)، و `data-testid` روی المان‌های کلیدی. ۴) منوی ناوبری در `Layout.tsx` را به گروه‌های منطقی بازسازی کن: گروه «عملیات» (dashboard, customers, facilities, offer-letters)، گروه «مالی و گزارش» (fx, reports, import)، گروه «سیستم» (users, audit, trash, settings, profile). برای هر آیتم منو href صحیح متناظر با مسیر App Router بگذار. ۵) مطمئن شو هر لینک منو به صفحه‌ای منتهی می‌شود که واقعاً render می‌شود (نه ۴۰۴). اگر صفحه‌ای backend-router دارد ولی frontend-page ندارد (مثل notifications یا google-auth settings)، یا صفحه بساز یا از منو حذف کن.

## 💡 نمونه‌های قبل/بعد
**نمونه ساختار صفحهٔ ناقص → تکمیل با الگوی صفحهٔ سالم**

_قبل:_
```
// صفحهٔ ناقص (placeholder)
export default function SomePage() {
  return <div>Coming soon</div>
}
```

_بعد:_
```
'use client'
import Layout from '@/components/Layout'
import { useEffect, useState } from 'react'
import { someApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'

export default function SomePage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    someApi.list().then(setData).catch((e) => toast.error(parseApiError(e))).finally(() => setLoading(false))
  }, [])
  return (<div data-testid="some-page"><Layout>
    {loading ? <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>
     : data ? (/* table */) : <div className="py-12 text-center text-gray-500">No items found</div>}
  </Layout></div>)
}
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`
- `cd backend && pytest --cov=app`

## ⚠️ ریسک‌ها و موارد احتیاط
تغییر ساختار منو در `frontend/src/components/Layout.tsx` روی همهٔ صفحات App Router اثر می‌گذارد چون این کامپوننت در هر page.tsx import می‌شود (مثلاً خط ۵ در customers/page.tsx و خط ۶ در facilities/page.tsx) — تغییر selector یا data-testid منو می‌تواند تست‌های e2e navigation را بشکند. اگر صفحه‌ای را برای router-only هایی مثل notifications (main.py خط ۱۹۴) یا google_auth (خط ۱۸۵) بسازی، باید endpoint و auth flow را درست متصل کنی وگرنه صفحهٔ جدید روی spinner گیر می‌کند. حذف لینک از منو بدون حذف صفحه ممکن است صفحه‌ای را orphan کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: feature_request
- اولویت: medium
- تخمین زمان: large

---

# 🔹 مرحله 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)

**Scope:** این مرحله شامل ساماندهی ارتباط بین اجزا و صفحات است؛ کاربر گفته ارتباط اجزا و صفحات به‌هم‌ریخته است. باید جریان ناوبری بین صفحات، لینک‌ها و انتقال‌ها منسجم و قابل پیش‌بینی شود (information architecture منظم، breadcrumb یا منوی یکپارچه). خارج از این مرحله: استایل بصری صرف و رفع backend. نکتهٔ حیاتی: کاربر باید بتواند به‌صورت منطقی بین صفحات و اجزای مرتبط حرکت کند بدون سردرگمی.
**Key terms:** ارتباط اجزا, صفحات, navigation flow, routing, information architecture

**بخش مربوط از متن کاربر:**
```
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
```

## 🎯 هدف (خلاصه ساختاریافته)
یکپارچه‌سازی ناوبری و breadcrumb بین صفحات Next.js

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/customers/page.tsx` — `CustomersPage` — این فایل deep-read شده اما snippet دقیق lines در blob موجود نبود؛ مجری باید الگوی لینک list→detail و active-state nav را اینجا بررسی کند
  ```tsx
  // سورس صفحهٔ Customers — کارت‌ها/ردیف‌های لیست از اینجا به /customer-detail/ لینک می‌شوند
  ```
- `frontend/src/app/facilities/page.tsx` — `FacilitiesPage` — deep-read شده؛ snippet خطی در blob نبود — الگوی navigation به detail را مجری تأیید کند
  ```tsx
  // سورس صفحهٔ Facilities — ردیف‌ها به /facility-detail/ منتقل می‌شوند؛ active-state و breadcrumb باید همسان شوند
  ```
- `backend/static/customers/index.html:1` — `nav active-state` — اینجا کلاس active (bg-blue-50 text-blue-700) hardcode روی Customers ست شده — باید پویا با usePathname شود تا detailها هم والد را highlight کنند
  ```
  <a class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors bg-blue-50 text-blue-700" href="/customers/">...Customers</a>
  ```
- `backend/static/customer-detail/index.html:1` — `main content` — صفحهٔ detail هیچ breadcrumb و هیچ active-state در nav ندارد — نقطهٔ اصلی به‌هم‌ریختگی ناوبری
  ```
  <main class="container mx-auto px-4 py-6"><!--$!--><template data-dgst="BAILOUT_TO_CLIENT_SIDE_RENDERING"></template><div class="py-16 text-center text-gray-500">Loading…</div><!--/$--></main>
  ```
- `backend/app/main.py:184-197` — `include_router` — روترهای users و settings ثبت شده‌اند ولی صفحات متناظر در nav اصلی حضور ندارند — عدم انسجام بین backend و IA فرانت
  ```python
  app.include_router(users.router, prefix="/api/users", tags=["users"])
  app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
  ```

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi (backend serve static + API routers) + nextjs 14 (App Router, React 18). ناوبری با `next/link` و active-state معمولاً با `usePathname()` از `next/navigation`. استایل با Tailwind CSS؛ آیکون‌ها lucide-react. خروجی build فرانت به‌صورت static export در `backend/static/` سرو می‌شود.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `backend/static/_next/static/chunks/app/layout-76fb5480b9f0209d.js` (سطر 1) — خروجی build از layout/Nav مشترک که header و nav همهٔ صفحات از آن می‌آید؛ منبع اصلی active-state و آیتم‌های منو
- `backend/static/facility-detail/index.html` (سطر 1) — همانند customer-detail فاقد breadcrumb و active-state است؛ باید با همان الگو اصلاح شود
- `backend/static/audit/index.html` (سطر 1) — نمونهٔ دیگری از header/nav تکراری که باید با منبع واحد یکپارچه شود (Audit در nav اصلی نیست ولی صفحه‌اش هست)
- `backend/static/settings/index.html` (سطر 1) — صفحهٔ Settings وجود دارد اما در nav اصلی لینک ندارد — باید به IA اضافه شود
- `backend/app/main.py` (سطر 232) — mount_static_frontend (خط 232) فرانت build شده را serve می‌کند؛ پس از تغییر باید static دوباره کپی شود

## 🌐 نقشهٔ وابستگی‌ها
نوار navigation و header از یک layout مشترک Next.js می‌آید (سورس `frontend/src/app/layout.tsx` + کامپوننت Nav)، که خروجی build آن `backend/static/_next/static/chunks/app/layout-76fb5480b9f0209d.js` است و در **همهٔ** صفحات static (`customers`, `customer-detail`, `facilities`, `facility-detail`, `audit`, `settings`, `users`, `reports`, ...) عیناً تکرار شده. هر تغییر در این کامپوننت روی تمام صفحات اثر می‌گذارد — این یک هاب UI است. سرو شدن این فایل‌ها از طریق `mount_static_frontend` در `backend/app/main.py` (خط 232) و `CachedStaticFiles` (خط 208) انجام می‌شود؛ پس از rebuild فرانت، خروجی باید مجدداً در `backend/static/` کپی شود تا تغییرات اعمال شوند. صفحات `frontend/src/app/customers/page.tsx` و `frontend/src/app/facilities/page.tsx` مصرف‌کنندهٔ این layout هستند و منطق لینک list→detail در آن‌ها قرار دارد.

## 🔍 Context و وضعیت فعلی
کاربر در بخش ۴ درخواست اصلی نوشته: «ارتباط اجزا و صفحات خیلی به هم ریخته س». هدف این تسک بهبود information architecture و انسجام navigation flow بین صفحات اپلیکیشن است — نه استایل بصری صرف و نه رفع backend (این دو صراحتاً خارج از scope این مرحله هستند). کاربر می‌خواهد بتواند به‌صورت منطقی و قابل پیش‌بینی بین صفحات و اجزای مرتبط حرکت کند بدون سردرگمی (information architecture منظم، breadcrumb یا منوی یکپارچه). کلیدواژه‌های صریح کاربر: «ارتباط اجزا», «صفحات», «navigation flow», «routing», «information architecture».

شواهد در کد واقعی پروژه: ناوبری اصلی در header مشترک تعریف شده و در همهٔ صفحات تکرار می‌شود — در `backend/static/audit/index.html` و `backend/static/customers/index.html` و `backend/static/customer-detail/index.html` نوار `<nav class="flex items-center gap-1">` دیده می‌شود که شامل لینک‌های `/dashboard/`, `/customers/`, `/facilities/`, `/offer-letters/`, `/reports/`, `/import/`, `/trash/` است. اما چند مشکل انسجام مشهود است: (۱) صفحات `customer-detail` و `facility-detail` در نوار اصلی navigation **هیچ آیتم فعال (active) متناظری ندارند** — وقتی کاربر وارد `/customer-detail/` می‌شود هیچ آیتمی highlight نمی‌شود (در `backend/static/customers/index.html` کلاس active به‌صورت `bg-blue-50 text-blue-700` روی Customers ست شده، ولی در `customer-detail` این لینک‌بک وجود ندارد و فقط «Loading…» نمایش داده می‌شود). (۲) صفحهٔ `Settings` و `Users` و `Profile` در نوار navigation اصلی **حضور ندارند** (در nav فقط Dashboard/Customers/Facilities/Offer Letters/Reports/Import/Recycle Bin هست) درحالی‌که routerهای backend آن‌ها در `backend/app/main.py` خطوط 191 و 196 ثبت شده‌اند (`users` و `settings`). (۳) **هیچ breadcrumb** بین صفحهٔ list و صفحهٔ detail وجود ندارد — کاربر از `/customers/` به `/customer-detail/` می‌رود ولی راه بازگشت منطقی (breadcrumb مثل Customers › نام مشتری) دیده نمی‌شود. این عدم تطابق دقیقاً همان «به‌هم‌ریختگی ارتباط اجزا و صفحات» است که کاربر گزارش کرده. منبع اصلی این header و nav، فایل layout مشترک Next.js (`frontend/src/app/layout.tsx` یا کامپوننت Nav مشترک) است که build آن در `backend/static/_next/static/chunks/app/layout-76fb5480b9f0209d.js` خروجی گرفته شده.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] در nav مشترک، active-state با usePathname پویا شود و صفحات detail والدشان را highlight کنند (customer-detail → Customers)
- [ ] یک کامپوننت Breadcrumb وجود دارد و در صفحات customer-detail و facility-detail استفاده می‌شود
- [ ] آیتم‌های منوی مفقود (Settings/Users) که روترشان در backend/app/main.py خطوط 191 و 196 ثبت شده، به IA/nav افزوده شوند
- [ ] ناوبری از صفحهٔ Customers به یک ردیف/کارت مشتری، صفحهٔ customer-detail را لود می‌کند و breadcrumb بازگشت نمایش داده می‌شود
- [ ] build فرانت بدون خطای type-check و lint کامل شود (npm run build شامل tsc --noEmit)
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) کامپوننت navigation مشترک (layout و Nav که خروجی build آن `backend/static/_next/static/chunks/app/layout-76fb5480b9f0209d.js` است و سورس آن در `frontend/src/app/layout.tsx` + احتمالاً `frontend/src/components/Nav.tsx`) را پیدا و یکپارچه کن: لیست واحدِ آیتم‌های nav را در یک آرایهٔ مرکزی (مثل `NAV_ITEMS`) تعریف کن تا همهٔ صفحات از همان منبع بخوانند. ۲) منطق active-state را به جای hardcode (کلاس `bg-blue-50 text-blue-700`) با `usePathname()` از `next/navigation` پویا کن، و mapping صفحات detail به والدشان اضافه کن (مثلاً `/customer-detail` → Customers و `/facility-detail` → Facilities highlight شود). ۳) یک کامپوننت Breadcrumb بساز (`frontend/src/components/Breadcrumb.tsx`) که در صفحات detail (`customer-detail`, `facility-detail`) مسیر منطقی نشان دهد: مثلاً «Customers › {customer.name}» با لینک بازگشت به `/customers/`. ۴) آیتم‌های مفقود را که router آن‌ها در `backend/app/main.py` ثبت است (Settings خط 196، Users خط 191، Profile) به nav یا یک منوی فرعی منسجم اضافه کن. ۵) از صفحهٔ list به detail و بالعکس، انتقال‌ها را یکدست کن (همهٔ کارت‌ها/ردیف‌ها لینک کلیک‌پذیر با همان الگو). سپس frontend را build و در `backend/static/` کپی کن (طبق `mount_static_frontend` در `backend/app/main.py` خط 232).

## 💡 نمونه‌های قبل/بعد
**active-state پویا برای صفحات detail در Nav**

_قبل:_
```
<a class="... bg-blue-50 text-blue-700" href="/customers/">Customers</a>  // active فقط روی /customers/ hardcode
```

_بعد:_
```
const pathname = usePathname();
const isActive = pathname.startsWith('/customers') || pathname.startsWith('/customer-detail');
<Link className={`... ${isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'}`} href="/customers/">Customers</Link>
```

**افزودن breadcrumb در صفحهٔ customer-detail**

_قبل:_
```
<main class="container mx-auto px-4 py-6"><div class="py-16 text-center text-gray-500">Loading…</div></main>
```

_بعد:_
```
<main class="container mx-auto px-4 py-6"><Breadcrumb items={[{label:'Customers', href:'/customers/'}, {label: customer?.name ?? '...'}]} /><!-- محتوای detail --></main>
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
نوار nav از layout مشترک می‌آید و در همهٔ صفحات static (`backend/static/*/index.html`) تکرار شده — هر تغییر در `frontend/src/app/layout.tsx` یا کامپوننت Nav روی تمام صفحات اثر می‌گذارد و باید همهٔ آن‌ها rebuild شوند. اگر active-state با usePathname اشتباه map شود، ممکن است هیچ آیتم یا چند آیتم همزمان highlight شوند. تغییر فقط در `backend/static/*.html` بدون تغییر سورس `frontend/src/` در build بعدی overwrite می‌شود (طبق mount_static_frontend خط 232 main.py) — پس تغییرات باید در سورس فرانت اعمال و سپس static دوباره کپی شود، وگرنه بی‌اثر است.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: refactor
- اولویت: medium
- تخمین زمان: medium

---

# 🔹 مرحله 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)

**Scope:** این مرحله شامل رفع آشفتگی بصری کلی برنامه است؛ کاربر گفته از منظر ظاهری خیلی آشفته است. باید یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها، تایپوگرافی، کامپوننت‌های مشترک) در سراسر صفحات اعمال شود تا ظاهر یکدست و تمیز شود. خارج از این مرحله: منطق backend و کارکرد صفحات. نکتهٔ حیاتی: consistency در همهٔ صفحات و کامپوننت‌ها باید رعایت شود تا حس آشفتگی برطرف گردد.
**Key terms:** ظاهر, visual consistency, design system, styling, UI

**بخش مربوط از متن کاربر:**
```
5- از منظر ظاهری خیلی آشفته اس
```

## 🎯 هدف (خلاصه ساختاریافته)
ساخت design system مشترک و یکدست‌سازی استایل صفحات Next.js

## 📍 موقعیت دقیق در پروژه
_(file:line — symbol — snippet)_

- `frontend/src/app/customers/page.tsx` — `CustomersPage` — source صفحهٔ Customers (معادل build شده در backend/static/customers/index.html خط ۱). دکمه‌ها با کلاس‌های inline ناهمگون — باید با کامپوننت مشترک Button جایگزین شوند. snippet از نسخهٔ build استخراج شده؛ مجری باید markup معادل را در این page.tsx پیدا کند.
  ```tsx
  <button type="button" data-testid="add-customer-btn" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">...Add Customer</button>
  ```
- `frontend/src/app/facilities/page.tsx` — `FacilitiesPage` — source صفحهٔ Facilities (build در backend/static/facilities/index.html). باید از همان design system و کامپوننت‌های مشترک استفاده کند. این فایل deep-read شده ولی محتوای کامل آن در blob نیامده — مجری markup را تأیید کند.
  ```tsx
  // صفحهٔ Facilities — همان الگوی header/nav + فیلترها + جدول که در سایر صفحات تکرار شده
  ```
- `backend/static/customers/index.html:1` — `header/nav build output` — خروجی build که نشان می‌دهد header/nav عیناً در همهٔ صفحات تکرار شده (همین markup در audit/index.html و customer-detail/index.html هم هست). شاهد آشفتگی و تکرار — منبع آن در frontend است نه این فایل static.
  ```
  <header class="bg-white border-b shadow-sm"><div class="container mx-auto px-4 flex items-center justify-between h-16"><div class="flex items-center gap-8"><span class="text-lg font-bold text-blue-600">Banking Ops</span><nav class="flex items-center gap-1">...
  ```
- `backend/static/audit/index.html:1` — `filter form build output` — دکمهٔ Filter با استایل `bg-gray-100` در حالی که در صفحهٔ customers دکمهٔ Filter `bg-blue-600 text-white` است — مصداق ناهماهنگی بین صفحات که باید با variant مشخص از Button مشترک یکدست شود.
  ```
  <button type="submit" class="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">Filter</button>
  ```
- `backend/static/_next/static/css/bb3c73b9739ec88a.css` — `compiled tailwind css` — خروجی نهایی Tailwind پس از build. تغییر tokens در tailwind.config باعث regenerate این فایل می‌شود. این فایل دستی ویرایش نمی‌شود — فقط نتیجهٔ build است.

## 🧭 هدف اصلی پروژه (از یادداشت کاربر)
(کاربر یادداشتی ثبت نکرده است)

## 🧱 پشتهٔ فناوری و معماری
Stack: fastapi (backend سرو static) + nextjs (frontend اصلی). فرانت: Next.js 14.1.0 (App Router)، React 18.2.0، Tailwind CSS 3.4.1، lucide-react 0.312.0 برای آیکون‌ها، react-hot-toast/sonner برای toast. هیچ کامپوننت UI library مثل shadcn نصب نیست؛ کامپوننت‌های مشترک باید دستی روی Tailwind ساخته شوند.

## 🔗 فایل‌های مرتبط (Cross-references)
_(فایل‌هایی که با موقعیت‌های هدف در ارتباط هستند — import، caller، shared state)_

- `frontend/src/app/layout.tsx` — محل مناسب برای قراردادن AppShell/Navbar مشترک تا header/nav تکراری از همهٔ صفحات حذف و یکدست شود
- `frontend/tailwind.config.ts` — محل تعریف design tokens (رنگ primary، spacing، radius، فونت) که consistency سراسری را تضمین می‌کند
- `frontend/src/app/globals.css` — محل تعریف CSS variables و base styles مشترک برای تایپوگرافی و رنگ‌ها
- `frontend/src/app/reports/page.tsx` — یکی از صفحاتی که باید با کامپوننت‌های مشترک بازنویسی شود تا آشفتگی رفع شود
- `frontend/src/app/dashboard/page.tsx` — صفحهٔ داشبورد که کارت‌های آماری دارد و باید از Card/Badge مشترک استفاده کند

## 🌐 نقشهٔ وابستگی‌ها
این تغییر در لایهٔ presentation فرانت‌اند Next.js متمرکز است. منبع همهٔ صفحات در `frontend/src/app/*/page.tsx` است (deep-read: `frontend/src/app/customers/page.tsx`, `frontend/src/app/facilities/page.tsx`) که خروجی build آن‌ها در `backend/static/*/index.html` دیده می‌شود. کامپوننت‌های مشترک جدید (در `frontend/src/components/ui/`) توسط همهٔ این page.tsxها import خواهند شد، پس به یک hub تبدیل می‌شوند — هر تغییر در Button/Card روی همهٔ صفحات اثر می‌گذارد (همان هدف consistency). `frontend/tailwind.config.ts` و `frontend/src/app/globals.css` پایهٔ design tokens هستند و توسط کل فرانت مصرف می‌شوند. `frontend/src/app/layout.tsx` به‌عنوان wrapper مشترک، Navbar یکدست را به همهٔ مسیرها تزریق می‌کند. هیچ‌یک از routerهای backend (`backend/app/routers/*.py`) و سرویس‌ها تحت تأثیر نیستند چون فقط markup/CSS عوض می‌شود؛ تنها نکته این است که خروجی build فرانت در نهایت توسط `mount_static_frontend` در `backend/app/main.py` (خط ۲۳۲) سرو می‌شود، پس باید پس از تغییر، فرانت دوباره build و در static کپی شود.

## 🔍 Context و وضعیت فعلی
کاربر در بند ۵ درخواست اصلی گفته است: «۵- از منظر ظاهری خیلی آشفته اس» و خواستهٔ این تسک «یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)» است. کلیدواژه‌های صریح کاربر: ظاهر، visual consistency، design system، styling، UI. هدف، رفع آشفتگی بصری در سراسر صفحات و اعمال یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها/spacing، تایپوگرافی و کامپوننت‌های مشترک) است. صریحاً خارج از scope این مرحله: منطق backend و کارکرد صفحات — یعنی فقط لایهٔ presentation/UI تغییر می‌کند نه business logic.

شواهد در کد واقعی پروژه: استک frontend روی Next.js 14 (App Router) + Tailwind CSS است (package.json: `next 14.1.0`, `tailwindcss 3.4.1`, `lucide-react 0.312.0`). نسخهٔ build شدهٔ صفحات در `backend/static/*/index.html` نشان می‌دهد که markup و کلاس‌های Tailwind به‌صورت **تکراری و کپی‌شده** در هر صفحه inline شده‌اند — مثلاً همان header/nav کامل (`<header class="bg-white border-b shadow-sm">` با `<span class="text-lg font-bold text-blue-600">Banking Ops</span>` و کل لیست `<nav>...`) در `backend/static/audit/index.html` (خط ۱)، `backend/static/customers/index.html` (خط ۱) و `backend/static/customer-detail/index.html` (خط ۱) عیناً تکرار شده. همین تکرار، منشأ ناهماهنگی است: هر صفحه ممکن است نسخهٔ کمی متفاوت از همان دکمه/کارت/فاصله داشته باشد. در `backend/static/customers/index.html` دکمه‌های مختلف با کلاس‌های ناهمگون دیده می‌شوند (`px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm` برای Export در مقابل `px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700` برای Add Customer و `bg-gray-100 rounded-lg hover:bg-gray-200` برای Filter در audit) — یعنی هیچ کامپوننت Button/Card/PageHeader مشترکی وجود ندارد و رنگ‌ها/spacing دستی و پراکنده‌اند. منبع اصلی کد در `frontend/src/app/*/page.tsx` است (مثلاً `frontend/src/app/customers/page.tsx` و `frontend/src/app/facilities/page.tsx` که deep-read شده‌اند و معادل source این HTMLهای build هستند). راه‌حل: تعریف design tokens در `tailwind.config` + ساخت کامپوننت‌های مشترک (Button, Card, PageHeader, Input/Select, Badge) و جایگزینی markupهای تکراری در همهٔ صفحات با این کامپوننت‌ها تا حس آشفتگی برطرف شود. نکتهٔ حیاتی کاربر: consistency باید در **همهٔ** صفحات و کامپوننت‌ها رعایت شود.

## ✅ معیار پذیرش (Acceptance Criteria) — رفتار-محور
**مهم:** هر AC رفتار قابل مشاهده را تعریف می‌کند، نه نام فایل/کلاس.
verify می‌تواند پیاده‌سازی متفاوت ولی هم‌ارز را قبول کند.

- [ ] پوشهٔ frontend/src/components/ui/ ساخته شده و حداقل کامپوننت‌های Button, Card, PageHeader تعریف شده‌اند
- [ ] design tokens (رنگ primary/spacing) در tailwind.config تعریف شده‌اند
- [ ] صفحهٔ customers از کامپوننت مشترک Button استفاده می‌کند نه کلاس inline تکراری bg-blue-600 ... rounded-lg hover:bg-blue-700
- [ ] header/nav مشترک به layout منتقل شده و در تک‌تک page.tsxها تکرار نشده
- [ ] type-check و build فرانت بدون خطا کامل می‌شوند (npm run type-check && npm run build)
- [ ] ظاهر کلی صفحات یکدست و تمیز به نظر برسد (حس آشفتگی رفع شود)
- [ ] هیچ تستی fail نمی‌شود (`npm run test` / `pytest`)
- [ ] linter بدون warning عبور می‌کند
- [ ] type-check موفق است (`tsc --noEmit` / `mypy`)

## 🪜 مراحل اجرایی پیشنهادی
1. ۱) تعریف design tokens مرکزی در `frontend/tailwind.config.ts` (یا js): پالت رنگ برند (مثلاً `primary` بر پایهٔ همان `blue-600`)، مقیاس spacing، radius و سایه‌های استاندارد، و خانوادهٔ فونت یکدست؛ و در صورت نبود، تعریف CSS variables در `frontend/src/app/globals.css`. ۲) ساخت پوشهٔ `frontend/src/components/ui/` و افزودن کامپوننت‌های مشترک: `Button.tsx` (variantهای primary/secondary/ghost با data-testid)، `Card.tsx`، `PageHeader.tsx` (تیتر + اکشن‌ها)، `Input.tsx`/`Select.tsx`، `Badge.tsx`. این‌ها جایگزین کلاس‌های تکراری مثل `px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700` می‌شوند. ۳) استخراج header/nav تکرارشده (که در `backend/static/audit/index.html` و `backend/static/customers/index.html` عیناً کپی شده) به یک `AppShell`/`Navbar` مشترک تا فقط یک منبع حقیقت برای layout بماند (احتمالاً در `frontend/src/app/layout.tsx` یا کامپوننت Navbar). ۴) بازنویسی صفحات `frontend/src/app/customers/page.tsx`، `frontend/src/app/facilities/page.tsx` و سایر `frontend/src/app/*/page.tsx` (dashboard, reports, offer-letters, audit, trash, users, settings, profile, import) برای استفاده از کامپوننت‌های مشترک و حذف کلاس‌های inline ناهمگون. ۵) اجرای `npm run type-check` و `npm run build` و `npm run lint` برای اطمینان از سالم‌بودن. کل تغییرات باید در لایهٔ UI بماند و هیچ تماس API یا منطق backend را تغییر ندهد (طبق scope صریح کاربر).

## 💡 نمونه‌های قبل/بعد
**یکدست‌سازی دکمهٔ primary با کامپوننت مشترک**

_قبل:_
```
<button type="button" data-testid="add-customer-btn" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"><Plus size={18}/>Add Customer</button>
```

_بعد:_
```
<Button variant="primary" data-testid="add-customer-btn" icon={<Plus size={18}/>}>Add Customer</Button>
// تعریف یکجا در frontend/src/components/ui/Button.tsx:
// const styles = { primary: 'bg-primary text-white hover:bg-primary/90', secondary: 'border hover:bg-gray-50', ghost: 'bg-gray-100 hover:bg-gray-200' }
```

**یکدست‌سازی دکمهٔ Filter بین صفحات (customers vs audit)**

_قبل:_
```
// customers: <button class="bg-blue-600 text-white rounded-lg hover:bg-blue-700">Filter</button>
// audit:     <button class="bg-gray-100 rounded-lg hover:bg-gray-200">Filter</button>
```

_بعد:_
```
// هر دو صفحه: <Button variant="secondary" type="submit">Filter</Button>  // یک ظاهر واحد در همه‌جا
```

## 📤 خروجی مورد انتظار
تغییر کد در فایل‌های مرتبط، commit یا PR جدید با پیام واضح، و عبور تمام معیارهای پذیرش.

## 🧪 دستورات اعتبارسنجی
- `cd frontend && npm run type-check`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`

## ⚠️ ریسک‌ها و موارد احتیاط
۱) کامپوننت‌های مشترک جدید در frontend/src/components/ui/ به hub تبدیل می‌شوند — هر page.tsx آن‌ها را import می‌کند؛ یک خطا در Button/Card روی همهٔ صفحات (customers, facilities, dashboard, reports, ...) منتشر می‌شود. ۲) صفحات از data-testid هایی مثل add-customer-btn, export-customers-xlsx, notification-bell, customers-content استفاده می‌کنند (دیده‌شده در backend/static/customers/index.html و audit/index.html) که احتمالاً در تست‌ها/E2E مرجع‌اند؛ هنگام بازنویسی markup با کامپوننت مشترک باید همین data-testidها حفظ شوند وگرنه تست‌های frontend (backend/tests/frontend/) می‌شکنند. ۳) خروجی build باید دوباره در backend/static کپی شود چون mount_static_frontend در backend/app/main.py خط ۲۳۲ همان را سرو می‌کند؛ فراموشی این مرحله یعنی تغییرات در production دیده نمی‌شود. ۴) تغییر globals.css/tailwind.config روی همهٔ صفحات اثر سراسری دارد و ممکن است layoutهای موجود را جابه‌جا کند.

## 🔗 وابستگی‌های تسکی
_(مستقل)_

## 🏷 دسته‌بندی
- نوع: refactor
- اولویت: medium
- تخمین زمان: large

---

## ✅ معیارهای پذیرش کلی (همهٔ مراحل)
- [ ] {'text': 'درخواست GET /api/users/?page=1&page_size=100 پاسخ 200 با ساختار pagination (items, page, page_size, total) برمی\u200cگرداند، نه 500', 'verify_method': 'api_response', 'verify_plan': {'method': 'GET', 'path': '/api/users/?page=1&page_size=100', 'expected_status': 200, 'required_fields': ['items', 'page', 'page_size', 'total']}}
- [ ] {'text': 'روتر users در backend/app/main.py با prefix /api/users ثبت شده و handler فهرست در backend/app/routers/users.py پارامترهای page و page_size را به\u200cدرستی پردازش می\u200cکند (offset/limit صحیح)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['include_router(users.router', 'page_size', 'offset', 'limit'], 'files_hint': ['backend/app/main.py', 'backend/app/routers/users.py']}}
- [ ] {'text': 'تست backend رگرسیون برای endpoint کاربران اضافه شده و pass می\u200cشود', 'verify_method': 'backend_test', 'verify_plan': {'test_path': 'backend/tests/integration/test_users.py::test_list_users_pagination', 'marker': 'verify'}}
- [ ] {'text': 'schema خروجی کاربران (backend/app/schemas/user.py یا admin_user.py) همهٔ فیلدهای nullable مدل User را به\u200cدرستی نگاشت می\u200cکند تا serialization منجر به 500 نشود', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['class.*User.*BaseModel', 'Optional', 'from_attributes'], 'files_hint': ['backend/app/schemas/user.py', 'backend/app/schemas/admin_user.py']}}
- [ ] {'text': "در کنسول مرورگر هنگام بارگذاری صفحهٔ کاربران، دیگر خطای 'Failed to load resource: status 500' برای api/users تکرار نمی\u200cشود", 'verify_method': 'ui_interaction', 'verify_plan': {'ui_steps': [{'action': 'navigate', 'url': '/users'}, {'action': 'wait_for', 'selector': 'table', 'timeout_ms': 5000}, {'action': 'assert_visible', 'selector': 'table'}]}}
- [ ] {'text': 'endpoint جدید GET /api/auth/google/login وجود دارد و یک redirect (302/307) به authorization URL گوگل با scope های openid/email/profile و پارامتر state برمی\u200cگرداند', 'verify_method': 'api_response', 'verify_plan': {'method': 'GET', 'path': '/api/auth/google/login', 'expected_status': 307}}
- [ ] {'text': 'endpoint callback GET /api/auth/google/callback در روتر google_auth تعریف شده و state را validate می\u200cکند (محافظت CSRF)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['/callback', 'state', 'def.*callback'], 'files_hint': ['backend/app/routers/google_auth.py']}}
- [ ] {'text': 'مدل User در backend/app/models/user.py فیلدهای google_id و auth_provider را دارد', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['google_id', 'auth_provider'], 'files_hint': ['backend/app/models/user.py']}}
- [ ] {'text': "دکمهٔ Login with Google با data-testid='btn-google-login' در صفحهٔ ورود frontend موجود است", 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['btn-google-login', 'Login with Google', 'google'], 'files_hint': ['frontend/src/app/login/page.tsx']}}
- [ ] {'text': 'متغیرهای GOOGLE_CLIENT_ID، GOOGLE_CLIENT_SECRET و redirect URI برای login در config و .env.example تعریف شده\u200cاند', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'REDIRECT_URI'], 'files_hint': ['backend/app/config.py', 'backend/.env.example']}}
- [ ] {'text': 'callback پس از موفقیت، با تابع صدور JWT از backend/app/utils/security.py توکن می\u200cسازد (نه پیاده\u200cسازی موازی)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['create_access_token', 'from app.utils.security', 'security'], 'files_hint': ['backend/app/routers/google_auth.py']}}
- [ ] {'text': "صفحهٔ /login شامل یک دکمه/لینک «Sign in with Google» با data-testid='btn-google-login' است که به /api/auth/google اشاره می\u200cکند", 'verify_method': 'ui_interaction', 'verify_plan': {'ui_steps': [{'action': 'navigate', 'url': '/login/'}, {'action': 'wait_for', 'selector': "[data-testid='btn-google-login']", 'timeout_ms': 3000}, {'action': 'assert_visible', 'selector': "[data-testid='btn-google-login']"}]}}
- [ ] {'text': "صفحهٔ /login دارای یک header/nav bar با برند 'Banking Ops' است (مشابه سایر صفحات)", 'verify_method': 'ui_interaction', 'verify_plan': {'ui_steps': [{'action': 'navigate', 'url': '/login/'}, {'action': 'wait_for', 'selector': 'header', 'timeout_ms': 3000}, {'action': 'assert_visible', 'selector': 'header'}]}}
- [ ] {'text': 'endpoint /api/auth/google در backend در دسترس است و redirect/پاسخ معتبر می\u200cدهد (روتر ثبت\u200cشده در main.py)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['google_auth.router', 'prefix="/api/auth/google"'], 'files_hint': ['backend/app/main.py']}}
- [ ] {'text': "در source TSX صفحهٔ login، دکمهٔ Google و یک جداکنندهٔ 'OR' بین فرم و دکمهٔ Google وجود دارد", 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['btn-google-login', '/api/auth/google', 'Sign in with Google'], 'files_hint': ['frontend/src/app/login/page.tsx']}}
- [ ] {'text': 'ظاهر کلی صفحهٔ ورود بهبود یافته و گزینه\u200cهای ورود قابل کشف و واضح هستند', 'verify_method': 'manual_only', 'verify_plan': {'reason': 'subjective — needs human review'}}
- [ ] {'text': 'فهرست مستند صفحات معیوب و وضعیت کارکردی هرکدام در FEATURE_BACKLOG.md یا یک فایل TO-DO ثبت شده باشد', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['صفحات ناقص', 'page audit', 'navigation', 'broken page'], 'files_hint': ['FEATURE_BACKLOG.md', 'frontend/src/components/Layout.tsx']}}
- [ ] {'text': 'منوی ناوبری در Layout.tsx به گروه\u200cهای منطقی دسته\u200cبندی شده باشد (حداقل ۲ گروه با عنوان)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['nav', 'group', 'href=', 'Layout'], 'files_hint': ['frontend/src/components/Layout.tsx']}}
- [ ] {'text': 'هر صفحهٔ تکمیل\u200cشده شامل کامپوننت Layout و الگوی loading spinner و empty-state باشد (مطابق customers/page.tsx خط ۱۹۰-۳۰۱)', 'verify_method': 'static', 'verify_plan': {'grep_patterns': ['<Layout>', 'animate-spin', 'No .* found', 'data-testid'], 'files_hint': ['frontend/src/app/customers/page.tsx', 'frontend/src/app/facilities/page.tsx']}}
- [ ] {'text': 'هیچ لینک منو به صفحهٔ ۴۰۴ منتهی نشود — همهٔ مسیرهای منو به page.tsx واقعی در App Router یا router فعال backend متصل باشند', 'verify_method': 'ui_interaction', 'verify_plan': {'ui_steps': [{'action': 'navigate', 'url': '/dashboard'}, {'action': 'assert_visible', 'selector': 'nav'}, {'action': 'navigate', 'url': '/reports'}, {'action': 'assert_visible', 'selector': "[data-testid='reports-page'], main, h2"}]}}

## Acceptance Criteria

1. درخواست GET /api/users/?page=1&page_size=100 پاسخ 200 با ساختار pagination (items, page, page_size, total) برمی‌گرداند، نه 500 _(verify: api_response)_
2. روتر users در backend/app/main.py با prefix /api/users ثبت شده و handler فهرست در backend/app/routers/users.py پارامترهای page و page_size را به‌درستی پردازش می‌کند (offset/limit صحیح) _(verify: static)_
3. تست backend رگرسیون برای endpoint کاربران اضافه شده و pass می‌شود _(verify: backend_test)_
4. schema خروجی کاربران (backend/app/schemas/user.py یا admin_user.py) همهٔ فیلدهای nullable مدل User را به‌درستی نگاشت می‌کند تا serialization منجر به 500 نشود _(verify: static)_
5. در کنسول مرورگر هنگام بارگذاری صفحهٔ کاربران، دیگر خطای 'Failed to load resource: status 500' برای api/users تکرار نمی‌شود _(verify: ui_interaction)_
6. هیچ تستی fail نمی‌شود (`npm run test` / `pytest`) _(verify: backend_test)_
7. linter بدون warning عبور می‌کند _(verify: manual_only)_
8. type-check موفق است (`tsc --noEmit` / `mypy`) _(verify: manual_only)_

## Task Steps

### Step 1: رفع خطای 500 در endpoint لیست کاربران (api/users)
**Status:** `pending` (0%)
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
**Status:** `pending` (0%)
**Scope:** این مرحله شامل پیاده‌سازی احراز هویت از طریق حساب Gmail/Google است تا کاربران بتوانند با گزینهٔ «Login with Google» وارد شوند. باید جریان OAuth (redirect، callback، صدور session/token) در backend و دکمهٔ مربوطه در صفحهٔ ورود فراهم شود. می‌توان از الگوی پروژهٔ مرجع `mahdighandi1989/language` (تمرکز روی لاگین جیمیل و دادن دسترسی و میزان دسترسی به افراد) الهام گرفت اما منطق را در stack پروژهٔ فعلی پیاده کرد. خارج از این مرحله: مدیریت سطوح دسترسی پیشرفته. نکتهٔ حیاتی: امنیت callback و ذخیرهٔ امن credentials.
**Excerpt:**
```
2- باید امکان لاگین از طریق جیمیل فراهم باشه

🎯 نقطهٔ تمرکز کاربر: امکان لاگین از طریق جیمیل و دادن دسترسی و میزن دسترسی به افراد
```

### Step 3: بازطراحی صفحهٔ ورود و افزودن منوی ناوبری و نمایش گزینه‌های دیگر
**Status:** `pending` (0%)
**Scope:** این مرحله شامل بهبود ظاهر و کارکرد صفحهٔ ورود است: صفحهٔ ورود فعلی جذاب نیست، گزینه‌های دیگر در آن دیده نمی‌شوند و منوی ناوبری ندارد. باید طراحی صفحهٔ ورود بهبود یابد، گزینه‌های دیگر (مثل ورود با Gmail که در مرحلهٔ ۲ اضافه شد) به‌وضوح نمایش داده شوند و یک منوی ناوبری (nav bar) اضافه شود. خارج از این مرحله: رفع خطای backend و طراحی کلی سایر صفحات. نکتهٔ حیاتی: گزینه‌های ورود باید قابل کشف و دیده‌شدنی باشند.
**Excerpt:**
```
1- صفحه ورود اصلا جالب نیست و گزینه های دیگه دیده نمیشه و منوی ناوبری نداره
```

### Step 4: تکمیل و رفع صفحات ناقص یا غیرفعال و دسته‌بندی صحیح آن‌ها
**Status:** `pending` (0%)
**Scope:** این مرحله شامل بررسی، تکمیل و اصلاح صفحاتی است که کاربر گفته ناقص هستند، کار نمی‌کنند یا درست دسته‌بندی نشده‌اند. باید هر صفحهٔ معیوب شناسایی، تکمیل و در ساختار/دسته‌بندی منطقی قرار گیرد (مثلاً گروه‌بندی منطقی صفحات در منو). خارج از این مرحله: رفع خطای endpoint کاربران و طراحی بصری کلی. نکتهٔ حیاتی: باید فهرستی از صفحات معیوب تهیه شود و هرکدام به وضعیت کارکردی برسد.
**Excerpt:**
```
3- خیلی از صفحات ناقص هستن یا کار نمیکنند یا درست دسته بندی نشدن
```

### Step 5: بهبود ارتباط و انسجام بین اجزا و صفحات (information architecture)
**Status:** `pending` (0%)
**Scope:** این مرحله شامل ساماندهی ارتباط بین اجزا و صفحات است؛ کاربر گفته ارتباط اجزا و صفحات به‌هم‌ریخته است. باید جریان ناوبری بین صفحات، لینک‌ها و انتقال‌ها منسجم و قابل پیش‌بینی شود (information architecture منظم، breadcrumb یا منوی یکپارچه). خارج از این مرحله: استایل بصری صرف و رفع backend. نکتهٔ حیاتی: کاربر باید بتواند به‌صورت منطقی بین صفحات و اجزای مرتبط حرکت کند بدون سردرگمی.
**Excerpt:**
```
4- ارتباط اجزا و صفحات خیلی به هم ریخته س
```

### Step 6: یکدست‌سازی و بهبود ظاهر کلی برنامه (visual consistency)
**Status:** `pending` (0%)
**Scope:** این مرحله شامل رفع آشفتگی بصری کلی برنامه است؛ کاربر گفته از منظر ظاهری خیلی آشفته است. باید یک سیستم طراحی منسجم (رنگ‌ها، فاصله‌ها، تایپوگرافی، کامپوننت‌های مشترک) در سراسر صفحات اعمال شود تا ظاهر یکدست و تمیز شود. خارج از این مرحله: منطق backend و کارکرد صفحات. نکتهٔ حیاتی: consistency در همهٔ صفحات و کامپوننت‌ها باید رعایت شود تا حس آشفتگی برطرف گردد.
**Excerpt:**
```
5- از منظر ظاهری خیلی آشفته اس
```
