'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { customersApi, parseApiError, downloadFile } from '@/lib/api'
import { Customer, CustomerList, CustomerForm as CustomerFormData } from '@/types'
import { Plus, Search, Edit, Trash2, Download } from 'lucide-react'
import toast from 'react-hot-toast'

export default function CustomersPage() {
  const router = useRouter()
  const [data, setData] = useState<CustomerList | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [accountType, setAccountType] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  useEffect(() => {
    loadCustomers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, sortBy, sortOrder])

  const loadCustomers = async () => {
    try {
      setLoading(true)
      const result = await customersApi.list({
        page, page_size: 20,
        search: search || undefined,
        account_type: accountType || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      })
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

  const toggleOne = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    const ids = (data?.items ?? []).map((c) => c.id)
    setSelected((prev) => (ids.every((i) => prev.has(i)) ? new Set() : new Set(ids)))
  }

  const bulkDelete = async () => {
    const ids = Array.from(selected)
    if (ids.length === 0) return
    if (!confirm(`Delete ${ids.length} selected customer(s)?`)) return
    try {
      const { deleted } = await customersApi.bulkDelete(ids)
      toast.success(`${deleted} deleted`)
      setSelected(new Set())
      loadCustomers()
    } catch (error) {
      toast.error(parseApiError(error))
    }
  }

  const exportFiltered = (fmt: 'xlsx' | 'csv') => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (accountType) params.set('account_type', accountType)
    const qs = params.toString()
    downloadFile(`/api/customers/export.${fmt}${qs ? `?${qs}` : ''}`, `customers.${fmt}`)
      .catch((e) => toast.error(parseApiError(e)))
  }

  const allChecked = (data?.items?.length ?? 0) > 0 && data!.items.every((c) => selected.has(c.id))

  return (<div data-testid="customers-page">
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Customers</h2>
        <div className="flex gap-2">
          <button type="button" data-testid="export-customers-xlsx" onClick={() => exportFiltered('xlsx')}
            className="flex items-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
            <Download size={16} /> Excel
          </button>
          <button type="button" data-testid="export-customers-csv" onClick={() => exportFiltered('csv')}
            className="flex items-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
            <Download size={16} /> CSV
          </button>
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
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6 space-y-2" data-testid="customers-filters">
        <div className="flex gap-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, account or email..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1">
            <Search size={16} /> Filter
          </button>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <select value={accountType} onChange={(e) => setAccountType(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="">All types</option>
            <option value="retail">Retail</option>
            <option value="corporate">Corporate</option>
            <option value="sme">SME</option>
          </select>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="px-3 py-2 border rounded-lg">
            <option value="created_at">Sort: Created</option>
            <option value="name">Sort: Name</option>
            <option value="account_no">Sort: Account</option>
            <option value="status">Sort: Status</option>
          </select>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')} className="px-3 py-2 border rounded-lg">
            <option value="desc">Desc</option>
            <option value="asc">Asc</option>
          </select>
        </div>
      </form>

      {/* Bulk action bar */}
      {selected.size > 0 && (
        <div className="mb-3 flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-4 py-2" data-testid="bulk-bar">
          <span className="text-sm text-blue-800">{selected.size} selected</span>
          <div className="flex gap-2">
            <button onClick={() => setSelected(new Set())} className="px-3 py-1.5 text-sm border rounded-lg hover:bg-white">Clear</button>
            <button onClick={bulkDelete} data-testid="bulk-delete"
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">
              Delete selected
            </button>
          </div>
        </div>
      )}

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
                  <th className="px-4 py-3 w-10">
                    <input type="checkbox" checked={allChecked} onChange={toggleAll}
                      aria-label="Select all" data-testid="select-all" />
                  </th>
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
                  <tr key={customer.id} className={`hover:bg-gray-50 ${selected.has(customer.id) ? 'bg-blue-50' : ''}`}>
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selected.has(customer.id)}
                        onChange={() => toggleOne(customer.id)} aria-label={`Select ${customer.name}`} />
                    </td>
                    <td className="px-4 py-3 text-sm">{customer.account_no}</td>
                    <td className="px-4 py-3 text-sm font-medium">
                      <button
                        type="button"
                        data-testid={`view-customer-${customer.id}`}
                        onClick={() => router.push(`/customer-detail?id=${customer.id}`)}
                        className="text-blue-600 hover:underline"
                      >
                        {customer.name}
                      </button>
                    </td>
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
    </div>
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