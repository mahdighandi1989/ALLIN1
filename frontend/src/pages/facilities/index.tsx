/**
 * Facilities Page
 * صفحه مدیریت تسهیلات
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Layout from '@/components/Layout'
import DataTable, { Column } from '@/components/ui/DataTable'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import { facilitiesApi, customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { CreditCard, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'

export default function FacilitiesPage() {
  const router = useRouter()
  const [facilities, setFacilities] = useState<any[]>([])
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingFacility, setEditingFacility] = useState<any>(null)
  const [stats, setStats] = useState({ total: 0, active: 0, totalAmount: 0, expiringSoon: 0 })

  // Dynamic fields based on customers
  const facilityFields: FormField[] = [
    { key: 'customer_id', label: 'Customer', type: 'select', required: true, group: 'Basic Information',
      options: customers.map(c => ({ value: c.id, label: c.full_name }))
    },
    { key: 'facility_type', label: 'Facility Type', type: 'select', required: true, group: 'Basic Information', options: [
      { value: 'OD', label: 'Overdraft (OD)' },
      { value: 'Loan', label: 'Term Loan' },
      { value: 'LG', label: 'Letter of Guarantee (LG)' },
      { value: 'LC', label: 'Letter of Credit (LC)' },
      { value: 'TF', label: 'Trade Finance' },
      { value: 'BG', label: 'Bank Guarantee' },
      { value: 'Other', label: 'Other' },
    ]},
    { key: 'facility_number', label: 'Facility Number', type: 'text', group: 'Basic Information' },
    { key: 'currency', label: 'Currency', type: 'select', required: true, group: 'Financial Details', options: [
      { value: 'AED', label: 'AED - UAE Dirham' },
      { value: 'USD', label: 'USD - US Dollar' },
      { value: 'EUR', label: 'EUR - Euro' },
      { value: 'GBP', label: 'GBP - British Pound' },
    ]},
    { key: 'approved_amount', label: 'Approved Amount', type: 'number', required: true, group: 'Financial Details' },
    { key: 'outstanding_amount', label: 'Outstanding Amount', type: 'number', group: 'Financial Details' },
    { key: 'interest_rate', label: 'Interest Rate (%)', type: 'number', group: 'Financial Details' },
    { key: 'start_date', label: 'Start Date', type: 'date', group: 'Dates' },
    { key: 'expiry_date', label: 'Expiry Date', type: 'date', group: 'Dates' },
    { key: 'review_date', label: 'Review Date', type: 'date', group: 'Dates' },
    { key: 'status', label: 'Status', type: 'select', group: 'Status', options: [
      { value: 'active', label: 'Active' },
      { value: 'pending', label: 'Pending' },
      { value: 'expired', label: 'Expired' },
      { value: 'cancelled', label: 'Cancelled' },
      { value: 'fully_paid', label: 'Fully Paid' },
    ], defaultValue: 'active' },
    { key: 'purpose', label: 'Purpose', type: 'textarea', width: 'full', group: 'Additional' },
    { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
  ]

  const tableColumns: Column[] = [
    { key: 'id', label: 'ID', sortable: true, width: '60px' },
    { key: 'facility_type', label: 'Type', sortable: true, type: 'badge' },
    { key: 'customer_name', label: 'Customer', sortable: true },
    { key: 'approved_amount', label: 'Amount', sortable: true, render: (v, row) => (
      <span className="font-medium">{row.currency} {Number(v).toLocaleString()}</span>
    )},
    { key: 'outstanding_amount', label: 'Outstanding', render: (v, row) => (
      <span>{row.currency} {Number(v || 0).toLocaleString()}</span>
    )},
    { key: 'expiry_date', label: 'Expiry', type: 'date', sortable: true },
    { key: 'status', label: 'Status', render: (value) => (
      <span className={`badge ${
        value === 'active' ? 'bg-green-100 text-green-800' :
        value === 'pending' ? 'bg-yellow-100 text-yellow-800' :
        value === 'expired' ? 'bg-red-100 text-red-800' :
        'bg-gray-100 text-gray-800'
      }`}>
        {value}
      </span>
    )},
    { key: 'actions', label: 'Actions', type: 'actions', width: '100px' },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const [facilitiesRes, customersRes] = await Promise.all([
        facilitiesApi.list({ limit: 100 }),
        customersApi.list({ limit: 100 })
      ])

      const facilitiesData = facilitiesRes.data.items || facilitiesRes.data || []
      const customersData = customersRes.data.items || customersRes.data || []

      // Add customer name to facilities
      const facilitiesWithNames = facilitiesData.map((f: any) => ({
        ...f,
        customer_name: customersData.find((c: any) => c.id === f.customer_id)?.full_name || 'Unknown'
      }))

      setFacilities(facilitiesWithNames)
      setCustomers(customersData)

      // Calculate stats
      const now = new Date()
      const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)

      setStats({
        total: facilitiesData.length,
        active: facilitiesData.filter((f: any) => f.status === 'active').length,
        totalAmount: facilitiesData.reduce((sum: number, f: any) => sum + (f.approved_amount || 0), 0),
        expiringSoon: facilitiesData.filter((f: any) => {
          const expiry = new Date(f.expiry_date)
          return f.status === 'active' && expiry <= thirtyDaysFromNow && expiry >= now
        }).length,
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      toast.error('Failed to load facilities')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleAdd = () => {
    setEditingFacility(null)
    setShowForm(true)
  }

  const handleEdit = (facility: any) => {
    setEditingFacility(facility)
    setShowForm(true)
  }

  const handleView = (facility: any) => {
    router.push(`/facilities/${facility.id}`)
  }

  const handleDelete = async (facility: any) => {
    if (!confirm('Are you sure you want to delete this facility?')) return

    try {
      await facilitiesApi.delete(facility.id)
      toast.success('Facility deleted successfully')
      fetchData()
    } catch (error) {
      toast.error('Failed to delete facility')
    }
  }

  const handleSubmit = async (data: Record<string, any>) => {
    try {
      if (editingFacility) {
        await facilitiesApi.update(editingFacility.id, data)
        toast.success('Facility updated successfully')
      } else {
        await facilitiesApi.create(data)
        toast.success('Facility created successfully')
      }
      setShowForm(false)
      fetchData()
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to save facility')
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facilities</h1>
          <p className="text-gray-600">Manage credit facilities and loans</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <CreditCard className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Facilities</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold">{stats.active}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Amount</p>
              <p className="text-xl font-bold">AED {(stats.totalAmount / 1000000).toFixed(1)}M</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <AlertTriangle className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Expiring (30d)</p>
              <p className="text-2xl font-bold">{stats.expiringSoon}</p>
            </div>
          </div>
        </div>

        {/* Data Table */}
        <DataTable
          columns={tableColumns}
          data={facilities}
          loading={loading}
          onAdd={handleAdd}
          onEdit={handleEdit}
          onView={handleView}
          onDelete={handleDelete}
          addButtonText="Add Facility"
        />

        {/* Form Modal */}
        {showForm && (
          <DynamicForm
            title={editingFacility ? 'Edit Facility' : 'Add New Facility'}
            fields={facilityFields}
            initialData={editingFacility || {}}
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
