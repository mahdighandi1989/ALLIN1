'use client'
// v141 — «نظارت و سرکشی»: the whole board.
//
// Every sheet the owner filed, what the supervisor answered, the dependency walk
// behind that answer, and the tick. The colour of a sheet is DERIVED from the
// outcome, never from the fact that somebody replied — that distinction is the
// whole reason this page is trustworthy.
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { RefreshCw, Check, Trash2, ExternalLink } from 'lucide-react'
import { inspectionApi, parseApiError, type InspectionReport } from '@/lib/api'
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

  const summary = useMemo(() => ({
    open: counts.open || 0, answered: counts.answered || 0,
    approved: counts.approved || 0, filed: counts.filed || 0,
  }), [counts])

  return (
    <Layout>
      <div dir="rtl" className="space-y-4">
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
                        </div>
                        <div className="whitespace-pre-wrap text-[12.5px] text-gray-800">{n.text}</div>
                        {!!n.commits?.length && (
                          <div dir="ltr" className="mt-1 text-[10px] text-gray-500">
                            {n.commits.join(' · ')}
                          </div>
                        )}
                        <div className="mt-2 flex gap-2 flex-wrap">
                          {n.shot_id && (
                            <figure className="max-w-xs">
                              <img src={inspectionApi.shotUrl(n.shot_id)} alt="تصویرِ گزارش"
                                className="rounded border border-gray-300" />
                              <figcaption className="text-[10px] text-gray-500">چیزی که دیدی</figcaption>
                            </figure>
                          )}
                          {n.after_shot_id && (
                            <figure className="max-w-xs">
                              <img src={inspectionApi.shotUrl(n.after_shot_id)} alt="تصویرِ بعد از اصلاح"
                                className="rounded border border-emerald-300" />
                              <figcaption className="text-[10px] text-emerald-700">بعد از کارِ ناظر</figcaption>
                            </figure>
                          )}
                        </div>
                      </div>
                    ))}

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
                          placeholder="اگر دستور یا توضیحِ بیشتری داری بنویس — برگه دوباره در صفِ ناظر می‌رود"
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
    </Layout>
  )
}
