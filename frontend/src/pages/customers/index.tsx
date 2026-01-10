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
import { Users, Building2, User } from 'lucide-react'

// Customer form fields - can be extended from settings
const customerFields: FormField[] = [
  // Basic Info
  { key: 'customer_type', label: 'Customer Type', type: 'select', required: true, group: 'Basic Information', options: [
    { value: 'individual', label: 'Individual' },
    { value: 'corporate', label: 'Corporate' },
    { value: 'sme', label: 'SME' },
  ]},
  { key: 'full_name', label: 'Full Name / Company Name', type: 'text', required: true, group: 'Basic Information' },
  { key: 'trade_name', label: 'Trade Name', type: 'text', group: 'Basic Information' },
  { key: 'email', label: 'Email', type: 'email', group: 'Basic Information' },
  { key: 'phone', label: 'Phone', type: 'tel', group: 'Basic Information' },
  { key: 'mobile', label: 'Mobile', type: 'tel', group: 'Basic Information' },

  // Identification
  { key: 'emirates_id', label: 'Emirates ID', type: 'text', group: 'Identification' },
  { key: 'passport_number', label: 'Passport Number', type: 'text', group: 'Identification' },
  { key: 'trade_license', label: 'Trade License', type: 'text', group: 'Identification' },
  { key: 'tax_registration', label: 'Tax Registration', type: 'text', group: 'Identification' },

  // Address
  { key: 'address', label: 'Address', type: 'textarea', width: 'full', group: 'Address' },
  { key: 'city', label: 'City', type: 'text', group: 'Address' },
  { key: 'country', label: 'Country', type: 'select', group: 'Address', options: [
    { value: 'UAE', label: 'United Arab Emirates' },
    { value: 'Iran', label: 'Iran' },
    { value: 'Other', label: 'Other' },
  ]},

  // Status
  { key: 'status', label: 'Status', type: 'select', group: 'Status', options: [
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
    { value: 'blocked', label: 'Blocked' },
  ], defaultValue: 'active' },
  { key: 'risk_rating', label: 'Risk Rating', type: 'select', group: 'Status', options: [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
  ]},

  // Notes
  { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
]

const tableColumns: Column[] = [
  { key: 'id', label: 'ID', sortable: true, width: '80px' },
  { key: 'customer_type', label: 'Type', sortable: true, type: 'badge' },
  { key: 'full_name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'phone', label: 'Phone' },
  { key: 'status', label: 'Status', sortable: true, render: (value) => (
    <span className={`badge ${
      value === 'active' ? 'bg-green-100 text-green-800' :
      value === 'inactive' ? 'bg-gray-100 text-gray-800' :
      'bg-red-100 text-red-800'
    }`}>
      {value}
    </span>
  )},
  { key: 'risk_rating', label: 'Risk', render: (value) => (
    <span className={`badge ${
      value === 'low' ? 'bg-green-100 text-green-800' :
      value === 'medium' ? 'bg-yellow-100 text-yellow-800' :
      'bg-red-100 text-red-800'
    }`}>
      {value || '-'}
    </span>
  )},
  { key: 'created_at', label: 'Created', type: 'date', sortable: true },
  { key: 'actions', label: 'Actions', type: 'actions', width: '100px' },
]

export default function CustomersPage() {
  const router = useRouter()
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<any>(null)
  const [stats, setStats] = useState({ total: 0, active: 0, corporate: 0 })

  const fetchCustomers = async () => {
    setLoading(true)
    try {
      const response = await customersApi.list()
      const data = response.data.items || response.data || []
      setCustomers(data)

      // Calculate stats
      setStats({
        total: data.length,
        active: data.filter((c: any) => c.status === 'active').length,
        corporate: data.filter((c: any) => c.customer_type === 'corporate').length,
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
    if (!confirm(`Are you sure you want to delete "${customer.full_name}"?`)) return

    try {
      await customersApi.delete(customer.id)
      toast.success('Customer deleted successfully')
      fetchCustomers()
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
      fetchCustomers()
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
