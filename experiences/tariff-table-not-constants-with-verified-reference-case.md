---
title: "تعرفهٔ کارمزد: جدولِ قابل‌ویرایش نه ثابت‌های کد، با کیسِ مرجعِ واقعی در تست"
tags: ["tariff", "billing", "fees", "backend", "data-modeling", "banking"]
topic_canonical: "tariff-table-not-constants-with-verified-reference-case"
source:
  type: "claude-code-task"
  origin: "claude-code"
  imported_at: "2026-07-10T00:00:00Z"
created_at: "2026-07-10T00:00:00Z"
updated_at: "2026-07-10T00:00:00Z"
merged_from: []
---

# Fee tariffs as editable data, locked by a real reference case

## 🎯 چالش / Challenge

کارمزدِ خودکارِ سند (مثلاً processing fee افرلتر) باید از «بولتنِ تعرفهٔ» بانک
محاسبه شود؛ بولتن دوره‌ای عوض می‌شود، پر از شرط است (کف/سقف، آستانهٔ مبلغِ
کوچک، معافیتِ کارمندی، حالتِ پوششِ سپرده، تجمیعِ چند تسهیلات در «یک» کارمزدِ
خط)، و منبعش اسکنِ کاغذی است — استخراجِ اشتباه یعنی رقمِ مالیِ غلط در سندِ رسمی.

## 💡 راه‌حل / Solution

1. **قواعد = دادهٔ قابل‌ویرایش، نه ثابتِ کد:** جدولِ `charge_rules` با فیلدهای
   عمومی (method: per_mille/percent/flat، rate، min/max، آستانهٔ مبلغِ کوچک +
   کفِ مخصوصش، segment، نسخهٔ بولتن، enabled) + UI ویرایش. seed پیش‌فرض از
   بولتن با سیاستِ **fill-empty-only** (فقط وقتی جدول خالی است؛ ویرایش‌ها هرگز
   بازنویسی نمی‌شوند).
2. **ماشینِ محاسبه جدا از داده:** یک classifier متنِ آزادِ «نوع تسهیلات» را به
   خانوادهٔ قاعده نگاشت می‌کند؛ ناشناخته ⇒ صفر + هشدار (هرگز حدس نزن). شرط‌های
   ساختاری (تجمیعِ خط، per-item بودنِ برخی قواعد، معافیت‌ها) در ماشین‌اند نه در
   ردیف‌های داده.
3. **کیسِ مرجعِ واقعی را پیدا و در تست قفل کن:** قبل از کدنویسی، یک سندِ واقعیِ
   نهایی‌شده بردار و مدل را با آن اثبات کن (این‌جا: OD+CD → 12,200). اگر مدلت
   عددِ سندِ واقعی را نمی‌سازد، خوانشت از بولتن غلط است — نه برعکس.
4. semantics ظریف را از سندِ واقعی دربیاور، نه از حدس: مثلاً min/max کارمزدِ
   «خط» روی جمعِ خط اعمال می‌شود نه هر ردیف (وگرنه کیسِ مرجع جور درنمی‌آمد).

## 🧪 نمونه کد (Anonymized)

```python
def apply(rule, base):
    amt = {"flat": rule.rate,
           "percent": base * rule.rate / 100,
           "per_mille": base * rule.rate / 1000}[rule.method]
    if rule.small_threshold and base <= rule.small_threshold:
        rule_min = rule.small_min_charge          # e.g. loan ≤ 10k → min 200
    else:
        rule_min = rule.min_charge
    return clamp(amt, rule_min, rule.max_charge)

def test_reference_case_from_real_document():
    assert compute(items_from_real_letter())["total"] == 12200   # printed in the letter
```

## ⚠️ نکات حیاتی / Pitfalls

- «per-line» و «per-item» را قاطی نکن: بعضی کارمزدها یک‌بار روی جمع (خطِ
  اعتباری)، بعضی به‌ازای هر قلم (پوششِ سپرده، هر وام) هستند — کیسِ مرجع تنها
  راهِ مطمئنِ تفکیک است.
- معافیت‌ها attribute-محورند نه customer-محور: «تسهیلاتِ کارمندی» معاف است ولی
  «تسهیلاتِ غیرکارمندیِ همان کارمند» نه ⇒ پرچم روی هر قلم، نه روی حساب.
- Decimal، نه float، برای پول؛ ورودی‌های آزاد («2,800,000/-») را با regex عددی
  تمیز کن.
- نسخهٔ بولتن (C01-04-2025) را روی هر ردیف نگه دار تا بعدِ بازنگریِ سالانه
  معلوم باشد هر قاعده مالِ کدام نسخه است.

## 🔁 چطور در جای دیگر اعمال کنیم / How to Apply Elsewhere

- [ ] هر جدولِ نرخ/کارمزد/تعرفهٔ تغییرپذیر → جدولِ DB + UI ویرایش + seedِ
  fill-empty-only، هرگز ثابتِ کد.
- [ ] اول کیسِ مرجعِ واقعی، بعد مدل؛ کیس را به‌عنوانِ تستِ رگرسیون قفل کن.
- [ ] ناشناخته ⇒ صفر + هشدارِ قابل‌رؤیت؛ محاسبهٔ حدسی ممنوع.
- [ ] خروجی را با ریزِ محاسبه (breakdown) به کاربر نشان بده تا قابلِ‌راستی‌آزمایی
  باشد، نه فقط عددِ نهایی.

## 🔗 References

- مرتبط: [startup-merge-must-be-fill-empty-only]
- مرتبط: [conservative-dedup-compare-all-columns]
