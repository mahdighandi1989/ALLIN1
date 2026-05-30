'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { customersApi, parseApiError } from '@/lib/api'
import { Customer, CustomerList, CustomerForm as CustomerFormData } from '@/types'
import { Plus, Search, Edit, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CustomersPage() {
  const [data, setData] = useState<CustomerList | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)

  useEffect(() => {
    loadCustomers()
  }, [page])

  const loadCustomers = async () => {
    try {
      setLoading(true)
      const result = await customersApi.list({ page, page_size: 20, search: search || undefined })
      setData(result)
    } catch (error) {
      console.error('Failed to load customers:', error)
      toast.error('Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadCustomers()
  }

  const handleDelete = async (customer: Customer) => {
    if (!confirm(`Delete "${customer.name}"?`)) return
    try {
      await customersApi.delete(customer.id)
      toast.success('Customer deleted')
      loadCustomers()
    } catch (error) {
      console.error('Failed to delete customer:', error)
      toast.error('Failed to delete')
    }
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Customers</h2>
        <button
          type="button"
          data-testid="add-customer-btn"
          onClick={() => { setEditingCustomer(null); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          Add Customer
        </button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6 flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or account..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button type="submit" className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">
          <Search size={18} />
        </button>
      </form>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="customers-content">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Account No</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Branch</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{customer.account_no}</td>
                    <td className="px-4 py-3 text-sm font-medium">{customer.name}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        customer.account_type === 'corporate' ? 'bg-purple-100 text-purple-700' :
                        customer.account_type === 'sme' ? 'bg-orange-100 text-orange-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {customer.account_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        customer.status === 'active' ? 'bg-green-100 text-green-700' :
                        customer.status === 'suspended' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {customer.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{customer.branch || '-'}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        data-testid={`edit-customer-${customer.id}`}
                        aria-label={`Edit ${customer.name}`}
                        onClick={() => { setEditingCustomer(customer); setShowForm(true) }}
                        className="text-gray-500 hover:text-blue-600 mr-2"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        type="button"
                        data-testid={`delete-customer-${customer.id}`}
                        aria-label={`Delete ${customer.name}`}
                        onClick={() => handleDelete(customer)}
                        className="text-gray-500 hover:text-red-600"
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
                Page {data.page ?? 1} of {Math.ceil((data.total ?? 0) / (data.page_size || 1)) || 1}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  data-testid="prev-page-btn"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  data-testid="next-page-btn"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil((data.total ?? 0) / (data.page_size || 1))}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="py-12 text-center text-gray-500">No customers found</div>
        )}
      </div>

      {/* Form Modal */}
      {showForm && (
        <CustomerForm
          customer={editingCustomer}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); loadCustomers() }}
        />
      )}
    </Layout>
  )
}

function CustomerForm({
  customer,
  onClose,
  onSaved,
}: {
  customer: Customer | null
  onClose: () => void
  onSaved: () => void
}) {
  const [form, setForm] = useState<CustomerFormData>({
    account_no: customer?.account_no || '',
    name: customer?.name || '',
    account_type: (customer?.account_type as CustomerFormData['account_type']) || 'retail',
    email: customer?.email || '',
    phone: customer?.phone || '',
    branch: customer?.branch || '',
    notes: customer?.notes || '',
  })
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (customer) {
        await customersApi.update(customer.id, form)
        toast.success('Customer updated')
      } else {
        await customersApi.create(form)
        toast.success('Customer created')
      }
      onSaved()
    } catch (error: any) {
      console.error('Failed to save customer:', error)
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
        className="bg-white rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold">{customer ? 'Edit Customer' : 'New Customer'}</h3>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Account Number *</label>
            <input
              type="text"
              value={form.account_no}
              onChange={(e) => setForm({ ...form, account_no: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              required
              disabled={!!customer}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name *</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Account Type</label>
            <select
              value={form.account_type}
              onChange={(e) =>
                setForm({
                  ...form,
                  account_type: e.target.value as CustomerFormData['account_type'],
                })
              }
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="retail">Retail</option>
              <option value="corporate">Corporate</option>
              <option value="sme">SME</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Branch</label>
            <input
              type="text"
              value={form.branch}
              onChange={(e) => setForm({ ...form, branch: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
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