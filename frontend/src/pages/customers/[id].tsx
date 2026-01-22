/**
 * Customer Detail Page
 * صفحه جزئیات مشتری
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import Layout from '@/components/Layout'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import { customersApi, facilitiesApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Edit,
  Trash2,
  User,
  Building2,
  CreditCard,
  Mail,
  Phone,
  MapPin,
  Calendar,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  Shield,
  DollarSign,
} from 'lucide-react'

// Customer form fields for editing
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
  { key: 'status', label: 'Status', type: 'select', group: 'Status', options: [
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
    { value: 'suspended', label: 'Suspended' },
  ]},
  { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
]

interface Customer {
  id: string
  account_no: string
  customer_name: string
  customer_name_ar?: string
  full_name?: string
  account_type: string
  branch?: string
  relationship_manager?: string
  email?: string
  phone?: string
  mobile?: string
  address?: string
  status: string
  notes?: string
  profile_completeness?: number
  created_at: string
  updated_at?: string
}

interface Facility {
  id: string
  facility_type: string
  facility_number?: string
  currency: string
  approved_amount: number
  outstanding_amount?: number
  status: string
  expiry_date?: string
}

export default function CustomerDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const [customer, setCustomer] = useState<Customer | null>(null)
  const [facilities, setFacilities] = useState<Facility[]>([])
  const [loading, setLoading] = useState(true)
  const [showEditForm, setShowEditForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'facilities' | 'documents' | 'history'>('overview')

  const fetchCustomer = async () => {
    if (!id) return

    setLoading(true)
    try {
      const customerId = Array.isArray(id) ? id[0] : id
      const [customerRes, facilitiesRes] = await Promise.all([
        customersApi.get(customerId),
        facilitiesApi.list({ customer_id: customerId })
      ])

      setCustomer(customerRes.data)

      const facilitiesData = facilitiesRes.data.items || facilitiesRes.data || []
      setFacilities(facilitiesData.filter((f: any) => f.customer_id === id))
    } catch (error: any) {
      console.error('Error fetching customer:', error)
      if (error.response?.status === 404) {
        toast.error('Customer not found')
        router.push('/customers')
      } else {
        toast.error('Failed to load customer details')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchCustomer()
    }
  }, [id])

  const handleUpdate = async (data: Record<string, any>) => {
    try {
      await customersApi.update(id as string, data)
      toast.success('Customer updated successfully')
      setShowEditForm(false)
      fetchCustomer()
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update customer')
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${customer?.customer_name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await customersApi.delete(id as string)
      toast.success('Customer deleted successfully')
      router.push('/customers')
    } catch (error) {
      toast.error('Failed to delete customer')
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-yellow-100 text-yellow-800',
      blocked: 'bg-red-100 text-red-800',
    }
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'
  }

  const getTypeBadge = (type: string) => {
    const styles = {
      corporate: 'bg-purple-100 text-purple-800',
      retail: 'bg-blue-100 text-blue-800',
      sme: 'bg-orange-100 text-orange-800',
    }
    return styles[type as keyof typeof styles] || 'bg-gray-100 text-gray-800'
  }

  // Calculate facility stats
  const facilityStats = {
    total: facilities.length,
    active: facilities.filter(f => f.status === 'active').length,
    totalApproved: facilities.reduce((sum, f) => sum + (f.approved_amount || 0), 0),
    totalOutstanding: facilities.reduce((sum, f) => sum + (f.outstanding_amount || 0), 0),
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading customer details...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!customer) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto text-red-400" size={48} />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Customer Not Found</h2>
          <p className="mt-2 text-gray-500">The customer you're looking for doesn't exist.</p>
          <Link href="/customers" className="mt-4 inline-block btn-primary">
            Back to Customers
          </Link>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {customer.customer_name}
                </h1>
                <span className={`badge ${getStatusBadge(customer.status)}`}>
                  {customer.status}
                </span>
                <span className={`badge ${getTypeBadge(customer.account_type)}`}>
                  {customer.account_type}
                </span>
              </div>
              {customer.customer_name_ar && (
                <p className="text-gray-500 mt-1" dir="rtl">{customer.customer_name_ar}</p>
              )}
              <p className="text-sm text-gray-500 mt-1">
                Account: {customer.account_no} • {customer.branch || 'No Branch'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowEditForm(true)}
              className="btn-secondary flex items-center gap-2"
            >
              <Edit size={16} />
              Edit
            </button>
            <button
              onClick={handleDelete}
              className="btn-danger flex items-center gap-2"
            >
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <CreditCard className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Facilities</p>
              <p className="text-2xl font-bold">{facilityStats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Facilities</p>
              <p className="text-2xl font-bold">{facilityStats.active}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <DollarSign className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Approved</p>
              <p className="text-xl font-bold">AED {facilityStats.totalApproved.toLocaleString()}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <TrendingUp className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Outstanding</p>
              <p className="text-xl font-bold">AED {facilityStats.totalOutstanding.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex gap-4">
            {(['overview', 'facilities', 'documents', 'history'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 border-b-2 font-medium capitalize ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Customer Info Card */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <User size={20} />
                Customer Information
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Basic Details</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Account Number</dt>
                      <dd className="font-medium">{customer.account_no}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Account Type</dt>
                      <dd className="capitalize font-medium">{customer.account_type}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Branch</dt>
                      <dd className="font-medium">{customer.branch || '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Relationship Manager</dt>
                      <dd className="font-medium">{customer.relationship_manager || '-'}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Contact Information</h4>
                  <dl className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Mail size={16} className="text-gray-400" />
                      <span>{customer.email || 'No email'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone size={16} className="text-gray-400" />
                      <span>{customer.phone || 'No phone'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone size={16} className="text-gray-400" />
                      <span>{customer.mobile || 'No mobile'}</span>
                    </div>
                    {customer.address && (
                      <div className="flex items-start gap-2">
                        <MapPin size={16} className="text-gray-400 mt-0.5" />
                        <span className="text-sm">{customer.address}</span>
                      </div>
                    )}
                  </dl>
                </div>
              </div>

              {customer.notes && (
                <div className="mt-6 pt-6 border-t">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Notes</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{customer.notes}</p>
                </div>
              )}
            </div>

            {/* Profile Completeness & Quick Actions */}
            <div className="space-y-6">
              {/* Profile Completeness */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Profile Completeness</h3>
                <div className="relative pt-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Progress</span>
                    <span className="text-sm font-semibold text-gray-700">
                      {customer.profile_completeness || 0}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${
                        (customer.profile_completeness || 0) >= 70
                          ? 'bg-green-500'
                          : (customer.profile_completeness || 0) >= 40
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${customer.profile_completeness || 0}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Calendar size={20} />
                  Timeline
                </h3>
                <dl className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <dt className="text-gray-600">Created</dt>
                    <dd>{new Date(customer.created_at).toLocaleDateString()}</dd>
                  </div>
                  {customer.updated_at && (
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Last Updated</dt>
                      <dd>{new Date(customer.updated_at).toLocaleDateString()}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'facilities' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">Facilities</h3>
              <Link
                href={`/facilities?customer_id=${id}`}
                className="btn-primary text-sm"
              >
                Add Facility
              </Link>
            </div>

            {facilities.length === 0 ? (
              <div className="p-8 text-center">
                <CreditCard className="mx-auto text-gray-300" size={48} />
                <p className="mt-2 text-gray-500">No facilities found for this customer</p>
              </div>
            ) : (
              <div className="divide-y">
                {facilities.map((facility) => (
                  <Link
                    key={facility.id}
                    href={`/facilities/${facility.id}`}
                    className="block p-4 hover:bg-gray-50"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{facility.facility_type}</span>
                          <span className={`badge text-xs ${
                            facility.status === 'active' ? 'bg-green-100 text-green-800' :
                            facility.status === 'expired' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {facility.status}
                          </span>
                        </div>
                        {facility.facility_number && (
                          <p className="text-sm text-gray-500 mt-1">
                            #{facility.facility_number}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">
                          {facility.currency} {facility.approved_amount?.toLocaleString()}
                        </p>
                        {facility.expiry_date && (
                          <p className="text-sm text-gray-500">
                            Expires: {new Date(facility.expiry_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <FileText className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Document management coming soon</p>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Clock className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Activity history coming soon</p>
          </div>
        )}

        {/* Edit Form Modal */}
        {showEditForm && (
          <DynamicForm
            title="Edit Customer"
            fields={customerFields}
            initialData={customer}
            onSubmit={handleUpdate}
            onCancel={() => setShowEditForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
