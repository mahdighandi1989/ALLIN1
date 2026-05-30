'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { settingsApi, parseApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { SettingsResponse } from '@/types'
import { Settings as SettingsIcon, Save, Lock } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const router = useRouter()
  const { user, authDisabled, loading: authLoading } = useAuth()
  const [data, setData] = useState<SettingsResponse | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const isAdmin = authDisabled || !!user?.is_admin

  useEffect(() => {
    if (authLoading) return
    if (!authDisabled && user && !user.is_admin) router.replace('/dashboard')
  }, [authLoading, authDisabled, user, router])

  const load = async () => {
    try {
      setLoading(true)
      const res = await settingsApi.get()
      setData(res)
      const initial: Record<string, string> = {}
      res.editable.forEach((e) => { initial[e.key] = e.value })
      setForm(initial)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await settingsApi.update(form)
      toast.success('Settings saved')
      load()
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <Layout><div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div></Layout>
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <SettingsIcon size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">System Settings</h2>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* Editable settings */}
        <form onSubmit={save} className="bg-white rounded-lg shadow-sm p-6 space-y-4" data-testid="settings-form">
          <h3 className="font-medium">Application settings</h3>
          {data?.editable.map((s) => (
            <div key={s.key}>
              <label className="block text-sm font-medium mb-1">{s.label}</label>
              <input
                type={s.type === 'number' ? 'number' : 'text'}
                value={form[s.key] ?? ''}
                onChange={(e) => setForm({ ...form, [s.key]: e.target.value })}
                disabled={!isAdmin}
                className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
              />
            </div>
          ))}
          {isAdmin ? (
            <button type="submit" disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              <Save size={16} /> {saving ? 'Saving…' : 'Save settings'}
            </button>
          ) : (
            <p className="text-sm text-gray-500 flex items-center gap-1"><Lock size={14} /> Read-only (admin required to edit)</p>
          )}
        </form>

        {/* Read-only runtime config */}
        <div className="bg-white rounded-lg shadow-sm p-6" data-testid="settings-runtime">
          <h3 className="font-medium mb-3">Runtime configuration <span className="text-xs text-gray-400">(read-only · from environment)</span></h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {data && Object.entries(data.runtime).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">{k.replace(/_/g, ' ')}</span>
                <span className="font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
