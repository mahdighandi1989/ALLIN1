'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { Search, User, Building2 } from 'lucide-react'
import { customersApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'

// Single entry point for the credit-file summary. Enter an account number; the
// customer's account_type (in the DB) decides which form opens — Retail for
// individuals, Corporate for companies/partnerships (corporate|sme). If the type
// isn't recorded yet, the user is asked, the choice is SAVED to the DB, and the
// matching form opens.
export default function CreditFilePage() {
  const router = useRouter()
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [choose, setChoose] = useState<{ id: string; accountNo: string; name: string } | null>(null)

  const go = (type: 'retail' | 'corporate', accountNo: string) => {
    const path = type === 'retail' ? '/credit-file-retail' : '/credit-file-corporate'
    router.push(`${path}/?acc=${encodeURIComponent(accountNo)}`)
  }

  const detect = async () => {
    const q = acc.trim()
    if (!q) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true); setChoose(null)
    try {
      const d: any = await customersApi.detail(q)
      const c = d.customer || {}
      const accountNo = c.account_no || q
      const t = String(c.account_type || '').toLowerCase()
      if (t === 'retail') { go('retail', accountNo); return }
      if (t === 'corporate' || t === 'sme') { go('corporate', accountNo); return }
      // Type not recorded → ask the operator.
      setChoose({ id: c.id, accountNo, name: c.name || accountNo })
    } catch (e) {
      toast.error(parseApiError(e))
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
        <p className="text-sm text-gray-500 mb-6">خلاصهٔ فایلِ اعتباری — شمارهٔ حساب را وارد کنید تا فرمِ مناسب باز شود.</p>

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
                نوعِ حسابِ «<span className="font-semibold">{choose.name}</span>» (شمارهٔ {choose.accountNo}) در دیتابیس ثبت نشده.
                این حساب از کدام دسته است؟ انتخابتان ذخیره می‌شود.
              </p>
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
          تشخیص بر اساس فیلدِ <code dir="ltr">account_type</code> مشتری انجام می‌شود: retail → فرم Retail؛ corporate/sme → فرم Corporate.
        </p>
      </div>
    </Layout>
  )
}
