/**
 * Checklists Page
 * صفحه مدیریت چک‌لیست‌ها
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { checklistsApi, customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { CheckSquare, Clock, AlertCircle, CheckCircle, Plus, ChevronDown, ChevronRight } from 'lucide-react'

interface ChecklistItem {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  due_date?: string
  assigned_to?: string
  notes?: string
}

interface Checklist {
  id: string
  title: string
  customer_id: string
  customer_name?: string
  type: string
  status: string
  items: ChecklistItem[]
  created_at: string
}

export default function ChecklistsPage() {
  const [checklists, setChecklists] = useState<Checklist[]>([])
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all')
  const [stats, setStats] = useState({ total: 0, pending: 0, completed: 0, overdue: 0 })

  const fetchData = async () => {
    setLoading(true)
    try {
      const [checklistsRes, customersRes] = await Promise.all([
        checklistsApi.list({ page_size: 100 }),
        customersApi.list({ page_size: 100 })
      ])

      const checklistsData = checklistsRes.data.items || checklistsRes.data || []
      const customersData = customersRes.data.items || customersRes.data || []

      // Add customer names
      const checklistsWithNames = checklistsData.map((c: any) => ({
        ...c,
        customer_name: customersData.find((cust: any) => cust.id === c.customer_id)?.full_name || 'Unknown',
        items: c.items || []
      }))

      setChecklists(checklistsWithNames)
      setCustomers(customersData)

      // Calculate stats
      let totalItems = 0
      let pendingItems = 0
      let completedItems = 0
      let overdueItems = 0

      checklistsWithNames.forEach((c: Checklist) => {
        c.items.forEach((item) => {
          totalItems++
          if (item.status === 'completed') completedItems++
          else if (item.status === 'overdue') overdueItems++
          else pendingItems++
        })
      })

      setStats({ total: totalItems, pending: pendingItems, completed: completedItems, overdue: overdueItems })
    } catch (error) {
      console.error('Error fetching data:', error)
      toast.error('Failed to load checklists')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(id)) newSet.delete(id)
      else newSet.add(id)
      return newSet
    })
  }

  const updateItemStatus = async (checklistId: string, itemId: string, newStatus: string) => {
    try {
      await checklistsApi.updateItem(checklistId, itemId, { status: newStatus })
      toast.success('Item updated')
      fetchData()
    } catch (error) {
      toast.error('Failed to update item')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={18} />
      case 'overdue':
        return <AlertCircle className="text-red-500" size={18} />
      case 'in_progress':
        return <Clock className="text-blue-500" size={18} />
      default:
        return <Clock className="text-gray-400" size={18} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'overdue': return 'bg-red-100 text-red-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const filteredChecklists = checklists.filter((c) => {
    if (filter === 'all') return true
    if (filter === 'pending') return c.items.some((i) => i.status !== 'completed')
    if (filter === 'completed') return c.items.every((i) => i.status === 'completed')
    return true
  })

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Checklists</h1>
            <p className="text-gray-600">Track documents and requirements</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Plus size={18} />
            New Checklist
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <CheckSquare className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Items</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Clock className="text-yellow-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-2xl font-bold">{stats.pending}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold">{stats.completed}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Overdue</p>
              <p className="text-2xl font-bold">{stats.overdue}</p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          {(['all', 'pending', 'completed'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg capitalize ${
                filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Checklists */}
        <div className="space-y-4">
          {loading ? (
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-500">Loading checklists...</p>
            </div>
          ) : filteredChecklists.length === 0 ? (
            <div className="bg-white rounded-lg p-8 text-center">
              <CheckSquare className="mx-auto text-gray-300" size={48} />
              <p className="mt-2 text-gray-500">No checklists found</p>
            </div>
          ) : (
            filteredChecklists.map((checklist) => {
              const isExpanded = expandedIds.has(checklist.id)
              const completedCount = checklist.items.filter((i) => i.status === 'completed').length
              const progress = checklist.items.length > 0
                ? Math.round((completedCount / checklist.items.length) * 100)
                : 0

              return (
                <div key={checklist.id} className="bg-white rounded-lg shadow overflow-hidden">
                  {/* Checklist Header */}
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50 flex items-center justify-between"
                    onClick={() => toggleExpand(checklist.id)}
                  >
                    <div className="flex items-center gap-4">
                      {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                      <div>
                        <h3 className="font-medium">{checklist.title}</h3>
                        <p className="text-sm text-gray-500">{checklist.customer_name} - {checklist.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm text-gray-600">{completedCount}/{checklist.items.length} items</p>
                        <div className="w-32 bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-green-500 h-2 rounded-full transition-all"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </div>
                      <span className={`badge ${getStatusColor(checklist.status)}`}>
                        {checklist.status}
                      </span>
                    </div>
                  </div>

                  {/* Checklist Items */}
                  {isExpanded && (
                    <div className="border-t">
                      {checklist.items.length === 0 ? (
                        <p className="p-4 text-gray-500 text-center">No items in this checklist</p>
                      ) : (
                        checklist.items.map((item) => (
                          <div
                            key={item.id}
                            className="p-4 border-b last:border-b-0 flex items-center justify-between hover:bg-gray-50"
                          >
                            <div className="flex items-center gap-3">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  const newStatus = item.status === 'completed' ? 'pending' : 'completed'
                                  updateItemStatus(checklist.id, item.id, newStatus)
                                }}
                                className="hover:scale-110 transition-transform"
                              >
                                {getStatusIcon(item.status)}
                              </button>
                              <div>
                                <p className={item.status === 'completed' ? 'line-through text-gray-400' : ''}>
                                  {item.title}
                                </p>
                                {item.due_date && (
                                  <p className="text-xs text-gray-500">
                                    Due: {new Date(item.due_date).toLocaleDateString()}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`badge text-xs ${getStatusColor(item.status)}`}>
                                {item.status}
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
    </Layout>
  )
}
