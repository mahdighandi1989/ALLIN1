'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { auditApi, parseApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { AuditList } from '@/types'
import { ScrollText } from 'lucide-react'
import toast from 'react-hot-toast'

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  login: 'bg-purple-100 text-purple-700',
}

export default function AuditPage() {
  const router = useRouter()
  const { user, authDisabled, loading: authLoading } = useAuth()
  const [data, setData] = useState<AuditList | null>(null)
  const [loading, setLoading] = useState(true)
  const [action, setAction] = useState('')
  const [entityType, setEntityType] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (authLoading) return
    if (!authDisabled && user && !user.is_admin) router.replace('/dashboard')
  }, [authLoading, authDisabled, user, router])

  const load = async () => {
    try {
      setLoading(true)
      setData(await auditApi.list({
        page: 1, page_size: 100,
        action: action || undefined,
        entity_type: entityType || undefined,
        search: search || undefined,
      }))
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

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <ScrollText size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">Audit Log</h2>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); load() }} className="mb-6 flex flex-wrap gap-2">
        <select value={action} onChange={(e) => setAction(e.target.value)} className="px-3 py-2 border rounded-lg">
          <option value="">All actions</option>
          {['create', 'update', 'delete', 'login'].map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={entityType} onChange={(e) => setEntityType(e.target.value)} className="px-3 py-2 border rounded-lg">
          <option value="">All entities</option>
          {['customer', 'facility', 'offer_letter', 'user', 'auth'].map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search user / detail…"
          className="flex-1 min-w-[200px] px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button type="submit" className="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200">Filter</button>
      </form>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="audit-content">
        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
        ) : data && data.items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr className="text-left text-gray-500">
                  <th className="px-4 py-3">When</th>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Entity</th>
                  <th className="px-4 py-3">Detail</th>
                  <th className="px-4 py-3">IP</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((e) => (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 whitespace-nowrap text-gray-500">
                      {e.created_at ? new Date(e.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="px-4 py-2 font-medium">{e.username || '-'}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${ACTION_COLORS[e.action] || 'bg-gray-100 text-gray-600'}`}>
                        {e.action}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {e.entity_type}{e.entity_id ? <span className="text-gray-400"> · {e.entity_id.slice(0, 10)}</span> : ''}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{e.detail || '-'}</td>
                    <td className="px-4 py-2 text-gray-400">{e.ip_address || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-gray-500">No audit entries</div>
        )}
      </div>
    </Layout>
  )
}
