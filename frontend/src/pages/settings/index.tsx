/**
 * Settings Page
 * صفحه تنظیمات سیستم
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { settingsApi, aiProvidersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  Settings, Database, Users, Bell, Shield, Palette, Globe, Key, Save, Plus, Trash2, Edit,
  Brain, CheckCircle, XCircle, RefreshCw, Eye, EyeOff, Zap, AlertCircle, Loader2, Star
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

interface AIProvider {
  provider_id: string
  name: string
  enabled: boolean
  has_api_key: boolean
  base_url?: string
  default_model?: string
  provider_type: string
  available_models: string[]
  status: 'connected' | 'disconnected' | 'error' | 'unknown'
}

interface KnownProvider {
  id: string
  name: string
  provider_type: string
  default_base_url: string
  known_models: string[]
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [customFields, setCustomFields] = useState<CustomField[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // AI Providers state
  const [providers, setProviders] = useState<AIProvider[]>([])
  const [knownProviders, setKnownProviders] = useState<KnownProvider[]>([])
  const [defaultProvider, setDefaultProvider] = useState<string>('')
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null)
  const [showProviderForm, setShowProviderForm] = useState(false)
  const [providerForm, setProviderForm] = useState({
    provider_id: '',
    name: '',
    api_key: '',
    base_url: '',
    default_model: '',
    provider_type: 'openai_compatible',
    enabled: true
  })
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})
  const [testingProvider, setTestingProvider] = useState<string | null>(null)
  const [fetchingModels, setFetchingModels] = useState<string | null>(null)
  const [providerModels, setProviderModels] = useState<Record<string, string[]>>({})

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

  // General settings form
  const [generalForm, setGeneralForm] = useState({
    app_name: 'Banking Ops',
    currency: 'AED',
    date_format: 'DD/MM/YYYY',
    language: 'en'
  })

  // Security settings
  const [securityForm, setSecurityForm] = useState({
    session_timeout: 30,
    max_login_attempts: 5,
    password_min_length: 8,
    require_2fa: false,
    ip_whitelist: ''
  })

  // Notification settings
  const [notificationForm, setNotificationForm] = useState({
    email_notifications: true,
    expiry_alerts: true,
    expiry_alert_days: 30,
    task_reminders: true,
    daily_digest: false
  })

  // Appearance settings
  const [appearanceForm, setAppearanceForm] = useState({
    theme: 'light',
    sidebar_collapsed: false,
    dense_mode: false,
    primary_color: '#2563eb'
  })

  // API Keys form
  const [apiKeysForm, setApiKeysForm] = useState({
    openai_key: '',
    anthropic_key: '',
    google_key: ''
  })

  // Email settings form
  const [emailForm, setEmailForm] = useState({
    smtp_host: '',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: ''
  })

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'ai-providers', label: 'AI Providers', icon: Brain },
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

  useEffect(() => {
    if (activeTab === 'ai-providers') {
      fetchAIProviders()
    }
  }, [activeTab])

  const fetchSettings = async () => {
    setLoading(true)
    try {
      // Get user settings first (accessible by all users)
      const userResponse = await settingsApi.getUser()
      if (userResponse.data?.settings) {
        const s = userResponse.data.settings
        if (s.theme) setAppearanceForm(prev => ({ ...prev, theme: s.theme }))
        if (s.notifications_enabled !== undefined) {
          setNotificationForm(prev => ({
            ...prev,
            email_notifications: s.email_notifications ?? true,
            task_reminders: s.task_reminders ?? true
          }))
        }
      }

      // Try to get system settings (only works for admin/manager)
      try {
        const response = await settingsApi.getSystem()
        setSettings(response.data.items || response.data.settings || [])
      } catch (err: any) {
        // Ignore 401/403 - user might not have admin access
        if (err.response?.status !== 401 && err.response?.status !== 403) {
          console.error('Error fetching system settings:', err)
        }
      }

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

  const fetchAIProviders = async () => {
    try {
      const [providersRes, knownRes, defaultRes] = await Promise.all([
        aiProvidersApi.list(),
        aiProvidersApi.getKnown(),
        aiProvidersApi.getDefault()
      ])

      setProviders(providersRes.data || [])
      setKnownProviders(knownRes.data.providers || [])
      setDefaultProvider(defaultRes.data.provider_id || 'openai')

      // Initialize models from known_models
      const models: Record<string, string[]> = {}
      providersRes.data?.forEach((p: AIProvider) => {
        models[p.provider_id] = p.available_models || []
      })
      setProviderModels(models)
    } catch (error) {
      console.error('Error fetching AI providers:', error)
      toast.error('Failed to load AI providers')
    }
  }

  const handleTestProvider = async (providerId: string) => {
    setTestingProvider(providerId)
    try {
      const response = await aiProvidersApi.test(providerId)
      if (response.data.status === 'connected') {
        toast.success('Connection successful!')
        // Update provider status
        setProviders(prev => prev.map(p =>
          p.provider_id === providerId ? { ...p, status: 'connected' } : p
        ))
      } else {
        toast.error(response.data.message || 'Connection failed')
        setProviders(prev => prev.map(p =>
          p.provider_id === providerId ? { ...p, status: 'error' } : p
        ))
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Connection test failed')
    } finally {
      setTestingProvider(null)
    }
  }

  const handleFetchModels = async (providerId: string) => {
    setFetchingModels(providerId)
    try {
      const response = await aiProvidersApi.fetchModels(providerId)
      setProviderModels(prev => ({
        ...prev,
        [providerId]: response.data.models || []
      }))
      toast.success(`Found ${response.data.count} models`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to fetch models')
    } finally {
      setFetchingModels(null)
    }
  }

  const handleSaveProvider = async () => {
    if (!providerForm.api_key && !editingProvider?.has_api_key) {
      toast.error('API Key is required')
      return
    }

    setSaving(true)
    try {
      const data: any = {
        enabled: providerForm.enabled,
        default_model: providerForm.default_model || undefined
      }

      if (providerForm.api_key) {
        data.api_key = providerForm.api_key
      }
      if (providerForm.base_url) {
        data.base_url = providerForm.base_url
      }
      if (providerForm.name) {
        data.name = providerForm.name
      }

      if (editingProvider) {
        await aiProvidersApi.update(editingProvider.provider_id, data)
        toast.success('Provider updated')
      } else {
        await aiProvidersApi.create({
          ...data,
          provider_id: providerForm.provider_id,
          name: providerForm.name,
          provider_type: providerForm.provider_type
        })
        toast.success('Provider added')
      }

      setShowProviderForm(false)
      setEditingProvider(null)
      resetProviderForm()
      fetchAIProviders()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save provider')
    } finally {
      setSaving(false)
    }
  }

  const handleSetDefaultProvider = async (providerId: string) => {
    try {
      await aiProvidersApi.setDefault(providerId)
      setDefaultProvider(providerId)
      toast.success('Default provider updated')
    } catch (error) {
      toast.error('Failed to set default provider')
    }
  }

  const resetProviderForm = () => {
    setProviderForm({
      provider_id: '',
      name: '',
      api_key: '',
      base_url: '',
      default_model: '',
      provider_type: 'openai_compatible',
      enabled: true
    })
  }

  const openEditProvider = (provider: AIProvider) => {
    setEditingProvider(provider)
    setProviderForm({
      provider_id: provider.provider_id,
      name: provider.name,
      api_key: '',
      base_url: provider.base_url || '',
      default_model: provider.default_model || '',
      provider_type: provider.provider_type,
      enabled: provider.enabled
    })
    setShowProviderForm(true)
  }

  const openAddProvider = (known?: KnownProvider) => {
    setEditingProvider(null)
    if (known) {
      setProviderForm({
        provider_id: known.id,
        name: known.name,
        api_key: '',
        base_url: known.default_base_url,
        default_model: known.known_models[0] || '',
        provider_type: known.provider_type,
        enabled: true
      })
      setProviderModels(prev => ({
        ...prev,
        [known.id]: known.known_models
      }))
    } else {
      resetProviderForm()
    }
    setShowProviderForm(true)
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

  // Save general settings (admin only)
  const handleSaveGeneral = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(generalForm)
      toast.success('General settings saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  // Save notification preferences (user settings)
  const handleSaveNotifications = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(notificationForm)
      toast.success('Notification preferences saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  // Save security settings (admin only)
  const handleSaveSecurity = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(securityForm)
      toast.success('Security settings saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save security settings')
    } finally {
      setSaving(false)
    }
  }

  // Save appearance settings (user settings)
  const handleSaveAppearance = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(appearanceForm)
      toast.success('Appearance settings saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save appearance')
    } finally {
      setSaving(false)
    }
  }

  // Save API Keys - updates AI providers with API keys
  const handleSaveApiKeys = async () => {
    setSaving(true)
    try {
      const promises = []

      // Update OpenAI if key provided
      if (apiKeysForm.openai_key) {
        promises.push(
          aiProvidersApi.update('openai', {
            api_key: apiKeysForm.openai_key,
            enabled: true
          }).catch(() =>
            aiProvidersApi.create({
              provider_id: 'openai',
              name: 'OpenAI',
              api_key: apiKeysForm.openai_key,
              provider_type: 'openai',
              enabled: true
            })
          )
        )
      }

      // Update Anthropic if key provided
      if (apiKeysForm.anthropic_key) {
        promises.push(
          aiProvidersApi.update('anthropic', {
            api_key: apiKeysForm.anthropic_key,
            enabled: true
          }).catch(() =>
            aiProvidersApi.create({
              provider_id: 'anthropic',
              name: 'Anthropic (Claude)',
              api_key: apiKeysForm.anthropic_key,
              provider_type: 'anthropic',
              enabled: true
            })
          )
        )
      }

      // Update Google if key provided
      if (apiKeysForm.google_key) {
        promises.push(
          aiProvidersApi.update('google', {
            api_key: apiKeysForm.google_key,
            enabled: true
          }).catch(() =>
            aiProvidersApi.create({
              provider_id: 'google',
              name: 'Google AI (Gemini)',
              api_key: apiKeysForm.google_key,
              provider_type: 'google',
              enabled: true
            })
          )
        )
      }

      if (promises.length === 0) {
        toast.error('Please enter at least one API key')
        return
      }

      await Promise.all(promises)
      toast.success('API keys saved successfully')

      // Clear the form
      setApiKeysForm({ openai_key: '', anthropic_key: '', google_key: '' })

      // Refresh providers list if on that tab
      if (activeTab === 'ai-providers') {
        fetchAIProviders()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save API keys')
    } finally {
      setSaving(false)
    }
  }

  // Save email settings
  const handleSaveEmailSettings = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser({
        smtp_host: emailForm.smtp_host,
        smtp_port: parseInt(emailForm.smtp_port),
        smtp_username: emailForm.smtp_username,
        smtp_password: emailForm.smtp_password
      })
      toast.success('Email settings saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save email settings')
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

  const getProviderStatusIcon = (provider: AIProvider) => {
    if (testingProvider === provider.provider_id) {
      return <Loader2 className="animate-spin text-blue-500" size={18} />
    }
    if (!provider.has_api_key) {
      return <AlertCircle className="text-gray-400" size={18} />
    }
    switch (provider.status) {
      case 'connected':
        return <CheckCircle className="text-green-500" size={18} />
      case 'error':
        return <XCircle className="text-red-500" size={18} />
      default:
        return <AlertCircle className="text-yellow-500" size={18} />
    }
  }

  const renderGeneralSettings = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Application Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Application Name</label>
            <input
              type="text"
              value={generalForm.app_name}
              onChange={(e) => setGeneralForm({ ...generalForm, app_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Default Currency</label>
            <select
              value={generalForm.currency}
              onChange={(e) => setGeneralForm({ ...generalForm, currency: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="AED">AED - UAE Dirham</option>
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="IRR">IRR - Iranian Rial</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date Format</label>
            <select
              value={generalForm.date_format}
              onChange={(e) => setGeneralForm({ ...generalForm, date_format: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Language</label>
            <select
              value={generalForm.language}
              onChange={(e) => setGeneralForm({ ...generalForm, language: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="en">English</option>
              <option value="fa">فارسی</option>
              <option value="ar">العربية</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleSaveGeneral}
          disabled={saving}
          className="btn-primary mt-4 flex items-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Changes
        </button>
      </div>
    </div>
  )

  const renderAIProviders = () => (
    <div className="space-y-6">
      {/* Default Provider Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Star className="text-yellow-500" size={20} />
          Default AI Provider
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Select the default provider for AI operations
        </p>
        <select
          value={defaultProvider}
          onChange={(e) => handleSetDefaultProvider(e.target.value)}
          className="w-full max-w-md px-3 py-2 border rounded-lg"
        >
          {providers.filter(p => p.enabled && p.has_api_key).map(p => (
            <option key={p.provider_id} value={p.provider_id}>{p.name}</option>
          ))}
        </select>
      </div>

      {/* Configured Providers */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="font-medium">AI Providers</h3>
            <p className="text-sm text-gray-500">Configure your AI service providers</p>
          </div>
          <button
            onClick={() => openAddProvider()}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={18} />
            Add Custom Provider
          </button>
        </div>

        <div className="space-y-4">
          {providers.map(provider => (
            <div
              key={provider.provider_id}
              className={`border rounded-lg p-4 ${provider.enabled ? 'border-blue-200 bg-blue-50/30' : 'border-gray-200'}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getProviderStatusIcon(provider)}
                  <div>
                    <h4 className="font-medium flex items-center gap-2">
                      {provider.name}
                      {defaultProvider === provider.provider_id && (
                        <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">Default</span>
                      )}
                    </h4>
                    <p className="text-sm text-gray-500">
                      {provider.provider_type} {provider.base_url && `- ${provider.base_url}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {provider.has_api_key && (
                    <>
                      <button
                        onClick={() => handleFetchModels(provider.provider_id)}
                        disabled={fetchingModels === provider.provider_id}
                        className="p-2 hover:bg-white rounded-lg text-gray-600"
                        title="Fetch models from API"
                      >
                        {fetchingModels === provider.provider_id ? (
                          <Loader2 className="animate-spin" size={18} />
                        ) : (
                          <RefreshCw size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => handleTestProvider(provider.provider_id)}
                        disabled={testingProvider === provider.provider_id}
                        className="p-2 hover:bg-white rounded-lg text-gray-600"
                        title="Test connection"
                      >
                        <Zap size={18} />
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => openEditProvider(provider)}
                    className="p-2 hover:bg-white rounded-lg text-gray-600"
                  >
                    <Edit size={18} />
                  </button>
                </div>
              </div>

              {/* Models */}
              {provider.has_api_key && (providerModels[provider.provider_id]?.length > 0 || provider.available_models?.length > 0) && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs text-gray-500 mb-2">Available Models:</p>
                  <div className="flex flex-wrap gap-1">
                    {(providerModels[provider.provider_id] || provider.available_models || []).slice(0, 8).map(model => (
                      <span
                        key={model}
                        className={`text-xs px-2 py-1 rounded ${
                          provider.default_model === model
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {model}
                      </span>
                    ))}
                    {(providerModels[provider.provider_id] || provider.available_models || []).length > 8 && (
                      <span className="text-xs text-gray-500 px-2 py-1">
                        +{(providerModels[provider.provider_id] || provider.available_models).length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {!provider.has_api_key && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-sm text-gray-500">
                    <AlertCircle className="inline mr-1" size={14} />
                    No API key configured - click Edit to add one
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Add from Known Providers */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Quick Add Provider</h3>
        <p className="text-sm text-gray-500 mb-4">
          Click on a provider to quickly configure it
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {knownProviders.filter(k => !providers.find(p => p.provider_id === k.id && p.has_api_key)).map(known => (
            <button
              key={known.id}
              onClick={() => openAddProvider(known)}
              className="p-3 border rounded-lg hover:border-blue-300 hover:bg-blue-50 text-left transition-colors"
            >
              <p className="font-medium text-sm">{known.name}</p>
              <p className="text-xs text-gray-500 mt-1">{known.known_models.length} models</p>
            </button>
          ))}
        </div>
      </div>

      {/* Provider Form Modal */}
      {showProviderForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b sticky top-0 bg-white">
              <h2 className="text-lg font-semibold">
                {editingProvider ? `Configure ${editingProvider.name}` : 'Add AI Provider'}
              </h2>
            </div>
            <div className="p-4 space-y-4">
              {!editingProvider && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Provider ID *</label>
                    <input
                      type="text"
                      value={providerForm.provider_id}
                      onChange={(e) => setProviderForm({ ...providerForm, provider_id: e.target.value })}
                      placeholder="e.g., my-custom-llm"
                      className="w-full px-3 py-2 border rounded-lg"
                      disabled={!!editingProvider}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Display Name *</label>
                    <input
                      type="text"
                      value={providerForm.name}
                      onChange={(e) => setProviderForm({ ...providerForm, name: e.target.value })}
                      placeholder="e.g., My Custom LLM"
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Provider Type</label>
                    <select
                      value={providerForm.provider_type}
                      onChange={(e) => setProviderForm({ ...providerForm, provider_type: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="openai_compatible">OpenAI Compatible</option>
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic</option>
                      <option value="google">Google</option>
                      <option value="ollama">Ollama (Local)</option>
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium mb-1">
                  API Key {editingProvider?.has_api_key ? '(leave empty to keep existing)' : '*'}
                </label>
                <div className="relative">
                  <input
                    type={showApiKey['form'] ? 'text' : 'password'}
                    value={providerForm.api_key}
                    onChange={(e) => setProviderForm({ ...providerForm, api_key: e.target.value })}
                    placeholder={editingProvider?.has_api_key ? '••••••••••••••••' : 'Enter API key'}
                    className="w-full px-3 py-2 border rounded-lg font-mono pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(prev => ({ ...prev, form: !prev.form }))}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showApiKey['form'] ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Base URL (optional)</label>
                <input
                  type="text"
                  value={providerForm.base_url}
                  onChange={(e) => setProviderForm({ ...providerForm, base_url: e.target.value })}
                  placeholder="https://api.example.com/v1"
                  className="w-full px-3 py-2 border rounded-lg"
                />
                <p className="text-xs text-gray-500 mt-1">Leave empty to use default URL</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Default Model</label>
                <select
                  value={providerForm.default_model}
                  onChange={(e) => setProviderForm({ ...providerForm, default_model: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="">Select a model...</option>
                  {(providerModels[providerForm.provider_id] || []).map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Save with API key first, then fetch models to see available options
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={providerForm.enabled}
                  onChange={(e) => setProviderForm({ ...providerForm, enabled: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="enabled" className="text-sm">Enable this provider</label>
              </div>
            </div>
            <div className="p-4 border-t flex justify-end gap-3 sticky bottom-0 bg-white">
              <button
                onClick={() => {
                  setShowProviderForm(false)
                  setEditingProvider(null)
                  resetProviderForm()
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProvider}
                disabled={saving}
                className="btn-primary flex items-center gap-2"
              >
                {saving && <Loader2 className="animate-spin" size={18} />}
                {editingProvider ? 'Update' : 'Add'} Provider
              </button>
            </div>
          </div>
        </div>
      )}
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

  const renderUsersRoles = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">User Management</h3>
        <p className="text-sm text-gray-500 mb-6">Manage system users and their access roles</p>

        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">User</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Email</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Role</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="px-4 py-3">Admin User</td>
                <td className="px-4 py-3 text-gray-600">admin@example.com</td>
                <td className="px-4 py-3">
                  <span className="badge bg-purple-100 text-purple-800">Admin</span>
                </td>
                <td className="px-4 py-3">
                  <span className="badge bg-green-100 text-green-800">Active</span>
                </td>
                <td className="px-4 py-3">
                  <button className="p-1 hover:bg-gray-100 rounded"><Edit size={16} /></button>
                </td>
              </tr>
              <tr className="border-t">
                <td className="px-4 py-3">Manager User</td>
                <td className="px-4 py-3 text-gray-600">manager@example.com</td>
                <td className="px-4 py-3">
                  <span className="badge bg-blue-100 text-blue-800">Manager</span>
                </td>
                <td className="px-4 py-3">
                  <span className="badge bg-green-100 text-green-800">Active</span>
                </td>
                <td className="px-4 py-3">
                  <button className="p-1 hover:bg-gray-100 rounded"><Edit size={16} /></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <button className="btn-primary mt-4 flex items-center gap-2">
          <Plus size={18} />
          Add User
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Role Permissions</h3>
        <div className="space-y-3">
          {['Admin', 'Manager', 'User', 'Viewer'].map(role => (
            <div key={role} className="flex items-center justify-between p-3 border rounded-lg">
              <div>
                <p className="font-medium">{role}</p>
                <p className="text-sm text-gray-500">
                  {role === 'Admin' && 'Full system access'}
                  {role === 'Manager' && 'Manage customers, facilities, and reports'}
                  {role === 'User' && 'View and edit assigned items'}
                  {role === 'Viewer' && 'View only access'}
                </p>
              </div>
              <button className="text-blue-600 text-sm hover:underline">Configure</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderNotifications = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Notification Preferences</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">Email Notifications</p>
              <p className="text-sm text-gray-500">Receive notifications via email</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationForm.email_notifications}
                onChange={(e) => setNotificationForm({ ...notificationForm, email_notifications: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">Expiry Alerts</p>
              <p className="text-sm text-gray-500">Get notified before documents expire</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationForm.expiry_alerts}
                onChange={(e) => setNotificationForm({ ...notificationForm, expiry_alerts: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>

          {notificationForm.expiry_alerts && (
            <div className="ml-4 p-3 bg-gray-50 rounded-lg">
              <label className="block text-sm font-medium mb-2">Days before expiry to alert</label>
              <input
                type="number"
                value={notificationForm.expiry_alert_days}
                onChange={(e) => setNotificationForm({ ...notificationForm, expiry_alert_days: parseInt(e.target.value) })}
                className="w-24 px-3 py-2 border rounded-lg"
                min={1}
                max={90}
              />
            </div>
          )}

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">Task Reminders</p>
              <p className="text-sm text-gray-500">Get reminded about pending tasks</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationForm.task_reminders}
                onChange={(e) => setNotificationForm({ ...notificationForm, task_reminders: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div>
              <p className="font-medium">Daily Digest</p>
              <p className="text-sm text-gray-500">Receive a daily summary email</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationForm.daily_digest}
                onChange={(e) => setNotificationForm({ ...notificationForm, daily_digest: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
          </div>
        </div>

        <button
          onClick={handleSaveNotifications}
          disabled={saving}
          className="btn-primary mt-6 flex items-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Preferences
        </button>
      </div>
    </div>
  )

  const renderSecurity = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Session Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Session Timeout (minutes)</label>
            <input
              type="number"
              value={securityForm.session_timeout}
              onChange={(e) => setSecurityForm({ ...securityForm, session_timeout: parseInt(e.target.value) })}
              className="w-32 px-3 py-2 border rounded-lg"
              min={5}
              max={480}
            />
            <p className="text-xs text-gray-500 mt-1">Auto logout after inactivity</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Max Login Attempts</label>
            <input
              type="number"
              value={securityForm.max_login_attempts}
              onChange={(e) => setSecurityForm({ ...securityForm, max_login_attempts: parseInt(e.target.value) })}
              className="w-32 px-3 py-2 border rounded-lg"
              min={3}
              max={10}
            />
            <p className="text-xs text-gray-500 mt-1">Lock account after failed attempts</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Password Policy</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Minimum Password Length</label>
            <input
              type="number"
              value={securityForm.password_min_length}
              onChange={(e) => setSecurityForm({ ...securityForm, password_min_length: parseInt(e.target.value) })}
              className="w-32 px-3 py-2 border rounded-lg"
              min={6}
              max={32}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="require_2fa"
              checked={securityForm.require_2fa}
              onChange={(e) => setSecurityForm({ ...securityForm, require_2fa: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="require_2fa" className="text-sm">Require Two-Factor Authentication</label>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">IP Whitelist</h3>
        <p className="text-sm text-gray-500 mb-3">Restrict access to specific IP addresses</p>
        <textarea
          value={securityForm.ip_whitelist}
          onChange={(e) => setSecurityForm({ ...securityForm, ip_whitelist: e.target.value })}
          placeholder="192.168.1.1&#10;10.0.0.0/24"
          className="w-full px-3 py-2 border rounded-lg h-24 font-mono text-sm"
        />
        <p className="text-xs text-gray-500 mt-1">One IP or CIDR range per line. Leave empty to allow all.</p>
      </div>

      <button
        onClick={handleSaveSecurity}
        disabled={saving}
        className="btn-primary flex items-center gap-2"
      >
        {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
        Save Security Settings
      </button>
    </div>
  )

  const renderAppearance = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Theme</h3>
        <div className="grid grid-cols-3 gap-4">
          {[
            { id: 'light', label: 'Light', bg: 'bg-white', text: 'text-gray-900' },
            { id: 'dark', label: 'Dark', bg: 'bg-gray-900', text: 'text-white' },
            { id: 'system', label: 'System', bg: 'bg-gradient-to-r from-white to-gray-900', text: 'text-gray-600' }
          ].map(theme => (
            <button
              key={theme.id}
              onClick={() => setAppearanceForm({ ...appearanceForm, theme: theme.id })}
              className={`p-4 border-2 rounded-lg transition-colors ${
                appearanceForm.theme === theme.id ? 'border-blue-500' : 'border-gray-200'
              }`}
            >
              <div className={`h-16 rounded ${theme.bg} ${theme.text} flex items-center justify-center mb-2 border`}>
                Aa
              </div>
              <p className="text-sm font-medium">{theme.label}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Primary Color</h3>
        <div className="flex gap-3">
          {['#2563eb', '#7c3aed', '#059669', '#dc2626', '#ea580c', '#0891b2'].map(color => (
            <button
              key={color}
              onClick={() => setAppearanceForm({ ...appearanceForm, primary_color: color })}
              className={`w-10 h-10 rounded-full border-2 transition-transform hover:scale-110 ${
                appearanceForm.primary_color === color ? 'border-gray-900 scale-110' : 'border-transparent'
              }`}
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Display Options</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="sidebar_collapsed"
              checked={appearanceForm.sidebar_collapsed}
              onChange={(e) => setAppearanceForm({ ...appearanceForm, sidebar_collapsed: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="sidebar_collapsed" className="text-sm">Start with collapsed sidebar</label>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="dense_mode"
              checked={appearanceForm.dense_mode}
              onChange={(e) => setAppearanceForm({ ...appearanceForm, dense_mode: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="dense_mode" className="text-sm">Dense mode (compact spacing)</label>
          </div>
        </div>
      </div>

      <button
        onClick={handleSaveAppearance}
        disabled={saving}
        className="btn-primary flex items-center gap-2"
      >
        {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
        Save Appearance
      </button>
    </div>
  )

  const renderIntegrations = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Google Drive Integration</h3>
        <p className="text-sm text-gray-500 mb-4">Sync documents and attachments with Google Drive</p>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Globe className="text-blue-600" size={20} />
              </div>
              <div>
                <p className="font-medium">Google Drive</p>
                <p className="text-sm text-gray-500">Not connected</p>
              </div>
            </div>
            <button className="btn-primary">Connect</button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Webhooks</h3>
        <p className="text-sm text-gray-500 mb-4">Send data to external services when events occur</p>

        <button className="btn-outline flex items-center gap-2">
          <Plus size={18} />
          Add Webhook
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Export & Import</h3>
        <div className="flex gap-3">
          <button className="btn-outline">Export All Data</button>
          <button className="btn-outline">Import Data</button>
        </div>
      </div>
    </div>
  )

  const renderAPIKeys = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">AI Provider API Keys</h3>
        <p className="text-sm text-gray-500 mb-6">
          Configure your AI provider API keys. Go to <button onClick={() => setActiveTab('ai-providers')} className="text-blue-600 hover:underline">AI Providers</button> tab for full management.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">OpenAI API Key</label>
            <input
              type="password"
              placeholder="sk-..."
              value={apiKeysForm.openai_key}
              onChange={(e) => setApiKeysForm({ ...apiKeysForm, openai_key: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Anthropic API Key (Claude)</label>
            <input
              type="password"
              placeholder="sk-ant-..."
              value={apiKeysForm.anthropic_key}
              onChange={(e) => setApiKeysForm({ ...apiKeysForm, anthropic_key: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Google AI API Key (Gemini)</label>
            <input
              type="password"
              placeholder="AIza..."
              value={apiKeysForm.google_key}
              onChange={(e) => setApiKeysForm({ ...apiKeysForm, google_key: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg font-mono"
            />
          </div>
        </div>

        <button
          onClick={handleSaveApiKeys}
          disabled={saving}
          className="btn-primary mt-6 flex items-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save API Keys
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4">Email Configuration (SMTP)</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">SMTP Host</label>
            <input
              type="text"
              placeholder="smtp.gmail.com"
              value={emailForm.smtp_host}
              onChange={(e) => setEmailForm({ ...emailForm, smtp_host: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">SMTP Port</label>
            <input
              type="number"
              placeholder="587"
              value={emailForm.smtp_port}
              onChange={(e) => setEmailForm({ ...emailForm, smtp_port: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              type="email"
              placeholder="your-email@gmail.com"
              value={emailForm.smtp_username}
              onChange={(e) => setEmailForm({ ...emailForm, smtp_username: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={emailForm.smtp_password}
              onChange={(e) => setEmailForm({ ...emailForm, smtp_password: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
        </div>
        <button
          onClick={handleSaveEmailSettings}
          disabled={saving}
          className="btn-primary mt-4 flex items-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Email Settings
        </button>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return renderGeneralSettings()
      case 'ai-providers':
        return renderAIProviders()
      case 'database':
        return renderDatabaseFields()
      case 'users':
        return renderUsersRoles()
      case 'notifications':
        return renderNotifications()
      case 'security':
        return renderSecurity()
      case 'appearance':
        return renderAppearance()
      case 'integrations':
        return renderIntegrations()
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
