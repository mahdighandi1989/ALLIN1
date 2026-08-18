'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search } from 'lucide-react'
import { lookupAccount, BRANCHES, ACCOUNT_COUNT } from './accounts'
import { BANK_LOGO } from './logo'
import { customersApi, crmApi, auditApi, vouchersApi, parseApiError } from '@/lib/api'
import { dmySlash } from '@/lib/dates'
import { useFormDesign, Movable, DesignControls, DesignPanel, DesignState } from '@/lib/formDesign'
import toast from 'react-hot-toast'

// Faithful re-implementation of the macro workbook
// "Securities (Contra-PerContra) (FOR CHQS)" — laid out to match the original
// Excel form (DEBIT/CREDIT headings, Bank Saderat logo, lavender banner) and
// sized so two vouchers fill one A4 page; cutting it in half gives two A5
// vouchers. GL logic:
//   DEBIT  (SECURITIES) = <branch>-860185-784-090
//   CREDIT (PER CONTRA) = <branch>-869900-784-590

function todayDMY(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}
function money(n: string): string {
  const v = Number(String(n).replace(/,/g, ''))
  return isFinite(v) && v !== 0 ? v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ''
}

type VProps = {
  kind: 'DEBIT' | 'CREDIT'
  title: string
  date: string
  acNo: string
  amount: string
  currency: string
  ourRef: string
  description: string
  acName: string
  extraLines?: string[]   // v95 — reversal stamps (SECURITY CHQ REVERSAL / LOAN SETTLED)
  amountText?: string     // v100 — verbatim amount cell (IRR mode prints the CHEQUE COUNT, not a money value)
}

function Voucher({ kind, title, date, acNo, amount, currency, ourRef, description, acName, extraLines, amountText, d, prefix }: VProps & { d: DesignState; prefix: string }) {
  const M = (id: string, node: React.ReactNode, block = false) => <Movable d={d} id={`${prefix}-${id}`} label={id} block={block}>{node}</Movable>
  return (
    <div className="vch" dir="ltr">
      <div className="vch-head">
        <div className="vch-kind">{M('kind', kind)}</div>
        <div className="vch-logo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={BANK_LOGO} alt="Bank Saderat Iran" />
          <div className="vch-iv">INTERNAL VOUCHER</div>
        </div>
      </div>

      <div className="vch-banner">{M('title', title)}</div>
      <div className="vch-daterow">DATE :&nbsp;&nbsp;{M('date', date)}</div>

      <div className="vch-acrow">
        <div><span className="vch-aclbl">A/c No. :</span>{M('acno', <span className="vch-ac">{acNo}</span>)}</div>
        {M('amount', amountText !== undefined ? (
          // v101 — the cheque COUNT sits in a labelled box (not loose on the page)
          <div className="vch-amt vch-qty"><span className="vch-qty-lbl">AMOUNT / QUANTITY</span><span className="vch-qty-box">{amountText || '—'}</span></div>
        ) : (
          <div className="vch-amt">{amount ? `${currency} ${money(amount)}` : '**********'}</div>
        ), true)}
      </div>

      <div className="vch-ref">
        <div className="vch-ref-lbl">OUR REF :</div>
        <div className="vch-ref-body">
          {M('refno', <div className="vch-ref-no">{ourRef}</div>, true)}
          {M('refdesc', <div className="vch-ref-desc">{description}</div>, true)}
          {M('refname', <div className="vch-ref-name">{acName}</div>, true)}
          {(extraLines || []).map((ln, i) => (
            <div key={i} className="vch-ref-desc" style={{ fontWeight: 800, borderTop: i === 0 ? '1pt solid #000' : undefined, paddingTop: i === 0 ? '1mm' : undefined }}>{ln}</div>
          ))}
        </div>
      </div>

      <div className="vch-spacer" />
      <div className="vch-foot">
        <div>Prepared By.<span className="vch-sigline" /></div>
        <div>Authorized Signatures<span className="vch-sigline" /></div>
      </div>
    </div>
  )
}

// v99 → QUARANTINED in v100 (docs/REMOVAL_CANDIDATES.md): this boxed layout
// copied the IRR workbook's look; the owner rejected it — the IRR slip must use
// the SAME Voucher frame as the normal/reversal slips, only the contents differ.
// Kept unused (not deleted) per rule 2.
function VoucherIRR({ kind, title, date, branchNo, acctNo, tranCode, narrative, count, d, prefix }:
  { kind: 'DEBIT' | 'CREDIT'; title: string; date: string; branchNo: string; acctNo: string;
    tranCode: string; narrative: string[]; count: string; d: DesignState; prefix: string }) {
  const M = (id: string, node: React.ReactNode, block = false) => <Movable d={d} id={`${prefix}-${id}`} label={id} block={block}>{node}</Movable>
  const box = (label: string, value: string, wide = false) => (
    <div style={{ marginTop: '2.5mm' }}>
      <div style={{ border: '1.2pt solid #000', display: 'inline-block', fontSize: '8.5pt', fontWeight: 800, padding: '0.4mm 1.5mm' }}>{label}</div>
      <div style={{ border: '1.2pt solid #000', borderTop: 0, display: 'flex', width: wide ? '58mm' : '30mm' }}>
        {value.split('').map((ch, i) => (
          <span key={i} style={{ flex: 1, textAlign: 'center', borderLeft: i ? '0.8pt solid #000' : undefined, fontSize: '11pt', fontWeight: 800, padding: '0.6mm 0' }}>{ch}</span>
        ))}
      </div>
    </div>
  )
  return (
    <div className="vch" dir="ltr">
      <div className="vch-head">
        <div className="vch-kind">{M('kind', kind)}</div>
        <div className="vch-logo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={BANK_LOGO} alt="Bank Saderat Iran" />
          <div className="vch-iv">INTERNAL VOUCHER</div>
        </div>
      </div>
      <div className="vch-banner">{M('title', title)}</div>
      <div className="vch-daterow">DATE :&nbsp;&nbsp;{M('date', date)}</div>
      <div style={{ display: 'flex', gap: '8mm', alignItems: 'flex-start' }}>
        <div style={{ flex: '0 0 auto' }}>
          {M('branch', box('BRANCH NO.', branchNo || '    '), true)}
          {M('acct', box('ACCOUNT NO.', acctNo || '         ', true), true)}
          {M('tran', box('TRAN. CODE', tranCode || '   '), true)}
        </div>
        <div style={{ flex: 1, marginTop: '2.5mm' }}>
          <div style={{ fontSize: '9pt', fontWeight: 800 }}>TRANSACTION NARRATIVE</div>
          <div style={{ border: '1.2pt solid #000' }}>
            {narrative.map((ln, i) => (
              <div key={i} style={{ borderTop: i ? '0.8pt solid #000' : undefined, fontSize: '9pt', fontWeight: 600, padding: '1mm 1.5mm', minHeight: '5mm' }}>{ln}</div>
            ))}
          </div>
          {M('amount', (
            <div style={{ marginTop: '4mm', display: 'flex', alignItems: 'center', gap: '3mm' }}>
              <span style={{ fontSize: '13pt', fontWeight: 900 }}>AMOUNT</span>
              <span style={{ border: '1.2pt solid #000', minWidth: '34mm', textAlign: 'right', fontSize: '12pt', fontWeight: 800, padding: '1mm 2mm' }}>{count || '—'}</span>
            </div>
          ), true)}
        </div>
      </div>
      <div className="vch-spacer" />
      <div className="vch-foot">
        <div>INTIATED BY<span className="vch-sigline" /></div>
        <div>APPROVED BY<span className="vch-sigline" /></div>
      </div>
    </div>
  )
}

