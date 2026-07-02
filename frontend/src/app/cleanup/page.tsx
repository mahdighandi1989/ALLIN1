'use client'

/**
 * Database Cleanup (de-duplication) — admin, REVIEW FIRST.
 *
 * Scan → review the proposed removals → Apply (soft-delete, reversible via the
 * Recycle Bin, logged per customer). A configurable schedule runs the same scan
 * automatically and notifies admins; it never auto-deletes. An optional AI
 * «second opinion» flags near-duplicates the deterministic rules did not merge.
 */
import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/lib/auth'
import {
  cleanupApi, parseApiError,
  type CleanupReport, type CleanupConfig, type CleanupRun, type CleanupAIReview,
} from '@/lib/api'
import {
  Sparkles, ScanSearch, Trash2, CalendarClock, Bot, History as HistoryIcon,
  AlertTriangle, ShieldCheck, RefreshCw, Building2, Users, Landmark, PiggyBank,
} from 'lucide-react'
import toast from 'react-hot-toast'

// Entity metadata (label in Persian to match the backend report + app content).
const ENTITY_META: Record<string, { label: string; Icon: any; color: string }> = {
  properties: { label: 'املاک مرهونه', Icon: Building2, color: 'text-blue-600' },
  guarantors: { label: 'ضامن‌ها', Icon: ShieldCheck, color: 'text-green-600' },
  fixed_deposits: { label: 'سپرده‌های ثابت', Icon: PiggyBank, color: 'text-purple-600' },
  partners: { label: 'شرکا', Icon: Users, color: 'text-amber-600' },
}

const SCHEDULE_LABEL: Record<string, string> = {
  off: 'خاموش', daily: 'روزانه', weekly: 'هفتگی', monthly: 'ماهانه',
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('fa-IR')
  } catch {
    return iso
  }
}

