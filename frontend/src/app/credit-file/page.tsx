'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { Search, User, Building2 } from 'lucide-react'
import { accountTypeApi, customersApi, parseApiError, type AccountTypeVerdict } from '@/lib/api'
import toast from 'react-hot-toast'

// Single entry point for the credit-file summary. Enter an account number and
// the matching form opens — Retail for individuals, Corporate for companies.
//
// v139 — it no longer trusts the stored account_type on its own. That column
// used to DEFAULT to «retail» and the bulk import invented «retail» for any
// record without the column, so a company nobody had classified was
// indistinguishable from an individual somebody had — and this page silently
// opened the wrong form (the owner hit exactly that). The backend now also
// reports what the EVIDENCE says (trade licence, partners, trade name), and
// this page asks whenever the two disagree or nothing was ever recorded.
// It never rewrites the type by itself: the operator decides, and only then is
// the choice saved.
export default function CreditFilePage() {
  const router = useRouter()
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [choose, setChoose] = useState<{ id: string; accountNo: string; name: string } | null>(null)
  const [verdict, setVerdict] = useState<AccountTypeVerdict | null>(null)

  const go = (type: 'retail' | 'corporate', accountNo: string) => {
    const path = type === 'retail' ? '/credit-file-retail' : '/credit-file-corporate'
    router.push(`${path}/?acc=${encodeURIComponent(accountNo)}`)
  }

  const detect = async () => {
    const q = acc.trim()
    if (!q) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true); setChoose(null); setVerdict(null)
    try {
      const v = await accountTypeApi.of(q)
      setVerdict(v)
      // Ask whenever nobody decided, or when the evidence contradicts what is
      // stored. Opening a form on a value nobody chose is the bug itself.
      if (v.undecided || v.conflict) {
        setChoose({ id: v.id, accountNo: v.account_no, name: v.name || v.account_no })
        return
      }
      go(v.stored === 'retail' ? 'retail' : 'corporate', v.account_no)
    } catch (e) {
      // an older backend (or a customer with no record) → fall back to the
      // previous behaviour rather than blocking the officer
      try {
        const d: any = await customersApi.detail(q)
        const c = d.customer || {}
        const accountNo = c.account_no || q
        const t = String(c.account_type || '').toLowerCase()
        if (t === 'retail') { go('retail', accountNo); return }
        if (t === 'corporate' || t === 'sme') { go('corporate', accountNo); return }
        setChoose({ id: c.id, accountNo, name: c.name || accountNo })
      } catch (e2) {
        toast.error(parseApiError(e2))
      }
    } finally {
      setLoading(false)
    }
  }

  const pick = async (type: 'retail' | 'corporate') => {
    if (!choose) return
    setLoading(true)
    try {
      if (choose.id) await customersApi.update(choose.id, { account_type: type })
      toast.success(`نوعِ حساب «${type === 'retail' ? 'حقیقی / Retail' : 'حقوقی / Corporate'}» در دیتابیس ثبت شد`)
      go(type, choose.accountNo)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-xl mx-auto mt-10">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Credit File Summary</h1>
        <p className="text-sm text-gray-500 mb-6">خلاصۀ فایلِ اعتباری — شمارۀ حساب را وارد کنید تا فرمِ مناسب باز شود.</p>

        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <label className="block text-sm font-semibold text-gray-700 mb-1.5">Account Number</label>
          <div className="flex gap-2">
            <input
              value={acc}
              onChange={(e) => setAcc(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && detect()}
              placeholder="مثلاً 110151"
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={detect}
              disabled={loading}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold px-4 py-2 rounded-lg"
            >
              <Search size={16} /> {loading ? '...' : 'باز کردن فرم'}
            </button>
          </div>

          {choose && (
            <div className="mt-5 border-t border-gray-100 pt-4">
              <p className="text-sm text-gray-700 mb-3" dir="rtl">
                {verdict?.conflict ? (
                  <>در دیتابیس نوعِ حسابِ «<span className="font-semibold">{choose.name}</span>» (شمارۀ {choose.accountNo}){' '}
                    <span className="font-semibold text-red-600">{verdict.stored === 'retail' ? 'حقیقی' : 'حقوقی'}</span>{' '}
                    ثبت شده، ولی شواهدِ خودِ پرونده چیزِ دیگری می‌گوید. کدام درست است؟ انتخابتان ذخیره می‌شود.</>
                ) : (
                  <>نوعِ حسابِ «<span className="font-semibold">{choose.name}</span>» (شمارۀ {choose.accountNo}) در دیتابیس ثبت نشده.
                    این حساب از کدام دسته است؟ انتخابتان ذخیره می‌شود.</>
                )}
              </p>
              {/* Show the evidence, so the operator decides on facts rather than
                  on a label. A finding nobody can check is not actionable. */}
              {!!verdict?.reasons?.length && (
                <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900" dir="rtl">
                  <div className="font-semibold mb-1">
                    شواهدِ پرونده می‌گوید «{verdict.guess === 'retail' ? 'حقیقی' : 'حقوقی'}»
                    {verdict.confidence === 'high' ? ' (قطعی)' : verdict.confidence === 'medium' ? ' (محتمل)' : ''}:
                  </div>
                  <ul className="list-disc pr-4 space-y-0.5">
                    {verdict.reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                  {!!verdict.counter_reasons?.length && (
                    <div className="mt-2 pt-2 border-t border-amber-200">
                      <div className="font-semibold mb-1">شواهدِ مخالف:</div>
                      <ul className="list-disc pr-4 space-y-0.5">
                        {verdict.counter_reasons.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => pick('retail')}
                  disabled={loading}
                  className="flex flex-col items-center gap-1 border border-gray-300 rounded-lg p-4 hover:border-blue-500 hover:bg-blue-50 disabled:opacity-60"
                >
                  <User className="text-blue-600" size={22} />
                  <span className="font-semibold text-gray-800">Retail</span>
                  <span className="text-xs text-gray-500">حقیقی / فردی</span>
                </button>
                <button
                  onClick={() => pick('corporate')}
                  disabled={loading}
                  className="flex flex-col items-center gap-1 border border-gray-300 rounded-lg p-4 hover:border-blue-500 hover:bg-blue-50 disabled:opacity-60"
                >
                  <Building2 className="text-blue-600" size={22} />
                  <span className="font-semibold text-gray-800">Corporate</span>
                  <span className="text-xs text-gray-500">حقوقی / شرکتی</span>
                </button>
              </div>
            </div>
          )}
        </div>

        <p className="text-xs text-gray-400 mt-4" dir="rtl">
          تشخیص بر اساسِ فیلدِ <code dir="ltr">account_type</code> و شواهدِ خودِ پرونده (جوازِ تجاری، شرکا، نامِ حساب) انجام می‌شود.
          اگر این دو با هم نخوانند یا نوع ثبت نشده باشد، از شما پرسیده می‌شود — هیچ نوعی خودکار عوض نمی‌شود.
          برای دیدنِ همهٔ حساب‌های مشکوک: صفحهٔ «کیفیت داده».
        </p>
      </div>
    </Layout>
  )
}
