'use client'

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search, Save, Plus, Trash2 } from 'lucide-react'
import { customersApi, crmApi, facilitiesApi, parseApiError } from '@/lib/api'
import { AmtInput, PctInput, WrapInput, DraftDrop, CountryInput, CountryDataList, CCY, fmtAmt, type PropRow, emptyProp, propFromRecord, savePropertyRows } from '@/components/creditFileBits'
import type { Facility, FacilityForm } from '@/types'
import toast from 'react-hot-toast'

const uid = () => Math.random().toString(36).slice(2, 9)

const MATCH: Record<string, (f: Facility) => boolean> = {
  overdraft: (f) => f.facility_type === 'overdraft',
  corpLoan: (f) => f.facility_type === 'loan',
  chequeDisc: (f) => f.facility_type === 'cheque_discounting',
  trustReceipt: (f) => f.facility_type === 'trust_receipt',
  lcSight: (f) => f.facility_type === 'lc_sight' || f.facility_type === 'lc',
  lcUsance: (f) => f.facility_type === 'lc_usance',
  log: (f) => f.facility_type === 'log' || f.facility_type === 'lg',
}

type FacRow = { uid: string; label: string; custom: boolean; matchKey?: string; facilityId: string; amount: string; rate: string; expiry: string; notices: string }
type SecRow = { uid: string; label: string; custom: boolean; facilityTag: string; aed: string; usd: string; irr: string; other: string }
type Partner = { uid: string; dbId?: string; name: string; nationality: string; share: string; remarks: string }

const facBase = (): FacRow[] => ([
  ['Overdraft', 'overdraft'], ['Corporate Loan', 'corpLoan'], ['Cheque Discounting', 'chequeDisc'],
  ['Trust Receipt', 'trustReceipt'], ['LC (Sight)', 'lcSight'], ['LC (Usance)', 'lcUsance'], ['Letter of Guarantee', 'log'],
] as [string, string][]).map(([label, matchKey]) => ({ uid: uid(), label, custom: false, matchKey, facilityId: '', amount: '', rate: '', expiry: '', notices: '' }))
const secBase = (): SecRow[] => ['Underlien Deposits', 'Cheques', 'Collaterals'].map((label) => ({ uid: uid(), label, custom: false, facilityTag: '', aed: '', usd: '', irr: '', other: '' }))
const partnersBase = (): Partner[] => Array.from({ length: 3 }, () => ({ uid: uid(), name: '', nationality: '', share: '', remarks: '' }))

const facLabel = (ft: string): string => (({
  overdraft: 'Overdraft', loan: 'Corporate Loan', cheque_discounting: 'Cheque Discounting',
  trust_receipt: 'Trust Receipt', lc_sight: 'LC (Sight)', lc: 'LC (Sight)', lc_usance: 'LC (Usance)',
  log: 'Letter of Guarantee', lg: 'Letter of Guarantee',
} as Record<string, string>)[String(ft || '').toLowerCase()] || (ft ? String(ft) : 'Facility'))

