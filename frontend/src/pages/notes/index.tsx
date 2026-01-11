/**
 * Personal Notes Page
 * صفحه یادداشت‌های شخصی
 */
import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { personalApi } from '@/services/api'
import { toast } from 'react-hot-toast'
import { StickyNote, Plus, Trash2, Edit, CheckCircle, Clock, Star, Search } from 'lucide-react'

interface Note {
  id: string
  title: string
  content: string
  category: string
  priority: 'low' | 'medium' | 'high'
  is_done: boolean
  reminder_date?: string
  created_at: string
  updated_at: string
}

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'active' | 'done'>('all')

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'general',
    priority: 'medium',
    reminder_date: '',
  })

  const fetchNotes = async () => {
    setLoading(true)
    try {
      const response = await personalApi.getNotes({ page_size: 100 })
      setNotes(response.data.items || response.data || [])
    } catch (error) {
      console.error('Error fetching notes:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNotes()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingNote) {
        await personalApi.updateNote(editingNote.id, formData)
        toast.success('Note updated')
      } else {
        await personalApi.createNote(formData)
        toast.success('Note created')
      }
      setShowForm(false)
      setEditingNote(null)
      setFormData({ title: '', content: '', category: 'general', priority: 'medium', reminder_date: '' })
      fetchNotes()
    } catch (error) {
      toast.error('Failed to save note')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this note?')) return
    try {
      await personalApi.deleteNote(id)
      toast.success('Note deleted')
      fetchNotes()
    } catch (error) {
      toast.error('Failed to delete')
    }
  }

  const toggleDone = async (note: Note) => {
    try {
      await personalApi.toggleNoteDone(note.id)
      fetchNotes()
    } catch (error) {
      toast.error('Failed to update')
    }
  }

  const openEdit = (note: Note) => {
    setEditingNote(note)
    setFormData({
      title: note.title,
      content: note.content,
      category: note.category,
      priority: note.priority,
      reminder_date: note.reminder_date || '',
    })
    setShowForm(true)
  }

  const filteredNotes = notes.filter((note) => {
    const matchesSearch = note.title.toLowerCase().includes(search.toLowerCase()) ||
      note.content.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'all' ||
      (filter === 'done' && note.is_done) ||
      (filter === 'active' && !note.is_done)
    return matchesSearch && matchesFilter
  })

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-l-red-500 bg-red-50'
      case 'medium': return 'border-l-yellow-500 bg-yellow-50'
      case 'low': return 'border-l-green-500 bg-green-50'
      default: return 'border-l-gray-500'
    }
  }

  const categories = ['general', 'work', 'personal', 'urgent', 'follow-up', 'reminder']

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Notes</h1>
            <p className="text-gray-600">Personal notes and reminders</p>
          </div>
          <button
            onClick={() => {
              setEditingNote(null)
              setFormData({ title: '', content: '', category: 'general', priority: 'medium', reminder_date: '' })
              setShowForm(true)
            }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={18} />
            New Note
          </button>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search notes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
          </div>
          <div className="flex gap-2">
            {(['all', 'active', 'done'] as const).map((f) => (
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
        </div>

        {/* Notes Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg">
            <StickyNote className="mx-auto text-gray-300" size={48} />
            <p className="mt-2 text-gray-500">No notes found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredNotes.map((note) => (
              <div
                key={note.id}
                className={`bg-white rounded-lg shadow border-l-4 ${getPriorityColor(note.priority)} ${
                  note.is_done ? 'opacity-60' : ''
                }`}
              >
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <h3 className={`font-medium ${note.is_done ? 'line-through' : ''}`}>
                      {note.title}
                    </h3>
                    <button
                      onClick={() => toggleDone(note)}
                      className={`p-1 rounded ${note.is_done ? 'text-green-500' : 'text-gray-300 hover:text-green-500'}`}
                    >
                      <CheckCircle size={20} />
                    </button>
                  </div>

                  <p className="mt-2 text-sm text-gray-600 line-clamp-3">{note.content}</p>

                  <div className="mt-3 flex items-center gap-2 flex-wrap">
                    <span className="badge bg-gray-100 text-gray-700 text-xs">{note.category}</span>
                    <span className={`badge text-xs ${
                      note.priority === 'high' ? 'bg-red-100 text-red-700' :
                      note.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {note.priority}
                    </span>
                    {note.reminder_date && (
                      <span className="badge bg-blue-100 text-blue-700 text-xs flex items-center gap-1">
                        <Clock size={12} />
                        {new Date(note.reminder_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <div className="mt-3 pt-3 border-t flex items-center justify-between">
                    <span className="text-xs text-gray-400">
                      {new Date(note.created_at).toLocaleDateString()}
                    </span>
                    <div className="flex gap-1">
                      <button
                        onClick={() => openEdit(note)}
                        className="p-1 hover:bg-gray-100 rounded text-gray-500"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(note.id)}
                        className="p-1 hover:bg-gray-100 rounded text-gray-500 hover:text-red-500"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
              <div className="p-4 border-b">
                <h2 className="text-lg font-semibold">
                  {editingNote ? 'Edit Note' : 'New Note'}
                </h2>
              </div>
              <form onSubmit={handleSubmit} className="p-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Content</label>
                  <textarea
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    rows={4}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Category</label>
                    <select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
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
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Reminder Date</label>
                  <input
                    type="datetime-local"
                    value={formData.reminder_date}
                    onChange={(e) => setFormData({ ...formData, reminder_date: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary">
                    {editingNote ? 'Update' : 'Create'}
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
