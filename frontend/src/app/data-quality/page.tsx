'use client'

// v130 — DATA QUALITY (کیفیتِ داده) — one sweep over the whole book.
//
// The owner's report: "the database is full of junk and gaps, and I only find
// out when I fill the Summary form by hand." Two causes: the stored
// «profile completeness» measured 13 items (so it read high while the record was
// half empty), and nothing ever answered "where is my data worst?" across all
// customers at once. This page answers both, from the SAME field spec the Credit
// File Summary form reads — so what it reports and what the form asks for can
// never drift apart.
import React, { useEffect, useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import Link from 'next/link'
import { RefreshCw, ShieldAlert, Search, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import { crmApi, parseApiError, type DataQuality, type DataQualityRow } from '@/lib/api'

const fa = (n: number | string) => String(n).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d])
const SECTION_LABEL: Record<string, string> = {
  identity: 'هویت و پایه', kyc: 'مدارک و KYC', credit: 'اعتباری و بازبینی', records: 'رکوردهای مرتبط',
}

// Traffic-light for a percentage — the same thresholds everywhere on the page.
const tone = (p: number) =>
  p >= 80 ? { bar: 'bg-green-500', text: 'text-green-700', chip: 'bg-green-50 border-green-200 text-green-800' }
  : p >= 50 ? { bar: 'bg-amber-500', text: 'text-amber-700', chip: 'bg-amber-50 border-amber-200 text-amber-800' }
  : { bar: 'bg-red-500', text: 'text-red-700', chip: 'bg-red-50 border-red-200 text-red-800' }

const Bar = ({ percent }: { percent: number }) => (
  <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
    <div className={`h-full ${tone(percent).bar}`} style={{ width: `${Math.max(2, percent)}%` }} />
  </div>
)

