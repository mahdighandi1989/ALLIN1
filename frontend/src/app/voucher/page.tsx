'use client'

import { useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search } from 'lucide-react'
import { lookupAccount, BRANCHES, ACCOUNT_COUNT } from './accounts'
import { BANK_LOGO } from './logo'

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
}

function Voucher({ kind, title, date, acNo, amount, currency, ourRef, description, acName }: VProps) {
  return (
    <div className="vch" dir="ltr">
      <div className="vch-head">
        <div className="vch-kind">{kind}</div>
        <div className="vch-logo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={BANK_LOGO} alt="Bank Saderat Iran" />
          <div className="vch-iv">INTERNAL VOUCHER</div>
        </div>
      </div>

      <div className="vch-banner">{title}</div>
      <div className="vch-daterow">DATE :&nbsp;&nbsp;{date}</div>

      <div className="vch-acrow">
        <div><span className="vch-aclbl">A/c No. :</span><span className="vch-ac">{acNo}</span></div>
        <div className="vch-amt">{amount ? `${currency} ${money(amount)}` : '**********'}</div>
      </div>

      <div className="vch-ref">
        <div className="vch-ref-lbl">OUR REF :</div>
        <div className="vch-ref-body">
          <div className="vch-ref-no">{ourRef}</div>
          <div className="vch-ref-desc">{description}</div>
          <div className="vch-ref-name">{acName}</div>
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

  const onAcctLookup = (value: string) => {
    setAcNo(value)
    const hit = lookupAccount(value)
    if (hit) { setAcName(hit.name); setBranch(hit.branch); setNotFound(false) }
    else setNotFound(value.trim().length > 0)
  }

  const nameOnCheque = nameType === 'Borrower Name' ? acName : guarantorName
  const debitGL = branch ? `${branch}-860185-784-090` : ''
  const creditGL = branch ? `${branch}-869900-784-590` : ''
  const ourRef = useMemo(() => [acNo, facilityId].filter(Boolean).join(' _ '), [acNo, facilityId])
  const description = `CHQ NO ${chqNo}_${nameType}: ${nameOnCheque}`
  const field = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

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

        /* on-screen preview width */
        #voucher-print { width: 190mm; margin: 0 auto; background: #fff; }

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
          #voucher-print { width: 188mm !important; margin: 8mm 11mm 0 11mm !important;
                           page-break-inside: avoid; break-inside: avoid; }
          .vch { page-break-inside: avoid; break-inside: avoid; }
        }
      `}</style>

      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-1 no-print">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><Printer size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">سند انتظامی چک ضمانتی (Securities / Per‑Contra)</h1>
            <p className="text-gray-500 text-sm">با وارد کردن چند مقدار، نام از دیتابیس ({ACCOUNT_COUNT} حساب) پر می‌شود. دو سند روی یک A4 — با نصف‌کردن، هر کدام یک A5.</p>
          </div>
        </div>

        <div className="voucher-grid grid lg:grid-cols-2 gap-6 items-start mt-4">
          {/* ---- inputs (not printed) ---- */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 no-print" dir="rtl">
            <h2 className="font-bold text-gray-800 mb-4">ورودی‌ها</h2>
            <div className="grid grid-cols-2 gap-3">
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">شماره حساب (A/C NO)</span>
                <div className="relative">
                  <input className={field} value={acNo} onChange={(e) => onAcctLookup(e.target.value)} placeholder="مثلاً 271520" inputMode="numeric" />
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                </div>
                {notFound && <span className="text-amber-600 text-xs">در دیتابیس یافت نشد؛ نام را دستی وارد کنید.</span>}
              </label>
              <label className="col-span-2 text-sm">
                <span className="text-gray-600">نام حساب (A/C NAME)</span>
                <input className={field} value={acName} onChange={(e) => setAcName(e.target.value)} placeholder="از روی شماره حساب پر می‌شود" />
              </label>
              <label className="text-sm">
                <span className="text-gray-600">شعبه (BRANCH)</span>
                <input className={field} value={branch} onChange={(e) => setBranch(e.target.value)} list="branches" placeholder="مثلاً 2776" />
                <datalist id="branches">{BRANCHES.map((b) => <option key={b} value={b} />)}</datalist>
              </label>
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
                  <input className={field} value={guarantorName} onChange={(e) => setGuarantorName(e.target.value)} />
                </label>
              )}
              <label className="text-sm">
                <span className="text-gray-600">شماره چک (CHQ NO)</span>
                <input className={field} value={chqNo} onChange={(e) => setChqNo(e.target.value)} inputMode="numeric" />
              </label>
              <label className="text-sm">
                <span className="text-gray-600">مبلغ چک (CHQ AMOUNT)</span>
                <input className={field} value={chqAmount} onChange={(e) => setChqAmount(e.target.value)} inputMode="numeric" placeholder="144000" />
              </label>
              <label className="text-sm">
                <span className="text-gray-600">شناسه تسهیلات (FACILITY ID)</span>
                <input className={field} value={facilityId} onChange={(e) => setFacilityId(e.target.value)} placeholder="STF1260603000001" />
              </label>
              <label className="text-sm">
                <span className="text-gray-600">ارز / تاریخ</span>
                <div className="flex gap-2">
                  <input className={field} value={currency} onChange={(e) => setCurrency(e.target.value)} />
                  <input className={field} value={date} onChange={(e) => setDate(e.target.value)} />
                </div>
              </label>
            </div>
            <button onClick={() => window.print()} type="button"
              className="mt-5 w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-2.5">
              <Printer size={18} /> چاپ (Print)
            </button>
            <p className="text-xs text-gray-400 mt-2 text-center">در پنجرهٔ چاپ، Scale را روی «Default / 100%» و Margins را «Default» بگذارید تا دقیق فیت شود.</p>
          </div>

          {/* ---- printable vouchers (A4 = two A5 halves) ---- */}
          <div id="voucher-print">
            <Voucher kind="DEBIT" title="SECURITIES" date={date} acNo={debitGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} />
            <Voucher kind="CREDIT" title="PER CONTRA" date={date} acNo={creditGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} />
          </div>
        </div>
      </div>
    </Layout>
  )
}
