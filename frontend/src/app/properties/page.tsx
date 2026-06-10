'use client'

// Mortgaged-properties register — now backed by the API (one source shared with
// each customer's Collateral tab). Every row links to its owning customer.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { Building2, Search, Download, ArrowUpDown } from 'lucide-react'
import { propertiesApi, downloadFile, parseApiError, type PropertyRow } from '@/lib/api'
import toast from 'react-hot-toast'

// label + (optional) server sort key. Columns without a server key aren't sortable.
const COLS: { key: keyof PropertyRow; label: string; num?: boolean; sort?: string }[] = [
  { key: 'ac_no', label: 'شماره حساب', sort: 'ac_no' },
  { key: 'customer', label: 'نام مشتری', sort: 'customer' },
  { key: 'deed_no', label: 'شماره سند' },
  { key: 'city', label: 'شهر', sort: 'city' },
  { key: 'zone', label: 'منطقه' },
  { key: 'type', label: 'نوع', sort: 'type' },
  { key: 'age', label: 'عمر' },
  { key: 'land_m2', label: 'زمین (م²)', num: true },
  { key: 'infra_m2', label: 'زیربنا (م²)', num: true },
  { key: 'mortgage_date', label: 'تاریخ ترهین' },
  { key: 'amount', label: 'مبلغ', num: true, sort: 'amount' },
  { key: 'currency', label: 'ارز' },
  { key: 'valuation_date', label: 'تاریخ ارزیابی' },
  { key: 'valuation', label: 'ارزش ارزیابی', num: true, sort: 'valuation' },
  { key: 'owner', label: 'مالک' },
  { key: 'insurance_expiry', label: 'انقضای بیمه' },
]

function fmt(v: any, num?: boolean): string {
  if (v === null || v === '' || v === undefined) return '—'
  if (num && typeof v === 'number') return v.toLocaleString('en-US')
  return String(v)
}

export default function PropertiesPage() {
  const router = useRouter()
  const [q, setQ] = useState('')
  const [city, setCity] = useState('')
  const [type, setType] = useState('')
  const [cur, setCur] = useState('')
  const [sortBy, setSortBy] = useState('customer')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [data, setData] = useState<{ items: PropertyRow[]; total: number; totals: { aed: number; irr: number; customers: number } }>({ items: [], total: 0, totals: { aed: 0, irr: 0, customers: 0 } })
  const [loading, setLoading] = useState(true)
  const [facets, setFacets] = useState<{ cities: string[]; types: string[] }>({ cities: [], types: [] })
  const timer = useRef<any>(null)

  useEffect(() => { propertiesApi.facets().then(setFacets).catch(() => {}) }, [])

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      try {
        setLoading(true)
        setData(await propertiesApi.list({ search: q, city, type, currency: cur, sort_by: sortBy, sort_order: sortDir, page_size: 500 }))
      } catch (e) { toast.error(parseApiError(e)) } finally { setLoading(false) }
    }, 300)
    return () => timer.current && clearTimeout(timer.current)
  }, [q, city, type, cur, sortBy, sortDir])

  const toggleSort = (k?: string) => {
    if (!k) return
    if (k === sortBy) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortBy(k); setSortDir('asc') }
  }

  const exportCsv = async () => {
    const p = new URLSearchParams({ search: q, city, type, currency: cur }).toString()
    try { await downloadFile(`/api/properties/export.csv?${p}`, 'mortgaged-properties.csv') }
    catch (e) { toast.error(parseApiError(e)) }
  }

  const rows = data.items
  const totals = data.totals
  const sel = 'border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      <div dir="rtl" className="max-w-full">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><Building2 size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">املاک رهنی (Mortgaged Properties)</h1>
            <p className="text-gray-500 text-sm">رجیستر تجمیع‌شده — متصل به پروفایلِ هر مشتری · {data.total.toLocaleString('en-US')} ملک</p>
          </div>
        </div>

        {/* summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <Card label="تعداد املاک (فیلترشده)" value={data.total.toLocaleString('en-US')} />
          <Card label="تعداد مشتری" value={totals.customers.toLocaleString('en-US')} />
          <Card label="مجموع ارزش (AED)" value={Math.round(totals.aed).toLocaleString('en-US')} />
          <Card label="مجموع ارزش (IRR)" value={Math.round(totals.irr).toLocaleString('en-US')} />
        </div>

        {/* filters */}
        <div className="flex flex-wrap gap-2 mb-3 items-center">
          <div className="relative flex-1 min-w-[220px]">
            <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="جست‌وجو: مشتری / شماره حساب / سند / مالک / شهر"
              className={`${sel} w-full pr-9`} />
          </div>
          <select className={sel} value={city} onChange={(e) => setCity(e.target.value)}>
            <option value="">همه شهرها</option>{facets.cities.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className={sel} value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">همه انواع</option>{facets.types.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className={sel} value={cur} onChange={(e) => setCur(e.target.value)}>
            <option value="">همه ارزها</option><option value="AED">AED</option><option value="IRR">IRR</option>
          </select>
          <button onClick={exportCsv} type="button" className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-lg px-3 py-2 text-sm">
            <Download size={15} /> CSV
          </button>
        </div>

        {/* table */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-auto" style={{ maxHeight: '70vh' }}>
          <table className="text-xs whitespace-nowrap">
            <thead className="bg-gray-100 sticky top-0">
              <tr>
                {COLS.map((c) => (
                  <th key={c.key} onClick={() => toggleSort(c.sort)}
                    className={`px-2.5 py-2 text-right font-semibold text-gray-700 border-b select-none ${c.sort ? 'cursor-pointer hover:bg-gray-200' : ''}`}>
                    <span className="inline-flex items-center gap-1">{c.label}{c.sort && <ArrowUpDown size={11} className={sortBy === c.sort ? 'text-blue-600' : 'text-gray-400'} />}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id} className="odd:bg-white even:bg-gray-50 hover:bg-blue-50">
                  {COLS.map((c) => (
                    <td key={c.key} className={`px-2.5 py-1.5 border-b border-gray-100 ${c.num ? 'text-left tabular-nums' : 'text-right'}`}>
                      {c.key === 'customer' && p.customer_id ? (
                        <button type="button" onClick={() => router.push(`/customer-detail?id=${p.customer_id}`)} className="text-blue-600 hover:underline">
                          {fmt(p.customer)}
                        </button>
                      ) : fmt(p[c.key], c.num)}
                    </td>
                  ))}
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={COLS.length} className="text-center text-gray-400 py-10">موردی یافت نشد.</td></tr>
              )}
              {loading && (
                <tr><td colSpan={COLS.length} className="text-center text-gray-400 py-10">در حال بارگذاری…</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          روی نامِ هر مشتری بزنید تا مستقیم به پروفایلش بروید. این رجیستر و تبِ «Collateral & Property» در صفحه‌ی مشتری از یک منبعِ واحد در دیتابیس می‌خوانند.
        </p>
      </div>
    </Layout>
  )
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3">
      <div className="text-gray-500 text-xs mb-1">{label}</div>
      <div className="text-lg font-bold text-gray-900 tabular-nums">{value}</div>
    </div>
  )
}
