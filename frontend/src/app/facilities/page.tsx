'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { facilitiesApi, customersApi, parseApiError } from '@/lib/api'
import { Facility, FacilityList, FacilityForm as FacilityFormData, Customer } from '@/types'
import { Plus, Search, Edit, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

const FACILITY_TYPES: FacilityFormData['facility_type'][] = [
  'loan',
  'overdraft',
  'lc',
  'lg',
  'other',
]

export default function FacilitiesPage() {
  const router = useRouter()
  const [data, setData] = useState<FacilityList | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Facility | null>(null)

  useEffect(() => {
    loadFacilities()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const loadFacilities = async () => {
    try {
      setLoading(true)
      const result = await facilitiesApi.list({
        page,
        page_size: 20,
        search: search || undefined,
      })
      setData(result)
    } catch (error) {
      console.error('Failed to load facilities:', error)
      toast.error(parseApiError(error))
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadFacilities()
  }

  const handleDelete = async (facility: Facility) => {
    if (!confirm(`Delete facility "${facility.name || facility.id}"?`)) return
    try {
      await facilitiesApi.delete(facility.id)
      toast.success('Facility deleted')
      loadFacilities()
    } catch (error) {
      console.error('Failed to delete facility:', error)
      toast.error(parseApiError(error))
    }
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Facilities</h2>
        <button
          onClick={() => {
            setEditing(null)
            setShowForm(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          Add Facility
        </button>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by facility name..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button type="submit" className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
          <Search size={18} />
        </button>
      </form>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="facilities-content">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Amount</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Expiry</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((facility) => (
                  <tr key={facility.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">
                      <button
                        type="button"
                        data-testid={`view-facility-${facility.id}`}
                        onClick={() => router.push(`/facility-detail?id=${facility.id}`)}
                        className="text-blue-600 hover:underline"
                      >
                        {facility.name || facility.facility_type.toUpperCase()}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm uppercase">{facility.facility_type}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      {facility.currency} {Number(facility.amount).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          facility.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : facility.status === 'closed'
                            ? 'bg-gray-100 text-gray-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}
                      >
                        {facility.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{facility.expiry_date || '-'}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          setEditing(facility)
                          setShowForm(true)
                        }}
                        className="text-gray-500 hover:text-blue-600 mr-2"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(facility)}
                        className="text-gray-500 hover:text-red-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="px-4 py-3 border-t flex justify-between items-center">
              <span className="text-sm text-gray-500">
                Page {data.page ?? 1} of{' '}
                {Math.ceil((data.total ?? 0) / (data.page_size || 1)) || 1}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil((data.total ?? 0) / (data.page_size || 1))}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="py-12 text-center text-gray-500">No facilities found</div>
        )}
      </div>

      {showForm && (
        <FacilityFormModal
          facility={editing}
          onClose={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false)
            loadFacilities()
          }}
        />
      )}
    </Layout>
  )
}

function FacilityFormModal({
  facility,
  onClose,
  onSaved,
}: {
  facility: Facility | null
  onClose: () => void
  onSaved: () => void
}) {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [form, setForm] = useState<FacilityFormData>({
    customer_id: facility?.customer_id || '',
    facility_type: (facility?.facility_type as FacilityFormData['facility_type']) || 'loan',
    name: facility?.name || '',
    amount: facility?.amount ?? 0,
    currency: facility?.currency || 'AED',
    interest_rate: facility?.interest_rate ?? undefined,
    expiry_date: facility?.expiry_date || undefined,
    notes: facility?.notes || '',
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    customersApi
      .list({ page: 1, page_size: 100 })
      .then((res) => setCustomers(res.items))
      .catch(() => setCustomers([]))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (facility) {
        await facilitiesApi.update(facility.id, form)
        toast.success('Facility updated')
      } else {
        await facilitiesApi.create(form)
        toast.success('Facility created')
      }
      onSaved()
    } catch (error) {
      console.error('Failed to save facility:', error)
      toast.error(parseApiError(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">
            {facility ? 'Edit Facility' : 'New Facility'}
          </h3>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Customer *</label>
            <select
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              required
              disabled={!!facility}
            >
              <option value="">Select a customer…</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.account_no})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Type</label>
              <select
                value={form.facility_type}
                onChange={(e) =>
                  setForm({
                    ...form,
                    facility_type: e.target.value as FacilityFormData['facility_type'],
                  })
                }
                className="w-full px-3 py-2 border rounded-lg"
              >
                {FACILITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Currency</label>
              <input
                type="text"
                value={form.currency}
                maxLength={3}
                onChange={(e) =>
                  setForm({ ...form, currency: e.target.value.toUpperCase() })
                }
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Amount *</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Interest Rate %</label>
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={form.interest_rate ?? ''}
                onChange={(e) =>
                  setForm({
                    ...form,
                    interest_rate: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Expiry Date</label>
            <input
              type="date"
              value={form.expiry_date ?? ''}
              onChange={(e) =>
                setForm({ ...form, expiry_date: e.target.value || undefined })
              }
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows={2}
            />
          </div>
          <div className="flex gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
