/**
 * Settings Page v2.0
 * صفحه تنظیمات سیستم
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Layout from '@/components/Layout'
import { settingsApi, aiApi } from '@/services/api'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'react-hot-toast'
import {
  Settings, Users, Bell, Shield, Palette, Key, Save, Brain,
  CheckCircle, XCircle, Loader2, Eye, EyeOff
} from 'lucide-react'

export default function SettingsPage() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('general')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // AI Providers state
  const [aiStatus, setAiStatus] = useState<any>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [apiKeyForm, setApiKeyForm] = useState({
    provider: 'openai',
    api_key: '',
    model: ''
  })

  // General settings
  const [generalForm, setGeneralForm] = useState({
    app_name: 'Banking Ops',
    currency: 'AED',
    date_format: 'DD/MM/YYYY',
    language: 'en'
  })

  // Notification settings
  const [notificationForm, setNotificationForm] = useState({
    email_notifications: true,
    expiry_alerts: true,
    expiry_alert_days: 30
  })

  // Appearance settings
  const [theme, setTheme] = useState('light')

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'ai', label: 'AI Providers', icon: Brain },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'security', label: 'Security', icon: Shield },
  ]

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchSettings()
      fetchAIStatus()
    }
  }, [isAuthenticated])

  const fetchSettings = async () => {
    setLoading(true)
    try {
      const response = await settingsApi.getUser()
      if (response.data) {
        const s = response.data
        if (s.theme) setTheme(s.theme)
        if (s.email_notifications !== undefined) {
          setNotificationForm(prev => ({
            ...prev,
            email_notifications: s.email_notifications ?? true
          }))
        }
      }
    } catch (error) {
      console.error('Error fetching settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAIStatus = async () => {
    try {
      const response = await aiApi.status()
      setAiStatus(response.data)
    } catch (error) {
      console.error('Error fetching AI status:', error)
    }
  }

  const handleSaveGeneral = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(generalForm)
      toast.success('Settings saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveNotifications = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser(notificationForm)
      toast.success('Notification preferences saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAppearance = async () => {
    setSaving(true)
    try {
      await settingsApi.updateUser({ theme })
      document.documentElement.classList.toggle('dark', theme === 'dark')
      toast.success('Appearance saved')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleAddAIProvider = async () => {
    if (!apiKeyForm.api_key) {
      toast.error('API Key is required')
      return
    }

    setSaving(true)
    try {
      await aiApi.addProvider(
        apiKeyForm.provider,
        apiKeyForm.api_key,
        apiKeyForm.model || undefined
      )
      toast.success('AI Provider configured')
      setApiKeyForm({ provider: 'openai', api_key: '', model: '' })
      fetchAIStatus()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add provider')
    } finally {
      setSaving(false)
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

  const renderGeneral = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Application Settings</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Application Name</label>
            <input
              type="text"
              value={generalForm.app_name}
              onChange={(e) => setGeneralForm({ ...generalForm, app_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Default Currency</label>
            <select
              value={generalForm.currency}
              onChange={(e) => setGeneralForm({ ...generalForm, currency: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="AED">AED - UAE Dirham</option>
              <option value="USD">USD - US Dollar</option>
              <option value="EUR">EUR - Euro</option>
              <option value="IRR">IRR - Iranian Rial</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Date Format</label>
            <select
              value={generalForm.date_format}
              onChange={(e) => setGeneralForm({ ...generalForm, date_format: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
            <select
              value={generalForm.language}
              onChange={(e) => setGeneralForm({ ...generalForm, language: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Changes
        </button>
      </div>
    </div>
  )

  const renderAI = () => (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">AI Provider Status</h3>
        {aiStatus ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium">Available Providers</span>
              <span className="text-sm text-gray-600">
                {aiStatus.available_providers?.length || 0} configured
              </span>
            </div>
            {aiStatus.available_providers?.map((provider: string) => (
              <div key={provider} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="text-green-500" size={18} />
                  <span className="font-medium capitalize">{provider}</span>
                </div>
                {aiStatus.default_provider === provider && (
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">Default</span>
                )}
              </div>
            ))}
            {(!aiStatus.available_providers || aiStatus.available_providers.length === 0) && (
              <div className="text-center py-4 text-gray-500">
                <XCircle className="mx-auto mb-2 text-gray-300" size={32} />
                <p>No AI providers configured</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-4">
            <Loader2 className="animate-spin mx-auto text-gray-400" size={24} />
          </div>
        )}
      </div>

      {/* Add Provider */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Add AI Provider</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
            <select
              value={apiKeyForm.provider}
              onChange={(e) => setApiKeyForm({ ...apiKeyForm, provider: e.target.value })}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="openai">OpenAI (GPT-4)</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="google">Google (Gemini)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={apiKeyForm.api_key}
                onChange={(e) => setApiKeyForm({ ...apiKeyForm, api_key: e.target.value })}
                placeholder="Enter your API key..."
                className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-lg font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model (Optional)</label>
            <input
              type="text"
              value={apiKeyForm.model}
              onChange={(e) => setApiKeyForm({ ...apiKeyForm, model: e.target.value })}
              placeholder="e.g., gpt-4-turbo-preview"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty to use default model</p>
          </div>
        </div>
        <button
          onClick={handleAddAIProvider}
          disabled={saving || !apiKeyForm.api_key}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Key size={18} />}
          Configure Provider
        </button>
      </div>
    </div>
  )

  const renderNotifications = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Notification Preferences</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-100 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Email Notifications</p>
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

          <div className="flex items-center justify-between p-4 border border-gray-100 rounded-lg">
            <div>
              <p className="font-medium text-gray-900">Expiry Alerts</p>
              <p className="text-sm text-gray-500">Get notified before facilities expire</p>
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
            <div className="ml-4 p-4 bg-gray-50 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">Days before expiry to alert</label>
              <input
                type="number"
                value={notificationForm.expiry_alert_days}
                onChange={(e) => setNotificationForm({ ...notificationForm, expiry_alert_days: parseInt(e.target.value) })}
                className="w-24 px-3 py-2 border border-gray-200 rounded-lg"
                min={1}
                max={90}
              />
            </div>
          )}
        </div>
        <button
          onClick={handleSaveNotifications}
          disabled={saving}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Preferences
        </button>
      </div>
    </div>
  )

  const renderAppearance = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Theme</h3>
        <div className="grid grid-cols-3 gap-4">
          {[
            { id: 'light', label: 'Light', bg: 'bg-white border-gray-200', text: 'text-gray-900' },
            { id: 'dark', label: 'Dark', bg: 'bg-gray-900', text: 'text-white' },
            { id: 'system', label: 'System', bg: 'bg-gradient-to-r from-white to-gray-900', text: 'text-gray-600' }
          ].map(themeOption => (
            <button
              key={themeOption.id}
              onClick={() => setTheme(themeOption.id)}
              className={`p-4 border-2 rounded-xl transition-colors ${
                theme === themeOption.id ? 'border-blue-500' : 'border-gray-200'
              }`}
            >
              <div className={`h-16 rounded-lg ${themeOption.bg} ${themeOption.text} flex items-center justify-center mb-2 border`}>
                Aa
              </div>
              <p className="text-sm font-medium">{themeOption.label}</p>
            </button>
          ))}
        </div>
        <button
          onClick={handleSaveAppearance}
          disabled={saving}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
          Save Appearance
        </button>
      </div>
    </div>
  )

  const renderSecurity = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Account Information</h3>
        <div className="space-y-3">
          <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-600">Username</span>
            <span className="font-medium">{user?.username}</span>
          </div>
          <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-600">Email</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
            <span className="text-gray-600">Role</span>
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-sm rounded-full capitalize">{user?.role}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Change Password</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        <button
          onClick={() => toast('Password change functionality coming soon')}
          className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Shield size={18} />
          Change Password
        </button>
      </div>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return renderGeneral()
      case 'ai':
        return renderAI()
      case 'notifications':
        return renderNotifications()
      case 'appearance':
        return renderAppearance()
      case 'security':
        return renderSecurity()
      default:
        return null
    }
  }

  return (
    <Layout>
      <Head>
        <title>Settings | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500">Manage your preferences and configuration</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar */}
          <div className="lg:w-56 space-y-1">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                      : 'hover:bg-gray-100 text-gray-700'
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
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
                <Loader2 className="animate-spin mx-auto text-blue-600" size={32} />
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
