'use client'

// AI Document Import — upload a PDF / image / Word file, pick an AI model
// (wired live from Settings; enable/route there), and let it extract the
// content and write each customer's data into the database. The file itself is
// moved to Google Drive and linked under every customer it belongs to.
import React, { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { Upload, FileText, Loader2, CheckCircle2, AlertTriangle, ExternalLink, Cpu } from 'lucide-react'
import toast from 'react-hot-toast'
import { importsApi, parseApiError } from '@/lib/api'

type Model = { id: number; display_name: string; capabilities: string[]; supports_pdf?: boolean; provider_key?: string }

export default function ImportPage() {
  const [models, setModels] = useState<Model[]>([])
  const [driveEnabled, setDriveEnabled] = useState(false)
  const [modelId, setModelId] = useState<number | 'auto'>('auto')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [incapable, setIncapable] = useState<any>(null)

  useEffect(() => {
    importsApi.aiModels()
      .then((d) => { setModels(d.models || []); setDriveEnabled(!!d.drive_enabled) })
      .catch(() => {})
  }, [])

  const pick = (f?: File | null) => {
    if (!f) return
    if (!/\.(pdf|png|jpe?g|webp|gif|tiff?|bmp|docx)$/i.test(f.name)) {
      toast.error('فقط PDF، تصویر یا Word (.docx)')
      return
    }
    setFile(f); setResult(null); setIncapable(null)
  }

  const analyze = async () => {
    if (!file) { toast.error('ابتدا یک فایل انتخاب کن'); return }
    setBusy(true); setResult(null); setIncapable(null)
    try {
      const r = await importsApi.analyzeDocument(file, modelId === 'auto' ? undefined : modelId)
      setResult(r)
      const n = (r.customers || []).filter((c: any) => c.ok).length
      toast.success(`استخراج شد — ${n} مشتری ثبت/به‌روزرسانی شد`)
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      if (detail && typeof detail === 'object' && detail.error === 'model_incapable') {
        setIncapable(detail)
      } else {
        toast.error(parseApiError(e))
      }
    } finally { setBusy(false) }
  }

  const sel = 'border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

  return (
    <Layout>
      <div dir="rtl" className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><FileText size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ایمپورتِ هوشمندِ اسناد</h1>
            <p className="text-gray-500 text-sm">PDF / تصویر / Word را بارگذاری کن؛ مدلِ هوش‌مصنوعی محتوا را استخراج و در دیتابیسِ مشتری ثبت می‌کند و فایل به Google Drive منتقل و در پروفایلِ مشتری لینک می‌شود.</p>
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
              فعال/غیرفعال و مسیریابیِ مدل‌ها فقط در «تنظیمات» انجام می‌شود.
              {driveEnabled ? ' · Drive متصل است' : ' · Drive متصل نیست (فایل فقط استخراج می‌شود)'}
            </div>
          </div>

          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); pick(e.dataTransfer.files?.[0]) }}
            className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'}`}
          >
            <input id="docfile" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.tiff,.tif,.bmp,.docx" className="hidden"
              onChange={(e) => { pick(e.target.files?.[0]); e.currentTarget.value = '' }} />
            <Upload size={26} className="mx-auto text-blue-600 mb-2" />
            <div className="text-sm text-gray-700">
              <label htmlFor="docfile" className="text-blue-700 font-semibold cursor-pointer hover:underline">انتخاب فایل</label>
              {' '}یا بکش و رها کن — PDF، تصویر، یا Word
            </div>
            {file && <div className="mt-2 text-sm font-medium text-gray-900">📎 {file.name} <span className="text-gray-400">({Math.round(file.size / 1024)} KB)</span></div>}
          </div>

          <button onClick={analyze} disabled={busy || !file}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-lg px-4 py-2.5 text-sm font-semibold">
            {busy ? <><Loader2 size={16} className="animate-spin" /> در حال تحلیل و استخراج…</> : <><Cpu size={16} /> تحلیل و ثبت در دیتابیس</>}
          </button>

          {/* Model-incapable → ordered suggestions of currently-active models */}
          {incapable && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm">
              <div className="flex items-center gap-2 text-amber-800 font-semibold"><AlertTriangle size={15} /> {incapable.message || `«${incapable.model}» از پسِ این فایل برنمی‌آید.`}</div>
              {(incapable.suggestions || []).length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {incapable.suggestions.map((s: any) => (
                    <li key={s.id}>
                      <button className="text-blue-700 hover:underline" onClick={() => { setModelId(s.id); setIncapable(null) }}>
                        ▸ {s.display_name}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : <div className="mt-1 text-amber-700 text-xs">هیچ مدلِ سند/تصویرخوانِ فعالِ دیگری در تنظیمات نیست.</div>}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 space-y-3 text-sm">
              <div className="flex items-center gap-2 text-gray-700">
                <CheckCircle2 size={15} className="text-green-600" /> با مدلِ <b>{result.model}</b>
                {result.multi_customer && <span className="text-xs bg-blue-100 text-blue-700 rounded px-1.5 py-0.5">چند مشتری</span>}
                {result.drive?.stored
                  ? <a href={result.drive.link} target="_blank" rel="noreferrer" className="mr-auto inline-flex items-center gap-1 text-blue-700 hover:underline">فایل در Drive <ExternalLink size={12} /></a>
                  : <span className="mr-auto text-xs text-gray-400">{result.drive?.skipped ? 'Drive غیرفعال' : 'در Drive ذخیره نشد'}</span>}
              </div>
              {(result.customers || []).map((c: any, i: number) => (
                <div key={i} className={`rounded border p-2 ${c.ok ? 'border-green-200 bg-white' : 'border-red-200 bg-red-50'}`}>
                  {c.ok ? (
                    <div>
                      <div className="font-semibold text-gray-900">{c.name} <span className="text-gray-400 font-normal">· {c.account_no}</span></div>
                      <div className="text-xs text-gray-600 mt-0.5">
                        {c.fields_saved?.length ? `${c.fields_saved.length} فیلد` : 'بدون فیلدِ جدید'}
                        {c.guarantors_added ? ` · ${c.guarantors_added} ضامن جدید` : ''}
                        {c.guarantors_updated ? ` · ${c.guarantors_updated} ضامن به‌روز` : ''}
                      </div>
                    </div>
                  ) : <div className="text-red-700 text-xs">ثبت نشد: {c.reason}</div>}
                </div>
              ))}
              {(result.documents || []).length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-500 mb-1">نقشهٔ صفحات → مستندات:</div>
                  <ul className="text-xs text-gray-600 space-y-0.5">
                    {result.documents.map((d: any, i: number) => (
                      <li key={i}>• صفحهٔ {d.pages}: <b>{d.type}</b>{d.customer_account ? ` (حساب ${d.customer_account})` : ''}{d.summary ? ` — ${d.summary}` : ''}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
