'use client'

import { useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search, Save } from 'lucide-react'
import { customersApi, crmApi, facilitiesApi, parseApiError } from '@/lib/api'
import type { Facility, FacilityForm } from '@/types'
import toast from 'react-hot-toast'

// A facility "row" on the form maps to a real Facility record the user picks.
type FacRow = {
  facilityId: string
  approvalDate: string
  amount: string
  rate: string
  instalments: string
  maturity: string
}
const EMPTY_ROW: FacRow = { facilityId: '', approvalDate: '', amount: '', rate: '', instalments: '', maturity: '' }

type FormData = {
  date: string
  branchName: string
  branchCode: string
  customerName: string
  accountNumber: string
  rating: string
  previousFiles: string
  passportNum: string; passportIssue: string; passportExpiry: string; passportRemarks: string
  emiratesIdNum: string; emiratesIdIssue: string; emiratesIdExpiry: string; emiratesRemarks: string
  underlienAED: string; underlienUSD: string; underlienIRR: string; underlienOther: string
  chequesAED: string; chequesUSD: string; chequesIRR: string; chequesOther: string
  collateralsAED: string; collateralsUSD: string; collateralsIRR: string; collateralsOther: string
  guarantorAvailable: boolean
  guarantor1Name: string; guarantor2Name: string; guarantor3Name: string
  grade: string // VERY GOOD | GOOD | AVERAGE | POOR
  customerStatus: string
  preparedBy: string
}

const today = () => new Date().toLocaleDateString('en-GB') // dd/mm/yyyy like the sample

const INITIAL: FormData = {
  date: today(),
  branchName: '', branchCode: '', customerName: '', accountNumber: '', rating: '', previousFiles: '',
  passportNum: '', passportIssue: '', passportExpiry: '', passportRemarks: '',
  emiratesIdNum: '', emiratesIdIssue: '', emiratesIdExpiry: '', emiratesRemarks: '',
  underlienAED: '', underlienUSD: '', underlienIRR: '', underlienOther: '',
  chequesAED: '', chequesUSD: '', chequesIRR: '', chequesOther: '',
  collateralsAED: '', collateralsUSD: '', collateralsIRR: '', collateralsOther: '',
  guarantorAvailable: true,
  guarantor1Name: '', guarantor2Name: '', guarantor3Name: '',
  grade: '', customerStatus: 'ACTIVE CUSTOMER', preparedBy: '',
}

