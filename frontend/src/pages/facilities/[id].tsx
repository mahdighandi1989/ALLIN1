/**
 * Facility Detail Page
 * صفحه جزئیات تسهیلات
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import Layout from '@/components/Layout'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import { facilitiesApi, customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Edit,
  Trash2,
  CreditCard,
  User,
  Calendar,
  DollarSign,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  FileText,
  Shield,
  Percent,
  Building2,
} from 'lucide-react'

interface Facility {
  id: string
  customer_id: string
  customer_name?: string
  facility_type: string
  facility_number?: string
  currency: string
  approved_amount: number
  outstanding_amount?: number
  interest_rate?: number
  start_date?: string
  expiry_date?: string
  review_date?: string
  status: string
  purpose?: string
  notes?: string
  created_at: string
  updated_at?: string
}

interface Customer {
  id: string
  customer_name: string
  account_no: string
}

export default function FacilityDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const [facility, setFacility] = useState<Facility | null>(null)
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [showEditForm, setShowEditForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'payments' | 'guarantors' | 'documents'>('overview')

  // Facility fields for editing
  const facilityFields: FormField[] = [
    { key: 'customer_id', label: 'Customer', type: 'select', required: true, group: 'Basic Information',
      options: customers.map(c => ({ value: c.id, label: c.customer_name }))
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
    ]},
    { key: 'purpose', label: 'Purpose', type: 'textarea', width: 'full', group: 'Additional' },
    { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
  ]

  const fetchFacility = async () => {
    if (!id) return

    setLoading(true)
    try {
      const [facilityRes, customersRes] = await Promise.all([
        facilitiesApi.get(id as string),
        customersApi.list()
      ])

      const customersData = customersRes.data.items || customersRes.data || []
      setCustomers(customersData)

      const facilityData = facilityRes.data
      const customerData = customersData.find((c: any) => c.id === facilityData.customer_id)

      setFacility({
        ...facilityData,
        customer_name: customerData?.customer_name || customerData?.full_name || 'Unknown'
      })
      setCustomer(customerData || null)
    } catch (error: any) {
      console.error('Error fetching facility:', error)
      if (error.response?.status === 404) {
        toast.error('Facility not found')
        router.push('/facilities')
      } else {
        toast.error('Failed to load facility details')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchFacility()
    }
  }, [id])

  const handleUpdate = async (data: Record<string, any>) => {
    try {
      await facilitiesApi.update(id as string, data)
      toast.success('Facility updated successfully')
      setShowEditForm(false)
      fetchFacility()
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update facility')
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this facility? This action cannot be undone.')) {
      return
    }

    try {
      await facilitiesApi.delete(id as string)
      toast.success('Facility deleted successfully')
      router.push('/facilities')
    } catch (error) {
      toast.error('Failed to delete facility')
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      expired: 'bg-red-100 text-red-800',
      cancelled: 'bg-gray-100 text-gray-800',
      fully_paid: 'bg-blue-100 text-blue-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      OD: 'bg-blue-100 text-blue-800',
      Loan: 'bg-purple-100 text-purple-800',
      LG: 'bg-orange-100 text-orange-800',
      LC: 'bg-cyan-100 text-cyan-800',
      TF: 'bg-pink-100 text-pink-800',
      BG: 'bg-indigo-100 text-indigo-800',
    }
    return styles[type] || 'bg-gray-100 text-gray-800'
  }

  // Calculate days until expiry
  const getDaysUntilExpiry = () => {
    if (!facility?.expiry_date) return null
    const expiry = new Date(facility.expiry_date)
    const today = new Date()
    const diffTime = expiry.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const daysUntilExpiry = getDaysUntilExpiry()

  // Calculate utilization
  const utilizationRate = facility?.approved_amount
    ? ((facility.outstanding_amount || 0) / facility.approved_amount) * 100
    : 0

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading facility details...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!facility) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto text-red-400" size={48} />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Facility Not Found</h2>
          <p className="mt-2 text-gray-500">The facility you're looking for doesn't exist.</p>
          <Link href="/facilities" className="mt-4 inline-block btn-primary">
            Back to Facilities
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
                  {facility.facility_type} Facility
                </h1>
                <span className={`badge ${getStatusBadge(facility.status)}`}>
                  {facility.status}
                </span>
                <span className={`badge ${getTypeBadge(facility.facility_type)}`}>
                  {facility.facility_type}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {facility.facility_number && `#${facility.facility_number} • `}
                {facility.currency} {facility.approved_amount?.toLocaleString()}
              </p>
              {customer && (
                <Link
                  href={`/customers/${customer.id}`}
                  className="text-sm text-blue-600 hover:underline mt-1 inline-flex items-center gap-1"
                >
                  <User size={14} />
                  {facility.customer_name}
                </Link>
              )}
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
            <div className="p-3 bg-green-100 rounded-lg">
              <DollarSign className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Approved Amount</p>
              <p className="text-xl font-bold">
                {facility.currency} {facility.approved_amount?.toLocaleString()}
              </p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <TrendingUp className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Outstanding</p>
              <p className="text-xl font-bold">
                {facility.currency} {(facility.outstanding_amount || 0).toLocaleString()}
              </p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Percent className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Interest Rate</p>
              <p className="text-xl font-bold">
                {facility.interest_rate ? `${facility.interest_rate}%` : '-'}
              </p>
            </div>
          </div>
          <div className={`bg-white p-4 rounded-lg shadow flex items-center gap-4 ${
            daysUntilExpiry !== null && daysUntilExpiry <= 30 ? 'ring-2 ring-red-300' : ''
          }`}>
            <div className={`p-3 rounded-lg ${
              daysUntilExpiry !== null && daysUntilExpiry <= 30 ? 'bg-red-100' : 'bg-blue-100'
            }`}>
              <Calendar className={`${
                daysUntilExpiry !== null && daysUntilExpiry <= 30 ? 'text-red-600' : 'text-blue-600'
              }`} size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Days to Expiry</p>
              <p className="text-xl font-bold">
                {daysUntilExpiry !== null ? (
                  daysUntilExpiry > 0 ? daysUntilExpiry : 'Expired'
                ) : '-'}
              </p>
            </div>
          </div>
        </div>

        {/* Utilization Bar */}
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">Facility Utilization</span>
            <span className="text-sm font-semibold">{utilizationRate.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all ${
                utilizationRate >= 90 ? 'bg-red-500' :
                utilizationRate >= 70 ? 'bg-orange-500' :
                'bg-green-500'
              }`}
              style={{ width: `${Math.min(utilizationRate, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-gray-500">
            <span>Used: {facility.currency} {(facility.outstanding_amount || 0).toLocaleString()}</span>
            <span>Available: {facility.currency} {(facility.approved_amount - (facility.outstanding_amount || 0)).toLocaleString()}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex gap-4">
            {(['overview', 'payments', 'guarantors', 'documents'] as const).map((tab) => (
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
            {/* Facility Details */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard size={20} />
                Facility Details
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Financial Information</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Type</dt>
                      <dd className="font-medium">{facility.facility_type}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Currency</dt>
                      <dd className="font-medium">{facility.currency}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Approved Amount</dt>
                      <dd className="font-medium">{facility.approved_amount?.toLocaleString()}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Outstanding</dt>
                      <dd className="font-medium">{(facility.outstanding_amount || 0).toLocaleString()}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Interest Rate</dt>
                      <dd className="font-medium">{facility.interest_rate ? `${facility.interest_rate}%` : '-'}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Important Dates</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Start Date</dt>
                      <dd className="font-medium">
                        {facility.start_date ? new Date(facility.start_date).toLocaleDateString() : '-'}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Expiry Date</dt>
                      <dd className={`font-medium ${
                        daysUntilExpiry !== null && daysUntilExpiry <= 30 ? 'text-red-600' : ''
                      }`}>
                        {facility.expiry_date ? new Date(facility.expiry_date).toLocaleDateString() : '-'}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Review Date</dt>
                      <dd className="font-medium">
                        {facility.review_date ? new Date(facility.review_date).toLocaleDateString() : '-'}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>

              {facility.purpose && (
                <div className="mt-6 pt-6 border-t">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Purpose</h4>
                  <p className="text-gray-700">{facility.purpose}</p>
                </div>
              )}

              {facility.notes && (
                <div className="mt-6 pt-6 border-t">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Notes</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{facility.notes}</p>
                </div>
              )}
            </div>

            {/* Customer Info & Timeline */}
            <div className="space-y-6">
              {/* Customer Card */}
              {customer && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <User size={20} />
                    Customer
                  </h3>
                  <Link
                    href={`/customers/${customer.id}`}
                    className="block p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <p className="font-medium">{customer.customer_name}</p>
                    <p className="text-sm text-gray-500">{customer.account_no}</p>
                  </Link>
                </div>
              )}

              {/* Timeline */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Clock size={20} />
                  Timeline
                </h3>
                <dl className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <dt className="text-gray-600">Created</dt>
                    <dd>{new Date(facility.created_at).toLocaleDateString()}</dd>
                  </div>
                  {facility.updated_at && (
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Last Updated</dt>
                      <dd>{new Date(facility.updated_at).toLocaleDateString()}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'payments' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <DollarSign className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Payment schedule coming soon</p>
          </div>
        )}

        {activeTab === 'guarantors' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Shield className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Guarantors management coming soon</p>
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <FileText className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Document management coming soon</p>
          </div>
        )}

        {/* Edit Form Modal */}
        {showEditForm && (
          <DynamicForm
            title="Edit Facility"
            fields={facilityFields}
            initialData={facility}
            onSubmit={handleUpdate}
            onCancel={() => setShowEditForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