export default function DataQualityPage() {
  const [data, setData] = useState<DataQuality | null>(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [type, setType] = useState<'' | 'corporate' | 'retail'>('')
  const [gapField, setGapField] = useState('')   // filter: only rows missing THIS field

  const load = async () => {
    setBusy(true)
    try { setData(await crmApi.dataQuality()) }
    catch (e) { toast.error(parseApiError(e)) }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [])

  const rows = useMemo(() => {
    let list: DataQualityRow[] = data?.customers || []
    const needle = q.trim().toLowerCase()
    if (needle) list = list.filter((c) => `${c.account_no} ${c.name} ${c.branch}`.toLowerCase().includes(needle))
    if (type) list = list.filter((c) => c.account_type === type)
    if (gapField) {
      const label = (data?.common_gaps || []).find((g) => g.field === gapField)?.label || ''
      list = list.filter((c) => c.top_missing.includes(label))
    }
    return list
  }, [data, q, type, gapField])

  const worst = (data?.customers || []).filter((c) => c.percent < 50).length

  return (
    <Layout>
      <div dir="rtl" className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-rose-600 text-white rounded-xl p-2.5"><ShieldAlert size={22} /></div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">کیفیتِ داده</h1>
            <p className="text-gray-500 text-sm">
              همان فیلدهایی که فرمِ «خلاصهٔ فایلِ اعتباری» لازم دارد، روی <b>کلِ مشتری‌ها</b> سنجیده می‌شود —
              تا قبل از رسیدن به فرم بدانی کجا ناقص است.
            </p>
          </div>
          <button onClick={load} disabled={busy}
            className="flex items-center gap-2 bg-gray-700 hover:bg-gray-800 disabled:opacity-60 text-white rounded-lg px-3 py-2 text-sm">
            <RefreshCw size={15} className={busy ? 'animate-spin' : ''} /> به‌روزرسانی
          </button>
        </div>

        {!data && busy && <div className="text-sm text-gray-500 mt-6">در حالِ محاسبه…</div>}

        {data && (
          <>
            {/* headline numbers */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="text-[12px] text-gray-500">مشتری‌های بررسی‌شده</div>
                <div className="text-2xl font-bold text-gray-900">{fa(data.total_customers)}</div>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="text-[12px] text-gray-500">میانگینِ کاملی</div>
                <div className={`text-2xl font-bold ${tone(data.average_percent).text}`}>{fa(data.average_percent)}٪</div>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="text-[12px] text-gray-500">زیرِ ۵۰٪</div>
                <div className="text-2xl font-bold text-red-700">{fa(worst)}</div>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-4">
                <div className="text-[12px] text-gray-500">ضعیف‌ترین بخش</div>
                <div className="text-base font-bold text-gray-900">
                  {data.sections.length
                    ? `${SECTION_LABEL[[...data.sections].sort((a, b) => a.percent - b.percent)[0].key]} · ${fa([...data.sections].sort((a, b) => a.percent - b.percent)[0].percent)}٪`
                    : '—'}
                </div>
              </div>
            </div>

            {/* per-section averages */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 mt-4">
              <div className="text-sm font-semibold text-gray-800 mb-3">وضعیتِ هر بخش روی کلِ دیتابیس</div>
              <div className="grid md:grid-cols-2 gap-x-6 gap-y-3">
                {data.sections.map((s) => (
                  <div key={s.key}>
                    <div className="flex justify-between text-[12.5px] mb-1">
                      <span className="text-gray-700">{s.title}</span>
                      <span className={tone(s.percent).text}>{fa(s.percent)}٪ ({fa(s.filled)} از {fa(s.total)})</span>
                    </div>
                    <Bar percent={s.percent} />
                  </div>
                ))}
              </div>
            </div>

            {/* the single most actionable list: which field is missing most often */}
            <div className="bg-white border border-gray-200 rounded-xl p-4 mt-4">
              <div className="text-sm font-semibold text-gray-800 mb-1">بیشترین فیلدهای جاافتاده</div>
              <div className="text-[11.5px] text-gray-500 mb-3">
                روی هر مورد بزن تا فقط مشتری‌هایی که همان را ندارند در فهرستِ پایین بمانند.
              </div>
              <div className="flex flex-wrap gap-2">
                {data.common_gaps.slice(0, 24).map((g) => (
                  <button key={g.field} onClick={() => setGapField(gapField === g.field ? '' : g.field)}
                    className={`text-[12px] rounded-full border px-3 py-1 transition-colors ${
                      gapField === g.field ? 'bg-rose-600 border-rose-600 text-white' : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'}`}
                    title={g.section_title}>
                    {g.label} <b>{fa(g.count)}</b>
                  </button>
                ))}
                {!data.common_gaps.length && <span className="text-sm text-gray-500">هیچ فیلدِ جاافتاده‌ای نیست 🎉</span>}
              </div>
            </div>

            {/* the customers themselves, worst first */}
            <div className="bg-white border border-gray-200 rounded-xl mt-4 overflow-hidden">
              <div className="flex flex-wrap items-center gap-2 p-3 border-b border-gray-100">
                <div className="text-sm font-semibold text-gray-800 ml-auto">مشتری‌ها — ناقص‌ترین در بالا</div>
                {gapField && (
                  <button onClick={() => setGapField('')} className="text-[12px] text-rose-700 hover:underline flex items-center gap-1">
                    <ArrowLeft size={12} /> برداشتنِ فیلترِ فیلد
                  </button>
                )}
                <select value={type} onChange={(e) => setType(e.target.value as any)}
                  className="border border-gray-300 rounded-md px-2 py-1.5 text-sm">
                  <option value="">همه</option>
                  <option value="corporate">حقوقی</option>
                  <option value="retail">حقیقی</option>
                </select>
                <div className="relative">
                  <Search size={14} className="absolute right-2 top-2.5 text-gray-400" />
                  <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="حساب، نام یا شعبه…"
                    className="border border-gray-300 rounded-md pr-7 pl-2 py-1.5 text-sm w-56" />
                </div>
              </div>

              <div className="divide-y divide-gray-100">
                {rows.slice(0, 300).map((c) => (
                  <Link key={c.account_no} href={`/customer-detail?account=${encodeURIComponent(c.account_no)}`}
                    className="flex flex-wrap items-center gap-3 px-3 py-2.5 hover:bg-gray-50">
                    <span className={`text-sm font-bold w-12 text-center ${tone(c.percent).text}`}>{fa(c.percent)}٪</span>
                    <span className="w-28"><Bar percent={c.percent} /></span>
                    <span className="text-sm text-gray-900 font-medium min-w-[9rem]">{c.name || '—'}</span>
                    <span className="text-[12px] text-gray-500" dir="ltr">{c.account_no}</span>
                    <span className={`text-[11px] rounded border px-1.5 py-0.5 ${c.account_type === 'retail' ? 'bg-sky-50 border-sky-200 text-sky-800' : 'bg-violet-50 border-violet-200 text-violet-800'}`}>
                      {c.account_type === 'retail' ? 'حقیقی' : 'حقوقی'}
                    </span>
                    <span className={`text-[11px] rounded border px-1.5 py-0.5 ${tone(c.percent).chip}`}>
                      {fa(c.missing_count)} قلم جاافتاده
                    </span>
                    <span className="text-[11.5px] text-gray-500 flex-1 truncate">
                      {c.top_missing.join('، ')}{c.missing_count > c.top_missing.length ? ' …' : ''}
                    </span>
                  </Link>
                ))}
                {!rows.length && <div className="px-3 py-6 text-sm text-gray-500 text-center">موردی با این فیلترها نیست.</div>}
              </div>
              {rows.length > 300 && (
                <div className="px-3 py-2 text-[12px] text-gray-500 border-t border-gray-100">
                  {fa(rows.length)} مورد پیدا شد؛ ۳۰۰ موردِ ناقص‌ترین نشان داده شد — با جست‌وجو محدودترش کن.
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}
