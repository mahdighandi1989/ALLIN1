'use client'

// Offer Letter generator — auto-selects the right template from the customer's
// account_type × facility_type:
//   • retail + loan            → bilingual EN/AR Personal Loan (4 pages)
//   • retail (non-loan) / any corporate → English letter (3 pages)
// English text + the 25 terms are verbatim from the bank's Word templates;
// the bilingual Personal Loan content lives in personalLoanContent.ts (extracted
// verbatim from the bank's bilingual sample). Dynamic values come from the
// customer/facility (editable), and each template prints to clean A4 pages.
import React, { useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Download, Search } from 'lucide-react'
import toast from 'react-hot-toast'
import { customersApi, parseApiError } from '@/lib/api'
import { BANK_LOGO } from '@/app/voucher/logo'
import { PL } from './personalLoanContent'

const today = new Date().toISOString().slice(0, 10)

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
  Prefix: 'M/S.', CompanyName: '', AccountNumber: '', POBox: '', CityCountry: 'DUBAI - U.A.E.',
  RefNumber: '', IssueDate: today, RequestDate: '', ExpiryDate: '12 Months',
  RequiredSecurities: SECURITIES_CORPORATE, Remarks: '', FacilityType: 'Overdraft',
  CreditLimit: '', InterestRate: '', ValidUntil: '', ProcessingFee: '1000',
  AccountSuffix: '', AcceptanceDate: '',
  // Personal-loan fields
  LoanAmount: '', LoanTenor: '', MonthlyInstallment: '', Purpose: 'PERSONAL NEED', SubjectDate: '',
}

const LOAN_TYPES = new Set(['loan'])
const isLoanFac = (ft: string) => LOAN_TYPES.has(String(ft || '').toLowerCase())

