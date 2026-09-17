---
title: "Long content belongs on more pages, not in a smaller font — flow it, repeat the header, decide orientation from the content"
tags: ["print", "pagination", "layout", "pdf", "tables", "a4", "rtl"]
topic_canonical: "flow-long-content-across-pages-dont-shrink-to-fit-one"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-09-17T14:00:00Z"
created_at: "2026-09-17T14:00:00Z"
updated_at: "2026-09-17T14:00:00Z"
merged_from: []
---

# Flow long content across pages — don't shrink it into one

## 🎯 چالش / Challenge

یک بلوکِ محتوا (معمولاً **جدول**) باید روی کاغذِ A4 چاپ شود. پیاده‌سازیِ اول
تقریباً همیشه این است: «اندازه‌اش بگیر؛ اگر جا نشد فونت را کوچک کن؛ اگر باز جا
نشد هشدار بده.» نتیجه:

- محتوای کمی بلند ⇒ فونتِ ۶۰٪ و یک صفحهٔ **خوانا-نشدنی**.
- محتوای واقعاً بلند ⇒ هشدارِ «کوتاهش کن» و یک جدولِ **بریده** در خروجی —
  یعنی کاربر اصلاً نمی‌تواند کارِ درستش را انجام دهد.

فرضِ پنهانِ غلط این است که «یک بلوک = یک صفحه». کاغذ محدود است، ولی **تعدادِ
کاغذها نیست**. کاربر با صفحهٔ دوم هیچ مشکلی ندارد؛ با متنِ ریز و دادهٔ گم‌شده دارد.

## 💡 راه‌حل / Solution

سه تصمیمِ مستقل را از هم جدا کن و هرکدام را با ورودیِ درستش بگیر:

1. **جهتِ صفحه (portrait / landscape) ← از عرضِ طبیعیِ محتوا.** محتوا را در یک
   ظرفِ خیلی پهن (مثلاً ۴۰۰۰px) رندر کن و عرضی که *خودش می‌خواهد* را بخوان؛ اگر
   از عرضِ مفیدِ صفحهٔ عمودی بیشتر بود، صفحه را افقی کن. ظرفِ اندازه‌گیری باید
   واقعاً پهن باشد وگرنه عرضِ طبیعی زیرْبرآورد می‌شود.
2. **اندازهٔ فونت ← فقط از عرض.** فونت را کوچک کن **تنها** وقتی محتوا حتی برای
   جهتِ انتخاب‌شده هم پهن‌تر است. ارتفاع هرگز دلیلِ کوچک‌کردنِ فونت نیست.
3. **ارتفاع ← با صفحهٔ بیشتر، نه با فونتِ کمتر.** محتوا را به **واحدهای اتمی**
   بشکن و حریصانه در صفحه‌ها بچین. واحدِ اتمیِ یک جدول، **یک ردیف** است — نه کلِ
   جدول — و هر تکه باید تگِ بازِ جدول و **ردیفِ سرستون** را با خود ببرد تا
   صفحهٔ دوم به‌تنهایی خوانا باشد و عرضِ ستون‌ها/استایل‌ها حفظ شود.

دو جزئیاتی که همیشه فراموش می‌شوند:

- **صفحهٔ خالیِ انتهایی.** ویرایشگرهای contentEditable همیشه یک خطِ خالی زیرِ
  جدول نگه می‌دارند. اگر آن خط دقیقاً سرریز کند، یک صفحهٔ **کاملاً سفید** ساخته
  می‌شود. هر صفحهٔ انتهایی که فقط بلوکِ نامرئی دارد را به صفحهٔ قبل تا کن.
- **ردیفِ بلندتر از یک صفحهٔ کامل.** تنها حالتی که خودکار حل‌شدنی نیست. آن ردیف
  را **دور نینداز** (رندرش کن، حتی با برش) و فقط همان یک مورد را به کاربر بگو.

اگر محتوا **ویرایش‌پذیر** است، تقسیم را یک پدیدهٔ صرفاً نمایشی نگه دار: هر تکه
ویرایشگرِ خودش را دارد، و در ذخیره تکه‌ها دوباره به **یک بلوکِ واحد** ادغام
می‌شوند (جدول‌های هم‌سرستونِ مجاور را fuse کن). آنچه ذخیره می‌شود همیشه کامل است.

## 🧪 نمونه کد (Anonymized)