export default function CleanupPage() {
  const { user, authDisabled } = useAuth()
  const isAdmin = authDisabled || !!user?.is_admin || user?.role === 'admin'

  const [report, setReport] = useState<CleanupReport | null>(null)
  const [scanning, setScanning] = useState(false)
  const [applying, setApplying] = useState(false)

  const [config, setConfig] = useState<CleanupConfig | null>(null)
  const [savingCfg, setSavingCfg] = useState(false)

  const [ai, setAi] = useState<CleanupAIReview | null>(null)
  const [aiLoading, setAiLoading] = useState(false)

  const [history, setHistory] = useState<CleanupRun[]>([])

  const loadConfig = async () => {
    try { setConfig(await cleanupApi.getConfig()) } catch (e) { toast.error(parseApiError(e)) }
  }
  const loadHistory = async () => {
    try { setHistory((await cleanupApi.history()).runs) } catch { /* non-critical */ }
  }

  useEffect(() => {
    if (!isAdmin) return
    loadConfig()
    loadHistory()
  }, [isAdmin])

  const runScan = async () => {
    try {
      setScanning(true)
      const r = await cleanupApi.scan()
      setReport(r)
      const t = r.counts.total_removals || 0
      toast.success(t ? `${t} رکوردِ تکراری پیدا شد` : 'موردِ تکراری پیدا نشد')
      loadHistory()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setScanning(false)
    }
  }

  const applyRemovals = async (only?: string[]) => {
    const total = report?.counts.total_removals || 0
    if (!total) return
    const scope = only && only.length ? ENTITY_META[only[0]]?.label || only[0] : 'همهٔ موارد'
    if (!window.confirm(
      `حذفِ رکوردهای تکراری (${scope})؟\n\n` +
      'رکوردها به‌صورت نرم حذف می‌شوند (قابل بازیابی از «سطل بازیافت») و هر حذف ' +
      'در تبِ لاگِ همان مشتری ثبت می‌گردد.'
    )) return
    try {
      setApplying(true)
      const res = await cleanupApi.apply(only)
      toast.success(`${res.removed.total || 0} رکورد حذف شد`)
      await runScan()          // refresh the report (now shows what remains)
      loadHistory()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setApplying(false)
    }
  }

  const saveConfig = async (patch: { schedule?: string; ai_review?: string }) => {
    try {
      setSavingCfg(true)
      setConfig(await cleanupApi.updateConfig(patch))
      toast.success('تنظیمات ذخیره شد')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSavingCfg(false)
    }
  }

  const runAiReview = async () => {
    try {
      setAiLoading(true)
      const r = await cleanupApi.aiReview()
      setAi(r)
      if (!r.available) toast(r.note || 'هوش مصنوعی در دسترس نیست', { icon: 'ℹ️' })
      else toast.success(`${r.suggestions?.length || 0} پیشنهاد از هوش مصنوعی`)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setAiLoading(false)
    }
  }

  if (!isAdmin) {
    return (
      <Layout>
        <div className="py-16 text-center text-gray-500">
          این صفحه فقط برای مدیران در دسترس است.
        </div>
      </Layout>
    )
  }

  const counts = report?.counts || {}
  const entityKeys = ['properties', 'guarantors', 'fixed_deposits', 'partners']
  const facReview = report?.review?.facilities || []

  return (
    <Layout>
      {/* Header + primary actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <Sparkles size={22} className="text-indigo-600" />
          <h2 className="text-2xl font-bold">Database Cleanup</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={runScan}
            disabled={scanning}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            {scanning ? <RefreshCw size={16} className="animate-spin" /> : <ScanSearch size={16} />}
            اسکنِ دیتابیس
          </button>
          <button
            type="button"
            onClick={() => applyRemovals()}
            disabled={applying || !(counts.total_removals)}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
          >
            {applying ? <RefreshCw size={16} className="animate-spin" /> : <Trash2 size={16} />}
            حذفِ همهٔ تکراری‌ها
          </button>
        </div>
      </div>
      <p className="text-sm text-gray-500 mb-6" dir="rtl">
        ابتدا اسکن کنید و نتیجه را بازبینی کنید، سپس تأیید کنید. حذف‌ها نرم و قابل بازگشت
        (از «سطل بازیافت») هستند و در لاگِ هر مشتری ثبت می‌شوند. تسهیلات فقط برای بازبینی
        نمایش داده می‌شوند و هرگز خودکار حذف نمی‌شوند.
      </p>

      {/* Schedule + AI config */}
      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4" dir="rtl">
          <div className="flex items-center gap-2 mb-3">
            <CalendarClock size={18} className="text-gray-500" />
            <h3 className="font-semibold">زمان‌بندیِ پاک‌سازیِ خودکار</h3>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            در بازهٔ انتخاب‌شده به‌صورت خودکار اسکن انجام می‌شود و در صورتِ یافتنِ مورد،
            به مدیران اطلاع داده می‌شود (بدونِ حذفِ خودکار).
          </p>
          <div className="flex items-center gap-2">
            <select
              value={config?.schedule || 'off'}
              onChange={(e) => saveConfig({ schedule: e.target.value })}
              disabled={savingCfg || !config}
              className="border rounded-lg px-3 py-2 text-sm bg-white"
            >
              {(config?.schedules || ['off', 'daily', 'weekly', 'monthly']).map((s) => (
                <option key={s} value={s}>{SCHEDULE_LABEL[s] || s}</option>
              ))}
            </select>
            <span className="text-xs text-gray-500">
              آخرین اجرای خودکار: {fmtDate(config?.last_run)}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4" dir="rtl">
          <div className="flex items-center gap-2 mb-3">
            <Bot size={18} className="text-gray-500" />
            <h3 className="font-semibold">نظرِ دومِ هوش مصنوعی</h3>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            {config?.ai_available
              ? <>مدلِ فعال: <b>{config?.active_model}</b></>
              : 'هیچ مدلِ فعالی پیکربندی نشده است.'}
          </p>
          {config && config.models.length > 0 && (
            <ul className="text-xs text-gray-500 mb-3 space-y-0.5">
              {config.models.slice(0, 4).map((m, i) => (
                <li key={m.id}>
                  {i === 0 ? '★ ' : ''}{m.name}{m.provider ? ` — ${m.provider}` : ''}
                </li>
              ))}
            </ul>
          )}
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={config?.ai_review === 'on'}
                onChange={(e) => saveConfig({ ai_review: e.target.checked ? 'on' : 'off' })}
                disabled={savingCfg || !config}
              />
              پیشنهادِ هوش مصنوعی در گزارش
            </label>
            <button
              type="button"
              onClick={runAiReview}
              disabled={aiLoading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {aiLoading ? <RefreshCw size={14} className="animate-spin" /> : <Bot size={14} />}
              اجرای نظرِ دوم
            </button>
          </div>
        </div>
      </div>

      {/* Scan report */}
      {report && (
        <div className="mb-6" dir="rtl">
          {/* Counts summary */}
          <div className="flex flex-wrap gap-2 mb-4 text-sm">
            {entityKeys.map((k) => (
              <span key={k} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">
                {ENTITY_META[k].label}: <b>{counts[k] || 0}</b>
              </span>
            ))}
            <span className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full">
              تسهیلاتِ نیازمندِ بررسی: <b>{counts.facilities_review || 0}</b>
            </span>
            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full">
              مجموعِ قابلِ حذف: <b>{counts.total_removals || 0}</b>
            </span>
          </div>

          {/* Per-entity duplicate groups */}
          {entityKeys.map((key) => {
            const groups = report.groups[key] || []
            if (!groups.length) return null
            const meta = ENTITY_META[key]
            const Icon = meta.Icon
            return (
              <div key={key} className="bg-white rounded-lg shadow-sm mb-4 overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
                  <div className="flex items-center gap-2 font-semibold">
                    <Icon size={16} className={meta.color} />
                    {meta.label}
                    <span className="text-xs text-gray-500">({counts[key] || 0} قابلِ حذف)</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => applyRemovals([key])}
                    disabled={applying}
                    className="inline-flex items-center gap-1 px-3 py-1.5 border border-red-200 text-red-600 rounded-lg text-xs hover:bg-red-50 disabled:opacity-50"
                  >
                    <Trash2 size={13} /> حذفِ تکراری‌های این بخش
                  </button>
                </div>
                <div className="divide-y">
                  {groups.map((g, gi) => (
                    <div key={gi} className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-1">
                        <span>حساب: <b className="text-gray-700">{g.account_no}</b></span>
                        {g.customer_name && <span>— {g.customer_name}</span>}
                        {g.reason && (
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">
                            دلیلِ تشخیص: {g.reason}
                          </span>
                        )}
                        {g.conflict_fields.length > 0 && (
                          <span className="inline-flex items-center gap-1 text-orange-600">
                            <AlertTriangle size={12} /> مغایرت: {g.conflict_fields.join('، ')}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-green-700 mb-1">
                        ✓ نگه‌داشته می‌شود: {g.keeper.summary}
                      </div>
                      <ul className="text-sm text-gray-500 space-y-0.5">
                        {g.removals.map((r) => (
                          <li key={r.id} className="line-through decoration-red-300">✕ {r.summary}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          {/* Facilities — review only */}
          {facReview.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm mb-4 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b bg-amber-50 font-semibold text-amber-800">
                <Landmark size={16} />
                تسهیلاتِ مشکوک به تکرار — فقط بازبینی (به‌صورت خودکار حذف نمی‌شوند)
              </div>
              <div className="divide-y">
                {facReview.map((f, fi) => (
                  <div key={fi} className="px-4 py-3">
                    <div className="text-xs text-gray-500 mb-1">
                      حساب: <b className="text-gray-700">{f.account_no}</b>
                      {f.customer_name && <span> — {f.customer_name}</span>}
                    </div>
                    <ul className="text-sm text-gray-600 space-y-0.5">
                      {f.rows.map((r) => <li key={r.id}>• {r.summary}</li>)}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {counts.total_removals === 0 && facReview.length === 0 && (
            <div className="bg-white rounded-lg shadow-sm py-10 text-center text-gray-500">
              موردِ تکراری‌ای پیدا نشد — دیتابیس تمیز است ✅
            </div>
          )}
        </div>
      )}

      {/* AI suggestions */}
      {ai && ai.available && (
        <div className="bg-white rounded-lg shadow-sm mb-6 overflow-hidden" dir="rtl">
          <div className="flex items-center gap-2 px-4 py-3 border-b bg-indigo-50 font-semibold text-indigo-800">
            <Bot size={16} /> پیشنهادِ هوش مصنوعی {ai.model ? `(${ai.model})` : ''} — فقط برای بازبینی
          </div>
          {ai.suggestions && ai.suggestions.length > 0 ? (
            <div className="divide-y">
              {ai.suggestions.map((s, si) => (
                <div key={si} className="px-4 py-3">
                  <div className="text-xs text-gray-500 mb-1">
                    {s.label} — حساب <b className="text-gray-700">{s.account_no}</b>
                  </div>
                  <ul className="text-sm text-gray-600 space-y-0.5">
                    {s.items.map((it) => <li key={it.id}>• {it.info}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-gray-500 text-sm">
              هوش مصنوعی موردِ اضافه‌ای پیدا نکرد.
            </div>
          )}
        </div>
      )}

      {/* History */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden" dir="rtl">
        <div className="flex items-center gap-2 px-4 py-3 border-b bg-gray-50 font-semibold">
          <HistoryIcon size={16} className="text-gray-500" /> تاریخچهٔ اجراها
        </div>
        {history.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <th className="px-4 py-2 text-right font-medium">زمان</th>
                <th className="px-4 py-2 text-right font-medium">نوع</th>
                <th className="px-4 py-2 text-right font-medium">کاربر</th>
                <th className="px-4 py-2 text-right font-medium">شرح</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {history.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{fmtDate(run.created_at)}</td>
                  <td className="px-4 py-2">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">
                      {run.kind === 'scan' ? 'اسکن' : run.kind === 'apply' ? 'حذف' : run.kind === 'scheduled' ? 'زمان‌بندی‌شده' : run.kind}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">{run.username || '—'}</td>
                  <td className="px-4 py-2 text-gray-500">
                    {run.detail || `مجموع: ${run.counts?.total_removals ?? run.counts?.total ?? 0}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-8 text-center text-gray-500 text-sm">هنوز اجرایی ثبت نشده است.</div>
        )}
      </div>
    </Layout>
  )
}
