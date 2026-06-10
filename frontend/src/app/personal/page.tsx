'use client'

// Private, per-user personal notes (the Excel personal-notes panel, A8/A11/A16).
// Notes are checklist-like (tick when done), private to the signed-in user, and
// can be emailed in one click (the unsent ones), then marked as sent.
import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { personalApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import { StickyNote, Plus, Trash2, Mail } from 'lucide-react'

export default function PersonalNotesPage() {
  const [notes, setNotes] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('Today')
  const [sending, setSending] = useState(false)

  const load = async () => {
    try { setNotes((await personalApi.list()).items) }
    catch (e) { toast.error(parseApiError(e)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const add = async () => {
    if (!content.trim()) return
    try {
      const n = await personalApi.add({ content: content.trim(), category })
      setNotes((ns) => [n, ...ns]); setContent('')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const toggle = async (n: any) => {
    try {
      const u = await personalApi.update(n.id, { is_done: !n.is_done })
      setNotes((ns) => ns.map((x) => x.id === n.id ? u : x))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const remove = async (id: string) => {
    try {
      await personalApi.remove(id)
      setNotes((ns) => ns.filter((x) => x.id !== id))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const sendEmail = async () => {
    setSending(true)
    try {
      const r = await personalApi.sendEmail()
      if (r.sent > 0) { toast.success(`Emailed ${r.sent} note(s) to ${r.to}`); load() }
      else toast(r.message || 'No unsent notes')
    } catch (e) { toast.error(parseApiError(e)) } finally { setSending(false) }
  }

  const unsent = notes.filter((n) => !n.is_sent).length

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-1">
        <StickyNote size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">Personal Notes</h2>
        <span className="text-sm text-gray-400">خصوصی · فقط برای شما</span>
      </div>
      <p className="text-xs text-gray-400 mb-5">یادداشت‌های شخصیِ روزانه؛ با یک دکمه می‌توانید موارد ارسال‌نشده را ایمیل کنید (آدرس/کلید/امضا در Settings).</p>

      <div className="max-w-3xl space-y-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="flex gap-2 mb-2">
            <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category"
              className="w-32 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm" />
            <span className="flex-1" />
            <button onClick={sendEmail} disabled={sending || unsent === 0} type="button"
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg px-3 py-1.5 text-sm">
              <Mail size={14} /> {sending ? 'Sending…' : `Email unsent (${unsent})`}
            </button>
          </div>
          <textarea value={content} dir="auto" onChange={(e) => setContent(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) add() }}
            placeholder="یک یادداشت بنویسید… (Ctrl+Enter برای ثبت)" rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" style={{ fontFamily: "'B Nazanin', Tahoma, sans-serif", fontSize: 14 }} />
          <div className="flex justify-end mt-2">
            <button onClick={add} type="button" className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-900 text-white rounded-lg px-4 py-1.5 text-sm font-medium"><Plus size={15} /> Add note</button>
          </div>
        </div>

        {loading ? <p className="text-center text-gray-400 py-8">Loading…</p> : notes.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-10 text-center text-gray-400">No notes yet</div>
        ) : (
          <div className="space-y-2">
            {notes.map((n) => (
              <div key={n.id} className={`bg-white rounded-lg shadow-sm p-3 flex items-start gap-3 ${n.is_done ? 'opacity-70' : ''}`}>
                <input type="checkbox" checked={!!n.is_done} onChange={() => toggle(n)} className="mt-1" />
                <div className="flex-1 min-w-0">
                  <p dir="auto" className={`text-sm whitespace-pre-wrap ${n.is_done ? 'line-through text-gray-400' : ''}`} style={{ fontFamily: "'B Nazanin', Tahoma, sans-serif" }}>{n.content}</p>
                  <div className="text-xs text-gray-400 mt-1">
                    {n.created_date} · {n.category || 'General'}
                    {n.is_sent ? <span className="ml-2 text-green-600">✓ sent</span> : <span className="ml-2 text-amber-600">unsent</span>}
                  </div>
                </div>
                <button onClick={() => remove(n.id)} type="button" className="text-gray-300 hover:text-red-600"><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  )
}
