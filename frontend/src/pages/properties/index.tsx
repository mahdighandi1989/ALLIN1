/**
 * Properties Page
 * صفحه مدیریت املاک و وثایق
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import DataTable, { Column } from '@/components/ui/DataTable'
import DynamicForm, { FormField } from '@/components/ui/DynamicForm'
import api, { customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { Building, MapPin, DollarSign, FileText } from 'lucide-react'

export default function PropertiesPage() {
  const [properties, setProperties] = useState<any[]>([])
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingProperty, setEditingProperty] = useState<any>(null)
  const [stats, setStats] = useState({ total: 0, uae: 0, iran: 0, totalValue: 0 })

  const propertyFields: FormField[] = [
    { key: 'customer_id', label: 'Customer', type: 'select', required: true, group: 'Basic Information',
      options: customers.map(c => ({ value: c.id, label: c.full_name }))
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
    { key: 'estimated_value', label: 'Estimated Value', type: 'number', group: 'Valuation' },
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
    ], defaultValue: 'active' },
    { key: 'notes', label: 'Notes', type: 'textarea', width: 'full', group: 'Additional' },
  ]

  const tableColumns: Column[] = [
    { key: 'id', label: 'ID', sortable: true, width: '60px' },
    { key: 'property_type', label: 'Type', sortable: true, type: 'badge' },
    { key: 'title', label: 'Title', sortable: true },
    { key: 'customer_name', label: 'Owner', sortable: true },
    { key: 'location_country', label: 'Country', render: (v) => (
      <span className="flex items-center gap-1">
        <MapPin size={14} />
        {v}
      </span>
    )},
    { key: 'location_city', label: 'City' },
    { key: 'estimated_value', label: 'Value', sortable: true, render: (v) => (
      v ? <span className="font-medium">AED {Number(v).toLocaleString()}</span> : '-'
    )},
    { key: 'mortgage_status', label: 'Mortgage', render: (v) => (
      <span className={`badge ${
        v === 'clear' ? 'bg-green-100 text-green-800' :
        v === 'mortgaged' ? 'bg-red-100 text-red-800' :
        'bg-yellow-100 text-yellow-800'
      }`}>
        {v || '-'}
      </span>
    )},
    { key: 'actions', label: 'Actions', type: 'actions', width: '100px' },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const [propertiesRes, customersRes] = await Promise.all([
        api.get('/properties', { params: { page_size: 100 } }),
        customersApi.list({ page_size: 100 })
      ])

      const propertiesData = propertiesRes.data.items || propertiesRes.data || []
      const customersData = customersRes.data.items || customersRes.data || []

      const propertiesWithNames = propertiesData.map((p: any) => ({
        ...p,
        customer_name: customersData.find((c: any) => c.id === p.customer_id)?.full_name || 'Unknown'
      }))

      setProperties(propertiesWithNames)
      setCustomers(customersData)

      setStats({
        total: propertiesData.length,
        uae: propertiesData.filter((p: any) => p.location_country === 'UAE').length,
        iran: propertiesData.filter((p: any) => p.location_country === 'Iran').length,
        totalValue: propertiesData.reduce((sum: number, p: any) => sum + (p.estimated_value || 0), 0),
      })
    } catch (error) {
      console.error('Error fetching data:', error)
      // toast.error('Failed to load properties')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (data: Record<string, any>) => {
    try {
      if (editingProperty) {
        await api.put(`/properties/${editingProperty.id}`, data)
        toast.success('Property updated')
      } else {
        await api.post('/properties', data)
        toast.success('Property created')
      }
      setShowForm(false)
      fetchData()
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to save property')
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Properties</h1>
          <p className="text-gray-600">Manage collateral properties and real estate</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Building className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Properties</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <MapPin className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">UAE</p>
              <p className="text-2xl font-bold">{stats.uae}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <MapPin className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Iran</p>
              <p className="text-2xl font-bold">{stats.iran}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <DollarSign className="text-orange-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-xl font-bold">AED {(stats.totalValue / 1000000).toFixed(1)}M</p>
            </div>
          </div>
        </div>

        <DataTable
          columns={tableColumns}
          data={properties}
          loading={loading}
          onAdd={() => { setEditingProperty(null); setShowForm(true) }}
          onEdit={(p) => { setEditingProperty(p); setShowForm(true) }}
          onDelete={async (p) => {
            if (confirm('Delete this property?')) {
              await api.delete(`/properties/${p.id}`)
              toast.success('Deleted')
              fetchData()
            }
          }}
          addButtonText="Add Property"
        />

        {showForm && (
          <DynamicForm
            title={editingProperty ? 'Edit Property' : 'Add Property'}
            fields={propertyFields}
            initialData={editingProperty || {}}
            onSubmit={handleSubmit}
            onCancel={() => setShowForm(false)}
          />
        )}
      </div>
    </Layout>
  )
}
