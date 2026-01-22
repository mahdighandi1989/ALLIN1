/**
 * Customers Page v2.0
 * صفحه مدیریت مشتریان
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Layout from '@/components/Layout'
import DataTable, { Column } from '@/components/ui/DataTable'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import { customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { Users, Building2, User, MapPin, Search, Plus } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const customerFields: FormField[] = [
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
  { key: 'email', label: 'Email', type: 'email', group: 'Contact Information' },
  { key: 'phone', label: 'Phone', type: 'tel', group: 'Contact Information' },
  { key: 'mobile', label: 'Mobile', type: 'tel', group: 'Contact Information' },
  { key: 'address', label: 'Address', type: 'textarea', width: 'full', group: 'Contact Information' },
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
  { key: 'actions', label: 'Actions', type: 'actions', width: '100px' },
]

export default function CustomersPage() {
  const router = useRouter()
  const { isLoading, isAuthenticated } = useAuth()
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<any>(null)
  const [stats, setStats] = useState({ total: 0, active: 0, corporate: 0, branches: 0 })
  const [searchTerm, setSearchTerm] = useState('')
  const [pagination, setPagination] = useState({ skip: 0, limit: 50, total: 0 })

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  const fetchCustomers = async (skip = 0, search = searchTerm) => {
    setLoading(true)
    try {
      const response = await customersApi.list({ skip, limit: pagination.limit, search: search || undefined })
      const data = response.data

      const items = data.items || data || []
      setCustomers(items)

      setPagination(prev => ({
        ...prev,
        skip,
        total: data.total || items.length,
      }))

      // Calculate stats
      setStats({
        total: data.total || items.length,
        active: items.filter((c: any) => c.status === 'active').length,
        corporate: items.filter((c: any) => c.account_type === 'corporate').length,
        branches: new Set(items.map((c: any) => c.branch).filter(Boolean)).size,
      })
    } catch (error: any) {
      console.error('Error fetching customers:', error)
      toast.error('Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      fetchCustomers(0)
    }
  }, [isAuthenticated])

  const handleSearch = () => {
    fetchCustomers(0, searchTerm)
  }

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
      fetchCustomers(pagination.skip)
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
      fetchCustomers(pagination.skip)
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to save customer')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const currentPage = Math.floor(pagination.skip / pagination.limit) + 1
  const totalPages = Math.ceil(pagination.total / pagination.limit)

  return (
    <Layout>
      <Head>
        <title>Customers | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
            <p className="text-gray-500">Manage your customer database</p>
          </div>
          <button
            onClick={handleAdd}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            Add Customer
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-blue-50 rounded-xl">
              <Users className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-green-50 rounded-xl">
              <User className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold text-gray-900">{stats.active}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-purple-50 rounded-xl">
              <Building2 className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Corporate</p>
              <p className="text-2xl font-bold text-gray-900">{stats.corporate}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-orange-50 rounded-xl">
              <MapPin className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Branches</p>
              <p className="text-2xl font-bold text-gray-900">{stats.branches}</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search by name, account number, or email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              Search
            </button>
          </div>
        </div>

        {/* Data Table */}
        <DataTable
          columns={tableColumns}
          data={customers}
          loading={loading}
          onEdit={handleEdit}
          onView={handleView}
          onDelete={handleDelete}
        />

        {/* Pagination */}
        {pagination.total > 0 && (
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-600">
            <span>
              Showing {pagination.skip + 1} to {Math.min(pagination.skip + pagination.limit, pagination.total)} of {pagination.total}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => fetchCustomers(pagination.skip - pagination.limit)}
                disabled={pagination.skip === 0}
                className="px-4 py-2 border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
              <span className="px-4 py-2 bg-gray-100 rounded-lg">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => fetchCustomers(pagination.skip + pagination.limit)}
                disabled={pagination.skip + pagination.limit >= pagination.total}
                className="px-4 py-2 border border-gray-200 rounded-lg disabled:opacity-50 hover:bg-gray-50 transition-colors"
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
