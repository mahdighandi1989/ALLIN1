'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { facilitiesApi, parseApiError } from '@/lib/api'
import { Facility, FacilityForm as FacilityFormData } from '@/types'
import { ArrowLeft, Save, Pencil, X } from 'lucide-react'
import toast from 'react-hot-toast'

const FACILITY_TYPES: FacilityFormData['facility_type'][] = ['loan', 'overdraft', 'lc', 'lg', 'other']
const STATUSES = ['active', 'pending', 'inactive', 'closed', 'defaulted', 'written_off']

function money(n: number | null | undefined, cur = 'AED') {
  return `${cur} ${Number(n || 0).toLocaleString()}`
}

function FacilityDetailInner() {
  const params = useSearchParams()
  const router = useRouter()
  const id = params.get('id')

  const [facility, setFacility] = useState<Facility | null>(null)
  const [customerName, setCustomerName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<Record<string, any>>({})

  const load = async () => {
    if (!id) {
      setError('No facility specified')
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const d = await facilitiesApi.detail(id)
      setFacility(d.facility)
      setCustomerName(d.customer_name)
      setForm({
        name: d.facility.name ?? '',
        facility_type: d.facility.facility_type,
        amount: d.facility.amount,
        outstanding: d.facility.outstanding,
        currency: d.facility.currency,
        interest_rate: d.facility.interest_rate ?? '',
        status: d.facility.status,
        expiry_date: d.facility.expiry_date ?? '',
        notes: d.facility.notes ?? '',
      })
    } catch (e) {
      setError(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const save = async () => {
    if (!facility) return
    setSaving(true)
    try {
      const payload: Record<string, any> = {
        name: form.name || undefined,
        facility_type: form.facility_type,
        amount: parseFloat(form.amount) || 0,
        outstanding: form.outstanding === '' ? undefined : parseFloat(form.outstanding),
        currency: form.currency,
        interest_rate: form.interest_rate === '' ? undefined : parseFloat(form.interest_rate),
        status: form.status,
        expiry_date: form.expiry_date || undefined,
        notes: form.notes || undefined,
      }
      await facilitiesApi.update(facility.id, payload)
      toast.success('Facility updated')
      setEditing(false)
      await load()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
  }
  if (error || !facility) {
    return (
      <div className="max-w-lg mx-auto mt-8">
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4" data-testid="facility-detail-error">
          {error || 'Facility not found'}
        </div>
        <button onClick={() => router.push('/facilities')} className="mt-4 px-4 py-2 border rounded-lg">Back to Facilities</button>
      </div>
    )
  }

  const field = (label: string, key: string, type = 'text', opts?: string[]) => (
    <div>
      <p className="text-gray-500 text-sm">{label}</p>
      {editing ? (
        opts ? (
          <select value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            className="w-full px-2 py-1 border rounded mt-1">
            {opts.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        ) : (
          <input type={type} value={form[key]}
            onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            className="w-full px-2 py-1 border rounded mt-1" />
        )
      ) : (
        <p className="font-medium">{renderValue(key)}</p>
      )}
    </div>
  )

  function renderValue(key: string) {
    const v = (facility as any)[key]
    if (key === 'amount' || key === 'outstanding') return money(v, facility!.currency)
    if (key === 'interest_rate') return v != null ? `${v}%` : '-'
    return v || '-'
  }

  return (
    <div data-testid="facility-detail-content">
      <button onClick={() => router.push('/facilities')} className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft size={16} /> Back to Facilities
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">{facility.name || facility.facility_type.toUpperCase()}</h2>
          <p className="text-gray-500">
            {facility.id} · {customerName || 'Unknown customer'}
          </p>
        </div>
        {editing ? (
          <div className="flex gap-2">
            <button onClick={() => { setEditing(false); load() }} className="flex items-center gap-1 px-3 py-2 border rounded-lg">
              <X size={16} /> Cancel
            </button>
            <button onClick={save} disabled={saving} data-testid="save-facility"
              className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              <Save size={16} /> {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        ) : (
          <button onClick={() => setEditing(true)} data-testid="edit-facility"
            className="flex items-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50">
            <Pencil size={16} /> Edit
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 grid grid-cols-2 md:grid-cols-3 gap-5">
        {field('Name', 'name')}
        {field('Type', 'facility_type', 'text', FACILITY_TYPES as string[])}
        {field('Status', 'status', 'text', STATUSES)}
        {field('Amount', 'amount', 'number')}
        {field('Outstanding', 'outstanding', 'number')}
        {field('Interest Rate %', 'interest_rate', 'number')}
        {field('Currency', 'currency')}
        {field('Expiry Date', 'expiry_date', 'date')}
        {field('Notes', 'notes')}
      </div>
    </div>
  )
}

export default function FacilityDetailPage() {
  return (
    <Layout>
      <Suspense fallback={<div className="py-16 text-center text-gray-500">Loading…</div>}>
        <FacilityDetailInner />
      </Suspense>
    </Layout>
  )
}
