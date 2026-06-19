'use client'

// Credit-Committee Approval (مصوبه / draft sanction) — the internal form that is
// printed, taken to the RCC and, once approved, drives the customer's Offer
// Letter. Two variants are auto-selected from the account type (corporate vs
// retail), mirroring the bank's Word templates (EFCO / NAEIMEH). Values are
// two-way synced with the customer profile: they prefill from the DB (incl. what
// the Offer Letter draft-extractor saved) and are saved back, keyed (deduped).
import React, { useState, useEffect, useCallback, useRef } from 'react'
import Layout from '@/components/Layout'
import { Printer, Download, Search, Save, Plus, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { crmApi, parseApiError } from '@/lib/api'
import { BANK_LOGO } from '@/app/voucher/logo'

const today = new Date().toISOString().slice(0, 10)

type Row = Record<string, string>
type Fields = Record<string, string>

const INITIAL: Fields = {
  CustomerName: '', AccountNumber: '', GroupName: 'N/A', BranchName: '', BorrowerType: 'Retail',
  RequestType: 'Interim', RelationshipDate: '', EstablishedSince: '', DateOfReview: today,
  CreditAppNo: '', BusinessActivity: '', ExistingRating: '', ProposedRating: '', RatingNotes: '',
  CAExpiryExisting: '', CAExpiryProposed: '', AuditorName: '',
  Purpose: '', MajorChanges: 'N/A', Background: '', PEP: 'N/A',
  AccountConduct: '', AECBScore: '', CRUFindings: '', CRURecommendation: '',
  MonthlySalary: '',
}

const LIMITS_CORP: Row[] = [
  { type: 'Overdraft', existing: '', os: '', pb: '', pc: '' },
  { type: 'Commercial Loan I', existing: '', os: '', pb: '', pc: '' },
  { type: 'Commercial Loan II', existing: '-', os: '', pb: '', pc: '' },
]
const LIMITS_RETAIL: Row[] = [
  { type: 'Staff Loan', existing: '', os: '', pb: '', pc: '' },
  { type: 'Personal Loan - I', existing: '', os: '', pb: '', pc: '' },
  { type: 'Personal Loan - II', existing: '-', os: '', pb: '', pc: '' },
]
const RECIP_ROWS = ['LC/Contract/Collection', 'Export', 'Guarantee', 'Fixed Deposit', 'Credit Turnover in Current A/c', 'Credit Balance']
const FIN_ROWS = ['Sales', 'Gross Profit', 'Operating Profit', 'Net Profit', 'Gross Profit Margin (%)', 'Net Profit Margin (%)', 'Total Equity', 'Current Ratio']

// Credit-committee members are fixed (verbatim from the bank templates).
const CRU_SIGNERS = [
  ['Salman Meghani', 'Corporate Credit Analyst'],
  ['Sayed Ibrahim', 'Sr. Corporate Credit Analyst'],
  ['Iqbal Ahmed', 'Sr. Officer Corp Credit Analyst'],
  ['Gholamreza Alizadeh', 'C.F Dept In-Charge'],
]
const RCC_SIGNERS = [
  ['GH. Alizadeh', 'HCAD Manager / C.F Dept In-Charge', 'Staff # 75166'],
  ['M. Moshtagh', 'Treasury & Invest. Manager', 'Staff # 29950'],
  ['B. Mohammadi', 'MRSD Br. Manager', 'Staff # 34547'],
  ['H. Pourmohammad', 'SHZR Br. Manager', 'Staff # 34444'],
  ['H. Malek Mohammadi', 'MAIN Br. Manager / Acting Regional Manager', 'Staff # 30531'],
]
const BRANCH_NAMES: Record<string, string> = {
  '2533': 'BUR DUBAI', '2690': 'ABU DHABI', '2776': 'SHARJAH', '2900': 'AJMAN',
  '4350': 'SHEIKH ZAYED ROAD', '2624': 'AL MAKTOUM', '2898': 'MURSHID BAZAR',
  '1741': 'AL AIN', '3535': 'HEAD OFFICE',
}
const fmtBranch = (c?: string) => {
  const s = String(c || '').trim()
  if (!s) return ''
  if (s.includes(' - ')) return s
  return BRANCH_NAMES[s] ? `${BRANCH_NAMES[s]} - ${s}` : s
}

// Bordered editable cell. Defined at module scope (stable identity) so inputs
// keep focus while typing.
function CI({ v, on, area }: { v: string; on: (e: any) => void; area?: boolean }) {
  return area
    ? <textarea value={v} onChange={on} className="sn-in sn-area" rows={2} />
    : <input value={v} onChange={on} className="sn-in" />
}

export default function SanctionPage() {
  const [f, setF] = useState<Fields>(INITIAL)
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isCorp, setIsCorp] = useState(false)
  const [limits, setLimits] = useState<Row[]>(LIMITS_RETAIL)
  const [recip, setRecip] = useState<Row[]>(RECIP_ROWS.map((l) => ({ label: l, y1: '', y2: '' })))
  const [fin, setFin] = useState<Row[]>(FIN_ROWS.map((l) => ({ label: l, y1: '', y2: '', y3: '' })))
  const [guars, setGuars] = useState<Row[]>([{ desc: '', branch: '', account: '', direct: '', indirect: '' }])
  const [banks, setBanks] = useState<Row[]>([{ bank: '', facility: '', amount: '', outstanding: '', security: '' }])

  const set = (k: string) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const setRow = (setter: any) => (i: number, key: string) => (e: any) =>
    setter((rows: Row[]) => rows.map((r, idx) => (idx === i ? { ...r, [key]: e.target.value } : r)))
  const addRow = (setter: any, blank: Row) => () => setter((rows: Row[]) => [...rows, { ...blank }])
  const delRow = (setter: any) => (i: number) => () => setter((rows: Row[]) => rows.filter((_, idx) => idx !== i))

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await crmApi.offerLetterData(a)
      const corp = ['corporate', 'sme'].includes(String(d.AccountType || '').toLowerCase())
      const pd = (d.ProfileData && typeof d.ProfileData === 'object') ? d.ProfileData : {}
      const sv = (pd.sanction && typeof pd.sanction === 'object') ? pd.sanction : {}
      setIsCorp(corp)
      setF((s) => ({
        ...s,
        CustomerName: sv.CustomerName || d.CompanyName || s.CustomerName,
        AccountNumber: sv.AccountNumber || d.AccountNumber || a,
        BranchName: sv.BranchName || fmtBranch(d.Branch) || s.BranchName,
        BorrowerType: sv.BorrowerType || (corp ? 'SME / Corporate' : 'Retail'),
        RelationshipDate: sv.RelationshipDate || pd.relationship_date || s.RelationshipDate,
        EstablishedSince: sv.EstablishedSince || pd.established_since || s.EstablishedSince,
        DateOfReview: sv.DateOfReview || pd.review_date || s.DateOfReview,
        CreditAppNo: sv.CreditAppNo || pd.credit_application_no || s.CreditAppNo,
        BusinessActivity: sv.BusinessActivity || d.BusinessType || pd.business_type || s.BusinessActivity,
        ProposedRating: sv.ProposedRating || d.Rating || s.ProposedRating,
        ExistingRating: sv.ExistingRating || s.ExistingRating,
        RatingNotes: sv.RatingNotes || (pd.proposed_rate ? `Proposed interest rate to be ${pd.proposed_rate}` : s.RatingNotes),
        CAExpiryProposed: sv.CAExpiryProposed || (pd.proposed_tenor ? `${pd.proposed_tenor} months from DOD` : s.CAExpiryProposed),
        Purpose: sv.Purpose || d.Purpose || pd.customer_profile || s.Purpose,
        Background: sv.Background || pd.customer_profile || s.Background,
        AECBScore: sv.AECBScore || pd.aecb_score || s.AECBScore,
        AuditorName: sv.AuditorName || pd.auditor || s.AuditorName,
        MonthlySalary: sv.MonthlySalary || pd.monthly_salary || s.MonthlySalary,
        AccountConduct: sv.AccountConduct || s.AccountConduct,
        CRUFindings: sv.CRUFindings || s.CRUFindings,
        CRURecommendation: sv.CRURecommendation || s.CRURecommendation,
        MajorChanges: sv.MajorChanges || s.MajorChanges,
        PEP: sv.PEP || s.PEP,
      }))
      if (Array.isArray(sv.limits)) setLimits(sv.limits)
      else setLimits(corp ? LIMITS_CORP.map((r) => ({ ...r })) : LIMITS_RETAIL.map((r) => ({ ...r })))
      if (Array.isArray(sv.recip)) setRecip(sv.recip)
      if (Array.isArray(sv.fin)) setFin(sv.fin)
      if (Array.isArray(sv.guars)) setGuars(sv.guars)
      if (Array.isArray(sv.banks)) setBanks(sv.banks)
      toast.success(`«${d.CompanyName || a}» — ${corp ? 'حقوقی' : 'حقیقی'}${Object.keys(sv).length ? ' · بازیابی از ذخیره' : ''}`)
    } catch (e) { toast.error(parseApiError(e)) }
    finally { setLoading(false) }
  }

  const saveForm = async (silent = false) => {
    const a = (acc || f.AccountNumber).trim()
    if (!a) { if (!silent) toast.error('ابتدا حساب را بارگیری کنید'); return false }
    setSaving(true)
    try {
      // First-class persistence: a deduped credit_reviews row + promoted profile
      // columns + the exact snapshot (for restore) — all in one call.
      await crmApi.saveSanction(a, { snapshot: { ...f }, limits, recip, fin, guars, banks })
      if (!silent) toast.success('مصوبه در پروندهٔ مشتری ذخیره شد')
      return true
    } catch (e) { if (!silent) toast.error(parseApiError(e)); return false }
    finally { setSaving(false) }
  }
  const printDoc = async () => { await saveForm(true); setTimeout(() => window.print(), 50) }

  // Auto-fit each printed page (shrink if content overflows A4).
  const printRef = useRef<HTMLDivElement>(null)
  const fitPages = useCallback(() => {
    const root = printRef.current
    if (!root) return
    const MM = 96 / 25.4
    const avail = (297 - 10 - 12 - 10) * MM
    root.querySelectorAll<HTMLElement>('.sn-page').forEach((pg) => {
      const fit = pg.querySelector<HTMLElement>('.sn-fit')
      if (!fit) return
      fit.style.setProperty('zoom', '1')
      if (fit.scrollHeight > avail) fit.style.setProperty('zoom', String(Math.max(0.55, avail / fit.scrollHeight)))
    })
  }, [])
  useEffect(() => { fitPages() })
  useEffect(() => {
    const on = () => fitPages()
    window.addEventListener('beforeprint', on)
    const t = setTimeout(on, 350)
    return () => { window.removeEventListener('beforeprint', on); clearTimeout(t) }
  }, [fitPages])

  const rccCols = RCC_SIGNERS

  return (
    <Layout>
      <style>{`
        .sn-page { box-sizing:border-box; width:210mm; min-height:297mm; background:#fff; margin:0 auto 8mm;
                   padding:10mm 12mm 10mm; color:#111; font-family:"Times New Roman",Georgia,serif; font-size:9pt;
                   line-height:1.25; box-shadow:0 1px 6px rgba(0,0,0,.12); position:relative; }
        .sn-fit { transform-origin:top left; }
        .sn-hd { display:flex; align-items:center; gap:4mm; border-bottom:2px solid #0a3d91; padding-bottom:2mm; margin-bottom:2mm; }
        .sn-hd img { height:13mm; }
        .sn-hd .t { flex:1; text-align:center; }
        .sn-hd .t b { font-size:13pt; color:#0a3d91; letter-spacing:.5px; }
        .sn-hd .t div { font-size:8pt; color:#444; }
        .sn-tbl { width:100%; border-collapse:collapse; margin:1.5mm 0; }
        .sn-tbl td, .sn-tbl th { border:1px solid #000; padding:0; font-size:8.2pt; vertical-align:middle; }
        .sn-tbl th { background:#e8eefc; font-family:Arial,sans-serif; padding:1mm; text-align:center; }
        .sn-lbl { background:#eef1f7; font-weight:600; padding:1mm 1.5mm; width:24%; }
        .sn-bar { background:#1f3864; color:#fff; font-weight:700; text-align:center; padding:1mm; font-size:8.6pt; }
        .sn-in { width:100%; border:none; padding:1mm 1.5mm; font:inherit; background:#fffef2; }
        .sn-in:focus { outline:2px solid #93c5fd; }
        .sn-area { resize:vertical; min-height:8mm; }
        .sn-sech { font-weight:700; background:#eef1f7; padding:1mm 1.5mm; border:1px solid #000; }
        .sn-sign { display:flex; justify-content:space-between; gap:4mm; margin-top:6mm; text-align:center; font-size:8pt; }
        .sn-sign .col { flex:1; }
        .sn-sign .ln { border-top:1px solid #000; margin-bottom:1mm; }
        .sn-addbtn { font-size:11px; color:#1d4ed8; }
        @media print {
          @page { size:A4 portrait; margin:0; }
          html, body, .min-h-screen { margin:0!important; padding:0!important; min-height:0!important; background:#fff!important; }
          .sn-page { margin:0!important; box-shadow:none!important; page-break-after:always; }
          .sn-page:last-child { page-break-after:auto; }
          .sn-tbl, .sn-sign { page-break-inside:avoid; }
          .sn-in, .sn-area { background:#fff!important; }
          #sn-controls, .sn-rowdel, .sn-addrow { display:none!important; }
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        {/* controls */}
        <div id="sn-controls" className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-blue-600 text-white rounded-lg p-2"><Printer size={18} /></div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Credit Approval — مصوبه / پیش‌نویس مصوبه</h1>
              <p className="text-gray-500 text-xs">شماره‌حساب را وارد کن؛ فرم بر اساس نوع حساب (حقیقی/حقوقی) ساخته می‌شود، از دیتابیس پر و هنگام ذخیره/چاپ در پروندهٔ مشتری به‌روزرسانی می‌شود.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-end gap-2 bg-blue-50 border border-blue-100 rounded-lg p-3">
            <label className="flex-1 min-w-[160px]">
              <span className="text-[11px] text-gray-500">Account No</span>
              <input value={acc} onChange={(e) => setAcc(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && loadAccount()}
                placeholder="مثلاً 127987" className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <button onClick={loadAccount} disabled={loading} type="button" className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Search size={15} /> {loading ? '...' : 'بارگیری'}
            </button>
            <span className="text-xs text-gray-500">نوع: <b>{isCorp ? 'حقوقی (Corporate)' : 'حقیقی (Retail)'}</b></span>
            <button onClick={() => saveForm()} disabled={saving} type="button" className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Save size={15} /> {saving ? '...' : 'ذخیره'}
            </button>
            <button onClick={printDoc} type="button" className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Download size={15} /> Print / PDF
            </button>
          </div>
          <p className="text-[11px] text-gray-400 mt-2">همهٔ سلول‌های زرد قابل ویرایش‌اند. ردیف‌های جدول (تسهیلات، ضامن‌ها، بانک‌ها) با + اضافه و با × حذف می‌شوند.</p>
        </div>

        {/* ===== printable document ===== */}
        <div ref={printRef} dir="ltr">
          {/* -------- PAGE 1 -------- */}
          <div className="sn-page">
            <div className="sn-fit">
              <div className="sn-hd">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={BANK_LOGO} alt="BSI" />
                <div className="t">
                  <b>BANK SADERAT IRAN — U.A.E.</b>
                  <div>Credit Review Unit (CRU) / Regional Credit Committee (RCC) — Credit Approval</div>
                </div>
              </div>

              {/* summary */}
              <table className="sn-tbl"><tbody>
                <tr>
                  <td className="sn-lbl">Customer Name</td><td><CI v={f.CustomerName} on={set('CustomerName')} /></td>
                  <td className="sn-lbl">Branch Name</td><td><CI v={f.BranchName} on={set('BranchName')} /></td>
                </tr>
                <tr>
                  <td className="sn-lbl">Account Number</td><td><CI v={f.AccountNumber} on={set('AccountNumber')} /></td>
                  <td className="sn-lbl">{isCorp ? 'Group Name' : 'Relationship Date'}</td>
                  <td>{isCorp ? <CI v={f.GroupName} on={set('GroupName')} /> : <CI v={f.RelationshipDate} on={set('RelationshipDate')} />}</td>
                </tr>
                <tr>
                  <td className="sn-lbl">Borrower Type</td><td><CI v={f.BorrowerType} on={set('BorrowerType')} /></td>
                  <td className="sn-lbl">Request Type</td><td><CI v={f.RequestType} on={set('RequestType')} /></td>
                </tr>
                <tr>
                  <td className="sn-lbl">CA Expiry (Existing)</td><td><CI v={f.CAExpiryExisting} on={set('CAExpiryExisting')} /></td>
                  <td className="sn-lbl">CA Expiry (Proposed)</td><td><CI v={f.CAExpiryProposed} on={set('CAExpiryProposed')} /></td>
                </tr>
                <tr>
                  <td className="sn-lbl">Date of Review</td><td><CI v={f.DateOfReview} on={set('DateOfReview')} /></td>
                  <td className="sn-lbl">{isCorp ? 'Credit Application #' : 'Loan Application #'}</td><td><CI v={f.CreditAppNo} on={set('CreditAppNo')} /></td>
                </tr>
                <tr>
                  <td className="sn-lbl">Business Activity</td><td><CI v={f.BusinessActivity} on={set('BusinessActivity')} /></td>
                  <td className="sn-lbl">{isCorp ? 'Established Since' : 'Monthly Salary (AED)'}</td>
                  <td>{isCorp ? <CI v={f.EstablishedSince} on={set('EstablishedSince')} /> : <CI v={f.MonthlySalary} on={set('MonthlySalary')} />}</td>
                </tr>
                <tr>
                  <td className="sn-lbl">Existing Rating</td><td><CI v={f.ExistingRating} on={set('ExistingRating')} /></td>
                  <td className="sn-lbl">Proposed Rating</td><td><CI v={f.ProposedRating} on={set('ProposedRating')} /></td>
                </tr>
                <tr>
                  <td className="sn-lbl">Pricing / Rating Notes</td><td colSpan={3}><CI v={f.RatingNotes} on={set('RatingNotes')} area /></td>
                </tr>
              </tbody></table>

              {/* limit structure */}
              <div className="sn-sech">Limit Structure — Amounts in “AED”</div>
              <table className="sn-tbl"><thead><tr>
                <th>Facility Type</th><th>Existing Limit</th><th>O/s</th><th>Proposed (Business)</th><th>Proposed (CRU/RISK)</th><th className="sn-rowdel"></th>
              </tr></thead><tbody>
                {limits.map((r, i) => (
                  <tr key={i}>
                    <td><input value={r.type} onChange={setRow(setLimits)(i, 'type')} className="sn-in" /></td>
                    <td><input value={r.existing} onChange={setRow(setLimits)(i, 'existing')} className="sn-in" /></td>
                    <td><input value={r.os} onChange={setRow(setLimits)(i, 'os')} className="sn-in" /></td>
                    <td><input value={r.pb} onChange={setRow(setLimits)(i, 'pb')} className="sn-in" /></td>
                    <td><input value={r.pc} onChange={setRow(setLimits)(i, 'pc')} className="sn-in" /></td>
                    <td className="sn-rowdel" style={{ width: '7mm', textAlign: 'center' }}><button onClick={delRow(setLimits)(i)} type="button" className="text-red-500"><X size={12} /></button></td>
                  </tr>
                ))}
              </tbody></table>
              <button onClick={addRow(setLimits, { type: '', existing: '', os: '', pb: '', pc: '' })} type="button" className="sn-addrow sn-addbtn flex items-center gap-1"><Plus size={12} /> ردیف تسهیلات</button>

              {/* business reciprocity */}
              <div className="sn-sech" style={{ marginTop: '2mm' }}>Business Reciprocity with BSI-UAE (AED)</div>
              <table className="sn-tbl"><thead><tr><th style={{ width: '46%' }}></th><th>2025 (Jan–Dec)</th><th>2026 (Jan–Date)</th></tr></thead><tbody>
                {recip.map((r, i) => (
                  <tr key={i}><td className="sn-lbl">{r.label}</td>
                    <td><input value={r.y1} onChange={setRow(setRecip)(i, 'y1')} className="sn-in" /></td>
                    <td><input value={r.y2} onChange={setRow(setRecip)(i, 'y2')} className="sn-in" /></td></tr>
                ))}
              </tbody></table>

              {/* purpose / changes / background */}
              <div className="sn-sech" style={{ marginTop: '2mm' }}>Purpose</div>
              <CI v={f.Purpose} on={set('Purpose')} area />
              <div className="sn-sech">Major Changes in Terms &amp; Conditions (incl. Pricing)</div>
              <CI v={f.MajorChanges} on={set('MajorChanges')} area />
              <div className="sn-sech">{isCorp ? 'Brief Company Background / Ownership / Group Profile' : 'Customer Profile'}</div>
              <CI v={f.Background} on={set('Background')} area />
              <div className="sn-sech">Any PEP (Yes/No — details if Yes)</div>
              <CI v={f.PEP} on={set('PEP')} />
            </div>
            <div className="sn-fit" style={{ position: 'absolute', bottom: '5mm', right: '12mm', fontSize: '7.5pt', color: '#666' }}>Page 1 of 2</div>
          </div>

          {/* -------- PAGE 2 -------- */}
          <div className="sn-page">
            <div className="sn-fit">
              <div className="sn-hd">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={BANK_LOGO} alt="BSI" />
                <div className="t"><b>{f.CustomerName || '—'}</b><div>A/C No. {f.AccountNumber || '—'}</div></div>
              </div>

              {isCorp ? (
                <>
                  <div className="sn-sech">Financial Highlights — Auditor: <input value={f.AuditorName} onChange={set('AuditorName')} className="sn-in" style={{ display: 'inline-block', width: '60mm' }} /></div>
                  <table className="sn-tbl"><thead><tr><th style={{ width: '40%' }}></th><th>FY-1</th><th>FY-2</th><th>FY-3</th></tr></thead><tbody>
                    {fin.map((r, i) => (
                      <tr key={i}><td className="sn-lbl">{r.label}</td>
                        <td><input value={r.y1} onChange={setRow(setFin)(i, 'y1')} className="sn-in" /></td>
                        <td><input value={r.y2} onChange={setRow(setFin)(i, 'y2')} className="sn-in" /></td>
                        <td><input value={r.y3} onChange={setRow(setFin)(i, 'y3')} className="sn-in" /></td></tr>
                    ))}
                  </tbody></table>
                </>
              ) : (
                <>
                  <div className="sn-sech">Guarantors Detail</div>
                  <table className="sn-tbl"><thead><tr>
                    <th>Description</th><th>Branch Code</th><th>Account No.</th><th>Direct Liab. (AED)</th><th>Indirect Liab. (AED)</th><th className="sn-rowdel"></th>
                  </tr></thead><tbody>
                    {guars.map((r, i) => (
                      <tr key={i}>
                        <td><input value={r.desc} onChange={setRow(setGuars)(i, 'desc')} className="sn-in" /></td>
                        <td><input value={r.branch} onChange={setRow(setGuars)(i, 'branch')} className="sn-in" /></td>
                        <td><input value={r.account} onChange={setRow(setGuars)(i, 'account')} className="sn-in" /></td>
                        <td><input value={r.direct} onChange={setRow(setGuars)(i, 'direct')} className="sn-in" /></td>
                        <td><input value={r.indirect} onChange={setRow(setGuars)(i, 'indirect')} className="sn-in" /></td>
                        <td className="sn-rowdel" style={{ width: '7mm', textAlign: 'center' }}><button onClick={delRow(setGuars)(i)} type="button" className="text-red-500"><X size={12} /></button></td>
                      </tr>
                    ))}
                  </tbody></table>
                  <button onClick={addRow(setGuars, { desc: '', branch: '', account: '', direct: '', indirect: '' })} type="button" className="sn-addrow sn-addbtn flex items-center gap-1"><Plus size={12} /> ردیف ضامن</button>
                </>
              )}

              {/* account conduct / AECB */}
              <div className="sn-sech" style={{ marginTop: '2mm' }}>Account Conduct / AECB — Score: <input value={f.AECBScore} onChange={set('AECBScore')} className="sn-in" style={{ display: 'inline-block', width: '24mm' }} /></div>
              <CI v={f.AccountConduct} on={set('AccountConduct')} area />

              {/* other banks */}
              <div className="sn-sech">Relationship with Other Banks</div>
              <table className="sn-tbl"><thead><tr>
                <th>Bank Name</th><th>Facility</th><th>Amount (AED)</th><th>Outstanding (AED)</th><th>Security</th><th className="sn-rowdel"></th>
              </tr></thead><tbody>
                {banks.map((r, i) => (
                  <tr key={i}>
                    <td><input value={r.bank} onChange={setRow(setBanks)(i, 'bank')} className="sn-in" /></td>
                    <td><input value={r.facility} onChange={setRow(setBanks)(i, 'facility')} className="sn-in" /></td>
                    <td><input value={r.amount} onChange={setRow(setBanks)(i, 'amount')} className="sn-in" /></td>
                    <td><input value={r.outstanding} onChange={setRow(setBanks)(i, 'outstanding')} className="sn-in" /></td>
                    <td><input value={r.security} onChange={setRow(setBanks)(i, 'security')} className="sn-in" /></td>
                    <td className="sn-rowdel" style={{ width: '7mm', textAlign: 'center' }}><button onClick={delRow(setBanks)(i)} type="button" className="text-red-500"><X size={12} /></button></td>
                  </tr>
                ))}
              </tbody></table>
              <button onClick={addRow(setBanks, { bank: '', facility: '', amount: '', outstanding: '', security: '' })} type="button" className="sn-addrow sn-addbtn flex items-center gap-1"><Plus size={12} /> ردیف بانک</button>

              {/* CRU */}
              <div className="sn-sech" style={{ marginTop: '2mm' }}>Credit Review Unit (CRU) Findings</div>
              <CI v={f.CRUFindings} on={set('CRUFindings')} area />
              <div className="sn-sech">CRU Recommendation &amp; Conclusion</div>
              <CI v={f.CRURecommendation} on={set('CRURecommendation')} area />

              {/* signatures */}
              <div style={{ fontWeight: 700, marginTop: '4mm' }}>SUBMITTED BY CREDIT REVIEW UNIT (CRU):</div>
              <div className="sn-sign">
                {CRU_SIGNERS.map(([n, r], i) => (
                  <div className="col" key={i}><div className="ln">&nbsp;</div><div style={{ fontWeight: 700 }}>{n}</div><div>{r}</div></div>
                ))}
              </div>
              <div style={{ fontWeight: 700, marginTop: '4mm' }}>APPROVED BY REGIONAL CREDIT COMMITTEE (RCC):</div>
              <div className="sn-sign">
                {rccCols.map(([n, r, s], i) => (
                  <div className="col" key={i}><div className="ln">&nbsp;</div><div style={{ fontWeight: 700 }}>{n}</div><div>{r}</div><div>{s}</div></div>
                ))}
              </div>
              <div className="sn-sign" style={{ justifyContent: 'flex-start' }}>
                <div className="col" style={{ maxWidth: '55mm' }}><div className="ln">&nbsp;</div><div style={{ fontWeight: 700 }}>Shafique Anwar</div><div>Head of RMD — Staff #: 78878</div><div>(Non-Voting Member)</div></div>
              </div>
            </div>
            <div style={{ position: 'absolute', bottom: '5mm', right: '12mm', fontSize: '7.5pt', color: '#666' }}>Page 2 of 2</div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