export default function VoucherPage() {
  const [acNo, setAcNo] = useState('')
  const [acName, setAcName] = useState('')
  const [branch, setBranch] = useState('')
  const [nameType, setNameType] = useState<'Borrower Name' | 'Guarantor Name'>('Borrower Name')
  const [guarantorName, setGuarantorName] = useState('')
  const [chqNo, setChqNo] = useState('')
  const [chqAmount, setChqAmount] = useState('')
  const [facilityId, setFacilityId] = useState('')
  const [currency, setCurrency] = useState('AED')
  const [date, setDate] = useState(todayDMY())
  const [notFound, setNotFound] = useState(false)
  const [accountCount, setAccountCount] = useState<number | null>(null)
  const [guarantors, setGuarantors] = useState<any[]>([])  // existing security cheques for this account
  const [facilities, setFacilities] = useState<any[]>([])
  const [selectedGid, setSelectedGid] = useState('')        // the picked existing cheque (for update)
  const [saving, setSaving] = useState(false)
  // v95/v99 — voucher mode: normal | reversal | irr. `reversal` stays a
  // derived boolean so every v95 code path is untouched.
  const [mode, setMode] = useState<'normal' | 'reversal' | 'irr'>('normal')
  const reversal = mode === 'reversal'
  const setReversal = (on: boolean) => setMode(on ? 'reversal' : 'normal')
  // v99 — IRR cheque inputs (ALL variable — defaults from the bank's IRR
  // workbook, every one editable; nothing fixed in code)
  const [irrCount, setIrrCount] = useState('1')
  const [irrAmount, setIrrAmount] = useState('')
  const [irrRate, setIrrRate] = useState('')
  const [irrLoanAed, setIrrLoanAed] = useState('')
  const [irrMonths, setIrrMonths] = useState('')
  const [irrCoverage, setIrrCoverage] = useState('')
  const [irrIssuer, setIrrIssuer] = useState('')
  const [irrIssuerBank, setIrrIssuerBank] = useState('')
  const [irrDrAcct, setIrrDrAcct] = useState('800016901')
  const [irrCrAcct, setIrrCrAcct] = useState('869999901')
  const [irrDrTran, setIrrDrTran] = useState('090')
  const [irrCrTran, setIrrCrTran] = useState('590')
  const [irrDrTitle, setIrrDrTitle] = useState('SECURITY DOC IRR TD')
  const [irrCrTitle, setIrrCrTitle] = useState('SECURITIES')
  const [settledFacility, setSettledFacility] = useState('')
  const [releasing, setReleasing] = useState(false)
  const previewRef = useRef<HTMLDivElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  // scoped: with an account typed/loaded, layout tweaks belong to THAT account
  // only; on a pristine form they update the base voucher template.
  const d = useFormDesign('voucherLayout_v1', acNo)
  const lookupTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Live customer count for the helper text (instead of the bundled 556).
  useEffect(() => {
    customersApi.list({ page: 1, page_size: 1 }).then((r) => setAccountCount(r.total)).catch(() => {})
  }, [])

  // Scale the on-screen preview to fit its column → no horizontal scroll. Uses
  // transform:scale (reliable + affects nothing in print, where it's reset). The
  // wrapper height is collapsed to the scaled height so there's no empty gap.
  useEffect(() => {
    const el = previewRef.current
    const wrap = wrapRef.current
    if (!el || !wrap) return
    const fit = () => {
      el.style.transform = 'none'
      const natW = el.offsetWidth || 1
      const natH = el.offsetHeight
      const s = Math.min(1, wrap.clientWidth / natW)
      el.style.transform = `scale(${s})`
      wrap.style.height = s < 1 ? `${Math.ceil(natH * s)}px` : 'auto'
    }
    fit()
    const ro = new ResizeObserver(fit)
    ro.observe(wrap.parentElement || wrap)
    window.addEventListener('resize', fit)
    return () => { ro.disconnect(); window.removeEventListener('resize', fit) }
  }, [])

  const onAcctLookup = (value: string) => {
    setAcNo(value)
    // Instant local hit from the bundled register…
    const hit = lookupAccount(value)
    if (hit) { setAcName(hit.name); setBranch(hit.branch); setNotFound(false) }
    else setNotFound(value.trim().length > 0)
    // …then a debounced live lookup against the full customer base in the DB.
    if (lookupTimer.current) clearTimeout(lookupTimer.current)
    const q = value.trim()
    if (q.length >= 5) {
      lookupTimer.current = setTimeout(async () => {
        try {
          const d: any = await customersApi.detail(q)
          const c = d.customer || {}
          if (c.name) setAcName(c.name)
          const code = d.profile?.data?.branch_code || String(c.branch || '').match(/\d{4}/)?.[0] || ''
          if (code) setBranch(code)
          setGuarantors(Array.isArray(d.guarantors) ? d.guarantors : [])
          setFacilities(Array.isArray(d.facilities) ? d.facilities : [])
          setNotFound(false)
        } catch { /* keep the local result / not-found state */ }
      }, 400)
    }
  }

  const refreshGuarantors = async (acct: string) => {
    try { setGuarantors(await crmApi.listGuarantors(acct)) } catch { /* ignore */ }
  }

  // Fill the form from a stored cheque record. The name slot follows whether the
  // recorded name is the account holder (Borrower) or someone else (Guarantor).
  const applyChequeRecord = (g: any) => {
    if (!g) return
    if (g.cheque_no != null) setChqNo(String(g.cheque_no))
    if (g.cheque_amount != null) setChqAmount(String(g.cheque_amount))
    if (g.facility_id) setFacilityId(String(g.facility_id))
    if (g.branch) setBranch(String(g.branch))
    const nm = g.guarantor_name ? String(g.guarantor_name) : ''
    if (nm) {
      if (acName && nm === acName) setNameType('Borrower Name')
      else { setNameType('Guarantor Name'); setGuarantorName(nm) }
    }
    // v101 — an IRR cheque record also carries the rial details the import
    // extraction stored; picking the cheque fills them (still editable).
    if (g.irr_amount) setIrrAmount(String(g.irr_amount))
    if (g.irr_rate) setIrrRate(String(g.irr_rate))
    if (g.coverage_pct) setIrrCoverage(String(g.coverage_pct))
    if (g.issuer_bank_code) setIrrIssuerBank(String(g.issuer_bank_code))
    if (nm && String(g.cheque_currency || '') === 'IRR') setIrrIssuer(nm)
    applyFacilityDetails(String(g.facility_id || ''))
    setSelectedGid(g.id || '')
  }

  // v101 — the linked facility record supplies the AED loan amount / tenor for
  // the IRR narrative (matched by the bank reference in Facility.name, or id).
  const applyFacilityDetails = (ref: string) => {
    const v = ref.trim()
    if (!v) return
    const f = facilities.find((x) => String(x.name || '') === v || String(x.id || '') === v)
    if (!f) return
    if (f.amount != null && Number(f.amount)) setIrrLoanAed(String(Math.round(Number(f.amount))))
    if (f.tenor_months) setIrrMonths(String(f.tenor_months))
  }

  const pickGuarantor = (id: string) => {
    setSelectedGid(id)
    applyChequeRecord(guarantors.find((x) => x.id === id))
  }

  // Selecting/typing a facility reference → if exactly one cheque is recorded for
  // it, auto-fill; otherwise the CHQ NO / AMOUNT lists narrow to that facility.
  const onFacilityChange = (value: string) => {
    setFacilityId(value)
    setSelectedGid('')
    const v = value.trim()
    const m = v ? guarantors.filter((g) => String(g.facility_id || '') === v) : []
    if (m.length === 1) applyChequeRecord(m[0])
    else applyFacilityDetails(v)   // v101 — at least the loan amount/tenor
  }

  // Picking a cheque number fills its amount + name (scoped to the chosen facility).
  const onChqNoChange = (value: string) => {
    setChqNo(value)
    const v = value.trim()
    const fac = facilityId.trim()
    const g = guarantors.find((x) => String(x.cheque_no || '') === v && (!fac || String(x.facility_id || '') === fac))
    if (g) applyChequeRecord(g)
  }

  // Save (upsert) under the account/facility — same Guarantor record the customer
  // page shows (two-way, no islands). No explicit id: the backend matches by
  // (account, cheque_no), so a SAME cheque updates and a NEW cheque number ADDS.
  const saveGuarantor = async () => {
    const acct = acNo.trim()
    const name = (nameType === 'Borrower Name' ? acName : guarantorName).trim()
    if (!acct) { toast.error('شماره حساب را وارد کنید'); return }
    if (!name) { toast.error('نام (روی چک) لازم است'); return }
    setSaving(true)
    try {
      const res = await crmApi.addGuarantor(acct, {
        guarantor_name: name,
        cheque_no: chqNo.trim() || undefined,
        cheque_amount: Number(String(chqAmount).replace(/,/g, '')) || undefined,
        issuing_bank: 'BSI',
        facility_id: facilityId.trim() || undefined,
        branch: branch.trim() || undefined,
      })
      await refreshGuarantors(acct)
      toast.success(res?.created ? 'چکِ جدید ذیلِ تسهیلات ثبت شد' : 'چک ضمانتی به‌روزرسانی شد')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSaving(false)
    }
  }

  // v95 — reversal write path: stamp the cheque as RETURNED on its own record
  // (nothing deleted; the customer profile + activity log carry the release).
  const releaseCheque = async () => {
    const acct = acNo.trim()
    if (!acct) { toast.error('شماره حساب را وارد کنید'); return }
    if (!chqNo.trim()) { toast.error('شمارهٔ چک برای ثبتِ خروج لازم است'); return }
    setReleasing(true)
    try {
      const r = await crmApi.releaseCheque(acct, {
        cheque_no: chqNo.trim(),
        facility_id: facilityId.trim() || undefined,
        settled_facility: settledFacility.trim() || undefined,
        date,
        // v98 — creation details for the both-unknown path (never-recorded facility)
        guarantor_name: (nameType === 'Borrower Name' ? acName : guarantorName).trim() || undefined,
        cheque_amount: Number(String(chqAmount).replace(/,/g, '')) || undefined,
        branch: branch.trim() || undefined,
      })
      if (r.ok === false) {
        // v98 triage: a lone mismatch is most likely MY typo — warn, change nothing
        toast.error(r.message || 'ثبت نشد', { duration: 9000 })
        return
      }
      await refreshGuarantors(acct)
      toast.success(r.created
        ? 'تسهیلات/چک قبلاً ثبت نشده بود — همین حالا ثبت و خروجش زده شد'
        : r.released ? `خروجِ چک ثبت شد (${r.released} رکورد)` : 'این چک قبلاً خروج خورده بود — تاریخ/یادداشت به‌روزرسانی شد')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setReleasing(false)
    }
  }

  // v99 — the IRR narrative lines, assembled ONLY from the inputs
  const nfmt = (v: string) => { const n = Number(String(v).replace(/,/g, '')); return isFinite(n) && n !== 0 ? n.toLocaleString('en-US') : String(v || '').trim() }
  const irrNarrative = [
    `AC NO ${acNo}${acName ? `   M/S.  ${acName}` : ''}`,
    `CHQ NO ${chqNo}${irrAmount ? `  FOR IRR ${nfmt(irrAmount)}/-` : ''}${irrRate ? `   RATE@ IRR ${nfmt(irrRate)}/-` : ''}`,
    `${irrLoanAed ? `LOAN AMOUNT AED ${nfmt(irrLoanAed)}/-` : ''}${irrMonths ? ` FOR ${irrMonths} MONTHS` : ''}${irrCoverage ? ` @ ${irrCoverage}% LOAN AMOUNT` : ''}`.trim(),
    `${irrIssuer ? `IRR CHQ FOR ${irrIssuer}` : ''}${irrIssuerBank ? ` (${irrIssuerBank})` : ''}`.trim(),
  ]
  const saveIrrCheque = async () => {
    const acct = acNo.trim()
    if (!acct) { toast.error('شماره حساب را وارد کنید'); return }
    if (!chqNo.trim()) { toast.error('شمارهٔ چکِ ریالی لازم است'); return }
    // v102 — a rial cheque is always written by a THIRD PARTY (guarantor
    // nature); it is never the UAE borrower's own cheque, so the record's name
    // must be the issuer — no silent fallback to the account holder.
    const issuer = irrIssuer.trim()
    if (!issuer) { toast.error('نامِ صادرکنندهٔ چکِ ریالی لازم است — چکِ ریالی صادرهٔ شخصِ ثالث است، نه گیرندهٔ تسهیلات'); return }
    setSaving(true)
    try {
      const res = await crmApi.addGuarantor(acct, {
        guarantor_name: issuer,
        cheque_no: chqNo.trim() || undefined,
        issuing_bank: (irrIssuerBank.split('-')[0] || 'IRR').trim().slice(0, 45) || undefined,
        facility_id: facilityId.trim() || undefined,
        branch: branch.trim() || undefined,
        cheque_currency: 'IRR',
        irr_amount: irrAmount.trim() || undefined,
        irr_rate: irrRate.trim() || undefined,
        coverage_pct: irrCoverage.trim() || undefined,
        issuer_bank_code: irrIssuerBank.trim() || undefined,
      } as any)
      await refreshGuarantors(acct)
      toast.success(res?.created ? 'چکِ ریالی ذیلِ تسهیلات ثبت شد' : 'چکِ ریالی به‌روزرسانی شد')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally { setSaving(false) }
  }

  const nameOnCheque = nameType === 'Borrower Name' ? acName : guarantorName
  // Cheques under the selected facility (if any) drive the CHQ NO / AMOUNT lists;
  // otherwise all of the account's cheques do.
  const facSel = facilityId.trim()
  const facCheques = facSel ? guarantors.filter((g) => String(g.facility_id || '') === facSel) : []
  const sourceCheques = facCheques.length ? facCheques : guarantors
  const chqNos = Array.from(new Set(sourceCheques.map((g) => g.cheque_no).filter(Boolean)))
  const chqAmounts = Array.from(new Set(sourceCheques.map((g) => g.cheque_amount).filter((v) => v != null).map(String)))
  const guarantorNames = Array.from(new Set(guarantors.map((g) => g.guarantor_name).filter(Boolean)))
  // v101 — suggestion pools for the IRR inputs, fed by whatever the import
  // extraction (or earlier manual saves) already stored for this account.
  const uniqVals = (xs: any[]) => Array.from(new Set(xs.filter((v) => v != null && String(v).trim() !== '').map((v) => String(v))))
  const sgIrrAmounts = uniqVals(sourceCheques.map((g) => g.irr_amount))
  const sgIrrRates = uniqVals(sourceCheques.map((g) => g.irr_rate))
  const sgIrrCoverages = uniqVals(sourceCheques.map((g) => g.coverage_pct))
  const sgIrrIssuers = uniqVals(guarantors.map((g) => g.guarantor_name))
  const sgIrrBanks = uniqVals(guarantors.map((g) => g.issuer_bank_code))
  const sgFacAmounts = uniqVals(facilities.map((f) => (f.amount != null && Number(f.amount) ? Math.round(Number(f.amount)) : null)))
  const sgFacMonths = uniqVals(facilities.map((f) => f.tenor_months))
  // The bank's real facility REFERENCE lives in Facility.name (e.g. "182/4/1099/2025",
  // "STF 1251218000001", "PIM …"), NOT the internal F-… id. Suggest those.
  const facilityIds = Array.from(new Set([
    ...facilities.map((f) => f.name),
    ...guarantors.map((g) => g.facility_id),
  ].filter((x) => x && String(x).trim() && x !== '???')))
  const debitGL = branch ? `${branch}-860185-784-090` : ''
  const creditGL = branch ? `${branch}-869900-784-590` : ''
  // v95 — REVERSAL swaps the GL sides (mirrors the bank's own reversal workbook):
  //   CREDIT (PER CONTRA)             = <branch>-860185-784-590
  //   DEBIT  (SECURITY HELD CHEQUES)  = <branch>-869900-784-090
  const revCreditGL = branch ? `${branch}-860185-784-590` : ''
  const revDebitGL = branch ? `${branch}-869900-784-090` : ''
  // v97 — the settlement line is FREE TEXT printed VERBATIM: exactly what the
  // user typed, no automatic «LOAN SETTLED» prefix («LOAN SETTLED» was only the
  // sample workbook's wording — the owner writes their own, e.g.
  // «O.D & C.D RENEWED WITH NEW SECURITIES»). Empty input ⇒ no line at all.
  const revLines = ['SECURITY CHQ REVERSAL', ...(settledFacility.trim() ? [settledFacility.trim()] : [])]
  // v100 — IRR slips reuse the standard Voucher frame; the A/c No is the same
  // dashed string style as the other slips (branch-account-trancode), built from
  // the editable inputs (empty parts simply drop out).
  // v101 — a digits-only GL account longer than 6 gets a small dash after the
  // 6-digit base (800016901 → 800016-901), per the bank's written form. Display
  // only; an account typed WITH its own dashes is left as-is.
  const fmtGlAcct = (a: string) => { const t = a.trim(); return /^\d{7,}$/.test(t) ? `${t.slice(0, 6)}-${t.slice(6)}` : t }
  const irrDebitGL = [branch.trim(), fmtGlAcct(irrDrAcct), irrDrTran.trim()].filter(Boolean).join('-')
  const irrCreditGL = [branch.trim(), fmtGlAcct(irrCrAcct), irrCrTran.trim()].filter(Boolean).join('-')
  // Ref-body content for IRR: the cheque line replaces the normal description,
  // the loan/coverage + issuer lines print as extra lines (only when non-empty).
  const irrChqLine = irrNarrative[1]
  const irrExtraLines = [irrNarrative[2], irrNarrative[3]].filter(Boolean)
  const ourRef = useMemo(() => [acNo, facilityId].filter(Boolean).join(' _ '), [acNo, facilityId])
  const description = `CHQ NO ${chqNo}_${nameType}: ${nameOnCheque}`
  // v105 — ONE spec drives the Excel/Word template exports: exactly the values
  // the preview renders for the CURRENT mode (no parallel logic to drift).
  const buildSlips = () => {
    const amt = chqAmount ? `${currency} ${money(chqAmount)}`.trim() : ''
    if (mode === 'irr') {
      const n = irrCount.trim()
      return [
        { kind: 'DEBIT', title: irrDrTitle, date, acNo: irrDebitGL, amount: n, amountBoxed: true, ourRef, description: irrChqLine, acName, extraLines: irrExtraLines },
        { kind: 'CREDIT', title: irrCrTitle, date, acNo: irrCreditGL, amount: n, amountBoxed: true, ourRef, description: irrChqLine, acName, extraLines: irrExtraLines },
      ]
    }
    if (reversal) {
      return [
        { kind: 'CREDIT', title: 'PER CONTRA', date, acNo: revCreditGL, amount: amt, amountBoxed: false, ourRef, description, acName, extraLines: revLines },
        { kind: 'DEBIT', title: 'SECURITY HELD CHEQUES', date, acNo: revDebitGL, amount: amt, amountBoxed: false, ourRef, description, acName, extraLines: revLines },
      ]
    }
    return [
      { kind: 'DEBIT', title: 'SECURITIES', date, acNo: debitGL, amount: amt, amountBoxed: false, ourRef, description, acName, extraLines: [] as string[] },
      { kind: 'CREDIT', title: 'PER CONTRA', date, acNo: creditGL, amount: amt, amountBoxed: false, ourRef, description, acName, extraLines: [] as string[] },
    ]
  }
  const saveBlobFile = (blob: Blob, name: string) => {
    const url = URL.createObjectURL(blob)
    const el = document.createElement('a')
    el.href = url; el.download = name
    document.body.appendChild(el); el.click(); document.body.removeChild(el)
    setTimeout(() => URL.revokeObjectURL(url), 4000)
  }
  const exportBase = () => `Voucher${mode === 'irr' ? ' IRR' : reversal ? ' Reversal' : ''}${chqNo.trim() ? ` - CHQ ${chqNo.trim()}` : ''}${acNo.trim() ? ` - ${acNo.trim()}` : ''}`.replace(/[\\/:*?"<>|]+/g, '-')
  const [exporting, setExporting] = useState<'' | 'xlsx' | 'docx'>('')
  const exportExcel = async () => {
    if (exporting) return
    setExporting('xlsx')
    const tId = toast.loading('در حالِ ساختِ فایلِ Excel…')
    try {
      const blob = await vouchersApi.exportExcel({ mode, slips: buildSlips().map((s) => ({
        kind: s.kind, title: s.title, date: s.date, ac_no: s.acNo, amount: s.amount,
        amount_boxed: s.amountBoxed, our_ref: s.ourRef, description: s.description,
        ac_name: s.acName, extra_lines: s.extraLines,
      })), logo_png: BANK_LOGO })
      saveBlobFile(blob, `${exportBase()}.xlsx`)
      toast.success('فایلِ Excel دانلود شد — سلول‌ها قابلِ پرکردن‌اند و پرینتِ خودِ Excel یک‌صفحهٔ A4 با همین قالب است', { id: tId })
      auditApi.logActivity({ action: 'export', entity_type: 'voucher', account_no: acNo || undefined, detail: `خروجیِ Excelِ سندِ انتظامی (${mode})${chqNo ? ` — چک ${chqNo}` : ''}` })
    } catch (e) {
      toast.error(parseApiError(e), { id: tId })
    } finally { setExporting('') }
  }
  const exportWord = async () => {
    if (exporting) return
    setExporting('docx')
    const tId = toast.loading('در حالِ ساختِ فایلِ Word…')
    try {
      const { buildVoucherDocx } = await import('./wordExport')
      const blob = await buildVoucherDocx(buildSlips(), 'voucher-v105')
      saveBlobFile(blob, `${exportBase()}.docx`)
      toast.success('فایلِ Word دانلود شد — هر دو سند در یک صفحهٔ A4، همه‌چیز قابلِ ویرایش', { id: tId })
      auditApi.logActivity({ action: 'export', entity_type: 'voucher', account_no: acNo || undefined, detail: `خروجیِ Wordِ سندِ انتظامی (${mode})${chqNo ? ` — چک ${chqNo}` : ''}` })
    } catch {
      toast.error('ساختِ Word ناموفق بود — دوباره تلاش کن', { id: tId })
    } finally { setExporting('') }
  }
  const field = 'w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      <style>{`
        /* ---- Voucher (matches the source Excel form) ---- */
        .vch { box-sizing: border-box; width: 100%; height: 135mm; border: 1.6pt solid #000;
               padding: 5mm 6mm 4mm; display: flex; flex-direction: column; color: #000;
               font-family: Arial, "Segoe UI", sans-serif; background: #fff; overflow: hidden; }
        .vch + .vch { border-top: 0; }
        .vch-head { display: flex; justify-content: space-between; align-items: flex-start; }
        .vch-kind { font-size: 30pt; font-weight: 900; letter-spacing: 1px; line-height: 0.9; }
        .vch-logo { text-align: right; line-height: 1; }
        .vch-logo img { height: 14mm; width: auto; display: inline-block; }
        .vch-iv { font-size: 11pt; font-weight: 800; margin-top: 1.5mm; letter-spacing: 0.5px; }
        .vch-banner { background: #CCCCFF; border: 1pt solid #000; margin-top: 4mm; text-align: center;
                      font-size: 16pt; font-weight: 800; letter-spacing: 2px; padding: 1.5mm 0; }
        .vch-daterow { text-align: right; font-size: 11pt; font-weight: 700; margin-top: 2mm; }
        .vch-acrow { display: flex; justify-content: space-between; align-items: baseline; margin-top: 6mm; }
        .vch-aclbl { font-size: 13pt; font-weight: 800; margin-right: 4mm; }
        .vch-ac { font-size: 14pt; font-weight: 800; letter-spacing: 0.5px; }
        .vch-amt { font-size: 12pt; font-weight: 700; white-space: nowrap; }
        /* v101 — boxed cheque-count cell for the IRR slip */
        .vch-qty { display: flex; align-items: center; gap: 2.5mm; }
        .vch-qty-lbl { font-size: 9pt; font-weight: 800; letter-spacing: 0.2mm; }
        .vch-qty-box { border: 1.2pt solid #000; min-width: 20mm; text-align: center; font-size: 12pt; font-weight: 800; padding: 0.8mm 2mm; }
        .vch-ref { display: flex; border: 1.2pt solid #000; margin-top: 5mm; }
        .vch-ref-lbl { font-size: 10pt; font-weight: 800; padding: 2mm; border-right: 1.2pt solid #000;
                       display: flex; align-items: center; white-space: nowrap; }
        .vch-ref-body { flex: 1; }
        .vch-ref-no { font-size: 11pt; font-weight: 700; padding: 1.5mm 2mm 0; }
        .vch-ref-desc { font-size: 9.5pt; padding: 0 2mm 1.5mm; }
        .vch-ref-name { font-size: 10.5pt; font-weight: 800; padding: 1.5mm 2mm; border-top: 1pt solid #000; }
        .vch-spacer { flex: 1; }
        .vch-foot { display: flex; justify-content: space-between; font-size: 10pt; font-weight: 700; }
        .vch-sigline { display: block; width: 52mm; border-top: 1pt solid #000; margin-top: 8mm; }

        /* on-screen preview: the fixed-mm sheet is scaled (transform, via JS) to
           fit its column so there is no horizontal scroll; print resets it. */
        .vch-wrap { min-width: 0; overflow: hidden; }
        #voucher-print { width: 190mm; margin: 0 auto; background: #fff; transform-origin: top left; }

        @media print {
          /* Own the whole sheet: no @page margin (so nothing spills to a 2nd
             page and the browser adds no header/footer); the safe inner margins
             live on the voucher block itself. */
          @page { size: A4 portrait; margin: 0; }
          html, body { margin: 0 !important; padding: 0 !important; }
          /* The app shell uses min-h-screen (100vh ≈ one page); with the block's
             8mm top margin that totals ~305mm and spilled a blank 2nd page. Drop
             every forced full-height so the document is exactly as tall as the
             two vouchers (≈278mm) → one page. */
          html, body, .min-h-screen { min-height: 0 !important; height: auto !important; }
          header, .no-print { display: none !important; }
          main { max-width: none !important; width: 100% !important; padding: 0 !important; margin: 0 !important; }
          .voucher-grid { display: block !important; margin: 0 !important; }
          /* Fixed, centred block — 188mm wide leaves ~11mm each side and 8mm top,
             so left/right borders never reach the printer's non-printable edge.
             Two 135mm vouchers = 270mm; +8mm top = 278mm of a 297mm page →
             ~19mm bottom safety → always one page with full borders visible. */
          .vch-wrap { overflow: visible !important; height: auto !important; }
          #voucher-print { width: 188mm !important; margin: 8mm 11mm 0 11mm !important;
                           transform: none !important; page-break-inside: avoid; break-inside: avoid; }
          .vch { page-break-inside: avoid; break-inside: avoid; }
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-2 mb-1 no-print">
          <div className="bg-blue-600 text-white rounded-lg p-2"><Printer size={18} /></div>
          <div>
            <h1 className="text-lg font-bold text-gray-900" dir="rtl">سند انتظامی چک ضمانتی (Securities / Per‑Contra)</h1>
            <p className="text-gray-500 text-xs" dir="rtl">با وارد کردن شماره حساب، نام از دیتابیس ({(accountCount ?? ACCOUNT_COUNT).toLocaleString()} حساب) پر می‌شود. دو سند روی یک A4 — با نصف‌کردن، هر کدام یک A5.</p>
          </div>
        </div>

        <div className="voucher-grid grid grid-cols-1 gap-3 items-start mt-2">
          {/* ---- inputs (not printed) ---- */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 no-print" dir="rtl">
            <h2 className="font-bold text-gray-800 mb-2">ورودی‌ها</h2>
            <div className="flex gap-2 mb-2">
              <button type="button" onClick={() => setReversal(false)}
                className={`flex-1 rounded-lg py-1.5 text-sm font-bold border ${!reversal ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600 border-gray-300'}`}>سندِ عادی</button>
              <button type="button" onClick={() => setReversal(true)}
                className={`flex-1 rounded-lg py-1.5 text-sm font-bold border ${reversal ? 'bg-purple-600 text-white border-purple-600' : 'bg-white text-gray-600 border-gray-300'}`}>سندِ برگشتی (Reversal)</button>
              <button type="button" onClick={() => setMode('irr')}
                className={`flex-1 rounded-lg py-1.5 text-sm font-bold border ${mode === 'irr' ? 'bg-teal-600 text-white border-teal-600' : 'bg-white text-gray-600 border-gray-300'}`}>سندِ چکِ ریالی (IRR)</button>
            </div>
            {reversal && (
              <p className="text-xs text-purple-700 mb-2">برگرداندنِ چکِ ضمانتی: طرف‌های بدهکار/بستانکار جابه‌جا چاپ می‌شوند و با «ثبتِ خروجِ چک»، خروجِ چک با تاریخ و تسهیلاتِ تسویه‌شده ذیلِ همان رکوردِ چک در پروفایل ثبت می‌شود.</p>
            )}
            <div className="grid grid-cols-2 gap-2">
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">شماره حساب (A/C NO)</span>
                <div className="relative">
                  <input className={field} value={acNo} onChange={(e) => onAcctLookup(e.target.value)} placeholder="مثلاً 271520" inputMode="numeric" />
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                </div>
                {notFound && <span className="text-amber-600 text-xs">در دیتابیس یافت نشد؛ نام را دستی وارد کنید.</span>}
              </label>
              {guarantors.length > 0 && (
                <label className="col-span-2 text-sm">
                  <span className="text-gray-600">چک‌های ثبت‌شدۀ این حساب (برای پر کردن انتخاب کن)</span>
                  <select className={field} value={selectedGid} onChange={(e) => pickGuarantor(e.target.value)}>
                    <option value="">— چک جدید —</option>
                    {guarantors.map((g) => (
                      <option key={g.id} value={g.id}>
                        {[g.cheque_no, g.guarantor_name, g.cheque_amount, g.facility_id].filter(Boolean).join(' · ')}{g.released ? ` — خروج‌خورده ${g.released_date || ''}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">نام حساب (A/C NAME)</span>
                <input className={field} value={acName} onChange={(e) => setAcName(e.target.value)} placeholder="از روی شماره حساب پر می‌شود" />
              </label>
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">شناسه تسهیلات (FACILITY ID)</span>
                <input className={field} value={facilityId} onChange={(e) => onFacilityChange(e.target.value)} placeholder="STF1260603000001" list="vch-facids" />
                <datalist id="vch-facids">{facilityIds.map((n) => <option key={n} value={n} />)}</datalist>
              </label>
              <label className="text-sm">
                <span className="text-gray-600">شعبه (BRANCH)</span>
                <input className={field} value={branch} onChange={(e) => setBranch(e.target.value)} list="branches" placeholder="مثلاً 2776" />
                <datalist id="branches">{BRANCHES.map((b) => <option key={b} value={b} />)}</datalist>
              </label>
              {/* v102 — no «نوع نام» in IRR mode: a rial cheque is BY NATURE a
                  third-party (guarantor-type) instrument — the UAE borrower can
                  never be its writer, so the Borrower/Guarantor choice is
                  meaningless there (the dedicated issuer-name input rules). */}
              {mode !== 'irr' && (<>
                <label className="text-sm">
                  <span className="text-gray-600">نوع نام</span>
                  <select className={field} value={nameType} onChange={(e) => setNameType(e.target.value as any)}>
                    <option value="Borrower Name">Borrower Name</option>
                    <option value="Guarantor Name">Guarantor Name</option>
                  </select>
                </label>
                {nameType === 'Guarantor Name' && (
                  <label className="col-span-2 text-sm">
                    <span className="text-gray-600">نام ضامن (Guarantor)</span>
                    <input className={field} value={guarantorName} onChange={(e) => setGuarantorName(e.target.value)} list="vch-gnames" />
                    <datalist id="vch-gnames">{guarantorNames.map((n) => <option key={n} value={n} />)}</datalist>
                  </label>
                )}
              </>)}
              <label className="text-sm">
                <span className="text-gray-600">شماره چک (CHQ NO)</span>
                <input className={field} value={chqNo} onChange={(e) => onChqNoChange(e.target.value)} inputMode="numeric" list="vch-chqnos" />
                <datalist id="vch-chqnos">{chqNos.map((n) => <option key={n} value={n} />)}</datalist>
              </label>
              <label className="text-sm">
                <span className="text-gray-600">مبلغ چک (CHQ AMOUNT)</span>
                <input className={field} value={chqAmount} onChange={(e) => setChqAmount(e.target.value)} inputMode="numeric" placeholder="144000" list="vch-amts" />
                <datalist id="vch-amts">{chqAmounts.map((n) => <option key={n} value={n} />)}</datalist>
              </label>
              {mode === 'irr' && (<>
                <label className="text-sm"><span className="text-gray-600">تعدادِ چک (در AMOUNT چاپ می‌شود)</span>
                  <input className={field} value={irrCount} onChange={(e) => setIrrCount(e.target.value)} inputMode="numeric" /></label>
                <label className="text-sm"><span className="text-gray-600">مبلغِ چکِ ریالی (IRR)</span>
                  <input className={field} value={irrAmount} onChange={(e) => setIrrAmount(e.target.value)} inputMode="numeric" placeholder="6383360000000" list="vch-irr-amts" />
                  <datalist id="vch-irr-amts">{sgIrrAmounts.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="text-sm"><span className="text-gray-600">نرخِ تبدیل (IRR به ازای هر AED)</span>
                  <input className={field} value={irrRate} onChange={(e) => setIrrRate(e.target.value)} inputMode="numeric" placeholder="398960" list="vch-irr-rates" />
                  <datalist id="vch-irr-rates">{sgIrrRates.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="text-sm"><span className="text-gray-600">مبلغِ تسهیلات (AED)</span>
                  <input className={field} value={irrLoanAed} onChange={(e) => setIrrLoanAed(e.target.value)} inputMode="numeric" placeholder="8000000" list="vch-fac-amts" />
                  <datalist id="vch-fac-amts">{sgFacAmounts.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="text-sm"><span className="text-gray-600">مدت (ماه)</span>
                  <input className={field} value={irrMonths} onChange={(e) => setIrrMonths(e.target.value)} inputMode="numeric" placeholder="48" list="vch-fac-months" />
                  <datalist id="vch-fac-months">{sgFacMonths.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="text-sm"><span className="text-gray-600">پوشش (٪ از تسهیلات)</span>
                  <input className={field} value={irrCoverage} onChange={(e) => setIrrCoverage(e.target.value)} inputMode="numeric" placeholder="200" list="vch-irr-cov" />
                  <datalist id="vch-irr-cov">{sgIrrCoverages.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="col-span-2 text-sm"><span className="text-gray-600">نامِ صادرکنندهٔ چکِ ریالی</span>
                  <input className={field} value={irrIssuer} onChange={(e) => setIrrIssuer(e.target.value)} placeholder="M/s Hani pokht iraninan" list="vch-irr-issuers" />
                  <datalist id="vch-irr-issuers">{sgIrrIssuers.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="col-span-2 text-sm"><span className="text-gray-600">بانکِ صادرکننده (+ کد)</span>
                  <input className={field} value={irrIssuerBank} onChange={(e) => setIrrIssuerBank(e.target.value)} placeholder="karafarin bank - 5300114" list="vch-irr-banks" />
                  <datalist id="vch-irr-banks">{sgIrrBanks.map((n) => <option key={n} value={n} />)}</datalist></label>
                <label className="text-sm"><span className="text-gray-600">حسابِ بدهکار (DR)</span>
                  <input className={field} value={irrDrAcct} onChange={(e) => setIrrDrAcct(e.target.value)} inputMode="numeric" /></label>
                <label className="text-sm"><span className="text-gray-600">حسابِ بستانکار (CR)</span>
                  <input className={field} value={irrCrAcct} onChange={(e) => setIrrCrAcct(e.target.value)} inputMode="numeric" /></label>
                <label className="text-sm"><span className="text-gray-600">کدِ تراکنشِ DR</span>
                  <input className={field} value={irrDrTran} onChange={(e) => setIrrDrTran(e.target.value)} inputMode="numeric" /></label>
                <label className="text-sm"><span className="text-gray-600">کدِ تراکنشِ CR</span>
                  <input className={field} value={irrCrTran} onChange={(e) => setIrrCrTran(e.target.value)} inputMode="numeric" /></label>
                <label className="text-sm"><span className="text-gray-600">عنوانِ سندِ DR</span>
                  <input className={field} value={irrDrTitle} onChange={(e) => setIrrDrTitle(e.target.value)} /></label>
                <label className="text-sm"><span className="text-gray-600">عنوانِ سندِ CR</span>
                  <input className={field} value={irrCrTitle} onChange={(e) => setIrrCrTitle(e.target.value)} /></label>
              </>)}
              {reversal && (
                <label className="col-span-2 text-sm">
                  <span className="text-gray-600">شرحِ تسویه/برگشت (متنِ سطرِ دومِ سند — عیناً چاپ می‌شود)</span>
                  <input className={field} value={settledFacility} onChange={(e) => setSettledFacility(e.target.value)} placeholder="مثلاً STF1260603000001 یا 182/4/1099/2025" list="vch-facids" />
                  <span className="text-[11px] text-gray-400">هر متنی اینجا بنویسی «عیناً» به‌عنوانِ سطرِ دوم روی سند چاپ و همراهِ خروجِ چک در پروفایل ثبت می‌شود (مثلاً LOAN SETTLED یا O.D RENEWED WITH NEW SECURITIES)؛ خالی باشد چیزی چاپ نمی‌شود.</span>
                </label>
              )}
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">ارز / تاریخ</span>
                <div className="flex gap-2">
                  <input className={field} value={currency} onChange={(e) => setCurrency(e.target.value)} />
                  <input className={field} value={date} onChange={(e) => setDate(e.target.value)} onBlur={(e) => setDate(dmySlash(e.target.value))} />
                </div>
              </label>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {mode === 'irr' ? (
                <button onClick={saveIrrCheque} disabled={saving} type="button"
                  className="flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white font-bold rounded-lg py-2">
                  {saving ? '...' : 'ذخیرهٔ چکِ ریالی ذیلِ تسهیلات'}
                </button>
              ) : reversal ? (
                <button onClick={releaseCheque} disabled={releasing} type="button"
                  className="flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white font-bold rounded-lg py-2">
                  {releasing ? '...' : 'ثبتِ خروجِ چک (برگشتی)'}
                </button>
              ) : (
                <button onClick={saveGuarantor} disabled={saving} type="button"
                  className="flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white font-bold rounded-lg py-2">
                  {saving ? '...' : 'ذخیره ذیلِ تسهیلات'}
                </button>
              )}
              <button onClick={() => { auditApi.logActivity({ action: 'print', entity_type: 'voucher', account_no: acNo || undefined, detail: `چاپِ سندِ انتظامی${reversal ? ' (برگشتی)' : mode === 'irr' ? ' (چکِ ریالی)' : ''}${chqNo ? ` — چک ${chqNo}` : ''}${acName ? ` — ${acName}` : ''}` }); window.print() }} type="button"
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-2">
                <Printer size={18} /> چاپ (Print)
              </button>
              {/* v105 — the same slips as fillable Excel / Word templates */}
              <div className="flex gap-2">
                <button onClick={exportExcel} disabled={!!exporting} type="button"
                  className="flex-1 flex items-center justify-center gap-1.5 bg-green-700 hover:bg-green-800 disabled:opacity-60 text-white font-bold rounded-lg py-2 text-sm">
                  {exporting === 'xlsx' ? '...' : 'Excel (.xlsx)'}
                </button>
                <button onClick={exportWord} disabled={!!exporting} type="button"
                  className="flex-1 flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-bold rounded-lg py-2 text-sm">
                  {exporting === 'docx' ? '...' : 'Word (.docx)'}
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">در پنجرۀ چاپ، Scale را روی «Default / 100%» و Margins را «Default» بگذارید تا دقیق فیت شود.</p>
            <div className="mt-3 pt-3 border-t flex flex-wrap items-center gap-2">
              <DesignControls d={d} />
              <span className="text-xs text-gray-400">{d.design ? 'فیلد را بکش، گوشه = اندازه، دبل‌کلیک = تنظیمِ دقیق، بعد «ذخیرۀ چیدمان».' : 'برای جابه‌جایی/اندازۀ فیلدهای سند روی «چیدمان» بزن.'}</span>
            </div>
          </div>

          {/* ---- printable vouchers (A4 = two A5 halves) ---- */}
          <div className="vch-wrap" ref={wrapRef}>
            <div id="voucher-print" ref={previewRef}>
              {mode === 'irr' ? (
                <>
                  <Voucher kind="DEBIT" title={irrDrTitle} date={date} acNo={irrDebitGL} amount="" amountText={irrCount.trim()} currency="" ourRef={ourRef} description={irrChqLine} acName={acName} extraLines={irrExtraLines} d={d} prefix="irrd" />
                  <Voucher kind="CREDIT" title={irrCrTitle} date={date} acNo={irrCreditGL} amount="" amountText={irrCount.trim()} currency="" ourRef={ourRef} description={irrChqLine} acName={acName} extraLines={irrExtraLines} d={d} prefix="irrc" />
                </>
              ) : reversal ? (
                <>
                  <Voucher kind="CREDIT" title="PER CONTRA" date={date} acNo={revCreditGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} extraLines={revLines} d={d} prefix="rvc" />
                  <Voucher kind="DEBIT" title="SECURITY HELD CHEQUES" date={date} acNo={revDebitGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} extraLines={revLines} d={d} prefix="rvd" />
                </>
              ) : (
                <>
                  <Voucher kind="DEBIT" title="SECURITIES" date={date} acNo={debitGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} d={d} prefix="sec" />
                  <Voucher kind="CREDIT" title="PER CONTRA" date={date} acNo={creditGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} d={d} prefix="pc" />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
      <DesignPanel d={d} />
    </Layout>
  )
}
