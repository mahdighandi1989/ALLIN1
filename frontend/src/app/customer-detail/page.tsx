'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import Breadcrumb from '@/components/Breadcrumb'
import { customersApi, crmApi, parseApiError, downloadFile } from '@/lib/api'
import toast from 'react-hot-toast'
import {
  ArrowLeft, Building, FileText, Wallet, Building2, ShieldCheck, ClipboardCheck,
  CreditCard, Paperclip, ListChecks, Activity, Users as UsersIcon, StickyNote, Mail,
} from 'lucide-react'
const CHECKLIST_STEPS = [
  'Offer Letter', 'Document Verification', 'Document Scanning', 'Add to Table',
  'Central Folder Upload', 'Regulatory Document (Contra)', 'K.Y.C', 'Summary', 'Archive',
]

function money(n: any, cur = 'AED') { return `${cur} ${Number(n || 0).toLocaleString()}` }
function val(v: any) { return v === null || v === undefined || v === '' ? '—' : String(v) }
function done(v: any) { return v === '✓' || v === true || String(v).toLowerCase() === 'true' || v === '1' }
function isHourglass(v: any) { return String(v) === '⌛' }

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
  const [showPropForm, setShowPropForm] = useState(false)
  const [np, setNp] = useState<any>({ valuation_currency: 'AED', country: 'UAE' })
  const [nfd, setNfd] = useState<any>({ currency: 'AED' })
  const [npt, setNpt] = useState<any>({})
  const [chkFacility, setChkFacility] = useState('')  // '' = account-level checklist
  const [comp, setComp] = useState<any>(null)
  const [upFiles, setUpFiles] = useState<File[]>([])
  const [upOpts, setUpOpts] = useState<any>({ facility_id: '', row_index: '', is_shared: false })

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

  const { customer, facilities = [], offer_letters = [], guarantors = [], securities = [], tasks = [], attachments = [], journal = [], notes = [], profile, checklist, summary = {}, properties = [], fixed_deposits: fixedDeposits = [], partners: partnerRows = [], facility_checklists: facilityChecklists = [] } = data
  const pdata = (profile && profile.data) || {}
  const acc = String(customer.account_no || '').trim()
  const completeness = profile?.profile_completeness || '—'

  // Live securities aggregation from the merged guarantor data — mirrors the
  // Excel CalculateTotalChequesFromBackend / GetGuarantorSummary and the FD
  // management forms (FD is stored on each guarantor row).
  const num = (v: any) => { const n = Number(String(v ?? '').replace(/[^0-9.-]/g, '')); return isFinite(n) ? n : 0 }
  const fdShown = (v: any) => { const f = String(v ?? '').trim(); return f && f !== '-' && f !== '—' && f !== '0' }
  const flag = (v: any) => { const t = String(v ?? '').toLowerCase(); return t.includes('avail') ? '✓' : (!t || t === '-' ? '—' : v) }
  const secTotal = securities.reduce((t: number, s: any) => t + Number(s.cheque_amount_num || 0), 0)
  const chequeRows = guarantors.filter((g: any) => g.cheque_no || g.cheque_amount)
  const chequeTotal = guarantors.reduce((s: number, g: any) => s + num(g.cheque_amount), 0)
  const fdRows = guarantors.filter((g: any) => fdShown(g.fd))
  const blobPartners = [1, 2, 3, 4, 5, 6, 7, 8]
    .map((i) => [pdata[`Partner${i}Name`], pdata[`Partner${i}Nationality`], pdata[`Partner${i}Share`]])
    .filter((r) => r[0])
  // Prefer the structured (editable) partner records; fall back to the legacy
  // data_json blob so older imported profiles still render.
  const partnerList: any[][] = partnerRows.length
    ? partnerRows.map((p: any) => [p.name, p.nationality, p.share])
    : blobPartners
  // Properties for the printable summary: structured backend rows if any, else
  // the imported mortgage register joined from the static dataset.
  const propsForSummary: any[] = properties.map((p: any) => ({ deed_no: p.mortgage_deed_no, city: p.city, type: p.prop_type, currency: p.valuation_currency, valuation: p.valuation }))
  // The checklist currently shown: a selected facility's own checklist, or the
  // account-level one when no facility is chosen.
  const activeChecklist = chkFacility
    ? (facilityChecklists.find((fc: any) => fc.facility_id === chkFacility) || null)
    : checklist
  const isCorporate = String(profile?.account_type || customer.account_type || '').toLowerCase().includes('corp')

  const toggleStep = async (step: number, isDone: boolean) => {
    try {
      if (chkFacility) {
        const updated = await crmApi.toggleFacilityChecklist(chkFacility, step, !isDone)
        setData((d: any) => {
          const list = d.facility_checklists || []
          const next = list.some((fc: any) => fc.facility_id === chkFacility)
            ? list.map((fc: any) => (fc.facility_id === chkFacility ? updated : fc))
            : [...list, updated]
          return { ...d, facility_checklists: next }
        })
      } else {
        await crmApi.toggleChecklistStep(acc, step, !isDone)
        setData((d: any) => ({ ...d, checklist: { ...(d.checklist || { account_no: acc }), [`item${step}`]: !isDone ? '✓' : '' } }))
      }
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
  // [title, numberKey, expiryKey, [ [extraKey, label], ... ]]
  const KYC_DOCS: [string, string, string, [string, string][]][] = [
    ['Trade License', 'trade_license_no', 'trade_license_expiry', [['trade_license_issue', 'Issue date'], ['trade_license_remarks', 'Remarks']]],
    ['Passport', 'passport_no', 'passport_expiry', [['passport_issue', 'Issue date'], ['passport_nationality', 'Nationality'], ['passport_remarks', 'Remarks']]],
    ['Emirates ID', 'emirates_id_no', 'emirates_id_expiry', [['emirates_id_issue', 'Issue date'], ['emirates_id_golden', 'Golden (Yes/No)'], ['emirates_id_remarks', 'Remarks']]],
    ['Visa', 'visa_no', 'visa_expiry', [['visa_issue', 'Issue date'], ['visa_type', 'Type']]],
    ['Tenancy', 'tenancy_no', 'tenancy_expiry', [['tenancy_issue', 'Issue date'], ['tenancy_address', 'Address']]],
  ]
  const startKycEdit = () => {
    const f: any = { business_type: profile?.business_type || '', rating: profile?.rating || '' }
    KYC_DOCS.forEach(([, nk, ek, extras]) => {
      f[nk] = profile?.[nk] || ''; f[ek] = profile?.[ek] || ''
      extras.forEach(([k]) => { f[k] = profile?.[k] || '' })
    })
    setKycForm(f); setKycEdit(true)
  }
  const saveKyc = async () => {
    try {
      const updated = await crmApi.updateProfile(acc, kycForm)
      setData((d: any) => ({ ...d, profile: { ...(d.profile || { account_no: acc }), ...updated } }))
      setKycEdit(false); toast.success('KYC updated')
      loadCompleteness()
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const loadCompleteness = async () => {
    try {
      const c = await crmApi.completeness(acc)
      setComp(c)
      setData((d: any) => ({ ...d, profile: { ...(d.profile || { account_no: acc }), profile_completeness: `${c.percent}%` } }))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const doUpload = async () => {
    if (!upFiles.length) { toast.error('Choose file(s)'); return }
    try {
      const created: any[] = []
      for (const f of upFiles) created.push(await crmApi.uploadAttachment(acc, f, upOpts))
      setData((d: any) => ({ ...d, attachments: [...created, ...(d.attachments || [])] }))
      setUpFiles([]); setUpOpts({ facility_id: '', row_index: '', is_shared: false })
      toast.success(`${created.length} document(s) uploaded`)
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const openAttachment = async (a: any) => {
    try {
      await downloadFile(`/api/crm/attachments/${a.id}/download`, a.original_name || a.file_name || 'document')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeAttachment = async (aid: string) => {
    if (!confirm('Remove this document?')) return
    try {
      await crmApi.deleteAttachment(aid)
      setData((d: any) => ({ ...d, attachments: (d.attachments || []).filter((a: any) => a.id !== aid) }))
      toast.success('Document removed')
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
  const addProperty = async () => {
    try {
      const body: any = { ...np }
      if (body.valuation) body.valuation = Number(body.valuation)
      if (body.mortgage_amount) body.mortgage_amount = Number(body.mortgage_amount)
      const p = await crmApi.addProperty(acc, body)
      setData((d: any) => ({ ...d, properties: [...(d.properties || []), p], summary: { ...d.summary, total_properties: (d.summary?.total_properties || 0) + 1, total_mortgage_amount: (d.summary?.total_mortgage_amount || 0) + Number(p.mortgage_amount || 0) } }))
      setNp({ valuation_currency: 'AED', country: 'UAE' }); setShowPropForm(false)
      toast.success('Property added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeProperty = async (pid: string) => {
    if (!confirm('Remove this property?')) return
    try {
      await crmApi.deleteProperty(pid)
      setData((d: any) => ({ ...d, properties: (d.properties || []).filter((x: any) => x.id !== pid), summary: { ...d.summary, total_properties: Math.max(0, (d.summary?.total_properties || 1) - 1) } }))
      toast.success('Property removed')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addFd = async () => {
    if (!nfd.fd_number && !nfd.amount) { toast.error('FD number or amount required'); return }
    try {
      const body: any = { ...nfd }
      if (body.amount) body.amount = Number(body.amount)
      const f = await crmApi.addFixedDeposit(acc, body)
      setData((d: any) => ({ ...d, fixed_deposits: [...(d.fixed_deposits || []), f], summary: { ...d.summary, total_fixed_deposits: (d.summary?.total_fixed_deposits || 0) + 1, total_fd_amount: (d.summary?.total_fd_amount || 0) + Number(f.amount || 0) } }))
      setNfd({ currency: 'AED' })
      toast.success('Fixed deposit added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeFd = async (fid: string) => {
    if (!confirm('Remove this fixed deposit?')) return
    try {
      await crmApi.deleteFixedDeposit(fid)
      setData((d: any) => ({ ...d, fixed_deposits: (d.fixed_deposits || []).filter((x: any) => x.id !== fid), summary: { ...d.summary, total_fixed_deposits: Math.max(0, (d.summary?.total_fixed_deposits || 1) - 1) } }))
      toast.success('Fixed deposit removed')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addPartnerRow = async () => {
    if (!npt.name?.trim()) { toast.error('Partner name required'); return }
    try {
      const p = await crmApi.addPartner(acc, npt)
      setData((d: any) => ({ ...d, partners: [...(d.partners || []), p], summary: { ...d.summary, total_partners: (d.summary?.total_partners || 0) + 1 } }))
      setNpt({})
      toast.success('Partner added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removePartner = async (pid: string) => {
    if (!confirm('Remove this partner?')) return
    try {
      await crmApi.deletePartner(pid)
      setData((d: any) => ({ ...d, partners: (d.partners || []).filter((x: any) => x.id !== pid), summary: { ...d.summary, total_partners: Math.max(0, (d.summary?.total_partners || 1) - 1) } }))
      toast.success('Partner removed')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const printSummary = () => {
    document.body.classList.add('print-summary')
    setTimeout(() => { window.print(); document.body.classList.remove('print-summary') }, 60)
  }
  const emailSummary = async () => {
    const to = window.prompt('Email the credit summary to:')
    if (!to || !to.trim()) return
    try {
      const r = await crmApi.emailSummary(acc, to.trim())
      toast.success(r?.message || 'Summary emailed')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const downloadPdf = async () => {
    try {
      await downloadFile(`/api/crm/summary/${encodeURIComponent(acc)}/export.pdf`, `credit-summary-${acc}.pdf`)
    } catch (e) { toast.error(parseApiError(e)) }
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
          <div className="mb-2 flex items-center gap-2 justify-end">
            <button onClick={emailSummary} type="button" className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-sm">
              <Mail size={14} /> Email
            </button>
            <button onClick={downloadPdf} type="button" className="flex items-center gap-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg px-3 py-1.5 text-sm">
              <FileText size={14} /> PDF
            </button>
            <button onClick={printSummary} type="button" className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-lg px-3 py-1.5 text-sm">
              <FileText size={14} /> Print Summary
            </button>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm ${statusBadge(customer.status)}`}>{customer.status}</span>
          <div className="text-xs text-gray-400 mt-1">Completeness: {completeness}</div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
        <Card icon={<Wallet size={15} />} label="Facilities" value={summary.total_facilities} sub={`${summary.active_facilities || 0} active`} />
        <Card icon={<Wallet size={15} />} label="Total Exposure" value={money(summary.total_exposure)} />
        <Card icon={<ShieldCheck size={15} />} label="Guarantors" value={summary.total_guarantors ?? guarantors.length} />
        <Card icon={<Building2 size={15} />} label="Properties" value={properties.length} />
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
          <div className="mb-3 flex items-center gap-3 flex-wrap">
            <button onClick={loadCompleteness} type="button" className="text-sm text-blue-600 hover:underline">Check completeness</button>
            {comp && (
              <span className="text-sm">
                <b>{comp.percent}%</b> complete · {comp.filled}/{comp.total} fields
                {comp.missing?.length
                  ? <span className="text-amber-600"> · Missing: {comp.missing.join('، ')}</span>
                  : <span className="text-green-600"> · همه‌چیز تکمیل است ✓</span>}
              </span>
            )}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {KYC_DOCS.map(([title, nk, ek, extras]) => (
              <div key={nk} className="border border-gray-200 rounded-lg p-3">
                <div className="text-xs text-gray-400">{title}</div>
                {kycEdit ? (
                  <>
                    <input value={kycForm[nk] || ''} onChange={(e) => setKycForm((s: any) => ({ ...s, [nk]: e.target.value }))}
                      placeholder="Number" className="w-full border border-gray-300 rounded px-2 py-1 text-sm mt-1" />
                    <input value={kycForm[ek] || ''} onChange={(e) => setKycForm((s: any) => ({ ...s, [ek]: e.target.value }))}
                      placeholder="Expiry (YYYY-MM-DD)" className="w-full border border-gray-300 rounded px-2 py-1 text-xs mt-1" />
                    {extras.map(([k, ph]) => (
                      <input key={k} value={kycForm[k] || ''} onChange={(e) => setKycForm((s: any) => ({ ...s, [k]: e.target.value }))}
                        placeholder={ph} className="w-full border border-gray-300 rounded px-2 py-1 text-xs mt-1" />
                    ))}
                  </>
                ) : (
                  <>
                    <div className="font-medium text-sm">{val(profile?.[nk])}</div>
                    <div className="text-xs text-gray-500 mt-1">Expiry: {val(profile?.[ek])}</div>
                    {extras.filter(([k]) => profile?.[k]).map(([k, ph]) => (
                      <div key={k} className="text-xs text-gray-500 mt-0.5">{ph}: {val(profile?.[k])}</div>
                    ))}
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
              <option value="overdraft">Overdraft</option>
              <option value="loan">Loan</option>
              <option value="cheque_discounting">Cheque Discounting</option>
              <option value="trust_receipt">Trust Receipt</option>
              <option value="lc">LC</option>
              <option value="lc_sight">LC Sight</option>
              <option value="lc_usance">LC Usance</option>
              <option value="lg">LG</option>
              <option value="log">Letter of Guarantee (LoG)</option>
              <option value="other">Other</option>
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
          <Section title="Security Cheques & Fixed Deposits">
            <Grid items={[
              ['Cheques Total (AED)', chequeTotal ? chequeTotal.toLocaleString() : (pdata.Sec_Cheques_AED_Total || '—')],
              ['Cheques Count', chequeRows.length || pdata.Sec_Cheques_Count || '0'],
              ['Fixed Deposits (FD)', fdRows.length || '0'],
              ['Collateral (AED)', pdata.Sec_Collateral_AED], ['Underlien (AED)', pdata.Sec_Underlien_AED],
              ['Borrower Chq No', pdata.Borrower_ChqNo],
            ]} />
            {chequeRows.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-500 mb-1.5">Security cheques held ({chequeRows.length})</p>
                <SimpleTable head={['Guarantor', 'Cheque No', 'Amount (AED)', 'Issuing Bank', 'FD Ref']}
                  rows={chequeRows.map((g: any) => [g.guarantor_name || g.customer_name || '—', g.cheque_no || '—', g.cheque_amount ? num(g.cheque_amount).toLocaleString() : '—', g.issuing_bank || '—', fdShown(g.fd) ? g.fd : '—'])}
                  empty="" />
              </div>
            )}
            {fdRows.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-gray-500 mb-1.5">Fixed deposits held as security ({fdRows.length})</p>
                <SimpleTable head={['Holder', 'FD Reference', 'Linked Cheque', 'Issuing Bank']}
                  rows={fdRows.map((g: any) => [g.guarantor_name || g.customer_name || '—', g.fd, g.cheque_no || '—', g.issuing_bank || '—'])}
                  empty="" />
              </div>
            )}
          </Section>

          <Section title={`Fixed Deposits (${fixedDeposits.length})`}>
            <div className="grid grid-cols-2 lg:grid-cols-7 gap-2 mb-3">
              {[['fd_number', 'FD Number'], ['amount', 'Amount'], ['currency', 'Currency'], ['open_date', 'Open Date'], ['maturity_date', 'Maturity'], ['rate', 'Rate']].map(([k, ph]) => (
                <input key={k} value={nfd[k] || ''} onChange={(e) => setNfd((s: any) => ({ ...s, [k]: e.target.value }))}
                  placeholder={ph} inputMode={k === 'amount' ? 'numeric' : undefined}
                  className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
              ))}
              <button onClick={addFd} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm font-medium">Add FD</button>
            </div>
            {fixedDeposits.length === 0 ? <Empty>No fixed deposits recorded</Empty> : (
              <div className="overflow-auto">
                <table className="w-full text-sm whitespace-nowrap">
                  <thead className="bg-gray-50"><tr className="text-left text-gray-500">
                    {['FD Number', 'Amount', 'Currency', 'Open', 'Maturity', 'Rate', ''].map((h, i) => <th key={i} className="px-3 py-2">{h}</th>)}
                  </tr></thead>
                  <tbody className="divide-y">
                    {fixedDeposits.map((f: any) => (
                      <tr key={f.id}>
                        <td className="px-3 py-1.5">{val(f.fd_number)}</td>
                        <td className="px-3 py-1.5 tabular-nums">{f.amount != null ? Number(f.amount).toLocaleString() : '—'}</td>
                        <td className="px-3 py-1.5">{val(f.currency)}</td>
                        <td className="px-3 py-1.5">{val(f.open_date)}</td>
                        <td className="px-3 py-1.5">{val(f.maturity_date)}</td>
                        <td className="px-3 py-1.5">{val(f.rate)}</td>
                        <td className="px-3 py-1.5"><button onClick={() => removeFd(f.id)} type="button" className="text-xs text-red-600 hover:underline">Remove</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

          {securities.length > 0 && (
            <Section title={`Securities Register — Securities List (${securities.length} entries · ${new Set(securities.map((s: any) => s.year)).size} years)`}>
              <p className="text-xs text-gray-500 mb-2">سابقهٔ کاملِ اوراقِ ثبت‌شده در لیستِ سالانه · مجموعِ مبلغِ چک‌ها: <b>AED {secTotal.toLocaleString()}</b></p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs whitespace-nowrap">
                  <thead className="bg-gray-50 text-gray-500 text-left">
                    <tr>{['Year', 'Date', 'Cheque No', 'Amount (AED)', 'Bank', 'FD', 'U/Taking', 'Guarantee', 'Cr.Facility', 'Offer', 'Property', 'Mortgage', 'Stored', 'Taken Out', 'Remarks'].map((h) => <th key={h} className="px-2 py-1.5 font-medium">{h}</th>)}</tr>
                  </thead>
                  <tbody className="divide-y">
                    {securities.map((s: any, i: number) => (
                      <tr key={i} className="hover:bg-gray-50 align-top">
                        <td className="px-2 py-1 font-semibold">{s.year}<div className="text-[10px] font-normal text-gray-400 capitalize">{s.segment}</div></td>
                        <td className="px-2 py-1">{val(s.date)}</td>
                        <td className="px-2 py-1 whitespace-pre-line">{val(s.cheque_no)}</td>
                        <td className="px-2 py-1 text-right tabular-nums">{s.cheque_amount_num ? Number(s.cheque_amount_num).toLocaleString() : val(s.cheque_amount)}</td>
                        <td className="px-2 py-1 whitespace-pre-line">{val(s.issuing_bank)}</td>
                        <td className="px-2 py-1">{fdShown(s.fd) ? s.fd : '—'}</td>
                        <td className="px-2 py-1 text-center">{flag(s.undertaking)}</td>
                        <td className="px-2 py-1 text-center">{flag(s.guarantee)}</td>
                        <td className="px-2 py-1 text-center">{flag(s.credit_facility)}</td>
                        <td className="px-2 py-1 text-center">{flag(s.original_offer)}</td>
                        <td className="px-2 py-1 whitespace-pre-line">{val(s.property_no)}</td>
                        <td className="px-2 py-1">{val(s.mortgage_aed)}</td>
                        <td className="px-2 py-1">{val(s.stored_date)}</td>
                        <td className="px-2 py-1">{val(s.taken_out_date)}</td>
                        <td className="px-2 py-1 max-w-[160px] whitespace-normal">{val(s.remarks)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          <Section title={`Mortgaged Properties (${properties.length})`}>
            <div className="flex justify-end mb-2">
              <button onClick={() => setShowPropForm((v) => !v)} type="button" className="text-sm text-blue-600 hover:underline">
                {showPropForm ? 'Close' : '+ Add property'}
              </button>
            </div>
            {showPropForm && (
              <div className="border border-gray-200 rounded-lg p-3 mb-3 bg-gray-50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {([
                    ['plate_no', 'Plate / Reg No'], ['mortgage_deed_no', 'Mortgage Deed No'], ['city', 'City'], ['country', 'Country (UAE/Iran)'],
                    ['address', 'Address'], ['prop_type', 'Type'], ['building_age', 'Building Age'], ['land_area', 'Land Area (m²)'],
                    ['cnbc', 'CNBC'], ['valuation', 'Valuation'], ['valuation_currency', 'Val. Currency'], ['mortgage_amount', 'Mortgage Amount'],
                    ['mortgage_date', 'Mortgage Date'], ['last_valuation_date', 'Last Valuation Date'], ['insurance_no', 'Insurance No'], ['insurance_expiry', 'Insurance Expiry'],
                  ] as [string, string][]).map(([k, ph]) => (
                    <input key={k} value={np[k] || ''} onChange={(e) => setNp((s: any) => ({ ...s, [k]: e.target.value }))}
                      placeholder={ph} inputMode={(k === 'valuation' || k === 'mortgage_amount') ? 'numeric' : undefined}
                      className="border border-gray-300 rounded px-2 py-1.5 text-sm" />
                  ))}
                </div>
                <input value={np.remarks || ''} onChange={(e) => setNp((s: any) => ({ ...s, remarks: e.target.value }))} placeholder="Remarks" className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm mt-2" />
                <div className="flex justify-end mt-2">
                  <button onClick={addProperty} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-1.5 text-sm font-medium">Save property</button>
                </div>
              </div>
            )}
            {properties.length === 0 ? <Empty>No mortgaged properties recorded</Empty> : (
              <div className="overflow-auto">
                <table className="w-full text-sm whitespace-nowrap">
                  <thead className="bg-gray-50"><tr className="text-left text-gray-500">
                    {['Plate', 'Deed No', 'City', 'Type', 'Valuation', 'Mortgage Amt', 'Insurance Expiry', ''].map((h, i) => <th key={i} className="px-3 py-2">{h}</th>)}
                  </tr></thead>
                  <tbody className="divide-y">
                    {properties.map((p: any) => (
                      <tr key={p.id}>
                        <td className="px-3 py-1.5">{val(p.plate_no)}</td>
                        <td className="px-3 py-1.5">{val(p.mortgage_deed_no)}</td>
                        <td className="px-3 py-1.5">{val(p.city)}{p.country ? ` · ${p.country}` : ''}</td>
                        <td className="px-3 py-1.5">{val(p.prop_type)}</td>
                        <td className="px-3 py-1.5 tabular-nums">{p.valuation != null ? `${p.valuation_currency || 'AED'} ${Number(p.valuation).toLocaleString()}` : '—'}</td>
                        <td className="px-3 py-1.5 tabular-nums">{p.mortgage_amount != null ? Number(p.mortgage_amount).toLocaleString() : '—'}</td>
                        <td className="px-3 py-1.5">{val(p.insurance_expiry)}</td>
                        <td className="px-3 py-1.5"><button onClick={() => removeProperty(p.id)} type="button" className="text-xs text-red-600 hover:underline">Remove</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

          <Section title={`Partners / Shareholders (${partnerList.length})`}>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 mb-3">
              {[['name', 'Partner name'], ['nationality', 'Nationality'], ['share', 'Share %']].map(([k, ph]) => (
                <input key={k} value={npt[k] || ''} onChange={(e) => setNpt((s: any) => ({ ...s, [k]: e.target.value }))}
                  placeholder={ph} className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
              ))}
              <button onClick={addPartnerRow} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm font-medium">Add</button>
            </div>
            {partnerRows.length === 0 && blobPartners.length > 0 && (
              <p className="text-xs text-amber-600 mb-2">نمایش از دادهٔ قدیمی (imported). برای ویرایش، به‌صورت ردیف‌های جدید اضافه کنید.</p>
            )}
            {partnerRows.length > 0 ? (
              <div className="overflow-auto">
                <table className="w-full text-sm whitespace-nowrap">
                  <thead className="bg-gray-50"><tr className="text-left text-gray-500">{['Name', 'Nationality', 'Share %', ''].map((h, i) => <th key={i} className="px-3 py-2">{h}</th>)}</tr></thead>
                  <tbody className="divide-y">
                    {partnerRows.map((p: any) => (
                      <tr key={p.id}>
                        <td className="px-3 py-1.5">{val(p.name)}</td>
                        <td className="px-3 py-1.5">{val(p.nationality)}</td>
                        <td className="px-3 py-1.5">{val(p.share)}</td>
                        <td className="px-3 py-1.5"><button onClick={() => removePartner(p.id)} type="button" className="text-xs text-red-600 hover:underline">Remove</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <SimpleTable head={['Name', 'Nationality', 'Share %']} rows={blobPartners} empty="No partners" />
            )}
          </Section>
        </div>
      )}

      {tab === 'checklist' && (
        <Section title="Credit-File Checklist (9 steps)">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <label className="text-xs text-gray-500">Checklist for:</label>
            <select value={chkFacility} onChange={(e) => setChkFacility(e.target.value)}
              className="border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm">
              <option value="">Account-level</option>
              {facilities.map((f: any) => (
                <option key={f.id} value={f.id}>{(f.name || (f.facility_type || '').toUpperCase() || 'Facility')} · {f.id}</option>
              ))}
            </select>
            {chkFacility
              ? <span className="text-xs text-amber-600">⌛ = در انتظار (هنگام ساختِ تسهیلات خودکار درج شد)</span>
              : <span className="text-xs text-gray-400">روی هر مرحله بزنید تا انجام‌شده/در‌انتظار شود (در Journal ثبت می‌شود).</span>}
          </div>
          <div className="space-y-1.5">
            {CHECKLIST_STEPS.map((s, i) => {
              const v = activeChecklist?.[`item${i + 1}`]
              const isDone = done(v)
              const hg = isHourglass(v)
              return (
                <button key={i} type="button" onClick={() => toggleStep(i + 1, isDone)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-colors ${isDone ? 'bg-green-50 border-green-200' : hg ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200 hover:bg-gray-50'}`}>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${isDone ? 'bg-green-600 text-white' : hg ? 'bg-amber-400 text-white' : 'bg-gray-200 text-gray-500'}`}>
                    {isDone ? '✓' : hg ? '⌛' : i + 1}
                  </span>
                  <span className={`flex-1 text-sm ${isDone ? 'text-green-800 font-medium' : 'text-gray-700'}`}>{s}</span>
                  <span className="text-xs text-gray-400">{isDone ? 'Done' : hg ? 'Pending' : '—'}</span>
                </button>
              )
            })}
          </div>
          {activeChecklist && <p className="text-xs text-gray-400 mt-3">Total {activeChecklist.total} · last action {val(activeChecklist.last_action)} by {val(activeChecklist.last_user)}</p>}
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
          <div className="flex flex-wrap items-center gap-2 mb-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <input type="file" multiple onChange={(e) => setUpFiles(Array.from(e.target.files || []))} className="text-sm" />
            <select value={upOpts.facility_id} onChange={(e) => setUpOpts((s: any) => ({ ...s, facility_id: e.target.value }))}
              className="border border-gray-300 rounded-lg px-2.5 py-2 text-sm">
              <option value="">No facility</option>
              {facilities.map((f: any) => <option key={f.id} value={f.id}>{(f.name || (f.facility_type || '').toUpperCase() || 'Facility')} · {f.id}</option>)}
            </select>
            <input value={upOpts.row_index} onChange={(e) => setUpOpts((s: any) => ({ ...s, row_index: e.target.value }))}
              placeholder="Row (e.g. 11)" className="w-28 border border-gray-300 rounded-lg px-2.5 py-2 text-sm" />
            <label className="flex items-center gap-1.5 text-sm text-gray-600">
              <input type="checkbox" checked={upOpts.is_shared} onChange={(e) => setUpOpts((s: any) => ({ ...s, is_shared: e.target.checked }))} />
              Shared across checklists
            </label>
            <button onClick={doUpload} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium">Upload</button>
          </div>
          {attachments.length === 0 ? <Empty>No attachments</Empty> : (
            <div className="overflow-auto">
              <table className="w-full text-sm whitespace-nowrap">
                <thead className="bg-gray-50"><tr className="text-left text-gray-500">{['Document', 'Facility', 'Row', 'Uploaded', 'By', 'Size', 'Shared', ''].map((h, i) => <th key={i} className="px-3 py-2">{h}</th>)}</tr></thead>
                <tbody className="divide-y">
                  {attachments.map((a: any) => (
                    <tr key={a.id}>
                      <td className="px-3 py-1.5"><button onClick={() => openAttachment(a)} type="button" className="text-blue-600 hover:underline">{a.original_name || a.file_name}</button></td>
                      <td className="px-3 py-1.5">{val(a.facility_id)}</td>
                      <td className="px-3 py-1.5">{val(a.row_index)}</td>
                      <td className="px-3 py-1.5">{(a.upload_date || '').slice(0, 10)}</td>
                      <td className="px-3 py-1.5">{val(a.uploaded_by)}</td>
                      <td className="px-3 py-1.5">{a.file_size ? `${Math.round(Number(a.file_size) / 1024)} KB` : '—'}</td>
                      <td className="px-3 py-1.5">{done(a.is_shared) ? 'Yes' : 'No'}</td>
                      <td className="px-3 py-1.5"><button onClick={() => removeAttachment(a.id)} type="button" className="text-xs text-red-600 hover:underline">Remove</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-gray-400 mt-2">مستندات روی سرور ذخیره و از همین‌جا قابلِ باز‌کردن‌اند. «Shared» یعنی در همهٔ چک‌لیست‌های این حساب در دسترس است. (ردیف‌های قدیمیِ importشده فقط متادیتا دارند.)</p>
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

        <h4>Securities & Collateral Summary</h4>
        <table className="kv"><tbody>
          <tr><td><b>Cheques Total:</b> AED {chequeTotal.toLocaleString()}</td><td><b>Cheques:</b> {chequeRows.length}</td><td><b>Fixed Deposits:</b> {fixedDeposits.length || fdRows.length}</td></tr>
          <tr><td><b>Collateral (AED):</b> {val(pdata.Sec_Collateral_AED)}</td><td><b>Underlien (AED):</b> {val(pdata.Sec_Underlien_AED)}</td><td><b>Outstanding:</b> {money(summary.total_outstanding)}</td></tr>
        </tbody></table>

        {isCorporate && partnerList.length > 0 && (<><h4>Partners / Shareholders</h4>
        <table><tbody>
          <tr><th>Name</th><th>Nationality</th><th>Share %</th></tr>
          {partnerList.map((p: any, i: number) => <tr key={i}><td>{val(p[0])}</td><td>{val(p[1])}</td><td>{val(p[2])}</td></tr>)}
        </tbody></table></>)}

        {checklist && (<><h4>Credit-File Checklist</h4>
        <table className="kv"><tbody>
          <tr><td><b>Completed:</b> {CHECKLIST_STEPS.filter((_, i) => done(checklist?.[`item${i + 1}`])).length} / {CHECKLIST_STEPS.length}</td>
          <td><b>Last action:</b> {val(checklist.last_action)}</td><td><b>By:</b> {val(checklist.last_user)}</td></tr>
        </tbody></table></>)}

        {propsForSummary.length > 0 && (<><h4>Mortgaged Properties ({propsForSummary.length})</h4>
        <table><tbody>
          <tr><th>Deed</th><th>City</th><th>Type</th><th>Valuation</th></tr>
          {propsForSummary.map((p: any, i: number) => <tr key={i}><td>{val(p.deed_no)}</td><td>{val(p.city)}</td><td>{val(p.type)}</td><td>{p.valuation != null ? `${p.currency || 'AED'} ${Number(p.valuation).toLocaleString()}` : '—'}</td></tr>)}
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
