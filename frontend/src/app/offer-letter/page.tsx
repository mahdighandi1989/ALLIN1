'use client'

// Offer Letter generator — auto-selects the right template from the customer's
// account_type × facility_type:
//   • retail + loan            → bilingual EN/AR Personal Loan (4 pages)
//   • retail (non-loan) / any corporate → English letter (3 pages)
// Headers/footers, borders, the dark section bars, the gray label cells, the
// account-number digit boxes and the document checkboxes are reproduced from the
// bank's scanned samples. Values are two-way synced with the customer profile:
// they prefill from the DB and are saved back (on Save / Print) so other forms
// and reports can reuse them.
import React, { useState, useRef, useEffect, useCallback } from 'react'
import Layout from '@/components/Layout'
import { Printer, Download, Search, Save, Upload } from 'lucide-react'
import toast from 'react-hot-toast'
import { chargeTariffApi, crmApi, parseApiError } from '@/lib/api'
// Verbatim letterhead assets extracted from the official Word letter template
// (same ground truth the official-letter page prints): blue emblem + REGIONAL
// OFFICE, blue bank wordmark + "Licensed by CBUAE", blue address/SWIFT banner.
import { LH_LOGO, LH_NAME, LH_FOOTER } from '@/app/letter/letterhead'
import { PL } from './personalLoanContent'

const today = new Date().toISOString().slice(0, 10)
const THIS_YEAR = String(new Date().getFullYear())

const TERM_TEXTS = [
  'The above-mentioned facility is valid up to {ValidUntil}, subject to full rights of the bank, at its sole discretion, to cancel/ amend/ reduce the Credit Facility Limits, change the terms and conditions of this sanction letter during the validity should the need arises on reasonable grounds to protect the Bank’s legitimate interests.',
  'Interest to be charged and debited to your account on a monthly basis. Interest debited and not paid at the end of each month shall form an excess and be charged as per above.',
  'The bank has right to change rate of interest or increase any other fees, commissions etc. whenever required due to change in local financial market.',
  'The total overdraft facility must be settled once every six months. However, the same will be available for utilization from the next business day following the settlement until the date of expiry of the Credit Facility mentioned herein.',
  'The commission and other charges of different services shall be levied as per bank’s usual tariff. Also, all legal and other costs incurred in documentation or for enforcing any of the bank’s rights, shall also be payable by you on demand or will be debited to your account.',
  'The level of existing net worth (i.e., capital, proprietor/ partners loan and current account, statutory reserves and retained earnings) should be maintained during the continuity of facilities from this bank.',
  'The proprietor/ partners/ shareholders current account balances and/ or loans to the company will be subordinated to the credit facilities from this bank, for which appropriate letter(s) of subordination should be provided. The moneys brought in by the Company’s proprietor/ partners/ shareholders for financing the needs of the Company shall not be withdrawn during the period of the Credit Facility, without the permission of the Bank.',
  'You will route business through the bank commensurate with the approved credit facilities. The credit facilities offered in this letter are subject to your completing the requisite formalities and execution of relevant security documents in form and substance satisfactory to us.',
  'The credit facilities offered are subject to our over-riding right of withdrawal of all or any credit facility and immediate demand for repayment. The Bank shall also have the right to call for cash cover on demand for prospective and contingent liabilities. The bank may also demand for additional security at any time, if in the sole opinion of the Bank such additional security is required to continue the Credit Facility.',
  'Further you will be required to sign the bank’s charge documents including additional charge documents for the facilities as and when called upon to do so.',
  'The bank has the right to set off any outstanding balance on one account against any other account held in your company or personal name at the bank whether in debit or credit, including but not limited to deposits of any kind and nature (including fixed deposits), balances lying in any accounts, any monies, securities, bonds and all other assets.',
  'You are responsible to provide us without any request from our side all latest documents related to your company i.e., Trade License, Chamber of Commerce Registration, Passport Renewal, Visa Renewal copies, a signed original copy of audited annual report of the last 3 years within a period of 90 days from financial year-end and any other documents upon branch request.',
  'You are fully responsible for the renewal/ increase/ decrease of your Credit Facilities and must approach us minimum one month before the expiry of same.',
  'This offer letter will be NULL & VOID after one month from the date of issue in case if you fail to activate or required documents are not provided to us.',
  'The laws and non-exclusive jurisdiction of the courts of United Arab Emirates shall govern this facility letter. However, this shall not prejudice the right of the bank to bring proceedings in any other jurisdiction.',
  'This letter of facility sanction supersedes all our previous sanction of credit limits in your favor.',
  'Any partial settlement or payment made towards overdue Credit Facilities shall first be debited towards service charges, commission, costs, expenses and other charges due towards the facilities till such date and then towards the principal.',
  'At the time of our customer credit rating, if there are changes in your grade, your interest rate will be modified point wised.',
  'All securities and guarantees provided and made by yourselves shall remain valid until all liabilities are fully settled.',
  'The security offered for one facility shall be additional security for all other Credit Facilities.',
  'Your obligations to the Bank under the Credit facility agreement will rank above and prior to all other present and future obligations, with first right to the bank over any amounts which may be due or available to you.',
  'You shall keep in good condition and fully insured at your own risk and expenses all the assets hypothecated, pledged, mortgaged or otherwise charged to the Bank as security for the aforesaid credit facilities, for such amount as the bank may from time to time stipulate with the Bank named as the beneficiary and the insurance policies shall be delivered to the Bank. If you fail to effect such insurance, the Bank may, without being obliged to do so, insure the movable and immovable and other assets against all risks and debit the premium and such other charges to your account.',
  'The consent of the bank should be obtained before any change in the Company’s shareholding.',
  'We will debit your account total for (AED {ProcessingFee}/-+Vat) being processing charges for above approved limit and same is non-refundable in case facilities or not activated due to any reason.',
  'Interest will be accrued in the account having suffix no.{AccountSuffix} and the customer has to pay the interest on monthly basis.',
]

const SECURITIES_PERSONAL =
  'Undertaking form for total facility amount from the borrower.\n' +
  'Facility agreement form from the borrower.\n' +
  'Letter of lien and authority to set off for advances against fixed deposits held underlien in borrower’s same account.\n' +
  'Personal guarantee form from the borrower.\n\n' +
  'Note:\n 1. In case of change in fixed deposit interest rate at any time, the overdraft interest rate must be revised from the same date.\n' +
  ' 2. The above offer is valid for 30 working days from the date of issuance.'

const SECURITIES_CORPORATE =
  'Signed undertaking form for total facility amount from the borrower.\n' +
  'Signed personal guarantee form from the borrower.\n' +
  'Signed credit facility agreement form from the borrower.\n' +
  'Signed overdraft / facility agreement form from the borrower.\n' +
  'Signed / accepted balance confirmation.\n\n' +
  'Note:\n 1. The offer letter is valid for 30 working days from the date of its issuance.\n' +
  ' 2. In case of changing fixed deposit interest rate any time, overdraft rate must be revised accordingly from the same date.'

// Notes printed under the securities table of the bilingual letter — editable;
// default text comes verbatim from the bank's scanned Personal Loan sample.
const DEFAULT_PL_NOTES =
  'Note : 1- In addition to above conditions, this approval will be executed after receiving balance confirmation.\n' +
  '2- Previous retail loan outstanding balance will be settled by above loan amount.'

type Fields = Record<string, string>
const INITIAL: Fields = {
  Prefix: 'M/S.', CompanyName: '', CompanyNameAr: '', AccountNumber: '', POBox: '', CityCountry: 'DUBAI - U.A.E.',
  Branch: '', RefSerial: '', RefYear: THIS_YEAR, IssueDate: today, RequestDate: '', ExpiryDate: '12 Months',
  RequiredSecurities: SECURITIES_CORPORATE, Remarks: '', FacilityType: 'Overdraft',
  CreditLimit: '', InterestRate: '', ValidUntil: '', ProcessingFee: '1000',
  AccountSuffix: '', AcceptanceDate: '',
  // Personal-loan fields
  LoanAmount: '', LoanInterestRate: '', LoanTenor: '', MonthlyInstallment: '', Purpose: 'PERSONAL NEED', SubjectDate: '',
  LienAmount: '', NotesPersonal: DEFAULT_PL_NOTES,
}

// The sheet starts BLANK (owner rule: no data appears until an account number
// is loaded — then the latest facility + the convenience defaults in INITIAL
// prefill it). INITIAL stays as the on-load default set.
const EMPTY: Fields = Object.fromEntries(Object.keys(INITIAL).map((k) => [k, ''])) as Fields

type GuarantorRow = { name: string; account: string }

// Persian-first field labels: what the field is + WHERE it lands on the printed
// letter, so the sheet explains itself (the English key stays as a subtitle).
const LABELS: Record<string, { fa: string; en: string }> = {
  Prefix: { fa: 'عنوان گیرنده (آقا/خانم/شرکت)', en: 'Mr. / Ms. / M/S.' },
  CompanyName: { fa: 'نام مشتری / شرکت', en: 'Customer / Company Name' },
  AccountNumber: { fa: 'شماره حساب', en: 'Account Number' },
  POBox: { fa: 'صندوق پستی', en: 'P.O. Box' },
  CityCountry: { fa: 'شهر / کشور', en: 'City / Country' },
  Branch: { fa: 'شعبه (نام و کد)', en: 'Branch Name & Code' },
  IssueDate: { fa: 'تاریخ صدور نامه', en: 'Issue Date' },
  RequestDate: { fa: 'تاریخ نامهٔ درخواست مشتری', en: 'Request Letter Date' },
  AcceptanceDate: { fa: 'تاریخ امضا/پذیرش مشتری', en: 'Acceptance Date' },
  FacilityType: { fa: 'نوع تسهیلات (از لیست یا تایپ آزاد)', en: 'Facility Type' },
  CreditLimit: { fa: 'سقف اعتبار — درهم', en: 'Credit Limit (AED)' },
  InterestRate: { fa: 'نرخ سود تسهیلات', en: 'Interest Rate' },
  ValidUntil: { fa: 'اعتبار تسهیلات تا تاریخ', en: 'Valid Until' },
  ProcessingFee: { fa: 'کارمزد پردازش — درهم (بند ۲۴ شرایط)', en: 'Processing Fee (AED)' },
  AccountSuffix: { fa: 'پسوند حسابِ سود (بند ۲۵ شرایط)', en: 'Interest A/C Suffix' },
  SubjectDate: { fa: 'تاریخ درخواست وام (موضوع نامه)', en: 'Loan Application Date' },
  LoanAmount: { fa: 'مبلغ وام — درهم', en: 'Loan Amount (AED)' },
  LoanInterestRate: { fa: 'نرخ سود وام — درصد سالانه', en: 'Loan Interest Rate (%)' },
  LoanTenor: { fa: 'مدت بازپرداخت — ماه', en: 'Loan Tenor (Months)' },
  MonthlyInstallment: { fa: 'قسط ماهانه (خالی = دکمهٔ محاسبه)', en: 'Monthly Installment' },
  Purpose: { fa: 'هدف / مصرف وام', en: 'Purpose' },
  LienAmount: { fa: 'مبلغ وثیقهٔ تودیع — درهم (بند ۴ مدارک)', en: 'Lien Amount (AED)' },
  Remarks: { fa: 'ملاحظات ردیف ۱ تسهیلات (ستون Remarks جدول)', en: 'Remarks (row 1)' },
  RequiredSecurities: { fa: 'وثایق و مدارک موردنیاز (متن صفحهٔ ۱)', en: 'Required Securities / Documents' },
  NotesPersonal: { fa: 'یادداشت‌های زیر جدول مدارک (Note 1, 2, …)', en: 'Notes under securities table' },
}

// Branch code → name; used for the dropdown and the bilingual header table
// ("AJMAN - 2900"). The select stores the "NAME - CODE" string directly.
const BRANCH_NAMES: Record<string, string> = {
  '2533': 'BUR DUBAI', '2690': 'ABU DHABI', '2776': 'SHARJAH', '2900': 'AJMAN',
  '4350': 'SHEIKH ZAYED ROAD', '2624': 'AL MAKTOUM', '2898': 'MURSHID BAZAR',
  '1741': 'AL AIN', '3535': 'HEAD OFFICE',
}
const BRANCH_OPTIONS = Object.entries(BRANCH_NAMES).map(([code, name]) => `${name} - ${code}`)
const fmtBranch = (code?: string) => {
  const c = String(code || '').trim()
  if (!c) return ''
  if (c.includes(' - ')) return c // already "NAME - CODE"
  return BRANCH_NAMES[c] ? `${BRANCH_NAMES[c]} - ${c}` : c
}

// Footer address (English template only) — verbatim from the scanned form.
const FOOT_AR = 'ص.ب : ٤١٨٢ ، دبي – إ.ع.م.  تليفون : ٦٠٣٥٥٥٥ ٩٧١٤+  فاكس : ٢٢١٥٩٦١ ٩٧١٤+'
const FOOT_EN = 'P.O. BOX: 4182, DUBAI – U.A.E.  TEL: +9714-6035555, FAX: +9714-2215961'
const FOOT_SWIFT = 'SWIFT CODE : BSIRAEAD'

// Safety net around the preview: if ANY render/commit error slips through
// (e.g. a future DOM collision with imperative marks), the boundary clears the
// stored selection formatting and remounts the preview instead of white-
// screening the whole app.
class OlSafe extends React.Component<{ onCrash: () => void; children: React.ReactNode }, { gen: number }> {
  state = { gen: 0 }
  static getDerivedStateFromError() { return {} }
  componentDidCatch() {
    this.props.onCrash()
    this.setState((s) => ({ gen: s.gen + 1 }))
  }
  render() { return <React.Fragment key={this.state.gen}>{this.props.children}</React.Fragment> }
}

