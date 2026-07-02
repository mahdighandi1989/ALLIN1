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
import { crmApi, parseApiError } from '@/lib/api'
import { BANK_LOGO } from '@/app/voucher/logo'
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

type Fields = Record<string, string>
const INITIAL: Fields = {
  Prefix: 'M/S.', CompanyName: '', CompanyNameAr: '', AccountNumber: '', POBox: '', CityCountry: 'DUBAI - U.A.E.',
  Branch: '', RefSerial: '', RefYear: THIS_YEAR, IssueDate: today, RequestDate: '', ExpiryDate: '12 Months',
  RequiredSecurities: SECURITIES_CORPORATE, Remarks: '', FacilityType: 'Overdraft',
  CreditLimit: '', InterestRate: '', ValidUntil: '', ProcessingFee: '1000',
  AccountSuffix: '', AcceptanceDate: '',
  // Personal-loan fields
  LoanAmount: '', LoanInterestRate: '', LoanTenor: '', MonthlyInstallment: '', Purpose: 'PERSONAL NEED', SubjectDate: '',
  LienAmount: '',
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

export default function OfferLetterPage() {
  const [f, setF] = useState<Fields>(INITIAL)
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isCorporate, setIsCorporate] = useState(true)
  const [tpl, setTpl] = useState<'auto' | 'english' | 'personal'>('auto')
  const [extracting, setExtracting] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  // Required-document checkboxes (bilingual form). Default: all ticked.
  const [checks, setChecks] = useState<boolean[]>(() => PL.securities.map(() => true))
  const set = (k: string) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const fill = (t: string) => t.replace(/\{(\w+)\}/g, (_, k) => f[k] || '________')
  const toggleCheck = (i: number) => setChecks((c) => c.map((v, idx) => (idx === i ? !v : v)))

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
        FacilityType: saved.FacilityType || d.FacilityType || s.FacilityType,
        CreditLimit: saved.CreditLimit || withSlash(d.CreditLimit) || s.CreditLimit,
        InterestRate: saved.InterestRate || d.InterestRate || s.InterestRate,
        ValidUntil: saved.ValidUntil || d.ValidUntil || s.ValidUntil,
        RequiredSecurities: saved.RequiredSecurities || (corp ? SECURITIES_CORPORATE : SECURITIES_PERSONAL),
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
      }))
      setChecks(
        Array.isArray(saved.securitiesChecked) && saved.securitiesChecked.length === PL.securities.length
          ? saved.securitiesChecked
          : PL.securities.map(() => true)
      )
      if (saved.tpl === 'english' || saved.tpl === 'personal' || saved.tpl === 'auto') setTpl(saved.tpl)
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
      await crmApi.saveOfferLetterData(a, {
        POBox: f.POBox, CityCountry: f.CityCountry, Salutation: f.Prefix, Branch: f.Branch,
        snapshot: { ...f, RefNumber: refNumber, securitiesChecked: checks, tpl },
      })
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

  const field = 'w-full border border-gray-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-yellow-50'
  // F is a render *function* (not a nested component) so inputs keep focus while typing.
  const F = (k: string, label: string, area?: boolean) => (
    <label className="block">
      <span className="text-[11px] text-gray-500">{label}</span>
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
        <div className="ol-head-left">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={BANK_LOGO} alt="Bank Saderat Iran" className="ol-logo" />
          <div className="ol-ro">
            <div className="ol-ro-ar" dir="rtl">المكتب الاقليمي</div>
            <div className="ol-ro-en">REGIONAL OFFICE</div>
          </div>
        </div>
        <div className="ol-head-right ol-head-right--en">
          <div className="ol-bank-ar" dir="rtl">بنك صادرات ايـران إ.ع.م.</div>
          <div className="ol-bank-en">BANK SADERAT IRAN <span className="ol-uae">U.A.E</span></div>
          <div className="ol-lic">&quot;Licensed by CBUAE&quot;</div>
          <div className="ol-refblock">
            <div className="ol-refline">REF: {refNumber}</div>
            <div className="ol-refline">DATE: {f.IssueDate || '____________'}</div>
          </div>
        </div>
      </div>
    ) : (
      <div className="ol-head ol-head--bi">
        <div className="ol-head-left">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={BANK_LOGO} alt="Bank Saderat Iran" className="ol-logo" />
          <div>
            <div className="ol-bank-ar" dir="rtl">بنك صادرات ايـران إ.ع.م.</div>
            <div className="ol-bank-en">BANK SADERAT IRAN <span className="ol-uae">s.a.e</span></div>
            <div className="ol-lic-bi">Licensed by the Central Bank of the U.A.E</div>
          </div>
        </div>
        <div className="ol-head-right ol-head-right--bi">
          <div className="ol-bsi">BSI-ROL-V002-2024</div>
          <table className="ol-hdr-tbl"><tbody>
            <tr><td className="hdr-en">Date</td><td className="hdr-v">{f.IssueDate || '—'}</td><td className="hdr-ar" dir="rtl">التاريخ</td></tr>
            <tr><td className="hdr-en">Branch Name &amp; Code</td><td className="hdr-v">{f.Branch || '—'}</td><td className="hdr-ar" dir="rtl">اسم و رقم الفرع</td></tr>
            <tr><td className="hdr-en">Offer Letter Ref #</td><td className="hdr-v">{refNumber}</td><td className="hdr-ar" dir="rtl">رقم اشعار القرض</td></tr>
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
          <div className="ol-foot-ar" dir="rtl">{FOOT_AR}</div>
          <div className="ol-foot-en">{FOOT_EN}</div>
          <div className="ol-foot-swift">{FOOT_SWIFT}</div>
        </div>
      </div>
    ) : (
      <div className="ol-foot ol-foot--bi">Page {n} of {total}</div>
    )

  // Bilingual EN/AR side-by-side line.
  const Row2 = ({ en, ar, bold }: { en: string; ar: string; bold?: boolean }) => (
    <div className="bi-row2" style={bold ? { fontWeight: 700 } : undefined}><div>{en}</div><div className="ar" dir="rtl">{ar}</div></div>
  )

  return (
    <Layout>
      <style>{`
        .ol-page { box-sizing: border-box; width: 210mm; min-height: 297mm; background:#fff; margin:0 auto 8mm;
                   padding: 9mm 13mm 13mm; color:#111; font-family: "Times New Roman", Georgia, serif;
                   font-size: 9.3pt; line-height: 1.2; box-shadow: 0 1px 6px rgba(0,0,0,.12); position:relative; }
        .ol-fit { transform-origin: top left; display:flex; flex-direction:column; min-height:255mm; }
        .ol-head { display:flex; justify-content:space-between; align-items:flex-start; padding-bottom:2mm; }
        .ol-head--en { margin-bottom:4mm; align-items:center; }
        .ol-head-left { display:flex; gap:3mm; align-items:center; }
        .ol-logo { height:12mm; width:auto; object-fit:contain; }
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
        .ol-terms-h { font-weight:800; text-decoration:underline; margin:2.5mm 0 1.5mm; }
        ol.ol-terms { margin:0; padding-left:6mm; } ol.ol-terms li { margin:0.8mm 0; text-align:justify; }
        .ol-foot { position:absolute; bottom:5mm; left:13mm; right:13mm; border-top:0.8px solid #555; padding-top:1.2mm; }
        .ol-foot--en { display:flex; align-items:flex-end; gap:4mm; }
        .ol-foot-pg { font-family:Georgia,serif; font-size:9pt; white-space:nowrap; }
        .ol-foot-addr { flex:1; text-align:center; line-height:1.25; }
        .ol-foot-ar { font-size:8pt; color:#111; }
        .ol-foot-en { font-style:italic; font-size:8pt; color:#111; }
        .ol-foot-swift { font-style:italic; font-size:8pt; color:#111; }
        .ol-foot--bi { text-align:right; font-family:Arial, sans-serif; font-weight:700; font-size:8.5pt; bottom:7mm; }
        /* bilingual pages are framed by a full-page border, like the scanned form */
        .ol-page--bordered::before { content:''; position:absolute; top:5mm; left:6mm; right:6mm; bottom:5mm; border:1px solid #111; pointer-events:none; }
        .ol-dots { letter-spacing:1px; }
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
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        {/* ---------------- controls (not printed) ---------------- */}
        <div id="ol-controls" className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-blue-600 text-white rounded-lg p-2"><Printer size={18} /></div>
            <div>
              <h1 className="text-lg font-bold text-gray-900" dir="rtl">Offer Letter — نامهٔ پیشنهادِ تسهیلات</h1>
              <p className="text-gray-500 text-xs" dir="rtl">شماره‌حساب را وارد کن؛ قالب بر اساس نوع حساب×تسهیلات خودکار انتخاب می‌شود (شخصی‌وام → دوزبانه، بقیه → English). داده‌ها از پروندهٔ مشتری خوانده و هنگام ذخیره/چاپ به آن برمی‌گردد.</p>
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
              <select value={tpl} onChange={(e) => setTpl(e.target.value as any)} className="border border-gray-300 rounded-md px-3 py-2 text-sm">
                <option value="auto">خودکار ({autoTpl === 'personal' ? 'Personal Loan' : 'English'})</option>
                <option value="english">English (3p)</option>
                <option value="personal">Personal Loan دوزبانه (4p)</option>
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

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            {F('Prefix', 'Prefix / عنوان (Mr./Ms./M/S.)')}
            {F('CompanyName', 'Customer / Company Name')}
            {F('AccountNumber', 'Account Number')}
            {F('POBox', 'P.O. Box')}
            {F('CityCountry', 'City / Country')}
            <label className="block">
              <span className="text-[11px] text-gray-500">Branch Name &amp; Code</span>
              <select value={f.Branch} onChange={set('Branch')} className={field}>
                <option value="">—</option>
                {BRANCH_OPTIONS.map((b) => <option key={b} value={b}>{b}</option>)}
                {f.Branch && !BRANCH_OPTIONS.includes(f.Branch) && <option value={f.Branch}>{f.Branch}</option>}
              </select>
            </label>
            <label className="block">
              <span className="text-[11px] text-gray-500">Ref Serial (شمارهٔ متغیر)</span>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400">182/4/</span>
                <input value={f.RefSerial} onChange={set('RefSerial')} className={field} placeholder="202" />
                <span className="text-xs text-gray-400">/</span>
                <input value={f.RefYear} onChange={set('RefYear')} className={field + ' w-16'} />
              </div>
            </label>
            {F('IssueDate', 'Issue Date')}
            {F('FacilityType', 'Facility Type')}
            {F('CreditLimit', 'Credit Limit (AED)')}
            {F('InterestRate', 'Interest Rate')}
            {F('ValidUntil', 'Valid Until / Expiry')}
            {F('ProcessingFee', 'Processing Fee (AED)')}
            {F('AccountSuffix', 'Account Suffix')}
            {F('AcceptanceDate', 'Acceptance / Borrower Date')}
            {effectiveTpl === 'personal' && <>
              {F('SubjectDate', 'Application Date')}
              {F('LoanAmount', 'Loan Amount (AED)')}
              {F('LoanInterestRate', 'Loan Interest Rate')}
              {F('LoanTenor', 'Loan Tenor (Months)')}
              {F('MonthlyInstallment', 'Monthly Installment')}
              {F('Purpose', 'Purpose')}
              {F('LienAmount', 'Lien Amount (AED) — مبلغ وثیقهٔ توديع')}
            </>}
          </div>
          <div className="grid md:grid-cols-2 gap-2.5 mt-2.5">
            {F('Remarks', 'Remarks (جدول)', true)}
            {effectiveTpl === 'english' && F('RequiredSecurities', 'REQUIRED SECURITIES / DOCUMENTS (English template)', true)}
          </div>
        </div>

        {/* ---------------- printable document ---------------- */}
        <div id="offer-print" dir="ltr" ref={printRef}>
          {effectiveTpl === 'english' ? (
            <>
              {/* ===== ENGLISH PAGE 1 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <div className="ol-title">OFFER LETTER</div>
                  <div className="ol-rcpt">{f.Prefix} {f.CompanyName || '________________'}</div>
                  <div className="ol-rcpt">ACCOUNT NO: {f.AccountNumber || '____________'}</div>
                  <div>P.O. Box {f.POBox || '______'}</div>
                  <div>{f.CityCountry}</div>
                  <div className="ol-p" style={{ fontWeight: 700 }}>Private &amp; Confidential</div>
                  <div className="ol-p">Dear Sir,</div>
                  <div className="ol-p">With reference to your request via letter Dated: {f.RequestDate || '____________'}, we are pleased to inform you that the below mentioned {f.FacilityType || 'Overdraft'} facility is approved/renewed{f.ValidUntil ? ` for a period expiring on ${f.ValidUntil}` : ''} subject to the terms and conditions set out in this offer letter which forms an integral part of it and its provision:</div>
                  <table className="ol-tbl">
                    <thead><tr><th>Facility</th><th>Credit Limit (AED)</th><th>Interest Rate</th><th>Remarks</th></tr></thead>
                    <tbody><tr>
                      <td>{f.FacilityType || '—'}</td>
                      <td>{f.CreditLimit || '—'}</td>
                      <td style={{ whiteSpace: 'pre-wrap' }}>{f.InterestRate || '—'}</td>
                      <td style={{ whiteSpace: 'pre-wrap', textAlign: 'left' }}>{f.Remarks || '—'}</td>
                    </tr></tbody>
                  </table>
                  <div className="ol-terms-h">REQUIRED SECURITIES / DOCUMENTS</div>
                  <div className="ol-sec">{f.RequiredSecurities}</div>
                  <div className="ol-sign" style={{ marginTop: 'auto' }}>
                    <span>Head of Credit Facility Department</span>
                    <span>Customer Signature with Stamp</span>
                  </div>
                </div>
                <PageFooter mode="english" n={1} total={3} />
              </div>

              {/* ===== ENGLISH PAGE 2 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <div className="ol-terms-h">TERMS AND CONDITIONS:</div>
                  <ol className="ol-terms">{TERM_TEXTS.slice(0, 17).map((t, i) => <li key={i}>{fill(t)}</li>)}</ol>
                  <div className="ol-sign" style={{ marginTop: 'auto' }}><span>&nbsp;</span><span>Customer Signature with Stamp</span></div>
                </div>
                <PageFooter mode="english" n={2} total={3} />
              </div>

              {/* ===== ENGLISH PAGE 3 ===== */}
              <div className="ol-page">
                <div className="ol-fit">
                  <Letterhead mode="english" />
                  <ol className="ol-terms" start={18}>{TERM_TEXTS.slice(17).map((t, i) => <li key={i}>{fill(t)}</li>)}</ol>
                  <div className="ol-p">Please read the content of this letter and if you agree kindly sign the original copy and return it to us as confirmation for our records not later than one month from the date of this letter; if not accepted it will be deemed to have lapsed.</div>
                  <div className="ol-p">We trust that you will find the above limits and its terms to your satisfaction and will utilize the same for our mutual benefits. While assuring you of our best service at all times, we appreciate your kind co-operation and prompt reply.</div>
                  <div className="ol-p" style={{ marginTop: '4mm' }}>Yours truly,</div>
                  <div style={{ fontWeight: 700 }}>Bank Saderat Iran</div>
                  <div>Credit Facility Department</div>
                  <div className="ol-sign"><span>Manager Signature &amp; Stamp</span><span>&nbsp;</span></div>
                  <div className="ol-dots" style={{ marginTop: '6mm' }}>....................................................................................................................................</div>
                  <div className="ol-p">I read all pages of offer letter and I agreed with the terms and conditions mentioned thereof.</div>
                  <div className="ol-p">Encl: Duplicate of this letter accepted and agreed by</div>
                  <div>{isCorporate ? 'M/s' : 'Mr.'}: {f.CompanyName || '..............................................................'}</div>
                  <div>Date: {f.AcceptanceDate || '............................'}</div>
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
                  <div className="ol-rcpt">{f.Prefix !== 'M/S.' ? f.Prefix + ' ' : ''}{f.CompanyName || '________________'}</div>
                  <div>P.O. Box: {f.POBox || '______'}</div>
                  <div>{f.CityCountry}</div>
                  <Row2 en={`Subject: Personal Loan Application dated: ${f.SubjectDate || '__________'}`} ar={'الموضوع: طلب القرض الشخصي المؤرخ'} bold />
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
                      <td className="pl-val">{f.LoanAmount || '—'}{f.LoanAmount && <span className="pl-tick">✓</span>}</td>
                      <td className="pl-lbl"><div>{PL.labels.interestRate.en}</div><div className="ar" dir="rtl">{PL.labels.interestRate.ar}</div></td>
                      <td className="pl-val">{f.LoanInterestRate || f.InterestRate || '—'}</td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.tenor.en}</div><div className="ar" dir="rtl">{PL.labels.tenor.ar}</div></td>
                      <td className="pl-val">{f.LoanTenor || '—'}{f.LoanTenor && <span className="pl-tick">✓</span>}</td>
                      <td className="pl-lbl"><div>{PL.labels.installment.en}</div><div className="ar" dir="rtl">{PL.labels.installment.ar}</div></td>
                      <td className="pl-val">{f.MonthlyInstallment || '—'}</td>
                    </tr>
                    <tr>
                      <td className="pl-lbl"><div>{PL.labels.purpose.en}</div><div className="ar" dir="rtl">{PL.labels.purpose.ar}</div></td>
                      <td className="pl-val" colSpan={3}>{f.Purpose || '—'}</td>
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
                        <td className="pl-val">{s.en.replace('250,000', f.LienAmount || '________')}</td>
                        <td className="pl-val pl-ar" dir="rtl">{s.ar.replace('250,000', f.LienAmount || '________')}</td>
                      </tr>
                    ))}
                  </tbody></table>
                  <div className="pl-note">{PL.securitiesNote.en}</div>
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

              {/* ===== BILINGUAL PAGE 3 — terms 8–13 + bank signature ===== */}
              <div className="ol-page ol-page--bordered">
                <div className="ol-fit">
                  <Letterhead mode="bilingual" />
                  <table className="pl-tbl"><tbody>
                    {PL.terms.slice(7, 12).map((t, i) => (
                      <tr key={i}><td className="pl-num">{i + 8}</td><td className="pl-val">{t.en}</td><td className="pl-val pl-ar" dir="rtl">{t.ar}</td></tr>
                    ))}
                  </tbody></table>
                  <div className="pl-close"><div>{PL.terms[12].en}</div><div className="ar" dir="rtl">{PL.terms[12].ar}</div></div>
                  <Row2 en={PL.closing.yoursSincerely.en} ar={PL.closing.yoursSincerely.ar} />
                  <Row2 en={PL.closing.forBank.en} ar={PL.closing.forBank.ar} />
                  <div className="ol-sign" style={{ marginTop: 'auto' }}>
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
                  <table className="pl-tbl" style={{ marginTop: 'auto' }}><tbody>
                    <tr><td className="pl-lbl">{PL.borrowerSign[0].en}</td><td className="pl-val">&nbsp;</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[0].ar}</td></tr>
                    <tr><td className="pl-lbl">{PL.borrowerSign[1].en}</td><td className="pl-val">{f.CompanyName}</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[1].ar}</td></tr>
                    <tr><td className="pl-lbl">{PL.borrowerSign[2].en}</td><td className="pl-val">{f.AcceptanceDate}</td><td className="pl-lbl pl-ar" dir="rtl">{PL.borrowerSign[2].ar}</td></tr>
                  </tbody></table>
                </div>
                <PageFooter mode="bilingual" n={4} total={4} />
              </div>
            </>
          )}
        </div>
      </div>
    </Layout>
  )
}
