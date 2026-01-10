/**
 * Profile Page
 * صفحه پروفایل کاربر
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  User, Mail, Phone, Building, Briefcase, Globe, Clock, Camera,
  Edit, Save, Key, Shield, Activity, LogOut, Trash2, Eye, EyeOff
} from 'lucide-react'

interface UserProfile {
  id: string
  username: string
  email: string | null
  full_name: string | null
  phone: string | null
  department: string | null
  position: string | null
  role: string
  avatar_url: string | null
  language: string
  timezone: string
  bio: string | null
  is_active: boolean
  last_login: string | null
  created_at: string | null
}

interface UserActivity {
  id: string
  action: string
  description: string
  timestamp: string
  entity_type?: string
  entity_id?: string
}

interface UserSession {
  id: string
  device: string
  ip_address: string
  location: string
  last_active: string
  is_current: boolean
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [activities, setActivities] = useState<UserActivity[]>([])
  const [sessions, setSessions] = useState<UserSession[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('profile')
  const [editMode, setEditMode] = useState(false)

  // Edit form state
  const [editForm, setEditForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    department: '',
    position: '',
    bio: '',
    language: 'en',
    timezone: 'Asia/Dubai'
  })

  // Password change form
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  })

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'activity', label: 'Activity', icon: Activity },
    { id: 'sessions', label: 'Sessions', icon: Globe },
  ]

  useEffect(() => {
    fetchProfile()
  }, [])

  useEffect(() => {
    if (activeTab === 'activity') {
      fetchActivity()
    } else if (activeTab === 'sessions') {
      fetchSessions()
    }
  }, [activeTab])

  const fetchProfile = async () => {
    setLoading(true)
    try {
      const [profileRes, statsRes] = await Promise.all([
        api.get('/profile'),
        api.get('/profile/stats')
      ])

      setProfile(profileRes.data)
      setStats(statsRes.data)

      // Set edit form values
      setEditForm({
        full_name: profileRes.data.full_name || '',
        email: profileRes.data.email || '',
        phone: profileRes.data.phone || '',
        department: profileRes.data.department || '',
        position: profileRes.data.position || '',
        bio: profileRes.data.bio || '',
        language: profileRes.data.language || 'en',
        timezone: profileRes.data.timezone || 'Asia/Dubai'
      })
    } catch (error) {
      console.error('Error fetching profile:', error)
      toast.error('Failed to load profile')
    } finally {
      setLoading(false)
    }
  }

  const fetchActivity = async () => {
    try {
      const response = await api.get('/profile/activity')
      setActivities(response.data.items || [])
    } catch (error) {
      console.error('Error fetching activity:', error)
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await api.get('/profile/sessions')
      setSessions(response.data.sessions || [])
    } catch (error) {
      console.error('Error fetching sessions:', error)
    }
  }

  const handleSaveProfile = async () => {
    setSaving(true)
    try {
      await api.put('/profile', editForm)
      toast.success('Profile updated successfully')
      setEditMode(false)
      fetchProfile()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Passwords do not match')
      return
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return
    }

    setSaving(true)
    try {
      await api.post('/profile/change-password', passwordForm)
      toast.success('Password changed successfully')
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to change password')
    } finally {
      setSaving(false)
    }
  }

  const handleRevokeSession = async (sessionId: string) => {
    if (!confirm('Revoke this session?')) return
    try {
      await api.post(`/profile/sessions/${sessionId}/revoke`)
      toast.success('Session revoked')
      fetchSessions()
    } catch (error) {
      toast.error('Failed to revoke session')
    }
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800'
      case 'manager': return 'bg-blue-100 text-blue-800'
      case 'user': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const renderProfileTab = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start gap-6">
          {/* Avatar */}
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-3xl font-bold">
              {profile?.full_name?.charAt(0) || profile?.username?.charAt(0) || 'U'}
            </div>
            <button className="absolute bottom-0 right-0 p-2 bg-white rounded-full shadow-lg hover:bg-gray-50">
              <Camera size={16} />
            </button>
          </div>

          {/* Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold">{profile?.full_name || profile?.username}</h2>
              <span className={`badge ${getRoleBadgeColor(profile?.role || '')}`}>
                {profile?.role}
              </span>
            </div>
            <p className="text-gray-500 mt-1">@{profile?.username}</p>
            {profile?.bio && <p className="text-gray-600 mt-2">{profile.bio}</p>}

            <div className="flex gap-6 mt-4 text-sm text-gray-600">
              {profile?.email && (
                <div className="flex items-center gap-2">
                  <Mail size={16} />
                  {profile.email}
                </div>
              )}
              {profile?.phone && (
                <div className="flex items-center gap-2">
                  <Phone size={16} />
                  {profile.phone}
                </div>
              )}
            </div>
          </div>

          {/* Edit Button */}
          <button
            onClick={() => setEditMode(!editMode)}
            className="btn-outline flex items-center gap-2"
          >
            <Edit size={18} />
            {editMode ? 'Cancel' : 'Edit Profile'}
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-3xl font-bold text-blue-600">{stats.customers_created}</p>
            <p className="text-sm text-gray-500">Customers Created</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-3xl font-bold text-green-600">{stats.facilities_managed}</p>
            <p className="text-sm text-gray-500">Facilities Managed</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-3xl font-bold text-purple-600">{stats.tasks_completed}</p>
            <p className="text-sm text-gray-500">Tasks Completed</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-3xl font-bold text-orange-600">{stats.documents_uploaded}</p>
            <p className="text-sm text-gray-500">Documents Uploaded</p>
          </div>
        </div>
      )}

      {/* Edit Form */}
      {editMode && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-medium mb-4">Edit Profile</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Full Name</label>
              <input
                type="text"
                value={editForm.full_name}
                onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Phone</label>
              <input
                type="tel"
                value={editForm.phone}
                onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Department</label>
              <input
                type="text"
                value={editForm.department}
                onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Position</label>
              <input
                type="text"
                value={editForm.position}
                onChange={(e) => setEditForm({ ...editForm, position: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Language</label>
              <select
                value={editForm.language}
                onChange={(e) => setEditForm({ ...editForm, language: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="en">English</option>
                <option value="fa">فارسی</option>
                <option value="ar">العربية</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Timezone</label>
              <select
                value={editForm.timezone}
                onChange={(e) => setEditForm({ ...editForm, timezone: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="Asia/Dubai">Asia/Dubai (GMT+4)</option>
                <option value="Asia/Tehran">Asia/Tehran (GMT+3:30)</option>
                <option value="UTC">UTC</option>
                <option value="Europe/London">Europe/London</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-1">Bio</label>
              <textarea
                value={editForm.bio}
                onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg h-24"
                placeholder="Tell us about yourself..."
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <button
              onClick={() => setEditMode(false)}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="btn-primary flex items-center gap-2"
            >
              <Save size={18} />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      {/* Profile Details */}
      {!editMode && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-medium mb-4">Profile Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center gap-3">
              <Building className="text-gray-400" size={20} />
              <div>
                <p className="text-sm text-gray-500">Department</p>
                <p className="font-medium">{profile?.department || 'Not set'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Briefcase className="text-gray-400" size={20} />
              <div>
                <p className="text-sm text-gray-500">Position</p>
                <p className="font-medium">{profile?.position || 'Not set'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Globe className="text-gray-400" size={20} />
              <div>
                <p className="text-sm text-gray-500">Language</p>
                <p className="font-medium">{profile?.language === 'fa' ? 'فارسی' : profile?.language === 'ar' ? 'العربية' : 'English'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="text-gray-400" size={20} />
              <div>
                <p className="text-sm text-gray-500">Timezone</p>
                <p className="font-medium">{profile?.timezone || 'UTC'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderSecurityTab = () => (
    <div className="space-y-6">
      {/* Change Password */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Key size={20} />
          Change Password
        </h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium mb-1">Current Password</label>
            <div className="relative">
              <input
                type={showPasswords.current ? 'text' : 'password'}
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                {showPasswords.current ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">New Password</label>
            <div className="relative">
              <input
                type={showPasswords.new ? 'text' : 'password'}
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                {showPasswords.new ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Confirm New Password</label>
            <div className="relative">
              <input
                type={showPasswords.confirm ? 'text' : 'password'}
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
              >
                {showPasswords.confirm ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <button
            onClick={handleChangePassword}
            disabled={saving}
            className="btn-primary"
          >
            {saving ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </div>

      {/* Two Factor Auth */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Shield size={20} />
          Two-Factor Authentication
        </h3>
        <p className="text-gray-600 mb-4">
          Add an extra layer of security to your account by enabling two-factor authentication.
        </p>
        <button className="btn-outline">
          Enable 2FA
        </button>
      </div>
    </div>
  )

  const renderActivityTab = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="font-medium mb-4">Recent Activity</h3>
      {activities.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No recent activity</p>
      ) : (
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-4 p-3 border rounded-lg">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <Activity className="text-blue-600" size={18} />
              </div>
              <div className="flex-1">
                <p className="font-medium">{activity.description}</p>
                <p className="text-sm text-gray-500">
                  {new Date(activity.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderSessionsTab = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="font-medium mb-4">Active Sessions</h3>
      {sessions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No active sessions</p>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <div key={session.id} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <Globe size={20} />
                </div>
                <div>
                  <p className="font-medium flex items-center gap-2">
                    {session.device}
                    {session.is_current && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
                        Current
                      </span>
                    )}
                  </p>
                  <p className="text-sm text-gray-500">
                    {session.ip_address} - {session.location}
                  </p>
                  <p className="text-xs text-gray-400">
                    Last active: {new Date(session.last_active).toLocaleString()}
                  </p>
                </div>
              </div>
              {!session.is_current && (
                <button
                  onClick={() => handleRevokeSession(session.id)}
                  className="text-red-500 hover:bg-red-50 p-2 rounded"
                >
                  <LogOut size={18} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile': return renderProfileTab()
      case 'security': return renderSecurityTab()
      case 'activity': return renderActivityTab()
      case 'sessions': return renderSessionsTab()
      default: return null
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <p className="text-gray-600">Manage your account settings and preferences</p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b">
            <nav className="flex gap-4 px-6">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 py-4 px-2 border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    <Icon size={18} />
                    {tab.label}
                  </button>
                )
              })}
            </nav>
          </div>
        </div>

        {/* Content */}
        {renderTabContent()}
      </div>
    </Layout>
  )
}
