'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import Breadcrumb from '@/components/Breadcrumb'
import { customersApi, crmApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import {
  ArrowLeft, Building, FileText, Wallet, Building2, ShieldCheck, ClipboardCheck,
  CreditCard, Paperclip, ListChecks, Activity, Users as UsersIcon,
} from 'lucide-react'
import { PROPERTIES } from '../properties/data'

const CHECKLIST_STEPS = [
  'Offer Letter', 'Document Verification', 'Document Scanning', 'Add to Table',
  'Central Folder Upload', 'Regulatory Document (Contra)', 'K.Y.C', 'Summary', 'Archive',
]

function money(n: any, cur = 'AED') { return `${cur} ${Number(n || 0).toLocaleString()}` }
function val(v: any) { return v === null || v === undefined || v === '' ? '—' : String(v) }
function done(v: any) { return v === '✓' || v === true || String(v).toLowerCase() === 'true' || v === '1' }

function statusBadge(s: any) {
  const v = (s || '').toString().toLowerCase()
  if (v === 'active') return 'bg-green-100 text-green-700'
  if (v === 'closed' || v === 'inactive') return 'bg-gray-100 text-gray-700'
  return 'bg-yellow-100 text-yellow-700'
}

function CustomerDetailInner() {
  const params = useSearchParams()
  const router = useRouter()
  const id = params.get('id')
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    if (!id) { setError('No customer specified'); setLoading(false); return }
    customersApi.detail(id).then(setData).catch((e) => setError(parseApiError(e))).finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
  if (error || !data) return (
    <div className="max-w-lg mx-auto mt-8">
      <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4" data-testid="customer-detail-error">{error || 'Customer not found'}</div>
      <button onClick={() => router.push('/customers')} className="mt-4 px-4 py-2 border rounded-lg">Back to Customers</button>
    </div>
  )

  const { customer, facilities = [], offer_letters = [], guarantors = [], tasks = [], attachments = [], journal = [], profile, checklist, summary = {} } = data
  const pdata = (profile && profile.data) || {}
  const acc = String(customer.account_no || '').trim()
  const myProps = acc ? PROPERTIES.filter((p) => String(p.ac_no).trim() === acc) : []
  const completeness = profile?.profile_completeness || '—'

  const toggleStep = async (step: number, isDone: boolean) => {
    try {
      await crmApi.toggleChecklistStep(acc, step, !isDone)
      setData((d: any) => ({ ...d, checklist: { ...(d.checklist || { account_no: acc }), [`item${step}`]: !isDone ? '✓' : '' } }))
      toast.success(`${CHECKLIST_STEPS[step - 1]}: ${!isDone ? 'done' : 'pending'}`)
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  const TABS = [
    { id: 'overview', label: 'Overview', icon: Building },
    { id: 'kyc', label: 'KYC & Docs', icon: CreditCard },
    { id: 'facilities', label: 'Facilities', icon: Wallet },
    { id: 'guarantors', label: 'Guarantors', icon: ShieldCheck },
    { id: 'collateral', label: 'Collateral & Property', icon: Building2 },
    { id: 'checklist', label: 'Checklist', icon: ClipboardCheck },
    { id: 'tasks', label: 'Tasks', icon: ListChecks },
    { id: 'attachments', label: 'Attachments', icon: Paperclip },
    { id: 'activity', label: 'Activity', icon: Activity },
  ]

  return (
    <div data-testid="customer-detail-content">
      <Breadcrumb items={[{ label: 'Customers', href: '/customers' }, { label: customer.name }]} />
      <button onClick={() => router.push('/customers')} className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4"><ArrowLeft size={16} /> Back</button>

      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-2xl font-bold">{customer.name || acc}</h2>
          <p className="text-gray-500">{acc} · <span className="capitalize">{profile?.account_type || customer.account_type}</span>{customer.branch ? ` · ${customer.branch}` : ''}{profile?.rating ? ` · Rating ${profile.rating}` : ''}</p>
        </div>
        <div className="text-right">
          <span className={`px-3 py-1 rounded-full text-sm ${statusBadge(customer.status)}`}>{customer.status}</span>
          <div className="text-xs text-gray-400 mt-1">Completeness: {completeness}</div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <Card icon={<Wallet size={15} />} label="Facilities" value={summary.total_facilities} sub={`${summary.active_facilities || 0} active`} />
        <Card icon={<Wallet size={15} />} label="Total Exposure" value={money(summary.total_exposure)} />
        <Card icon={<ShieldCheck size={15} />} label="Guarantors" value={summary.total_guarantors ?? guarantors.length} />
        <Card icon={<Building2 size={15} />} label="Properties" value={myProps.length} />
        <Card icon={<FileText size={15} />} label="Offer Letters" value={summary.total_offers} />
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 border-b border-gray-200 mb-4">
        {TABS.map((t) => {
          const I = t.icon
          return (
            <button key={t.id} onClick={() => setTab(t.id)} type="button"
              className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px ${tab === t.id ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              <I size={15} /> {t.label}
            </button>
          )
        })}
      </div>

      {tab === 'overview' && (
        <div className="space-y-5">
          <Section title="Contact & Basics">
            <Grid items={[
              ['Email', customer.email], ['Phone', customer.phone], ['Mobile', customer.mobile],
              ['Relationship Manager', customer.relationship_manager],
              ['Business Type', profile?.business_type], ['Customer Status', profile?.customer_status],
              ['Rating', profile?.rating], ['Updated By', profile?.updated_by],
            ]} />
          </Section>
          <FacilitiesTable facilities={facilities} />
        </div>
      )}

      {tab === 'kyc' && (
        <Section title="KYC Documents">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <KycCard title="Trade License" no={profile?.trade_license_no} expiry={profile?.trade_license_expiry} />
            <KycCard title="Passport" no={profile?.passport_no} expiry={profile?.passport_expiry} />
            <KycCard title="Emirates ID" no={profile?.emirates_id_no} expiry={profile?.emirates_id_expiry} />
            <KycCard title="Visa" no={profile?.visa_no} expiry={profile?.visa_expiry} />
            <KycCard title="Tenancy" no={profile?.tenancy_no} expiry={profile?.tenancy_expiry} />
          </div>
          {!profile && <Empty>No profile/KYC data</Empty>}
        </Section>
      )}

      {tab === 'facilities' && <FacilitiesTable facilities={facilities} standalone />}

      {tab === 'guarantors' && (
        <Section title={`Guarantors & Security Cheques (${guarantors.length})`}>
          <SimpleTable head={['Guarantor', 'Account', 'Cheque No', 'Amount', 'Bank', 'Ref']}
            rows={guarantors.map((g: any) => [g.guarantor_name, g.guarantor_account, g.cheque_no, g.cheque_amount ? Number(g.cheque_amount).toLocaleString() : '—', g.issuing_bank, g.pim_ref])}
            empty="No guarantors" />
        </Section>
      )}

      {tab === 'collateral' && (
        <div className="space-y-5">
          <Section title="Security Summary">
            <Grid items={[
              ['Cheques Total (AED)', pdata.Sec_Cheques_AED_Total], ['Cheques Count', pdata.Sec_Cheques_Count],
              ['Collateral (AED)', pdata.Sec_Collateral_AED], ['Underlien (AED)', pdata.Sec_Underlien_AED],
              ['Borrower Chq No', pdata.Borrower_ChqNo], ['Borrower Chq Amount', pdata.Borrower_ChqAmount],
            ]} />
          </Section>
          <Section title="Property / Mortgage">
            <Grid items={[
              ['Property No', pdata.Property_No], ['Address', pdata.Property_Address],
              ['Mortgage Amount', pdata.Mortgage_Amount], ['Mortgage Bank', pdata.Mortgage_Bank],
              ['Mortgage Date', pdata.Mortgage_Date],
            ]} />
            {myProps.length > 0 && (
              <SimpleTable head={['Deed No.', 'City', 'Type', 'Mortgage Date', 'Valuation', 'Insurance Expiry']}
                rows={myProps.map((p) => [p.deed_no, p.city, p.type, p.mortgage_date, p.valuation != null ? `${p.currency} ${p.valuation.toLocaleString()}` : '—', p.insurance_expiry])}
                empty="" />
            )}
          </Section>
          <Section title="Partners">
            <SimpleTable head={['Name', 'Nationality', 'Share %']}
              rows={[1, 2, 3, 4, 5, 6, 7, 8].map((i) => [pdata[`Partner${i}Name`], pdata[`Partner${i}Nationality`], pdata[`Partner${i}Share`]]).filter((r) => r[0])}
              empty="No partners" />
          </Section>
        </div>
      )}

      {tab === 'checklist' && (
        <Section title="Credit-File Workflow (9 steps)">
          <p className="text-xs text-gray-400 mb-3">روی هر مرحله بزنید تا انجام‌شده/در‌انتظار شود (در Journal ثبت می‌شود).</p>
          <div className="space-y-1.5">
            {CHECKLIST_STEPS.map((s, i) => {
              const isDone = done(checklist?.[`item${i + 1}`])
              return (
                <button key={i} type="button" onClick={() => toggleStep(i + 1, isDone)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-colors ${isDone ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200 hover:bg-gray-50'}`}>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${isDone ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                    {isDone ? '✓' : i + 1}
                  </span>
                  <span className={`flex-1 text-sm ${isDone ? 'text-green-800 font-medium' : 'text-gray-700'}`}>{s}</span>
                  <span className="text-xs text-gray-400">{isDone ? 'Done' : 'Pending'}</span>
                </button>
              )
            })}
          </div>
          {checklist && <p className="text-xs text-gray-400 mt-3">Total {checklist.total} · last action {val(checklist.last_action)} by {val(checklist.last_user)}</p>}
        </Section>
      )}

      {tab === 'tasks' && (
        <Section title={`Tasks & Follow-ups (${tasks.length})`}>
          <SimpleTable head={['Task', 'Status', 'Follow-up', 'Priority', 'Created By']}
            rows={tasks.map((t: any) => [t.task_name, t.status || '—', t.followup_date, t.priority, t.created_by])}
            empty="No tasks" />
        </Section>
      )}

      {tab === 'attachments' && (
        <Section title={`Documents (${attachments.length})`}>
          <SimpleTable head={['Document', 'Uploaded', 'By', 'Size', 'Shared']}
            rows={attachments.map((a: any) => [a.original_name || a.file_name, (a.upload_date || '').slice(0, 10), a.uploaded_by, a.file_size ? `${Math.round(Number(a.file_size) / 1024)} KB` : '—', done(a.is_shared) ? 'Yes' : 'No'])}
            empty="No attachments" />
          <p className="text-xs text-gray-400 mt-2">فایل‌ها روی شبکهٔ بانک (S:) ذخیره‌اند؛ اینجا فقط متادیتا نمایش داده می‌شود.</p>
        </Section>
      )}

      {tab === 'activity' && (
        <Section title={`Activity Log (${journal.length})`}>
          <SimpleTable head={['Date', 'Item', 'Action', 'Source', 'User', 'Status']}
            rows={journal.map((j: any) => [(j.date || '').slice(0, 10), j.item, j.action, j.source, j.user, done(j.status) ? '✓' : j.status])}
            empty="No activity" />
        </Section>
      )}
    </div>
  )
}

function Card({ icon, label, value, sub }: any) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-3">
      <div className="flex items-center justify-between text-gray-500 mb-1"><span className="text-xs">{label}</span>{icon}</div>
      <div className="text-lg font-bold">{value ?? 0}</div>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}
function Section({ title, children }: any) {
  return <div className="bg-white rounded-lg shadow-sm p-4"><div className="font-medium mb-3">{title}</div>{children}</div>
}
function Empty({ children }: any) { return <p className="px-2 py-6 text-gray-400 text-center text-sm">{children}</p> }
function Grid({ items }: { items: any[][] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
      {items.map(([k, v], i) => <div key={i}><p className="text-gray-400 text-xs">{k}</p><p>{val(v)}</p></div>)}
    </div>
  )
}
function KycCard({ title, no, expiry }: any) {
  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <div className="text-xs text-gray-400">{title}</div>
      <div className="font-medium text-sm">{val(no)}</div>
      <div className="text-xs text-gray-500 mt-1">Expiry: {val(expiry)}</div>
    </div>
  )
}
function SimpleTable({ head, rows, empty }: { head: string[]; rows: any[][]; empty: string }) {
  if (!rows.length) return <Empty>{empty}</Empty>
  return (
    <div className="overflow-auto">
      <table className="w-full text-sm whitespace-nowrap">
        <thead className="bg-gray-50"><tr className="text-left text-gray-500">{head.map((h, i) => <th key={i} className="px-3 py-2">{h}</th>)}</tr></thead>
        <tbody className="divide-y">
          {rows.map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j} className="px-3 py-1.5">{val(c)}</td>)}</tr>)}
        </tbody>
      </table>
    </div>
  )
}
function FacilitiesTable({ facilities, standalone }: any) {
  const inner = (
    <SimpleTable head={['Name / Ref', 'Type', 'Amount', 'Outstanding', 'Status']}
      rows={facilities.map((f: any) => [f.name, (f.facility_type || '').toUpperCase(), money(f.amount, f.currency), money(f.outstanding, f.currency), f.status])}
      empty="No facilities" />
  )
  return standalone ? <Section title={`Facilities (${facilities.length})`}>{inner}</Section> : <Section title="Facilities">{inner}</Section>
}

export default function CustomerDetailPage() {
  return (
    <Layout>
      <Suspense fallback={<div className="py-16 text-center text-gray-500">Loading…</div>}>
        <CustomerDetailInner />
      </Suspense>
    </Layout>
  )
}
