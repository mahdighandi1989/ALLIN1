'use client'

import { useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Building2, Search, Download, ArrowUpDown } from 'lucide-react'
import { PROPERTIES, type Property } from './data'

const COLS: { key: keyof Property; label: string; num?: boolean }[] = [
  { key: 'ac_no', label: 'شماره حساب' },
  { key: 'customer', label: 'نام مشتری' },
  { key: 'deed_no', label: 'شماره سند' },
  { key: 'city', label: 'شهر' },
  { key: 'zone', label: 'منطقه' },
  { key: 'type', label: 'نوع' },
  { key: 'age', label: 'عمر' },
  { key: 'land_m2', label: 'زمین (م²)', num: true },
  { key: 'infra_m2', label: 'زیربنا (م²)', num: true },
  { key: 'mortgage_date', label: 'تاریخ ترهین' },
  { key: 'amount', label: 'مبلغ', num: true },
  { key: 'currency', label: 'ارز' },
  { key: 'valuation_date', label: 'تاریخ ارزیابی' },
  { key: 'valuation', label: 'ارزش ارزیابی', num: true },
  { key: 'owner', label: 'مالک' },
  { key: 'insurance_expiry', label: 'انقضای بیمه' },
]

function fmt(v: string | number | null, num?: boolean): string {
  if (v === null || v === '' || v === undefined) return '—'
  if (num && typeof v === 'number') return v.toLocaleString('en-US')
  return String(v)
}

export default function PropertiesPage() {
  const [q, setQ] = useState('')
  const [city, setCity] = useState('')
  const [type, setType] = useState('')
  const [cur, setCur] = useState('')
  const [sortKey, setSortKey] = useState<keyof Property>('customer')
  const [sortDir, setSortDir] = useState<1 | -1>(1)

  const cities = useMemo(() => Array.from(new Set(PROPERTIES.map((p) => p.city).filter(Boolean))).sort(), [])
  const types = useMemo(() => Array.from(new Set(PROPERTIES.map((p) => p.type).filter(Boolean))).sort(), [])

  const rows = useMemo(() => {
    const ql = q.trim().toLowerCase()
    let r = PROPERTIES.filter((p) => {
      if (city && p.city !== city) return false
      if (type && p.type !== type) return false
      if (cur && p.currency !== cur) return false
      if (ql) {
        const hay = `${p.ac_no} ${p.customer} ${p.deed_no} ${p.owner} ${p.city}`.toLowerCase()
        if (!hay.includes(ql)) return false
      }
      return true
    })
    r = [...r].sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey]
      if (av === null || av === '') return 1
      if (bv === null || bv === '') return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * sortDir
      return String(av).localeCompare(String(bv)) * sortDir
    })
    return r
  }, [q, city, type, cur, sortKey, sortDir])

  const totals = useMemo(() => {
    const sum = (c: string) => rows.filter((p) => p.currency === c).reduce((s, p) => s + (p.valuation || 0), 0)
    return { aed: sum('AED'), irr: sum('IRR'), customers: new Set(rows.map((p) => p.customer)).size }
  }, [rows])

  const toggleSort = (k: keyof Property) => {
    if (k === sortKey) setSortDir((d) => (d === 1 ? -1 : 1))
    else { setSortKey(k); setSortDir(1) }
  }

  const exportCsv = () => {
    const head = COLS.map((c) => c.label).join(',')
    const body = rows.map((p) => COLS.map((c) => {
      const v = p[c.key]
      const s = v === null ? '' : String(v)
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
    }).join(',')).join('\n')
    const blob = new Blob(['﻿' + head + '\n' + body], { type: 'text/csv;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'mortgaged-properties.csv'
    a.click()
  }

  const sel = 'border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      <div dir="rtl" className="max-w-full">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><Building2 size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">املاک رهنی (Mortgaged Properties)</h1>
            <p className="text-gray-500 text-sm">رجیستر تجمیع‌شده و پاک‌سازی‌شده — {PROPERTIES.length} ملک</p>
          </div>
        </div>

        {/* summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
          <Card label="تعداد املاک (فیلترشده)" value={rows.length.toLocaleString('en-US')} />
          <Card label="تعداد مشتری" value={totals.customers.toLocaleString('en-US')} />
          <Card label="مجموع ارزش (AED)" value={totals.aed.toLocaleString('en-US')} />
          <Card label="مجموع ارزش (IRR)" value={totals.irr.toLocaleString('en-US')} />
        </div>

        {/* filters */}
        <div className="flex flex-wrap gap-2 mb-3 items-center">
          <div className="relative flex-1 min-w-[220px]">
            <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="جست‌وجو: مشتری / شماره حساب / سند / مالک / شهر"
              className={`${sel} w-full pr-9`} />
          </div>
          <select className={sel} value={city} onChange={(e) => setCity(e.target.value)}>
            <option value="">همه شهرها</option>{cities.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className={sel} value={type} onChange={(e) => setType(e.target.value)}>
            <option value="">همه انواع</option>{types.map((t) => <option key={t} value={t}>{t}</option>)}
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
                  <th key={c.key} onClick={() => toggleSort(c.key)}
                    className="px-2.5 py-2 text-right font-semibold text-gray-700 border-b cursor-pointer hover:bg-gray-200 select-none">
                    <span className="inline-flex items-center gap-1">{c.label}<ArrowUpDown size={11} className="text-gray-400" /></span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((p, i) => (
                <tr key={i} className={i % 2 ? 'bg-gray-50' : 'bg-white'}>
                  {COLS.map((c) => (
                    <td key={c.key} className={`px-2.5 py-1.5 border-b border-gray-100 ${c.num ? 'text-left tabular-nums' : 'text-right'}`}>
                      {fmt(p[c.key], c.num)}
                    </td>
                  ))}
                </tr>
              ))}
              {rows.length === 0 && (
                <tr><td colSpan={COLS.length} className="text-center text-gray-400 py-10">موردی یافت نشد.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          منبع: شیت «تهران و شهرستان» از فایل Head Office (canonical). نوع ملک و املای شهرها یکدست شد، مقادیر «-» پاک شد، شیت تکراری «شهرستان» کنار گذاشته شد.
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
