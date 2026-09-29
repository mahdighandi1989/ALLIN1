'use client'
// v141 — «نظارت و سرکشی»: the whole board.
//
// Every sheet the owner filed, what the supervisor answered, the dependency walk
// behind that answer, and the tick. The colour of a sheet is DERIVED from the
// outcome, never from the fact that somebody replied — that distinction is the
// whole reason this page is trustworthy.
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Layout from '@/components/Layout'
import { RefreshCw, Check, Trash2, ExternalLink, Paperclip, X, Pencil } from 'lucide-react'
import { inspectionApi, parseApiError, type InspectionFile, type InspectionReport } from '@/lib/api'
import { geometryLabel } from '@/lib/inspectionSpot'
import { AuthedDownload, AuthedImage } from '@/lib/AuthedMedia'
import { TONE } from '@/lib/inspection'
import toast from 'react-hot-toast'

const FA = '۰۱۲۳۴۵۶۷۸۹'
const fa = (n: number | string) => String(n).replace(/[0-9]/g, (d) => FA[+d])

const FILTERS: { key: string; label: string }[] = [
  { key: 'open', label: 'در انتظارِ ناظر' },
  { key: 'answered', label: 'ناظر پاسخ داد' },
  { key: 'approved', label: 'تأییدشده' },
  { key: 'filed', label: 'بایگانی' },
  { key: '', label: 'همه' },
]

