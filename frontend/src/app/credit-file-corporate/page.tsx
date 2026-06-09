'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import { Printer, Search } from 'lucide-react'
import { customersApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'

type FormData = {
  date: string
  branchName: string
  branchCode: string
  customerName: string
  accountNumber: string
  businessType: string
  rating: string
  callReport: string
  previousFiles: string
  tradeLicenseNum: string
  tradeLicenseIssue: string
  tradeLicenseExpiry: string
  passportNum: string
  passportIssue: string
  passportExpiry: string
  managerIdNum: string
  managerIdIssue: string
  managerIdExpiry: string
  partner1Name: string
  partner1Nationality: string
  partner1Share: string
  partner1Remarks: string
  partner2Name: string
  partner2Nationality: string
  partner2Share: string
  partner2Remarks: string
  partner3Name: string
  partner3Nationality: string
  partner3Share: string
  partner3Remarks: string
  overdraftAmount: string
  overdraftRate: string
  overdraftExpiry: string
  overdraftNotices: string
  corporateLoanAmount: string
  corporateLoanRate: string
  corporateLoanExpiry: string
  chequeDiscountAmount: string
  chequeDiscountRate: string
  chequeDiscountExpiry: string
  labourGuaranteeAmount: string
  labourGuaranteeRate: string
  labourGuaranteeExpiry: string
  trustReceiptsAmount: string
  trustReceiptsRate: string
  trustReceiptsExpiry: string
  locSightAmount: string
  locSightMargin: string
  locSightExpiry: string
  locUsanceAmount: string
  locUsanceMargin: string
  locUsanceExpiry: string
  logAmount: string
  logMargin: string
  logExpiry: string
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
  guarantorNames: string
  partnerNames: string
  customerStatus: string
}

const INITIAL: FormData = {
  date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }),
  branchName: '',
  branchCode: '',
  customerName: '',
  accountNumber: '',
  businessType: '',
  rating: '',
  callReport: '',
  previousFiles: '',
  tradeLicenseNum: '',
  tradeLicenseIssue: '',
  tradeLicenseExpiry: '',
  passportNum: '',
  passportIssue: '',
  passportExpiry: '',
  managerIdNum: '',
  managerIdIssue: '',
  managerIdExpiry: '',
  partner1Name: '',
  partner1Nationality: '',
  partner1Share: '',
  partner1Remarks: '',
  partner2Name: '',
  partner2Nationality: '',
  partner2Share: '',
  partner2Remarks: '',
  partner3Name: '',
  partner3Nationality: '',
  partner3Share: '',
  partner3Remarks: '',
  overdraftAmount: '',
  overdraftRate: '',
  overdraftExpiry: '',
  overdraftNotices: '',
  corporateLoanAmount: '',
  corporateLoanRate: '',
  corporateLoanExpiry: '',
  chequeDiscountAmount: '',
  chequeDiscountRate: '',
  chequeDiscountExpiry: '',
  labourGuaranteeAmount: '',
  labourGuaranteeRate: '',
  labourGuaranteeExpiry: '',
  trustReceiptsAmount: '',
  trustReceiptsRate: '',
  trustReceiptsExpiry: '',
  locSightAmount: '',
  locSightMargin: '',
  locSightExpiry: '',
  locUsanceAmount: '',
  locUsanceMargin: '',
  locUsanceExpiry: '',
  logAmount: '',
  logMargin: '',
  logExpiry: '',
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
  guarantorNames: '',
  partnerNames: '',
  customerStatus: 'ACTIVE CUSTOMER',
}

