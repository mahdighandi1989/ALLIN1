'use client'

import { useMemo, useRef, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search, Save, Plus, Trash2 } from 'lucide-react'
import { customersApi, crmApi, facilitiesApi, parseApiError } from '@/lib/api'
import type { Facility, FacilityForm } from '@/types'
import toast from 'react-hot-toast'

const uid = () => Math.random().toString(36).slice(2, 9)

// Predefined facility rows match a real Facility by type/loan_type.
const MATCH: Record<string, (f: Facility) => boolean> = {
  overdraft: (f) => f.facility_type === 'overdraft',
  personal: (f) => f.facility_type === 'loan' && !/staff/i.test(`${(f as any).loan_type || ''} ${f.name || ''}`),
  staff: (f) => f.facility_type === 'loan' && /staff/i.test(`${(f as any).loan_type || ''} ${f.name || ''}`),
}

type FacRow = {
  uid: string; label: string; custom: boolean; matchKey?: string
  facilityId: string; approvalDate: string; amount: string; rate: string; instalments: string; maturity: string
}
type SecRow = { uid: string; label: string; custom: boolean; facilityTag: string; aed: string; usd: string; irr: string; other: string }

const facBase = (): FacRow[] => [
  { uid: uid(), label: 'Overdraft', custom: false, matchKey: 'overdraft', facilityId: '', approvalDate: '', amount: '', rate: '', instalments: '', maturity: '' },
  { uid: uid(), label: 'Personal Loan', custom: false, matchKey: 'personal', facilityId: '', approvalDate: '', amount: '', rate: '', instalments: '', maturity: '' },
  { uid: uid(), label: 'Staff Loan', custom: false, matchKey: 'staff', facilityId: '', approvalDate: '', amount: '', rate: '', instalments: '', maturity: '' },
]
const secBase = (): SecRow[] => [
  { uid: uid(), label: 'Underlien Deposits', custom: false, facilityTag: '', aed: '', usd: '', irr: '', other: '' },
  { uid: uid(), label: 'Cheques', custom: false, facilityTag: '', aed: '', usd: '', irr: '', other: '' },
  { uid: uid(), label: 'Collaterals', custom: false, facilityTag: '', aed: '', usd: '', irr: '', other: '' },
]

type Acct = {
  date: string; branchCode: string; branchName: string; customerName: string; accountNumber: string
  rating: string; previousFiles: string
  passportNum: string; passportIssue: string; passportExpiry: string; passportRemarks: string
  emiratesIdNum: string; emiratesIdIssue: string; emiratesIdExpiry: string; emiratesRemarks: string
  guarantor1Name: string; guarantor2Name: string; guarantor3Name: string; guarantorAvailable: boolean
  grade: string; customerStatus: string
}
const ACCT0: Acct = {
  date: new Date().toLocaleDateString('en-GB'), branchCode: '', branchName: '', customerName: '', accountNumber: '',
  rating: '', previousFiles: '',
  passportNum: '', passportIssue: '', passportExpiry: '', passportRemarks: '',
  emiratesIdNum: '', emiratesIdIssue: '', emiratesIdExpiry: '', emiratesRemarks: '',
  guarantor1Name: '', guarantor2Name: '', guarantor3Name: '', guarantorAvailable: true,
  grade: '', customerStatus: 'ACTIVE CUSTOMER',
}

const fmtDate = (s: string | null | undefined) => {
  if (!s) return ''
  const d = new Date(s)
  return isNaN(d.getTime()) ? String(s) : d.toLocaleDateString('en-GB')
}
const onlyNum = (s: string): number | undefined => {
  const n = parseFloat(String(s).replace(/[,/\s]/g, '').replace(/[^\d.-]/g, ''))
  return isNaN(n) ? undefined : n
}

