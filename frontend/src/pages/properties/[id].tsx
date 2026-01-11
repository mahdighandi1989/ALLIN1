/**
 * Property Detail Page
 * صفحه جزئیات ملک
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import Layout from '@/components/Layout'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import api, { customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Edit,
  Trash2,
  Building,
  User,
  MapPin,
  Calendar,
  DollarSign,
  AlertCircle,
  FileText,
  Clock,
  Home,
  Landmark,
  Ruler,
  Key,
} from 'lucide-react'

interface Property {
  id: string
  customer_id: string
  customer_name?: string
  property_type: string
  title: string
  location_country: string
  location_city?: string
  location_area?: string
  address?: string
  size_sqft?: number
  plot_number?: string
  title_deed_number?: string
  estimated_value?: number
  valuation_date?: string
  mortgage_status?: string
  status: string
  notes?: string
  created_at: string
  updated_at?: string
}

interface Customer {
  id: string
  customer_name: string
  full_name?: string
  account_no: string
}

export default function PropertyDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const [property, setProperty] = useState<Property | null>(null)
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [showEditForm, setShowEditForm] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'valuation' | 'documents' | 'history'>('overview')

  // Property fields for editing
  const propertyFields: FormField[] = [
    { key: 'customer_id', label: 'Customer', type: 'select', required: true, group: 'Basic Information',
      options: customers.map(c => ({ value: c.id, label: c.customer_name || c.full_name || 'Unknown' }))
    },
    { key: 'property_type', label: 'Property Type', type: 'select', required: true, group: 'Basic Information', options: [
      { value: 'residential', label: 'Residential' },
      { value: 'commercial', label: 'Commercial' },
      { value: 'land', label: 'Land' },
      { value: 'industrial', label: 'Industrial' },
      { value: 'mixed_use', label: 'Mixed Use' },
    ]},
    { key: 'title', label: 'Property Title/Name', type: 'text', required: true, group: 'Basic Information' },
    { key: 'location_country', label: 'Country', type: 'select', required: true, group: 'Location', options: [
      { value: 'UAE', label: 'UAE' },
      { value: 'Iran', label: 'Iran' },
      { value: 'Other', label: 'Other' },
    ]},
    { key: 'location_city', label: 'City', type: 'text', group: 'Location' },
    { key: 'location_area', label: 'Area/District', type: 'text', group: 'Location' },
    { key: 'address', label: 'Full Address', type: 'textarea', width: 'full', group: 'Location' },
    { key: 'size_sqft', label: 'Size (sq.ft)', type: 'number', group: 'Details' },
    { key: 'plot_number', label: 'Plot Number', type: 'text', group: 'Details' },
    { key: 'title_deed_number', label: 'Title Deed Number', type: 'text', group: 'Details' },
    { key: 'estimated_value', label: 'Estimated Value (AED)', type: 'number', group: 'Valuation' },
    { key: 'valuation_date', label: 'Valuation Date', type: 'date', group: 'Valuation' },
    { key: 'mortgage_status', label: 'Mortgage Status', type: 'select', group: 'Valuation', options: [
      { value: 'clear', label: 'Clear' },
      { value: 'mortgaged', label: 'Mortgaged' },
      { value: 'partial', label: 'Partial Mortgage' },
    ]},
    { key: 'status', label: 'Status', type: 'select', group: 'Status', options: [
      { value: 'active', label: 'Active' },
      { value: 'sold', label: 'Sold' },
      { value: 'under_transfer', label: 'Under Transfer' },
    ]},
    { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
  ]

  const fetchProperty = async () => {
    if (!id) return

    setLoading(true)
    try {
      const [propertyRes, customersRes] = await Promise.all([
        api.get(`/properties/${id}`),
        customersApi.list()
      ])

      const customersData = customersRes.data.items || customersRes.data || []
      setCustomers(customersData)

      const propertyData = propertyRes.data
      const customerData = customersData.find((c: any) => c.id === propertyData.customer_id)

      setProperty({
        ...propertyData,
        customer_name: customerData?.customer_name || customerData?.full_name || 'Unknown'
      })
      setCustomer(customerData || null)
    } catch (error: any) {
      console.error('Error fetching property:', error)
      if (error.response?.status === 404) {
        toast.error('Property not found')
        router.push('/properties')
      } else {
        toast.error('Failed to load property details')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchProperty()
    }
  }, [id])

  const handleUpdate = async (data: Record<string, any>) => {
    try {
      await api.put(`/properties/${id}`, data)
      toast.success('Property updated successfully')
      setShowEditForm(false)
      fetchProperty()
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update property')
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this property? This action cannot be undone.')) {
      return
    }

    try {
      await api.delete(`/properties/${id}`)
      toast.success('Property deleted successfully')
      router.push('/properties')
    } catch (error) {
      toast.error('Failed to delete property')
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      sold: 'bg-blue-100 text-blue-800',
      under_transfer: 'bg-yellow-100 text-yellow-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      residential: 'bg-blue-100 text-blue-800',
      commercial: 'bg-purple-100 text-purple-800',
      land: 'bg-green-100 text-green-800',
      industrial: 'bg-orange-100 text-orange-800',
      mixed_use: 'bg-pink-100 text-pink-800',
    }
    return styles[type] || 'bg-gray-100 text-gray-800'
  }

  const getMortgageBadge = (status: string) => {
    const styles: Record<string, string> = {
      clear: 'bg-green-100 text-green-800',
      mortgaged: 'bg-red-100 text-red-800',
      partial: 'bg-yellow-100 text-yellow-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'residential': return Home
      case 'commercial': return Building
      case 'land': return MapPin
      case 'industrial': return Landmark
      default: return Building
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading property details...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!property) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto text-red-400" size={48} />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Property Not Found</h2>
          <p className="mt-2 text-gray-500">The property you're looking for doesn't exist.</p>
          <Link href="/properties" className="mt-4 inline-block btn-primary">
            Back to Properties
          </Link>
        </div>
      </Layout>
    )
  }

  const TypeIcon = getTypeIcon(property.property_type)

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
                  {property.title}
                </h1>
                <span className={`badge ${getStatusBadge(property.status)}`}>
                  {property.status}
                </span>
                <span className={`badge ${getTypeBadge(property.property_type)}`}>
                  {property.property_type}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                <MapPin size={14} />
                {property.location_city && `${property.location_city}, `}
                {property.location_country}
              </p>
              {customer && (
                <Link
                  href={`/customers/${customer.id}`}
                  className="text-sm text-blue-600 hover:underline mt-1 inline-flex items-center gap-1"
                >
                  <User size={14} />
                  {property.customer_name}
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
              <p className="text-sm text-gray-600">Estimated Value</p>
              <p className="text-xl font-bold">
                {property.estimated_value
                  ? `AED ${property.estimated_value.toLocaleString()}`
                  : '-'}
              </p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Ruler className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Size</p>
              <p className="text-xl font-bold">
                {property.size_sqft ? `${property.size_sqft.toLocaleString()} sq.ft` : '-'}
              </p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TypeIcon className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Type</p>
              <p className="text-xl font-bold capitalize">{property.property_type}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className={`p-3 rounded-lg ${
              property.mortgage_status === 'clear' ? 'bg-green-100' :
              property.mortgage_status === 'mortgaged' ? 'bg-red-100' :
              'bg-yellow-100'
            }`}>
              <Key className={`${
                property.mortgage_status === 'clear' ? 'text-green-600' :
                property.mortgage_status === 'mortgaged' ? 'text-red-600' :
                'text-yellow-600'
              }`} size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Mortgage</p>
              <p className="text-xl font-bold capitalize">{property.mortgage_status || '-'}</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex gap-4">
            {(['overview', 'valuation', 'documents', 'history'] as const).map((tab) => (
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
            {/* Property Details */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Building size={20} />
                Property Details
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Location Information</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Country</dt>
                      <dd className="font-medium">{property.location_country}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">City</dt>
                      <dd className="font-medium">{property.location_city || '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Area/District</dt>
                      <dd className="font-medium">{property.location_area || '-'}</dd>
                    </div>
                    {property.address && (
                      <div className="pt-2">
                        <dt className="text-gray-600 mb-1">Full Address</dt>
                        <dd className="font-medium text-sm">{property.address}</dd>
                      </div>
                    )}
                  </dl>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-3">Property Information</h4>
                  <dl className="space-y-2">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Type</dt>
                      <dd className="font-medium capitalize">{property.property_type}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Size</dt>
                      <dd className="font-medium">
                        {property.size_sqft ? `${property.size_sqft.toLocaleString()} sq.ft` : '-'}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Plot Number</dt>
                      <dd className="font-medium">{property.plot_number || '-'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Title Deed #</dt>
                      <dd className="font-medium">{property.title_deed_number || '-'}</dd>
                    </div>
                  </dl>
                </div>
              </div>

              {property.notes && (
                <div className="mt-6 pt-6 border-t">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Notes</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{property.notes}</p>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Owner Card */}
              {customer && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <User size={20} />
                    Owner
                  </h3>
                  <Link
                    href={`/customers/${customer.id}`}
                    className="block p-3 border rounded-lg hover:bg-gray-50"
                  >
                    <p className="font-medium">{customer.customer_name || customer.full_name}</p>
                    <p className="text-sm text-gray-500">{customer.account_no}</p>
                  </Link>
                </div>
              )}

              {/* Valuation Summary */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <DollarSign size={20} />
                  Valuation
                </h3>
                <dl className="space-y-3">
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Value</dt>
                    <dd className="font-bold text-lg">
                      {property.estimated_value
                        ? `AED ${property.estimated_value.toLocaleString()}`
                        : '-'}
                    </dd>
                  </div>
                  <div className="flex justify-between text-sm">
                    <dt className="text-gray-600">Valuation Date</dt>
                    <dd>
                      {property.valuation_date
                        ? new Date(property.valuation_date).toLocaleDateString()
                        : '-'}
                    </dd>
                  </div>
                  <div className="flex justify-between text-sm">
                    <dt className="text-gray-600">Mortgage Status</dt>
                    <dd>
                      <span className={`badge text-xs ${getMortgageBadge(property.mortgage_status || '')}`}>
                        {property.mortgage_status || '-'}
                      </span>
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Timeline */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Clock size={20} />
                  Timeline
                </h3>
                <dl className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <dt className="text-gray-600">Created</dt>
                    <dd>{new Date(property.created_at).toLocaleDateString()}</dd>
                  </div>
                  {property.updated_at && (
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-600">Last Updated</dt>
                      <dd>{new Date(property.updated_at).toLocaleDateString()}</dd>
                    </div>
                  )}
                </dl>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'valuation' && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <DollarSign className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">Valuation history coming soon</p>
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
            title="Edit Property"
            fields={propertyFields}
            initialData={property}
            onSubmit={handleUpdate}
            onCancel={() => setShowEditForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
