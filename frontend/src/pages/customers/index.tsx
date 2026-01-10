/**
 * Customers Page
 * صفحه مدیریت مشتریان
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Layout from '@/components/Layout'
import DataTable, { Column } from '@/components/ui/DataTable'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import { customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { Users, Building2, User, MapPin } from 'lucide-react'

// Customer form fields - matching API structure
const customerFields: FormField[] = [
  // Basic Info
  { key: 'account_no', label: 'Account Number', type: 'text', required: true, group: 'Basic Information' },
  { key: 'customer_name', label: 'Customer Name', type: 'text', required: true, group: 'Basic Information' },
  { key: 'customer_name_ar', label: 'Name (Arabic/Persian)', type: 'text', group: 'Basic Information' },
  { key: 'account_type', label: 'Account Type', type: 'select', required: true, group: 'Basic Information', options: [
    { value: 'retail', label: 'Retail' },
    { value: 'corporate', label: 'Corporate' },
    { value: 'sme', label: 'SME' },
  ]},
  { key: 'branch', label: 'Branch', type: 'text', group: 'Basic Information' },
  { key: 'relationship_manager', label: 'Relationship Manager', type: 'text', group: 'Basic Information' },

  // Contact Info
  { key: 'email', label: 'Email', type: 'email', group: 'Contact Information' },
  { key: 'phone', label: 'Phone', type: 'tel', group: 'Contact Information' },
  { key: 'mobile', label: 'Mobile', type: 'tel', group: 'Contact Information' },
  { key: 'address', label: 'Address', type: 'textarea', width: 'full', group: 'Contact Information' },

  // Notes
  { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
]

const tableColumns: Column[] = [
  { key: 'account_no', label: 'Account No', sortable: true, width: '120px' },
  { key: 'customer_name', label: 'Name', sortable: true },
  { key: 'account_type', label: 'Type', sortable: true, render: (value) => (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
      value === 'corporate' ? 'bg-purple-100 text-purple-800' :
      value === 'retail' ? 'bg-blue-100 text-blue-800' :
      'bg-gray-100 text-gray-800'
    }`}>
      {value}
    </span>
  )},
  { key: 'branch', label: 'Branch', sortable: true },
  { key: 'email', label: 'Email' },
  { key: 'status', label: 'Status', sortable: true, render: (value) => (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
      value === 'active' ? 'bg-green-100 text-green-800' :
      value === 'inactive' ? 'bg-gray-100 text-gray-800' :
      value === 'suspended' ? 'bg-yellow-100 text-yellow-800' :
      'bg-red-100 text-red-800'
    }`}>
      {value}
    </span>
  )},
  { key: 'profile_completeness', label: 'Profile %', render: (value) => (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${
            value >= 70 ? 'bg-green-500' :
            value >= 40 ? 'bg-yellow-500' : 'bg-red-500'
          }`}
          style={{ width: `${value || 0}%` }}
        />
      </div>
      <span className="text-xs text-gray-600">{value || 0}%</span>
    </div>
  )},
  { key: 'actions', label: 'Actions', type: 'actions', width: '100px' },
]

export default function CustomersPage() {
  const router = useRouter()
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<any>(null)
  const [stats, setStats] = useState({ total: 0, active: 0, corporate: 0, branches: 0 })
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0, pages: 1 })

  const fetchCustomers = async (page = 1) => {
    setLoading(true)
    try {
      const response = await customersApi.list({ page, page_size: pagination.pageSize })
      const data = response.data

      const items = data.items || []
      setCustomers(items)

      setPagination({
        page: data.page || 1,
        pageSize: data.page_size || 20,
        total: data.total || 0,
        pages: data.pages || 1,
      })

      // Calculate stats
      const uniqueBranches = new Set(items.map((c: any) => c.branch).filter(Boolean))
      setStats({
        total: data.total || items.length,
        active: items.filter((c: any) => c.status === 'active').length,
        corporate: items.filter((c: any) => c.account_type === 'corporate').length,
        branches: uniqueBranches.size,
      })
    } catch (error: any) {
      console.error('Error fetching customers:', error)
      toast.error('Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCustomers()
  }, [])

  const handleAdd = () => {
    setEditingCustomer(null)
    setShowForm(true)
  }

  const handleEdit = (customer: any) => {
    setEditingCustomer(customer)
    setShowForm(true)
  }

  const handleView = (customer: any) => {
    router.push(`/customers/${customer.id}`)
  }

  const handleDelete = async (customer: any) => {
    if (!confirm(`Are you sure you want to delete "${customer.customer_name}"?`)) return

    try {
      await customersApi.delete(customer.id)
      toast.success('Customer deleted successfully')
      fetchCustomers(pagination.page)
    } catch (error) {
      toast.error('Failed to delete customer')
    }
  }

  const handleSubmit = async (data: Record<string, any>) => {
    try {
      if (editingCustomer) {
        await customersApi.update(editingCustomer.id, data)
        toast.success('Customer updated successfully')
      } else {
        await customersApi.create(data)
        toast.success('Customer created successfully')
      }
      setShowForm(false)
      fetchCustomers(pagination.page)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to save customer')
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-600">Manage your customer database</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Customers</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <User className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold">{stats.active}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Building2 className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Corporate</p>
              <p className="text-2xl font-bold">{stats.corporate}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <MapPin className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Branches</p>
              <p className="text-2xl font-bold">{stats.branches}</p>
            </div>
          </div>
        </div>

        {/* Data Table */}
        <DataTable
          columns={tableColumns}
          data={customers}
          loading={loading}
          onAdd={handleAdd}
          onEdit={handleEdit}
          onView={handleView}
          onDelete={handleDelete}
          addButtonText="Add Customer"
        />

        {/* Pagination Info */}
        {pagination.total > 0 && (
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>
              Showing {((pagination.page - 1) * pagination.pageSize) + 1} to {Math.min(pagination.page * pagination.pageSize, pagination.total)} of {pagination.total} customers
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => fetchCustomers(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1">
                Page {pagination.page} of {pagination.pages}
              </span>
              <button
                onClick={() => fetchCustomers(pagination.page + 1)}
                disabled={pagination.page >= pagination.pages}
                className="px-3 py-1 border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <DynamicForm
            title={editingCustomer ? 'Edit Customer' : 'Add New Customer'}
            fields={customerFields}
            initialData={editingCustomer || {}}
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
