/**
 * Checklist Detail Page
 * صفحه جزئیات چک‌لیست
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { checklistsApi, customersApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckSquare,
  User,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  Plus,
  Square,
  FileText,
  MoreVertical,
} from 'lucide-react'

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
  updated_at?: string
}

interface Customer {
  id: string
  customer_name: string
  full_name?: string
  account_no: string
}

export default function ChecklistDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const [checklist, setChecklist] = useState<Checklist | null>(null)
  const [customer, setCustomer] = useState<Customer | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddItem, setShowAddItem] = useState(false)
  const [newItemTitle, setNewItemTitle] = useState('')
  const [newItemDueDate, setNewItemDueDate] = useState('')

  const fetchChecklist = async () => {
    if (!id) return

    setLoading(true)
    try {
      const [checklistRes, customersRes] = await Promise.all([
        checklistsApi.get(id as string),
        customersApi.list()
      ])

      const customersData = customersRes.data.items || customersRes.data || []
      const checklistData = checklistRes.data
      const customerData = customersData.find((c: any) => c.id === checklistData.customer_id)

      setChecklist({
        ...checklistData,
        customer_name: customerData?.customer_name || customerData?.full_name || 'Unknown',
        items: checklistData.items || []
      })
      setCustomer(customerData || null)
    } catch (error: any) {
      console.error('Error fetching checklist:', error)
      if (error.response?.status === 404) {
        toast.error('Checklist not found')
        router.push('/checklists')
      } else {
        toast.error('Failed to load checklist details')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchChecklist()
    }
  }, [id])

  const updateItemStatus = async (itemId: string, newStatus: string) => {
    try {
      await checklistsApi.updateItem(id as string, itemId, { status: newStatus })
      toast.success('Item updated')
      fetchChecklist()
    } catch (error) {
      toast.error('Failed to update item')
    }
  }

  const toggleItemStatus = (item: ChecklistItem) => {
    const newStatus = item.status === 'completed' ? 'pending' : 'completed'
    updateItemStatus(item.id, newStatus)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={20} />
      case 'overdue':
        return <AlertCircle className="text-red-500" size={20} />
      case 'in_progress':
        return <Clock className="text-blue-500" size={20} />
      default:
        return <Square className="text-gray-400" size={20} />
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

  // Calculate progress
  const completedCount = checklist?.items.filter(i => i.status === 'completed').length || 0
  const totalCount = checklist?.items.length || 0
  const progress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0

  // Group items by status
  const pendingItems = checklist?.items.filter(i => i.status === 'pending' || i.status === 'in_progress') || []
  const overdueItems = checklist?.items.filter(i => i.status === 'overdue') || []
  const completedItems = checklist?.items.filter(i => i.status === 'completed') || []

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading checklist...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!checklist) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto text-red-400" size={48} />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Checklist Not Found</h2>
          <p className="mt-2 text-gray-500">The checklist you're looking for doesn't exist.</p>
          <Link href="/checklists" className="mt-4 inline-block btn-primary">
            Back to Checklists
          </Link>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {checklist.title}
                </h1>
                <span className={`badge ${getStatusColor(checklist.status)}`}>
                  {checklist.status}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {checklist.type}
              </p>
              {customer && (
                <Link
                  href={`/customers/${customer.id}`}
                  className="text-sm text-blue-600 hover:underline mt-1 inline-flex items-center gap-1"
                >
                  <User size={14} />
                  {checklist.customer_name}
                </Link>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="btn-secondary flex items-center gap-2">
              <Edit size={16} />
              Edit
            </button>
            <button className="btn-danger flex items-center gap-2">
              <Trash2 size={16} />
              Delete
            </button>
          </div>
        </div>

        {/* Progress Card */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-semibold">Progress</h3>
              <p className="text-sm text-gray-500">{completedCount} of {totalCount} items completed</p>
            </div>
            <div className="text-3xl font-bold text-blue-600">{progress}%</div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all ${
                progress === 100 ? 'bg-green-500' :
                progress >= 50 ? 'bg-blue-500' :
                'bg-orange-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <CheckSquare className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Items</p>
              <p className="text-2xl font-bold">{totalCount}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Clock className="text-yellow-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending</p>
              <p className="text-2xl font-bold">{pendingItems.length}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertCircle className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Overdue</p>
              <p className="text-2xl font-bold">{overdueItems.length}</p>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold">{completedCount}</p>
            </div>
          </div>
        </div>

        {/* Items List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="text-lg font-semibold">Checklist Items</h3>
            <button
              onClick={() => setShowAddItem(true)}
              className="btn-primary text-sm flex items-center gap-2"
            >
              <Plus size={16} />
              Add Item
            </button>
          </div>

          {checklist.items.length === 0 ? (
            <div className="p-8 text-center">
              <CheckSquare className="mx-auto text-gray-300" size={48} />
              <p className="mt-2 text-gray-500">No items in this checklist</p>
              <button
                onClick={() => setShowAddItem(true)}
                className="mt-4 btn-primary text-sm"
              >
                Add First Item
              </button>
            </div>
          ) : (
            <div className="divide-y">
              {/* Overdue Items */}
              {overdueItems.length > 0 && (
                <div className="p-4 bg-red-50">
                  <h4 className="text-sm font-medium text-red-700 mb-3 flex items-center gap-2">
                    <AlertCircle size={16} />
                    Overdue ({overdueItems.length})
                  </h4>
                  <div className="space-y-2">
                    {overdueItems.map((item) => (
                      <ItemRow
                        key={item.id}
                        item={item}
                        onToggle={() => toggleItemStatus(item)}
                        getStatusIcon={getStatusIcon}
                        getStatusColor={getStatusColor}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Pending Items */}
              {pendingItems.length > 0 && (
                <div className="p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <Clock size={16} />
                    Pending ({pendingItems.length})
                  </h4>
                  <div className="space-y-2">
                    {pendingItems.map((item) => (
                      <ItemRow
                        key={item.id}
                        item={item}
                        onToggle={() => toggleItemStatus(item)}
                        getStatusIcon={getStatusIcon}
                        getStatusColor={getStatusColor}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Completed Items */}
              {completedItems.length > 0 && (
                <div className="p-4 bg-gray-50">
                  <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <CheckCircle size={16} />
                    Completed ({completedItems.length})
                  </h4>
                  <div className="space-y-2">
                    {completedItems.map((item) => (
                      <ItemRow
                        key={item.id}
                        item={item}
                        onToggle={() => toggleItemStatus(item)}
                        getStatusIcon={getStatusIcon}
                        getStatusColor={getStatusColor}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Customer Info */}
        {customer && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <User size={20} />
              Customer
            </h3>
            <Link
              href={`/customers/${customer.id}`}
              className="block p-4 border rounded-lg hover:bg-gray-50"
            >
              <p className="font-medium">{customer.customer_name || customer.full_name}</p>
              <p className="text-sm text-gray-500">{customer.account_no}</p>
            </Link>
          </div>
        )}

        {/* Timeline */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Calendar size={20} />
            Timeline
          </h3>
          <dl className="space-y-3">
            <div className="flex justify-between text-sm">
              <dt className="text-gray-600">Created</dt>
              <dd>{new Date(checklist.created_at).toLocaleDateString()}</dd>
            </div>
            {checklist.updated_at && (
              <div className="flex justify-between text-sm">
                <dt className="text-gray-600">Last Updated</dt>
                <dd>{new Date(checklist.updated_at).toLocaleDateString()}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Add Item Modal */}
        {showAddItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
              <div className="p-4 border-b">
                <h2 className="text-lg font-semibold">Add Checklist Item</h2>
              </div>
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  toast.success('Item adding coming soon')
                  setShowAddItem(false)
                }}
                className="p-4 space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium mb-1">Item Title *</label>
                  <input
                    type="text"
                    value={newItemTitle}
                    onChange={(e) => setNewItemTitle(e.target.value)}
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="Enter item title"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Due Date</label>
                  <input
                    type="date"
                    value={newItemDueDate}
                    onChange={(e) => setNewItemDueDate(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddItem(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    Add Item
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}

// Item Row Component
function ItemRow({
  item,
  onToggle,
  getStatusIcon,
  getStatusColor,
}: {
  item: ChecklistItem
  onToggle: () => void
  getStatusIcon: (status: string) => JSX.Element
  getStatusColor: (status: string) => string
}) {
  return (
    <div
      className={`flex items-center justify-between p-3 rounded-lg border ${
        item.status === 'completed' ? 'bg-gray-50 opacity-60' : 'bg-white'
      }`}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onToggle}
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
          {item.assigned_to && (
            <p className="text-xs text-gray-500">
              Assigned to: {item.assigned_to}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={`badge text-xs ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
        <button className="p-1 hover:bg-gray-100 rounded">
          <MoreVertical size={16} className="text-gray-400" />
        </button>
      </div>
    </div>
  )
}
