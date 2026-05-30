'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { usersApi, parseApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { AdminUser, AdminUserList, AdminUserForm } from '@/types'
import { Plus, Shield, ShieldOff, UserX, Pencil } from 'lucide-react'
import toast from 'react-hot-toast'

export default function UsersPage() {
  const router = useRouter()
  const { user, authDisabled, loading: authLoading } = useAuth()
  const [data, setData] = useState<AdminUserList | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<AdminUser | null>(null)

  // Guard: only admins (or the demo admin when auth is disabled) may view this.
  useEffect(() => {
    if (authLoading) return
    if (!authDisabled && user && !user.is_admin) {
      router.replace('/dashboard')
    }
  }, [authLoading, authDisabled, user, router])

  const load = async () => {
    try {
      setLoading(true)
      setData(await usersApi.list({ page: 1, page_size: 100, search: search || undefined }))
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

  const deactivate = async (u: AdminUser) => {
    if (!confirm(`Deactivate ${u.username}?`)) return
    try {
      await usersApi.deactivate(u.id)
      toast.success('User deactivated')
      load()
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  const toggleAdmin = async (u: AdminUser) => {
    try {
      await usersApi.update(u.id, { is_admin: !u.is_admin })
      toast.success(u.is_admin ? 'Admin revoked' : 'Promoted to admin')
      load()
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Users</h2>
        <button
          type="button"
          data-testid="add-user-btn"
          onClick={() => { setEditing(null); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} /> New User
        </button>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); load() }}
        className="mb-6 flex gap-2"
      >
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Search username / email / name…"
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button type="submit" className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">Search</button>
      </form>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="users-content">
        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
        ) : data && data.items.length > 0 ? (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Username</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Email</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Role</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.items.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{u.username}</td>
                  <td className="px-4 py-3 text-sm">{u.full_name || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${u.is_admin ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                      {u.is_admin ? 'admin' : 'user'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {u.is_active ? 'active' : 'inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => { setEditing(u); setShowForm(true) }} aria-label="Edit user"
                      className="text-gray-500 hover:text-blue-600 mr-2"><Pencil size={16} /></button>
                    <button onClick={() => toggleAdmin(u)} aria-label="Toggle admin"
                      className="text-gray-500 hover:text-purple-600 mr-2">
                      {u.is_admin ? <ShieldOff size={16} /> : <Shield size={16} />}
                    </button>
                    <button onClick={() => deactivate(u)} aria-label="Deactivate user"
                      className="text-gray-500 hover:text-red-600"><UserX size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-12 text-center text-gray-500">No users found</div>
        )}
      </div>

      {showForm && (
        <UserFormModal
          existing={editing}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load() }}
        />
      )}
    </Layout>
  )
}

function UserFormModal({ existing, onClose, onSaved }: {
  existing: AdminUser | null; onClose: () => void; onSaved: () => void
}) {
  const isEdit = !!existing
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<AdminUserForm>({
    username: existing?.username || '',
    email: existing?.email || '',
    password: '',
    full_name: existing?.full_name || '',
    is_admin: existing?.is_admin || false,
    is_active: existing?.is_active ?? true,
  })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (isEdit && existing) {
        const payload: any = {
          email: form.email,
          full_name: form.full_name,
          is_admin: form.is_admin,
          is_active: form.is_active,
        }
        if (form.password) payload.password = form.password
        await usersApi.update(existing.id, payload)
        toast.success('User updated')
      } else {
        await usersApi.create(form)
        toast.success('User created')
      }
      onSaved()
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b"><h3 className="text-lg font-semibold">{isEdit ? 'Edit User' : 'New User'}</h3></div>
        <form onSubmit={submit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Username *</label>
            <input value={form.username} disabled={isEdit}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Full Name *</label>
            <input value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email *</label>
            <input type="email" value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg" required />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              {isEdit ? 'New Password (leave blank to keep)' : 'Password *'}
            </label>
            <input type="password" value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg" required={!isEdit} minLength={8} />
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_admin}
                onChange={(e) => setForm({ ...form, is_admin: e.target.checked })} />
              Admin
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Active
            </label>
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