// The three retail facility rows and how they map to a real Facility's type/loan_type.
const ROWS = [
  { key: 'overdraft', label: 'Overdraft', match: (f: Facility) => f.facility_type === 'overdraft' },
  { key: 'personal', label: 'Personal Loan', match: (f: Facility) => f.facility_type === 'loan' && !/staff/i.test((f as any).loan_type || f.name || '') },
  { key: 'staff', label: 'Staff Loan', match: (f: Facility) => f.facility_type === 'loan' && /staff/i.test((f as any).loan_type || f.name || '') },
] as const
type RowKey = (typeof ROWS)[number]['key']

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
  const [data, setData] = useState<FormData>(INITIAL)
  const [rows, setRows] = useState<Record<RowKey, FacRow>>({ overdraft: { ...EMPTY_ROW }, personal: { ...EMPTY_ROW }, staff: { ...EMPTY_ROW } })
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const set = (key: keyof FormData) => (e: any) =>
    setData((s) => ({ ...s, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const setRow = (rk: RowKey, key: keyof FacRow) => (e: any) =>
    setRows((s) => ({ ...s, [rk]: { ...s[rk], [key]: e.target.value } }))

  // Fill a facility row's fields from a chosen Facility record.
  const fillRowFromFacility = (rk: RowKey, f?: Facility) =>
    setRows((s) => ({
      ...s,
      [rk]: f
        ? {
            facilityId: f.id,
            approvalDate: fmtDate(f.start_date),
            amount: f.amount != null ? String(f.amount) : '',
            rate: f.interest_rate != null ? String(f.interest_rate) : '',
            instalments: (f as any).installments || (f as any).tenor_months || '',
            maturity: fmtDate(f.expiry_date),
          }
        : { ...EMPTY_ROW },
    }))

  const bindRow = (rk: RowKey) => (e: any) => {
    const id = e.target.value
    fillRowFromFacility(rk, facilities.find((f) => f.id === id))
  }

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await customersApi.detail(a)
      const { customer, profile = {}, facilities: facs = [], guarantors = [] } = d
      const acct = customer?.account_no || a
      setFacilities(facs)
      setData((s) => ({
        ...s,
        accountNumber: acct,
        customerName: customer?.name || '',
        branchCode: customer?.branch_code || customer?.branch || '',
        branchName: customer?.branch || '',
        rating: profile?.rating || '',
        customerStatus: profile?.customer_status || s.customerStatus,
        passportNum: profile?.passport_no || '',
        passportIssue: profile?.passport_issue || '',
        passportExpiry: profile?.passport_expiry || '',
        passportRemarks: profile?.passport_remarks || '',
        emiratesIdNum: profile?.emirates_id_no || '',
        emiratesIdIssue: profile?.emirates_id_issue || '',
        emiratesIdExpiry: profile?.emirates_id_expiry || '',
        emiratesRemarks: profile?.emirates_id_remarks || '',
        guarantor1Name: guarantors?.[0]?.guarantor_name || '',
        guarantor2Name: guarantors?.[1]?.guarantor_name || '',
        guarantor3Name: guarantors?.[2]?.guarantor_name || '',
        guarantorAvailable: (guarantors?.length || 0) > 0 ? true : s.guarantorAvailable,
      }))
      // Auto-bind each facility row to the first matching real facility.
      ROWS.forEach((r) => fillRowFromFacility(r.key, facs.find((f: Facility) => r.match(f))))
      toast.success(`بارگیری «${customer?.name || acct}» — ${facs.length} تسهیلات`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  const save = async () => {
    const a = data.accountNumber.trim()
    if (!a) { toast.error('ابتدا یک حساب بارگیری کنید'); return }
    setSaving(true)
    try {
      // 1) Account-level → CustomerProfile (only non-blank values; never clears existing).
      const prof: Record<string, string> = {}
      const put = (k: string, v: string) => { if (v && v.trim()) prof[k] = v.trim() }
      put('rating', data.rating)
      put('customer_status', data.customerStatus)
      put('passport_no', data.passportNum); put('passport_issue', data.passportIssue)
      put('passport_expiry', data.passportExpiry); put('passport_remarks', data.passportRemarks)
      put('emirates_id_no', data.emiratesIdNum); put('emirates_id_issue', data.emiratesIdIssue)
      put('emirates_id_expiry', data.emiratesIdExpiry); put('emirates_id_remarks', data.emiratesRemarks)
      if (Object.keys(prof).length) await crmApi.updateProfile(a, prof)

      // 2) Facility-level → each bound Facility (only non-blank values).
      let facUpdates = 0
      for (const r of ROWS) {
        const row = rows[r.key]
        if (!row.facilityId) continue
        const payload: Partial<FacilityForm> = {}
        const amt = onlyNum(row.amount); if (amt != null) payload.amount = amt
        const rate = onlyNum(row.rate); if (rate != null) payload.interest_rate = rate
        if (row.instalments.trim()) payload.installments = row.instalments.trim()
        if (Object.keys(payload).length) { await facilitiesApi.update(row.facilityId, payload); facUpdates++ }
      }

      toast.success(`ذخیره شد — پروفایل${facUpdates ? ` و ${facUpdates} تسهیلات` : ''}`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSaving(false)
    }
  }

  const facOptions = useMemo(
    () => facilities.map((f) => ({ id: f.id, label: `${f.facility_type}${f.name ? ' · ' + f.name : ''} · ${f.amount?.toLocaleString?.() ?? f.amount} ${f.currency || ''}` })),
    [facilities],
  )

  return (
    <Layout>
      <style>{`
        #cf-sheet { max-width: 800px; margin: 0 auto; color: #000; }
        .cf-sheet { font-family: Arial, Helvetica, sans-serif; font-size: 10px; line-height: 1.25; }
        .cf-row-top { display: flex; align-items: stretch; border: 1px solid #000; margin-bottom: 6px; }
        .cf-logo { flex: 1; padding: 6px 8px; display: flex; flex-direction: column; justify-content: center; border-right: 1px solid #000; }
        .cf-logo b { font-size: 13px; letter-spacing: .3px; }
        .cf-logo span { font-size: 9px; color: #333; }
        .cf-date { width: 200px; display: flex; }
        .cf-date .l { width: 56px; background: #e5e7eb; font-weight: 700; display: flex; align-items: center; justify-content: center; border-right: 1px solid #000; }
        .cf-date input { flex: 1; border: 0; padding: 4px 6px; font-size: 11px; text-align: center; }
        .cf-title { border: 1px solid #000; text-align: center; font-weight: 700; font-size: 13px; padding: 5px; margin-bottom: 6px; letter-spacing: .5px; }
        .cf-branch { border: 1px solid #000; padding: 4px 8px; font-weight: 700; margin-bottom: 6px; }
        .cf-branch input { border: 0; font-weight: 700; font-size: 11px; width: 70%; }
        table.cf { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        table.cf td, table.cf th { border: 1px solid #000; padding: 2px 5px; font-size: 10px; vertical-align: middle; }
        table.cf .band { background: #d1d5db; font-weight: 700; font-size: 11px; text-align: left; padding: 3px 6px; }
        table.cf thead th, table.cf .hdr td { background: #eef0f3; font-weight: 700; text-align: center; }
        table.cf td.sn { text-align: center; width: 34px; }
        table.cf td.desc { font-weight: 600; white-space: nowrap; }
        table.cf input { width: 100%; border: 0; padding: 1px 2px; font-size: 10px; background: transparent; }
        table.cf input:focus { outline: 1px solid #2563eb; background: #fff; }
        /* Fillable cells get a soft tint on screen so they're visually distinct
           from the non-editable label/header cells. Cleared for printing. */
        #cf-sheet input { background: #eaf3ff; }
        #cf-sheet input::placeholder { color: #94a3b8; }
        .cf-foot { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 14px; }
        .cf-sign { width: 240px; }
        .cf-sign .line { border-top: 1px solid #000; margin-top: 26px; padding-top: 3px; font-weight: 600; }
        .chk { display: inline-flex; align-items: center; gap: 3px; margin-right: 10px; }

        .cf-controls { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
        .cf-controls label { font-size: 12px; font-weight: 600; color: #334155; display: block; margin-bottom: 3px; }
        .cf-controls input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
        .cf-btn { padding: 8px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; border: 0; display: inline-flex; align-items: center; gap: 6px; color: #fff; }
        .cf-btn.blue { background: #2563eb; } .cf-btn.green { background: #16a34a; } .cf-btn.gray { background: #475569; }
        .cf-btn:disabled { opacity: .6; cursor: not-allowed; }
        .cf-pick { width: 100%; border: 1px dashed #94a3b8; border-radius: 4px; font-size: 10px; padding: 1px; color: #475569; background: #f8fafc; }

        @media print {
          @page { size: A4 portrait; margin: 8mm; }
          html, body { margin: 0 !important; padding: 0 !important; }
          * { box-sizing: border-box; }
          .no-print, .cf-pick { display: none !important; }
          /* Fit the sheet to the printable width so the right-hand border/column
             is never clipped: full width + let every cell wrap instead of forcing
             the table wider than the page. */
          #cf-sheet { max-width: 100%; width: 100%; }
          .cf-sheet { font-size: 9px; }
          table.cf { width: 100%; }
          table.cf td, table.cf th { white-space: normal !important; word-break: break-word; overflow-wrap: anywhere; }
          #cf-sheet input { background: transparent !important; }
          table.cf, .cf-row-top, .cf-title, .cf-branch { page-break-inside: avoid; }
        }
      `}</style>

      <div className="cf-sheet">
        {/* ---- Controls (screen only) ---- */}
        <div className="no-print cf-controls">
          <div>
            <label>Account Number</label>
            <input value={acc} onChange={(e) => setAcc(e.target.value)} placeholder="مثال: 305169"
              onKeyDown={(e) => e.key === 'Enter' && loadAccount()} />
          </div>
          <button onClick={loadAccount} disabled={loading} className="cf-btn blue"><Search size={15} /> {loading ? '...' : 'بارگیری'}</button>
          <button onClick={save} disabled={saving || !data.accountNumber} className="cf-btn green"><Save size={15} /> {saving ? '...' : 'ذخیره در پروفایل'}</button>
          <button onClick={() => window.print()} className="cf-btn gray"><Printer size={15} /> پرینت</button>
          <div style={{ flexBasis: '100%', fontSize: 11, color: '#64748b' }}>
            اطلاعات هویتی/وضعیت در پروفایل حساب ذخیره می‌شود؛ مبلغ/نرخ/اقساطِ هر ردیف ذیل همان تسهیلاتِ انتخاب‌شده. خانهٔ خالی، مقدار قبلی را پاک نمی‌کند.
          </div>
        </div>

        <div id="cf-sheet">
          {/* ---- Header: logo + date ---- */}
          <div className="cf-row-top">
            <div className="cf-logo"><b>بانک صادرات ایران — BANK SADERAT IRAN</b><span>U.A.E. · Credit Facility Dept.</span></div>
            <div className="cf-date"><div className="l">Date</div><input value={data.date} onChange={set('date')} /></div>
          </div>

          <div className="cf-title">CREDIT FILE SUMMARY (Retail)</div>

          <div className="cf-branch">Branch Code and Name:&nbsp;
            <input value={data.branchCode} onChange={set('branchCode')} placeholder="1741" style={{ width: 70 }} /> -
            <input value={data.branchName} onChange={set('branchName')} placeholder="Al Ain" />
          </div>

          {/* ---- Account Details ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={6}>Account Details</td></tr>
              <tr className="hdr"><td>S/No.</td><td>Description</td><td>Details</td><td>S/No.</td><td>Description</td><td>Details</td></tr>
              <tr>
                <td className="sn">1</td><td className="desc">Customer&rsquo;s Name</td><td><input value={data.customerName} onChange={set('customerName')} /></td>
                <td className="sn">3</td><td className="desc">Rating</td><td><input value={data.rating} onChange={set('rating')} /></td>
              </tr>
              <tr>
                <td className="sn">2</td><td className="desc">Account Number</td><td><input value={data.accountNumber} onChange={set('accountNumber')} /></td>
                <td className="sn">4</td><td className="desc">No. of Previous Files</td><td><input value={data.previousFiles} onChange={set('previousFiles')} /></td>
              </tr>
            </tbody>
          </table>

          {/* ---- KYC Details ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={6}>KYC Details</td></tr>
              <tr className="hdr"><td>S/No.</td><td>Description</td><td>Number</td><td>Issue Date</td><td>Expiry</td><td>Remarks</td></tr>
              <tr>
                <td className="sn">1</td><td className="desc">Passport</td>
                <td><input value={data.passportNum} onChange={set('passportNum')} /></td>
                <td><input value={data.passportIssue} onChange={set('passportIssue')} /></td>
                <td><input value={data.passportExpiry} onChange={set('passportExpiry')} /></td>
                <td><input value={data.passportRemarks} onChange={set('passportRemarks')} /></td>
              </tr>
              <tr>
                <td className="sn">2</td><td className="desc">Emirates ID</td>
                <td><input value={data.emiratesIdNum} onChange={set('emiratesIdNum')} /></td>
                <td><input value={data.emiratesIdIssue} onChange={set('emiratesIdIssue')} /></td>
                <td><input value={data.emiratesIdExpiry} onChange={set('emiratesIdExpiry')} /></td>
                <td><input value={data.emiratesRemarks} onChange={set('emiratesRemarks')} /></td>
              </tr>
            </tbody>
          </table>

          {/* ---- Facility Details ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={7}>Facility Details</td></tr>
              <tr className="hdr"><td>S/No.</td><td>Description</td><td>Approval Date</td><td>Amount (AED)</td><td>Rate Of Int.</td><td>No. of Instalment</td><td>Maturity Date</td></tr>
              {ROWS.map((r, i) => {
                const row = rows[r.key]
                return (
                  <tr key={r.key}>
                    <td className="sn">{i + 1}</td>
                    <td className="desc">
                      {r.label}
                      {facOptions.length > 0 && (
                        <select className="cf-pick" value={row.facilityId} onChange={bindRow(r.key)}>
                          <option value="">— انتخاب تسهیلات —</option>
                          {facOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
                        </select>
                      )}
                    </td>
                    <td><input value={row.approvalDate} onChange={setRow(r.key, 'approvalDate')} /></td>
                    <td><input value={row.amount} onChange={setRow(r.key, 'amount')} /></td>
                    <td><input value={row.rate} onChange={setRow(r.key, 'rate')} /></td>
                    <td><input value={row.instalments} onChange={setRow(r.key, 'instalments')} /></td>
                    <td><input value={row.maturity} onChange={setRow(r.key, 'maturity')} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {/* ---- Security Details ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={6}>Security Details</td></tr>
              <tr className="hdr"><td>S/No.</td><td>Description</td><td>AED</td><td>USD</td><td>IRR &rsquo;000&rsquo;</td><td>OTHERS</td></tr>
              <tr>
                <td className="sn">1</td><td className="desc">Underlien Deposits</td>
                <td><input value={data.underlienAED} onChange={set('underlienAED')} /></td>
                <td><input value={data.underlienUSD} onChange={set('underlienUSD')} /></td>
                <td><input value={data.underlienIRR} onChange={set('underlienIRR')} /></td>
                <td><input value={data.underlienOther} onChange={set('underlienOther')} /></td>
              </tr>
              <tr>
                <td className="sn">2</td><td className="desc">Cheques</td>
                <td><input value={data.chequesAED} onChange={set('chequesAED')} /></td>
                <td><input value={data.chequesUSD} onChange={set('chequesUSD')} /></td>
                <td><input value={data.chequesIRR} onChange={set('chequesIRR')} /></td>
                <td><input value={data.chequesOther} onChange={set('chequesOther')} /></td>
              </tr>
              <tr>
                <td className="sn">3</td><td className="desc">Collaterals</td>
                <td><input value={data.collateralsAED} onChange={set('collateralsAED')} /></td>
                <td><input value={data.collateralsUSD} onChange={set('collateralsUSD')} /></td>
                <td><input value={data.collateralsIRR} onChange={set('collateralsIRR')} /></td>
                <td><input value={data.collateralsOther} onChange={set('collateralsOther')} /></td>
              </tr>
              <tr>
                <td className="sn">4</td>
                <td className="desc">Guarantor/s</td>
                <td colSpan={4}>
                  <label className="chk"><input type="checkbox" checked={data.guarantorAvailable} onChange={set('guarantorAvailable')} /> Available</label>
                  <label className="chk"><input type="checkbox" checked={!data.guarantorAvailable} onChange={(e) => setData((s) => ({ ...s, guarantorAvailable: !e.target.checked }))} /> Not Available</label>
                </td>
              </tr>
            </tbody>
          </table>

          {/* ---- Guarantor's Names ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={2}>Guarantor&rsquo;s Details</td></tr>
              <tr className="hdr"><td style={{ width: 34 }}>S/No.</td><td>Name</td></tr>
              <tr><td className="sn">1</td><td><input value={data.guarantor1Name} onChange={set('guarantor1Name')} /></td></tr>
              <tr><td className="sn">2</td><td><input value={data.guarantor2Name} onChange={set('guarantor2Name')} /></td></tr>
              <tr><td className="sn">3</td><td><input value={data.guarantor3Name} onChange={set('guarantor3Name')} /></td></tr>
            </tbody>
          </table>

          {/* ---- Customer's History and Current Status ---- */}
          <table className="cf">
            <tbody>
              <tr><td className="band" colSpan={2}>Customer&rsquo;s History and Current Status</td></tr>
              <tr>
                <td className="desc" style={{ width: 90 }}>Grade</td>
                <td>
                  {['VERY GOOD', 'GOOD', 'AVERAGE', 'POOR'].map((g) => (
                    <label className="chk" key={g}>
                      <input type="checkbox" checked={data.grade === g} onChange={() => setData((s) => ({ ...s, grade: s.grade === g ? '' : g }))} /> {g}
                    </label>
                  ))}
                </td>
              </tr>
              <tr>
                <td className="desc">STATUS</td>
                <td><input value={data.customerStatus} onChange={set('customerStatus')} /></td>
              </tr>
            </tbody>
          </table>

          {/* ---- Signatures ---- */}
          <div className="cf-foot">
            <div className="cf-sign">Prepared By:<div className="line">&nbsp;</div></div>
            <div className="cf-sign" style={{ textAlign: 'right' }}>Authorized:<div className="line">&nbsp;</div></div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
