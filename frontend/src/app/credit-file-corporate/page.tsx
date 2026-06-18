'use client'

import { useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search, Save } from 'lucide-react'
import { customersApi, crmApi, facilitiesApi, parseApiError } from '@/lib/api'
import type { Facility, FacilityForm } from '@/types'
import toast from 'react-hot-toast'

type FacRow = { facilityId: string; amount: string; rate: string; expiry: string; notices: string }
const EMPTY_ROW: FacRow = { facilityId: '', amount: '', rate: '', expiry: '', notices: '' }
type Partner = { name: string; nationality: string; share: string; remarks: string }

// Corporate facility rows mapped to real Facility types.
const ROWS = [
  { key: 'overdraft', label: 'Overdraft', match: (f: Facility) => f.facility_type === 'overdraft' },
  { key: 'corpLoan', label: 'Corporate Loan', match: (f: Facility) => f.facility_type === 'loan' },
  { key: 'chequeDisc', label: 'Cheque Discounting', match: (f: Facility) => f.facility_type === 'cheque_discounting' },
  { key: 'trustReceipt', label: 'Trust Receipt', match: (f: Facility) => f.facility_type === 'trust_receipt' },
  { key: 'lcSight', label: 'LC (Sight)', match: (f: Facility) => f.facility_type === 'lc_sight' || f.facility_type === 'lc' },
  { key: 'lcUsance', label: 'LC (Usance)', match: (f: Facility) => f.facility_type === 'lc_usance' },
  { key: 'log', label: 'Letter of Guarantee', match: (f: Facility) => f.facility_type === 'log' || f.facility_type === 'lg' },
] as const
type RowKey = (typeof ROWS)[number]['key']
const emptyRows = (): Record<RowKey, FacRow> =>
  Object.fromEntries(ROWS.map((r) => [r.key, { ...EMPTY_ROW }])) as Record<RowKey, FacRow>

type FormData = {
  date: string; branchName: string; branchCode: string
  customerName: string; accountNumber: string; businessType: string
  rating: string; callReport: string; previousFiles: string
  tradeLicenseNum: string; tradeLicenseIssue: string; tradeLicenseExpiry: string; tradeLicenseRemarks: string
  passportNum: string; passportIssue: string; passportExpiry: string; passportRemarks: string
  managerIdNum: string; managerIdIssue: string; managerIdExpiry: string; managerIdRemarks: string
  underlienAED: string; underlienUSD: string; underlienIRR: string; underlienOther: string
  chequesAED: string; chequesUSD: string; chequesIRR: string; chequesOther: string
  collateralsAED: string; collateralsUSD: string; collateralsIRR: string; collateralsOther: string
  undertakingGuarantor: boolean; undertakingPartner: boolean
  grade: string; customerStatus: string
}

const today = () => new Date().toLocaleDateString('en-GB')
const INITIAL: FormData = {
  date: today(), branchName: '', branchCode: '', customerName: '', accountNumber: '', businessType: '',
  rating: '', callReport: '', previousFiles: '',
  tradeLicenseNum: '', tradeLicenseIssue: '', tradeLicenseExpiry: '', tradeLicenseRemarks: '',
  passportNum: '', passportIssue: '', passportExpiry: '', passportRemarks: '',
  managerIdNum: '', managerIdIssue: '', managerIdExpiry: '', managerIdRemarks: '',
  underlienAED: '', underlienUSD: '', underlienIRR: '', underlienOther: '',
  chequesAED: '', chequesUSD: '', chequesIRR: '', chequesOther: '',
  collateralsAED: '', collateralsUSD: '', collateralsIRR: '', collateralsOther: '',
  undertakingGuarantor: true, undertakingPartner: false,
  grade: '', customerStatus: 'ACTIVE CUSTOMER',
}
const blankPartners = (): Partner[] => Array.from({ length: 6 }, () => ({ name: '', nationality: '', share: '', remarks: '' }))