```ts
type U = { html: string; h: number; tid: number; header: string; headerH: number; topen: string }

export function paginate(html: string, holder: HTMLElement, w: number, h: number, fontPt: number) {
  const box = document.createElement('div')
  box.style.cssText = `position:static;visibility:hidden;width:${w}px;font-size:${fontPt}pt`
  box.innerHTML = html
  holder.appendChild(box)

  const units: U[] = []
  let tid = 0, oversize = false
  const collect = (node: Element) => {
    for (const c of Array.from(node.children) as HTMLElement[]) {
      if (c.tagName === 'TABLE') {
        const rows = Array.from(c.querySelectorAll('tr')) as HTMLElement[]
        if (rows.length > 1) {
          tid++
          const header = rows[0].outerHTML, headerH = rows[0].offsetHeight
          const topen = c.outerHTML.slice(0, c.outerHTML.indexOf('>') + 1)  // keep width/class!
          for (let i = 1; i < rows.length; i++)
            units.push({ html: rows[i].outerHTML, h: rows[i].offsetHeight, tid, header, headerH, topen })
          continue
        }
      }
      if (c.tagName !== 'TABLE' && c.querySelector('table')) { collect(c); continue }  // unwrap
      units.push({ html: c.outerHTML, h: c.offsetHeight, tid: 0, header: '', headerH: 0, topen: '' })
    }
  }
  collect(box)
  holder.removeChild(box)

  const pgs: U[][] = []
  let cur: U[] = [], used = 0, seen = new Set<number>()
  for (const u of units) {
    const need = () => u.h + (u.tid && !seen.has(u.tid) ? u.headerH : 0)   // header costs once per page
    if (need() > h) oversize = true
    if (cur.length && used + need() > h) { pgs.push(cur); cur = []; used = 0; seen = new Set() }
    used += need(); cur.push(u); if (u.tid) seen.add(u.tid)
  }
  if (cur.length || !pgs.length) pgs.push(cur)

  const blank = (u: U) => !u.tid && !u.html.replace(/<[^>]+>/g, '').trim()
  while (pgs.length > 1 && pgs[pgs.length - 1].every(blank)) pgs[pgs.length - 2].push(...(pgs.pop() as U[]))

  const render = (us: U[]) => {           // regroup consecutive rows back into one <table>
    let out = '', i = 0
    while (i < us.length) {
      const u = us[i]
      if (!u.tid) { out += u.html; i++; continue }
      let rr = ''
      const t = u.tid
      while (i < us.length && us[i].tid === t) { rr += us[i].html; i++ }
      out += `${u.topen}${u.header}${rr}</table>`
    }
    return out
  }
  return { chunks: pgs.map(render), oversize }
}
```

تستِ این منطق در jsdom (که موتورِ چیدمان ندارد) با یک getterِ ساختگی ممکن است —
و همین آن را از «اسکنِ سورس» به تستِ واقعیِ تصمیم‌ها تبدیل می‌کند:

```ts
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  configurable: true,
  get() { return Number(this.getAttribute('data-h') || 0) || sumOfChildren(this) },
})
```

## ⚠️ نکات حیاتی / Pitfalls

- **تگِ بازِ جدول را بازنساز.** `<table>`ِ خالی، عرضِ ستون‌ها/کلاس‌های
  تغییرداده‌شده را بی‌صدا صفر می‌کند. رشتهٔ تگِ بازِ اصلی را ببر و همان را بگذار.
- **ارتفاعِ سرستون را در هر صفحه حساب کن** (یک‌بار به‌ازای هر جدول در هر صفحه).
  فراموش‌کردنش یعنی صفحهٔ آخرِ هر جدول همیشه کمی سرریز می‌کند.
- **هر تکه یک «برگهٔ» مستقلِ چاپ باشد.** اگر خروجیِ PDF از روی همان
  گره‌های صفحه ساخته شود، با این کار PDF و شماره‌گذاری **بدونِ هیچ تغییری** درست
  می‌شوند. سعی نکن PDF را جدا paginate کنی — دو منطق همیشه از هم جدا می‌افتند.
- **شمارهٔ صفحه را از مجموع بگیر، نه از تعدادِ بلوک‌ها** (`تعدادِ بلوک` ≠
  `تعدادِ صفحه` به‌محضِ اینکه یک بلوک چندصفحه‌ای شود).
- **در خروجیِ Word اصلاً تقسیم نکن:** Word خودش جدول را جاری می‌کند؛ فقط ردیفِ
  اول را به‌عنوانِ header علامت بزن تا تکرار شود.
- **هشدارِ قدیمی را پاک نکن، شرطش را واقعی کن.** هشداری که برای حالتِ حل‌شده
  می‌آید، کاربر را به حذفِ دادهٔ درست تشویق می‌کند.
- تغییرِ سیاستِ «کوچک‌کردنِ فونت» ظاهرِ **اسنادِ قدیمی** را هم عوض می‌کند
  (جدولِ ۶۰٪ حالا ۱۰۰٪ در دو صفحه). این معمولاً همان چیزی است که می‌خواستیم،
  ولی باید آگاهانه و اعلام‌شده باشد.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

1. هر جا `scale`/`zoom`/`font-size` را برای «جا شدن در یک صفحه» کم می‌کنی پیدا کن.
2. آن سه تصمیم را از هم جدا کن: جهت ← عرضِ طبیعی، فونت ← فقط عرض، ارتفاع ← صفحه.
3. واحدِ اتمیِ محتوا را تعریف کن (ردیفِ جدول، پاراگراف، آیتمِ لیست) و حریصانه بچین.
4. سرآیندِ تکرارشونده را در هر تکه بازتولید کن، با تگِ بازِ اصلی.
5. صفحهٔ انتهاییِ فقط-خالی را تا کن؛ واحدِ بزرگ‌تر از یک صفحه را گزارش کن نه حذف.
6. اگر ویرایش‌پذیر است: تقسیم فقط نمایشی، و در ذخیره دوباره ادغام کن.
7. تست بنویس که (الف) هیچ واحدی گم/تکرار نشود، (ب) هیچ صفحه‌ای سرریز نکند،
   (ج) رفت‌وبرگشتِ تقسیم←ویرایش←ادغام داده را نگه دارد.

## 🔗 References
- مرتبط: [paginated-doc-fixed-footer-cliff-slide-dont-push]
- مرتبط: [form-blank-by-default-blinking-placeholders-and-path-keyed-layout-overrides]
- مرتبط: [silent-input-truncation-makes-partial-output-look-complete]
