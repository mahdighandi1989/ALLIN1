```tsx
'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { facilitiesApi, customersApi } from '@/lib/api'
import { Facility, FacilityList, Customer } from '@/types'
import { Plus, Edit, Trash2, X, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function FacilitiesPage() {
  const [data, setData] = useState<FacilityList | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editingFacility, setEditingFacility] = useState<Facility | null>(null)
  const [deleteModal, setDeleteModal] = useState<{ show: boolean; facility: Facility | null }>({
    show: false,
    facility: null
  })

  useEffect(() => {
    loadData()
  }, [page])

  const loadData = async () => {
    try {
      const [facilitiesData, customersData] = await Promise.all([
        facilitiesApi.list({ page, page_size: 20 }),
        customersApi.list({ page_size: 100 }),
      ])
      setData(facilitiesData)
      setCustomers(customersData.items)
    } catch (error) {
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteClick = (facility: Facility) => {
    setDeleteModal({ show: true, facility })
  }

  const handleDeleteConfirm = async () => {
    if (!deleteModal.facility) return
    
    try {
      await facilitiesApi.delete(deleteModal.facility.id)
      toast.success('Facility deleted successfully')
      setDeleteModal({ show: false, facility: null })
      loadData()
    } catch (error) {
      toast.error('Failed to delete facility')
    }
  }

  const handleDeleteCancel = () => {
    setDeleteModal({ show: false, facility: null })
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Facilities</h2>
        <button
          onClick={() => { setEditingFacility(null); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          Add Facility
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Customer</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Amount</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Outstanding</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Expiry</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((facility) => (
                  <tr key={facility.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">{facility.customer_name || facility.customer_id}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs uppercase">
                        {facility.facility_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{formatCurrency(facility.amount, facility.currency)}</td>
                    <td className="px-4 py-3 text-sm">{formatCurrency(facility.outstanding, facility.currency)}</td>
                    <td className="px-4 py-3 text-sm">{facility.expiry_date || '-'}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        facility.status === 'active' ? 'bg-green-100 text-green-700' :
                        facility.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        facility.status === 'closed' ? 'bg-gray-100 text-gray-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {facility.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => { setEditingFacility(facility); setShowForm(true) }}
                        className="text-gray-500 hover:text-blue-600 mr-2"
                        title="Edit facility"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteClick(facility)}
                        className="text-gray-500 hover:text-red-600"
                        title="Delete facility"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="px-4 py-3 border-t flex justify-between items-center">
              <span className="text-sm text-gray-500">
                Page {data.page} of {Math.ceil(data.total / data.page_size)}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(data.total / data.page_size)}
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

      {/* Delete Confirmation Modal */}
      {deleteModal.show && deleteModal.facility && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-red-100 rounded-full">
                  <AlertTriangle className="text-red-600" size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Delete Facility</h3>
                  <p className="text-sm text-gray-500">This action cannot be undone</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-700">
                  Are you sure you want to delete the facility{' '}
                  <span className="font-medium">
                    {deleteModal.facility.name || `${deleteModal.facility.facility_type} - ${deleteModal.facility.customer_name || deleteModal.facility.customer_id}`}
                  </span>
                  ?
                </p>
                {deleteModal.facility.outstanding > 0 && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      <strong>Warning:</strong> This facility has an outstanding balance of{' '}
                      {formatCurrency(deleteModal.facility.outstanding, deleteModal.facility.currency)}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleDeleteCancel}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete Facility
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <FacilityForm
          facility={editingFacility}
          customers={customers}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); loadData() }}
        />
      )}
    </Layout>
  )
}

function FacilityForm({
  facility,
  customers,
  onClose,
  onSaved,
}: {
  facility: Facility | null
  customers: Customer[]
  onClose: () => void
  onSaved: () => void
}) {
  const [form, setForm] = useState({
    customer_id: facility?.customer_id || '',
    facility_type: facility?.facility_type || 'loan',
    name: facility?.name || '',
    amount: facility?.amount?.toString() || '',
    currency: facility?.currency || 'AED',
    start_date: facility?.start_date || '',
    expiry_date: facility?.expiry_date || '',
    interest_rate: facility?.interest_rate?.toString() || '',
    notes: facility?.notes || '',
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const data = {
        ...form,
        amount: parseFloat(form.amount),
        interest_rate: form.interest_rate ? parseFloat(form.interest_rate) : null,
        start_date: form.start_date || null,
        expiry_date: form.expiry_date || null,
      }
      if (facility) {
        await facilitiesApi.update(facility.id, data)
        toast.success('Facility updated successfully')
      } else {
        await facilitiesApi.create(data)
        toast.success('Facility created successfully')
      }
      onSaved()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save facility')
    } finally {
      setSaving(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b sticky top-0 bg-white flex justify-between items-center">
          <h3 className="text-lg font-semibold">{facility ? 'Edit Facility' : 'New Facility'}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
            title="Close"
          >
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Customer *</label>
            <select
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={!!facility}
            >
              <option value="">Select Customer</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>{c.name} ({c.account_no})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Facility Type *</label>
            <select
              value={form.facility_type}
              onChange={(e) => setForm({ ...form, facility_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="loan">Loan</option>
              <option value="overdraft">Overdraft</option>
              <option value="lc">LC</option>
              <option value="lg">LG</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter facility name"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Amount *</label>
              <input
                type="