type Acct = {
  date: string; branchCode: string; branchName: string; customerName: string; accountNumber: string; businessType: string
  rating: string; callReport: string; previousFiles: string
  tradeLicenseNum: string; tradeLicenseIssue: string; tradeLicenseExpiry: string; tradeLicenseRemarks: string
  passportNum: string; passportIssue: string; passportExpiry: string; passportRemarks: string
  managerIdNum: string; managerIdIssue: string; managerIdExpiry: string; managerIdRemarks: string
  undertakingGuarantor: boolean; undertakingPartner: boolean; grade: string; customerStatus: string
}
const ACCT0: Acct = {
  date: new Date().toLocaleDateString('en-GB'), branchCode: '', branchName: '', customerName: '', accountNumber: '', businessType: '',
  rating: '', callReport: '', previousFiles: '',
  tradeLicenseNum: '', tradeLicenseIssue: '', tradeLicenseExpiry: '', tradeLicenseRemarks: '',
  passportNum: '', passportIssue: '', passportExpiry: '', passportRemarks: '',
  managerIdNum: '', managerIdIssue: '', managerIdExpiry: '', managerIdRemarks: '',
  undertakingGuarantor: true, undertakingPartner: false, grade: '', customerStatus: 'ACTIVE CUSTOMER',
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

export default function CreditFileCorporatePage() {
  const [a, setA] = useState<Acct>(ACCT0)
  const [facRows, setFacRows] = useState<FacRow[]>(facBase())
  const [secRows, setSecRows] = useState<SecRow[]>(secBase())
  const [partners, setPartners] = useState<Partner[]>(partnersBase())
  const [props, setProps] = useState<PropRow[]>([emptyProp()])
  const [partnerNameList, setPartnerNameList] = useState<string[]>([])
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const sheetRef = useRef<HTMLDivElement>(null)

  const set = (k: keyof Acct) => (e: any) => setA((s) => ({ ...s, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }))
  const setFac = (id: string, k: keyof FacRow) => (e: any) => setFacRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: e.target.value } : r)))
  const setFacV = (id: string, k: keyof FacRow) => (v: string) => setFacRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: v } : r)))
  const setSec = (id: string, k: keyof SecRow) => (e: any) => setSecRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: e.target.value } : r)))
  const setSecV = (id: string, k: keyof SecRow) => (v: string) => setSecRows((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: v } : r)))
  const setPartner = (id: string, k: keyof Partner) => (e: any) => setPartners((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: e.target.value } : r)))
  const setPartnerV = (id: string, k: keyof Partner) => (v: string) => setPartners((rows) => rows.map((r) => (r.uid === id ? { ...r, [k]: v } : r)))
  const setProp = (i: number, k: keyof PropRow) => (e: any) => setProps((rows) => rows.map((r, idx) => (idx === i ? { ...r, [k]: e.target.value } : r)))
  const setPropV = (i: number, k: keyof PropRow) => (v: string) => setProps((rows) => rows.map((r, idx) => (idx === i ? { ...r, [k]: v } : r)))
  const addProp = () => setProps((r) => [...r, emptyProp()])
  const delProp = (i: number) => setProps((r) => (r.length > 1 ? r.filter((_, idx) => idx !== i) : r))
  const toggleProp = (i: number) => setProps((r) => r.map((x, idx) => (idx === i ? { ...x, _open: !x._open } : x)))
  const handleExtract = async (r: any) => {
    const o = r?.offer || {}
    const pf = r?.profile || {}
    const acct = r?.account_no || acc
    if (acct) { setAcc(acct); await loadAccount(acct) } // pull DB-persisted data first
    // Overlay the draft-derived values loadAccount cannot provide.
    setA((s) => ({
      ...s,
      customerName: s.customerName || o.CompanyName || '',
      businessType: s.businessType || o.BusinessType || pf.business_type || '',
      rating: o.Rating || s.rating,
      tradeLicenseNum: s.tradeLicenseNum || pf.trade_license_no || '',
      tradeLicenseExpiry: s.tradeLicenseExpiry || pf.trade_license_expiry || '',
    }))
    // Proposed facility → fill the matching (empty) facility row.
    const ft = String(o.FacilityType || pf.proposed_facility || '').toLowerCase()
    const amt = o.LoanAmount || o.CreditLimit || (pf.proposed_amount ? fmtAmt(pf.proposed_amount) : '')
    const rateRaw = String(o.InterestRate || pf.proposed_rate || '').replace(/[^\d.]/g, '')
    const rate = rateRaw ? `${rateRaw}%` : ''
    const ten = o.LoanTenor || pf.proposed_tenor || ''
    if (amt || rate || ten) {
      setFacRows((rows) => {
        let t = rows.findIndex((rw) => /loan/.test(rw.label.toLowerCase()) && /loan/.test(ft))
        if (t < 0) t = rows.findIndex((rw) => rw.matchKey === 'corpLoan')
        if (t < 0) return rows
        return rows.map((rw, i) => (i === t ? { ...rw, amount: rw.amount || amt, rate: rw.rate || rate, expiry: rw.expiry || (ten ? `${ten} MONTHS` : '') } : rw))
      })
    }
    toast.success('استخراج و در فیلدها نگاشت شد')
  }

  const facFromRecord = (f?: Facility) => ({
    facilityId: f?.id || '', amount: fmtAmt(f && f.amount != null ? String(f.amount) : ''),
    rate: f && f.interest_rate != null ? `${f.interest_rate}%` : '', expiry: fmtDate(f?.expiry_date), notices: f?.notes || '',
  })
  const bindFac = (id: string) => (e: any) => {
    const f = facilities.find((x) => x.id === e.target.value)
    setFacRows((rows) => rows.map((r) => (r.uid === id ? { ...r, ...facFromRecord(f) } : r)))
  }

  const addFacRow = () => setFacRows((r) => [...r, { uid: uid(), label: '', custom: true, facilityId: '', amount: '', rate: '', expiry: '', notices: '' }])
  const addSecRow = () => setSecRows((r) => [...r, { uid: uid(), label: '', custom: true, facilityTag: '', aed: '', usd: '', irr: '', other: '' }])
  const addPartner = () => setPartners((r) => [...r, { uid: uid(), name: '', nationality: '', share: '', remarks: '' }])
  const delFacRow = (id: string) => setFacRows((r) => r.filter((x) => x.uid !== id))
  const delSecRow = (id: string) => setSecRows((r) => r.filter((x) => x.uid !== id))
  const delPartner = (id: string) => setPartners((r) => r.filter((x) => x.uid !== id))

  const loadAccount = async (override?: string) => {
    const q = (override ?? acc).trim()
    if (!q) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await customersApi.detail(q)
      const { customer, profile = {}, facilities: facs = [], partners: parts = [], properties: propList = [] } = d
      const pdata = (profile && profile.data) || {}
      const acct = customer?.account_no || q
      setFacilities(facs)
      const uf = String(profile?.undertaking_from || '')
      // Reset from ACCT0, not the previous account's state — leftover values
      // must not leak into (and then be saved onto) the new customer.
      const s = { ...ACCT0 } as Acct
      setA(() => ({
        ...s, accountNumber: acct, customerName: customer?.name || '',
        branchCode: customer?.branch_code || customer?.branch || '', branchName: customer?.branch || '',
        businessType: profile?.business_type || pdata.business_type || '', rating: profile?.rating || '',
        callReport: profile?.call_report || '', previousFiles: profile?.previous_files || '',
        grade: profile?.grade || s.grade,
        customerStatus: profile?.customer_status || s.customerStatus,
        undertakingGuarantor: uf ? /guarant/i.test(uf) : s.undertakingGuarantor,
        undertakingPartner: uf ? /partner/i.test(uf) : s.undertakingPartner,
        tradeLicenseNum: profile?.trade_license_no || '', tradeLicenseIssue: profile?.trade_license_issue || '',
        tradeLicenseExpiry: profile?.trade_license_expiry || '', tradeLicenseRemarks: profile?.trade_license_remarks || '',
        passportNum: profile?.passport_no || '', passportIssue: profile?.passport_issue || '',
        passportExpiry: profile?.passport_expiry || '', passportRemarks: profile?.passport_remarks || '',
        managerIdNum: profile?.emirates_id_no || '', managerIdIssue: profile?.emirates_id_issue || '',
        managerIdExpiry: profile?.emirates_id_expiry || '', managerIdRemarks: profile?.emirates_id_remarks || '',
      }))
      // Security/collateral matrix (data_json) → fill the base rows, append extras.
      const sd: any[] = Array.isArray(pdata.security_details) ? pdata.security_details : []
      // ALWAYS reset from the pristine base: keeping the previous account's
      // matrix/partners on screen (then saving) wrote customer A's data into
      // customer B's records.
      setSecRows(() => {
        const base = secBase(); const used = new Set<number>(); const extra: SecRow[] = []
        sd.forEach((e: any) => {
          const t = String(e?.type || '').trim()
          const row = { facilityTag: e?.for_facility || '', aed: e?.aed || '', usd: e?.usd || '', irr: e?.irr || '', other: e?.other || '' }
          const idx = base.findIndex((b, i) => !used.has(i) && b.label.toLowerCase() === t.toLowerCase())
          if (idx >= 0) { used.add(idx); base[idx] = { ...base[idx], ...row } }
          else if (t) extra.push({ uid: uid(), label: t, custom: true, ...row })
        })
        return [...base, ...extra]
      })
      setPartners(parts.length
        ? parts.map((p: any) => ({ uid: uid(), dbId: p.id, name: p.partner_name || p.name || '', nationality: p.nationality || '', share: String(p.share || p.share_pct || ''), remarks: p.remarks || '' }))
        : partnersBase())
      // Two-way sync: properties already in the customer's املاک list fill the rows.
      setProps(Array.isArray(propList) && propList.length ? propList.map(propFromRecord) : [emptyProp()])
      // Bind predefined rows to facilities, then AUTO-ADD a row for every extra
      // facility so nothing in the DB is left off the form.
      setFacRows(() => {
        const rows = facBase()
        const used = new Set<string>()
        const mapped = rows.map((r) => {
          if (!r.matchKey) return r
          const f = facs.find((x: Facility) => MATCH[r.matchKey!]?.(x) && !used.has(x.id))
          if (f) { used.add(f.id); return { ...r, ...facFromRecord(f) } }
          return r
        })
        const extra = facs.filter((x: Facility) => !used.has(x.id)).map((x: Facility) => ({
          uid: uid(), label: x.name || facLabel(x.facility_type), custom: true, ...facFromRecord(x),
        }))
        return [...mapped, ...extra]
      })
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
      put('business_type', a.businessType); put('rating', a.rating); put('customer_status', a.customerStatus)
      put('call_report', a.callReport); put('previous_files', a.previousFiles); put('grade', a.grade)
      prof['undertaking_from'] = [a.undertakingGuarantor && 'Guarantor/s', a.undertakingPartner && 'Partner/s'].filter(Boolean).join(', ')
      put('trade_license_no', a.tradeLicenseNum); put('trade_license_issue', a.tradeLicenseIssue); put('trade_license_expiry', a.tradeLicenseExpiry); put('trade_license_remarks', a.tradeLicenseRemarks)
      put('passport_no', a.passportNum); put('passport_issue', a.passportIssue); put('passport_expiry', a.passportExpiry); put('passport_remarks', a.passportRemarks)
      put('emirates_id_no', a.managerIdNum); put('emirates_id_issue', a.managerIdIssue); put('emirates_id_expiry', a.managerIdExpiry); put('emirates_id_remarks', a.managerIdRemarks)
      if (Object.keys(prof).length) await crmApi.updateProfile(acct, prof)

      // Security/collateral matrix → data_json (the only place this table lives).
      const secData = secRows
        .filter((r) => r.label.trim() && (r.aed || r.usd || r.irr || r.other || r.facilityTag))
        .map((r) => ({ type: r.label.trim(), for_facility: r.facilityTag || '', aed: r.aed || '', usd: r.usd || '', irr: r.irr || '', other: r.other || '' }))
      if (secData.length) await crmApi.saveOfferLetterData(acct, { fields: { security_details: secData }, snapshot_key: 'credit_file_corporate' })

      let n = 0
      for (const r of facRows) {
        if (!r.facilityId) continue
        const payload: Partial<FacilityForm> = {}
        const amt = onlyNum(r.amount); if (amt != null) payload.amount = amt
        const rate = onlyNum(r.rate); if (rate != null) payload.interest_rate = rate
        if (r.notices.trim()) payload.notes = r.notices.trim()
        if (Object.keys(payload).length) { await facilitiesApi.update(r.facilityId, payload); n++ }
      }

      let pc = 0
      try {
        const res = await savePropertyRows(acct, a.customerName, props)
        setProps(res.rows); pc = res.count
      } catch (pe: any) { toast.error(pe?.message || String(pe)); setSaving(false); return }

      // Partners: two-way upsert (dedup by id; new rows captured; empties skipped).
      let pn = 0
      const pr = partners.map((p) => ({ ...p }))
      for (let i = 0; i < pr.length; i++) {
        const p = pr[i]
        if (!p.name.trim()) continue
        const body: Record<string, any> = {
          name: p.name.trim(), customer_name: a.customerName || undefined,
          nationality: p.nationality.trim() || undefined, share: p.share.trim() || undefined,
          remarks: p.remarks.trim() || undefined,
        }
        if (p.dbId) { await crmApi.updatePartner(p.dbId, body); pn++ }
        else { const res = await crmApi.addPartner(acct, body); if (res?.id) pr[i] = { ...p, dbId: res.id }; pn++ }
      }
      setPartners(pr)

      toast.success(`ذخیره شد — پروفایل${n ? ` و ${n} تسهیلات` : ''}${pc ? ` و ${pc} ملک` : ''}${pn ? ` و ${pn} شریک` : ''}`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally { setSaving(false) }
  }

  // Fit the whole sheet onto ONE A4 page: measure at the REAL print width (190mm)
  // so text wrapping matches the printout, then shrink with CSS zoom. Runs on the
  // Print button AND on Ctrl+P (beforeprint).
  const fitSheet = useCallback(() => {
    const el = sheetRef.current
    if (!el) return
    const MMpx = 96 / 25.4
    const PRINT_W = 186   // mm — printed width (fills A4 width, safe inside the margins)
    const avail = 270     // mm — one-A4 height budget (survives default print margins)
    const regrow = () => el.querySelectorAll('textarea.wrap-cell').forEach((t) => {
      const ta = t as HTMLTextAreaElement
      ta.style.height = 'auto'; ta.style.height = `${ta.scrollHeight}px`
    })
    const savedW = el.style.width
    const savedZ = (el.style as any).zoom
    // Measure content height at the full print width.
    el.style.width = `${PRINT_W}mm`
    ;(el.style as any).zoom = '1'
    void el.offsetHeight
    regrow()
    const hMm = el.scrollHeight / MMpx
    // If it's too tall, shrink with zoom — but render the sheet WIDER first so that
    // after zoom the visual width is STILL the full page width. (A plain zoom scales
    // width and height together, which is what left the sheet narrow + tiny.)
    // width = PRINT_W/z  ⇒  visual width = PRINT_W, visual height = h(wider) × z ≤ avail.
    let z = 1, pw = PRINT_W
    if (hMm > avail) {
      z = Math.max(0.4, avail / hMm)
      pw = PRINT_W / z
      el.style.width = `${pw}mm`
      void el.offsetHeight
      regrow()  // re-fit the text cells at the wider layout
    }
    // Restore the on-screen layout; print uses the CSS vars.
    el.style.width = savedW
    ;(el.style as any).zoom = savedZ
    void el.offsetHeight
    regrow()
    el.style.setProperty('--pw', `${pw}mm`)
    el.style.setProperty('--pz', String(z))
  }, [])
  const printSheet = () => { fitSheet(); setTimeout(() => window.print(), 60) }
  useEffect(() => {
    const on = () => fitSheet()
    window.addEventListener('beforeprint', on)
    return () => window.removeEventListener('beforeprint', on)
  }, [fitSheet])

  // Auto-load when arriving from the unified /credit-file router (?acc=…).
  useEffect(() => {
    const qp = new URLSearchParams(window.location.search).get('acc')
    if (qp) { setAcc(qp); loadAccount(qp) }
    crmApi.partnerNames().then(setPartnerNameList).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const facOptions = useMemo(
    () => facilities.map((f) => ({ id: f.id, label: `${f.facility_type}${f.name ? ' · ' + f.name : ''} · ${f.amount?.toLocaleString?.() ?? f.amount} ${f.currency || ''}` })),
    [facilities],
  )
  const tagLabel = (t: string) => facRows.find((r) => r.uid === t)?.label || ''

  return (
    <Layout>
      <style>{`
        #cf-sheet { max-width: 820px; margin: 0 auto; color: #000; }
        .cf-sheet { font-family: Arial, Helvetica, sans-serif; font-size: 10px; line-height: 1.2; }
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
        table.cf td, table.cf th { border: 1px solid #000; padding: 2px 5px; font-size: 10px; vertical-align: middle; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        table.cf .band { background: #c7ccd3; font-weight: 700; font-size: 11px; text-align: left; padding: 3px 6px; }
        table.cf .hdr td { background: #dde1e7; font-weight: 700; text-align: center; }
        table.cf td.sn { text-align: center; width: 30px; background: #eef1f5; } table.cf td.desc { font-weight: 600; background: #eef1f5; }
        table.cf input { width: 100%; border: 0; padding: 1px 2px; font-size: 10px; background: #eaf3ff; }
        table.cf textarea.wrap-cell { width: 100%; border: 0; padding: 1px 2px; font-size: 10px; background: #eaf3ff; resize: none; overflow: hidden; font-family: inherit; line-height: 1.3; vertical-align: top; box-sizing: border-box; display: block; }
        table.cf input:focus { outline: 1px solid #2563eb; }
        .tools { width: 1%; white-space: nowrap; background: #f8fafc; }
        .tools select { font-size: 10px; max-width: 150px; border: 1px dashed #94a3b8; border-radius: 4px; }
        .tools button { border: 0; background: transparent; color: #dc2626; cursor: pointer; padding: 0 4px; }
        .addbtn { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; color: #2563eb; background: #eff6ff; border: 1px dashed #93c5fd; border-radius: 6px; padding: 3px 8px; cursor: pointer; margin: 0 0 8px; }
        .print-only { display: none; }
        .cf-foot { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 30px; }
        .cf-sign { width: 260px; font-weight: 600; } .cf-sign .line { border-top: 1px solid #000; margin-top: 50px; padding-top: 4px; }
        .chk { display: inline-flex; align-items: center; gap: 3px; margin-right: 10px; }
        .cf-controls { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
        .cf-controls label { font-size: 12px; font-weight: 600; color: #334155; display: block; margin-bottom: 3px; }
        .cf-controls input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
        .cf-btn { padding: 8px 14px; border-radius: 6px; font-weight: 600; cursor: pointer; border: 0; display: inline-flex; align-items: center; gap: 6px; color: #fff; }
        .cf-btn.blue { background: #2563eb; } .cf-btn.green { background: #16a34a; } .cf-btn.gray { background: #475569; }
        .cf-btn:disabled { opacity: .6; cursor: not-allowed; }

        @media print {
          @page { size: A4 portrait; margin: 7mm; }
          html, body { margin: 0 !important; padding: 0 !important; }
          * { box-sizing: border-box; }
          .no-print, .tools, .screen-only, .addbtn { display: none !important; }
          .print-only { display: inline !important; }
          .print-wrap { display: block !important; white-space: normal !important; word-break: break-word; overflow-wrap: anywhere; }
          #cf-sheet { width: var(--pw, 192mm); max-width: none; margin: 0 auto; zoom: var(--pz, 1); }
          .cf-sheet { font-size: 8.5px; }
          table.cf td, table.cf th, table.cf input, table.cf textarea.wrap-cell, table.cf select { font-size: 9px !important; }
          table.cf td, table.cf th { white-space: normal !important; word-break: break-word; overflow-wrap: anywhere; }
          table.cf input { background: transparent !important; }
          table.cf textarea.wrap-cell { background: transparent !important; overflow: visible !important; }
          table.cf, .cf-row-top, .cf-title, .cf-branch { page-break-inside: avoid; }
        }
      `}</style>

      <div className="cf-sheet">
        <div className="no-print cf-controls">
          <div>
            <label>Account Number</label>
            <input value={acc} onChange={(e) => setAcc(e.target.value)} placeholder="مثال: 002106" onKeyDown={(e) => e.key === 'Enter' && loadAccount()} />
          </div>
          <button onClick={() => loadAccount()} disabled={loading} className="cf-btn blue"><Search size={15} /> {loading ? '...' : 'بارگیری'}</button>
          <button onClick={save} disabled={saving || !a.accountNumber} className="cf-btn green"><Save size={15} /> {saving ? '...' : 'ذخیره در پروفایل'}</button>
          <button onClick={printSheet} className="cf-btn gray"><Printer size={15} /> پرینت</button>
          <div style={{ flexBasis: '100%', fontSize: 11, color: '#64748b' }}>
            ستون آبیِ سمت راستِ هر ردیف تسهیلات (فقط روی صفحه) برای انتخاب تسهیلاتِ مشتری. در «Security» می‌توانید مشخص کنید هر سند برای کدام تسهیلات است. مبالغ خودکار کاما می‌گیرند. خانه‌های آبی قابل‌ویرایش‌اند؛ موقع پرینت پاک می‌شوند و خروجی تک‌صفحه است.
          </div>
          <DraftDrop accountNo={a.accountNumber || acc} onExtracted={handleExtract} />
        </div>

        <div id="cf-sheet" ref={sheetRef}>
          <div className="cf-row-top">
            <div className="cf-logo"><b>بانک صادرات ایران — BANK SADERAT IRAN</b><span>U.A.E. · Credit Facility Dept.</span></div>
            <div className="cf-date"><div className="l">Date</div><input value={a.date} onChange={set('date')} /></div>
          </div>
          <div className="cf-title">CREDIT FILE SUMMARY (Corporate)</div>
          <div className="cf-branch">Branch Code and Name:&nbsp;
            <input value={a.branchCode} onChange={set('branchCode')} placeholder="2900" style={{ width: 70 }} /> -
            <input value={a.branchName} onChange={set('branchName')} placeholder="Ajman" style={{ width: '55%' }} />
          </div>

          {/* Account Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Account Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Details</td><td>S/No.</td><td>Description</td><td>Details</td></tr>
            <tr><td className="sn">1</td><td className="desc">Customer&rsquo;s Name</td><td><input value={a.customerName} onChange={set('customerName')} /></td>
              <td className="sn">4</td><td className="desc">Rating</td><td><input value={a.rating} onChange={set('rating')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Account Number</td><td><input value={a.accountNumber} onChange={set('accountNumber')} /></td>
              <td className="sn">5</td><td className="desc">Call Report</td><td><input value={a.callReport} onChange={set('callReport')} /></td></tr>
            <tr><td className="sn">3</td><td className="desc">Business Type</td><td><input value={a.businessType} onChange={set('businessType')} /></td>
              <td className="sn">6</td><td className="desc">No. of Previous Files</td><td><input value={a.previousFiles} onChange={set('previousFiles')} /></td></tr>
          </tbody></table>

          {/* KYC Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>KYC Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Number</td><td>Issue Date</td><td>Expiry</td><td>Remarks</td></tr>
            <tr><td className="sn">1</td><td className="desc">Trade License</td>
              <td><input value={a.tradeLicenseNum} onChange={set('tradeLicenseNum')} /></td><td><input value={a.tradeLicenseIssue} onChange={set('tradeLicenseIssue')} /></td>
              <td><input value={a.tradeLicenseExpiry} onChange={set('tradeLicenseExpiry')} /></td><td><WrapInput value={a.tradeLicenseRemarks} onChange={set('tradeLicenseRemarks')} /></td></tr>
            <tr><td className="sn">2</td><td className="desc">Passport</td>
              <td><input value={a.passportNum} onChange={set('passportNum')} /></td><td><input value={a.passportIssue} onChange={set('passportIssue')} /></td>
              <td><input value={a.passportExpiry} onChange={set('passportExpiry')} /></td><td><WrapInput value={a.passportRemarks} onChange={set('passportRemarks')} /></td></tr>
            <tr><td className="sn">3</td><td className="desc">Manager Emirates ID</td>
              <td><input value={a.managerIdNum} onChange={set('managerIdNum')} /></td><td><input value={a.managerIdIssue} onChange={set('managerIdIssue')} /></td>
              <td><input value={a.managerIdExpiry} onChange={set('managerIdExpiry')} /></td><td><WrapInput value={a.managerIdRemarks} onChange={set('managerIdRemarks')} /></td></tr>
          </tbody></table>

          <CountryDataList />
          <datalist id="cf-partner-names">{partnerNameList.map((n) => <option key={n} value={n} />)}</datalist>
          {/* Partners */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={6}>Partners Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Partner&rsquo;s Name</td><td>Nationality</td><td>Share</td><td>Remarks</td><td className="tools">حذف</td></tr>
            {partners.map((p, i) => (
              <tr key={p.uid}>
                <td className="sn">{i + 1}</td>
                <td><input list="cf-partner-names" value={p.name} onChange={setPartner(p.uid, 'name')} placeholder="جستجو / نام شریک" /></td>
                <td><CountryInput value={p.nationality} onChange={setPartner(p.uid, 'nationality')} /></td>
                <td><PctInput value={p.share} onValue={setPartnerV(p.uid, 'share')} /></td>
                <td><WrapInput value={p.remarks} onChange={setPartner(p.uid, 'remarks')} /></td>
                <td className="tools"><button title="حذف" onClick={() => delPartner(p.uid)}><Trash2 size={13} /></button></td>
              </tr>
            ))}
          </tbody></table>
          <button className="addbtn" onClick={addPartner}><Plus size={13} /> افزودن شریک</button>

          {/* Facility Details */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={7}>Facility Details</td></tr>
            <tr className="hdr"><td>S/No.</td><td>Description</td><td>Amount (AED)</td><td>Rate Of Int. / Margin</td><td>Expiry Date</td><td>Notices</td><td className="tools">تسهیلات / حذف</td></tr>
            {facRows.map((r, i) => (
              <tr key={r.uid}>
                <td className="sn">{i + 1}</td>
                <td className="desc">{r.custom ? <input value={r.label} onChange={setFac(r.uid, 'label')} placeholder="نوع تسهیلات" /> : r.label}</td>
                <td><AmtInput value={r.amount} onValue={setFacV(r.uid, 'amount')} /></td>
                <td><PctInput value={r.rate} onValue={setFacV(r.uid, 'rate')} /></td>
                <td><input value={r.expiry} onChange={setFac(r.uid, 'expiry')} /></td>
                <td><WrapInput value={r.notices} onChange={setFac(r.uid, 'notices')} /></td>
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
                <td><AmtInput value={r.aed} onValue={setSecV(r.uid, 'aed')} /></td>
                <td><AmtInput value={r.usd} onValue={setSecV(r.uid, 'usd')} /></td>
                <td><AmtInput value={r.irr} onValue={setSecV(r.uid, 'irr')} /></td>
                <td><AmtInput value={r.other} onValue={setSecV(r.uid, 'other')} /></td>
                <td className="tools">{r.custom && <button title="حذف ردیف" onClick={() => delSecRow(r.uid)}><Trash2 size={13} /></button>}</td>
              </tr>
            ))}
            <tr><td className="sn">{secRows.length + 1}</td><td className="desc">Undertaking Forms From</td><td colSpan={5}>
              <label className="chk"><input type="checkbox" checked={a.undertakingGuarantor} onChange={set('undertakingGuarantor')} style={{ width: 'auto' }} /> GUARANTOR/S</label>
              <label className="chk"><input type="checkbox" checked={a.undertakingPartner} onChange={set('undertakingPartner')} style={{ width: 'auto' }} /> PARTNER/S</label>
            </td><td className="tools" /></tr>
          </tbody></table>
          <button className="addbtn" onClick={addSecRow}><Plus size={13} /> افزودن ردیف مدرک/وثیقه</button>

          {/* Mortgaged Properties (املاک) — two-way synced with the customer's properties list */}
          <table className="cf"><tbody>
            <tr><td className="band" colSpan={7}>Mortgaged Properties / املاک<span className="screen-only" style={{ fontWeight: 400, fontSize: 9 }}>&nbsp;(نوع و ارزیابی اجباری‌اند؛ بقیه اختیاری و در دیتابیس ذخیره می‌شود)</span></td></tr>
            <tr className="hdr"><td>S/No.</td><td>Type *</td><td>Address</td><td>City</td><td>Valuation *</td><td>Mortgage Amt</td><td className="tools">جزئیات / حذف</td></tr>
            {props.map((p, i) => (
              <React.Fragment key={i}>
                <tr>
                  <td className="sn">{i + 1}</td>
                  <td><input value={p.prop_type} onChange={setProp(i, 'prop_type')} placeholder="Land & Building" /></td>
                  <td><WrapInput value={p.address} onChange={setProp(i, 'address')} /></td>
                  <td><input value={p.city} onChange={setProp(i, 'city')} /></td>
                  <td><div style={{ display: 'flex', gap: 2, alignItems: 'center' }}><AmtInput value={p.valuation} onValue={setPropV(i, 'valuation')} /><select value={p.valuation_currency} onChange={setProp(i, 'valuation_currency')} style={{ flex: '0 0 auto', fontSize: 9, border: 0, background: '#eaf3ff' }}>{CCY.map((c) => <option key={c} value={c}>{c}</option>)}</select></div></td>
                  <td><div style={{ display: 'flex', gap: 2, alignItems: 'center' }}><AmtInput value={p.mortgage_amount} onValue={setPropV(i, 'mortgage_amount')} /><select value={p.mortgage_currency} onChange={setProp(i, 'mortgage_currency')} style={{ flex: '0 0 auto', fontSize: 9, border: 0, background: '#eaf3ff' }}>{CCY.map((c) => <option key={c} value={c}>{c}</option>)}</select></div></td>
                  <td className="tools">
                    <button className="screen-only" title="جزئیات بیشتر" onClick={() => toggleProp(i)} style={{ color: '#2563eb' }}>⋯</button>
                    <button title="حذف" onClick={() => delProp(i)}><Trash2 size={13} /></button>
                  </td>
                </tr>
                {p._open && (
                  <tr className="screen-only"><td /><td colSpan={6}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 6, padding: '4px 0' }}>
                      <label style={{ fontSize: 10 }}>پلاک ثبتی<input value={p.plate_no} onChange={setProp(i, 'plate_no')} /></label>
                      <label style={{ fontSize: 10 }}>شماره سند رهنی<input value={p.mortgage_deed_no} onChange={setProp(i, 'mortgage_deed_no')} /></label>
                      <label style={{ fontSize: 10 }}>تاریخ ترهین<input value={p.mortgage_date} onChange={setProp(i, 'mortgage_date')} /></label>
                      <label style={{ fontSize: 10 }}>انقضای بیمه<input value={p.insurance_expiry} onChange={setProp(i, 'insurance_expiry')} /></label>
                      <label style={{ fontSize: 10 }}>سن ساختمان<input value={p.building_age} onChange={setProp(i, 'building_age')} /></label>
                      <label style={{ fontSize: 10 }}>مساحت زمین (م²)<input value={p.land_area} onChange={setProp(i, 'land_area')} /></label>
                      <label style={{ fontSize: 10, gridColumn: '1 / span 3' }}>توضیحات<input value={p.remarks} onChange={setProp(i, 'remarks')} /></label>
                    </div>
                  </td></tr>
                )}
              </React.Fragment>
            ))}
          </tbody></table>
          <button className="addbtn" onClick={addProp}><Plus size={13} /> افزودن ملک</button>

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
