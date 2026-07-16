'use client'

/**
 * Database Cleanup (de-duplication) — admin, REVIEW FIRST.
 *
 * Two tiers:
 *   • CERTAIN duplicates — identical strong id + identical key values → safe to
 *     remove (soft-delete, reversible via the Recycle Bin, logged per customer).
 *   • NEEDS JUDGMENT ("probable") — same strong id but a key value differs: almost
 *     always the SAME record whose data was UPDATED over time, occasionally a
 *     distinct sub-entity (another unit / another cheque). These are never
 *     auto-removed. The AI adjudicator judges each one holistically (weighing every
 *     field) and pre-selects the ones it is confident are the same; you approve.
 */
import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/lib/auth'
import {
  cleanupApi, parseApiError,
  type CleanupReport, type CleanupConfig, type CleanupRun, type CleanupAIReview,
  type CleanupGroup,
} from '@/lib/api'
import {
  Sparkles, ScanSearch, Trash2, CalendarClock, Bot, History as HistoryIcon,
  AlertTriangle, ShieldCheck, RefreshCw, Building2, Users, Landmark, PiggyBank,
  CheckCircle2, HelpCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'

const ENTITY_META: Record<string, { label: string; Icon: any; color: string }> = {
  properties: { label: 'املاک مرهونه', Icon: Building2, color: 'text-blue-600' },
  guarantors: { label: 'ضامن‌ها', Icon: ShieldCheck, color: 'text-green-600' },
  fixed_deposits: { label: 'سپرده‌های ثابت', Icon: PiggyBank, color: 'text-purple-600' },
  partners: { label: 'شرکا', Icon: Users, color: 'text-amber-600' },
}
const ENTITY_KEYS = ['properties', 'guarantors', 'fixed_deposits', 'partners']
const SCHEDULE_LABEL: Record<string, string> = { off: 'خاموش', daily: 'روزانه', weekly: 'هفتگی', monthly: 'ماهانه' }

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString('fa-IR') } catch { return iso }
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
  // AI verdict per removal id, for inline display on the probable groups.
  const [aiById, setAiById] = useState<Record<string, { same: boolean; confidence: number; reason: string }>>({})
  // 'probable' removal ids the admin has selected to delete on apply.
  const [confirm, setConfirm] = useState<Set<string>>(new Set())

  const [history, setHistory] = useState<CleanupRun[]>([])

  const loadConfig = async () => { try { setConfig(await cleanupApi.getConfig()) } catch (e) { toast.error(parseApiError(e)) } }
  const loadHistory = async () => { try { setHistory((await cleanupApi.history()).runs) } catch { /* non-critical */ } }

  useEffect(() => { if (isAdmin) { loadConfig(); loadHistory() } }, [isAdmin])

  const runScan = async () => {
    try {
      setScanning(true)
      const r = await cleanupApi.scan()
      setReport(r)
      setConfirm(new Set()); setAi(null); setAiById({})
      const c = r.counts.total_removals || 0, rev = r.counts.total_review || 0
      toast.success(`${c} تکراریِ قطعی، ${rev} موردِ نیازمندِ بررسی`)
      loadHistory()
    } catch (e) { toast.error(parseApiError(e)) } finally { setScanning(false) }
  }

  const applyRemovals = async () => {
    const certain = report?.counts.total_removals || 0
    const picked = confirm.size
    if (!certain && !picked) { toast('چیزی برای حذف انتخاب نشده', { icon: 'ℹ️' }); return }
    if (!window.confirm(
      `حذفِ ${certain} تکراریِ قطعی` + (picked ? ` و ${picked} موردِ تأییدشده` : '') +
      '؟\n\nرکوردها نرم‌حذف می‌شوند (قابل بازیابی از «سطل بازیافت») و در لاگِ هر مشتری ثبت می‌گردند.'
    )) return
    try {
      setApplying(true)
      const res = await cleanupApi.apply(undefined, Array.from(confirm))
      toast.success(`${res.removed.total || 0} رکورد حذف شد`)
      await runScan(); loadHistory()
    } catch (e) { toast.error(parseApiError(e)) } finally { setApplying(false) }
  }

  const saveConfig = async (patch: { schedule?: string; ai_review?: string }) => {
    try { setSavingCfg(true); setConfig(await cleanupApi.updateConfig(patch)); toast.success('تنظیمات ذخیره شد') }
    catch (e) { toast.error(parseApiError(e)) } finally { setSavingCfg(false) }
  }

  const runAiReview = async () => {
    try {
      setAiLoading(true)
      const r = await cleanupApi.aiReview()
      setAi(r)
      if (!r.available) { toast(r.note || 'هوش مصنوعی در دسترس نیست', { icon: 'ℹ️' }); return }
      // index verdicts by removal id and pre-select the ones the AI confirms are the same
      const idx: Record<string, { same: boolean; confidence: number; reason: string }> = {}
      for (const g of r.verdicts || []) for (const v of g.verdicts) idx[v.id] = { same: v.same, confidence: v.confidence, reason: v.reason }
      setAiById(idx)
      setConfirm(new Set(r.confirmed_ids || []))
      toast.success(`داوریِ هوش مصنوعی: ${(r.confirmed_ids || []).length} موردِ «تکراری» تأیید شد`)
    } catch (e) { toast.error(parseApiError(e)) } finally { setAiLoading(false) }
  }

  const toggle = (id: string) => setConfirm((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })

  if (!isAdmin) {
    return <Layout><div className="py-16 text-center text-gray-500">این صفحه فقط برای مدیران در دسترس است.</div></Layout>
  }

  const counts = report?.counts || {}
  const facReview = report?.review?.facilities || []
  const groupsOf = (key: string, conf: 'certain' | 'probable'): CleanupGroup[] =>
    (report?.groups[key] || []).filter((g) => g.confidence === conf)
  const anyProbable = ENTITY_KEYS.some((k) => groupsOf(k, 'probable').length > 0)

  return (
    <Layout>
      {/* Header + primary actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <Sparkles size={22} className="text-indigo-600" />
          <h2 className="text-2xl font-bold">Database Cleanup</h2>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={runScan} disabled={scanning}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
            {scanning ? <RefreshCw size={16} className="animate-spin" /> : <ScanSearch size={16} />} اسکنِ دیتابیس
          </button>
          <button type="button" onClick={applyRemovals} disabled={applying || !((counts.total_removals || 0) + confirm.size)}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50">
            {applying ? <RefreshCw size={16} className="animate-spin" /> : <Trash2 size={16} />}
            حذف ({(counts.total_removals || 0) + confirm.size})
          </button>
        </div>
      </div>
      <p className="text-sm text-gray-500 mb-6" dir="rtl">
        «تکراریِ قطعی» = شناسه و مقادیر یکسان (امن برای حذف). «نیازمندِ بررسی» = شناسۀ یکسان ولی مقداری
        متفاوت (احتمالاً همان رکوردِ به‌روزشده، یا موردی جدا) — این‌ها خودکار حذف نمی‌شوند؛ هوش مصنوعی با
        سنجشِ همۀ فیلدها داوری می‌کند و شما تأیید می‌کنید. حذف‌ها قابلِ بازگشت‌اند و در لاگِ هر مشتری ثبت می‌شوند.
      </p>

      {/* Schedule + AI config */}
      <div className="grid gap-4 md:grid-cols-2 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-4" dir="rtl">
          <div className="flex items-center gap-2 mb-3"><CalendarClock size={18} className="text-gray-500" />
            <h3 className="font-semibold">زمان‌بندیِ پاک‌سازیِ خودکار</h3></div>
          <p className="text-xs text-gray-500 mb-3">در بازۀ انتخاب‌شده خودکار اسکن می‌شود و در صورتِ یافتنِ مورد، به مدیران اطلاع می‌رسد (بدونِ حذفِ خودکار).</p>
          <div className="flex items-center gap-2">
            <select value={config?.schedule || 'off'} onChange={(e) => saveConfig({ schedule: e.target.value })}
              disabled={savingCfg || !config} className="border rounded-lg px-3 py-2 text-sm bg-white">
              {(config?.schedules || ['off', 'daily', 'weekly', 'monthly']).map((s) => (
                <option key={s} value={s}>{SCHEDULE_LABEL[s] || s}</option>))}
            </select>
            <span className="text-xs text-gray-500">آخرین اجرای خودکار: {fmtDate(config?.last_run)}</span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4" dir="rtl">
          <div className="flex items-center gap-2 mb-3"><Bot size={18} className="text-gray-500" />
            <h3 className="font-semibold">داوریِ هوش مصنوعی</h3></div>
          <p className="text-xs text-gray-500 mb-3">
            {config?.ai_available ? <>مدلِ فعال: <b>{config?.active_model}</b></> : 'هیچ مدلِ فعالی پیکربندی نشده است.'}
          </p>
          {config && config.models.length > 0 && (
            <ul className="text-xs text-gray-500 mb-3 space-y-0.5">
              {config.models.slice(0, 4).map((m, i) => (
                <li key={m.id}>{i === 0 ? '★ ' : ''}{m.name}{m.provider ? ` — ${m.provider}` : ''}</li>))}
            </ul>
          )}
          <div className="flex items-center gap-3 flex-wrap">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={config?.ai_review === 'on'}
                onChange={(e) => saveConfig({ ai_review: e.target.checked ? 'on' : 'off' })} disabled={savingCfg || !config} />
              فعال‌سازیِ داوری در گزارش
            </label>
            <button type="button" onClick={runAiReview} disabled={aiLoading || !report}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50">
              {aiLoading ? <RefreshCw size={14} className="animate-spin" /> : <Bot size={14} />} داوریِ مواردِ نیازمندِ بررسی
            </button>
          </div>
        </div>
      </div>

      {report && (
        <div className="mb-6" dir="rtl">
          {/* Counts summary */}
          <div className="flex flex-wrap gap-2 mb-4 text-sm">
            {ENTITY_KEYS.map((k) => (
              <span key={k} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">
                {ENTITY_META[k].label}: <b>{counts[k] || 0}</b>
                {(counts[k + '_review'] || 0) > 0 && <span className="text-amber-700"> (+{counts[k + '_review']} بررسی)</span>}
              </span>
            ))}
            <span className="px-3 py-1 bg-red-50 text-red-700 rounded-full">تکراریِ قطعی: <b>{counts.total_removals || 0}</b></span>
            <span className="px-3 py-1 bg-amber-50 text-amber-700 rounded-full">نیازمندِ بررسی: <b>{counts.total_review || 0}</b></span>
          </div>

          {/* ---- CERTAIN duplicates (safe to remove) ---- */}
          {ENTITY_KEYS.map((key) => {
            const gs = groupsOf(key, 'certain')
            if (!gs.length) return null
            const meta = ENTITY_META[key]; const Icon = meta.Icon
            return (
              <div key={`c-${key}`} className="bg-white rounded-lg shadow-sm mb-4 overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-3 border-b bg-gray-50 font-semibold">
                  <Icon size={16} className={meta.color} /> {meta.label}
                  <span className="inline-flex items-center gap-1 text-xs text-green-700"><CheckCircle2 size={13} /> تکراریِ قطعی ({counts[key] || 0})</span>
                </div>
                <div className="divide-y">
                  {gs.map((g, gi) => (
                    <div key={gi} className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-1">
                        <span>حساب: <b className="text-gray-700">{g.account_no}</b></span>
                        {g.customer_name && <span>— {g.customer_name}</span>}
                        {g.reason && <span className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">دلیل: {g.reason}</span>}
                      </div>
                      <div className="text-sm text-green-700 mb-1">✓ نگه‌داشته می‌شود: {g.keeper.summary}</div>
                      <ul className="text-sm text-gray-500 space-y-0.5">
                        {g.removals.map((r) => <li key={r.id} className="line-through decoration-red-300">✕ {r.summary}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          {/* ---- NEEDS JUDGMENT (probable) ---- */}
          {anyProbable && (
            <div className="bg-white rounded-lg shadow-sm mb-4 overflow-hidden">
              <div className="flex items-center justify-between gap-2 px-4 py-3 border-b bg-amber-50 font-semibold text-amber-800">
                <span className="inline-flex items-center gap-2"><HelpCircle size={16} /> نیازمندِ بررسی — شناسۀ یکسان، مقادیرِ متفاوت</span>
                <span className="text-xs font-normal">تیک بزنید تا در حذف لحاظ شود · «داوریِ هوش مصنوعی» موارد را پیشنهاد می‌دهد</span>
              </div>
              <div className="divide-y">
                {ENTITY_KEYS.flatMap((key) => groupsOf(key, 'probable').map((g, gi) => {
                  const meta = ENTITY_META[key]; const Icon = meta.Icon
                  return (
                    <div key={`p-${key}-${gi}`} className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-1">
                        <Icon size={14} className={meta.color} />
                        <span>حساب: <b className="text-gray-700">{g.account_no}</b></span>
                        {g.customer_name && <span>— {g.customer_name}</span>}
                        {g.reason && <span className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">{g.reason}</span>}
                        {g.conflict_fields.length > 0 && (
                          <span className="inline-flex items-center gap-1 text-orange-600"><AlertTriangle size={12} /> اختلاف: {g.conflict_fields.join('، ')}</span>
                        )}
                      </div>
                      <div className="text-sm text-green-700 mb-1">✓ مبنا (نگه‌داشته می‌شود): {g.keeper.summary}</div>
                      <ul className="space-y-1">
                        {g.removals.map((r) => {
                          const v = aiById[r.id]
                          return (
                            <li key={r.id} className="flex items-start gap-2 text-sm">
                              <input type="checkbox" className="mt-1" checked={confirm.has(r.id)} onChange={() => toggle(r.id)} />
                              <span className="flex-1">
                                <span className={confirm.has(r.id) ? 'line-through decoration-red-300 text-gray-500' : 'text-gray-700'}>{r.summary}</span>
                                {v && (
                                  <span className={`block text-xs mt-0.5 ${v.same ? 'text-red-600' : 'text-green-700'}`}>
                                    <Bot size={11} className="inline" /> {v.same ? 'همان رکورد (به‌روزشده)' : 'موردِ جدا — نگه‌دار'}
                                    {typeof v.confidence === 'number' && ` · اطمینان ${Math.round(v.confidence * 100)}٪`}
                                    {v.reason && ` · ${v.reason}`}
                                  </span>
                                )}
                              </span>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )
                }))}
              </div>
            </div>
          )}

          {/* ---- Facilities — review only ---- */}
          {facReview.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm mb-4 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b bg-amber-50 font-semibold text-amber-800">
                <Landmark size={16} /> تسهیلاتِ مشکوک به تکرار — فقط بازبینی (خودکار حذف نمی‌شوند)
              </div>
              <div className="divide-y">
                {facReview.map((f, fi) => (
                  <div key={fi} className="px-4 py-3">
                    <div className="text-xs text-gray-500 mb-1">حساب: <b className="text-gray-700">{f.account_no}</b>{f.customer_name && <span> — {f.customer_name}</span>}</div>
                    <ul className="text-sm text-gray-600 space-y-0.5">{f.rows.map((r) => <li key={r.id}>• {r.summary}</li>)}</ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(counts.total_removals || 0) === 0 && (counts.total_review || 0) === 0 && (
            <div className="bg-white rounded-lg shadow-sm py-10 text-center text-gray-500">موردِ تکراری‌ای پیدا نشد — دیتابیس تمیز است ✅</div>
          )}
        </div>
      )}

      {/* History */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden" dir="rtl">
        <div className="flex items-center gap-2 px-4 py-3 border-b bg-gray-50 font-semibold">
          <HistoryIcon size={16} className="text-gray-500" /> تاریخچۀ اجراها
        </div>
        {history.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500"><tr>
              <th className="px-4 py-2 text-right font-medium">زمان</th>
              <th className="px-4 py-2 text-right font-medium">نوع</th>
              <th className="px-4 py-2 text-right font-medium">کاربر</th>
              <th className="px-4 py-2 text-right font-medium">شرح</th>
            </tr></thead>
            <tbody className="divide-y">
              {history.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{fmtDate(run.created_at)}</td>
                  <td className="px-4 py-2"><span className="px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-700">
                    {run.kind === 'scan' ? 'اسکن' : run.kind === 'apply' ? 'حذف' : run.kind === 'scheduled' ? 'زمان‌بندی‌شده' : run.kind === 'ai_review' ? 'داوریِ AI' : run.kind}
                  </span></td>
                  <td className="px-4 py-2 text-gray-600">{run.username || '—'}</td>
                  <td className="px-4 py-2 text-gray-500">{run.detail || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <div className="py-8 text-center text-gray-500 text-sm">هنوز اجرایی ثبت نشده است.</div>}
      </div>
    </Layout>
  )
}