export default function OfferLetterPage() {
  const [f, setF] = useState<Fields>(EMPTY)
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isCorporate, setIsCorporate] = useState(true)
  const [tpl, setTpl] = useState<'auto' | 'english' | 'personal'>('auto')
  const [extracting, setExtracting] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  // Required-document checkboxes (bilingual form). Default: all ticked.
  const [checks, setChecks] = useState<boolean[]>(() => PL.securities.map(() => true))
  // Facility-type catalog (DB-backed): dropdown options for the combobox; a
  // brand-new typed value is added to the catalog on Save.
  const [ftypes, setFtypes] = useState<string[]>([])
  // Guarantors printed into security-documents item 7 (and synced to the
  // customer's guarantor records on Save).
  const [guars, setGuars] = useState<GuarantorRow[]>([])
  // --- MULTI-FACILITY rows (corporate letters like the bank's OD+CD sample):
  // row 1 stays in f.FacilityType/CreditLimit/InterestRate/Remarks (back-compat);
  // extra rows live here and print as additional table rows + a Total row. Each
  // row carries the flags the charge calculator needs (100% FD underlien /
  // staff facility / temporary). ---
  type FacRow = { type: string; limit: string; rate: string; remarks: string; fd: boolean; staff: boolean; temp: boolean }
  const [extraFacs, setExtraFacs] = useState<FacRow[]>([])
  const [fac1, setFac1] = useState<{ fd: boolean; staff: boolean; temp: boolean }>({ fd: false, staff: false, temp: false })
  const [autoCharge, setAutoCharge] = useState(true)
  const [chargeInfo, setChargeInfo] = useState<{ lines: { label: string; base: number; charge: number }[]; warnings: string[] } | null>(null)
  const setFacRow = (i: number, k: keyof FacRow) => (e: any) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setExtraFacs((rows) => rows.map((r, idx) => (idx === i ? { ...r, [k]: v } : r)))
  }
  const set = (k: string) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const fill = (t: string) => t.replace(/\{(\w+)\}/g, (_, k) => f[k] || '________')

  // ---- unfilled-variable highlighting: every variable printed on the letter
  // BLINKS until its field has a value; once filled the highlight vanishes.
  // (Print strips the highlight — see the .olv-e print rule.) ----
  const Blink = ({ v, ph, fa }: { v: string; ph: string; fa: string }) =>
    v ? <>{v}</> : <span className="olv-e" title={`${fa} — از فرم بالا پر کن`}>{ph}</span>
  const V = (k: string, ph = '________') =>
    <Blink v={(f[k] || '').trim()} ph={ph} fa={LABELS[k]?.fa || k} />
  // like fill(), but unfilled {Key} placeholders become blinking spans
  const fillN = (t: string): React.ReactNode =>
    t.split(/(\{\w+\})/g).map((part, i) => {
      const m = part.match(/^\{(\w+)\}$/)
      return m ? <React.Fragment key={i}>{V(m[1])}</React.Fragment> : <React.Fragment key={i}>{part}</React.Fragment>
    })
  // replace ONE literal token inside a template string with a (blinking) node
  const replaceNode = (text: string, token: string, node: React.ReactNode): React.ReactNode => {
    const parts = text.split(token)
    if (parts.length === 1) return text
    return parts.map((seg, i) => (
      <React.Fragment key={i}>{seg}{i < parts.length - 1 ? node : null}</React.Fragment>
    ))
  }
  // the REF number with blinking serial/year (refNumber stays a string for save)
  const RefNo = () => <>182/4/{V('RefSerial', '____')}/{V('RefYear', '____')}</>

  // ---- double-click layout editing (like the official-letter page): dblclick
  // any block/variable in the preview → a floating panel adjusts font, align,
  // direction, spacing and offsets. Overrides are keyed by the element's path
  // inside its page, stored per TEMPLATE in localStorage, applied after every
  // render, and saved into the customer snapshot too. ----
  // dx/dy/rot = FREE move/rotate via CSS transform (Word "behind text" feel —
  // zero effect on siblings); wx = absolute width (px, edge-resize); txt =
  // rewrite the element's text (leaf elements only). mt/mis kept for legacy.
  type OlBox = { fs?: number; bold?: boolean; align?: string; dir?: string; lh?: number; ls?: number; mt?: number; mis?: number; w?: number; dx?: number; dy?: number; rot?: number; wx?: number; txt?: string; hide?: boolean; font?: string; list?: string }
  const [olLayout, setOlLayout] = useState<Record<string, OlBox>>({})
  const [olSel, setOlSel] = useState<{ key: string; label: string; x: number; y: number } | null>(null)
  const olPrevKeys = useRef<string[]>([])
  // remount sequence for the preview when marks are active (see key below)
  const olRenderSeq = useRef(0)
  const OLKEY = (t: string) => `ol-layout:${t}`
  // ---- layout SCOPE (owner rule): once the document belongs to an account
  // (loaded or even just typed, saved or not), layout/format edits apply to
  // THAT ACCOUNT ONLY — the base template stays untouched. Only on a pristine
  // form (no account) do edits update the base template itself. The preview
  // shows base-template overrides UNDER the account's own (account wins).
  const olAcct = (acc || f.AccountNumber).trim()
  const olScopeOf = (t: string) => (olAcct ? `${t}::${olAcct}` : t)
  const [olBase, setOlBase] = useState<Record<string, OlBox>>({})
  const [olMarksBase, setOlMarksBase] = useState<Record<string, OlMark[]>>({})
  // global «چیدمان» mode (like the official-letter page's toolbar toggle):
  // hover highlights the block under the cursor, a single click opens the panel.
  const [olDesign, setOlDesign] = useState(false)
  const olHoverEl = useRef<HTMLElement | null>(null)
  // ---- SELECTION formatting (like the letter page's floating toolbar): select
  // part of a sentence in the preview → a small bar applies bold/italic/
  // underline/size to JUST that range. Marks are stored as text offsets inside
  // the element's path key and re-applied after every render. ----
  type OlMark = { s: number; e: number; b?: boolean; i?: boolean; u?: boolean; fs?: number }
  const [olMarks, setOlMarks] = useState<Record<string, OlMark[]>>({})
  const [olFmt, setOlFmt] = useState<{ key: string; s: number; e: number; x: number; y: number } | null>(null)
  const OLMKEY = (t: string) => `ol-marks:${t}`
  const toggleCheck = (i: number) => setChecks((c) => c.map((v, idx) => (idx === i ? !v : v)))
  const setGuar = (i: number, k: keyof GuarantorRow) => (e: any) =>
    setGuars((g) => g.map((row, idx) => (idx === i ? { ...row, [k]: e.target.value } : row)))

  useEffect(() => {
    crmApi.facilityTypes().then((r) => setFtypes(r.types || [])).catch(() => {})
  }, [])

  // Reducing-balance EMI (like the sample's "2,106/71" for 80,000 @12% / 48m).
  const parseNum = (s: string) => parseFloat(String(s || '').replace(/[^0-9.]/g, '')) || 0
  const emiSuggest = (): string => {
    const P = parseNum(f.LoanAmount)
    const r = parseNum(f.LoanInterestRate || f.InterestRate)
    const n = Math.round(parseNum(f.LoanTenor))
    if (!P || !n) return ''
    const m = r > 0 ? (P * (r / 1200)) / (1 - Math.pow(1 + r / 1200, -n)) : P / n
    const [int_, dec] = m.toFixed(2).split('.')
    return `${Number(int_).toLocaleString('en-US')}/${dec}`
  }

  // Guarantor entries appended to securities item 7. The owner wants them
  // STACKED (one per line, neatly under each other) rather than run together.
  const guarItems = guars
    .filter((g) => g.name.trim())
    .map((g) => `-${g.name.trim()}-${g.account.trim() ? ` A/C NO.${g.account.trim()}` : ''}`)
  const guarLine = guarItems.join(' / ')   // kept for any single-line consumers
  const GuarStack = ({ dir }: { dir?: 'ltr' | 'rtl' }) =>
    guarItems.length ? (
      <div className="guar-stack" dir={dir || 'ltr'}>
        {guarItems.map((s, i) => <div key={i} className="guar-line" dir="ltr">{s}</div>)}
      </div>
    ) : null

  // Department reference number: "182/4/<serial>/<year>" — prefix fixed, serial
  // typed, year auto (current year unless overridden).
  const refYear = f.RefYear || THIS_YEAR
  const refNumber = `182/4/${f.RefSerial || '____'}/${refYear}`

  // Auto template: a retail account with a (personal) LOAN → bilingual letter;
  // everything else → English. Recomputes live as the loaded account type or the
  // Facility Type typed in the inputs changes, so the form shifts automatically.
  const isLoanType = /loan/i.test(f.FacilityType) && !/overdraft|over\s*draft/i.test(f.FacilityType)
  const autoTpl: 'english' | 'personal' = !isCorporate && isLoanType ? 'personal' : 'english'
  const effectiveTpl = tpl === 'auto' ? autoTpl : tpl

  // every facility row (row 1 + extras) as calculator items
  const facItems = () => [
    { facility_type: (f.FacilityType || '').trim(), amount: f.CreditLimit || '',
      covered_by_fd: fac1.fd, staff_facility: fac1.staff, temporary: fac1.temp },
    ...extraFacs.map((r) => ({ facility_type: r.type.trim(), amount: r.limit,
      covered_by_fd: r.fd, staff_facility: r.staff, temporary: r.temp })),
  ].filter((i) => i.facility_type || String(i.amount).trim())
  // Ask the editable tariff (/charge-tariff) for the processing charges and put
  // the SUM into ProcessingFee — the one cell term 23 prints (کامیشن جمعی).
  const computeCharges = async (silent = false) => {
    const items = facItems()
    if (!items.length) { if (!silent) toast.error('نوع و مبلغ تسهیلات را وارد کن'); return }
    try {
      const r = await chargeTariffApi.compute(isCorporate ? 'corporate' : 'individual', items)
      setChargeInfo({ lines: r.lines, warnings: r.warnings })
      const t = Math.round(r.total)
      setF((s) => ({ ...s, ProcessingFee: t.toLocaleString('en-US') }))
      if (!silent && r.warnings.length) r.warnings.forEach((w) => toast(w, { icon: '⚠️' }))
    } catch (e) { if (!silent) toast.error(parseApiError(e)) }
  }
  // auto-recompute (debounced) as the facility type/amount rows change
  useEffect(() => {
    if (!autoCharge) return
    const items = facItems()
    if (!items.some((i) => String(i.amount).trim())) return
    const t = setTimeout(() => { computeCharges(true) }, 900)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f.FacilityType, f.CreditLimit, JSON.stringify(extraFacs), JSON.stringify(fac1), isCorporate, autoCharge])

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await crmApi.offerLetterData(a)
      const corp = ['corporate', 'sme'].includes(String(d.AccountType || '').toLowerCase())
      const saved = (d.Saved && typeof d.Saved === 'object') ? d.Saved : {}
      setIsCorporate(corp)
      const withSlash = (v: any) => (v ? `${v}/-` : '')
      // FACILITY ROWS: the DB's facilities (what the imported مصوبه just wrote)
      // WIN over the older snapshot — that's the whole sync the owner wants.
      // The snapshot's rows are only the fallback when the DB has none, and its
      // per-row flags (FD-covered/staff/temporary) are re-attached by type so a
      // reload doesn't lose them.
      const dbFacs: any[] = Array.isArray(d.Facilities) ? d.Facilities.filter((r: any) => r && (r.type || r.amount)) : []
      const savedRows: any[] = Array.isArray(saved.extraFacilities) ? saved.extraFacilities : []
      const savedFlags = (t: string) => {
        const k = String(t || '').trim().toLowerCase()
        if (saved.fac1Flags && String(saved.FacilityType || '').trim().toLowerCase() === k)
          return { fd: !!saved.fac1Flags.fd, staff: !!saved.fac1Flags.staff, temp: !!saved.fac1Flags.temp }
        const m = savedRows.find((r: any) => String(r?.type || '').trim().toLowerCase() === k)
        return m ? { fd: !!m.fd, staff: !!m.staff, temp: !!m.temp } : { fd: false, staff: false, temp: false }
      }
      // Reset from INITIAL — the previous account's values (`s.X` fallbacks)
      // otherwise stayed on the sheet and were saved into the new customer.
      const s = { ...INITIAL } as Fields
      setF(() => ({
        ...s,
        Prefix: saved.Prefix || d.Salutation || (corp ? 'M/S.' : 'Mr.'),
        CompanyName: saved.CompanyName || d.CompanyName || s.CompanyName,
        CompanyNameAr: saved.CompanyNameAr || d.CompanyNameAr || s.CompanyNameAr,
        AccountNumber: d.AccountNumber || a,
        POBox: saved.POBox || d.POBox || s.POBox,
        CityCountry: saved.CityCountry || d.CityCountry || s.CityCountry,
        Branch: saved.Branch || fmtBranch(d.Branch) || s.Branch,
        RefSerial: saved.RefSerial || s.RefSerial,
        RefYear: saved.RefYear || THIS_YEAR,
        FacilityType: (dbFacs.length ? dbFacs[0].type : '') || saved.FacilityType || d.FacilityType || s.FacilityType,
        CreditLimit: (dbFacs.length ? withSlash(dbFacs[0].amount) : '') || saved.CreditLimit || withSlash(d.CreditLimit) || s.CreditLimit,
        InterestRate: (dbFacs.length ? dbFacs[0].rate : '') || saved.InterestRate || d.InterestRate || s.InterestRate,
        ValidUntil: saved.ValidUntil || d.ValidUntil || s.ValidUntil,
        RequiredSecurities: d.RequiredSecurities || saved.RequiredSecurities || (corp ? SECURITIES_CORPORATE : SECURITIES_PERSONAL),
        // loan specifics
        LoanAmount: saved.LoanAmount || withSlash(d.LoanAmount) || s.LoanAmount,
        LoanInterestRate: saved.LoanInterestRate || d.LoanInterestRate || s.LoanInterestRate,
        LoanTenor: saved.LoanTenor || d.LoanTenor || s.LoanTenor,
        MonthlyInstallment: saved.MonthlyInstallment || d.MonthlyInstallment || s.MonthlyInstallment,
        Purpose: saved.Purpose || d.Purpose || s.Purpose || 'PERSONAL NEED',
        LienAmount: saved.LienAmount || withSlash(d.LoanAmount) || s.LienAmount,
        SubjectDate: saved.SubjectDate || s.SubjectDate,
        AcceptanceDate: saved.AcceptanceDate || s.AcceptanceDate,
        Remarks: saved.Remarks || s.Remarks,
        RequestDate: saved.RequestDate || s.RequestDate,
        ProcessingFee: saved.ProcessingFee || s.ProcessingFee,
        AccountSuffix: saved.AccountSuffix || s.AccountSuffix,
        NotesPersonal: saved.NotesPersonal || s.NotesPersonal,
      }))
      setChecks(
        Array.isArray(saved.securitiesChecked) && saved.securitiesChecked.length === PL.securities.length
          ? saved.securitiesChecked
          : PL.securities.map(() => true)
      )
      // Guarantors: last saved snapshot wins; otherwise the customer's recorded
      // guarantors from the DB prefill the section.
      const savedGuars = Array.isArray(saved.guarantors) ? saved.guarantors : null
      const dbGuars = Array.isArray(d.Guarantors) ? d.Guarantors : []
      setGuars(
        (savedGuars ?? dbGuars)
          .map((g: any) => ({ name: String(g?.name || ''), account: String(g?.account || '') }))
          .filter((g: GuarantorRow) => g.name.trim())
      )
      if (saved.tpl === 'english' || saved.tpl === 'personal' || saved.tpl === 'auto') setTpl(saved.tpl)
      if (dbFacs.length) {
        // rows 2..n come straight from the DB (latest مصوبه); saved flags re-attach by type
        setExtraFacs(dbFacs.slice(1).map((r: any) => ({
          type: String(r.type || ''), limit: r.amount ? `${r.amount}/-` : '',
          rate: String(r.rate || ''), remarks: String(r.remarks || ''),
          ...savedFlags(r.type),
        })))
        setFac1(savedFlags(dbFacs[0].type))
      } else {
        setExtraFacs(savedRows.map((r: any) => ({ type: String(r?.type || ''), limit: String(r?.limit || ''), rate: String(r?.rate || ''), remarks: String(r?.remarks || ''), fd: !!r?.fd, staff: !!r?.staff, temp: !!r?.temp })))
        setFac1(saved.fac1Flags && typeof saved.fac1Flags === 'object'
          ? { fd: !!saved.fac1Flags.fd, staff: !!saved.fac1Flags.staff, temp: !!saved.fac1Flags.temp }
          : { fd: false, staff: false, temp: false })
      }
      if (typeof saved.autoCharge === 'boolean') setAutoCharge(saved.autoCharge)
      // restore the layout overrides saved with this customer — into the
      // ACCOUNT-scoped stores (this customer's own look), never the template.
      // Old snapshots (pre-scoping) restore the same way: they were edits made
      // while this customer was loaded, so account scope is their true home.
      if (saved.olLayoutMap && typeof saved.olLayoutMap === 'object') {
        for (const t of ['english', 'personal']) {
          if (saved.olLayoutMap[t] && typeof saved.olLayoutMap[t] === 'object' && Object.keys(saved.olLayoutMap[t]).length) {
            try { localStorage.setItem(OLKEY(`${t}::${a}`), JSON.stringify(saved.olLayoutMap[t])) } catch { /* in-memory only */ }
          }
        }
      }
      if (saved.olMarksMap && typeof saved.olMarksMap === 'object') {
        for (const t of ['english', 'personal']) {
          if (saved.olMarksMap[t] && typeof saved.olMarksMap[t] === 'object' && Object.keys(saved.olMarksMap[t]).length) {
            try { localStorage.setItem(OLMKEY(`${t}::${a}`), JSON.stringify(saved.olMarksMap[t])) } catch { /* in-memory only */ }
          }
        }
      }
      // load the restored account stores into state NOW — the scope effect only
      // re-fires when the account/template actually changes, and here the
      // account was already typed before the click (same scope, fresh keys).
      try { setOlLayout(JSON.parse(localStorage.getItem(OLKEY(`${effectiveTpl}::${a}`)) || '{}')) } catch { /* keep current */ }
      try { setOlMarks(JSON.parse(localStorage.getItem(OLMKEY(`${effectiveTpl}::${a}`)) || '{}')) } catch { /* keep current */ }
      try { setOlBase(JSON.parse(localStorage.getItem(OLKEY(effectiveTpl)) || '{}')) } catch { setOlBase({}) }
      try { setOlMarksBase(JSON.parse(localStorage.getItem(OLMKEY(effectiveTpl)) || '{}')) } catch { setOlMarksBase({}) }
      toast.success(`«${d.CompanyName || a}» — ${corp ? 'حقوقی' : 'حقیقی'} · ${d.facilities_count || 0} تسهیلات${d.Saved && Object.keys(d.Saved).length ? ' · بازیابی از ذخیره' : ''}`)
    } catch (e) { toast.error(parseApiError(e)) }
    finally { setLoading(false) }
  }

  // Two-way sync: persist reusable fields + a full snapshot to the customer
  // profile so other forms/reports can use them (and the form restores next time).
  const saveOffer = async (silent = false) => {
    const a = (acc || f.AccountNumber).trim()
    if (!a) { if (!silent) toast.error('ابتدا حساب را بارگیری کنید'); return false }
    setSaving(true)
    try {
      const cleanGuars = guars
        .map((g) => ({ name: g.name.trim(), account: g.account.trim() }))
        .filter((g) => g.name)
      // the snapshot carries the ACCOUNT's own overrides (its scoped stores) —
      // the base template belongs to the device/template, not to this customer.
      const layoutMap: Record<string, any> = {}
      const marksMap: Record<string, any> = {}
      for (const t of ['english', 'personal']) {
        try { layoutMap[t] = JSON.parse(localStorage.getItem(OLKEY(`${t}::${a}`)) || '{}') } catch { layoutMap[t] = {} }
        try { marksMap[t] = JSON.parse(localStorage.getItem(OLMKEY(`${t}::${a}`)) || '{}') } catch { marksMap[t] = {} }
      }
      await crmApi.saveOfferLetterData(a, {
        POBox: f.POBox, CityCountry: f.CityCountry, Salutation: f.Prefix, Branch: f.Branch,
        snapshot: { ...f, RefNumber: refNumber, securitiesChecked: checks, tpl, guarantors: cleanGuars, olLayoutMap: layoutMap, olMarksMap: marksMap,
                    extraFacilities: extraFacs, fac1Flags: fac1, autoCharge },
      })
      // A facility type with no name-similar entry in the catalog opens its own
      // place in the DB list (and becomes selectable from now on). Similar
      // entries are matched, not duplicated.
      const ft = f.FacilityType.trim()
      if (ft) {
        try {
          const r = await crmApi.addFacilityType(ft)
          if (Array.isArray(r.types)) setFtypes(r.types)
          if (r.added && !silent) toast.success(`نوع تسهیلات جدید «${ft}» به فهرست اضافه شد`)
        } catch { /* catalog is best-effort; the letter still saves */ }
      }
      // Guarantors typed here also become customer guarantor records (idempotent
      // upsert server-side) so the profile and future letters see them.
      for (const g of cleanGuars) {
        try { await crmApi.addGuarantor(a, { guarantor_name: g.name, guarantor_account: g.account }) }
        catch { /* best-effort — the snapshot already holds them */ }
      }
      if (!silent) toast.success('در پروندهٔ مشتری ذخیره شد')
      return true
    } catch (e) { if (!silent) toast.error(parseApiError(e)); return false }
    finally { setSaving(false) }
  }
  const printDoc = async () => { await saveOffer(true); setTimeout(() => window.print(), 50) }

  // Drop / pick a filled committee-approval draft (.docx): the backend parses it,
  // persists everything to the customer record, and returns the fields that
  // prefill this Offer Letter.
  const handleDraft = async (file?: File | null) => {
    if (!file) return
    if (!/\.docx$/i.test(file.name)) { toast.error('فقط فایل Word با پسوند .docx'); return }
    setExtracting(true)
    try {
      const a = (acc || f.AccountNumber).trim()
      const r: any = await crmApi.extractDraft(a, file)
      const o = r.offer || {}
      const corp = ['corporate', 'sme'].includes(String(r.account_type || o.AccountType || '').toLowerCase())
      if (o.AccountType) setIsCorporate(corp)
      if (!acc && r.account_no) setAcc(r.account_no)
      const withSlash = (v: any) => (v ? `${v}/-` : '')
      // Reset from INITIAL — the previous account's values (`s.X` fallbacks)
      // otherwise stayed on the sheet and were saved into the new customer.
      const s = { ...INITIAL } as Fields
      setF(() => ({
        ...s,
        CompanyName: o.CompanyName || s.CompanyName,
        AccountNumber: o.AccountNumber || s.AccountNumber,
        Branch: o.Branch || s.Branch,
        FacilityType: o.FacilityType || s.FacilityType,
        CreditLimit: withSlash(o.CreditLimit) || s.CreditLimit,
        LoanAmount: withSlash(o.LoanAmount) || s.LoanAmount,
        InterestRate: o.InterestRate || s.InterestRate,
        LoanInterestRate: o.LoanInterestRate || s.LoanInterestRate,
        LoanTenor: o.LoanTenor || s.LoanTenor,
        Purpose: o.Purpose || s.Purpose,
        BusinessType: o.BusinessType || s.BusinessType,
        Rating: o.Rating || s.Rating,
        SubjectDate: o.SubjectDate || s.SubjectDate,
      }))
      const parts = [`«${o.CompanyName || r.account_no}»`]
      if (Array.isArray(r.profile_keys) && r.profile_keys.length) parts.push(`${r.profile_keys.length} مورد در پروفایل`)
      if (r.guarantors_added) parts.push(`${r.guarantors_added} ضامن جدید`)
      if (r.guarantors_updated) parts.push(`${r.guarantors_updated} ضامن به‌روز`)
      // Pull the (possibly just-extracted) guarantors into the letter's section.
      const acctForGuars = (r.account_no || a || '').trim()
      if (acctForGuars) {
        try {
          const rows = await crmApi.listGuarantors(acctForGuars)
          const seen = new Set<string>()
          setGuars(rows
            .map((g: any) => ({ name: String(g?.guarantor_name || '').trim(), account: String(g?.guarantor_account || '').trim() }))
            .filter((g: GuarantorRow) => {
              const k = g.name.toLowerCase() + '|' + g.account
              if (!g.name || seen.has(k)) return false
              seen.add(k)
              return true
            }))
        } catch { /* prefill only */ }
      }
      toast.success('استخراج و ثبت شد: ' + parts.join(' · '))
    } catch (e) { toast.error(parseApiError(e)) }
    finally { setExtracting(false) }
  }

  // Auto-fit: if a page's content is taller than the printable A4 area, shrink it
  // (CSS zoom, which also reduces the laid-out height) so it never spills over.
  const printRef = useRef<HTMLDivElement>(null)
  const fitPages = useCallback(() => {
    const root = printRef.current
    if (!root) return
    const MM = 96 / 25.4
    const avail = (297 - 9 - 13 - 12) * MM // A4 height − top/bottom padding − footer reserve
    root.querySelectorAll<HTMLElement>('.ol-page').forEach((pg) => {
      const fit = pg.querySelector<HTMLElement>('.ol-fit')
      if (!fit) return
      fit.style.setProperty('zoom', '1')
      const h = fit.scrollHeight
      if (h > avail) fit.style.setProperty('zoom', String(Math.max(0.4, avail / h)))
    })
  }, [])
  useEffect(() => { fitPages() })
  useEffect(() => {
    const on = () => fitPages()
    window.addEventListener('resize', on)
    window.addEventListener('beforeprint', on)
    const t = setTimeout(on, 350)
    return () => { window.removeEventListener('resize', on); window.removeEventListener('beforeprint', on); clearTimeout(t) }
  }, [fitPages])

  // ---- layout-override plumbing (path keys resolve inside the current pages) ----
  const elPath = (el: HTMLElement): string | null => {
    const page = el.closest('.ol-page') as HTMLElement | null
    if (!page || !printRef.current) return null
    const pages = Array.from(printRef.current.querySelectorAll('.ol-page'))
    const chain: number[] = []
    let cur: HTMLElement = el
    while (cur !== page) {
      const par = cur.parentElement
      if (!par) return null
      chain.unshift(Array.from(par.children).indexOf(cur))
      cur = par
    }
    return `${pages.indexOf(page)}|${chain.join('.')}`
  }
  const elFromPath = (key: string): HTMLElement | null => {
    const [pi, chain] = key.split('|')
    let cur: Element | null | undefined = printRef.current?.querySelectorAll('.ol-page')[Number(pi)]
    if (!cur) return null
    for (const i of chain ? chain.split('.') : []) {
      cur = cur.children[Number(i)]
      if (!cur) return null
    }
    return cur as HTMLElement
  }
  const OL_PROPS = ['fontSize', 'fontWeight', 'textAlign', 'direction', 'lineHeight', 'letterSpacing', 'marginTop', 'marginInlineStart', 'width', 'transform', 'transformOrigin', 'display', 'opacity', 'outline', 'outlineOffset', 'cursor', 'fontFamily'] as const
  // re-apply after EVERY render (React re-creates nodes freely); clear the
  // previously-touched elements first so removed overrides really reset.
  // effective maps: on a pristine form these are just the template stores; with
  // an account, the account's overrides sit ON TOP of the template's (per key).
  const olEffLayout: Record<string, OlBox> = olAcct ? { ...olBase, ...olLayout } : olLayout
  const olEffMarks: Record<string, OlMark[]> = olAcct ? { ...olMarksBase, ...olMarks } : olMarks
  // text rewrites mutate React-owned text nodes — engage the same remount
  // guard as selection marks so reconciliation never trips over them
  const olHasTxt = Object.values(olEffLayout).some((b) => b.txt != null || !!b.list)
  useEffect(() => {
    for (const k of olPrevKeys.current) {
      const el = elFromPath(k)
      if (el) OL_PROPS.forEach((p) => { (el.style as any)[p] = '' })
    }
    for (const [k, b] of Object.entries(olEffLayout)) {
      const el = elFromPath(k)
      if (!el) continue
      if (b.txt != null && el.children.length === 0) el.textContent = b.txt
      if (b.list && el.children.length === 0) {
        // Word-style list markers: prefix every non-empty LINE of this block
        let n = 0
        el.textContent = (el.textContent || '').split('\n').map((ln) => {
          if (!ln.trim()) return ln
          n++
          const pre = b.list === 'num' ? `${n}. ` : b.list === 'check' ? '\u2713 ' : b.list === 'dash' ? '\u2013 ' : '\u2022 '
          return ln.replace(/^\s*/, (m) => m + pre)
        }).join('\n')
      }
      if (b.font) el.style.fontFamily = b.font
      if (b.fs) el.style.fontSize = `${b.fs}pt`
      if (b.bold != null) el.style.fontWeight = b.bold ? '700' : '400'
      if (b.align) el.style.textAlign = b.align
      if (b.dir) el.style.direction = b.dir
      if (b.lh) el.style.lineHeight = String(b.lh)
      if (b.ls) el.style.letterSpacing = `${b.ls}px`
      if (b.mt) el.style.marginTop = `${b.mt}px`
      if (b.mis) el.style.marginInlineStart = `${b.mis}px`
      if (b.wx) el.style.width = `${b.wx}px`
      else if (b.w) el.style.width = `${b.w}%`
      if (b.dx || b.dy || b.rot) {
        // transform = free float, Word-style: siblings keep their place, the
        // element glides/rotates over the page with no flow constraints
        el.style.transform = `translate(${b.dx || 0}px, ${b.dy || 0}px) rotate(${b.rot || 0}deg)`
        el.style.transformOrigin = 'center center'
        if (getComputedStyle(el).display === 'inline') el.style.display = 'inline-block'
      }
      if (b.hide) {
        // removed from the letter; in layout mode it stays as a ghost so it
        // can be clicked and brought back
        if (olDesign) { el.style.opacity = '0.3'; el.style.outline = '1.5px dashed #dc2626'; el.style.outlineOffset = '1px' }
        else el.style.display = 'none'
      }
    }
    // the panel's target stays visibly selected and draggable even outside
    // layout mode (dblclick → drag/resize directly, like the letter page)
    if (olSel) {
      const el = elFromPath(olSel.key)
      if (el && !(olEffLayout[olSel.key] || {}).hide) {
        el.style.outline = '2px solid #2563eb'
        el.style.outlineOffset = '1px'
        el.style.cursor = 'move'
      }
    }
    olPrevKeys.current = [...Object.keys(olEffLayout), ...(olSel ? [olSel.key] : [])]
    // ---- selection marks: unwrap previous spans, re-wrap current offsets ----
    printRef.current?.querySelectorAll('span[data-olm]').forEach((sp) => {
      const parent = sp.parentNode
      if (!parent) return
      while (sp.firstChild) parent.insertBefore(sp.firstChild, sp)
      parent.removeChild(sp)
      if ((parent as HTMLElement).normalize) (parent as HTMLElement).normalize()
    })
    for (const [key, marks] of Object.entries(olEffMarks)) {
      const el = elFromPath(key)
      if (!el) continue
      for (const m of [...marks].sort((a, b) => a.s - b.s)) {
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
        let pos = 0
        let sN: Node | null = null, sO = 0, eN: Node | null = null, eO = 0
        let n: Node | null
        while ((n = walker.nextNode())) {
          const len = (n.textContent || '').length
          if (!sN && m.s < pos + len) { sN = n; sO = Math.max(0, m.s - pos) }
          if (m.e <= pos + len) { eN = n; eO = m.e - pos; break }
          pos += len
        }
        if (!sN || !eN) continue
        try {
          const rg = document.createRange()
          rg.setStart(sN, sO); rg.setEnd(eN, eO)
          const sp = document.createElement('span')
          sp.setAttribute('data-olm', '1')
          if (m.b) sp.style.fontWeight = '700'
          if (m.i) sp.style.fontStyle = 'italic'
          if (m.u) sp.style.textDecoration = 'underline'
          if (m.fs) sp.style.fontSize = `${m.fs}em`
          rg.surroundContents(sp)
        } catch { /* range crosses an element boundary — skip this mark */ }
      }
    }
    fitPages()
  })
  // per-scope persistence (device-local; the snapshot carries the account's too).
  // Scope = template when the form is pristine, template::account once the
  // document belongs to an account. On scope change, load that scope's store
  // and (with an account) the template store as the read-only base layer.
  useEffect(() => {
    const sc = olScopeOf(effectiveTpl)
    try { setOlLayout(JSON.parse(localStorage.getItem(OLKEY(sc)) || '{}')) } catch { setOlLayout({}) }
    try { setOlMarks(JSON.parse(localStorage.getItem(OLMKEY(sc)) || '{}')) } catch { setOlMarks({}) }
    if (olAcct) {
      try { setOlBase(JSON.parse(localStorage.getItem(OLKEY(effectiveTpl)) || '{}')) } catch { setOlBase({}) }
      try { setOlMarksBase(JSON.parse(localStorage.getItem(OLMKEY(effectiveTpl)) || '{}')) } catch { setOlMarksBase({}) }
    } else { setOlBase({}); setOlMarksBase({}) }
    setOlSel(null); setOlFmt(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveTpl, olAcct])
  // write-back: empty stores REMOVE their key (typing an account number digit by
  // digit must not litter localStorage with junk scope keys)
  useEffect(() => {
    try {
      const s = JSON.stringify(olMarks)
      if (s === '{}') localStorage.removeItem(OLMKEY(olScopeOf(effectiveTpl)))
      else localStorage.setItem(OLMKEY(olScopeOf(effectiveTpl)), s)
    } catch { /* quota */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [olMarks])
  useEffect(() => {
    try {
      const s = JSON.stringify(olLayout)
      if (s === '{}') localStorage.removeItem(OLKEY(olScopeOf(effectiveTpl)))
      else localStorage.setItem(OLKEY(olScopeOf(effectiveTpl)), s)
    } catch { /* quota — layout stays in-memory */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [olLayout])
  const olUpdate = (patch: OlBox) => {
    if (!olSel) return
    setOlLayout((s) => ({ ...s, [olSel.key]: { ...(s[olSel.key] || {}), ...patch } }))
  }
  // text offset of (node, off) inside host — marks survive re-renders via offsets
  const textOffsetIn = (host: HTMLElement, node: Node, off: number): number => {
    let total = 0
    const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT)
    let n: Node | null
    while ((n = walker.nextNode())) {
      if (n === node) return total + off
      total += (n.textContent || '').length
    }
    return total
  }
  const onPreviewMouseUp = () => {
    setTimeout(() => {
      const sel = typeof window !== 'undefined' ? window.getSelection() : null
      if (!sel || sel.isCollapsed || !sel.rangeCount || !printRef.current) return
      const r = sel.getRangeAt(0)
      if (r.startContainer.nodeType !== 3 || r.endContainer.nodeType !== 3) return
      const hostEl = (r.commonAncestorContainer.nodeType === 3
        ? r.commonAncestorContainer.parentElement
        : (r.commonAncestorContainer as HTMLElement))?.closest('span,td,th,li,p,div') as HTMLElement | null
      if (!hostEl || !printRef.current.contains(hostEl) || hostEl.closest('.olp-panel,.olf-bar')) return
      const key = elPath(hostEl)
      if (!key) return
      const s = textOffsetIn(hostEl, r.startContainer, r.startOffset)
      const e = textOffsetIn(hostEl, r.endContainer, r.endOffset)
      if (e <= s) return
      const rect = r.getBoundingClientRect()
      setOlFmt({ key, s, e, x: Math.min(Math.max(rect.left + rect.width / 2 - 130, 8), (window.innerWidth || 1200) - 270), y: Math.max(8, rect.top - 46) })
    }, 10)
  }
  const addMark = (patch: Partial<OlMark>) => {
    if (!olFmt) return
    const { key, s, e } = olFmt
    setOlMarks((prev) => ({ ...prev, [key]: [...(prev[key] || []), { s, e, ...patch }] }))
    setOlFmt(null)
    try { window.getSelection()?.removeAllRanges() } catch { /* selection already gone */ }
  }
  // block-level ops from the SELECTION bar: they land on the block hosting
  // the selection via the same layout-override store (scoped + resettable)
  const hostUpdate = (patch: OlBox) => {
    if (!olFmt) return
    const key = olFmt.key
    setOlLayout((s) => ({ ...s, [key]: { ...(s[key] || {}), ...patch } }))
  }
  const hostLh = (d: number) => {
    if (!olFmt) return
    const key = olFmt.key
    setOlLayout((s) => {
      const cur = s[key] || {}
      const base = cur.lh ?? 1.2   // the page's default line-height
      return { ...s, [key]: { ...cur, lh: Math.max(0.8, Math.round((base + d) * 10) / 10) } }
    })
  }
  const clearMarksInRange = () => {
    if (!olFmt) return
    const { key, s, e } = olFmt
    setOlMarks((prev) => {
      const kept = (prev[key] || []).filter((m) => m.e <= s || m.s >= e)
      const n = { ...prev }
      if (kept.length) n[key] = kept; else delete n[key]
      return n
    })
    setOlFmt(null)
  }
  const onPreviewCrash = () => {
    // drop the selection formatting that caused the render error and recover
    // (both layers: the account-scoped stores AND the template bases)
    setOlMarks({}); setOlMarksBase({}); setOlFmt(null)
    try {
      localStorage.removeItem(OLMKEY('english'))
      localStorage.removeItem(OLMKEY('personal'))
      if (olAcct) {
        localStorage.removeItem(OLMKEY(`english::${olAcct}`))
        localStorage.removeItem(OLMKEY(`personal::${olAcct}`))
      }
    } catch { /* storage unavailable */ }
    toast('قالب‌بندیِ انتخابی به‌دلیلِ خطا بازنشانی شد — صفحه ادامه می‌دهد', { icon: '🛟' })
  }
  // design-mode DRAG (like the official-letter page): press a block and pull —
  // it moves via the same mt/mis offsets the panel edits (scoped per account/
  // template like every other layout change). A real drag suppresses the
  // click-opens-panel that follows; a plain click still opens the panel.
  const olSkipClick = useRef(false)
  const olPanelPos = useRef<{ x: number; y: number } | null>(null)
  const onPreviewPointerDown = (e: React.PointerEvent) => {
    olSkipClick.current = false   // new gesture — a stale flag must not eat it
    if ((!olDesign && !olSel) || e.button !== 0) return
    const t = e.target as HTMLElement
    if (!t || t.closest('.olp-panel,.olf-bar')) return
    const el = (t.closest('span,td,th,li,p,div') as HTMLElement) || null
    if (!el || !printRef.current?.contains(el)) return
    const key = elPath(el)
    if (!key) return
    // outside layout mode only the dblclicked (selected) element is draggable
    if (!olDesign && key !== olSel?.key) return
    const b = olEffLayout[key] || {}
    const r = el.getBoundingClientRect()
    // press near a side edge ⇒ resize that side; anywhere else ⇒ FREE move
    // (transform-based, Word "behind text": no flow resistance, any direction)
    const EDGE = 8
    const mode: 'move' | 'r' | 'l' = e.clientX > r.right - EDGE ? 'r' : e.clientX < r.left + EDGE ? 'l' : 'move'
    const drag = {
      key, sx: e.clientX, sy: e.clientY, mode,
      dx0: b.dx || 0, dy0: b.dy || 0, w0: b.wx || r.width,
      moved: false,
    }
    const mv = (ev: PointerEvent) => {
      const dx = ev.clientX - drag.sx, dy = ev.clientY - drag.sy
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 3) return
      drag.moved = true
      setOlLayout((s) => {
        const cur: OlBox = { ...(s[drag.key] || {}) }
        if (drag.mode === 'move') { cur.dx = Math.round(drag.dx0 + dx); cur.dy = Math.round(drag.dy0 + dy) }
        else if (drag.mode === 'r') cur.wx = Math.max(24, Math.round(drag.w0 + dx))
        else { cur.wx = Math.max(24, Math.round(drag.w0 - dx)); cur.dx = Math.round(drag.dx0 + dx) }
        return { ...s, [drag.key]: cur }
      })
    }
    const up = () => {
      document.removeEventListener('pointermove', mv)
      document.removeEventListener('pointerup', up)
      if (drag.moved) olSkipClick.current = true   // consumed by the next click
    }
    document.addEventListener('pointermove', mv)
    document.addEventListener('pointerup', up)
    e.preventDefault()
  }
  // design-mode hover: outline the block a click would edit (cleared on leave/off)
  const clearOlHover = () => {
    const el = olHoverEl.current
    if (el) { el.style.outline = ''; el.style.outlineOffset = ''; olHoverEl.current = null }
  }
  const onPreviewHover = (e: React.MouseEvent) => {
    const t = e.target as HTMLElement
    const el = (t?.closest('span,td,th,li,p,div') as HTMLElement) || null
    if (!el || !printRef.current?.contains(el) || el.closest('.olp-panel,.olf-bar')) { clearOlHover(); return }
    if (olHoverEl.current !== el) {
      clearOlHover()
      olHoverEl.current = el
      el.style.outline = '2px dashed #f59e0b'
      el.style.outlineOffset = '1px'
    }
  }
  const onPreviewClick = (e: React.MouseEvent) => {
    if (olSkipClick.current) { olSkipClick.current = false; return }  // it was a drag
    onPreviewDblClick(e)
  }
  const onPreviewDblClick = (e: React.MouseEvent) => {
    const t = e.target as HTMLElement
    if (!t || t.closest('.olp-panel')) return
    const el = (t.closest('span,td,th,li,p,div') as HTMLElement) || t
    const key = elPath(el)
    if (!key) return
    e.preventDefault()
    // the panel opens OUT OF THE WAY (screen edge, or wherever the user last
    // dragged it) instead of on top of the text being adjusted
    const pos = olPanelPos.current || {
      x: Math.max(8, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 300),
      y: 90,
    }
    setOlSel({
      key,
      label: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 44) || 'عنصر',
      ...pos,
    })
  }
  // the panel itself is draggable by its header; the position sticks
  const startPanelDrag = (e: React.PointerEvent) => {
    const sel = olSel
    if (!sel) return
    const ox = e.clientX - sel.x, oy = e.clientY - sel.y
    const mv = (ev: PointerEvent) => {
      const x = Math.max(0, ev.clientX - ox), y = Math.max(0, ev.clientY - oy)
      olPanelPos.current = { x, y }
      setOlSel((s) => (s ? { ...s, x, y } : s))
    }
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv)
    document.addEventListener('pointerup', up)
    e.preventDefault()
  }

  const field = 'w-full border border-gray-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-yellow-50'
  // F is a render *function* (not a nested component) so inputs keep focus while
  // typing. Labels are Persian-first (what the field is + where it prints) with
  // the English key as a subtitle — see LABELS.
  const FieldLabel = ({ k }: { k: string }) => {
    const L = LABELS[k] || { fa: k, en: '' }
    return (
      <span className="flex items-baseline justify-between gap-1 text-[11px]">
        <span className="text-gray-700 font-medium" dir="rtl">{L.fa}</span>
        {L.en && <span className="text-gray-400 truncate" dir="ltr">{L.en}</span>}
      </span>
    )
  }
  const F = (k: string, area?: boolean) => (
    <label className="block">
      <FieldLabel k={k} />
      {area
        ? <textarea value={f[k]} onChange={set(k)} rows={3} className={field + ' font-mono text-xs'} />
        : <input value={f[k]} onChange={set(k)} className={field} />}
    </label>
  )

  // Account number as a row of one-digit cells, like the scanned form.
  const DigitBoxes = ({ value }: { value: string }) => {
    const digits = String(value || '').replace(/\D/g, '')
    const cells = digits ? digits.split('') : Array(12).fill('')
    return <div className="pl-digits">{cells.map((d, i) => <span key={i}>{d}</span>)}</div>
  }
  const CheckBox = ({ on, onClick }: { on: boolean; onClick: () => void }) => (
    <span className={'pl-chkbox' + (on ? ' on' : '')} onClick={onClick} role="checkbox" aria-checked={on}>{on ? '✓' : ''}</span>
  )

  // Letterhead differs per form type (verbatim from the scanned samples) and
  // repeats on every page (ref/date included).
  const Letterhead = ({ mode }: { mode: 'english' | 'bilingual' }) =>
    mode === 'english' ? (
      <div className="ol-head ol-head--en">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={LH_LOGO} alt="Bank Saderat Iran — المكتب الاقليمي REGIONAL OFFICE" className="ol-logo-lh" />
        <div className="ol-head-right ol-head-right--en">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LH_NAME} alt={'بنك صادرات ايران إ.ع.م. BANK SADERAT IRAN U.A.E "Licensed by CBUAE"'} className="ol-name-lh" />
          <div className="ol-refblock">
            <div className="ol-refline">REF: <RefNo /></div>
            <div className="ol-refline">DATE: {V('IssueDate', '____________')}</div>
          </div>
        </div>
      </div>
    ) : (
      <div className="ol-head ol-head--bi">
        <div className="ol-head-left">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LH_LOGO} alt="Bank Saderat Iran — المكتب الاقليمي REGIONAL OFFICE" className="ol-logo-lh ol-logo-lh--bi" />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LH_NAME} alt={'بنك صادرات ايران إ.ع.م. BANK SADERAT IRAN U.A.E "Licensed by CBUAE"'} className="ol-name-lh ol-name-lh--bi" />
        </div>
        <div className="ol-head-right ol-head-right--bi">
          <div className="ol-bsi">BSI-ROL-V002-2024</div>
          <table className="ol-hdr-tbl"><tbody>
            <tr><td className="hdr-en">Date</td><td className="hdr-v">{V('IssueDate', '—')}</td><td className="hdr-ar" dir="rtl">التاريخ</td></tr>
            <tr><td className="hdr-en">Branch Name &amp; Code</td><td className="hdr-v">{V('Branch', '—')}</td><td className="hdr-ar" dir="rtl">اسم و رقم الفرع</td></tr>
            <tr><td className="hdr-en">Offer Letter Ref #</td><td className="hdr-v"><RefNo /></td><td className="hdr-ar" dir="rtl">رقم اشعار القرض</td></tr>
          </tbody></table>
        </div>
      </div>
    )

  // Footer differs per form type: english carries the bank address + SWIFT with a
  // "N | Page" marker; bilingual carries only "Page N of M".
  const PageFooter = ({ mode, n, total }: { mode: 'english' | 'bilingual'; n: number; total: number }) =>
    mode === 'english' ? (
      <div className="ol-foot ol-foot--en">
        <div className="ol-foot-pg">{n} | Page</div>
        <div className="ol-foot-addr">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={LH_FOOTER} alt={`${FOOT_AR} — ${FOOT_EN} — ${FOOT_SWIFT}`} className="ol-foot-img" />
        </div>
      </div>
    ) : (
      <div className="ol-foot ol-foot--bi">Page {n} of {total}</div>
    )

  // Bilingual EN/AR side-by-side line.
  const Row2 = ({ en, ar, bold }: { en: React.ReactNode; ar: React.ReactNode; bold?: boolean }) => (
    <div className="bi-row2" style={bold ? { fontWeight: 700 } : undefined}><div>{en}</div><div className="ar" dir="rtl">{ar}</div></div>
  )

  return (
    <Layout>
      <style>{`
        .ol-page { box-sizing: border-box; width: 210mm; min-height: 297mm; background:#fff; margin:0 auto 8mm;
                   padding: 9mm 13mm 13mm; color:#111;
                   /* mixed-script default: Latin resolves in Times, Persian/Arabic
                      falls through to B Nazanin (per-character font fallback) */
                   font-family: "Times New Roman", "B Nazanin", "Traditional Arabic", Georgia, serif;
                   font-size: 9.3pt; line-height: 1.2; box-shadow: 0 1px 6px rgba(0,0,0,.12); position:relative; }
        .ol-fit { transform-origin: top left; display:flex; flex-direction:column; min-height:255mm; }
        .ol-head { display:flex; justify-content:space-between; align-items:flex-start; padding-bottom:2mm; }
        .ol-head--en { margin-bottom:4mm; align-items:center; }
        .ol-head-left { display:flex; gap:3mm; align-items:center; }
        .ol-logo { height:12mm; width:auto; object-fit:contain; } /* legacy (quarantined) */
        /* verbatim letterhead images (real-letter proportions: emblem ~28x27mm, wordmark ~65x20mm) */
        .ol-logo-lh { height:26mm; width:auto; object-fit:contain; }
        .ol-name-lh { display:block; width:64mm; height:auto; margin:0 0 1.5mm auto; }
        .ol-logo-lh--bi { height:16mm; }
        .ol-name-lh--bi { width:44mm; margin:0; }
        .ol-ro { text-align:center; line-height:1.2; }
        .ol-ro-ar { font-size:8.5pt; color:#222; text-align:center; }
        .ol-ro-en { font-family:Arial, sans-serif; font-size:7.6pt; letter-spacing:1px; color:#222; text-align:center; }
        .ol-head-right--en { text-align:right; font-family:Arial, sans-serif; line-height:1.3; }
        .ol-bank-ar { font-size:10.5pt; color:#111; font-family:"Traditional Arabic","Times New Roman",serif; }
        .ol-bank-en { font-weight:800; font-size:12pt; color:#0a1f6b; letter-spacing:.3px; }
        .ol-uae { font-weight:600; font-size:8pt; }
        .ol-lic { font-size:7.5pt; font-style:italic; margin-bottom:2mm; }
        .ol-refblock { text-align:left; display:inline-block; }
        .ol-refline { font-size:8.7pt; }
        .ol-head--bi .ol-head-left > div { line-height:1.15; }
        .ol-lic-bi { font-size:7pt; color:#333; }
        .ol-head-right--bi { text-align:right; }
        .ol-bsi { font-size:7.5pt; font-family:Arial, sans-serif; margin-bottom:1mm; }
        .ol-hdr-tbl { border-collapse:collapse; font-size:7.5pt; margin-left:auto; }
        .ol-hdr-tbl td { border:1px solid #000; padding:0.6mm 1.5mm; white-space:nowrap; }
        .ol-hdr-tbl .hdr-en { text-align:left; font-family:Arial, sans-serif; }
        .ol-hdr-tbl .hdr-v { text-align:center; font-weight:700; min-width:24mm; }
        .ol-hdr-tbl .hdr-ar { text-align:right; }
        .ol-title { text-align:center; font-weight:800; font-size:13pt; text-decoration:underline; margin:3mm 0 1mm; letter-spacing:1px; }
        .ol-title-ar { text-align:center; font-weight:800; font-size:12pt; margin:0 0 2mm; }
        .ol-rcpt { font-weight:700; }
        .ol-p { margin:1.4mm 0; text-align:justify; }
        .ol-tbl { width:100%; border-collapse:collapse; margin:2.5mm 0; }
        .ol-tbl th, .ol-tbl td { border:1px solid #000; padding:1.2mm 2mm; font-size:9pt; text-align:center; }
        .ol-tbl th { background:#e9e9ee; font-family:Arial, sans-serif; }
        .ol-sec { white-space:pre-wrap; font-size:9pt; margin:1mm 0 2mm; }
        .ol-sign { display:flex; justify-content:space-between; margin-top:9mm; font-weight:700; font-size:9pt; }
        .ol-sign span { border-top:1px solid #000; padding-top:1mm; width:70mm; text-align:center; }
        /* page-1 signatures: stacked left, underlined, stamp room between */
        .ol-sign-stack { font-weight:700; font-size:9.5pt; text-align:left; }
        .ol-sign-stack > div { text-decoration:underline; }
        .ol-sign-stack-gap { margin-top:16mm; }
        .ol-terms-h { font-weight:800; text-decoration:underline; margin:2.5mm 0 1.5mm; }
        ol.ol-terms { margin:0; padding-left:6mm; } ol.ol-terms li { margin:0.8mm 0; text-align:justify; }
        .ol-foot { position:absolute; bottom:5mm; left:13mm; right:13mm; border-top:0.8px solid #555; padding-top:1.2mm; }
        /* english footer = verbatim blue banner image (it carries its own blue top rule) */
        .ol-foot--en { display:flex; align-items:flex-end; gap:4mm; border-top:0; padding-top:0; }
        .ol-foot-pg { font-family:Georgia,serif; font-size:9pt; white-space:nowrap; }
        .ol-foot-addr { flex:1; text-align:center; line-height:1.25; }
        .ol-foot-img { display:inline-block; width:100%; max-width:152mm; height:auto; }
        .ol-foot-ar { font-size:8pt; color:#111; }  /* legacy (quarantined) */
        .ol-foot-en { font-style:italic; font-size:8pt; color:#111; }
        .ol-foot-swift { font-style:italic; font-size:8pt; color:#111; }
        .ol-foot--bi { text-align:right; font-family:Arial, sans-serif; font-weight:700; font-size:8.5pt; bottom:7mm; }
        /* bilingual pages are framed by a full-page border, like the scanned form */
        .ol-page--bordered::before { content:''; position:absolute; top:5mm; left:6mm; right:6mm; bottom:5mm; border:1px solid #111; pointer-events:none; }
        .ol-dots { letter-spacing:1px; }
        /* row-7 guarantors: one per line, neatly stacked (not run together) */
        .guar-stack { margin-top:1mm; }
        .guar-line { font-weight:700; line-height:1.5; }
        /* unfilled variables blink until their field is filled (never printed) */
        .olv-e { background:#fde047; border-radius:2px; padding:0 3px; animation:olvB 1.1s ease-in-out infinite; cursor:help; }
        @keyframes olvB { 0%,100% { background-color:#fef9c3 } 50% { background-color:#fde047 } }
        /* dblclick layout panel */
        .olp-panel { position:fixed; z-index:60; width:270px; background:#fff; border:1px solid #cbd5e1; border-radius:12px;
                     box-shadow:0 10px 30px rgba(0,0,0,.18); padding:10px; font-size:12px; font-family:inherit; }
        .olp-h { display:flex; justify-content:space-between; align-items:center; font-weight:700; margin-bottom:8px; gap:6px; }
        .olp-h span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .olp-x { border:0; background:transparent; font-size:16px; cursor:pointer; color:#64748b; }
        .olp-row { display:flex; align-items:center; gap:6px; margin-bottom:6px; }
        .olp-row label { flex:1; color:#475569; }
        .olp-row input { width:64px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; }
        .olp-seg { display:flex; gap:4px; margin-bottom:6px; }
        .olp-seg button, .olp-row button { flex:1; border:1px solid #cbd5e1; background:#f8fafc; border-radius:6px; padding:3px 4px; cursor:pointer; }
        .olp-seg button.on, .olp-row button.on { background:#2563eb; color:#fff; border-color:#2563eb; }
        .olp-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:6px; }
        .olp-grid label { display:flex; flex-direction:column; gap:2px; color:#475569; }
        .olp-grid input { border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; width:100%; }
        .olp-font { flex:1; border:1px solid #cbd5e1; border-radius:6px; padding:2px 6px; max-width:170px; }
        .olp-txt { display:block; color:#475569; margin-bottom:6px; }
        .olp-txt textarea { display:block; width:100%; height:56px; margin-top:2px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 6px; font-size:11px; resize:vertical; }
        .olp-actions { display:flex; gap:6px; }
        .olp-actions button { flex:1; border:1px solid #fca5a5; color:#b91c1c; background:#fef2f2; border-radius:6px; padding:4px; cursor:pointer; }
        .olp-hint { margin-top:6px; color:#94a3b8; font-size:10.5px; line-height:1.6; }
        /* selection format bar */
        .olf-bar { position:fixed; z-index:70; display:flex; gap:2px; background:#1e293b; border-radius:8px; padding:4px;
                   box-shadow:0 8px 24px rgba(0,0,0,.3); }
        .olf-bar button { border:0; background:transparent; color:#e2e8f0; min-width:28px; height:26px; border-radius:6px;
                          cursor:pointer; font-size:13px; }
        .olf-bar button:hover { background:#334155; }
        /* bilingual blocks */
        .bi-row2 { display:flex; justify-content:space-between; gap:6mm; margin:1.2mm 0; }
        .bi-row2 .ar { direction:rtl; text-align:right; font-size:10pt; }
        .bi-conf { text-align:right; font-size:9pt; }
        .ol-p.ar { font-size:9.5pt; }
        /* Personal-loan tables: dark section bars, gray label cells, bordered grid */
        .pl-tbl { width:100%; border-collapse:collapse; margin:2mm 0; }
        .pl-tbl td { border:1px solid #000; padding:1mm 1.6mm; font-size:8.4pt; vertical-align:middle; }
        .pl-bar td { background:#1b1c22; color:#fff; padding:1.1mm 2mm; }
        .pl-bar-row { display:flex; justify-content:space-between; font-weight:700; font-size:9pt; }
        .pl-lbl { background:#d6d8e2; font-weight:600; width:23%; }
        .pl-lbl .ar { font-size:7.6pt; font-weight:400; direction:rtl; }
        .pl-val { background:#fff; }
        .pl-num { width:6mm; text-align:center; font-weight:700; background:#d6d8e2; }
        .pl-chk { width:8mm; text-align:center; }
        .pl-ar { text-align:right; direction:rtl; font-size:8.2pt; }
        .pl-chkbox { display:inline-block; width:3.6mm; height:3.6mm; border:1.2px solid #000; line-height:3.3mm; text-align:center; font-size:8pt; font-weight:800; color:#0a6b2e; cursor:pointer; }
        .pl-tick { color:#0a6b2e; font-weight:800; margin-left:1.5mm; }
        .pl-digits { display:flex; gap:0; flex-wrap:wrap; }
        .pl-digits span { display:inline-block; min-width:5.4mm; height:5.4mm; line-height:5.4mm; border:1px solid #000; border-left:none; text-align:center; font-weight:700; font-size:9.5pt; }
        .pl-digits span:first-child { border-left:1px solid #000; }
        .pl-note { font-size:7.8pt; margin:1mm 0; font-weight:600; }
        .pl-close { margin:2mm 0; }
        .pl-close .ar { direction:rtl; text-align:right; font-size:8.6pt; }
        .pl-decl-h { display:flex; justify-content:space-between; font-weight:700; margin:1mm 0; }
        .pl-decl-h .ar { direction:rtl; }

        @media print {
          @page { size: A4 portrait; margin: 0; }
          html, body, .min-h-screen { margin:0 !important; padding:0 !important; min-height:0 !important; background:#fff !important; }
          .ol-page { margin:0 !important; box-shadow:none !important; page-break-after: always; }
          .ol-page:last-child { page-break-after: auto; }
          .ol-tbl, .pl-tbl tr, .ol-sign { page-break-inside: avoid; }
          #ol-controls { display:none !important; }
          .pl-chkbox { cursor:default; }
          .olp-panel { display:none !important; }
          .olf-bar { display:none !important; }
          .olv-e { animation:none !important; background:none !important; padding:0; }
          /* design-mode hover outline must never reach paper */
          #offer-print * { outline:none !important; }
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        {/* ---------------- controls (not printed) ---------------- */}
        <div id="ol-controls" className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-blue-600 text-white rounded-lg p-2"><Printer size={18} /></div>
            <div>
              <h1 className="text-lg font-bold text-gray-900" dir="rtl">Offer Letter — نامهٔ پیشنهادِ تسهیلات</h1>
              <p className="text-gray-500 text-xs" dir="rtl">فرم خالی شروع می‌شود؛ با واردکردن شماره‌حساب و «بارگیری»، از آخرین تسهیلاتِ مشتری خودکار پر می‌شود (قالب هم بر اساس نوع حساب×تسهیلات انتخاب می‌شود). متغیرهای پرنشده در متنِ نامه چشمک می‌زنند تا پر شوند، و با دبل‌کلیک روی هر بخشِ نامه پنلِ چینش (فونت/تراز/جهت/فاصله) باز می‌شود.</p>
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-2 mb-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
            <label className="flex-1 min-w-[160px]">
              <span className="text-[11px] text-gray-500">Account No</span>
              <input value={acc} onChange={(e) => setAcc(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && loadAccount()}
                placeholder="مثلاً 172999" className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </label>
            <button onClick={loadAccount} disabled={loading} type="button"
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Search size={15} /> {loading ? '...' : 'بارگیری'}
            </button>
            <label>
              <span className="text-[11px] text-gray-500 block">قالب</span>
              {/* dir=rtl: the options mix Persian with Latin (EN/AR, English) —
                  without an explicit RTL ancestor the browser scrambles them. */}
              <select value={tpl} onChange={(e) => setTpl(e.target.value as any)} dir="rtl" className="border border-gray-300 rounded-md px-3 py-2 text-sm">
                <option value="auto">خودکار — {autoTpl === 'personal' ? 'وام شخصی دوزبانه' : 'English عمومی'}</option>
                <option value="english">English — اضافه‌برداشت/عمومی (۳ صفحه)</option>
                <option value="personal">وام شخصی دوزبانه EN/AR (۴ صفحه)</option>
              </select>
            </label>
            <button onClick={() => saveOffer()} disabled={saving} type="button"
              className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Save size={15} /> {saving ? '...' : 'ذخیره'}
            </button>
            <button onClick={printDoc} type="button"
              className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Download size={15} /> Print / PDF
            </button>
            {/* page-wide layout mode, like the official-letter page's toolbar
                toggle — hover highlights a block, one click opens its layout
                panel (double-click keeps working without this mode too) */}
            <button onClick={() => { setOlDesign((d) => !d); setOlSel(null); clearOlHover() }} type="button"
              className={`flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-white ${olDesign ? 'bg-green-600 hover:bg-green-700' : 'bg-amber-500 hover:bg-amber-600'}`}>
              {olDesign ? '✓ پایانِ چیدمان' : 'چیدمان'}
            </button>
            <span className="text-[11px] text-gray-500 self-center" dir="rtl">
              {olAcct
                ? <>چینش فقط برای حسابِ <b dir="ltr">{olAcct}</b> ذخیره می‌شود — قالبِ اصلی دست‌نخورده می‌ماند</>
                : 'فرم خالی است — تغییرِ چینش، قالبِ اصلی (پیش‌فرضِ همهٔ حساب‌ها) را به‌روز می‌کند'}
            </span>
          </div>

          {/* Draft (مصوبه) drop zone → smart extract into the fields + customer DB */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleDraft(e.dataTransfer.files?.[0]) }}
            className={`mb-3 rounded-lg border-2 border-dashed px-4 py-3 text-center transition-colors ${dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}`}
          >
            <input id="draftFile" type="file" accept=".docx" className="hidden"
              onChange={(e) => { handleDraft(e.target.files?.[0]); e.currentTarget.value = '' }} />
            <div className="flex items-center justify-center gap-2 text-sm">
              <Upload size={16} className="text-blue-600" />
              <label htmlFor="draftFile" className="cursor-pointer font-medium text-blue-700 hover:underline">انتخاب فایل پیش‌نویس مصوبه (.docx)</label>
              <span className="text-gray-500">یا فایل را اینجا بکش و رها کن — استخراج هوشمند فیلدها و ثبت در دیتابیس مشتری</span>
              {extracting && <span className="text-blue-600 font-medium">⏳ در حال استخراج…</span>}
            </div>
          </div>

          {/* Smart sheet: only the fields THIS template actually prints are shown. */}
          <p className="text-[11px] text-gray-400 mb-2" dir="rtl">
            فقط فیلدهای مرتبط با قالبِ انتخاب‌شده نمایش داده می‌شوند — قالب فعلی:{' '}
            <b>{effectiveTpl === 'personal' ? 'وام شخصی دوزبانه (EN/AR)' : 'English (اضافه‌برداشت / عمومی)'}</b>
          </p>

          <div className="text-xs font-bold text-gray-600 mb-1.5" dir="rtl">گیرندهٔ نامه — مشخصات مشتری</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {F('Prefix')}
            {F('CompanyName')}
            {F('AccountNumber')}
            {F('POBox')}
            {F('CityCountry')}
            <label className="block">
              <FieldLabel k="Branch" />
              <select value={f.Branch} onChange={set('Branch')} className={field}>
                <option value="">—</option>
                {BRANCH_OPTIONS.map((b) => <option key={b} value={b}>{b}</option>)}
                {f.Branch && !BRANCH_OPTIONS.includes(f.Branch) && <option value={f.Branch}>{f.Branch}</option>}
              </select>
            </label>
            <label className="block">
              <span className="flex items-baseline justify-between gap-1 text-[11px]">
                <span className="text-gray-700 font-medium" dir="rtl">شمارهٔ نامه (سریال متغیر)</span>
                <span className="text-gray-400" dir="ltr">Ref Serial</span>
              </span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400">182/4/</span>
                <input value={f.RefSerial} onChange={set('RefSerial')} className={field} placeholder="202" />
                <span className="text-xs text-gray-400">/</span>
                <input value={f.RefYear} onChange={set('RefYear')} className={field + ' w-16'} />
              </div>
            </label>
            {F('IssueDate')}
            {F('AcceptanceDate')}
            {/* Facility Type: combobox — pick from the DB-backed list OR type a
                new one; a brand-new name is added to the list on Save. */}
            <label className="block">
              <FieldLabel k="FacilityType" />
              <input value={f.FacilityType} onChange={set('FacilityType')} list="ftype-options" className={field} placeholder="Overdraft / Personal Loan / …" />
              <datalist id="ftype-options">
                {ftypes.map((t) => <option key={t} value={t} />)}
              </datalist>
            </label>
          </div>

          {effectiveTpl === 'english' && <>
            <div className="text-xs font-bold text-gray-600 mt-3 mb-1.5" dir="rtl">مشخصات تسهیلات — جدول صفحهٔ ۱ و شرایط (قالب English)</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {F('RequestDate')}
              {F('CreditLimit')}
              {F('InterestRate')}
              {F('ValidUntil')}
              {F('ProcessingFee')}
              {F('AccountSuffix')}
            </div>

            {/* ---- multi-facility rows + automatic processing charges ---- */}
            <div className="mt-3 border border-amber-200 rounded-lg p-3 bg-amber-50/50">
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2" dir="rtl">
                <span className="text-xs font-bold text-gray-700">
                  تسهیلاتِ جدول صفحهٔ ۱ — ردیف ۱ همان فیلدهای بالاست؛ برای تسهیلاتِ بیشتر ردیف اضافه کن (جمعِ سقف‌ها در ردیفِ Total چاپ می‌شود)
                </span>
                <button type="button" onClick={() => setExtraFacs((r) => [...r, { type: '', limit: '', rate: '', remarks: '', fd: false, staff: false, temp: false }])}
                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md px-2.5 py-1">+ افزودن ردیف تسهیلات</button>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-gray-600 mb-2" dir="rtl">
                <span className="font-medium">ردیف ۱ ({(f.FacilityType || 'نوع؟')}):</span>
                <label className="flex items-center gap-1"><input type="checkbox" checked={fac1.fd} onChange={(e) => setFac1((s) => ({ ...s, fd: e.target.checked }))} /> پوشش ۱۰۰٪ سپرده (underlien)</label>
                <label className="flex items-center gap-1"><input type="checkbox" checked={fac1.staff} onChange={(e) => setFac1((s) => ({ ...s, staff: e.target.checked }))} /> تسهیلاتِ کارمندی (معاف)</label>
                <label className="flex items-center gap-1"><input type="checkbox" checked={fac1.temp} onChange={(e) => setFac1((s) => ({ ...s, temp: e.target.checked }))} /> موقت</label>
              </div>
              <div className="mb-2">{F('Remarks', true)}</div>
              {extraFacs.map((r, i) => (
                <div key={i} className="mb-2 border border-gray-200 rounded-md p-2 bg-white">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <input value={r.type} onChange={setFacRow(i, 'type')} list="ftype-options" placeholder={`نوع تسهیلات ردیف ${i + 2} — مثلاً Cheque Discount`} className={field} />
                    <input value={r.limit} onChange={setFacRow(i, 'limit')} placeholder="سقف اعتبار (AED) — 2,800,000/-" className={field} dir="ltr" />
                    <input value={r.rate} onChange={setFacRow(i, 'rate')} placeholder="نرخ سود — 11%" className={field} dir="ltr" />
                    <input value={r.remarks} onChange={setFacRow(i, 'remarks')} placeholder="Remarks این ردیف" className={field} dir="ltr" />
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-gray-600 mt-1.5" dir="rtl">
                    <label className="flex items-center gap-1"><input type="checkbox" checked={r.fd} onChange={setFacRow(i, 'fd')} /> پوشش ۱۰۰٪ سپرده</label>
                    <label className="flex items-center gap-1"><input type="checkbox" checked={r.staff} onChange={setFacRow(i, 'staff')} /> تسهیلاتِ کارمندی</label>
                    <label className="flex items-center gap-1"><input type="checkbox" checked={r.temp} onChange={setFacRow(i, 'temp')} /> موقت</label>
                    <button type="button" onClick={() => setExtraFacs((rows) => rows.filter((_, idx) => idx !== i))}
                      className="text-red-500 hover:text-red-700 marker:mr-auto" style={{ marginInlineStart: 'auto' }}>✕ حذف ردیف</button>
                  </div>
                </div>
              ))}
              <div className="flex items-center gap-3 flex-wrap mt-1" dir="rtl">
                <button type="button" onClick={() => computeCharges()}
                  className="text-xs bg-amber-600 hover:bg-amber-700 text-white rounded-md px-3 py-1.5">
                  محاسبهٔ کارمزد از تعرفه ← ProcessingFee
                </button>
                <label className="flex items-center gap-1 text-[11px] text-gray-600">
                  <input type="checkbox" checked={autoCharge} onChange={(e) => setAutoCharge(e.target.checked)} />
                  محاسبهٔ خودکار با هر تغییرِ نوع/مبلغ
                </label>
                <span className="text-[11px] text-gray-400">تعرفه از «Charge Tariff» در منو قابل‌ویرایش است؛ جمعِ کارمزدِ همهٔ ردیف‌ها در بند ۲۳ می‌نشیند (+VAT).</span>
              </div>
              {chargeInfo && (
                <div className="mt-2 text-[11px] bg-white border border-amber-200 rounded-md p-2" dir="rtl">
                  {chargeInfo.lines.map((l, i) => (
                    <div key={i} className="flex justify-between gap-2">
                      <span>{l.label}</span>
                      <span dir="ltr" className="font-mono">{l.base.toLocaleString('en-US')} → AED {l.charge.toLocaleString('en-US')}</span>
                    </div>
                  ))}
                  <div className="flex justify-between gap-2 border-t mt-1 pt-1 font-bold">
                    <span>جمع (بند ۲۳)</span>
                    <span dir="ltr" className="font-mono">AED {chargeInfo.lines.reduce((a, l) => a + l.charge, 0).toLocaleString('en-US')} + VAT</span>
                  </div>
                  {chargeInfo.warnings.map((w, i) => <div key={i} className="text-amber-700 mt-1">⚠ {w}</div>)}
                </div>
              )}
            </div>
            <div className="grid md:grid-cols-1 gap-2.5 mt-2.5">
              {F('RequiredSecurities', true)}
            </div>
          </>}

          {effectiveTpl === 'personal' && <>
            <div className="text-xs font-bold text-gray-600 mt-3 mb-1.5" dir="rtl">جزئیات وام — جدول «Details of Loan» (قالب دوزبانه)</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {F('SubjectDate')}
              {F('LoanAmount')}
              {F('LoanInterestRate')}
              {F('LoanTenor')}
              <label className="block">
                <FieldLabel k="MonthlyInstallment" />
                <div className="flex items-center gap-1">
                  <input value={f.MonthlyInstallment} onChange={set('MonthlyInstallment')} className={field} />
                  <button type="button" title="محاسبهٔ قسط (مانده‌ی نزولی) از مبلغ/نرخ/مدت"
                    onClick={() => { const m = emiSuggest(); if (m) setF((s) => ({ ...s, MonthlyInstallment: m })); else toast.error('مبلغ وام و مدت را وارد کنید') }}
                    className="shrink-0 border border-gray-300 rounded-md px-2 py-1.5 text-xs bg-white hover:bg-blue-50 text-blue-700">
                    محاسبه
                  </button>
                </div>
              </label>
              {F('Purpose')}
              {F('LienAmount')}
            </div>
            <div className="grid md:grid-cols-2 gap-2.5 mt-2.5">
              {F('NotesPersonal', true)}
              {F('Remarks', true)}
            </div>

            {/* Guarantors — printed into securities item 7 (like the bank sample)
                and synced to the customer's guarantor records on Save. */}
            <div className="mt-3 border border-gray-200 rounded-lg p-3 bg-gray-50/60">
              <div className="flex items-center justify-between mb-2" dir="rtl">
                <span className="text-xs font-bold text-gray-600">ضامن‌ها — در بند ۷ «مدارک موردنیاز» چاپ و در پروندهٔ مشتری ثبت می‌شوند</span>
                <button type="button" onClick={() => setGuars((g) => [...g, { name: '', account: '' }])}
                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md px-2.5 py-1">+ افزودن ضامن</button>
              </div>
              {guars.length === 0 && (
                <p className="text-[11px] text-gray-400" dir="rtl">ضامنی ثبت نشده است. ضامن‌های موجود مشتری هنگام «بارگیری» خودکار می‌آیند؛ ضامن جدید را با دکمهٔ بالا اضافه کن.</p>
              )}
              {guars.map((g, i) => (
                <div key={i} className="flex items-center gap-2 mb-1.5">
                  <input value={g.name} onChange={setGuar(i, 'name')} placeholder="Guarantor name — نام ضامن (مثل Mr. MUHAMMAD EBRAHIM)" className={field} />
                  <input value={g.account} onChange={setGuar(i, 'account')} placeholder="A/C No — حساب ضامن" className={field + ' md:max-w-[200px]'} dir="ltr" />
                  <button type="button" title="حذف از نامه (رکورد پرونده حذف نمی‌شود)"
                    onClick={() => setGuars((rows) => rows.filter((_, idx) => idx !== i))}
                    className="shrink-0 text-red-500 hover:text-red-700 border border-gray-200 rounded-md px-2 py-1.5 text-xs bg-white">✕</button>
                </div>
              ))}
            </div>
          </>}
        </div>

        {/* ---------------- printable document ----------------
            dblclick any block → layout panel (font/align/dir/spacing/offsets) */}
        <OlSafe onCrash={onPreviewCrash}>
        <div id="offer-print" dir="ltr" ref={printRef}
          /* CRASH GUARD: while selection marks exist, remount the whole preview
             on every render (fresh tree = React never reconciles against the
             text nodes our mark spans moved → no removeChild crash); with no
             marks the key is stable and nothing changes. Marks + overrides are
             re-applied by the after-render effect either way. */
          key={Object.keys(olEffMarks).length || olHasTxt ? `mk-${++olRenderSeq.current}` : 'stable'}
          onDoubleClick={onPreviewDblClick} onMouseUp={onPreviewMouseUp}
          onClick={olDesign ? onPreviewClick : undefined}
          onPointerDown={olDesign || olSel ? onPreviewPointerDown : undefined}
          onMouseOver={olDesign ? onPreviewHover : undefined}
          onMouseLeave={olDesign ? clearOlHover : undefined}
          style={olDesign ? { cursor: 'move' } : undefined}>
          {effectiveTpl === 'english' ? (
            <>
              {/* ===== ENGLISH PAGE 1 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <div className="ol-title">OFFER LETTER</div>
                  <div className="ol-rcpt">{V('Prefix', 'M/S.')} {V('CompanyName', '________________')}</div>
                  <div className="ol-rcpt">ACCOUNT NO: {V('AccountNumber', '____________')}</div>
                  <div>P.O. Box {V('POBox', '______')}</div>
                  <div>{V('CityCountry', '________________')}</div>
                  <div className="ol-p" style={{ fontWeight: 700 }}>Private &amp; Confidential</div>
                  <div className="ol-p">Dear Sir,</div>
                  <div className="ol-p">With reference to your request via letter Dated: {V('RequestDate', '____________')}, we are pleased to inform you that the below mentioned {extraFacs.length
                    ? <>{[(f.FacilityType || '').trim(), ...extraFacs.map((r) => r.type.trim())].filter(Boolean).join(' and ') || '__________'} facilities are</>
                    : <>{V('FacilityType', '__________')} facility is</>} approved/renewed{f.ValidUntil ? ` for a period expiring on ${f.ValidUntil}` : ''} subject to the terms and conditions set out in this offer letter which forms an integral part of it and its provision:</div>
                  <table className="ol-tbl">
                    <thead><tr><th>Facility</th><th>Credit Limit (AED)</th><th>Interest Rate</th><th>Remarks</th></tr></thead>
                    <tbody>
                      <tr>
                        <td>{V('FacilityType', '—')}</td>
                        <td>{V('CreditLimit', '—')}</td>
                        <td style={{ whiteSpace: 'pre-wrap' }}>{V('InterestRate', '—')}</td>
                        <td style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>{f.Remarks || '—'}</td>
                      </tr>
                      {extraFacs.map((r, i) => (
                        <tr key={i}>
                          <td>{r.type || '—'}</td>
                          <td>{r.limit || '—'}</td>
                          <td style={{ whiteSpace: 'pre-wrap' }}>{r.rate || '—'}</td>
                          <td style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>{r.remarks || '—'}</td>
                        </tr>
                      ))}
                      {extraFacs.length > 0 && (
                        <tr style={{ fontWeight: 700 }}>
                          <td>Total</td>
                          <td>{(parseNum(f.CreditLimit) + extraFacs.reduce((a, r) => a + parseNum(r.limit), 0)).toLocaleString('en-US')}/-</td>
                          <td>-</td>
                          <td style={{ textAlign: 'left' }}>-</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                  <div className="ol-terms-h">REQUIRED SECURITIES / DOCUMENTS</div>
                  <div className="ol-sec">{V('RequiredSecurities', '____________________________')}</div>
                  {/* page-1 signatures: stacked LEFT (head above, customer below),
                      underlined labels with stamp room between — like the real
                      letter, NOT one row split left/right */}
                  <div className="ol-sign-stack" style={{ marginTop: 'auto' }}>
                    <div>Head of Credit Facility Department</div>
                    <div className="ol-sign-stack-gap">Customer Signature with Stamp</div>
                  </div>
                </div>
                <PageFooter mode="english" n={1} total={3} />
              </div>

              {/* ===== ENGLISH PAGE 2 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <div className="ol-terms-h">TERMS AND CONDITIONS:</div>
                  <ol className="ol-terms">{TERM_TEXTS.slice(0, 17).map((t, i) => <li key={i}>{fillN(t)}</li>)}</ol>
                  {/* like the source doc: a single bold label at the LEFT, no rule lines */}
                  <div style={{ marginTop: 'auto', fontWeight: 700, fontSize: '9pt' }}>Customer Signature with Stamp</div>
                </div>
                <PageFooter mode="english" n={2} total={3} />
              </div>

              {/* ===== ENGLISH PAGE 3 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <ol className="ol-terms" start={18}>{TERM_TEXTS.slice(17).map((t, i) => <li key={i}>{fillN(t)}</li>)}</ol>
                  <div className="ol-p">Please read the content of this letter and if you agree kindly sign the original copy and return it to us as confirmation for our records not later than one month from the date of this letter; if not accepted it will be deemed to have lapsed.</div>
                  <div className="ol-p">We trust that you will find the above limits and its terms to your satisfaction and will utilize the same for our mutual benefits. While assuring you of our best service at all times, we appreciate your kind co-operation and prompt reply.</div>
                  <div className="ol-p" style={{ marginTop: '4mm' }}>Yours truly,</div>
                  <div style={{ fontWeight: 700 }}>Bank Saderat Iran</div>
                  <div>Credit Facility Department</div>
                  {/* stamp+wet-signature room above the rule; the page's slack is
                      absorbed by the bottom sign's auto margin, so nothing shifts */}
                  <div className="ol-sign" style={{ marginTop: '22mm' }}><span>Manager Signature &amp; Stamp</span><span>&nbsp;</span></div>
                  <div className="ol-dots" style={{ marginTop: '6mm' }}>....................................................................................................................................</div>
                  <div className="ol-p">I read all pages of offer letter and I agreed with the terms and conditions mentioned thereof.</div>
                  <div className="ol-p">Encl: Duplicate of this letter accepted and agreed by</div>
                  <div>{isCorporate ? 'M/s' : 'Mr.'}: {V('CompanyName', '..............................................................')}</div>
                  <div>Date: {V('AcceptanceDate', '............................')}</div>
                  <div className="ol-sign" style={{ marginTop: 'auto' }}>
                    <span>Authorized Signature(s)</span>
                    {isCorporate ? <span>Company Stamp</span> : <span>&nbsp;</span>}
                  </div>
                </div>
                <PageFooter mode="english" n={3} total={3} />
              </div>
            </>
          ) : (
            /* ===== BILINGUAL PERSONAL LOAN (4 bordered pages, like the scan) ===== */
            <>
              {/* ===== BILINGUAL PAGE 1 — recipient, loan details, securities ===== */}
              <div className="ol-page ol-page--bordered">
                <div className="ol-fit">
                  <Letterhead mode="bilingual" />
                  <div className="bi-conf"><b>{PL.header.confidential.en}</b></div>
                  <div className="bi-conf" dir="rtl"><b>{PL.header.confidential.ar}</b></div>
                  <div className="ol-title">{PL.header.title.en}</div>
                  <div className="ol-title-ar" dir="rtl">{PL.header.title.ar}</div>
                  <div className="ol-rcpt">{f.Prefix && f.Prefix !== 'M/S.' ? f.Prefix + ' ' : ''}{V('CompanyName', '________________')}</div>
                  <div>P.O. Box: {V('POBox', '______')}</div>
                  <div>{V('CityCountry', '________________')}</div>
                  <Row2 en={<>Subject: Personal Loan Application dated: {V('SubjectDate', '__________')}</>} ar={'الموضوع: طلب القرض الشخصي المؤرخ'} bold />
                  <Row2 en={PL.dear.en} ar={PL.dear.ar} />
                  <div className="ol-p">{PL.intro.en}</div>
                  <div className="ol-p ar" dir="rtl" style={{ textAlign: 'right' }}>{PL.intro.ar}</div>

                  {/* Details of Loan */}
                  <table className="pl-tbl"><tbody>
                    <tr className="pl-bar"><td colSpan={4}><div className="pl-bar-row"><span>{PL.detailsTitle.en}</span><span dir="rtl">{PL.detailsTitle.ar}</span></div></td></tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.accountNumber.en}</div><div className="ar" dir="rtl">{PL.labels.accountNumber.ar}</div></td>
                      <td className="pl-val" colSpan={3}><DigitBoxes value={f.AccountNumber} /></td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.loanAmount.en}</div><div className="ar" dir="rtl">{PL.labels.loanAmount.ar}</div></td>
                      <td className="pl-val">{V('LoanAmount', '—')}{f.LoanAmount && <span className="pl-tick">✓</span>}</td>
                      <td className="pl-lbl"><div>{PL.labels.interestRate.en}</div><div className="ar" dir="rtl">{PL.labels.interestRate.ar}</div></td>
                      <td className="pl-val">{(f.LoanInterestRate || f.InterestRate) ? (f.LoanInterestRate || f.InterestRate) : V('LoanInterestRate', '—')}</td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.tenor.en}</div><div className="ar" dir="rtl">{PL.labels.tenor.ar}</div></td>
                      <td className="pl-val">{V('LoanTenor', '—')}{f.LoanTenor && <span className="pl-tick">✓</span>}</td>
                      <td className="pl-lbl"><div>{PL.labels.installment.en}</div><div className="ar" dir="rtl">{PL.labels.installment.ar}</div></td>
                      <td className="pl-val">{V('MonthlyInstallment', '—')}</td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.purpose.en}</div><div className="ar" dir="rtl">{PL.labels.purpose.ar}</div></td>
                      <td className="pl-val" colSpan={3}>{V('Purpose', '—')}</td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.processingFees.label.en}</div><div className="ar" dir="rtl">{PL.processingFees.label.ar}</div></td>
                      <td className="pl-val" colSpan={3} style={{ fontSize: '7.4pt' }}><div>{PL.processingFees.value.en}</div><div dir="rtl" style={{ textAlign: 'right' }}>{PL.processingFees.value.ar}</div></td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.latePayment.label.en}</div><div className="ar" dir="rtl">{PL.latePayment.label.ar}</div></td>
                      <td className="pl-val" colSpan={3} style={{ fontSize: '7.4pt' }}><div>{PL.latePayment.value.en}</div><div dir="rtl" style={{ textAlign: 'right' }}>{PL.latePayment.value.ar}</div></td>
                    </tr>
                  </tbody></table>

                  {/* Required Security Documents */}
                  <table className="pl-tbl"><tbody>
                    <tr className="pl-bar"><td colSpan={4}><div className="pl-bar-row"><span>{PL.securitiesTitle.en}</span><span dir="rtl">{PL.securitiesTitle.ar}</span></div></td></tr>
                    {PL.securities.map((s, i) => (
                      <tr key={i}>
                        <td className="pl-num">{s.n}</td>
                        <td className="pl-chk"><CheckBox on={!!checks[i]} onClick={() => toggleCheck(i)} /></td>
                        {/* Item 7 names the guarantor(s), exactly like the filled sample:
                            "… borrower(s) / -Mr. NAME- A/C NO.124076" */}
                        <td className="pl-val">
                          {replaceNode(s.en, '250,000', V('LienAmount', '________'))}
                          {s.n === '7' && guarItems.length ? <GuarStack /> : null}
                        </td>
                        <td className="pl-val pl-ar" dir="rtl">
                          {replaceNode(s.ar, '250,000', V('LienAmount', '________'))}
                          {s.n === '7' && guarItems.length ? <GuarStack dir="rtl" /> : null}
                        </td>
                      </tr>
                    ))}
                  </tbody></table>
                  <div className="pl-note" style={{ whiteSpace: 'pre-wrap' }}>{f.NotesPersonal}</div>
                </div>
                <PageFooter mode="bilingual" n={1} total={4} />
              </div>

              {/* ===== BILINGUAL PAGE 2 — terms 1–7 ===== */}
              <div className="ol-page ol-page--bordered">
                <div className="ol-fit">
                  <Letterhead mode="bilingual" />
                  <table className="pl-tbl"><tbody>
                    {PL.terms.slice(0, 7).map((t, i) => (
                      <tr key={i}><td className="pl-num">{i + 1}</td><td className="pl-val">{t.en}</td><td className="pl-val pl-ar" dir="rtl">{t.ar}</td></tr>
                    ))}
                  </tbody></table>
                </div>
                <PageFooter mode="bilingual" n={2} total={4} />
              </div>

              {/* ===== BILINGUAL PAGE 3 — terms 8–14 + closing note + bank signature ===== */}
              <div className="ol-page ol-page--bordered">
                <div className="ol-fit">
                  <Letterhead mode="bilingual" />
                  <table className="pl-tbl"><tbody>
                    {PL.terms.slice(7, 14).map((t, i) => (
                      <tr key={i}><td className="pl-num">{i + 8}</td><td className="pl-val">{t.en}</td><td className="pl-val pl-ar" dir="rtl">{t.ar}</td></tr>
                    ))}
                  </tbody></table>
                  <div className="pl-close"><div>{PL.closingNote.en}</div><div className="ar" dir="rtl">{PL.closingNote.ar}</div></div>
                  <Row2 en={PL.closing.yoursSincerely.en} ar={PL.closing.yoursSincerely.ar} />
                  <Row2 en={PL.closing.forBank.en} ar={PL.closing.forBank.ar} />
                  <div className="ol-sign" style={{ marginTop: '14mm' }}>
                    <span>{PL.closing.headDept.en}<br />{PL.closing.signStamp.en}</span>
                    <span dir="rtl">{PL.closing.headDept.ar}<br />{PL.closing.signStamp.ar}</span>
                  </div>
                </div>
                <PageFooter mode="bilingual" n={3} total={4} />
              </div>

              {/* ===== BILINGUAL PAGE 4 — borrower declaration ===== */}
              <div className="ol-page ol-page--bordered">
                <div className="ol-fit">
                  <Letterhead mode="bilingual" />
                  <div className="pl-decl-h"><span>Borrower Declaration:</span><span className="ar" dir="rtl">{PL.closing.borrowerDeclaration.ar}</span></div>
                  <table className="pl-tbl"><tbody>
                    <tr><td className="pl-val">{PL.declaration.en}</td><td className="pl-val pl-ar" dir="rtl">{PL.declaration.ar}</td></tr>
                  </tbody></table>
                  {/* signature block sits right below the declaration with room to
                      sign (owner: not glued to the very bottom of the page) */}
                  <table className="pl-tbl" style={{ marginTop: '14mm' }}><tbody>
                    <tr><td className="pl-lbl">{PL.borrowerSign[0].en}</td><td className="pl-val" style={{ height: '18mm' }}>&nbsp;</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[0].ar}</td></tr>
                    <tr><td className="pl-lbl">{PL.borrowerSign[1].en}</td><td className="pl-val">{V('CompanyName', '________')}</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[1].ar}</td></tr>
                    <tr><td className="pl-lbl">{PL.borrowerSign[2].en}</td><td className="pl-val">{V('AcceptanceDate', '________')}</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[2].ar}</td></tr>
                  </tbody></table>
                </div>
                <PageFooter mode="bilingual" n={4} total={4} />
              </div>
            </>
          )}
        </div>
        </OlSafe>

        {/* ---- selection format bar (like the letter page's floating toolbar):
             applies ONLY to the selected part of the sentence, not the block ---- */}
        {olFmt && (
          <div className="olf-bar" style={{ left: olFmt.x, top: olFmt.y }}>
            <button title="توپُر — فقط روی متنِ انتخاب‌شده" style={{ fontWeight: 700 }} onMouseDown={(e) => { e.preventDefault(); addMark({ b: true }) }}>B</button>
            <button title="کج" style={{ fontStyle: 'italic' }} onMouseDown={(e) => { e.preventDefault(); addMark({ i: true }) }}>I</button>
            <button title="زیرخط" style={{ textDecoration: 'underline' }} onMouseDown={(e) => { e.preventDefault(); addMark({ u: true }) }}>U</button>
            <button title="کوچک‌تر" onMouseDown={(e) => { e.preventDefault(); addMark({ fs: 0.85 }) }}>A−</button>
            <button title="بزرگ‌تر" onMouseDown={(e) => { e.preventDefault(); addMark({ fs: 1.18 }) }}>A＋</button>
            <button title="فاصلهٔ خطِ کمتر (کلِ این بند)" onMouseDown={(e) => { e.preventDefault(); hostLh(-0.1) }}>خ−</button>
            <button title="فاصلهٔ خطِ بیشتر (کلِ این بند)" onMouseDown={(e) => { e.preventDefault(); hostLh(+0.1) }}>خ＋</button>
            <button title="شماره‌گذاریِ خطوطِ این بند (مثل Word)" onMouseDown={(e) => { e.preventDefault(); hostUpdate({ list: 'num' }); setOlFmt(null) }}>1.</button>
            <button title="بولتِ ابتدای خطوط" onMouseDown={(e) => { e.preventDefault(); hostUpdate({ list: 'bullet' }); setOlFmt(null) }}>•</button>
            <button title="تیکِ ابتدای خطوط" onMouseDown={(e) => { e.preventDefault(); hostUpdate({ list: 'check' }); setOlFmt(null) }}>✓</button>
            <button title="برداشتنِ نشانه‌های لیست" onMouseDown={(e) => { e.preventDefault(); hostUpdate({ list: undefined }); setOlFmt(null) }}>↺</button>
            <button title="پاک‌کردنِ قالبِ این بخش" onMouseDown={(e) => { e.preventDefault(); clearMarksInRange() }}>⌫</button>
            <button title="بستن" onMouseDown={(e) => { e.preventDefault(); setOlFmt(null) }}>×</button>
          </div>
        )}

        {/* ---- floating layout panel (dblclick target), like the letter page's ---- */}
        {olSel && (() => {
          // show the EFFECTIVE value (template base + this account's override);
          // edits always write to the current scope's store
          const b = olEffLayout[olSel.key] || {}
          return (
            <div className="olp-panel" style={{ left: olSel.x, top: olSel.y }} dir="rtl">
              <div className="olp-h" onPointerDown={startPanelDrag} title="برای جابه‌جاییِ پنل بکشید" style={{ cursor: 'move', touchAction: 'none' }}>
                <span title={olSel.label}>چینش — {olSel.label}</span>
                <button className="olp-x" onPointerDown={(e) => e.stopPropagation()} onClick={() => setOlSel(null)}>×</button>
              </div>
              <div className="olp-row">
                <label>اندازهٔ فونت (pt)</label>
                <input type="number" step="0.5" value={b.fs ?? ''} placeholder="—"
                  onChange={(e) => olUpdate({ fs: +e.target.value || undefined })} />
                <button className={b.bold ? 'on' : ''} onClick={() => olUpdate({ bold: !b.bold })}>بولد</button>
              </div>
              <div className="olp-seg" title="چینش">
                {([['right', '≡راست'], ['center', 'وسط'], ['left', 'چپ≡'], ['justify', 'تراز']] as const).map(([a, t]) => (
                  <button key={a} className={b.align === a ? 'on' : ''} onClick={() => olUpdate({ align: a })}>{t}</button>
                ))}
              </div>
              <div className="olp-seg" title="جهتِ نوشتار">
                <button className={b.dir === 'rtl' ? 'on' : ''} onClick={() => olUpdate({ dir: 'rtl' })}>راست‑چپ</button>
                <button className={b.dir === 'ltr' ? 'on' : ''} onClick={() => olUpdate({ dir: 'ltr' })}>چپ‑راست</button>
              </div>
              <div className="olp-row">
                <label>فونت</label>
                <select className="olp-font" value={b.font ?? ''} onChange={(e) => olUpdate({ font: e.target.value || undefined })}>
                  <option value="">پیش‌فرض (EN: Times / FA: B Nazanin)</option>
                  <option value='"B Nazanin", "Times New Roman", serif'>B Nazanin</option>
                  <option value='"Times New Roman", "B Nazanin", serif'>Times New Roman</option>
                  <option value='Arial, "B Nazanin", sans-serif'>Arial</option>
                  <option value='"Traditional Arabic", "Times New Roman", serif'>Traditional Arabic</option>
                  <option value='Georgia, "B Nazanin", serif'>Georgia</option>
                  <option value='Tahoma, "B Nazanin", sans-serif'>Tahoma</option>
                </select>
              </div>
              <div className="olp-seg" title="نشانهٔ ابتدای هر خطِ این بلوک (مثل Word)">
                <button className={!b.list ? 'on' : ''} onClick={() => olUpdate({ list: undefined })}>بدون</button>
                <button className={b.list === 'num' ? 'on' : ''} onClick={() => olUpdate({ list: 'num' })}>1.2.3</button>
                <button className={b.list === 'bullet' ? 'on' : ''} onClick={() => olUpdate({ list: 'bullet' })}>•</button>
                <button className={b.list === 'check' ? 'on' : ''} onClick={() => olUpdate({ list: 'check' })}>✓</button>
                <button className={b.list === 'dash' ? 'on' : ''} onClick={() => olUpdate({ list: 'dash' })}>–</button>
              </div>
              <div className="olp-grid">
                <label>فاصلهٔ خط<input type="number" step="0.1" value={b.lh ?? ''} placeholder="—" onChange={(e) => olUpdate({ lh: +e.target.value || undefined })} /></label>
                <label>فاصلهٔ حروف<input type="number" step="0.5" value={b.ls ?? ''} placeholder="—" onChange={(e) => olUpdate({ ls: +e.target.value || undefined })} /></label>
                <label>جابه‌جایی عمودی<input type="number" value={b.mt ?? ''} placeholder="px" onChange={(e) => olUpdate({ mt: +e.target.value || undefined })} /></label>
                <label>جابه‌جایی افقی<input type="number" value={b.mis ?? ''} placeholder="px" onChange={(e) => olUpdate({ mis: +e.target.value || undefined })} /></label>
                <label>عرض ٪<input type="number" value={b.w ?? ''} placeholder="—" onChange={(e) => olUpdate({ w: +e.target.value || undefined })} /></label>
                <label>X آزاد (px)<input type="number" value={b.dx ?? ''} placeholder="—" onChange={(e) => olUpdate({ dx: e.target.value === '' ? undefined : +e.target.value })} /></label>
                <label>Y آزاد (px)<input type="number" value={b.dy ?? ''} placeholder="—" onChange={(e) => olUpdate({ dy: e.target.value === '' ? undefined : +e.target.value })} /></label>
                <label>چرخش (درجه)<input type="number" step="1" value={b.rot ?? ''} placeholder="0" onChange={(e) => olUpdate({ rot: e.target.value === '' ? undefined : +e.target.value })} /></label>
                <label>عرض (px)<input type="number" value={b.wx ?? ''} placeholder="—" onChange={(e) => olUpdate({ wx: +e.target.value || undefined })} /></label>
              </div>
              <label className="olp-txt">متنِ این عنصر (بازنویسی — فقط بلوکِ متنِ ساده)
                <textarea value={b.txt ?? ''} placeholder="— متنِ اصلی —" dir="auto"
                  onChange={(e) => olUpdate({ txt: e.target.value === '' ? undefined : e.target.value })} />
              </label>
              <div className="olp-actions">
                <button style={b.hide ? undefined : { color: '#dc2626' }}
                  onClick={() => olUpdate({ hide: !b.hide || undefined })}>
                  {b.hide ? 'نمایشِ دوباره' : 'حذف از برگه'}
                </button>
                <button onClick={() => { setOlLayout((s) => { const n = { ...s }; delete n[olSel.key]; return n }) }}>بازنشانیِ این عنصر</button>
                <button onClick={() => { if (confirm(olAcct ? `همهٔ چینش/قالب‌بندیِ سفارشیِ حسابِ ${olAcct} پاک شود؟ (قالبِ اصلی دست نمی‌خورد)` : 'همهٔ چیدمان و قالب‌بندیِ سفارشیِ قالبِ اصلی پاک شود؟')) { setOlLayout({}); setOlMarks({}); setOlSel(null) } }}>بازنشانیِ همه</button>
              </div>
              <div className="olp-hint">
                {olAcct
                  ? <>تغییرها فقط برای حسابِ <b dir="ltr">{olAcct}</b> اعمال و ذخیره می‌شوند؛ قالبِ اصلی تغییری نمی‌کند (با «ذخیره» در پروندهٔ مشتری هم می‌مانند).</>
                  : 'فرم به حسابی تعلق ندارد — این تغییرها قالبِ اصلی (پیش‌فرضِ همهٔ حساب‌ها) را به‌روز می‌کنند.'}
              </div>
            </div>
          )
        })()}
      </div>
    </Layout>
  )
}
