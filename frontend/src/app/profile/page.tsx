'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { authApi, parseApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { User } from '@/types'
import { UserCircle, Save, KeyRound } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { authDisabled } = useAuth()
  const [me, setMe] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // profile form
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)

  // password form
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [savingPw, setSavingPw] = useState(false)

  useEffect(() => {
    authApi
      .me()
      .then((u) => {
        setMe(u)
        setFullName(u.full_name || '')
        setEmail(u.email || '')
      })
      .catch((e) => toast.error(parseApiError(e)))
      .finally(() => setLoading(false))
  }, [])

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingProfile(true)
    try {
      const updated = await authApi.updateProfile({ full_name: fullName, email })
      setMe(updated)
      toast.success('Profile updated')
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSavingProfile(false)
    }
  }

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (newPw !== confirmPw) {
      toast.error('New passwords do not match')
      return
    }
    setSavingPw(true)
    try {
      await authApi.changePassword(currentPw, newPw)
      toast.success('Password changed')
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSavingPw(false)
    }
  }

  if (loading) {
    return <Layout><div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div></Layout>
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <UserCircle size={24} className="text-gray-500" />
        <h2 className="text-2xl font-bold">My Profile</h2>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* Account summary */}
        <div className="bg-white rounded-lg shadow-sm p-6 flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xl font-bold">
            {(me?.full_name || me?.username || '?').charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-lg font-semibold">{me?.full_name || me?.username}</p>
            <p className="text-sm text-gray-500">
              @{me?.username}
              {me?.is_admin && <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">admin</span>}
            </p>
          </div>
        </div>

        {/* Profile form */}
        <form onSubmit={saveProfile} className="bg-white rounded-lg shadow-sm p-6 space-y-4" data-testid="profile-form">
          <h3 className="font-medium">Profile details</h3>
          <div>
            <label className="block text-sm font-medium mb-1">Full Name</label>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <button type="submit" disabled={savingProfile}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            <Save size={16} /> {savingProfile ? 'Saving…' : 'Save Profile'}
          </button>
        </form>

        {/* Password form */}
        <form onSubmit={changePassword} className="bg-white rounded-lg shadow-sm p-6 space-y-4" data-testid="password-form">
          <h3 className="font-medium flex items-center gap-2"><KeyRound size={16} /> Change password</h3>
          {authDisabled && (
            <p className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
              Login is currently disabled, so password change is unavailable.
            </p>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Current Password</label>
            <input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg" disabled={authDisabled} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">New Password</label>
              <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg" minLength={8} disabled={authDisabled} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Confirm New Password</label>
              <input type="password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg" minLength={8} disabled={authDisabled} />
            </div>
          </div>
          <button type="submit" disabled={savingPw || authDisabled}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            <KeyRound size={16} /> {savingPw ? 'Updating…' : 'Change Password'}
          </button>
        </form>
      </div>
    </Layout>
  )
}
