'use client'

import { useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search } from 'lucide-react'
import { lookupAccount, BRANCHES, ACCOUNT_COUNT } from './accounts'

// Faithful re-implementation of the macro workbook
// "Securities (Contra-PerContra) (FOR CHQS)". The user types a few fields; the
// account name is looked up from the embedded 601-row database; the GL accounts,
// reference and description are computed; pressing Print sends the two internal
// vouchers (SECURITIES debit + PER CONTRA credit) to the default printer.
//
// GL logic (from the workbook):
//   DEBIT  (SECURITIES) = <branch>-860185-784-090
//   CREDIT (PER CONTRA) = <branch>-869900-784-590
//   OUR REF             = <account no> _ <facility id>
//   DESCRIPTION         = CHQ NO <chq no>_<Borrower|Guarantor Name>: <name>

function todayDMY(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()}`
}

function money(n: string): string {
  const v = Number(String(n).replace(/,/g, ''))
  return isFinite(v) && v !== 0 ? v.toLocaleString('en-US') : ''
}

type VoucherProps = {
  title: string
  date: string
  acNo: string
  amount: string
  currency: string
  ourRef: string
  description: string
  acName: string
}

function Voucher({ title, date, acNo, amount, currency, ourRef, description, acName }: VoucherProps) {
  return (
    <div className="voucher" dir="ltr">
      <div className="v-top">
        <div className="v-bank">Bank Saderat Iran — R.O.</div>
        <div className="v-iv">INTERNAL VOUCHER</div>
      </div>
      <div className="v-banner">{title}</div>
      <table className="v-grid">
        <tbody>
          <tr>
            <td className="v-lbl">DATE :</td>
            <td className="v-val">{date}</td>
            <td className="v-lbl">AMOUNT :</td>
            <td className="v-val v-amt">{currency} {money(amount)}</td>
          </tr>
          <tr>
            <td className="v-lbl">A/c No. :</td>
            <td className="v-val" colSpan={3}>{acNo}</td>
          </tr>
          <tr>
            <td className="v-lbl">OUR REF :</td>
            <td className="v-val" colSpan={3}>{ourRef}</td>
          </tr>
          <tr>
            <td className="v-lbl">DESC. :</td>
            <td className="v-val" colSpan={3}>{description}</td>
          </tr>
          <tr>
            <td className="v-lbl">A/c Name :</td>
            <td className="v-val" colSpan={3}>{acName}</td>
          </tr>
        </tbody>
      </table>
      <div className="v-sign">
        <div>Prepared By.<br /><span className="v-line" /></div>
        <div>Authorized Signatures<br /><span className="v-line" /></div>
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
    if (hit) {
      setAcName(hit.name)
      setBranch(hit.branch)
      setNotFound(false)
    } else {
      setNotFound(value.trim().length > 0)
    }
  }

  const nameOnCheque = nameType === 'Borrower Name' ? acName : guarantorName
  const debitGL = branch ? `${branch}-860185-784-090` : ''
  const creditGL = branch ? `${branch}-869900-784-590` : ''
  const ourRef = useMemo(() => [acNo, facilityId].filter(Boolean).join(' _ '), [acNo, facilityId])
  const description = `CHQ NO ${chqNo}_${nameType}: ${nameOnCheque}`

  const field = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      {/* Print rules: hide everything except #voucher-print when printing. */}
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          #voucher-print, #voucher-print * { visibility: visible !important; }
          #voucher-print { position: absolute; top: 0; left: 0; width: 100%; }
          @page { size: A4 portrait; margin: 14mm; }
        }
        .voucher { border: 1.5px solid #111; padding: 14px 16px; margin-bottom: 22px; font-family: Arial, sans-serif; color:#111; }
        .v-top { display:flex; justify-content:space-between; align-items:flex-start; }
        .v-bank { font-size: 12px; font-weight:600; }
        .v-iv { font-size: 12px; font-weight:700; border:1px solid #111; padding:2px 8px; }
        .v-banner { text-align:center; font-size:18px; font-weight:800; letter-spacing:2px; margin:10px 0 12px; }
        .v-grid { width:100%; border-collapse:collapse; font-size:13px; }
        .v-grid td { padding:6px 6px; border-bottom:1px dotted #999; vertical-align:top; }
        .v-lbl { width:90px; font-weight:700; white-space:nowrap; }
        .v-val { font-weight:500; }
        .v-amt { font-weight:800; }
        .v-sign { display:flex; justify-content:space-between; margin-top:30px; font-size:12px; font-weight:600; }
        .v-line { display:block; width:170px; border-top:1px solid #111; margin-top:34px; }
      `}</style>

      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><Printer size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">سند انتظامی چک ضمانتی (Securities / Per‑Contra)</h1>
            <p className="text-gray-500 text-sm">با وارد کردن چند مقدار، نامِ حساب از دیتابیس ({ACCOUNT_COUNT} حساب) پر می‌شود و دو واچر چاپ می‌شود.</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6 items-start mt-4">
          {/* ---- Input form (not printed) ---- */}
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
            <button
              onClick={() => window.print()}
              className="mt-5 w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg py-2.5"
              type="button"
            >
              <Printer size={18} /> چاپ (Print)
            </button>
            <p className="text-xs text-gray-400 mt-2 text-center">پنجرهٔ چاپ باز می‌شود؛ پرینتر پیش‌فرض از قبل انتخاب شده — کافیست Print را بزنید.</p>
          </div>

          {/* ---- Printable vouchers ---- */}
          <div id="voucher-print">
            <Voucher title="SECURITIES" date={date} acNo={debitGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} />
            <Voucher title="PER CONTRA" date={date} acNo={creditGL} amount={chqAmount} currency={currency} ourRef={ourRef} description={description} acName={acName} />
          </div>
        </div>
      </div>
    </Layout>
  )
}
