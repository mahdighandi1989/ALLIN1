/**
 * Settings Page
 * صفحه تنظیمات سیستم
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { settingsApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  Settings, Database, Users, Bell, Shield, Palette, Globe, Key, Save, Plus, Trash2, Edit
} from 'lucide-react'

interface SystemSetting {
  key: string
  value: string
  category: string
  description?: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'json'
  options?: string[]
}

interface CustomField {
  id: string
  entity: string
  field_name: string
  field_label: string
  field_type: string
  required: boolean
  options?: string[]
  order: number
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [customFields, setCustomFields] = useState<CustomField[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Form for new custom field
  const [showFieldForm, setShowFieldForm] = useState(false)
  const [editingField, setEditingField] = useState<CustomField | null>(null)
  const [fieldForm, setFieldForm] = useState({
    entity: 'customer',
    field_name: '',
    field_label: '',
    field_type: 'text',
    required: false,
    options: '',
  })

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'database', label: 'Database Fields', icon: Database },
    { id: 'users', label: 'Users & Roles', icon: Users },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'integrations', label: 'Integrations', icon: Globe },
    { id: 'api', label: 'API Keys', icon: Key },
  ]

  const entities = [
    { value: 'customer', label: 'Customers' },
    { value: 'facility', label: 'Facilities' },
    { value: 'property', label: 'Properties' },
    { value: 'checklist', label: 'Checklists' },
    { value: 'guarantor', label: 'Guarantors' },
  ]

  const fieldTypes = [
    { value: 'text', label: 'Text' },
    { value: 'number', label: 'Number' },
    { value: 'date', label: 'Date' },
    { value: 'email', label: 'Email' },
    { value: 'tel', label: 'Phone' },
    { value: 'select', label: 'Dropdown' },
    { value: 'textarea', label: 'Long Text' },
    { value: 'checkbox', label: 'Checkbox' },
    { value: 'file', label: 'File Upload' },
  ]

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    setLoading(true)
    try {
      const response = await settingsApi.getSystem()
      setSettings(response.data.items || response.data || [])

      // Fetch custom fields (mock for now - would come from API)
      setCustomFields([
        { id: '1', entity: 'customer', field_name: 'company_size', field_label: 'Company Size', field_type: 'select', required: false, options: ['Small', 'Medium', 'Large', 'Enterprise'], order: 1 },
        { id: '2', entity: 'customer', field_name: 'annual_revenue', field_label: 'Annual Revenue', field_type: 'number', required: false, order: 2 },
        { id: '3', entity: 'facility', field_name: 'collateral_coverage', field_label: 'Collateral Coverage %', field_type: 'number', required: true, order: 1 },
      ])
    } catch (error) {
      console.error('Error fetching settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSetting = async (key: string, value: string) => {
    setSaving(true)
    try {
      await settingsApi.updateSystem(key, value)
      toast.success('Setting saved')
      fetchSettings()
    } catch (error) {
      toast.error('Failed to save setting')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveField = async () => {
    if (!fieldForm.field_name || !fieldForm.field_label) {
      toast.error('Please fill in all required fields')
      return
    }

    try {
      // In a real app, this would call an API
      const newField: CustomField = {
        id: editingField?.id || Date.now().toString(),
        entity: fieldForm.entity,
        field_name: fieldForm.field_name.toLowerCase().replace(/\s+/g, '_'),
        field_label: fieldForm.field_label,
        field_type: fieldForm.field_type,
        required: fieldForm.required,
        options: fieldForm.options ? fieldForm.options.split(',').map(o => o.trim()) : undefined,
        order: customFields.filter(f => f.entity === fieldForm.entity).length + 1,
      }

      if (editingField) {
        setCustomFields(customFields.map(f => f.id === editingField.id ? newField : f))
        toast.success('Field updated')
      } else {
        setCustomFields([...customFields, newField])
        toast.success('Field created')
      }

      setShowFieldForm(false)
      setEditingField(null)
      setFieldForm({ entity: 'customer', field_name: '', field_label: '', field_type: 'text', required: false, options: '' })
    } catch (error) {
      toast.error('Failed to save field')
    }
  }

  const handleDeleteField = (id: string) => {
    if (!confirm('Delete this custom field?')) return
    setCustomFields(customFields.filter(f => f.id !== id))
    toast.success('Field deleted')
  }

  const openEditField = (field: CustomField) => {
    setEditingField(field)
    setFieldForm({
      entity: field.entity,
      field_name: field.field_name,
      field_label: field.field_label,
      field_type: field.field_type,
      required: field.required,
      options: field.options?.join(', ') || '',
    })
    setShowFieldForm(true)
  }

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Application Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Application Name</label>
            <input type="text" defaultValue="Banking Ops" className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Default Currency</label>
            <select className="w-full px-3 py-2 border rounded-lg">
              <option value="AED">AED - UAE Dirham</option>
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date Format</label>
            <select className="w-full px-3 py-2 border rounded-lg">
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Language</label>
            <select className="w-full px-3 py-2 border rounded-lg">
              <option value="en">English</option>
              <option value="fa">فارسی</option>
              <option value="ar">العربية</option>
            </select>
          </div>
        </div>
        <button className="btn-primary mt-4 flex items-center gap-2">
          <Save size={18} />
          Save Changes
        </button>
      </div>
    </div>
  )

  const renderDatabaseFields = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="font-medium">Custom Database Fields</h3>
            <p className="text-sm text-gray-500">Add custom fields to extend your data model</p>
          </div>
          <button
            onClick={() => {
              setEditingField(null)
              setFieldForm({ entity: 'customer', field_name: '', field_label: '', field_type: 'text', required: false, options: '' })
              setShowFieldForm(true)
            }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={18} />
            Add Field
          </button>
        </div>

        {/* Fields by Entity */}
        {entities.map(entity => {
          const entityFields = customFields.filter(f => f.entity === entity.value)
          if (entityFields.length === 0) return null

          return (
            <div key={entity.value} className="mt-6">
              <h4 className="font-medium text-gray-700 mb-3">{entity.label}</h4>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm">Field Name</th>
                      <th className="px-4 py-2 text-left text-sm">Label</th>
                      <th className="px-4 py-2 text-left text-sm">Type</th>
                      <th className="px-4 py-2 text-left text-sm">Required</th>
                      <th className="px-4 py-2 text-left text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entityFields.map(field => (
                      <tr key={field.id} className="border-t">
                        <td className="px-4 py-2 font-mono text-sm">{field.field_name}</td>
                        <td className="px-4 py-2">{field.field_label}</td>
                        <td className="px-4 py-2">
                          <span className="badge bg-blue-100 text-blue-800">{field.field_type}</span>
                        </td>
                        <td className="px-4 py-2">
                          {field.required ? (
                            <span className="badge bg-red-100 text-red-800">Yes</span>
                          ) : (
                            <span className="badge bg-gray-100 text-gray-800">No</span>
                          )}
                        </td>
                        <td className="px-4 py-2">
                          <div className="flex gap-1">
                            <button
                              onClick={() => openEditField(field)}
                              className="p-1 hover:bg-gray-100 rounded"
                            >
                              <Edit size={16} />
                            </button>
                            <button
                              onClick={() => handleDeleteField(field.id)}
                              className="p-1 hover:bg-gray-100 rounded text-red-500"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })}

        {customFields.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Database className="mx-auto mb-2" size={32} />
            <p>No custom fields defined yet</p>
          </div>
        )}
      </div>

      {/* Field Form Modal */}
      {showFieldForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">
                {editingField ? 'Edit Field' : 'Add Custom Field'}
              </h2>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Entity *</label>
                <select
                  value={fieldForm.entity}
                  onChange={(e) => setFieldForm({ ...fieldForm, entity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {entities.map(e => (
                    <option key={e.value} value={e.value}>{e.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Field Name *</label>
                <input
                  type="text"
                  value={fieldForm.field_name}
                  onChange={(e) => setFieldForm({ ...fieldForm, field_name: e.target.value })}
                  placeholder="e.g., company_size"
                  className="w-full px-3 py-2 border rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-1">Use lowercase with underscores</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Display Label *</label>
                <input
                  type="text"
                  value={fieldForm.field_label}
                  onChange={(e) => setFieldForm({ ...fieldForm, field_label: e.target.value })}
                  placeholder="e.g., Company Size"
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Field Type *</label>
                <select
                  value={fieldForm.field_type}
                  onChange={(e) => setFieldForm({ ...fieldForm, field_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {fieldTypes.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              {fieldForm.field_type === 'select' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Options</label>
                  <input
                    type="text"
                    value={fieldForm.options}
                    onChange={(e) => setFieldForm({ ...fieldForm, options: e.target.value })}
                    placeholder="Option1, Option2, Option3"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                  <p className="text-xs text-gray-500 mt-1">Comma-separated values</p>
                </div>
              )}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="required"
                  checked={fieldForm.required}
                  onChange={(e) => setFieldForm({ ...fieldForm, required: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="required" className="text-sm">Required field</label>
              </div>
            </div>
            <div className="p-4 border-t flex justify-end gap-3">
              <button
                onClick={() => setShowFieldForm(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button onClick={handleSaveField} className="btn-primary">
                {editingField ? 'Update' : 'Create'} Field
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderAPIKeys = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">AI Provider API Keys</h3>
        <p className="text-sm text-gray-500 mb-6">Configure your AI provider API keys</p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">OpenAI API Key</label>
            <input
              type="password"
              placeholder="sk-..."
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Anthropic API Key (Claude)</label>
            <input
              type="password"
              placeholder="sk-ant-..."
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Google AI API Key (Gemini)</label>
            <input
              type="password"
              placeholder="AIza..."
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
        </div>

        <button className="btn-primary mt-6 flex items-center gap-2">
          <Save size={18} />
          Save API Keys
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Email Configuration (SMTP)</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">SMTP Host</label>
            <input type="text" placeholder="smtp.gmail.com" className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">SMTP Port</label>
            <input type="number" placeholder="587" className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input type="email" placeholder="your-email@gmail.com" className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input type="password" className="w-full px-3 py-2 border rounded-lg" />
          </div>
        </div>
        <button className="btn-primary mt-4 flex items-center gap-2">
          <Save size={18} />
          Save Email Settings
        </button>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return renderGeneralSettings()
      case 'database':
        return renderDatabaseFields()
      case 'api':
        return renderAPIKeys()
      default:
        return (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Settings className="mx-auto mb-2 text-gray-300" size={48} />
            <p className="text-gray-500">This section is coming soon</p>
          </div>
        )
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Manage system configuration and preferences</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <div className="lg:w-64 space-y-1">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <Icon size={20} />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Content */}
          <div className="flex-1">
            {loading ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : (
              renderTabContent()
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
