'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search } from 'lucide-react'
import { crmApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'

type FormData = {
  date: string
  branchName: string
  branchCode: string
  customerName: string
  accountNumber: string
  rating: string
  previousFiles: string
  passportNum: string
  passportIssue: string
  passportExpiry: string
  emiratesIdNum: string
  emiratesIdIssue: string
  emiratesIdExpiry: string
  overdraftApprovalDate: string
  overdraftAmount: string
  overdraftRate: string
  overdraftInstalments: string
  overdraftMaturity: string
  personalLoanApprovalDate: string
  personalLoanAmount: string
  personalLoanRate: string
  personalLoanInstalments: string
  personalLoanMaturity: string
  staffLoanApprovalDate: string
  staffLoanAmount: string
  staffLoanRate: string
  staffLoanInstalments: string
  staffLoanMaturity: string
  underlienAED: string
  underlienUSD: string
  underlienIRR: string
  underlienOther: string
  chequesAED: string
  chequesUSD: string
  chequesIRR: string
  chequesOther: string
  collateralsAED: string
  collateralsUSD: string
  collateralsIRR: string
  collateralsOther: string
  guarantor1Name: string
  guarantor2Name: string
  customerStatus: string
  preparedBy: string
}

const INITIAL: FormData = {
  date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }),
  branchName: '',
  branchCode: '',
  customerName: '',
  accountNumber: '',
  rating: '',
  previousFiles: '',
  passportNum: '',
  passportIssue: '',
  passportExpiry: '',
  emiratesIdNum: '',
  emiratesIdIssue: '',
  emiratesIdExpiry: '',
  overdraftApprovalDate: '',
  overdraftAmount: '',
  overdraftRate: '',
  overdraftInstalments: '',
  overdraftMaturity: '',
  personalLoanApprovalDate: '',
  personalLoanAmount: '',
  personalLoanRate: '',
  personalLoanInstalments: '',
  personalLoanMaturity: '',
  staffLoanApprovalDate: '',
  staffLoanAmount: '',
  staffLoanRate: '',
  staffLoanInstalments: '',
  staffLoanMaturity: '',
  underlienAED: '',
  underlienUSD: '',
  underlienIRR: '',
  underlienOther: '',
  chequesAED: '',
  chequesUSD: '',
  chequesIRR: '',
  chequesOther: '',
  collateralsAED: '',
  collateralsUSD: '',
  collateralsIRR: '',
  collateralsOther: '',
  guarantor1Name: '',
  guarantor2Name: '',
  customerStatus: 'ACTIVE CUSTOMER',
  preparedBy: '',
}

