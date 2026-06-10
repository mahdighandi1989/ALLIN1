'use client'

// General (non-account) profiles + checklists — requirement A7. A generic
// checklist workspace for recurring topics that aren't tied to a customer
// account: each profile holds several checklists, each with tickable items.
import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { generalApi, parseApiError } from '@/lib/api'
import toast from 'react-hot-toast'
import { LayoutGrid, Plus, Trash2, FolderPlus } from 'lucide-react'

export default function GeneralPage() {
  const [profiles, setProfiles] = useState<any[]>([])
  const [sel, setSel] = useState<any>(null)
  const [checklists, setChecklists] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [newProfile, setNewProfile] = useState('')
  const [newChecklist, setNewChecklist] = useState('')
  const [newItem, setNewItem] = useState<Record<string, string>>({})

  const loadProfiles = async () => {
    try {
      const r = await generalApi.listProfiles()
      setProfiles(r.items)
    } catch (e) { toast.error(parseApiError(e)) } finally { setLoading(false) }
  }
  useEffect(() => { loadProfiles() }, [])

  const openProfile = async (p: any) => {
    setSel(p)
    try {
      const r = await generalApi.listChecklists(p.id)
      setChecklists(r.checklists)
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const addProfile = async () => {
    if (!newProfile.trim()) return
    try {
      await generalApi.createProfile({ title: newProfile.trim() })
      setNewProfile('')
      await loadProfiles()
      toast.success('Profile added')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeProfile = async (id: string) => {
    if (!confirm('Delete this profile and its checklists?')) return
    try {
      await generalApi.deleteProfile(id)
      if (sel?.id === id) { setSel(null); setChecklists([]) }
      await loadProfiles()
      toast.success('Profile deleted')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addChecklist = async () => {
    if (!newChecklist.trim() || !sel) return
    try {
      const c = await generalApi.createChecklist(sel.id, { title: newChecklist.trim() })
      setChecklists((cs) => [...cs, c]); setNewChecklist('')
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeChecklist = async (id: string) => {
    if (!confirm('Delete this checklist?')) return
    try {
      await generalApi.deleteChecklist(id)
      setChecklists((cs) => cs.filter((c) => c.id !== id))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const addItem = async (cid: string) => {
    const text = (newItem[cid] || '').trim()
    if (!text) return
    try {
      const it = await generalApi.addItem(cid, { text })
      setChecklists((cs) => cs.map((c) => c.id === cid ? { ...c, items: [...c.items, it] } : c))
      setNewItem((s) => ({ ...s, [cid]: '' }))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const toggleItem = async (cid: string, it: any) => {
    try {
      const u = await generalApi.updateItem(it.id, { is_done: !it.is_done })
      setChecklists((cs) => cs.map((c) => c.id === cid ? { ...c, items: c.items.map((x: any) => x.id === it.id ? u : x) } : c))
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const removeItem = async (cid: string, id: string) => {
    try {
      await generalApi.deleteItem(id)
      setChecklists((cs) => cs.map((c) => c.id === cid ? { ...c, items: c.items.filter((x: any) => x.id !== id) } : c))
    } catch (e) { toast.error(parseApiError(e)) }
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-5">
        <LayoutGrid size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">General Checklists</h2>
        <span className="text-sm text-gray-400">موضوعاتِ کلی و تکرارشونده (غیرِ مرتبط با یک حساب)</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-5">
        {/* Profiles list */}
        <div className="bg-white rounded-lg shadow-sm p-4 h-fit">
          <div className="flex gap-2 mb-3">
            <input value={newProfile} onChange={(e) => setNewProfile(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addProfile()}
              placeholder="New profile…" className="flex-1 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm" />
            <button onClick={addProfile} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-2.5"><Plus size={16} /></button>
          </div>
          {loading ? <p className="text-sm text-gray-400 py-4 text-center">Loading…</p> : profiles.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">No profiles yet</p>
          ) : (
            <div className="space-y-1">
              {profiles.map((p) => (
                <div key={p.id} className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer ${sel?.id === p.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50'}`}
                  onClick={() => openProfile(p)}>
                  <span className="truncate">{p.title}<span className="text-xs text-gray-400 ml-1">({p.checklists})</span></span>
                  <button onClick={(e) => { e.stopPropagation(); removeProfile(p.id) }} type="button" className="text-gray-400 hover:text-red-600"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected profile's checklists */}
        <div className="space-y-4">
          {!sel ? (
            <div className="bg-white rounded-lg shadow-sm p-10 text-center text-gray-400">یک پروفایل را از سمتِ چپ انتخاب کنید</div>
          ) : (
            <>
              <div className="bg-white rounded-lg shadow-sm p-4 flex gap-2 items-center">
                <FolderPlus size={16} className="text-gray-400" />
                <input value={newChecklist} onChange={(e) => setNewChecklist(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addChecklist()}
                  placeholder={`New checklist in "${sel.title}"…`} className="flex-1 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm" />
                <button onClick={addChecklist} type="button" className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium">Add checklist</button>
              </div>
              {checklists.length === 0 ? (
                <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-400">No checklists yet</div>
              ) : checklists.map((c) => {
                const doneN = c.items.filter((i: any) => i.is_done).length
                return (
                  <div key={c.id} className="bg-white rounded-lg shadow-sm p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{c.title} <span className="text-xs text-gray-400">{doneN}/{c.items.length}</span></h3>
                      <button onClick={() => removeChecklist(c.id)} type="button" className="text-gray-400 hover:text-red-600"><Trash2 size={15} /></button>
                    </div>
                    <div className="space-y-1 mb-2">
                      {c.items.map((it: any) => (
                        <div key={it.id} className="flex items-center gap-2 group">
                          <input type="checkbox" checked={!!it.is_done} onChange={() => toggleItem(c.id, it)} />
                          <span className={`flex-1 text-sm ${it.is_done ? 'line-through text-gray-400' : ''}`}>{it.text}</span>
                          <button onClick={() => removeItem(c.id, it.id)} type="button" className="text-gray-300 hover:text-red-600 opacity-0 group-hover:opacity-100"><Trash2 size={13} /></button>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <input value={newItem[c.id] || ''} onChange={(e) => setNewItem((s) => ({ ...s, [c.id]: e.target.value }))} onKeyDown={(e) => e.key === 'Enter' && addItem(c.id)}
                        placeholder="New item…" className="flex-1 border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm" />
                      <button onClick={() => addItem(c.id)} type="button" className="text-blue-600 hover:underline text-sm">Add</button>
                    </div>
                  </div>
                )
              })}
            </>
          )}
        </div>
      </div>
    </Layout>
  )
}