export default function InspectionPage() {
  const [reports, setReports] = useState<InspectionReport[]>([])
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [filter, setFilter] = useState('')
  const [busy, setBusy] = useState(false)
  const [openId, setOpenId] = useState<string | null>(null)
  const [reply, setReply] = useState('')
  // v146 — attaching a sample to a sheet that already exists, and reading one back.
  const [upPct, setUpPct] = useState<{ id: string; name: string; pct: number } | null>(null)
  const [peek, setPeek] = useState<{ file: InspectionFile; text: string; loading: boolean } | null>(null)
  const [editing, setEditing] = useState<{ noteId: string; text: string } | null>(null)

  const load = useCallback(async () => {
    setBusy(true)
    try {
      const d = await inspectionApi.list({ include_filed: true, status: filter || undefined })
      setReports(d.reports)
      setCounts(d.counts || {})
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy(false) }
  }, [filter])
  useEffect(() => { void load() }, [load])

  const approve = async (r: InspectionReport) => {
    try {
      await inspectionApi.setStatus(r.id, r.status === 'approved' ? 'open' : 'approved')
      toast.success(r.status === 'approved' ? 'تأیید برداشته شد' : 'تأیید ثبت شد — دورِ بعدِ ناظر بایگانی‌اش می‌کند')
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }
  const remove = async (r: InspectionReport) => {
    if (!confirm(`گزارشِ ${fa(r.number)} حذف شود؟`)) return
    try { await inspectionApi.remove(r.id); await load() } catch (e) { toast.error(parseApiError(e)) }
  }
  const addNote = async (r: InspectionReport) => {
    if (!reply.trim()) return
    try {
      await inspectionApi.note(r.id, { text: reply.trim() })
      setReply('')
      toast.success('نوشته شد — این برگه دوباره در صفِ ناظر است')
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const attach = useCallback(async (r: InspectionReport, files: File[]) => {
    for (const f of files) {
      try {
        setUpPct({ id: r.id, name: f.name, pct: 0 })
        await inspectionApi.upload(r.id, f, '', (pct) => setUpPct({ id: r.id, name: f.name, pct }))
        toast.success(`«${f.name}» پیوست شد — ناظر باید کاملش را بخواند`)
      } catch (e) { toast.error(`${f.name}: ${parseApiError(e)}`) }
    }
    setUpPct(null)
    await load()
  }, [load])

  const rush = useCallback(async (r: InspectionReport) => {
    try {
      if (r.urgent) {
        await inspectionApi.unrush(r.id)
        toast.success('از صفِ فوری بیرون آمد')
      } else {
        const { position } = await inspectionApi.rush(r.id)
        toast.success(position === 1
          ? 'در صفِ فوری، نفرِ اول — ناظر در بازبینیِ بعدی همین را برمی‌دارد'
          : `در صفِ فوری، نفرِ ${fa(position)} — به ترتیبی که زدی انجام می‌شود`)
      }
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }, [load])

  const saveEdit = useCallback(async (r: InspectionReport, noteId: string) => {
    const text = (editing?.text || '').trim()
    if (!text) return
    try {
      await inspectionApi.editNote(r.id, noteId, text)
      toast.success('ویرایش ذخیره شد — متنِ اولیه هم نگه داشته شد')
      setEditing(null)
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }, [editing, load])

  const dropFile = useCallback(async (f: InspectionFile) => {
    if (!window.confirm(`«${f.filename}» از این برگه برداشته شود؟ (نسخهٔ درایو دست‌نخورده می‌ماند)`)) return
    try {
      await inspectionApi.removeFile(f.id)
      toast.success('برداشته شد')
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }, [load])

  // The owner reading their own sample back — the whole text, not one slice: a
  // human checking what the supervisor will see, and a partial view here would
  // be the same half-truth the reports used to tell.
  const openPeek = useCallback(async (f: InspectionFile) => {
    setPeek({ file: f, text: '', loading: true })
    try {
      let out = ''
      let offset = 0
      for (let guard = 0; guard < 400; guard++) {
        const got = await inspectionApi.fileText(f.id, offset)
        out += got.text
        if (!got.has_more || got.next_offset === null) break
        offset = got.next_offset
      }
      setPeek({ file: f, text: out, loading: false })
    } catch (e) {
      toast.error(parseApiError(e))
      setPeek(null)
    }
  }, [])

  // v155 — WATCH THE FAST QUEUE, and say what happened.
  //
  // «بعدشم رفرش کنه و پیام بیاد تو صفحه فلان چیز انجام شده تا بعد از رفرش خودکار
  // بتونم ببینمش». Polling only while something is actually pending: an idle
  // page must not poll forever, and a page with nothing rushed has nothing to
  // wait for. The banner names the sheet, because «something was done» is not an
  // answer to «what happened».
  const watching = useMemo(
    () => reports.filter((r) => r.urgent).map((r) => r.id).join(','), [reports])
  const seen = useRef<Record<string, string>>({})
  const [done, setDone] = useState<{ number: number; title: string; label: string }[]>([])

  useEffect(() => {
    // remember the state of each rushed sheet, so a CHANGE can be recognised
    for (const r of reports) {
      if (r.urgent || r.urgent_done_at) seen.current[r.id] = `${r.status}|${r.notes?.length || 0}`
    }
  }, [reports])

  useEffect(() => {
    if (!watching) return
    let alive = true
    const tick = async () => {
      try {
        const d = await inspectionApi.list({ include_filed: true, status: filter || undefined })
        if (!alive) return
        const changed: { number: number; title: string; label: string }[] = []
        for (const r of d.reports) {
          const before = seen.current[r.id]
          const now = `${r.status}|${r.notes?.length || 0}`
          if (before && before !== now && (r.urgent_done_at || r.status === 'answered')) {
            changed.push({ number: r.number, title: r.title || '', label: r.glow?.label || r.status })
          }
          seen.current[r.id] = now
        }
        setReports(d.reports)
        setCounts(d.counts || {})
        if (changed.length) setDone((prev) => [...changed, ...prev].slice(0, 5))
      } catch { /* signed out or offline — the next tick tries again */ }
    }
    const t = window.setInterval(tick, 20_000)
    const onFocus = () => void tick()
    window.addEventListener('focus', onFocus)
    return () => {
      alive = false
      window.clearInterval(t)
      window.removeEventListener('focus', onFocus)
    }
  }, [watching, filter])

  const summary = useMemo(() => ({
    open: counts.open || 0, answered: counts.answered || 0,
    approved: counts.approved || 0, filed: counts.filed || 0,
  }), [counts])

  return (
    <Layout>
      <div dir="rtl" className="space-y-4">
        {/* v155 — what happened while you were looking at this page. */}
        {!!done.length && (
          <div dir="rtl" className="rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-3">
            <div className="flex items-start gap-2">
              <span className="text-lg leading-none">⚡</span>
              <div className="flex-1 text-[13px] text-emerald-900">
                <div className="font-semibold">ناظر روی موردهای فوری کار کرد:</div>
                <ul className="mt-1 space-y-0.5">
                  {done.map((d) => (
                    <li key={d.number}>
                      گزارشِ {fa(d.number)}{d.title ? ` — ${d.title}` : ''}
                      <span className="text-emerald-700"> · {d.label}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-1 text-[11px] text-emerald-700">
                  صفحه خودش به‌روز شد — بازش کن و ببین.
                </div>
              </div>
              <button onClick={() => setDone([])} title="بستن"
                className="rounded p-1 text-emerald-700 hover:bg-emerald-100">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">نظارت و سرکشی</h1>
            <p className="text-sm text-gray-500 mt-1">
              ایراد و پیشنهادی که خودت روی صفحه‌ها ثبت کرده‌ای، و آنچه ناظر زیرش نوشته.
              برای ثبتِ گزارشِ تازه، دکمهٔ 📝 بالای صفحه را روشن کن و دورِ همان چیز کادر بکش.
            </p>
          </div>
          <button onClick={load} disabled={busy}
            className="flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-60">
            <RefreshCw size={14} className={busy ? 'animate-spin' : ''} /> تازه‌سازی
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {([['open', 'در انتظارِ ناظر', 'border-amber-200 bg-amber-50 text-amber-800'],
             ['answered', 'ناظر پاسخ داد', 'border-emerald-200 bg-emerald-50 text-emerald-800'],
             ['approved', 'تأییدِ تو', 'border-blue-200 bg-blue-50 text-blue-800'],
             ['filed', 'بایگانی', 'border-gray-200 bg-gray-50 text-gray-700']] as const).map(([k, label, cls]) => (
            <div key={k} className={`rounded-xl border p-3 text-center ${cls}`}>
              <div className="text-2xl font-bold">{fa((summary as any)[k])}</div>
              <div className="text-[11px]">{label}</div>
            </div>
          ))}
        </div>

        <div className="flex gap-2 flex-wrap">
          {FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)}
              className={`rounded-lg px-3 py-1 text-xs ${filter === f.key
                ? 'bg-gray-900 text-white' : 'border border-gray-300 text-gray-600 hover:bg-gray-50'}`}>
              {f.label}
            </button>
          ))}
        </div>

        {!reports.length && (
          <div className="rounded-xl border border-dashed border-gray-300 p-10 text-center text-sm text-gray-500">
            هنوز گزارشی ثبت نشده. دکمهٔ 📝 بالای صفحه را روشن کن، برو هر جای برنامه که ایراد دیدی،
            و دورش کادر بکش.
          </div>
        )}

        <div className="space-y-3">
          {reports.map((r) => {
            const expanded = openId === r.id
            const lastReviewer = [...(r.notes || [])].reverse().find((n) => n.by === 'reviewer')
            return (
              <div key={r.id} className="rounded-xl border border-gray-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`rounded px-2 py-[2px] text-[11px] text-white ${TONE[r.glow?.tone] || 'bg-gray-500'}`}>
                        {r.glow?.label}
                      </span>
                      <span className="text-sm font-semibold text-gray-900">
                        گزارشِ {fa(r.number)} — {r.title}
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] text-gray-500">
                      {r.page_label}{r.section_label ? ` ← ${r.section_label}` : ''}
                      {' · '}
                      <a href={r.page} className="inline-flex items-center gap-0.5 text-blue-600 hover:underline">
                        رفتن به همان‌جا <ExternalLink size={10} />
                      </a>
                      {r.binder && <> · زونکنِ {fa(r.binder.number)}، برگهٔ {fa(r.binder.page)}</>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {/* v155 — «همین الان». The supervisor's round is twice a
                        week; this puts one sheet in a queue that is checked
                        hourly, in the order the owner pressed them. */}
                    {r.status !== 'filed' && r.status !== 'approved' && (
                      <button onClick={() => void rush(r)}
                        title={r.urgent
                          ? 'در صفِ فوری است — برای بیرون‌آوردن بزن'
                          : 'ناظر خارج از نوبت سراغش برود'}
                        className={`rounded-lg px-2.5 py-1 text-xs ${r.urgent
                          ? 'bg-orange-600 text-white hover:bg-orange-700'
                          : 'border border-orange-300 text-orange-700 hover:bg-orange-50'}`}>
                        {r.urgent
                          ? (r.urgent_in_progress ? '⚡ در دستِ ناظر' : '⚡ در صفِ فوری')
                          : '⚡ فوری'}
                      </button>
                    )}
                    {!!r.urgent_done_at && !r.urgent && (
                      <span className="rounded-lg bg-emerald-50 px-2 py-1 text-[11px] text-emerald-700"
                        title="چیزی که فوری خواسته بودی، جواب گرفت">
                        ⚡ جواب گرفت
                      </span>
                    )}
                    <button onClick={() => setOpenId(expanded ? null : r.id)}
                      className="rounded-lg border border-gray-300 px-2.5 py-1 text-xs hover:bg-gray-50">
                      {expanded ? 'بستن' : 'جزئیات'}
                    </button>
                    {r.status !== 'filed' && (
                      <button onClick={() => approve(r)} title="تأیید — فقط دستِ توست"
                        className={`rounded-lg px-2.5 py-1 text-xs ${r.status === 'approved'
                          ? 'bg-blue-600 text-white' : 'border border-blue-300 text-blue-700 hover:bg-blue-50'}`}>
                        <Check size={12} className="inline" /> {r.status === 'approved' ? 'تأییدشده' : 'تأیید'}
                      </button>
                    )}
                    <button onClick={() => remove(r)} title="حذف"
                      className="rounded-lg border border-red-200 px-2 py-1 text-xs text-red-600 hover:bg-red-50">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>

                {!expanded && lastReviewer && (
                  <div className="mt-2 line-clamp-2 rounded-lg bg-gray-50 p-2 text-[12px] text-gray-700">
                    {lastReviewer.text}
                  </div>
                )}

                {expanded && (
                  <div className="mt-3 space-y-3 border-t border-gray-100 pt-3">
                    <div className="rounded-lg bg-gray-50 p-2 text-[11px] text-gray-600">
                      <div><b>نشانیِ دقیق:</b> <span dir="ltr">{r.reopen}</span></div>
                      {/* v150 — the precise measurement, so the supervisor knows
                          WHICH control the owner meant, not just which page. */}
                      {!!r.geometry && (
                        <>
                          <div><b>مختصات و ابعاد:</b> {geometryLabel(r.geometry)}</div>
                          <div>
                            <b>گره:</b>{' '}
                            {r.geometry.anchor.path
                              ? (<span dir="ltr" className="text-[11px]">{r.geometry.anchor.path}</span>)
                              : 'به عنصری گره نخورد — فقط مختصاتِ سند'}
                          </div>
                        </>
                      )}
                      {!!r.dom_path && <div dir="ltr" className="mt-0.5 text-gray-500">{r.dom_path}</div>}
                      {!!r.covered_text && <div className="mt-1">آنچه در کادر بود: {r.covered_text}</div>}
                    </div>

                    {r.notes?.map((n) => (
                      <div key={n.id} className={`rounded-lg border p-2.5 ${n.by === 'reviewer'
                        ? 'border-emerald-200 bg-emerald-50/50' : 'border-amber-200 bg-amber-50/50'}`}>
                        <div className="mb-1 flex items-center gap-2 text-[11px]">
                          <b>{n.by === 'reviewer' ? '🤖 ناظر' : '👤 تو'}</b>
                          <span className="text-gray-400">{new Date(n.at).toLocaleString('fa-IR')}</span>
                          {n.outcome && (
                            <span className={`rounded px-1.5 text-[10px] text-white ${TONE[n.outcome] || 'bg-gray-500'}`}>
                              {n.outcome}
                            </span>
                          )}
                          {/* v152 — edit in place. Only your own side, and never
                              on a filed sheet; the original is kept either way. */}
                          {n.by === 'owner' && r.status !== 'filed' && editing?.noteId !== n.id && (
                            <button type="button" title="ویرایشِ همین متن"
                              onClick={() => setEditing({ noteId: n.id, text: n.text })}
                              className="text-gray-500 hover:text-gray-800">
                              <Pencil size={12} />
                            </button>
                          )}
                          {!!n.edited_at && (
                            <span className="text-[10px] text-gray-400"
                              title={n.original_text ? `متنِ اول: ${n.original_text}` : ''}>
                              ویرایش شد
                            </span>
                          )}
                        </div>
                        {editing?.noteId === n.id ? (
                          <div>
                            <textarea
                              value={editing.text} rows={4} autoFocus
                              onChange={(e) => setEditing({ noteId: n.id, text: e.target.value })}
                              className="w-full rounded-lg border border-gray-300 p-2 text-[12.5px]" />
                            <div className="mt-1 flex items-center gap-2 flex-wrap">
                              <button type="button" disabled={!editing.text.trim()}
                                onClick={() => void saveEdit(r, n.id)}
                                className="rounded-lg bg-gray-900 px-3 py-1 text-xs text-white disabled:opacity-50">
                                ذخیرهٔ ویرایش
                              </button>
                              {/* v153 — attaching belongs to EDITING the report, not to
                                  writing a follow-up. The owner went looking for it here
                                  and found only a text box: «ویرایش می‌زنم نمی‌شه که فایل
                                  پیوست کرد … فقط می‌شه در ادامه گزارشِ قبلی گزارش جدید ثبت
                                  کرد». The files always belonged to the SHEET; only the
                                  control was in the wrong place. */}
                              <label className="cursor-pointer rounded-lg border border-dashed border-sky-300 px-2.5 py-1 text-xs text-sky-800 hover:bg-sky-50">
                                <Paperclip className="inline h-3 w-3 ml-1" />
                                پیوستِ فایل به همین گزارش
                                <input type="file" multiple className="hidden"
                                  onChange={(e) => {
                                    const list = Array.from(e.target.files || [])
                                    if (list.length) void attach(r, list)
                                    e.target.value = ''
                                  }} />
                              </label>
                              <button type="button" onClick={() => setEditing(null)}
                                className="px-2 py-1 text-xs text-gray-600 hover:underline">انصراف</button>
                              <span className="text-[10px] text-gray-400">
                                متنِ اولیه نگه داشته می‌شود
                              </span>
                            </div>
                            {upPct?.id === r.id && (
                              <div dir="rtl" className="mt-1 text-[11px] text-amber-800">
                                {upPct.name} — {fa(upPct.pct)}٪
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap text-[12.5px] text-gray-800">{n.text}</div>
                        )}
                        {!!n.commits?.length && (
                          <div dir="ltr" className="mt-1 text-[10px] text-gray-500">
                            {n.commits.join(' · ')}
                          </div>
                        )}
                        <div className="mt-2 flex gap-2 flex-wrap">
                          {n.shot_id && (
                            <figure className="max-w-xs">
                              <AuthedImage src={inspectionApi.shotUrl(n.shot_id)} alt="تصویرِ گزارش"
                                className="rounded border border-gray-300 max-w-full" />
                              <figcaption className="text-[10px] text-gray-500">چیزی که دیدی</figcaption>
                            </figure>
                          )}
                          {n.after_shot_id && (
                            <figure className="max-w-xs">
                              <AuthedImage src={inspectionApi.shotUrl(n.after_shot_id)} alt="تصویرِ بعد از اصلاح"
                                className="rounded border border-emerald-300 max-w-full" />
                              <figcaption className="text-[10px] text-emerald-700">بعد از کارِ ناظر</figcaption>
                            </figure>
                          )}
                        </div>
                      </div>
                    ))}

                    {/* v146 — the samples on this sheet, and whether the
                        supervisor has actually read them. The read state is
                        shown to the OWNER on purpose: «ناظر خواند یا نه» was
                        the thing they could not see before. */}
                    <div className="rounded-lg border border-sky-200 bg-sky-50/40 p-2.5">
                      <div className="mb-1.5 flex items-center gap-2 text-[11px] font-semibold text-sky-900">
                        <Paperclip className="h-3.5 w-3.5" />
                        فایل‌های نمونه {r.files?.length ? `(${fa(r.files.length)})` : ''}
                      </div>
                      {!r.files?.length && (
                        <div className="mb-1.5 text-[11px] text-gray-500">
                          فایلی پیوست نشده. هر نوع فایلی می‌شود — ورد، PDF، عکس، اکسل…
                        </div>
                      )}
                      <div className="space-y-1.5">
                        {(r.files || []).map((f) => (
                          <div key={f.id} dir="rtl"
                            className="rounded-md border border-sky-100 bg-white px-2 py-1.5 text-[11px]">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-gray-800 truncate max-w-[16rem]">{f.filename}</span>
                              <span className="text-gray-400">{f.size_label}</span>
                              {f.extract_status === 'ok' ? (
                                <span className={f.fully_read ? 'text-emerald-700' : 'text-amber-700'}>
                                  {f.fully_read
                                    ? '✓ ناظر کاملش را خواند'
                                    : `ناظر ${fa(f.read_percent ?? 0)}٪ خوانده`}
                                </span>
                              ) : (
                                <span className={f.viewed_at ? 'text-emerald-700' : 'text-amber-700'}>
                                  {f.viewed_at ? '✓ ناظر بازش کرد' : 'ناظر هنوز بازش نکرده'}
                                </span>
                              )}
                              {!f.durable && (
                                <span className="text-red-700" title={f.store_note}>
                                  ⚠ در درایو ذخیره نشد
                                </span>
                              )}
                              <span className="flex-1" />
                              {f.extract_status === 'ok' && (
                                <button type="button" onClick={() => void openPeek(f)}
                                  className="text-sky-700 hover:underline">متن</button>
                              )}
                              <AuthedDownload href={inspectionApi.fileUrl(f.id)} filename={f.filename}
                                className="text-sky-700 hover:underline">دانلود</AuthedDownload>
                              {!!f.drive_link && (
                                <a href={f.drive_link} target="_blank" rel="noreferrer"
                                  className="text-sky-700 hover:underline">درایو</a>
                              )}
                              {r.status !== 'filed' && (
                                <button type="button" onClick={() => void dropFile(f)}
                                  title="برداشتن" className="text-red-600 hover:underline">×</button>
                              )}
                            </div>
                            <div className="mt-0.5 text-gray-500">{f.extract_label}</div>
                            {!!f.extract_note && (
                              <div className="mt-0.5 text-gray-500">{f.extract_note}</div>
                            )}
                            {!!f.caption && (
                              <div className="mt-0.5 text-gray-700" dir="auto">توضیح: {f.caption}</div>
                            )}
                          </div>
                        ))}
                      </div>
                      {r.status !== 'filed' && (
                        <label className="mt-1.5 flex cursor-pointer items-center gap-1.5 text-[11px] text-sky-800 hover:underline">
                          <Paperclip className="h-3 w-3" />
                          <span>پیوست کردنِ فایلِ نمونه به همین گزارش (هر نوعی)</span>
                          <input type="file" multiple className="hidden"
                            onChange={(e) => {
                              const list = Array.from(e.target.files || [])
                              if (list.length) void attach(r, list)
                              e.target.value = ''
                            }} />
                        </label>
                      )}
                      {upPct?.id === r.id && (
                        <div className="mt-1 text-[11px] text-amber-800">
                          {upPct.name} — {fa(upPct.pct)}٪
                        </div>
                      )}
                      {!!r.read_debt?.length && (
                        <div className="mt-1.5 rounded-md bg-amber-100/70 px-2 py-1 text-[11px] text-amber-900">
                          ناظر تا این فایل‌ها را کامل نخواند نمی‌تواند برگه را جواب بدهد:{' '}
                          {r.read_debt.map((d) => d.filename).join(' · ')}
                        </div>
                      )}
                    </div>

                    {!!r.dependencies?.length && (
                      <div className="rounded-lg border border-purple-200 bg-purple-50/40 p-2.5">
                        <div className="mb-1 text-[11px] font-semibold text-purple-900">
                          وابستگی‌هایی که ناظر بررسی کرد
                        </div>
                        <ul className="space-y-0.5 text-[11.5px]">
                          {r.dependencies.map((d, i) => (
                            <li key={i} className="flex gap-1.5">
                              <span>{d.status === 'ok' ? '✅' : d.status === 'missing' ? '❌' : '⚠️'}</span>
                              <span className="text-gray-800" dir="auto">{d.name}</span>
                              {!!d.note && <span className="text-gray-500">— {d.note}</span>}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {r.status !== 'filed' && (
                      <div>
                        <textarea value={reply} onChange={(e) => setReply(e.target.value)} rows={2}
                          placeholder="یادداشتِ تازه — این متنِ گزارش را عوض نمی‌کند. برای اصلاحِ خودِ گزارش و پیوستِ فایل به آن، دکمهٔ ✏ کنارِ متنِ بالا را بزن."
                          className="w-full rounded-lg border border-gray-300 p-2 text-sm" />
                        <button onClick={() => addNote(r)} disabled={!reply.trim()}
                          className="mt-1 rounded-lg bg-gray-900 px-3 py-1.5 text-xs text-white disabled:opacity-50">
                          افزودن به همین برگه
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* v146 — reading a sample back. Whole text, in a scroll box: the owner
          checks what they actually handed over. */}
      {peek && (
        <div dir="rtl" className="fixed inset-0 z-[95] flex items-center justify-center bg-black/50 p-4"
          onClick={(e) => { if (e.target === e.currentTarget) setPeek(null) }}>
          <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-2xl">
            <div className="flex items-center gap-2 border-b border-gray-200 p-3">
              <Paperclip className="h-4 w-4 text-sky-700" />
              <span className="truncate text-sm font-bold text-gray-900">{peek.file.filename}</span>
              <span className="text-[11px] text-gray-500">{peek.file.size_label}</span>
              {peek.file.page_count > 0 && (
                <span className="text-[11px] text-gray-500">{fa(peek.file.page_count)} صفحه</span>
              )}
              <span className="flex-1" />
              <button onClick={() => setPeek(null)} className="rounded p-1 hover:bg-gray-100">
                <X className="h-4 w-4 text-gray-600" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-auto p-3">
              {peek.loading ? (
                <div className="text-sm text-gray-500">در حالِ خواندن…</div>
              ) : (
                <pre dir="auto" className="whitespace-pre-wrap break-words text-[12.5px] leading-6 text-gray-800">
                  {peek.text || '(متنی استخراج نشد)'}
                </pre>
              )}
            </div>
            <div className="border-t border-gray-200 p-2 text-[11px] text-gray-500">
              این همان متنی است که ناظر می‌خواند — تکه‌تکه، تا آخر.
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