const fmtDate = (s: string | null | undefined) => {
  if (!s) return ''
  const d = new Date(s)
  return isNaN(d.getTime()) ? String(s) : d.toLocaleDateString('en-GB')
}
const onlyNum = (s: string): number | undefined => {
  const n = parseFloat(String(s).replace(/[,/\s]/g, '').replace(/[^\d.-]/g, ''))
  return isNaN(n) ? undefined : n
}

export default function CreditFileCorporatePage() {
  const [data, setData] = useState<FormData>(INITIAL)
  const [rows, setRows] = useState<Record<RowKey, FacRow>>(emptyRows())
  const [partners, setPartners] = useState<Partner[]>(blankPartners())
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const set = (key: keyof FormData) => (e: any) =>
    setData((s) => ({ ...s, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const setRow = (rk: RowKey, key: keyof FacRow) => (e: any) =>
    setRows((s) => ({ ...s, [rk]: { ...s[rk], [key]: e.target.value } }))
  const setPartner = (i: number, key: keyof Partner) => (e: any) =>
    setPartners((s) => s.map((p, idx) => (idx === i ? { ...p, [key]: e.target.value } : p)))

  const fillRowFromFacility = (rk: RowKey, f?: Facility) =>
    setRows((s) => ({
      ...s,
      [rk]: f
        ? { facilityId: f.id, amount: f.amount != null ? String(f.amount) : '', rate: f.interest_rate != null ? String(f.interest_rate) : '', expiry: fmtDate(f.expiry_date), notices: f.notes || '' }
        : { ...EMPTY_ROW },
    }))
  const bindRow = (rk: RowKey) => (e: any) =>
    fillRowFromFacility(rk, facilities.find((f) => f.id === e.target.value))

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await customersApi.detail(a)
      const { customer, profile = {}, facilities: facs = [], partners: parts = [] } = d
      const pdata = (profile && profile.data) || {}
      const acct = customer?.account_no || a
      setFacilities(facs)
      setData((s) => ({
        ...s,
        accountNumber: acct,
        customerName: customer?.name || '',
        branchCode: customer?.branch_code || customer?.branch || '',
        branchName: customer?.branch || '',
        businessType: profile?.business_type || pdata.business_type || '',
        rating: profile?.rating || '',
        customerStatus: profile?.customer_status || s.customerStatus,
        tradeLicenseNum: profile?.trade_license_no || '', tradeLicenseIssue: profile?.trade_license_issue || '',
        tradeLicenseExpiry: profile?.trade_license_expiry || '', tradeLicenseRemarks: profile?.trade_license_remarks || '',
        passportNum: profile?.passport_no || '', passportIssue: profile?.passport_issue || '',
        passportExpiry: profile?.passport_expiry || '', passportRemarks: profile?.passport_remarks || '',
        managerIdNum: profile?.emirates_id_no || '', managerIdIssue: profile?.emirates_id_issue || '',
        managerIdExpiry: profile?.emirates_id_expiry || '', managerIdRemarks: profile?.emirates_id_remarks || '',
      }))
      if (parts.length) {
        setPartners(blankPartners().map((p, i) => parts[i]
          ? { name: parts[i].partner_name || parts[i].name || '', nationality: parts[i].nationality || '', share: String(parts[i].share || parts[i].share_pct || ''), remarks: parts[i].remarks || '' }
          : p))
      }
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
      const prof: Record<string, string> = {}
      const put = (k: string, v: string) => { if (v && v.trim()) prof[k] = v.trim() }
      put('business_type', data.businessType); put('rating', data.rating); put('customer_status', data.customerStatus)
      put('trade_license_no', data.tradeLicenseNum); put('trade_license_issue', data.tradeLicenseIssue)
      put('trade_license_expiry', data.tradeLicenseExpiry); put('trade_license_remarks', data.tradeLicenseRemarks)
      put('passport_no', data.passportNum); put('passport_issue', data.passportIssue)
      put('passport_expiry', data.passportExpiry); put('passport_remarks', data.passportRemarks)
      put('emirates_id_no', data.managerIdNum); put('emirates_id_issue', data.managerIdIssue)
      put('emirates_id_expiry', data.managerIdExpiry); put('emirates_id_remarks', data.managerIdRemarks)
      if (Object.keys(prof).length) await crmApi.updateProfile(a, prof)

      let facUpdates = 0
      for (const r of ROWS) {
        const row = rows[r.key]
        if (!row.facilityId) continue
        const payload: Partial<FacilityForm> = {}
        const amt = onlyNum(row.amount); if (amt != null) payload.amount = amt
        const rate = onlyNum(row.rate); if (rate != null) payload.interest_rate = rate
        if (row.notices.trim()) payload.notes = row.notices.trim()
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
        .cf-sheet { font-family: Arial, Helvetica, sans-serif; font-size: 10px; line-height: 1.2; }
        .cf-row-top { display: flex; align-items: stretch; border: 1px solid #000; margin-bottom: 6px; }
        .cf-logo { flex: 1; padding: 6px 8px; display: flex; flex-direction: column; justify-content: center; border-right: 1px solid #000; }
        .cf-logo b { font-size: 13px; letter-spacing: .3px; } .cf-logo span { font-size: 9px; color: #333; }
        .cf-date { width: 200px; display: flex; }
        .cf-date .l { width: 56px; background: #e5e7eb; font-weight: 700; display: flex; align-items: center; justify-content: center; border-right: 1px solid #000; }
        .cf-date input { flex: 1; border: 0; padding: 4px 6px; font-size: 11px; text-align: center; }
        .cf-title { border: 1px solid #000; text-align: center; font-weight: 700; font-size: 13px; padding: 5px; margin-bottom: 6px; letter-spacing: .5px; }
        .cf-branch { border: 1px solid #000; padding: 4px 8px; font-weight: 700; margin-bottom: 6px; }
        .cf-branch input { border: 0; font-weight: 700; font-size: 11px; }
        table.cf { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        table.cf td, table.cf th { border: 1px solid #000; padding: 2px 5px; font-size: 10px; vertical-align: middle; }
        table.cf .band { background: #d1d5db; font-weight: 700; font-size: 11px; text-align: left; padding: 3px 6px; }
        table.cf .hdr td { background: #eef0f3; font-weight: 700; text-align: center; }
        table.cf td.sn { text-align: center; width: 34px; } table.cf td.desc { font-weight: 600; white-space: nowrap; }
        table.cf input { width: 100%; border: 0; padding: 1px 2px; font-size: 10px; background: transparent; }
        table.cf input:focus { outline: 1px solid #2563eb; background: #fff; }
        .cf-foot { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 12px; }
        .cf-sign { width: 240px; } .cf-sign .line { border-top: 1px solid #000; margin-top: 24px; padding-top: 3px; font-weight: 600; }
        .chk { display: inline-flex; align-items: center; gap: 3px; margin-right: 10px; }
        .cf-controls { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
        .cf-controls label { font-size: 12px; font-weight: 600; color: #334155; display: block; margin-bottom: 3px; }
        .cf-controls input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
        .cf-btn { padding: 8px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; border: 0; display: inline-flex; align-items: center; gap: 6px; color: #fff; }
        .cf-btn.blue { background: #2563eb; } .cf-btn.green { background: #16a34a; } .cf-btn.gray { background: #475569; }
        .cf-btn:disabled { opacity: .6; cursor: not-allowed; }
        .cf-pick { width: 100%; border: 1px dashed #94a3b8; border-radius: 4px; font-size: 10px; padding: 1px; color: #475569; background: #f8fafc; }
        @media print {
          @page { size: A4 portrait; margin: 7mm; }
          html, body { margin: 0 !important; padding: 0 !important; }
          .no-print, .cf-pick { display: none !important; }
          #cf-sheet { max-width: 100%; } .cf-sheet { font-size: 8.5px; }
          table.cf, .cf-row-top, .cf-title, .cf-branch { page-break-inside: avoid; }
        }
      `}</style>

      <div className="cf-sheet">
        <div className="no-print cf-controls">
          <div>
            <label>Account Number</label>
            <input value={acc} onChange={(e) => setAcc(e.target.value)} placeholder="مثال: 002106" onKeyDown={(e) => e.key === 'Enter' && loadAccount()} />
          </div>
          <button onClick={loadAccount} disabled={loading} className="cf-btn blue"><Search size={15} /> {loading ? '...' : 'بارگیری'}</button>
          <button onClick={save} disabled={saving || !data.accountNumber} className="cf-btn green"><Save size={15} /> {saving ? '...' : 'ذخیره در پروفایل'}</button>
          <button onClick={() => window.print()} className="cf-btn gray"><Printer size={15} /> پرینت</button>
          <div style={{ flexBasis: '100%', fontSize: 11, color: '#64748b' }}>
            هویت/شرکا/وضعیت در پروفایل حساب ذخیره می‌شود؛ مبلغ/نرخ/توضیحاتِ هر ردیف ذیل همان تسهیلاتِ انتخاب‌شده. خانهٔ خالی، مقدار قبلی را پاک نمی‌کند.
          </div>
        </div>

        <div id="cf-sheet">
          <div className="cf-row-top">
            <div className="cf-logo"><b>بانک صادرات ایران — BANK SADERAT IRAN</b><span>U.A.E. · Credit Facility Dept.</span></div>
            <div className="cf-date"><div className="l">Date</div><input value={data.date} onChange={set('date')} /></div>
          </div>
          <div className="cf-title">CREDIT FILE SUMMARY (Corporate)</div>
          <div className="cf-branch">Branch Code and Name:&nbsp;
            <input value={data.branchCode} onChange={set('branchCode')} placeholder="2900" style={{ width: 70 }} /> -
            <input value={data.branchName} onChange={set('branchName')} placeholder="Ajman" style={{ width: '60%' }} />
          </div>

          {/* Account Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Account Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Details</td><td>S/No.</td><td>Description</td><td>Details</td></tr>
            <tr>
              <td className="sn">1</td><td className="desc">Customer&rsquo;s Name</td><td><input value={data.customerName} onChange={set('customerName')} /></td>
              <td className="sn">4</td><td className="desc">Rating</td><td><input value={data.rating} onChange={set('rating')} /></td>
            </tr>
            <tr>
              <td className="sn">2</td><td className="desc">Account Number</td><td><input value={data.accountNumber} onChange={set('accountNumber')} /></td>
              <td className="sn">5</td><td className="desc">Call Report</td><td><input value={data.callReport} onChange={set('callReport')} /></td>
            </tr>
            <tr>
              <td className="sn">3</td><td className="desc">Business Type</td><td><input value={data.businessType} onChange={set('businessType')} /></td>
              <td className="sn">6</td><td className="desc">No. of Previous Files</td><td><input value={data.previousFiles} onChange={set('previousFiles')} /></td>
            </tr>
          </tbody></table>

          {/* KYC Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>KYC Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Number</td><td>Issue Date</td><td>Expiry</td><td>Remarks</td></tr>
            <tr><td className="sn">1</td><td className="desc">Trade License</td>
              <td><input value={data.tradeLicenseNum} onChange={set('tradeLicenseNum')} /></td>
              <td><input value={data.tradeLicenseIssue} onChange={set('tradeLicenseIssue')} /></td>
              <td><input value={data.tradeLicenseExpiry} onChange={set('tradeLicenseExpiry')} /></td>
              <td><input value={data.tradeLicenseRemarks} onChange={set('tradeLicenseRemarks')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Passport</td>
              <td><input value={data.passportNum} onChange={set('passportNum')} /></td>
              <td><input value={data.passportIssue} onChange={set('passportIssue')} /></td>
              <td><input value={data.passportExpiry} onChange={set('passportExpiry')} /></td>
              <td><input value={data.passportRemarks} onChange={set('passportRemarks')} /></td></tr>
            <tr><td className="sn">3</td><td className="desc">Manager Emirates ID</td>
              <td><input value={data.managerIdNum} onChange={set('managerIdNum')} /></td>
              <td><input value={data.managerIdIssue} onChange={set('managerIdIssue')} /></td>
              <td><input value={data.managerIdExpiry} onChange={set('managerIdExpiry')} /></td>
              <td><input value={data.managerIdRemarks} onChange={set('managerIdRemarks')} /></td></tr>
          </tbody></table>

          {/* Partners Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={5}>Partners Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Partner&rsquo;s Name</td><td>Nationality</td><td>Share</td><td>Remarks</td></tr>
            {partners.map((p, i) => (
              <tr key={i}>
                <td className="sn">{i + 1}</td>
                <td><input value={p.name} onChange={setPartner(i, 'name')} /></td>
                <td><input value={p.nationality} onChange={setPartner(i, 'nationality')} /></td>
                <td><input value={p.share} onChange={setPartner(i, 'share')} /></td>
                <td><input value={p.remarks} onChange={setPartner(i, 'remarks')} /></td>
              </tr>
            ))}
          </tbody></table>

          {/* Facility Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Facility Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Amount (AED)</td><td>Rate Of Int. / Margin</td><td>Expiry Date</td><td>Notices</td></tr>
            {ROWS.map((r, i) => {
              const row = rows[r.key]
              return (
                <tr key={r.key}>
                  <td className="sn">{i + 1}</td>
                  <td className="desc">{r.label}
                    {facOptions.length > 0 && (
                      <select className="cf-pick" value={row.facilityId} onChange={bindRow(r.key)}>
                        <option value="">— انتخاب تسهیلات —</option>
                        {facOptions.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
                      </select>
                    )}
                  </td>
                  <td><input value={row.amount} onChange={setRow(r.key, 'amount')} /></td>
                  <td><input value={row.rate} onChange={setRow(r.key, 'rate')} /></td>
                  <td><input value={row.expiry} onChange={setRow(r.key, 'expiry')} /></td>
                  <td><input value={row.notices} onChange={setRow(r.key, 'notices')} /></td>
                </tr>
              )
            })}
          </tbody></table>

          {/* Security Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Security Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>AED</td><td>USD</td><td>IRR &rsquo;000&rsquo;</td><td>OTHERS</td></tr>
            <tr><td className="sn">1</td><td className="desc">Underlien Deposits</td>
              <td><input value={data.underlienAED} onChange={set('underlienAED')} /></td>
              <td><input value={data.underlienUSD} onChange={set('underlienUSD')} /></td>
              <td><input value={data.underlienIRR} onChange={set('underlienIRR')} /></td>
              <td><input value={data.underlienOther} onChange={set('underlienOther')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Cheques</td>
              <td><input value={data.chequesAED} onChange={set('chequesAED')} /></td>
              <td><input value={data.chequesUSD} onChange={set('chequesUSD')} /></td>
              <td><input value={data.chequesIRR} onChange={set('chequesIRR')} /></td>
              <td><input value={data.chequesOther} onChange={set('chequesOther')} /></td></tr>
            <tr><td className="sn">3</td><td className="desc">Collaterals</td>
              <td><input value={data.collateralsAED} onChange={set('collateralsAED')} /></td>
              <td><input value={data.collateralsUSD} onChange={set('collateralsUSD')} /></td>
              <td><input value={data.collateralsIRR} onChange={set('collateralsIRR')} /></td>
              <td><input value={data.collateralsOther} onChange={set('collateralsOther')} /></td></tr>
            <tr><td className="sn">4</td><td className="desc">Undertaking Forms From</td>
              <td colSpan={4}>
                <label className="chk"><input type="checkbox" checked={data.undertakingGuarantor} onChange={set('undertakingGuarantor')} /> GUARANTOR/S</label>
                <label className="chk"><input type="checkbox" checked={data.undertakingPartner} onChange={set('undertakingPartner')} /> PARTNER/S</label>
              </td></tr>
          </tbody></table>

          {/* Status */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={2}>Customer&rsquo;s History and Current Status</td></tr>
            <tr><td className="desc" style={{ width: 90 }}>Grade</td><td>
              {['VERY GOOD', 'GOOD', 'AVERAGE', 'POOR'].map((g) => (
                <label className="chk" key={g}><input type="checkbox" checked={data.grade === g} onChange={() => setData((s) => ({ ...s, grade: s.grade === g ? '' : g }))} /> {g}</label>
              ))}
            </td></tr>
            <tr><td className="desc">STATUS</td><td><input value={data.customerStatus} onChange={set('customerStatus')} /></td></tr>
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
