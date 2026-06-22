'use client'

// Shared bits for the Credit File Summary forms (corporate + retail): an
// amount input that auto-inserts thousands separators, a draft (مصوبه) drop
// zone that extracts into the DB, and the property (املاک) two-way-sync save
// (required summary fields enforced, extras optional, upsert by id → no dupes).
import React, { useState } from 'react'
import { Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { crmApi, parseApiError } from '@/lib/api'

export const onlyNum = (s: string): number | undefined => {
  const n = parseFloat(String(s ?? '').replace(/[,/\s]/g, '').replace(/[^\d.-]/g, ''))
  return isNaN(n) ? undefined : n
}

// "8000000" → "8,000,000" (leaves non-numeric text untouched).
export function fmtAmt(s: string | number | null | undefined): string {
  const str = String(s ?? '').trim()
  if (!str) return ''
  const cleaned = str.replace(/,/g, '')
  const m = cleaned.match(/^(-?)(\d*)(\.\d*)?$/)
  if (!m) return str
  const intp = (m[2] || '').replace(/^0+(?=\d)/, '') || '0'
  return (m[1] || '') + intp.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (m[3] || '')
}

// Amount cell: shows grouped digits (1,000,000) whenever it's NOT being edited —
// including values just loaded from the DB / an import — and the raw digits while
// you type, so the cursor stays put. Module-level so it keeps focus while typing.
export function AmtInput({ value, onValue, style }: { value: string; onValue: (v: string) => void; style?: React.CSSProperties }) {
  const [focused, setFocused] = React.useState(false)
  const shown = focused ? String(value ?? '').replace(/,/g, '') : fmtAmt(value)
  return (
    <input
      value={shown}
      inputMode="decimal"
      style={style}
      onFocus={() => setFocused(true)}
      onChange={(e) => onValue(e.target.value)}
      onBlur={(e) => { setFocused(false); onValue(fmtAmt(e.target.value)) }}
    />
  )
}

// Text cell that WRAPS and grows: a textarea that auto-resizes to fit its content
// so long text (notices, remarks, address) is fully visible both on screen and in
// print, instead of being clipped to the single line of an <input>. Styled via
// the forms' `table.cf textarea.wrap-cell` rule to look like the other cells.
export function WrapInput({ value, onChange, placeholder, style }: {
  value: string; onChange: (e: any) => void; placeholder?: string; style?: React.CSSProperties
}) {
  const ref = React.useRef<HTMLTextAreaElement>(null)
  const grow = () => {
    const el = ref.current
    if (el) { el.style.height = 'auto'; el.style.height = `${el.scrollHeight}px` }
  }
  React.useEffect(grow, [value])
  return (
    <textarea
      ref={ref}
      className="wrap-cell"
      value={value || ''}
      placeholder={placeholder}
      rows={1}
      onChange={(e) => { onChange(e); grow() }}
      style={style}
    />
  )
}

// Selectable currencies (per amount, not a column each).
export const CCY = ['AED', 'IRR', 'USD', 'EUR', 'GBP']

// Percentage cell: type a number, the "%" is appended on blur.
export function PctInput({ value, onValue, style }: { value: string; onValue: (v: string) => void; style?: React.CSSProperties }) {
  const fmt = (s: string) => {
    const t = String(s || '').trim()
    if (!t || t.endsWith('%')) return t
    return /^-?\d*\.?\d+$/.test(t) ? `${t}%` : t
  }
  return (
    <input value={value || ''} inputMode="decimal" style={style}
      onChange={(e) => onValue(e.target.value)}
      onBlur={(e) => onValue(fmt(e.target.value))} />
  )
}

// Searchable country list (native datalist → type to filter, custom allowed).
export const COUNTRIES = [
  'United Arab Emirates', 'Iran', 'Saudi Arabia', 'Qatar', 'Kuwait', 'Bahrain', 'Oman',
  'India', 'Pakistan', 'Bangladesh', 'Sri Lanka', 'Nepal', 'Afghanistan', 'Philippines',
  'Egypt', 'Jordan', 'Lebanon', 'Syria', 'Iraq', 'Yemen', 'Sudan', 'Turkey', 'Türkiye',
  'United Kingdom', 'United States', 'Canada', 'Germany', 'France', 'Italy', 'Spain',
  'Netherlands', 'Switzerland', 'Sweden', 'Russia', 'Ukraine', 'China', 'Japan',
  'South Korea', 'Indonesia', 'Malaysia', 'Singapore', 'Thailand', 'Vietnam',
  'Australia', 'New Zealand', 'South Africa', 'Nigeria', 'Kenya', 'Ethiopia', 'Morocco',
  'Algeria', 'Tunisia', 'Libya', 'Somalia', 'Brazil', 'Argentina', 'Mexico',
]
export function CountryDataList() {
  return <datalist id="cf-countries">{COUNTRIES.map((c) => <option key={c} value={c} />)}</datalist>
}
export function CountryInput({ value, onChange }: { value: string; onChange: (e: any) => void }) {
  return <input list="cf-countries" value={value} onChange={onChange} placeholder="جستجوی کشور…" />
}

// ---- Properties (املاک) -------------------------------------------------
export type PropRow = {
  id?: string
  prop_type: string; address: string; city: string
  valuation: string; valuation_currency: string; mortgage_amount: string; mortgage_currency: string
  // extra (optional) — saved to DB, not printed on the one-page summary
  plate_no: string; mortgage_deed_no: string; mortgage_date: string; insurance_expiry: string
  building_age: string; land_area: string; remarks: string
  _open?: boolean
}
export const emptyProp = (): PropRow => ({
  prop_type: '', address: '', city: '',
  valuation: '', valuation_currency: 'AED', mortgage_amount: '', mortgage_currency: 'AED',
  plate_no: '', mortgage_deed_no: '', mortgage_date: '', insurance_expiry: '',
  building_age: '', land_area: '', remarks: '',
})
export const propFromRecord = (p: any): PropRow => ({
  id: p.id,
  prop_type: p.prop_type || '', address: p.address || '', city: p.city || '',
  valuation: p.valuation != null ? fmtAmt(String(p.valuation)) : '',
  valuation_currency: p.valuation_currency || 'AED',
  mortgage_amount: p.mortgage_amount != null ? fmtAmt(String(p.mortgage_amount)) : '',
  mortgage_currency: p.mortgage_currency || 'AED',
  plate_no: p.plate_no || '', mortgage_deed_no: p.mortgage_deed_no || '',
  mortgage_date: p.mortgage_date || '', insurance_expiry: p.insurance_expiry || '',
  building_age: p.building_age || '', land_area: p.land_area || '', remarks: p.remarks || '',
})

// Upsert each non-empty property. Summary-relevant fields (type + valuation) are
// REQUIRED; a row with data but missing them throws (so save is blocked).
// Existing rows (with id) update in place → never duplicated.
export async function savePropertyRows(
  accountNo: string, customerName: string, rows: PropRow[],
): Promise<{ rows: PropRow[]; count: number }> {
  const out = rows.map((r) => ({ ...r }))
  let count = 0
  for (let i = 0; i < out.length; i++) {
    const r = out[i]
    const hasAny = [r.prop_type, r.address, r.city, r.valuation, r.mortgage_amount,
      r.plate_no, r.mortgage_deed_no, r.mortgage_date, r.insurance_expiry, r.remarks]
      .some((v) => String(v || '').trim())
    if (!hasAny) continue
    if (!r.prop_type.trim() || !String(r.valuation).trim()) {
      throw new Error(`ردیف ملک ${i + 1}: «نوع ملک» و «ارزیابی (AED)» اجباری‌اند`)
    }
    const body: Record<string, any> = {
      customer_name: customerName || undefined,
      prop_type: r.prop_type.trim(),
      address: r.address.trim() || undefined,
      city: r.city.trim() || undefined,
      valuation: onlyNum(r.valuation),
      valuation_currency: r.valuation_currency || 'AED',
      mortgage_amount: onlyNum(r.mortgage_amount),
      mortgage_currency: r.mortgage_currency || 'AED',
      plate_no: r.plate_no.trim() || undefined,
      mortgage_deed_no: r.mortgage_deed_no.trim() || undefined,
      mortgage_date: r.mortgage_date.trim() || undefined,
      insurance_expiry: r.insurance_expiry.trim() || undefined,
      building_age: r.building_age.trim() || undefined,
      land_area: r.land_area.trim() || undefined,
      remarks: r.remarks.trim() || undefined,
    }
    if (r.id) {
      await crmApi.updateProperty(r.id, body)
    } else {
      const res = await crmApi.addProperty(accountNo, body)
      if (res?.id) out[i] = { ...r, id: res.id }
    }
    count++
  }
  return { rows: out, count }
}

// ---- Draft (مصوبه) drop zone -------------------------------------------
export function DraftDrop({ accountNo, onExtracted }: { accountNo: string; onExtracted: (r: any) => void }) {
  const [over, setOver] = useState(false)
  const [busy, setBusy] = useState(false)
  const handle = async (file?: File | null) => {
    if (!file) return
    if (!/\.docx$/i.test(file.name)) { toast.error('فقط فایل Word با پسوند .docx'); return }
    setBusy(true)
    try {
      const r = await crmApi.extractDraft(accountNo, file)
      onExtracted(r)
    } catch (e) { toast.error(parseApiError(e)) }
    finally { setBusy(false) }
  }
  return (
    <div
      className="no-print"
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); handle(e.dataTransfer.files?.[0]) }}
      style={{
        flexBasis: '100%', border: `2px dashed ${over ? '#2563eb' : '#cbd5e1'}`,
        background: over ? '#eff6ff' : '#f8fafc', borderRadius: 8, padding: '8px 12px',
        textAlign: 'center', fontSize: 12, color: '#475569', marginTop: 4,
      }}
    >
      <input id="cf-draft" type="file" accept=".docx" style={{ display: 'none' }}
        onChange={(e) => { handle(e.target.files?.[0]); e.currentTarget.value = '' }} />
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
        <Upload size={15} />
        <label htmlFor="cf-draft" style={{ color: '#1d4ed8', fontWeight: 600, cursor: 'pointer' }}>انتخاب فایل پیش‌نویس مصوبه (.docx)</label>
        <span>یا اینجا بکش و رها کن — استخراج هوشمند و ثبت در دیتابیس مشتری</span>
        {busy && <span style={{ color: '#2563eb', fontWeight: 600 }}>⏳ در حال استخراج…</span>}
      </span>
    </div>
  )
}
