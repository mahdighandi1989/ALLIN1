'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  X, Send, Paperclip, MessageSquare, Plus, Globe, BookOpen, CheckCircle2, Loader2, FileText,
  Zap, Search, Wallet, AlertTriangle, ExternalLink, Download, History,
} from 'lucide-react'
import api, {
  knowledgeApi, parseApiError,
  type KbChatFile, type KbChatMessage, type KbChatModels, type KbChatSessionRow,
} from '@/lib/api'
import { KB_TABS } from './tabs'

const SOURCE_STYLE: Record<string, string> = {
  kb: 'bg-green-50 text-green-700 border-green-200',
  web: 'bg-amber-50 text-amber-800 border-amber-200',
  none: 'bg-gray-100 text-gray-600 border-gray-200',
}
const SOURCE_LABEL: Record<string, string> = { kb: 'پاسخ از دانش‌نامه', web: 'پاسخ از وب (در دانش‌نامه نبود)', none: 'بدون پاسخ' }
const EXTRACT_LABEL: Record<string, string> = {
  ok: 'کامل خوانده شد', empty: 'خالی', unsupported: 'متن ندارد/پشتیبانی نمی‌شود', failed: 'استخراج شکست خورد', image: 'تصویر',
}

function fmtSize(n: number): string {
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`
  if (n >= 1024) return `${Math.round(n / 1024)} KB`
  return `${n} B`
}

function ModelBadges({ m }: { m: { fast: boolean; web: boolean; files: boolean; cheap: boolean } }) {
  const items = [
    m.fast && { k: 'fast', t: 'سریع', I: Zap },
    m.web && { k: 'web', t: 'جستجوی وب', I: Search },
    m.files && { k: 'files', t: 'خواندن فایل', I: FileText },
    m.cheap && { k: 'cheap', t: 'ارزان', I: Wallet },
  ].filter(Boolean) as { k: string; t: string; I: any }[]
  return (
    <span className="inline-flex flex-wrap gap-1">
      {items.map(({ k, t, I }) => (
        <span key={k} className="inline-flex items-center gap-0.5 text-[10px] bg-blue-50 text-blue-700 rounded-full px-1.5 py-0.5"><I size={10} />{t}</span>
      ))}
    </span>
  )
}

export default function KbChat({ onClose, canAsk, onFiled }: { onClose: () => void; canAsk: boolean; onFiled: () => void }) {
  const [models, setModels] = useState<KbChatModels | null>(null)
  const [modelId, setModelId] = useState<number | null>(null)
  const [allowWeb, setAllowWeb] = useState(true)
  const [sessions, setSessions] = useState<KbChatSessionRow[]>([])
  const [sid, setSid] = useState<string>('')
  const [msgs, setMsgs] = useState<KbChatMessage[]>([])
  const [files, setFiles] = useState<KbChatFile[]>([])
  const [text, setText] = useState('')
  const [picked, setPicked] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [approving, setApproving] = useState<string>('')
  const [tabAsk, setTabAsk] = useState<{ id: string; tabs: { id: string; label: string }[] } | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const loadSessions = useCallback(() => knowledgeApi.chatSessions().then((r) => setSessions(r.sessions || [])).catch(() => {}), [])
  useEffect(() => {
    knowledgeApi.chatModels().then((r) => { setModels(r); setModelId(r.default_model_id) }).catch((e) => setErr(parseApiError(e)))
    loadSessions()
  }, [loadSessions])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, busy])

  const open = async (id: string) => {
    setErr(''); setShowHistory(false)
    try {
      const r = await knowledgeApi.chatSession(id)
      setSid(id); setMsgs(r.messages); setFiles(r.files)
    } catch (e) { setErr(parseApiError(e)) }
  }
  const fresh = () => { setSid(''); setMsgs([]); setFiles([]); setErr(''); setPicked([]); setText(''); setShowHistory(false) }

  const send = async () => {
    const q = text.trim()
    if (!q || busy) return
    setBusy(true); setErr('')
    const optimistic: KbChatMessage = {
      id: 'tmp', session_id: sid, role: 'user', content: q, source: '', model_name: '', web_model_name: '', sources: [],
      kb_state: '', kb_placement: '', error: '', meta: { file_ids: [] },
    }
    setMsgs((m) => [...m, optimistic])
    try {
      const r = await knowledgeApi.chatAsk({ question: q, session_id: sid || undefined, model_id: modelId, allow_web: allowWeb, files: picked })
      setSid(r.session_id)
      setMsgs((m) => [...m.filter((x) => x.id !== 'tmp'), r.user, r.assistant])
      setFiles((f) => [...f, ...r.files])
      setText(''); setPicked([])
      loadSessions()
    } catch (e) {
      setMsgs((m) => m.filter((x) => x.id !== 'tmp'))
      setErr(parseApiError(e))
    } finally { setBusy(false) }
  }

  const approve = async (id: string, tab?: string) => {
    setApproving(id); setErr('')
    try {
      const r = await knowledgeApi.chatApprove(id, { model_id: modelId, tab })
      if (r.error === 'tab_unclear') { setTabAsk({ id, tabs: r.tabs || [] }); return }
      setTabAsk(null)
      if (sid) await open(sid)
      onFiled()
    } catch (e) { setErr(parseApiError(e)) } finally { setApproving('') }
  }

  const download = async (f: KbChatFile) => {
    try {
      const r = await api.get(knowledgeApi.chatFileUrl(f.id), { responseType: 'blob' })
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a'); a.href = url; a.download = f.filename; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 5000)
    } catch (e) { setErr(parseApiError(e)) }
  }

  const filesOf = (m: KbChatMessage) => files.filter((f) => f.message_id === m.id || (m.meta?.file_ids || []).includes(f.id))
  const maxMb = models?.limits.max_file_mb ?? 50

  return (
    <div dir="rtl" className="fixed inset-0 z-50 bg-black/40 flex items-stretch justify-center p-0 sm:p-4" role="dialog" aria-label="گفت‌وگو با دانش‌نامه">
      <div className="bg-gray-50 w-full max-w-6xl rounded-none sm:rounded-2xl shadow-2xl flex overflow-hidden">
        {/* تاریخچه */}
        <aside className={`${showHistory ? 'flex' : 'hidden'} md:flex w-full md:w-64 shrink-0 bg-white border-l border-gray-200 flex-col absolute md:static inset-0 z-10`}>
          <div className="p-3 border-b border-gray-100 flex items-center gap-2">
            <History size={16} className="text-gray-500" />
            <span className="font-bold text-sm flex-1">تاریخچهٔ گفت‌وگو</span>
            <button type="button" onClick={() => setShowHistory(false)} className="md:hidden text-gray-400"><X size={16} /></button>
          </div>
          <button type="button" onClick={fresh} className="m-3 flex items-center justify-center gap-1.5 text-sm bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700">
            <Plus size={15} /> گفت‌وگوی جدید
          </button>
          <div className="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
            {sessions.length === 0 && <p className="text-xs text-gray-400 px-2 py-4 text-center">هنوز گفت‌وگویی ثبت نشده.</p>}
            {sessions.map((s) => (
              <button key={s.id} type="button" onClick={() => open(s.id)}
                className={`w-full text-right text-sm rounded-lg px-3 py-2 hover:bg-blue-50 ${s.id === sid ? 'bg-blue-50 text-blue-800 font-bold' : 'text-gray-700'}`}>
                <div className="line-clamp-2 leading-6">{s.title}</div>
                <div className="text-[10px] text-gray-400" dir="ltr">{(s.updated_at || s.created_at || '').slice(0, 16).replace('T', ' ')}</div>
              </button>
            ))}
          </div>
        </aside>

        <section className="flex-1 min-w-0 flex flex-col">
          {/* هدر + انتخاب مدل */}
          <header className="bg-white border-b border-gray-200 p-3 flex flex-wrap items-center gap-2">
            <MessageSquare size={18} className="text-blue-600" />
            <h2 className="font-bold text-gray-900">گفت‌وگو با دانش‌نامه</h2>
            <button type="button" onClick={() => setShowHistory(true)} className="md:hidden text-xs text-blue-700 border border-blue-200 rounded-lg px-2 py-1">تاریخچه</button>
            <div className="flex-1" />
            <label className="flex items-center gap-1.5 text-xs text-gray-600">
              <input type="checkbox" checked={allowWeb} onChange={(e) => setAllowWeb(e.target.checked)} />
              <Globe size={13} /> اگر در دانش‌نامه نبود از وب بیاور
            </label>
            <button type="button" onClick={onClose} aria-label="بستن" className="text-gray-400 hover:text-gray-700"><X size={20} /></button>
            <div className="w-full flex flex-wrap items-center gap-2">
              <span className="text-xs text-gray-500">مدل:</span>
              <select value={modelId ?? ''} onChange={(e) => setModelId(e.target.value ? Number(e.target.value) : null)}
                className="border border-gray-300 rounded-lg px-2 py-1 text-sm bg-white max-w-full" disabled={!models || models.models.length === 0}>
                {models?.models.length === 0 && <option value="">هیچ مدلِ فعالی نیست</option>}
                {models?.models.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.recommended ? '★ ' : ''}{m.display_name} — {m.provider_name}{m.fast ? ' · سریع' : ''}{m.web ? ' · وب' : ''}{m.files ? ' · فایل' : ''}{m.cheap ? ' · ارزان' : ''}
                  </option>
                ))}
              </select>
              {models && modelId != null && (() => { const m = models.models.find((x) => x.id === modelId); return m ? <ModelBadges m={m} /> : null })()}
              {models && models.models.length === 0 && (
                <span className="text-xs text-red-600">در «تنظیمات › مدل‌های هوش مصنوعی» یک ارائه‌دهنده را فعال و کلید بدهید.</span>
              )}
            </div>
            {models && (
              <p className="w-full text-[11px] text-gray-400 leading-5">
                فهرست از مدل‌های فعالِ سیستم ساخته می‌شود و خودکار هر {models.sync.interval_hours} ساعت با ارائه‌دهنده‌ها هماهنگ می‌شود
                {models.sync.last_run_at ? <> (آخرین: <span dir="ltr">{models.sync.last_run_at.slice(0, 16).replace('T', ' ')}</span>)</> : ' (هنوز اجرا نشده)'}؛
                پیش‌فرض: مدل‌های سریع + دارای جستجوی وب + خواننده‌ٔ فایل + ارزان. ★ = پیشنهادی.
              </p>
            )}
          </header>

          {/* پیام‌ها */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {msgs.length === 0 && (
              <div className="text-center text-gray-400 py-16 leading-8">
                <BookOpen size={36} className="mx-auto mb-3 text-gray-300" />
                <p>درباره‌ی مسائل بانکی بپرسید.</p>
                <p className="text-sm">پاسخ از همهٔ مطالب دانش‌نامه (همهٔ تب‌ها، چه موجود و چه آنچه بعداً اضافه می‌شود) داده می‌شود؛ اگر آنجا نبود، از وب می‌آید و با «تأیید» در دانش‌نامه ثبت می‌شود.</p>
              </div>
            )}
            {msgs.map((m) => m.role === 'user' ? (
              <div key={m.id} className="flex justify-start">
                <div className="max-w-[85%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 leading-7 whitespace-pre-wrap">
                  {m.content}
                  {filesOf(m).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {filesOf(m).map((f) => (
                        <span key={f.id} className="inline-flex items-center gap-1 text-[11px] bg-white/20 rounded-full px-2 py-0.5"><Paperclip size={11} />{f.filename}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div key={m.id} className="flex justify-end">
                <div className="max-w-[92%] w-full sm:w-auto bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className={`text-[11px] border rounded-full px-2 py-0.5 ${SOURCE_STYLE[m.source || 'none']}`}>{SOURCE_LABEL[m.source || 'none']}</span>
                    {m.model_name && <span className="text-[11px] text-gray-400">{m.model_name}{m.web_model_name && m.web_model_name !== m.model_name ? ` ← وب: ${m.web_model_name}` : ''}</span>}
                  </div>
                  <div className="text-gray-800 leading-8 whitespace-pre-wrap">{m.content}</div>
                  {m.sources.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      <div className="text-xs font-bold text-gray-500 mb-1">منابع وب</div>
                      <ul className="space-y-0.5">
                        {m.sources.map((s) => (
                          <li key={s.url} className="text-xs">
                            <a href={s.url} target="_blank" rel="noreferrer noopener" className="text-blue-700 hover:underline inline-flex items-center gap-1">
                              <ExternalLink size={11} /><span dir="ltr">{s.title.length > 70 ? s.title.slice(0, 70) + '…' : s.title}</span>
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {m.meta?.web_model_reason && m.source === 'web' && m.meta.web_model_reason.startsWith('مدلِ انتخاب‌شده جستجو') && (
                    <p className="text-[11px] text-amber-700 mt-2">{m.meta.web_model_reason}</p>
                  )}
                  {(m.meta?.unread_files?.length || 0) > 0 && (
                    <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 leading-6">
                      <AlertTriangle size={12} className="inline ml-1" />فایل‌های خوانده‌نشده: {m.meta.unread_files!.join(' | ')}
                    </div>
                  )}
                  {(m.meta?.warnings?.length || 0) > 0 && (
                    <div className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 leading-6">{m.meta.warnings!.join(' | ')}</div>
                  )}
                  {m.meta?.kb?.trimmed && (
                    <p className="text-[11px] text-amber-700 mt-2">
                      به‌دلیل حجم، {m.meta.kb.included_sections} از {m.meta.kb.total_sections} بخشِ دانش‌نامه (نزدیک‌ترین‌ها به پرسش) به مدل داده شد.
                    </p>
                  )}
                  {m.source === 'web' && m.kb_state === 'pending' && canAsk && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <button type="button" disabled={approving === m.id} onClick={() => approve(m.id)}
                        className="inline-flex items-center gap-1.5 text-sm bg-green-600 text-white rounded-lg px-3 py-1.5 hover:bg-green-700 disabled:opacity-60">
                        {approving === m.id ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                        تأیید و ثبت در دانش‌نامه
                      </button>
                      <span className="text-[11px] text-gray-400 mr-2">هوش مصنوعی تحلیل می‌کند و ذیلِ تب و فهرستِ مربوط ثبت می‌شود (در صورت نبودنِ دسته/عنوان، ساخته می‌شود).</span>
                      {tabAsk?.id === m.id && (
                        <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg p-2 text-xs">
                          هوش مصنوعی تبِ مناسب را مشخص نکرد؛ کدام تب؟
                          <div className="flex flex-wrap gap-1.5 mt-1.5">
                            {(tabAsk.tabs.length ? tabAsk.tabs : KB_TABS.filter((t) => t.id !== 'compare').map((t) => ({ id: t.id, label: t.label }))).map((t) => (
                              <button key={t.id} type="button" onClick={() => approve(m.id, t.id)} className="bg-white border border-amber-300 rounded-full px-2.5 py-1 hover:bg-amber-100">{t.label}</button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {m.kb_state === 'filed' && (
                    <div className="mt-3 pt-2 border-t border-gray-100 text-xs text-green-700 flex items-start gap-1.5">
                      <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
                      <span>در دانش‌نامه ثبت شد: <b>{m.kb_placement}</b></span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {busy && (
              <div className="flex justify-end">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                  <Loader2 size={15} className="animate-spin" /> در حال بررسیِ دانش‌نامه و فایل‌ها… (در صورت جستجوی وب ممکن است چند دقیقه طول بکشد)
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* فایل‌های این گفت‌وگو */}
          {files.length > 0 && (
            <div className="bg-white border-t border-gray-100 px-3 py-2">
              <div className="text-[11px] font-bold text-gray-500 mb-1">فایل‌های این گفت‌وگو (متنِ کامل نگه‌داری شده؛ نسخهٔ اصلی در Google Drive با نامِ کدگذاری‌شده)</div>
              <div className="flex flex-wrap gap-1.5">
                {files.map((f) => (
                  <span key={f.id} className="inline-flex items-center gap-1.5 text-[11px] bg-gray-50 border border-gray-200 rounded-lg px-2 py-1" title={f.note || f.store_note}>
                    <FileText size={12} className="text-gray-400" />
                    <span>{f.filename}</span>
                    <span className="text-gray-400" dir="ltr">{fmtSize(f.byte_size)}</span>
                    <span className={f.extract_status === 'ok' ? 'text-green-700' : 'text-amber-700'}>{EXTRACT_LABEL[f.extract_status] || f.extract_status}{f.extract_status === 'ok' ? ` (${f.text_chars.toLocaleString('fa')} نویسه)` : ''}</span>
                    {f.durable && f.drive_link ? (
                      <a href={f.drive_link} target="_blank" rel="noreferrer noopener" className="text-blue-700 hover:underline inline-flex items-center gap-0.5"><ExternalLink size={10} />Drive</a>
                    ) : (
                      <span className="text-red-600">فقط روی سرور (Drive تنظیم نیست)</span>
                    )}
                    <button type="button" onClick={() => download(f)} className="text-gray-400 hover:text-gray-700" title="دانلود"><Download size={11} /></button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* ورودی */}
          <footer className="bg-white border-t border-gray-200 p-3">
            {err && <div className="mb-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{err}</div>}
            {!canAsk && <div className="mb-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">پرسیدن (که هزینهٔ هوش مصنوعی دارد) فقط برای ویرایشگر و مدیر باز است؛ تاریخچه را می‌توانید ببینید.</div>}
            {picked.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {picked.map((f, i) => (
                  <span key={i} className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-800 border border-blue-200 rounded-full px-2 py-0.5">
                    <Paperclip size={11} />{f.name} <span dir="ltr" className="text-blue-400">{fmtSize(f.size)}</span>
                    <button type="button" onClick={() => setPicked((p) => p.filter((_, j) => j !== i))} aria-label="حذف"><X size={11} /></button>
                  </span>
                ))}
              </div>
            )}
            <div className="flex items-end gap-2">
              <input ref={fileRef} type="file" multiple className="hidden" onChange={(e) => {
                const list = Array.from(e.target.files || [])
                const big = list.find((f) => f.size > maxMb * 1024 * 1024)
                if (big) setErr(`«${big.name}» از ${maxMb} مگابایت بزرگ‌تر است.`)
                else setPicked((p) => [...p, ...list].slice(0, models?.limits.max_files ?? 12))
                e.target.value = ''
              }} />
              <button type="button" onClick={() => fileRef.current?.click()} disabled={!canAsk}
                title={`پیوست فایل (هر نوع؛ چندتایی؛ تا ${maxMb} مگابایت هر فایل) — کامل و بدون خلاصه خوانده می‌شود`}
                className="shrink-0 border border-gray-300 rounded-xl p-2.5 text-gray-600 hover:bg-gray-50 disabled:opacity-50"><Paperclip size={18} /></button>
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} disabled={!canAsk}
                onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send() } }}
                placeholder="پرسش بانکی خود را بنویسید… (Ctrl+Enter برای ارسال)"
                className="flex-1 border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y max-h-48" />
              <button type="button" onClick={send} disabled={busy || !canAsk || !text.trim() || !models?.models.length}
                className="shrink-0 bg-blue-600 text-white rounded-xl px-4 py-2.5 hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1.5 text-sm">
                {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />} ارسال
              </button>
            </div>
          </footer>
        </section>
      </div>
    </div>
  )
}
