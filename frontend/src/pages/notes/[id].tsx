/**
 * Note Detail Page
 * صفحه جزئیات یادداشت
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import Layout from '@/components/Layout'
import { personalApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Edit,
  Trash2,
  StickyNote,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  Star,
  Tag,
  Bell,
  Save,
  X,
} from 'lucide-react'

interface Note {
  id: string
  title: string
  content: string
  category: string
  priority: 'low' | 'medium' | 'high'
  is_done: boolean
  reminder_date?: string
  created_at: string
  updated_at?: string
}

export default function NoteDetailPage() {
  const router = useRouter()
  const { id } = router.query

  const [note, setNote] = useState<Note | null>(null)
  const [loading, setLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    title: '',
    content: '',
    category: 'general',
    priority: 'medium',
    reminder_date: '',
  })

  const categories = ['general', 'work', 'personal', 'urgent', 'follow-up', 'reminder']

  const fetchNote = async () => {
    if (!id) return

    setLoading(true)
    try {
      const response = await personalApi.getNotes()
      const notes = response.data.items || response.data || []
      const foundNote = notes.find((n: Note) => n.id === id)

      if (foundNote) {
        setNote(foundNote)
        setEditData({
          title: foundNote.title,
          content: foundNote.content,
          category: foundNote.category,
          priority: foundNote.priority,
          reminder_date: foundNote.reminder_date || '',
        })
      } else {
        toast.error('Note not found')
        router.push('/notes')
      }
    } catch (error: any) {
      console.error('Error fetching note:', error)
      toast.error('Failed to load note')
      router.push('/notes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchNote()
    }
  }, [id])

  const handleUpdate = async () => {
    try {
      await personalApi.updateNote(id as string, editData)
      toast.success('Note updated successfully')
      setIsEditing(false)
      fetchNote()
    } catch (error) {
      toast.error('Failed to update note')
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this note? This action cannot be undone.')) {
      return
    }

    try {
      await personalApi.deleteNote(id as string)
      toast.success('Note deleted successfully')
      router.push('/notes')
    } catch (error) {
      toast.error('Failed to delete note')
    }
  }

  const toggleDone = async () => {
    try {
      await personalApi.toggleNoteDone(id as string)
      toast.success(note?.is_done ? 'Marked as pending' : 'Marked as done')
      fetchNote()
    } catch (error) {
      toast.error('Failed to update note')
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low': return 'bg-green-100 text-green-800 border-green-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getPriorityBorderColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-l-red-500'
      case 'medium': return 'border-l-yellow-500'
      case 'low': return 'border-l-green-500'
      default: return 'border-l-gray-500'
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading note...</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!note) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="mx-auto text-red-400" size={48} />
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Note Not Found</h2>
          <p className="mt-2 text-gray-500">The note you're looking for doesn't exist.</p>
          <Link href="/notes" className="mt-4 inline-block btn-primary">
            Back to Notes
          </Link>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6 max-w-4xl mx-auto">
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
              {isEditing ? (
                <input
                  type="text"
                  value={editData.title}
                  onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                  className="text-2xl font-bold border-b-2 border-blue-500 focus:outline-none bg-transparent"
                />
              ) : (
                <h1 className={`text-2xl font-bold text-gray-900 ${note.is_done ? 'line-through opacity-60' : ''}`}>
                  {note.title}
                </h1>
              )}
              <div className="flex items-center gap-2 mt-2">
                <span className={`badge text-xs ${getPriorityColor(note.priority)}`}>
                  {note.priority} priority
                </span>
                <span className="badge bg-gray-100 text-gray-700 text-xs">
                  {note.category}
                </span>
                {note.is_done && (
                  <span className="badge bg-green-100 text-green-700 text-xs flex items-center gap-1">
                    <CheckCircle size={12} />
                    Done
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isEditing ? (
              <>
                <button
                  onClick={() => setIsEditing(false)}
                  className="btn-secondary flex items-center gap-2"
                >
                  <X size={16} />
                  Cancel
                </button>
                <button
                  onClick={handleUpdate}
                  className="btn-primary flex items-center gap-2"
                >
                  <Save size={16} />
                  Save
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={toggleDone}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
                    note.is_done
                      ? 'bg-yellow-50 border-yellow-300 text-yellow-700 hover:bg-yellow-100'
                      : 'bg-green-50 border-green-300 text-green-700 hover:bg-green-100'
                  }`}
                >
                  <CheckCircle size={16} />
                  {note.is_done ? 'Mark Pending' : 'Mark Done'}
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary flex items-center gap-2"
                >
                  <Edit size={16} />
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  className="btn-danger flex items-center gap-2"
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              </>
            )}
          </div>
        </div>

        {/* Note Card */}
        <div className={`bg-white rounded-lg shadow-lg border-l-4 ${getPriorityBorderColor(note.priority)} ${
          note.is_done ? 'opacity-60' : ''
        }`}>
          {/* Content */}
          <div className="p-6">
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Content</label>
                  <textarea
                    value={editData.content}
                    onChange={(e) => setEditData({ ...editData, content: e.target.value })}
                    rows={10}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Note content..."
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Category</label>
                    <select
                      value={editData.category}
                      onChange={(e) => setEditData({ ...editData, category: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      {categories.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Priority</label>
                    <select
                      value={editData.priority}
                      onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Reminder</label>
                    <input
                      type="datetime-local"
                      value={editData.reminder_date}
                      onChange={(e) => setEditData({ ...editData, reminder_date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="prose max-w-none">
                <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {note.content || 'No content'}
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t rounded-b-lg">
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Tag size={14} />
                <span className="capitalize">{note.category}</span>
              </div>
              <div className="flex items-center gap-1">
                <Star size={14} />
                <span className="capitalize">{note.priority}</span>
              </div>
              {note.reminder_date && (
                <div className="flex items-center gap-1 text-blue-600">
                  <Bell size={14} />
                  <span>{new Date(note.reminder_date).toLocaleString()}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <Calendar size={14} />
                <span>Created: {new Date(note.created_at).toLocaleDateString()}</span>
              </div>
              {note.updated_at && (
                <div className="flex items-center gap-1">
                  <Clock size={14} />
                  <span>Updated: {new Date(note.updated_at).toLocaleDateString()}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Related Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/notes"
            className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow flex items-center gap-3"
          >
            <div className="p-2 bg-blue-100 rounded-lg">
              <StickyNote className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="font-medium">All Notes</p>
              <p className="text-sm text-gray-500">View all notes</p>
            </div>
          </Link>

          <button
            onClick={() => {
              router.push('/notes')
              setTimeout(() => {
                // Trigger new note creation
              }, 100)
            }}
            className="bg-white p-4 rounded-lg shadow hover:shadow-md transition-shadow flex items-center gap-3 text-left"
          >
            <div className="p-2 bg-green-100 rounded-lg">
              <Edit className="text-green-600" size={20} />
            </div>
            <div>
              <p className="font-medium">New Note</p>
              <p className="text-sm text-gray-500">Create a new note</p>
            </div>
          </button>

          <div className="bg-white p-4 rounded-lg shadow flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              note.is_done ? 'bg-green-100' : 'bg-yellow-100'
            }`}>
              {note.is_done ? (
                <CheckCircle className="text-green-600" size={20} />
              ) : (
                <Clock className="text-yellow-600" size={20} />
              )}
            </div>
            <div>
              <p className="font-medium">Status</p>
              <p className="text-sm text-gray-500">
                {note.is_done ? 'Completed' : 'Pending'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
