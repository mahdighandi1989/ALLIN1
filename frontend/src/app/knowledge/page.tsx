'use client'

import { useEffect, useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { BookOpen, Search, ListTree, Sparkles, Trash2 } from 'lucide-react'
import { SECTIONS, KB_TITLE, KB_SUBTITLE, type Block, type Section } from './content'
import { knowledgeApi, type KbTopic } from '@/lib/api'
import { useAuth } from '@/lib/auth'

function blockText(b: Block): string {
  switch (b.type) {
    case 'p':
    case 'sub':
    case 'note':
    case 'code':
      return b.text
    case 'ul':
    case 'ol':
      return b.items.join(' ')
    case 'table':
      return [...b.headers, ...b.rows.flat()].join(' ')
    default:
      return ''
  }
}

function sectionMatches(s: Section, q: string): boolean {
  if (!q) return true
  const hay = (s.title + ' ' + s.blocks.map(blockText).join(' ')).toLowerCase()
  return hay.includes(q.toLowerCase())
}

function BlockView({ b }: { b: Block }) {
  switch (b.type) {
    case 'p':
      return <p className="text-gray-700 leading-8 mb-3">{b.text}</p>
    case 'sub':
      return <h3 className="font-bold text-gray-900 mt-6 mb-2 text-[15px]">{b.text}</h3>
    case 'ul':
      return (
        <ul className="list-disc pr-6 space-y-1.5 mb-3 text-gray-700 leading-7">
          {b.items.map((it, i) => <li key={i}>{it}</li>)}
        </ul>
      )
    case 'ol':
      return (
        <ol className="list-decimal pr-6 space-y-1.5 mb-3 text-gray-700 leading-7">
          {b.items.map((it, i) => <li key={i}>{it}</li>)}
        </ol>
      )
    case 'note':
      return (
        <div className="bg-amber-50 border-r-4 border-amber-400 px-4 py-3 rounded mb-3 text-amber-900 leading-7">
          {b.text}
        </div>
      )
    case 'code':
      return (
        <pre dir="ltr" className="bg-gray-900 text-gray-100 text-xs leading-6 p-4 rounded-lg mb-3 overflow-x-auto whitespace-pre-wrap text-left">
          {b.text}
        </pre>
      )
    case 'table':
      return (
        <div className="overflow-x-auto mb-4">
          <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
            <thead className="bg-gray-100 text-gray-700">
              <tr>
                {b.headers.map((h, i) => (
                  <th key={i} className="px-3 py-2 text-right font-semibold border-b border-gray-200">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {b.rows.map((row, ri) => (
                <tr key={ri} className={ri % 2 ? 'bg-gray-50' : 'bg-white'}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-3 py-2 text-gray-700 border-b border-gray-100 align-top">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    default:
      return null
  }
}

function topicMatches(t: KbTopic, q: string): boolean {
  if (!q) return true
  const hay = (t.title + ' ' + t.category + ' ' + t.entries.map((e) => e.content + ' ' + (e.source_ref || '')).join(' ')).toLowerCase()
  return hay.includes(q.toLowerCase())
}

export default function KnowledgePage() {
  const { user } = useAuth()
  const [query, setQuery] = useState('')
  const [dyn, setDyn] = useState<KbTopic[]>([])
  const canEdit = user && ['admin', 'manager', 'editor'].includes((user as any).role || '')
  const loadDyn = () => knowledgeApi.list().then((r) => setDyn(r.topics || [])).catch(() => setDyn([]))
  useEffect(() => { loadDyn() }, [])
  const visible = useMemo(() => SECTIONS.filter((s) => sectionMatches(s, query)), [query])
  const dynVisible = useMemo(() => dyn.filter((t) => topicMatches(t, query)), [dyn, query])
  // the LIVE index of the dynamic part: categories in first-seen order
  const dynCats = useMemo(() => {
    const out: { cat: string; topics: KbTopic[] }[] = []
    for (const t of dynVisible) {
      const g = out.find((c) => c.cat === (t.category || 'عمومی'))
      if (g) g.topics.push(t)
      else out.push({ cat: t.category || 'عمومی', topics: [t] })
    }
    return out
  }, [dynVisible])
  const removeEntry = async (id: string) => {
    if (!confirm('این مطلب از پایگاه دانش حذف شود؟')) return
    try { await knowledgeApi.deleteEntry(id); loadDyn() } catch { /* keep page usable */ }
  }

  return (
    <Layout>
      <div dir="rtl" className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-start gap-3 mb-2">
          <div className="bg-blue-600 text-white rounded-xl p-2.5">
            <BookOpen size={22} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{KB_TITLE}</h1>
            <p className="text-gray-500 text-sm mt-0.5">{KB_SUBTITLE}</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative my-5">
          <Search size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="جست‌وجو در دانش‌نامه (مثلاً: ترهین، AECB، اوردرافت، کارمزد، چک ضمانتی)…"
            className="w-full border border-gray-300 rounded-xl py-2.5 pr-10 pl-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
        </div>

        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Table of contents (فهرست) */}
          <aside className="lg:w-72 w-full lg:sticky lg:top-20 shrink-0">
            <div className="bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-center gap-2 text-gray-900 font-bold mb-3">
                <ListTree size={18} className="text-blue-600" />
                فهرست
              </div>
              <nav className="space-y-1 max-h-[70vh] overflow-y-auto">
                {visible.map((s) => (
                  <a
                    key={s.id}
                    href={`#${s.id}`}
                    className="block text-sm text-gray-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg px-3 py-1.5 transition-colors"
                  >
                    {s.title}
                  </a>
                ))}
                {dynCats.length > 0 && (
                  <div className="pt-2 mt-2 border-t border-gray-100">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-violet-700 px-3 pb-1">
                      <Sparkles size={13} /> مطالبِ برداشت‌شده از نامه‌ها
                    </div>
                    {dynCats.map((c) => (
                      <div key={c.cat}>
                        <div className="text-[11px] text-gray-400 px-3 pt-1">{c.cat}</div>
                        {c.topics.map((t) => (
                          <a key={t.id} href={`#kb-${t.id}`}
                            className="block text-sm text-gray-600 hover:text-violet-700 hover:bg-violet-50 rounded-lg px-3 py-1.5 transition-colors">
                            {t.title}
                          </a>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
                {visible.length === 0 && dynVisible.length === 0 && (
                  <p className="text-sm text-gray-400 px-3 py-1.5">موردی یافت نشد.</p>
                )}
              </nav>
            </div>
          </aside>

          {/* Content */}
          <div className="flex-1 min-w-0 space-y-5">
            {visible.map((s) => (
              <section
                key={s.id}
                id={s.id}
                className="bg-white border border-gray-200 rounded-xl p-5 lg:p-6 scroll-mt-20"
              >
                <h2 className="text-lg font-bold text-blue-800 mb-4 pb-2 border-b border-gray-100">
                  {s.title}
                </h2>
                {s.blocks.map((b, i) => <BlockView key={i} b={b} />)}
              </section>
            ))}
            {/* دانشِ برداشت‌شده از نامه‌ها/پیوست‌ها (پویا — دستیارِ هوشمند پرش می‌کند) */}
            {dynCats.map((c) => (
              <div key={c.cat} className="space-y-5">
                {c.topics.map((t) => (
                  <section key={t.id} id={`kb-${t.id}`}
                    className="bg-white border border-violet-200 rounded-xl p-5 lg:p-6 scroll-mt-20">
                    <div className="flex items-center justify-between gap-2 mb-4 pb-2 border-b border-gray-100">
                      <h2 className="text-lg font-bold text-violet-800 flex items-center gap-2">
                        <Sparkles size={16} /> {t.title}
                      </h2>
                      <span className="text-xs bg-violet-50 text-violet-700 rounded-full px-2.5 py-1">{t.category}</span>
                    </div>
                    {t.entries.map((e) => (
                      <div key={e.id} className="mb-4 last:mb-0">
                        <p className="text-gray-700 leading-8 whitespace-pre-wrap">{e.content}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[11px] text-gray-400" dir="rtl">
                            منبع: {e.source_ref || '—'}{e.account_no ? ` · حساب ${e.account_no}` : ''}{e.created_at ? ` · ${e.created_at.slice(0, 10)}` : ''}
                          </span>
                          {canEdit && (
                            <button onClick={() => removeEntry(e.id)} type="button" title="حذفِ این مطلب"
                              className="text-red-400 hover:text-red-600"><Trash2 size={13} /></button>
                          )}
                        </div>
                      </div>
                    ))}
                  </section>
                ))}
              </div>
            ))}
            {visible.length === 0 && dynVisible.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-xl p-10 text-center text-gray-400">
                نتیجه‌ای برای «{query}» پیدا نشد.
              </div>
            )}
            <p className="text-xs text-gray-400 text-center pt-2">
              منبع: گردآوری و سازمان‌دهیِ اسناد عملیاتیِ دایره تسهیلات اعطایی (CFD) — بانک صادرات ایران، سرپرستی امارات.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  )
}
