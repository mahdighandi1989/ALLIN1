'use client'

// Daily log — smart routing (A22). Write what you did today in free text; any
// 6-digit account number is detected (a number followed by a currency word is
// treated as an amount, not an account), matched to a customer, and routed to
// them as a follow-up task. A journal entry is always recorded.
import { useState } from 'react'
import Layout from '@/components/Layout'
import { crmApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import { ClipboardList, Send } from 'lucide-react'

export default function DailyLogPage() {
  const [text, setText] = useState('')
  const [followup, setFollowup] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<any>(null)

  const submit = async () => {
    if (!text.trim()) return
    setBusy(true)
    try {
      const r = await crmApi.dailyLog(text.trim(), followup)
      setResult(r)
      toast.success(`Logged · routed to ${r.routed.length} account(s)`)
      setText('')
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy(false) }
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-1">
        <ClipboardList size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">Daily Log</h2>
      </div>
      <p className="text-xs text-gray-400 mb-5">هرچه امروز انجام دادید را بنویسید. شماره‌حساب‌های ۶‌رقمیِ موجود در متن، به‌صورتِ خودکار به همان مشتری به‌عنوان تسک منتقل می‌شوند (عددی که بلافاصله بعدش واحد پول بیاید، مبلغ تلقی می‌شود نه حساب).</p>

      <div className="max-w-3xl space-y-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <textarea value={text} dir="auto" onChange={(e) => setText(e.target.value)} rows={4}
            placeholder="مثلاً: پیگیری 182255 بابت تمدید؛ دریافت 500000 درهم؛ ارسال نامه به 200145"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" style={{ fontFamily: "'B Nazanin', Tahoma, sans-serif", fontSize: 14 }} />
          <div className="flex items-center gap-2 mt-2">
            <label className="text-xs text-gray-500">Follow-up:</label>
            <input type="date" value={followup} onChange={(e) => setFollowup(e.target.value)} className="border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm" />
            <span className="flex-1" />
            <button onClick={submit} disabled={busy} type="button" className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg px-4 py-1.5 text-sm font-medium">
              <Send size={14} /> {busy ? 'Saving…' : 'Log it'}
            </button>
          </div>
        </div>

        {result && (
          <div className="bg-white rounded-lg shadow-sm p-4 text-sm space-y-2">
            <div><b>Accounts found:</b> {result.accounts_found.length ? result.accounts_found.join('، ') : '—'}</div>
            <div>
              <b className="text-green-700">Routed:</b>{' '}
              {result.routed.length ? result.routed.map((r: any) => `${r.account_no} (${r.customer_name || '—'})`).join('، ') : '—'}
            </div>
            {result.unknown_accounts.length > 0 && (
              <div className="text-amber-700">
                <b>Unknown (not in database):</b> {result.unknown_accounts.join('، ')} — اگر واقعاً شماره‌حساب‌اند، ابتدا در «Customers» ثبتشان کنید.
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