export default function CreditFileCorporatePage() {
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
      const d: any = await customersApi.detail(a)
      const { customer, profile = {}, facilities = [] } = d
      const pdata = (profile && profile.data) || {}

      setData((s) => ({
        ...s,
        accountNumber: a,
        customerName: customer?.name || '',
        branchCode: customer?.branch_code || '',
        branchName: customer?.branch || '',
        businessType: pdata.business_type || '',
        rating: profile?.rating || '',
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
        #credit-file-corporate { max-width: 1200px; margin: 0 auto; }
        .cf-form-section { background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px; padding: 12px; margin-bottom: 12px; }
        .cf-form-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 8px; border-bottom: 2px solid #2563eb; padding-bottom: 4px; }
        .cf-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 8px; }
        .cf-field { display: flex; flex-direction: column; gap: 2px; }
        .cf-field input { width: 100%; border: 1px solid #ccc; border-radius: 3px; padding: 4px 6px; font-size: 12px; }
        .cf-field input:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1); }
        .cf-table { width: 100%; border-collapse: collapse; font-size: 11px; margin: 8px 0; }
        .cf-table th { background: #e5e7eb; font-weight: 600; padding: 4px 6px; text-align: left; border: 1px solid #999; }
        .cf-table td { padding: 3px 4px; border: 1px solid #999; }
        .cf-table input { width: 100%; border: none; padding: 2px; font-size: 10px; }
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
          #credit-file-corporate { width: 100%; max-width: 100%; }
        }
      `}</style>

      <div id="credit-file-corporate" dir="ltr">
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
          <div style={{ fontSize: '14px', fontWeight: '700', marginBottom: '4px' }}>CREDIT FILE SUMMARY (Corporate)</div>
          <div style={{ fontSize: '12px', color: '#666' }}>Bank Saderat Iran &mdash; R.O.</div>
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
                <th style={{ width: '8%' }}>S/No.</th>
                <th style={{ width: '18%' }}>Description</th>
                <th style={{ width: '18%' }}>Details</th>
                <th style={{ width: '8%' }}>S/No.</th>
                <th style={{ width: '20%' }}>Description</th>
                <th style={{ width: '18%' }}>Details</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Customer&rsquo;s Name</td>
                <td><input type="text" value={data.customerName} onChange={set('customerName')} /></td>
                <td>4.0</td>
                <td>Rating</td>
                <td><input type="text" value={data.rating} onChange={set('rating')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Account Number</td>
                <td><input type="text" value={data.accountNumber} onChange={set('accountNumber')} /></td>
                <td>5.0</td>
                <td>Call Report</td>
                <td><input type="text" value={data.callReport} onChange={set('callReport')} /></td>
              </tr>
              <tr>
                <td>3.0</td>
                <td>Type Of Business</td>
                <td><input type="text" value={data.businessType} onChange={set('businessType')} /></td>
                <td>6.0</td>
                <td>No. Of Previous Files</td>
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
                <td>Trade License</td>
                <td><input type="text" value={data.tradeLicenseNum} onChange={set('tradeLicenseNum')} /></td>
                <td><input type="text" value={data.tradeLicenseIssue} onChange={set('tradeLicenseIssue')} /></td>
                <td><input type="text" value={data.tradeLicenseExpiry} onChange={set('tradeLicenseExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Passport</td>
                <td><input type="text" value={data.passportNum} onChange={set('passportNum')} /></td>
                <td><input type="text" value={data.passportIssue} onChange={set('passportIssue')} /></td>
                <td><input type="text" value={data.passportExpiry} onChange={set('passportExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>4.0</td>
                <td>Manager Emirates ID</td>
                <td><input type="text" value={data.managerIdNum} onChange={set('managerIdNum')} /></td>
                <td><input type="text" value={data.managerIdIssue} onChange={set('managerIdIssue')} /></td>
                <td><input type="text" value={data.managerIdExpiry} onChange={set('managerIdExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* PARTNERS DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Partners Details</div>
          <table className="cf-table">
            <tbody>
              <tr>
                <th style={{ width: '8%' }}>S/No.</th>
                <th style={{ width: '30%' }}>Partners Name</th>
                <th style={{ width: '20%' }}>Nationality</th>
                <th style={{ width: '15%' }}>Share</th>
                <th style={{ width: '27%' }}>Remarks</th>
              </tr>
              {[
                { name: 'partner1Name', nat: 'partner1Nationality', share: 'partner1Share', rem: 'partner1Remarks' },
                { name: 'partner2Name', nat: 'partner2Nationality', share: 'partner2Share', rem: 'partner2Remarks' },
                { name: 'partner3Name', nat: 'partner3Nationality', share: 'partner3Share', rem: 'partner3Remarks' },
              ].map((fields, i) => (
                <tr key={i}>
                  <td>{i + 1}.0</td>
                  <td><input type="text" value={data[fields.name as keyof FormData]} onChange={set(fields.name as keyof FormData)} /></td>
                  <td><input type="text" value={data[fields.nat as keyof FormData]} onChange={set(fields.nat as keyof FormData)} /></td>
                  <td><input type="text" value={data[fields.share as keyof FormData]} onChange={set(fields.share as keyof FormData)} /></td>
                  <td><input type="text" value={data[fields.rem as keyof FormData]} onChange={set(fields.rem as keyof FormData)} /></td>
                </tr>
              ))}
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
                <th>Amount (AED)</th>
                <th>Rate Of Int./Margin</th>
                <th>Expiry Date</th>
                <th>Notices</th>
              </tr>
              <tr>
                <td>1.0</td>
                <td>Overdraft</td>
                <td><input type="text" value={data.overdraftAmount} onChange={set('overdraftAmount')} /></td>
                <td><input type="text" value={data.overdraftRate} onChange={set('overdraftRate')} /></td>
                <td><input type="text" value={data.overdraftExpiry} onChange={set('overdraftExpiry')} /></td>
                <td><input type="text" value={data.overdraftNotices} onChange={set('overdraftNotices')} /></td>
              </tr>
              <tr>
                <td>2.0</td>
                <td>Corporate Loan</td>
                <td><input type="text" value={data.corporateLoanAmount} onChange={set('corporateLoanAmount')} /></td>
                <td><input type="text" value={data.corporateLoanRate} onChange={set('corporateLoanRate')} /></td>
                <td><input type="text" value={data.corporateLoanExpiry} onChange={set('corporateLoanExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>3.0</td>
                <td>Cheque Discount</td>
                <td><input type="text" value={data.chequeDiscountAmount} onChange={set('chequeDiscountAmount')} /></td>
                <td><input type="text" value={data.chequeDiscountRate} onChange={set('chequeDiscountRate')} /></td>
                <td><input type="text" value={data.chequeDiscountExpiry} onChange={set('chequeDiscountExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>4.0</td>
                <td>labour Guarantee</td>
                <td><input type="text" value={data.labourGuaranteeAmount} onChange={set('labourGuaranteeAmount')} /></td>
                <td><input type="text" value={data.labourGuaranteeRate} onChange={set('labourGuaranteeRate')} /></td>
                <td><input type="text" value={data.labourGuaranteeExpiry} onChange={set('labourGuaranteeExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>5.0</td>
                <td>Trust Receipts</td>
                <td><input type="text" value={data.trustReceiptsAmount} onChange={set('trustReceiptsAmount')} /></td>
                <td><input type="text" value={data.trustReceiptsRate} onChange={set('trustReceiptsRate')} /></td>
                <td><input type="text" value={data.trustReceiptsExpiry} onChange={set('trustReceiptsExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td colSpan={6} style={{ fontWeight: '600', background: '#f0f0f0' }}>6.0 Letter Of Credit</td>
              </tr>
              <tr>
                <td>A</td>
                <td>SIGHT</td>
                <td><input type="text" value={data.locSightAmount} onChange={set('locSightAmount')} /></td>
                <td><input type="text" value={data.locSightMargin} onChange={set('locSightMargin')} /></td>
                <td><input type="text" value={data.locSightExpiry} onChange={set('locSightExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>B</td>
                <td>USANCE</td>
                <td><input type="text" value={data.locUsanceAmount} onChange={set('locUsanceAmount')} /></td>
                <td><input type="text" value={data.locUsanceMargin} onChange={set('locUsanceMargin')} /></td>
                <td><input type="text" value={data.locUsanceExpiry} onChange={set('locUsanceExpiry')} /></td>
                <td><input type="text" /></td>
              </tr>
              <tr>
                <td>6.0</td>
                <td>Letter Of Guarantee</td>
                <td><input type="text" value={data.logAmount} onChange={set('logAmount')} /></td>
                <td><input type="text" value={data.logMargin} onChange={set('logMargin')} /></td>
                <td><input type="text" value={data.logExpiry} onChange={set('logExpiry')} /></td>
                <td><input type="text" /></td>
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
                <th>IRR &rsquo;000&rsquo;</th>
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
                <td colSpan={6}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '11px' }}>
                    <div><strong>4.0 Undertaking Forms From GUARANTOR/S</strong></div>
                    <div><strong>PARTNER/S</strong></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* GUARANTOR DETAILS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Guarantor&rsquo;s Name</div>
          <div className="cf-field">
            <input type="text" value={data.guarantorNames} onChange={set('guarantorNames')} placeholder="Enter guarantor names" />
          </div>
        </div>

        {/* CUSTOMER STATUS */}
        <div className="cf-form-section">
          <div className="cf-form-title">Customer&rsquo;s History and Current Status</div>
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
