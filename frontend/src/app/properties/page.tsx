'use client'

// Mortgaged-properties register — now backed by the API (one source shared with
// each customer's Collateral tab). Every row links to its owning customer.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { Building2, Search, Download, ArrowUpDown, Plus, Pencil, Trash2, X } from 'lucide-react'
import { propertiesApi, downloadFile, parseApiError, type PropertyRow } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import toast from 'react-hot-toast'

// Editable fields for the create/edit form (key + label + numeric flag).
const FORM_FIELDS: { key: string; label: string; num?: boolean }[] = [
  { key: 'account_no', label: 'شماره حساب *' },
  { key: 'customer_name', label: 'نام مشتری' },
  { key: 'mortgage_deed_no', label: 'شماره سند' },
  { key: 'city', label: 'شهر' },
  { key: 'zone', label: 'منطقه' },
  { key: 'prop_type', label: 'نوع ملک' },
  { key: 'owner', label: 'مالک' },
  { key: 'building_age', label: 'عمر ساختمان' },
  { key: 'land_area', label: 'مساحت زمین (م²)' },
  { key: 'infra_area', label: 'مساحت زیربنا (م²)' },
  { key: 'address', label: 'نشانی' },
  { key: 'mortgage_date', label: 'تاریخ ترهین' },
  { key: 'mortgage_amount', label: 'مبلغ ترهین', num: true },
  { key: 'valuation', label: 'ارزش ارزیابی', num: true },
  { key: 'last_valuation_date', label: 'تاریخ ارزیابی' },
  { key: 'insurance_expiry', label: 'انقضای بیمه' },
  { key: 'remarks', label: 'توضیحات' },
]

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
  const { user, authDisabled } = useAuth()
  const canEdit = authDisabled || user?.role === 'admin' || user?.role === 'editor' || !!user?.is_admin
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
  // Create/edit form state. `editing` holds the row id being edited (or '' for new).
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<string>('')
  const [form, setForm] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState(false)

  useEffect(() => { propertiesApi.facets().then(setFacets).catch(() => {}) }, [])

  const reload = async () => {
    try {
      setLoading(true)
      setData(await propertiesApi.list({ search: q, city, type, currency: cur, sort_by: sortBy, sort_order: sortDir, page_size: 500 }))
    } catch (e) { toast.error(parseApiError(e)) } finally { setLoading(false) }
  }

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(reload, 300)
    return () => timer.current && clearTimeout(timer.current)
  }, [q, city, type, cur, sortBy, sortDir])

  const openNew = () => { setEditing(''); setForm({ valuation_currency: 'AED' }); setShowForm(true) }
  const openEdit = async (row: PropertyRow) => {
    // The list row is a summary; map its fields back into the editable form.
    setEditing(row.id)
    setForm({
      account_no: row.ac_no || '', customer_name: row.customer || '', mortgage_deed_no: row.deed_no || '',
      city: row.city || '', zone: row.zone || '', prop_type: row.type || '', owner: row.owner || '',
      building_age: row.age || '', land_area: row.land_m2 || '', infra_area: row.infra_m2 || '',
      mortgage_date: row.mortgage_date || '', mortgage_amount: row.amount != null ? String(row.amount) : '',
      valuation: row.valuation != null ? String(row.valuation) : '', last_valuation_date: row.valuation_date || '',
      insurance_expiry: row.insurance_expiry || '', valuation_currency: row.currency || 'AED',
    })
    setShowForm(true)
  }
  const saveForm = async () => {
    if (!editing && !(form.account_no || '').trim()) { toast.error('شماره حساب الزامی است'); return }
    setSaving(true)
    try {
      const body: Record<string, any> = { ...form }
      if (body.valuation) body.valuation = Number(body.valuation)
      if (body.mortgage_amount) body.mortgage_amount = Number(body.mortgage_amount)
      if (editing) await propertiesApi.update(editing, body)
      else await propertiesApi.create(body)
      toast.success(editing ? 'ملک ویرایش شد' : 'ملک ثبت شد و به پروفایلِ مشتری متصل شد')
      setShowForm(false)
      await reload()
    } catch (e) { toast.error(parseApiError(e)) } finally { setSaving(false) }
  }
  const removeRow = async (row: PropertyRow) => {
    if (!confirm(`حذف ملکِ «${row.deed_no || row.city || row.id}»؟`)) return
    try { await propertiesApi.remove(row.id); toast.success('ملک حذف شد'); await reload() }
    catch (e) { toast.error(parseApiError(e)) }
  }

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
          {canEdit && (
            <button onClick={openNew} type="button" className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm">
              <Plus size={15} /> ملک جدید
            </button>
          )}
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
                {canEdit && <th className="px-2.5 py-2 text-center font-semibold text-gray-700 border-b">عملیات</th>}
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
                  {canEdit && (
                    <td className="px-2.5 py-1.5 border-b border-gray-100 text-center whitespace-nowrap">
                      <button type="button" onClick={() => openEdit(p)} title="ویرایش" className="text-gray-500 hover:text-blue-600 p-1"><Pencil size={14} /></button>
                      <button type="button" onClick={() => removeRow(p)} title="حذف" className="text-gray-500 hover:text-red-600 p-1"><Trash2 size={14} /></button>
                    </td>
                  )}
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={COLS.length + (canEdit ? 1 : 0)} className="text-center text-gray-400 py-10">موردی یافت نشد.</td></tr>
              )}
              {loading && (
                <tr><td colSpan={COLS.length + (canEdit ? 1 : 0)} className="text-center text-gray-400 py-10">در حال بارگذاری…</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          روی نامِ هر مشتری بزنید تا مستقیم به پروفایلش بروید. این رجیستر و تبِ «Collateral & Property» در صفحه‌ی مشتری از یک منبعِ واحد در دیتابیس می‌خوانند. ثبتِ ملک برای شماره‌حسابی که هنوز مشتری ندارد، یک پروفایلِ مشتری می‌سازد تا ملک ذیلِ آن دیده شود.
        </p>

        {/* Create / edit modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between px-5 py-3 border-b sticky top-0 bg-white">
                <h3 className="font-bold text-gray-900">{editing ? 'ویرایش ملک' : 'ثبتِ ملکِ جدید'}</h3>
                <button onClick={() => setShowForm(false)} type="button" className="text-gray-400 hover:text-gray-700"><X size={18} /></button>
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
                {FORM_FIELDS.map((f) => (
                  <div key={f.key}>
                    <label className="block text-xs text-gray-500 mb-1">{f.label}</label>
                    <input
                      value={form[f.key] ?? ''}
                      onChange={(e) => setForm((s) => ({ ...s, [f.key]: e.target.value }))}
                      disabled={f.key === 'account_no' && !!editing}
                      inputMode={f.num ? 'numeric' : undefined}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" />
                  </div>
                ))}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">ارز</label>
                  <select value={form.valuation_currency ?? 'AED'} onChange={(e) => setForm((s) => ({ ...s, valuation_currency: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white">
                    <option value="AED">AED</option><option value="IRR">IRR</option><option value="USD">USD</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 px-5 py-3 border-t sticky bottom-0 bg-white">
                <button onClick={() => setShowForm(false)} type="button" className="px-4 py-2 text-sm rounded-lg bg-gray-100 hover:bg-gray-200">انصراف</button>
                <button onClick={saveForm} disabled={saving} type="button" className="px-4 py-2 text-sm rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50">
                  {saving ? 'در حال ذخیره…' : (editing ? 'ذخیره' : 'ثبت')}
                </button>
              </div>
            </div>
          </div>
        )}
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