export default function OfferLetterPage() {
  const [f, setF] = useState<Fields>(INITIAL)
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)
  const [isCorporate, setIsCorporate] = useState(true)
  const [tpl, setTpl] = useState<'auto' | 'english' | 'personal'>('auto')
  const [autoTpl, setAutoTpl] = useState<'english' | 'personal'>('english')
  const set = (k: string) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const fill = (t: string) => t.replace(/\{(\w+)\}/g, (_, k) => f[k] || '________')

  const effectiveTpl = tpl === 'auto' ? autoTpl : tpl

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d: any = await customersApi.detail(a)
      const c = d.customer || {}
      const profile = d.profile || {}
      const pdata = profile.data || {}
      const facs: any[] = Array.isArray(d.facilities) ? d.facilities : []
      const corp = ['corporate', 'sme'].includes(String(c.account_type || '').toLowerCase())
      const loanFac = facs.find((x) => isLoanFac(x.facility_type))
      const fac = loanFac || facs[0]
      setIsCorporate(corp)
      setAutoTpl(!corp && loanFac ? 'personal' : 'english')
      setF((s) => ({
        ...s,
        Prefix: corp ? 'M/S.' : 'Mr.',
        CompanyName: c.name || s.CompanyName,
        AccountNumber: c.account_no || a,
        POBox: pdata.po_box || pdata.POBox || s.POBox,
        CityCountry: (c.branch ? `${c.branch} - U.A.E.` : s.CityCountry),
        RequiredSecurities: corp ? SECURITIES_CORPORATE : SECURITIES_PERSONAL,
        FacilityType: fac?.facility_type ? facTypeLabel(fac.facility_type) : s.FacilityType,
        CreditLimit: fac?.amount != null ? Number(fac.amount).toLocaleString() + '/-' : s.CreditLimit,
        InterestRate: fac?.interest_rate != null ? `${fac.interest_rate} % p.a.` : s.InterestRate,
        // loan specifics
        LoanAmount: loanFac?.amount != null ? Number(loanFac.amount).toLocaleString() + '/-' : s.LoanAmount,
        LoanTenor: loanFac?.tenor_months ? String(loanFac.tenor_months) : s.LoanTenor,
        MonthlyInstallment: loanFac?.installments || s.MonthlyInstallment,
        AccountSuffix: pdata.suffix || s.AccountSuffix,
      }))
      toast.success(`«${c.name || a}» — ${corp ? 'حقوقی' : 'حقیقی'} · ${facs.length} تسهیلات`)
    } catch (e) { toast.error(parseApiError(e)) }
    finally { setLoading(false) }
  }

  const field = 'w-full border border-gray-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-yellow-50'
  const F = ({ k, label, area }: { k: string; label: string; area?: boolean }) => (
    <label className="block">
      <span className="text-[11px] text-gray-500">{label}</span>
      {area
        ? <textarea value={f[k]} onChange={set(k)} rows={3} className={field + ' font-mono text-xs'} />
        : <input value={f[k]} onChange={set(k)} className={field} />}
    </label>
  )

  const Letterhead = () => (
    <div className="ol-head">
      <div className="ol-head-left">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={BANK_LOGO} alt="Bank Saderat Iran" className="ol-logo" />
        <div>
          <div className="ol-bank">BANK SADERAT IRAN <span style={{ fontWeight: 400, fontSize: '8pt' }}>s.a.e</span></div>
          <div className="ol-bank-sub">U.A.E. &nbsp;|&nbsp; Licensed by the Central Bank of the U.A.E.</div>
          <div className="ol-bank-sub">Credit Facility Department</div>
        </div>
      </div>
      <div className="ol-head-right">
        <div><b>Offer Letter No:</b> {f.RefNumber || '____________'}</div>
        <div><b>Date:</b> {f.IssueDate || '____________'}</div>
      </div>
    </div>
  )
  const FootAddr = ({ p }: { p: string }) => (
    <div className="ol-foot">P.O. Box {f.POBox || '—'}, DUBAI – U.A.E. &nbsp;|&nbsp; SWIFT: BSIRAEAD &nbsp;|&nbsp; Bank Saderat Iran — Credit Facility Department &nbsp;|&nbsp; {p}</div>
  )

  // Bilingual two-column row (EN left / AR right)
  const Bi = ({ en, ar, n }: { en: string; ar: string; n?: number }) => (
    <tr>
      {n != null && <td className="bi-n">{n}</td>}
      <td className="bi-en">{en}</td>
      <td className="bi-ar" dir="rtl">{ar}</td>
    </tr>
  )

  return (
    <Layout>
      <style>{`
        .ol-page { box-sizing: border-box; width: 210mm; min-height: 297mm; background:#fff; margin:0 auto 8mm;
                   padding: 9mm 13mm 13mm; color:#111; font-family: "Times New Roman", Georgia, serif;
                   font-size: 9.3pt; line-height: 1.2; box-shadow: 0 1px 6px rgba(0,0,0,.12); position:relative; }
        .ol-head { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #0a3d91; padding-bottom:2mm; }
        .ol-head-left { display:flex; gap:3mm; align-items:center; }
        .ol-logo { height:14mm; width:auto; object-fit:contain; }
        .ol-bank { font-family: Arial, sans-serif; font-weight:800; color:#0a3d91; font-size:14pt; letter-spacing:.5px; }
        .ol-bank-sub { font-family: Arial, sans-serif; font-size:7pt; color:#444; }
        .ol-head-right { font-family: Arial, sans-serif; font-size:8.5pt; text-align:right; white-space:nowrap; }
        .ol-title { text-align:center; font-weight:800; font-size:13pt; text-decoration:underline; margin:3mm 0 2mm; letter-spacing:1px; }
        .ol-title-ar { text-align:center; font-weight:800; font-size:12pt; margin:-1mm 0 2mm; }
        .ol-rcpt { font-weight:700; }
        .ol-p { margin:1.4mm 0; text-align:justify; }
        .ol-tbl { width:100%; border-collapse:collapse; margin:2.5mm 0; }
        .ol-tbl th, .ol-tbl td { border:1px solid #000; padding:1.2mm 2mm; font-size:9pt; text-align:center; }
        .ol-tbl th { background:#e8eefc; font-family:Arial, sans-serif; }
        .ol-sec { white-space:pre-wrap; font-size:9pt; margin:1mm 0 2mm; }
        .ol-sign { display:flex; justify-content:space-between; margin-top:9mm; font-weight:700; font-size:9pt; }
        .ol-sign span { border-top:1px solid #000; padding-top:1mm; width:70mm; text-align:center; }
        .ol-terms-h { font-weight:800; text-decoration:underline; margin:2.5mm 0 1.5mm; }
        ol.ol-terms { margin:0; padding-left:6mm; } ol.ol-terms li { margin:0.8mm 0; text-align:justify; }
        .ol-foot { position:absolute; bottom:5mm; left:13mm; right:13mm; text-align:center; font-size:7pt; color:#666; font-family:Arial,sans-serif; border-top:1px solid #ccc; padding-top:1mm; }
        .ol-dots { letter-spacing:1px; }
        /* bilingual */
        .bi { width:100%; border-collapse:collapse; margin:2mm 0; }
        .bi td { border:1px solid #000; padding:1.3mm 2mm; vertical-align:top; font-size:8.6pt; }
        .bi .bi-n { width:7mm; text-align:center; font-weight:700; }
        .bi .bi-en { width:48%; text-align:left; }
        .bi .bi-ar { width:48%; text-align:right; font-family:"Traditional Arabic","Times New Roman",serif; font-size:9.5pt; }
        .bi-row2 { display:flex; justify-content:space-between; gap:6mm; margin:1.2mm 0; }
        .bi-row2 .ar { direction:rtl; text-align:right; font-size:10pt; }

        @media print {
          @page { size: A4 portrait; margin: 0; }
          html, body, .min-h-screen { margin:0 !important; padding:0 !important; min-height:0 !important; background:#fff !important; }
          .ol-page { margin:0 !important; box-shadow:none !important; page-break-after: always; }
          .ol-page:last-child { page-break-after: auto; }
          .ol-tbl, .bi, .ol-sign { page-break-inside: avoid; }
          #ol-controls { display:none !important; }
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        {/* ---------------- controls (not printed) ---------------- */}
        <div id="ol-controls" className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="bg-blue-600 text-white rounded-lg p-2"><Printer size={18} /></div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Offer Letter — نامهٔ پیشنهادِ تسهیلات</h1>
              <p className="text-gray-500 text-xs">شماره‌حساب را وارد کن؛ قالب بر اساس نوع حساب×تسهیلات خودکار انتخاب می‌شود (شخصی‌وام → دوزبانه، بقیه → English).</p>
            </div>
          </div>

          <div className="flex flex-wrap items-end gap-2 mb-3 bg-blue-50 border border-blue-100 rounded-lg p-3">
            <label className="flex-1 min-w-[180px]">
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
            <button onClick={() => window.print()} type="button"
              className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-md px-4 py-2 text-sm font-medium">
              <Download size={15} /> Print / PDF
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
            <F k="Prefix" label="Prefix (Mr./Ms./M/S.)" />
            <F k="CompanyName" label="Customer / Company Name" />
            <F k="AccountNumber" label="Account Number" />
            <F k="POBox" label="P.O. Box" />
            <F k="CityCountry" label="City / Country" />
            <F k="RefNumber" label="Offer Letter No" />
            <F k="IssueDate" label="Issue Date" />
            <F k="RequestDate" label="Request Date" />
            <F k="FacilityType" label="Facility Type" />
            <F k="CreditLimit" label="Credit Limit (AED)" />
            <F k="InterestRate" label="Interest Rate" />
            <F k="ValidUntil" label="Valid Until / Expiry" />
            <F k="ProcessingFee" label="Processing Fee (AED)" />
            <F k="AccountSuffix" label="Account Suffix" />
            <F k="AcceptanceDate" label="Acceptance Date" />
            {effectiveTpl === 'personal' && <>
              <F k="SubjectDate" label="Application Date" />
              <F k="LoanAmount" label="Loan Amount (AED)" />
              <F k="LoanTenor" label="Loan Tenor (Months)" />
              <F k="MonthlyInstallment" label="Monthly Installment" />
              <F k="Purpose" label="Purpose" />
            </>}
          </div>
          <div className="grid md:grid-cols-2 gap-2.5 mt-2.5">
            <F k="Remarks" label="Remarks (جدول)" area />
            <F k="RequiredSecurities" label="REQUIRED SECURITIES / DOCUMENTS (English template)" area />
          </div>
        </div>

        {/* ---------------- printable document ---------------- */}
        <div id="offer-print" dir="ltr">
          {effectiveTpl === 'english' ? (
            <>
              {/* ===== ENGLISH PAGE 1 ===== */}
              <div className="ol-page">
                <Letterhead />
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
                <div className="ol-sign">
                  <span>Head of Credit Facility Department</span>
                  <span>Customer Signature with Stamp</span>
                </div>
                <FootAddr p="Page 1 of 3" />
              </div>

              {/* ===== ENGLISH PAGE 2 ===== */}
              <div className="ol-page">
                <Letterhead />
                <div className="ol-terms-h">TERMS AND CONDITIONS:</div>
                <ol className="ol-terms">{TERM_TEXTS.slice(0, 17).map((t, i) => <li key={i}>{fill(t)}</li>)}</ol>
                <div className="ol-sign"><span>&nbsp;</span><span>Customer Signature with Stamp</span></div>
                <FootAddr p="Page 2 of 3" />
              </div>

              {/* ===== ENGLISH PAGE 3 ===== */}
              <div className="ol-page">
                <Letterhead />
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
                <div className="ol-sign" style={{ marginTop: '8mm' }}>
                  <span>Authorized Signature(s)</span>
                  {isCorporate ? <span>Company Stamp</span> : <span>&nbsp;</span>}
                </div>
                <FootAddr p="Page 3 of 3" />
              </div>
            </>
          ) : (
            /* ================= BILINGUAL PERSONAL LOAN ================= */
            <div className="ol-page">
              <Letterhead />
              <div className="bi-row2"><div style={{ fontWeight: 700 }}>{PL.header.confidential.en}</div><div className="ar" style={{ fontWeight: 700 }}>{PL.header.confidential.ar}</div></div>
              <div className="ol-title">{PL.header.title.en}</div>
              <div className="ol-title-ar" dir="rtl">{PL.header.title.ar}</div>
              <div className="ol-rcpt">{f.Prefix !== 'M/S.' ? f.Prefix + ' ' : ''}{f.CompanyName || '________________'}</div>
              <div>P.O. Box: {f.POBox || '______'}</div>
              <div>{f.CityCountry}</div>
              <div className="bi-row2"><div><b>{PL.subject.en}</b> {f.SubjectDate || '__________'}</div><div className="ar"><b>{PL.subject.ar}</b></div></div>
              <div className="bi-row2"><div>{PL.dear.en}</div><div className="ar">{PL.dear.ar}</div></div>
              <div className="ol-p">{PL.intro.en}</div>
              <div className="ol-p ar" dir="rtl" style={{ textAlign: 'right' }}>{PL.intro.ar}</div>

              {/* Details of Loan */}
              <table className="bi"><tbody>
                <tr><td colSpan={3} style={{ background: '#e8eefc', fontWeight: 700, textAlign: 'center' }}>{PL.detailsTitle.en} / {PL.detailsTitle.ar}</td></tr>
                <Bi en={`${PL.labels.accountNumber?.en || 'Account Number'} : ${f.AccountNumber || '—'}`} ar={PL.labels.accountNumber?.ar || ''} />
                <Bi en={`${PL.labels.loanAmount?.en || 'Loan Amount (AED)'} : ${f.LoanAmount || '—'}`} ar={PL.labels.loanAmount?.ar || ''} />
                <Bi en={`${PL.labels.interestRate?.en || 'Interest Rate'} : ${f.InterestRate || '—'}`} ar={PL.labels.interestRate?.ar || ''} />
                <Bi en={`${PL.labels.tenor?.en || 'Loan Tenor (Months)'} : ${f.LoanTenor || '—'}`} ar={PL.labels.tenor?.ar || ''} />
                <Bi en={`${PL.labels.installment?.en || 'Monthly Installment'} : ${f.MonthlyInstallment || '—'}`} ar={PL.labels.installment?.ar || ''} />
                <Bi en={`${PL.labels.purpose?.en || 'Purpose'} : ${f.Purpose || '—'}`} ar={PL.labels.purpose?.ar || ''} />
                <Bi en={`${PL.processingFees.label.en}: ${PL.processingFees.value.en}`} ar={`${PL.processingFees.label.ar} ${PL.processingFees.value.ar}`} />
                <Bi en={`${PL.latePayment.label.en}: ${PL.latePayment.value.en}`} ar={`${PL.latePayment.label.ar} ${PL.latePayment.value.ar}`} />
              </tbody></table>

              {/* Required Security Documents */}
              <table className="bi"><tbody>
                <tr><td colSpan={3} style={{ background: '#e8eefc', fontWeight: 700, textAlign: 'center' }}>{PL.securitiesTitle.en} / {PL.securitiesTitle.ar}</td></tr>
                {PL.securities.map((s, i) => <Bi key={i} n={Number(s.n) || i + 1} en={s.en} ar={s.ar} />)}
              </tbody></table>
              <div className="ol-p" style={{ fontSize: '8pt' }}>{PL.securitiesNote.en} {PL.securitiesNote.ar}</div>

              {/* Terms */}
              <table className="bi"><tbody>
                {PL.terms.map((t, i) => <Bi key={i} n={i + 1} en={t.en} ar={t.ar} />)}
              </tbody></table>

              {/* Bank signature */}
              <div className="bi-row2" style={{ marginTop: '4mm' }}><div>{PL.closing.yoursSincerely.en}</div><div className="ar">{PL.closing.yoursSincerely.ar}</div></div>
              <div className="bi-row2"><div>{PL.closing.forBank.en}</div><div className="ar">{PL.closing.forBank.ar}</div></div>
              <div className="ol-sign"><span>{PL.closing.headDept.en}</span><span dir="rtl">{PL.closing.headDept.ar}</span></div>

              {/* Borrower declaration */}
              <div className="bi-row2" style={{ marginTop: '4mm', fontWeight: 700 }}><div>{PL.closing.borrowerDeclaration.en}</div><div className="ar">{PL.closing.borrowerDeclaration.ar}</div></div>
              <table className="bi"><tbody><Bi en={PL.declaration.en} ar={PL.declaration.ar} /></tbody></table>
              <table className="bi"><tbody>
                <Bi en={`${PL.borrowerSign[0]?.en || 'Borrower Signature'}`} ar={PL.borrowerSign[0]?.ar || ''} />
                <Bi en={`${PL.borrowerSign[1]?.en || 'Borrower Name:'} ${f.CompanyName || ''}`} ar={PL.borrowerSign[1]?.ar || ''} />
                <Bi en={`${PL.borrowerSign[2]?.en || 'Date:'} ${f.AcceptanceDate || ''}`} ar={PL.borrowerSign[2]?.ar || ''} />
              </tbody></table>
              <FootAddr p="Personal Loan" />
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

function facTypeLabel(ft: string): string {
  const m: Record<string, string> = {
    overdraft: 'Overdraft', loan: 'Loan', lc: 'Letter of Credit', lc_sight: 'LC (Sight)',
    lc_usance: 'LC (Usance)', lg: 'Letter of Guarantee', log: 'Letter of Guarantee',
    cheque_discounting: 'Cheque Discounting', trust_receipt: 'Trust Receipt', other: 'Facility',
  }
  return m[String(ft || '').toLowerCase()] || ft || 'Facility'
}