export default function CreditFileRetailPage() {
  const [data, setData] = useState<FormData>(INITIAL)
  const [acc, setAcc] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key: keyof FormData) => (e: any) => {
    setData((s) => ({ ...s, [key]: e.target.value }))
  }

  const loadAccount = async () => {
    const a = acc.trim()
    if (!a) { toast.error('شماره حساب را وارد کنید'); return }
    setLoading(true)
    try {
      const d = await crmApi.detail(a)
      const { customer, profile = {}, facilities = [], guarantors = [] } = d
      const pdata = (profile.data || {})

      setData((s) => ({
        ...s,
        accountNumber: a,
        customerName: customer?.name || '',
        branchCode: customer?.branch_code || '',
        branchName: customer?.branch || '',
        rating: profile?.rating || '',
        previousFiles: '',
      }))
      toast.success(`بارگیری داده‌های حساب «${customer?.name}»`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  const field = 'w-full border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500'
  const label = 'text-xs font-semibold text-gray-700'

  return (
    <Layout>
      <style>{`
        #credit-file-retail { max-width: 1000px; margin: 0 auto; }
        .cf-form-section { background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; padding: 12px; margin-bottom: 12px; }
        .cf-form-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 8px; border-bottom: 2px solid #2563eb; padding-bottom: 4px; }
        .cf-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; }
        .cf-field { display: flex; flex-direction: column; gap: 2px; }
        .cf-field input { width: 100%; border: 1px solid #ccc; border-radius: 3px; padding: 4px 6px; font-size: 12px; }
        .cf-field input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1); }
        .cf-table { width: 100%; border-collapse: collapse; font-size: 12px; margin: 8px 0; }
        .cf-table th { background: #e5e7eb; font-weight: 600; padding: 6px; text-align: left; border: 1px solid #999; }
        .cf-table td { padding: 4px 6px; border: 1px solid #999; }
        .cf-table input { width: 100%; border: none; padding: 2px; font-size: 11px; }
        .cf-actions { display: flex; gap: 8px; margin-bottom: 16px; }
        .cf-btn { padding: 8px 16px; border-radius: 4px; font-weight: 600; cursor: pointer; border: none; display: flex; align-items: center; gap: 6px; }
        .cf-btn-primary { background: #2563eb; color: white; }
        .cf-btn-primary:hover { background: #1d4ed8; }
        .cf-btn-print { background: #16a34a; color: white; }
        .cf-btn-print:hover { background: #15803d; }

        @media print {
          @page { size: A4 portrait; margin: 10mm; }
          html, body { margin: 0; padding: 0; }
          .no-print { display: none !important; }
          .cf-actions, #account-lookup { display: none !important; }
          .cf-form-section { background: white; border: none; padding: 0; margin-bottom: 0; page-break-inside: avoid; }
          #credit-file-retail { width: 100%; max-width: 100%; }
        }
      `}</style>

      <div id="credit-file-retail" dir="ltr">
        <div className="no-print">
          <div className="cf-actions">
            <div id="account-lookup" style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
              <div className="cf-field" style={{ flex: 1 }}>
                <label className={label}>Account Number</label>
                <input
                  type="text"
                  value={acc}
                  onChange={(e) => setAcc(e.target.value)}
                  placeholder="مثال: 115420"
                  className={field}
                />
              </div>
              <button onClick={loadAccount} disabled={loading} className="cf-btn cf-btn-primary">
                <Search size={16} /> {loading ? 'Loading...' : 'Load'}
              </button>
            </div>
            <button onClick={() => window.print()} className="cf-btn cf-btn-print">
              <Printer size={16} /> Print
            </button>
          </div>
        </div>

        {/* HEADER */}
        <div className="cf-form-section" style={{ textAlign: 'center', marginBottom: '6px' }}>
          <div style={{ fontSize: '14px', fontWeight: '700', marginBottom: '4px' }}>CREDIT FILE SUMMARY (Retail)</div>
          <div style={{ fontSize: '12px', color: '#666' }}>Bank Saderat Iran — R.O.</div>
        </div>

        {/* BRANCH */}
        <div className="cf-form-section">
          <div className="cf-form-title">Branch Code and Name</div>
          <div className="cf-grid">
            <div className="cf-field">
              <label className={label}>Branch Code</label>
              <input type="text" value={data.branchCode} onChange={set('branchCode')} />
            </div>
            <div className="cf-field">
              <label className={label}>Branch Name</label>
              <input type="text" value={data.branchName} onChange={set('branchName')} />
            </div>
            <div className="cf-field">
              <label className={label}>Date</label>
              <input type="text" value={data.date} onChange={set('date')} />
            </div>
          </div>
        </div>

        {/* ACCOUNT DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Account Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th style={{ width: '10%' }}>S/No.</th>
                <th style={{ width: '25%' }}>Description</th>
                <th style={{ width: '15%' }}>Details</th>
                <th style={{ width: '10%' }}>S/No.</th>
                <th style={{ width: '25%' }}>Description</th>
                <th style={{ width: '15%' }}>Details</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Customer's Name</td>
                <td><input type="text" value={data.customerName} onChange={set('customerName')} /></td>
                <td>3.0</td>
                <td>Rating</td>
                <td><input type="text" value={data.rating} onChange={set('rating')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Account Number</td>
                <td><input type="text" value={data.accountNumber} onChange={set('accountNumber')} /></td>
                <td>4.0</td>
                <td>No.of Previous Files</td>
                <td><input type="text" value={data.previousFiles} onChange={set('previousFiles')} /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* KYC DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">KYC Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th>S/No.</th>
                <th>Description</th>
                <th>Number</th>
                <th>Issue Date</th>
                <th>Expiry</th>
                <th>Remarks</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Passport</td>
                <td><input type="text" value={data.passportNum} onChange={set('passportNum')} /></td>
                <td><input type="text" value={data.passportIssue} onChange={set('passportIssue')} /></td>
                <td><input type="text" value={data.passportExpiry} onChange={set('passportExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>3.0</td>
                <td>Emirates ID</td>
                <td><input type="text" value={data.emiratesIdNum} onChange={set('emiratesIdNum')} /></td>
                <td><input type="text" value={data.emiratesIdIssue} onChange={set('emiratesIdIssue')} /></td>
                <td><input type="text" value={data.emiratesIdExpiry} onChange={set('emiratesIdExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* FACILITY DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Facility Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th>S/No.</th>
                <th>Description</th>
                <th>Approval Date</th>
                <th>Amount (AED)</th>
                <th>Rate Of Int.</th>
                <th>No. of Instalment</th>
                <th>Maturity Date</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Overdraft</td>
                <td><input type="text" value={data.overdraftApprovalDate} onChange={set('overdraftApprovalDate')} /></td>
                <td><input type="text" value={data.overdraftAmount} onChange={set('overdraftAmount')} /></td>
                <td><input type="text" value={data.overdraftRate} onChange={set('overdraftRate')} /></td>
                <td><input type="text" value={data.overdraftInstalments} onChange={set('overdraftInstalments')} /></td>
                <td><input type="text" value={data.overdraftMaturity} onChange={set('overdraftMaturity')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Personal Loan</td>
                <td><input type="text" value={data.personalLoanApprovalDate} onChange={set('personalLoanApprovalDate')} /></td>
                <td><input type="text" value={data.personalLoanAmount} onChange={set('personalLoanAmount')} /></td>
                <td><input type="text" value={data.personalLoanRate} onChange={set('personalLoanRate')} /></td>
                <td><input type="text" value={data.personalLoanInstalments} onChange={set('personalLoanInstalments')} /></td>
                <td><input type="text" value={data.personalLoanMaturity} onChange={set('personalLoanMaturity')} /></td>
              </tr>
              <tr>
                <td>3.0</td>
                <td>Staff loan</td>
                <td><input type="text" value={data.staffLoanApprovalDate} onChange={set('staffLoanApprovalDate')} /></td>
                <td><input type="text" value={data.staffLoanAmount} onChange={set('staffLoanAmount')} /></td>
                <td><input type="text" value={data.staffLoanRate} onChange={set('staffLoanRate')} /></td>
                <td><input type="text" value={data.staffLoanInstalments} onChange={set('staffLoanInstalments')} /></td>
                <td><input type="text" value={data.staffLoanMaturity} onChange={set('staffLoanMaturity')} /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* SECURITY DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Security Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th>S/No.</th>
                <th>Description</th>
                <th>AED</th>
                <th>USD</th>
                <th>IRR '000'</th>
                <th>OTHERS</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Underlien Deposits</td>
                <td><input type="text" value={data.underlienAED} onChange={set('underlienAED')} /></td>
                <td><input type="text" value={data.underlienUSD} onChange={set('underlienUSD')} /></td>
                <td><input type="text" value={data.underlienIRR} onChange={set('underlienIRR')} /></td>
                <td><input type="text" value={data.underlienOther} onChange={set('underlienOther')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Cheques</td>
                <td><input type="text" value={data.chequesAED} onChange={set('chequesAED')} /></td>
                <td><input type="text" value={data.chequesUSD} onChange={set('chequesUSD')} /></td>
                <td><input type="text" value={data.chequesIRR} onChange={set('chequesIRR')} /></td>
                <td><input type="text" value={data.chequesOther} onChange={set('chequesOther')} /></td>
              </tr>
              <tr>
                <td>3.0</td>
                <td>Collaterals</td>
                <td><input type="text" value={data.collateralsAED} onChange={set('collateralsAED')} /></td>
                <td><input type="text" value={data.collateralsUSD} onChange={set('collateralsUSD')} /></td>
                <td><input type="text" value={data.collateralsIRR} onChange={set('collateralsIRR')} /></td>
                <td><input type="text" value={data.collateralsOther} onChange={set('collateralsOther')} /></td>
              </tr>
              <tr>
                <td>4.0</td>
                <td>Guarantor/s</td>
                <td colSpan={5}><input type="text" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* GUARANTOR DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Guarantor's Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th style={{ width: '20%' }}>S/No.</th>
                <th>Name</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td><input type="text" value={data.guarantor1Name} onChange={set('guarantor1Name')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td><input type="text" value={data.guarantor2Name} onChange={set('guarantor2Name')} /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* CUSTOMER STATUS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Customer's History and Current Status</div>
          <div className="cf-grid">
            <div className="cf-field">
              <label className={label}>Status</label>
              <input type="text" value={data.customerStatus} onChange={set('customerStatus')} />
            </div>
          </div>
        </div>

        {/* SIGNATURE */}
        <div className="cf-form-section" style={{ marginTop: '24px', paddingTop: '20px', borderTop: '2px solid #999' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '600' }}>
            <div>Prepared By: __________________</div>
            <div>Authorized: __________________</div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
