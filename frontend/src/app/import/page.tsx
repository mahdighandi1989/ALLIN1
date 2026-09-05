'use client'

// AI Document Import — upload one OR MANY PDF / image / Word files, pick an AI
// model (wired live from Settings; enable/route there), and let it extract each
// file and write every customer's data into the database. Files are analyzed
// one-by-one (so AI rate limits aren't hammered) and each is moved to Google
// Drive and linked under every customer it belongs to.
import React, { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { Upload, FileText, Loader2, CheckCircle2, AlertTriangle, ExternalLink, Cpu, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { importsApi, parseApiError } from '@/lib/api'

type Model = { id: number; display_name: string; capabilities: string[]; supports_pdf?: boolean }
type FileResult = { filename: string; ok: boolean; data?: any; error?: string; incapable?: any }

export default function ImportPage() {
  const [models, setModels] = useState<Model[]>([])
  const [driveEnabled, setDriveEnabled] = useState(false)
  const [modelId, setModelId] = useState<number | 'auto'>('auto')
  const [files, setFiles] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })
  const [results, setResults] = useState<FileResult[]>([])
  // v103 — optional operator instructions the extraction model MUST follow;
  // the per-file result then reports exactly what was done because of them.
  const [instructions, setInstructions] = useState('')
  // v118 — the v117 «Drive policy inbox» card was REMOVED from this page at the
  // owner's explicit request (2026-09-05: the one-off batch was handled outside
  // the app, and production Drive runs in OAuth mode where the app cannot see
  // user-dropped files). The backend /api/policy-inbox endpoints are kept,
  // quarantined — see docs/REMOVAL_CANDIDATES.md.

  useEffect(() => {
    importsApi.aiModels()
      .then((d) => { setModels(d.models || []); setDriveEnabled(!!d.drive_enabled) })
      .catch(() => {})
  }, [])

  const OK_EXT = /\.(pdf|png|jpe?g|webp|gif|tiff?|bmp|docx|xlsx|xlsm|xls|csv)$/i
  const addFiles = (fl?: FileList | File[] | null) => {
    if (!fl) return
    const arr = Array.from(fl).filter((f) => OK_EXT.test(f.name))
    if (arr.length === 0) { toast.error('فقط PDF، تصویر یا Word (.docx)'); return }
    if (arr.length !== Array.from(fl).length) toast('بعضی فایل‌ها نادیده گرفته شدند (فرمت نامعتبر)', { icon: '⚠️' })
    setFiles((prev) => [...prev, ...arr])
    setResults([])
  }
  const removeFile = (i: number) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== i))
    // Results are index-aligned with the file list; keep them in sync or the
    // remaining files show the wrong success/failure icons.
    setResults((prev) => (prev.length ? prev.filter((_, idx) => idx !== i) : prev))
  }

  const analyzeAll = async () => {
    if (!files.length) { toast.error('ابتدا فایل انتخاب کن'); return }
    setBusy(true); setResults([]); setProgress({ done: 0, total: files.length })
    const out: FileResult[] = []
    for (let i = 0; i < files.length; i++) {
      const f = files[i]
      try {
        const r = await importsApi.analyzeDocument(f, modelId === 'auto' ? undefined : modelId, undefined, instructions)
        out.push({ filename: f.name, ok: true, data: r })
      } catch (e: any) {
        const d = e?.response?.data?.detail
        if (d && typeof d === 'object' && d.error === 'model_incapable') out.push({ filename: f.name, ok: false, incapable: d })
        else out.push({ filename: f.name, ok: false, error: parseApiError(e) })
      }
      setProgress({ done: i + 1, total: files.length })
      setResults([...out])
    }
    setBusy(false)
    const okN = out.filter((x) => x.ok).length
    if (okN) toast.success(`${okN} از ${files.length} فایل تحلیل و ثبت شد`)
    else toast.error('هیچ فایلی با موفقیت تحلیل نشد')
    // v103 review finding (major): a document-specific instruction (e.g. an
    // account number) must never silently ride into the NEXT batch — clear the
    // box once a batch that used it succeeds. On full failure it stays for the
    // retry. (Cleared here, NOT in addFiles: a note typed between adding file 1
    // and file 2 of the same batch must survive.)
    if (okN && instructions.trim()) {
      setInstructions('')
      toast('دستورِ متنی روی این دسته اعمال شد و برای دستهٔ بعدی پاک شد — گزارشش زیر هر فایل آمده است.', { icon: '🧭' })
    }
  }

  const sel = 'border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      <div dir="rtl" className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><FileText size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ایمپورتِ هوشمندِ اسناد</h1>
            <p className="text-gray-500 text-sm">یک یا چند فایلِ PDF / تصویر / Word / Excel را بارگذاری کن؛ مدلِ هوش‌مصنوعی هر فایل را استخراج و در دیتابیسِ مشتری ثبت می‌کند و فایل‌ها به Google Drive منتقل و در پروفایلِ مشتری لینک می‌شوند.</p>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 mt-5 space-y-4">
          {/* Model picker — wired from Settings */}
          <div className="flex flex-wrap items-end gap-3">
            <label className="flex-1 min-w-[220px]">
              <span className="text-[12px] text-gray-600 flex items-center gap-1"><Cpu size={13} /> مدلِ تحلیل (از تنظیمات)</span>
              <select value={modelId} onChange={(e) => setModelId(e.target.value === 'auto' ? 'auto' : Number(e.target.value))} className={sel + ' w-full mt-1'}>
                <option value="auto">خودکار (بهترین مدلِ فعال)</option>
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.display_name}{m.supports_pdf ? ' · PDF✓' : ' · فقط تصویر'}</option>
                ))}
              </select>
            </label>
            <div className="text-[11px] text-gray-400 pb-2">
              فعال/غیرفعال و مسیریابیِ مدل‌ها فقط در «تنظیمات».
              {driveEnabled ? ' · Drive متصل است' : ' · Drive متصل نیست'}
            </div>
          </div>

          {/* Drop zone (multiple) */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files) }}
            className={`rounded-xl border-2 border-dashed p-6 text-center transition-colors ${dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}`}
          >
            <input id="docfile" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.tiff,.tif,.bmp,.docx,.xlsx,.xlsm,.xls,.csv" className="hidden"
              onChange={(e) => { addFiles(e.target.files); e.currentTarget.value = '' }} />
            <Upload size={24} className="mx-auto text-blue-600 mb-2" />
            <div className="text-sm text-gray-700">
              <label htmlFor="docfile" className="text-blue-700 font-semibold cursor-pointer hover:underline">انتخاب چند فایل</label>
              {' '}یا بکش و رها کن — PDF، تصویر، Word یا Excel
            </div>
          </div>

          {/* Selected files list */}
          {files.length > 0 && (
            <div className="border border-gray-200 rounded-lg divide-y">
              {files.map((f, i) => {
                const r = results[i]
                return (
                  <div key={i} className="flex items-center gap-2 px-3 py-2 text-sm">
                    <span className="text-gray-400">{i + 1}.</span>
                    <span className="flex-1 truncate">📎 {f.name} <span className="text-gray-400">({Math.round(f.size / 1024)} KB)</span></span>
                    {busy && progress.done === i && !r && <Loader2 size={14} className="animate-spin text-blue-600" />}
                    {r?.ok && <CheckCircle2 size={14} className="text-green-600" />}
                    {r && !r.ok && <AlertTriangle size={14} className="text-amber-500" />}
                    {!busy && <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-600"><X size={14} /></button>}
                  </div>
                )
              })}
            </div>
          )}

          {/* v103 — operator instructions for the extraction model (optional) */}
          <label className="block">
            <span className="text-[12px] text-gray-600 font-semibold">دستور / توضیح برای مدلِ استخراج‌گر (اختیاری)</span>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={3}
              maxLength={6000}
              className="w-full mt-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
              placeholder="مثلاً: «شمارهٔ حسابِ این مدارک 271520 است»، «فقط بخشِ ضامن‌ها را استخراج کن»، «نامِ شرکت را Alpha Trading LLC ثبت کن»، یا هر دستور/تکمیلِ دیگری…"
            />
            <span className="text-[11px] text-gray-400">مدل موظف است دقیقاً طبقِ این نوشته عمل کند و بعد از استخراج گزارش می‌دهد که بر اساسِ آن چه کرده است.</span>
          </label>

          <button onClick={analyzeAll} disabled={busy || !files.length}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-lg px-4 py-2.5 text-sm font-semibold">
            {busy
              ? <><Loader2 size={16} className="animate-spin" /> در حال تحلیل… ({progress.done}/{progress.total})</>
              : <><Cpu size={16} /> تحلیل و ثبت در دیتابیس{files.length > 1 ? ` (${files.length} فایل)` : ''}</>}
          </button>

          {/* Per-file results */}
          {results.length > 0 && results.map((r, i) => (
            <div key={i} className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
              <div className="font-semibold text-gray-800 flex items-center gap-2 mb-1">
                {r.ok ? <CheckCircle2 size={15} className="text-green-600" /> : <AlertTriangle size={15} className="text-amber-500" />}
                {r.filename}
                {r.ok && r.data?.drive?.stored && <a href={r.data.drive.link} target="_blank" rel="noreferrer" className="mr-auto inline-flex items-center gap-1 text-blue-700 hover:underline text-xs">Drive <ExternalLink size={11} /></a>}
              </div>

              {/* v103 — what the model did because of the operator's instructions */}
              {r.ok && r.data?.instructions_used && (
                <div className="mb-1 rounded-lg border border-indigo-200 bg-indigo-50 p-2">
                  <div className="text-[12px] font-bold text-indigo-800">🧭 گزارشِ اجرای دستورِ شما</div>
                  <div className="text-[12px] text-indigo-900 whitespace-pre-wrap leading-5">{r.data.instruction_report || '—'}</div>
                </div>
              )}
              {/* v114 — loud coverage warning: a partial extraction must never look complete */}
              {r.ok && ((r.data?.chunks_failed || 0) > 0 || (r.data?.chunk_errors || []).length > 0) && (
                <div className="mb-1 rounded-lg border border-amber-300 bg-amber-50 p-2">
                  <div className="text-[12px] font-bold text-amber-800">
                    ⚠️ استخراج ناقص بود — {r.data?.chunks_failed || (r.data?.chunk_errors || []).length} بخش از {r.data?.chunks_total || '؟'} بخشِ فایل خوانده نشد
                  </div>
                  {(r.data?.failed_pages || []).length > 0 && (
                    <div className="text-[11px] text-amber-800">بخش‌های شروع‌شده از صفحه‌های: {(r.data.failed_pages as number[]).join('، ')}</div>
                  )}
                  <div className="text-[11px] text-amber-700">همین فایل را دوباره تحلیل کن تا بخش‌های جامانده هم استخراج شود؛ داده‌های قبلاً ثبت‌شده تکراری نمی‌شوند.</div>
                  {(r.data?.chunk_errors || []).length > 0 && (
                    <details className="mt-1">
                      <summary className="text-[11px] text-amber-700 cursor-pointer select-none">جزئیاتِ خطاها</summary>
                      <div className="text-[10px] text-amber-800 whitespace-pre-wrap leading-4">{(r.data.chunk_errors as string[]).join('\n')}</div>
                    </details>
                  )}
                </div>
              )}
              {r.incapable && (
                <div className="text-xs text-amber-800">
                  {r.incapable.message || `«${r.incapable.model}» از پسِ این فایل برنمی‌آید.`}
                  {(r.incapable.suggestions || []).length > 0 && (
                    <span> پیشنهاد: {r.incapable.suggestions.map((s: any) => (
                      <button key={s.id} className="text-blue-700 hover:underline mx-1" onClick={() => setModelId(s.id)}>{s.display_name}</button>
                    ))} — سپس دوباره «تحلیل» بزن.</span>
                  )}
                </div>
              )}
              {r.error && <div className="text-xs text-red-700">خطا: {r.error}</div>}

              {r.ok && (r.data?.customers || []).map((c: any, j: number) => (
                <div key={j} className={`rounded border p-2 mt-1 ${c.ok ? 'border-green-200 bg-white' : 'border-red-200 bg-red-50'}`}>
                  {c.ok ? (
                    <div>
                      <div className="font-medium text-gray-900">{c.name} <span className="text-gray-400 font-normal">· {c.account_no}</span></div>
                      {c.match_basis && <div className="text-[11px] text-blue-700">🔗 بدون شمارهٔ حساب در سند — {c.match_basis}</div>}
                      <div className="text-xs text-gray-600">
                        {c.fields_saved?.length ? `${c.fields_saved.length} فیلد` : 'بدون فیلدِ جدید'}
                        {c.guarantors_added ? ` · ${c.guarantors_added} ضامن جدید` : ''}
                        {c.partners_added ? ` · ${c.partners_added} شریک جدید` : ''}
                        {c.facilities_added ? ` · ${c.facilities_added} تسهیلات جدید` : ''}
                        {c.properties_added ? ` · ${c.properties_added} ملک جدید` : ''}
                        {c.properties_updated ? ` · ${c.properties_updated} ملک به‌روز` : ''}
                      </div>
                      {c.fields_saved?.length > 0 && (
                        <details className="mt-1">
                          <summary className="text-[11px] text-blue-600 cursor-pointer select-none">فیلدهای استخراج‌شده از فایل ({c.fields_saved.length}) — برای دیدن باز کن</summary>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {c.fields_saved.map((f: string) => (
                              <span key={f} className="text-[10px] bg-gray-100 text-gray-700 rounded px-1.5 py-0.5">{f}</span>
                            ))}
                          </div>
                        </details>
                      )}
                      {c.kyc_missing?.length > 0 && (
                        <div className="mt-1 text-[11px] text-amber-700">
                          در این فایل یافت نشد: {c.kyc_missing.join('، ')}
                        </div>
                      )}
                    </div>
                  ) : <div className="text-red-700 text-xs">ثبت نشد: {c.reason}</div>}
                </div>
              ))}
              {r.ok && (r.data?.documents || []).length > 0 && (
                <div className="mt-1 text-xs text-gray-500">
                  {r.data.documents.map((d: any, k: number) => (
                    <span key={k} className="mr-3">📄 ص {d.pages}: <b>{d.type}</b>{d.customer_account ? ` (${d.customer_account})` : ''}</span>
                  ))}
                </div>
              )}
              {r.ok && r.data?.kb && (r.data.kb.added > 0 || r.data.kb.duplicates > 0) && (
                <div className="mt-1 text-xs text-purple-700">
                  📚 دانشنامه: {r.data.kb.added > 0 ? `${r.data.kb.added} مطلب جدید` : 'مطلب جدیدی نداشت'}
                  {r.data.kb.topics_created > 0 ? ` (${r.data.kb.topics_created} سرفصل جدید)` : ''}
                  {r.data.kb.duplicates > 0 ? ` — ${r.data.kb.duplicates} مورد تکراری ثبت نشد` : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  )
}