export default function CreditFileRetailPage() {
  const [a, setA] = useState<Acct>(ACCT0)
  const [facRows, setFacRows] = useState<FacRow[]>(facBase())
  const [secRows, setSecRows] = useState<SecRow[]>(secBase())
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const sheetRef = useRef<HTMLDivElement>(null)

  const set = (k: keyof Acct) => (e: any) => setA((s) => ({ ...s, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const setFac = (id: string, k: keyof FacRow) => (e: any) => setFacRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: e.target.value } : r)))
  const setSec = (id: string, k: keyof SecRow) => (e: any) => setSecRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: e.target.value } : r)))

  const facFromRecord = (f?: Facility) => ({
    facilityId: f?.id || '',
    approvalDate: fmtDate(f?.start_date), amount: f && f.amount != null ? String(f.amount) : '',
    rate: f && f.interest_rate != null ? String(f.interest_rate) : '',
    instalments: (f as any)?.installments || (f as any)?.tenor_months || '', maturity: fmtDate(f?.expiry_date),
  })
  const bindFac = (id: string) => (e: any) => {
    const f = facilities.find((x) => x.id === e.target.value)
    setFacRows((rows) => rows.map((r) => (r.uid === id ? { ...r, ...facFromRecord(f) } : r)))
  }

  const addFacRow = () => setFacRows((r) => [...r, { uid: uid(), label: '', custom: true, facilityId: '', approvalDate: '', amount: '', rate: '', instalments: '', maturity: '' }])
  const addSecRow = () => setSecRows((r) => [...r, { uid: uid(), label: '', custom: true, facilityTag: '', aed: '', usd: '', irr: '', other: '' }])
  const delFacRow = (id: string) => setFacRows((r) => r.filter((x) => x.uid !== id))
  const delSecRow = (id: string) => setSecRows((r) => r.filter((x) => x.uid !== id))

  const loadAccount = async () => {
    const q = acc.trim()
    if (!q) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await customersApi.detail(q)
      const { customer, profile = {}, facilities: facs = [], guarantors = [] } = d
      const acct = customer?.account_no || q
      setFacilities(facs)
      setA((s) => ({
        ...s, accountNumber: acct, customerName: customer?.name || '',
        branchCode: customer?.branch_code || customer?.branch || '', branchName: customer?.branch || '',
        rating: profile?.rating || '', customerStatus: profile?.customer_status || s.customerStatus,
        passportNum: profile?.passport_no || '', passportIssue: profile?.passport_issue || '',
        passportExpiry: profile?.passport_expiry || '', passportRemarks: profile?.passport_remarks || '',
        emiratesIdNum: profile?.emirates_id_no || '', emiratesIdIssue: profile?.emirates_id_issue || '',
        emiratesIdExpiry: profile?.emirates_id_expiry || '', emiratesRemarks: profile?.emirates_id_remarks || '',
        guarantor1Name: guarantors?.[0]?.guarantor_name || '', guarantor2Name: guarantors?.[1]?.guarantor_name || '',
        guarantor3Name: guarantors?.[2]?.guarantor_name || '', guarantorAvailable: (guarantors?.length || 0) > 0 ? true : s.guarantorAvailable,
      }))
      // Auto-bind predefined facility rows to the first matching real facility.
      setFacRows((rows) => rows.map((r) => {
        if (!r.matchKey) return r
        const f = facs.find((x: Facility) => MATCH[r.matchKey!]?.(x))
        return f ? { ...r, ...facFromRecord(f) } : r
      }))
      toast.success(`بارگیری «${customer?.name || acct}» — ${facs.length} تسهیلات`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally { setLoading(false) }
  }

  const save = async () => {
    const acct = a.accountNumber.trim()
    if (!acct) { toast.error('ابتدا یک حساب بارگیری کنید'); return }
    setSaving(true)
    try {
      const prof: Record<string, string> = {}
      const put = (k: string, v: string) => { if (v && v.trim()) prof[k] = v.trim() }
      put('rating', a.rating); put('customer_status', a.customerStatus)
      put('passport_no', a.passportNum); put('passport_issue', a.passportIssue); put('passport_expiry', a.passportExpiry); put('passport_remarks', a.passportRemarks)
      put('emirates_id_no', a.emiratesIdNum); put('emirates_id_issue', a.emiratesIdIssue); put('emirates_id_expiry', a.emiratesIdExpiry); put('emirates_id_remarks', a.emiratesRemarks)
      if (Object.keys(prof).length) await crmApi.updateProfile(acct, prof)

      let n = 0
      for (const r of facRows) {
        if (!r.facilityId) continue
        const payload: Partial<FacilityForm> = {}
        const amt = onlyNum(r.amount); if (amt != null) payload.amount = amt
        const rate = onlyNum(r.rate); if (rate != null) payload.interest_rate = rate
        if (r.instalments.trim()) payload.installments = r.instalments.trim()
        if (Object.keys(payload).length) { await facilitiesApi.update(r.facilityId, payload); n++ }
      }
      toast.success(`ذخیره شد — پروفایل${n ? ` و ${n} تسهیلات` : ''}`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally { setSaving(false) }
  }

  // Auto-fit to ONE A4 page on print: shrink via zoom (CSS var used only in
  // @media print) when the content would exceed a page at 190mm width.
  const printSheet = () => {
    const el = sheetRef.current
    if (el) {
      const w = el.offsetWidth || 1
      const printHmm = (190 * el.scrollHeight) / w
      const z = printHmm > 277 ? Math.max(0.5, 277 / printHmm) : 1
      el.style.setProperty('--pz', String(z))
    }
    setTimeout(() => window.print(), 40)
  }

  const facOptions = useMemo(
    () => facilities.map((f) => ({ id: f.id, label: `${f.facility_type}${f.name ? ' · ' + f.name : ''} · ${f.amount?.toLocaleString?.() ?? f.amount} ${f.currency || ''}` })),
    [facilities],
  )
  const tagLabel = (t: string) => facRows.find((r) => r.uid === t)?.label || ''

  return (
    <Layout>
      <style>{`
        #cf-sheet { max-width: 820px; margin: 0 auto; color: #000; }
        .cf-sheet { font-family: Arial, Helvetica, sans-serif; font-size: 10px; line-height: 1.25; }
        .cf-row-top { display: flex; align-items: stretch; border: 1px solid #000; margin-bottom: 6px; }
        .cf-logo { flex: 1; padding: 6px 8px; display: flex; flex-direction: column; justify-content: center; border-right: 1px solid #000; }
        .cf-logo b { font-size: 13px; } .cf-logo span { font-size: 9px; color: #333; }
        .cf-date { width: 200px; display: flex; }
        .cf-date .l { width: 56px; background: #e5e7eb; font-weight: 700; display: flex; align-items: center; justify-content: center; border-right: 1px solid #000; }
        .cf-date input { flex: 1; border: 0; padding: 4px 6px; font-size: 11px; text-align: center; }
        .cf-title { border: 1px solid #000; text-align: center; font-weight: 700; font-size: 13px; padding: 5px; margin-bottom: 6px; }
        .cf-branch { border: 1px solid #000; padding: 4px 8px; font-weight: 700; margin-bottom: 6px; }
        .cf-branch input { border: 0; font-weight: 700; font-size: 11px; }
        table.cf { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        table.cf td, table.cf th { border: 1px solid #000; padding: 2px 5px; font-size: 10px; vertical-align: middle; }
        table.cf .band { background: #d1d5db; font-weight: 700; font-size: 11px; text-align: left; padding: 3px 6px; }
        table.cf .hdr td { background: #eef0f3; font-weight: 700; text-align: center; }
        table.cf td.sn { text-align: center; width: 30px; } table.cf td.desc { font-weight: 600; }
        table.cf input { width: 100%; border: 0; padding: 1px 2px; font-size: 10px; background: #eaf3ff; }
        table.cf input:focus { outline: 1px solid #2563eb; }
        .tools { width: 1%; white-space: nowrap; background: #f8fafc; }
        .tools select { font-size: 10px; max-width: 150px; border: 1px dashed #94a3b8; border-radius: 4px; }
        .tools button { border: 0; background: transparent; color: #dc2626; cursor: pointer; padding: 0 4px; }
        .addbtn { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: #2563eb; background: #eff6ff; border: 1px dashed #93c5fd; border-radius: 6px; padding: 3px 8px; cursor: pointer; margin: 0 0 8px; }
        .print-only { display: none; }
        .cf-foot { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 14px; }
        .cf-sign { width: 240px; } .cf-sign .line { border-top: 1px solid #000; margin-top: 26px; padding-top: 3px; font-weight: 600; }
        .chk { display: inline-flex; align-items: center; gap: 3px; margin-right: 10px; }
        .cf-controls { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
        .cf-controls label { font-size: 12px; font-weight: 600; color: #334155; display: block; margin-bottom: 3px; }
        .cf-controls input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
        .cf-btn { padding: 8px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; border: 0; display: inline-flex; align-items: center; gap: 6px; color: #fff; }
        .cf-btn.blue { background: #2563eb; } .cf-btn.green { background: #16a34a; } .cf-btn.gray { background: #475569; }
        .cf-btn:disabled { opacity: .6; cursor: not-allowed; }

        @media print {
          @page { size: A4 portrait; margin: 8mm; }
          html, body { margin: 0 !important; padding: 0 !important; }
          * { box-sizing: border-box; }
          .no-print, .tools, .screen-only, .addbtn { display: none !important; }
          .print-only { display: inline !important; }
          /* Deterministic width (< printable 194mm) so the right border is never
             clipped, plus zoom auto-fit so added rows still fit ONE page. */
          #cf-sheet { width: 190mm; max-width: 190mm; margin: 0 auto; zoom: var(--pz, 1); }
          .cf-sheet { font-size: 9px; }
          table.cf td, table.cf th { white-space: normal !important; word-break: break-word; overflow-wrap: anywhere; }
          table.cf input { background: transparent !important; }
          table.cf, .cf-row-top, .cf-title, .cf-branch { page-break-inside: avoid; }
        }
      `}</style>

      <div className="cf-sheet">
        {/* Controls (screen only) */}
        <div className="no-print cf-controls">
          <div>
            <label>Account Number</label>
            <input value={acc} onChange={(e) => setAcc(e.target.value)} placeholder="مثال: 110151" onKeyDown={(e) => e.key === 'Enter' && loadAccount()} />
          </div>
          <button onClick={loadAccount} disabled={loading} className="cf-btn blue"><Search size={15} /> {loading ? '...' : 'بارگیری'}</button>
          <button onClick={save} disabled={saving || !a.accountNumber} className="cf-btn green"><Save size={15} /> {saving ? '...' : 'ذخیره در پروفایل'}</button>
          <button onClick={printSheet} className="cf-btn gray"><Printer size={15} /> پرینت</button>
          <div style={{ flexBasis: '100%', fontSize: 11, color: '#64748b' }}>
            ستون آبیِ سمت راستِ هر ردیف تسهیلات (فقط روی صفحه) برای انتخاب اینکه ردیف به کدام تسهیلاتِ مشتری وصل شود. خانه‌های آبی قابل‌ویرایش‌اند؛ موقع پرینت پاک می‌شوند و خروجی تک‌صفحه است.
          </div>
        </div>

        <div id="cf-sheet" ref={sheetRef}>
          <div className="cf-row-top">
            <div className="cf-logo"><b>بانک صادرات ایران — BANK SADERAT IRAN</b><span>U.A.E. · Credit Facility Dept.</span></div>
            <div className="cf-date"><div className="l">Date</div><input value={a.date} onChange={set('date')} /></div>
          </div>
          <div className="cf-title">CREDIT FILE SUMMARY (Retail)</div>
          <div className="cf-branch">Branch Code and Name:&nbsp;
            <input value={a.branchCode} onChange={set('branchCode')} placeholder="1741" style={{ width: 70 }} /> -
            <input value={a.branchName} onChange={set('branchName')} placeholder="Al Ain" style={{ width: '55%' }} />
          </div>

          {/* Account Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Account Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Details</td><td>S/No.</td><td>Description</td><td>Details</td></tr>
            <tr><td className="sn">1</td><td className="desc">Customer&rsquo;s Name</td><td><input value={a.customerName} onChange={set('customerName')} /></td>
              <td className="sn">3</td><td className="desc">Rating</td><td><input value={a.rating} onChange={set('rating')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Account Number</td><td><input value={a.accountNumber} onChange={set('accountNumber')} /></td>
              <td className="sn">4</td><td className="desc">No. of Previous Files</td><td><input value={a.previousFiles} onChange={set('previousFiles')} /></td></tr>
          </tbody></table>

          {/* KYC Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>KYC Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Number</td><td>Issue Date</td><td>Expiry</td><td>Remarks</td></tr>
            <tr><td className="sn">1</td><td className="desc">Passport</td>
              <td><input value={a.passportNum} onChange={set('passportNum')} /></td><td><input value={a.passportIssue} onChange={set('passportIssue')} /></td>
              <td><input value={a.passportExpiry} onChange={set('passportExpiry')} /></td><td><input value={a.passportRemarks} onChange={set('passportRemarks')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Emirates ID</td>
              <td><input value={a.emiratesIdNum} onChange={set('emiratesIdNum')} /></td><td><input value={a.emiratesIdIssue} onChange={set('emiratesIdIssue')} /></td>
              <td><input value={a.emiratesIdExpiry} onChange={set('emiratesIdExpiry')} /></td><td><input value={a.emiratesRemarks} onChange={set('emiratesRemarks')} /></td></tr>
          </tbody></table>

          {/* Facility Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={8}>Facility Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Approval Date</td><td>Amount (AED)</td><td>Rate Of Int.</td><td>No. of Instalment</td><td>Maturity Date</td><td className="tools">تسهیلات / حذف</td></tr>
            {facRows.map((r, i) => (
              <tr key={r.uid}>
                <td className="sn">{i + 1}</td>
                <td className="desc">{r.custom ? <input value={r.label} onChange={setFac(r.uid, 'label')} placeholder="نوع تسهیلات" /> : r.label}</td>
                <td><input value={r.approvalDate} onChange={setFac(r.uid, 'approvalDate')} /></td>
                <td><input value={r.amount} onChange={setFac(r.uid, 'amount')} /></td>
                <td><input value={r.rate} onChange={setFac(r.uid, 'rate')} /></td>
                <td><input value={r.instalments} onChange={setFac(r.uid, 'instalments')} /></td>
                <td><input value={r.maturity} onChange={setFac(r.uid, 'maturity')} /></td>
                <td className="tools">
                  <select value={r.facilityId} onChange={bindFac(r.uid)}>
                    <option value="">— تسهیلات —</option>
                    {facOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
                  </select>
                  {r.custom && <button title="حذف ردیف" onClick={() => delFacRow(r.uid)}><Trash2 size={13} /></button>}
                </td>
              </tr>
            ))}
          </tbody></table>
          <button className="addbtn" onClick={addFacRow}><Plus size={13} /> افزودن ردیف تسهیلات</button>

          {/* Security Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={8}>Security Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>For Facility</td><td>AED</td><td>USD</td><td>IRR &rsquo;000&rsquo;</td><td>OTHERS</td><td className="tools">حذف</td></tr>
            {secRows.map((r, i) => (
              <tr key={r.uid}>
                <td className="sn">{i + 1}</td>
                <td className="desc">{r.custom ? <input value={r.label} onChange={setSec(r.uid, 'label')} placeholder="نوع سند/وثیقه" /> : r.label}</td>
                <td>
                  <select className="screen-only" value={r.facilityTag} onChange={setSec(r.uid, 'facilityTag')} style={{ width: '100%', fontSize: 10 }}>
                    <option value="">— همه / نامشخص —</option>
                    {facRows.map((fr) => <option key={fr.uid} value={fr.uid}>{fr.label || '(بدون نام)'}</option>)}
                  </select>
                  <span className="print-only">{tagLabel(r.facilityTag)}</span>
                </td>
                <td><input value={r.aed} onChange={setSec(r.uid, 'aed')} /></td>
                <td><input value={r.usd} onChange={setSec(r.uid, 'usd')} /></td>
                <td><input value={r.irr} onChange={setSec(r.uid, 'irr')} /></td>
                <td><input value={r.other} onChange={setSec(r.uid, 'other')} /></td>
                <td className="tools">{r.custom && <button title="حذف ردیف" onClick={() => delSecRow(r.uid)}><Trash2 size={13} /></button>}</td>
              </tr>
            ))}
            <tr><td className="sn">{secRows.length + 1}</td><td className="desc">Guarantor/s</td><td colSpan={5}>
              <label className="chk"><input type="checkbox" checked={a.guarantorAvailable} onChange={set('guarantorAvailable')} style={{ width: 'auto' }} /> Available</label>
              <label className="chk"><input type="checkbox" checked={!a.guarantorAvailable} onChange={(e) => setA((s) => ({ ...s, guarantorAvailable: !e.target.checked }))} style={{ width: 'auto' }} /> Not Available</label>
            </td><td className="tools" /></tr>
          </tbody></table>
          <button className="addbtn" onClick={addSecRow}><Plus size={13} /> افزودن ردیف مدرک/وثیقه</button>

          {/* Guarantor's Names */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={2}>Guarantor&rsquo;s Details</td></tr>
            <tr className="hdr"><td style={{ width: 34 }}>S/No.</td><td>Name</td></tr>
            <tr><td className="sn">1</td><td><input value={a.guarantor1Name} onChange={set('guarantor1Name')} /></td></tr>
            <tr><td className="sn">2</td><td><input value={a.guarantor2Name} onChange={set('guarantor2Name')} /></td></tr>
            <tr><td className="sn">3</td><td><input value={a.guarantor3Name} onChange={set('guarantor3Name')} /></td></tr>
          </tbody></table>

          {/* Status */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={2}>Customer&rsquo;s History and Current Status</td></tr>
            <tr><td className="desc" style={{ width: 90 }}>Grade</td><td>
              {['VERY GOOD', 'GOOD', 'AVERAGE', 'POOR'].map((g) => (
                <label className="chk" key={g}><input type="checkbox" checked={a.grade === g} onChange={() => setA((s) => ({ ...s, grade: s.grade === g ? '' : g }))} style={{ width: 'auto' }} /> {g}</label>
              ))}
            </td></tr>
            <tr><td className="desc">STATUS</td><td><input value={a.customerStatus} onChange={set('customerStatus')} /></td></tr>
          </tbody></table>

          <div className="cf-foot">
            <div className="cf-sign">Prepared By:<div className="line">&nbsp;</div></div>
            <div className="cf-sign" style={{ textAlign: 'right' }}>Authorized:<div className="line">&nbsp;</div></div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
