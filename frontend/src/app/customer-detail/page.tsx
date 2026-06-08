'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import Breadcrumb from '@/components/Breadcrumb'
import { customersApi, crmApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import {
  ArrowLeft, Building, FileText, Wallet, Building2, ShieldCheck, ClipboardCheck,
  CreditCard, Paperclip, ListChecks, Activity, Users as UsersIcon, StickyNote,
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
  const [newTask, setNewTask] = useState('')
  const [newTaskDate, setNewTaskDate] = useState('')
  const [ng, setNg] = useState<any>({ guarantor_name: '', guarantor_account: '', cheque_no: '', cheque_amount: '', issuing_bank: 'BSI' })
  const [nf, setNf] = useState<any>({ facility_type: 'overdraft', amount: '', currency: 'AED', name: '' })
  const [kycEdit, setKycEdit] = useState(false)
  const [kycForm, setKycForm] = useState<any>({})
  const [newNote, setNewNote] = useState('')

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

  const { customer, facilities = [], offer_letters = [], guarantors = [], tasks = [], attachments = [], journal = [], notes = [], profile, checklist, summary = {} } = data
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

  const addTask = async () => {
    if (!newTask.trim()) return
    try {
      const t = await crmApi.createTask(acc, { task_name: newTask.trim(), followup_date: newTaskDate })
      setData((d: any) => ({ ...d, tasks: [t, ...(d.tasks || [])] }))
      setNewTask(''); setNewTaskDate('')
      toast.success('Task added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const completeTask = async (id: string) => {
    try {
      await crmApi.updateTask(id, { status: 'Done' })
      setData((d: any) => ({ ...d, tasks: (d.tasks || []).map((t: any) => t.id === id ? { ...t, status: 'Done' } : t) }))
      toast.success('Task completed')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addGuarantor = async () => {
    if (!ng.guarantor_name?.trim()) { toast.error('Guarantor name required'); return }
    try {
      const body = { ...ng, cheque_amount: ng.cheque_amount ? Number(ng.cheque_amount) : undefined }
      const g = await crmApi.addGuarantor(acc, body)
      setData((d: any) => ({ ...d, guarantors: [...(d.guarantors || []), g], summary: { ...d.summary, total_guarantors: (d.summary?.total_guarantors || 0) + 1 } }))
      setNg({ guarantor_name: '', guarantor_account: '', cheque_no: '', cheque_amount: '', issuing_bank: 'BSI' })
      toast.success('Guarantor added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addFacility = async () => {
    if (!nf.amount || Number(nf.amount) <= 0) { toast.error('Amount required'); return }
    try {
      const f = await crmApi.addFacility(acc, { facility_type: nf.facility_type, amount: Number(nf.amount), currency: nf.currency, name: nf.name })
      setData((d: any) => ({ ...d, facilities: [f, ...(d.facilities || [])], summary: { ...d.summary, total_facilities: (d.summary?.total_facilities || 0) + 1, total_exposure: (d.summary?.total_exposure || 0) + Number(nf.amount) } }))
      setNf({ facility_type: 'overdraft', amount: '', currency: 'AED', name: '' })
      toast.success('Facility added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const KYC_DOCS = [
    ['Trade License', 'trade_license_no', 'trade_license_expiry'],
    ['Passport', 'passport_no', 'passport_expiry'],
    ['Emirates ID', 'emirates_id_no', 'emirates_id_expiry'],
    ['Visa', 'visa_no', 'visa_expiry'],
    ['Tenancy', 'tenancy_no', 'tenancy_expiry'],
  ]
  const startKycEdit = () => {
    const f: any = { business_type: profile?.business_type || '', rating: profile?.rating || '' }
    KYC_DOCS.forEach(([, nk, ek]) => { f[nk] = profile?.[nk] || ''; f[ek] = profile?.[ek] || '' })
    setKycForm(f); setKycEdit(true)
  }
  const saveKyc = async () => {
    try {
      const updated = await crmApi.updateProfile(acc, kycForm)
      setData((d: any) => ({ ...d, profile: { ...(d.profile || { account_no: acc }), ...updated } }))
      setKycEdit(false); toast.success('KYC updated')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addNote = async () => {
    if (!newNote.trim()) return
    try {
      const n = await crmApi.addNote(acc, { content: newNote.trim() })
      setData((d: any) => ({ ...d, notes: [n, ...(d.notes || [])] }))
      setNewNote(''); toast.success('Note added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const printSummary = () => {
    document.body.classList.add('print-summary')
    setTimeout(() => { window.print(); document.body.classList.remove('print-summary') }, 60)
  }

  const TABS = [
    { id: 'overview', label: 'Overview', icon: Building },
    { id: 'kyc', label: 'KYC & Docs', icon: CreditCard },
    { id: 'facilities', label: 'Facilities', icon: Wallet },
    { id: 'guarantors', label: 'Guarantors', icon: ShieldCheck },
    { id: 'collateral', label: 'Collateral & Property', icon: Building2 },
    { id: 'checklist', label: 'Checklist', icon: ClipboardCheck },
    { id: 'tasks', label: 'Tasks', icon: ListChecks },
    { id: 'notes', label: 'Notes', icon: StickyNote },
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
          <button onClick={printSummary} type="button" className="mb-2 flex items-center gap-1.5 ml-auto bg-gray-800 hover:bg-gray-900 text-white rounded-lg px-3 py-1.5 text-sm">
            <FileText size={14} /> Print Summary
          </button>
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
          <div className="flex justify-end mb-3">
            {!kycEdit ? (
              <button onClick={startKycEdit} type="button" className="text-sm text-blue-600 hover:underline">Edit</button>
            ) : (
              <div className="flex gap-2">
                <button onClick={() => setKycEdit(false)} type="button" className="text-sm text-gray-500">Cancel</button>
                <button onClick={saveKyc} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium">Save</button>
              </div>
            )}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {KYC_DOCS.map(([title, nk, ek]) => (
              <div key={nk} className="border border-gray-200 rounded-lg p-3">
                <div className="text-xs text-gray-400">{title}</div>
                {kycEdit ? (
                  <>
                    <input value={kycForm[nk] || ''} onChange={(e) => setKycForm((s: any) => ({ ...s, [nk]: e.target.value }))}
                      placeholder="Number" className="w-full border border-gray-300 rounded px-2 py-1 text-sm mt-1" />
                    <input value={kycForm[ek] || ''} onChange={(e) => setKycForm((s: any) => ({ ...s, [ek]: e.target.value }))}
                      placeholder="Expiry (YYYY-MM-DD)" className="w-full border border-gray-300 rounded px-2 py-1 text-xs mt-1" />
                  </>
                ) : (
                  <>
                    <div className="font-medium text-sm">{val(profile?.[nk])}</div>
                    <div className="text-xs text-gray-500 mt-1">Expiry: {val(profile?.[ek])}</div>
                  </>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {tab === 'facilities' && (
        <Section title={`Facilities (${facilities.length})`}>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 mb-4">
            <select value={nf.facility_type} onChange={(e) => setNf((s: any) => ({ ...s, facility_type: e.target.value }))}
              className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm">
              <option value="overdraft">Overdraft</option><option value="loan">Loan</option>
              <option value="lc">LC</option><option value="lg">LG</option><option value="other">Other</option>
            </select>
            <input value={nf.amount} onChange={(e) => setNf((s: any) => ({ ...s, amount: e.target.value }))} placeholder="Amount" inputMode="numeric" className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
            <input value={nf.currency} onChange={(e) => setNf((s: any) => ({ ...s, currency: e.target.value }))} placeholder="AED" className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
            <input value={nf.name} onChange={(e) => setNf((s: any) => ({ ...s, name: e.target.value }))} placeholder="Ref / Offer Letter No" className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
            <button onClick={addFacility} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm font-medium">Add Facility</button>
          </div>
          <SimpleTable head={['Name / Ref', 'Type', 'Amount', 'Outstanding', 'Status']}
            rows={facilities.map((f: any) => [f.name, (f.facility_type || '').toUpperCase(), money(f.amount, f.currency), money(f.outstanding, f.currency), f.status])}
            empty="No facilities" />
        </Section>
      )}

      {tab === 'guarantors' && (
        <Section title={`Guarantors & Security Cheques (${guarantors.length})`}>
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-2 mb-4">
            {[['guarantor_name', 'Guarantor name'], ['guarantor_account', 'Account'], ['cheque_no', 'Cheque No'], ['cheque_amount', 'Amount'], ['issuing_bank', 'Bank']].map(([k, ph]) => (
              <input key={k} value={ng[k] || ''} onChange={(e) => setNg((s: any) => ({ ...s, [k]: e.target.value }))}
                placeholder={ph} inputMode={k === 'cheque_amount' ? 'numeric' : undefined}
                className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            ))}
            <button onClick={addGuarantor} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm font-medium">Add</button>
          </div>
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
          <div className="flex flex-wrap gap-2 mb-4">
            <input value={newTask} onChange={(e) => setNewTask(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addTask()}
              placeholder="New task…" className="flex-1 min-w-[200px] border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <input value={newTaskDate} onChange={(e) => setNewTaskDate(e.target.value)} type="date"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <button onClick={addTask} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium">Add Task</button>
          </div>
          {tasks.length === 0 ? <Empty>No tasks</Empty> : (
            <div className="overflow-auto">
              <table className="w-full text-sm whitespace-nowrap">
                <thead className="bg-gray-50"><tr className="text-left text-gray-500">
                  <th className="px-3 py-2">Task</th><th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Follow-up</th><th className="px-3 py-2">Priority</th>
                  <th className="px-3 py-2">By</th><th className="px-3 py-2"></th>
                </tr></thead>
                <tbody className="divide-y">
                  {tasks.map((t: any) => {
                    const isDone = done(t.status) || String(t.status).toLowerCase() === 'done'
                    return (
                      <tr key={t.id} className={isDone ? 'bg-green-50' : ''}>
                        <td className="px-3 py-1.5">{val(t.task_name)}</td>
                        <td className="px-3 py-1.5">{isDone ? <span className="text-green-700">✓ Done</span> : (val(t.status) === '—' ? 'Open' : t.status)}</td>
                        <td className="px-3 py-1.5">{val(t.followup_date)}</td>
                        <td className="px-3 py-1.5">{val(t.priority)}</td>
                        <td className="px-3 py-1.5">{val(t.created_by)}</td>
                        <td className="px-3 py-1.5">{!isDone && <button onClick={() => completeTask(t.id)} type="button" className="text-xs text-blue-600 hover:underline">Complete</button>}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Section>
      )}

      {tab === 'notes' && (
        <Section title={`Notes (${notes.length})`}>
          <div className="flex gap-2 mb-4">
            <input value={newNote} onChange={(e) => setNewNote(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addNote()}
              placeholder="Write a note…" className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <button onClick={addNote} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium">Add Note</button>
          </div>
          {notes.length === 0 ? <Empty>No notes</Empty> : (
            <div className="space-y-2">
              {notes.map((n: any) => (
                <div key={n.id} className="border border-gray-200 rounded-lg p-3">
                  {n.title && <div className="font-medium text-sm">{n.title}</div>}
                  <div className="text-sm text-gray-700">{n.content}</div>
                  <div className="text-xs text-gray-400 mt-1">{val(n.created_date)} · {val(n.created_by)}{n.category ? ` · ${n.category}` : ''}</div>
                </div>
              ))}
            </div>
          )}
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

      {/* ---- Printable credit summary (Excel GenerateSummaryReport equivalent) ---- */}
      <style>{`
        #credit-summary { position: fixed; left: -9999px; top: 0; width: 190mm; }
        @media print {
          body.print-summary * { visibility: hidden !important; }
          body.print-summary #credit-summary, body.print-summary #credit-summary * { visibility: visible !important; }
          body.print-summary #credit-summary { position: absolute; left: 0; top: 0; }
          @page { size: A4 portrait; margin: 12mm; }
        }
        #credit-summary .cs-h { font-size: 16pt; font-weight: 800; }
        #credit-summary .cs-sub { font-size: 10pt; color:#444; margin-bottom: 6mm; }
        #credit-summary h4 { font-size: 11pt; font-weight: 700; background:#eee; padding: 2px 6px; margin: 5mm 0 2mm; }
        #credit-summary table { width:100%; border-collapse: collapse; font-size: 9.5pt; }
        #credit-summary td, #credit-summary th { border: 0.5pt solid #999; padding: 2px 5px; text-align: left; }
        #credit-summary .kv { font-size: 9.5pt; }
        #credit-summary .kv td { border: 0; padding: 1px 4px; }
      `}</style>
      <div id="credit-summary" dir="ltr">
        <div className="cs-h">CREDIT FILE SUMMARY</div>
        <div className="cs-sub">Bank Saderat Iran — R.O. &nbsp;|&nbsp; Generated {new Date().toLocaleDateString()}</div>
        <table className="kv"><tbody>
          <tr><td><b>Customer:</b> {customer.name}</td><td><b>Account:</b> {acc}</td><td><b>Branch:</b> {val(customer.branch)}</td></tr>
          <tr><td><b>Type:</b> {val(profile?.account_type || customer.account_type)}</td><td><b>Rating:</b> {val(profile?.rating)}</td><td><b>Business:</b> {val(profile?.business_type)}</td></tr>
        </tbody></table>

        <h4>Facilities — Total Exposure {money(summary.total_exposure)}</h4>
        <table><tbody>
          <tr><th>Ref</th><th>Type</th><th>Amount</th><th>Status</th></tr>
          {facilities.map((f: any) => <tr key={f.id}><td>{val(f.name)}</td><td>{(f.facility_type || '').toUpperCase()}</td><td>{money(f.amount, f.currency)}</td><td>{f.status}</td></tr>)}
        </tbody></table>

        <h4>KYC Documents</h4>
        <table><tbody>
          <tr><th>Document</th><th>Number</th><th>Expiry</th></tr>
          {KYC_DOCS.map(([t, nk, ek]) => <tr key={nk}><td>{t}</td><td>{val(profile?.[nk])}</td><td>{val(profile?.[ek])}</td></tr>)}
        </tbody></table>

        <h4>Guarantors ({guarantors.length})</h4>
        <table><tbody>
          <tr><th>Name</th><th>Account</th><th>Cheque No</th><th>Amount</th></tr>
          {guarantors.map((g: any, i: number) => <tr key={i}><td>{val(g.guarantor_name)}</td><td>{val(g.guarantor_account)}</td><td>{val(g.cheque_no)}</td><td>{g.cheque_amount ? Number(g.cheque_amount).toLocaleString() : '—'}</td></tr>)}
        </tbody></table>

        {myProps.length > 0 && (<><h4>Mortgaged Properties ({myProps.length})</h4>
        <table><tbody>
          <tr><th>Deed</th><th>City</th><th>Type</th><th>Valuation</th></tr>
          {myProps.map((p, i) => <tr key={i}><td>{val(p.deed_no)}</td><td>{val(p.city)}</td><td>{val(p.type)}</td><td>{p.valuation != null ? `${p.currency} ${p.valuation.toLocaleString()}` : '—'}</td></tr>)}
        </tbody></table></>)}

        <div style={{ marginTop: '14mm', display: 'flex', justifyContent: 'space-between', fontSize: '9.5pt', fontWeight: 700 }}>
          <div>Prepared By: __________________</div><div>Authorized: __________________</div>
        </div>
      </div>
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
