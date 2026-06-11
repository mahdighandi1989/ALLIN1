'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import AISettings from '@/components/AISettings'
import TelegramSettings from '@/components/TelegramSettings'
import { settingsApi, fxApi, crmApi, parseApiError, downloadFile } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { SettingsResponse, FxRates } from '@/types'
import { Settings as SettingsIcon, Save, Lock, Coins, Database, RefreshCw, Bot, Cloud, CloudOff, CheckCircle2, XCircle, Send } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const router = useRouter()
  const { user, authDisabled, loading: authLoading } = useAuth()
  const [data, setData] = useState<SettingsResponse | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
  const [tab, setTab] = useState<'general' | 'ai' | 'telegram'>('general')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [fx, setFx] = useState<FxRates | null>(null)
  const [fxForm, setFxForm] = useState<Record<string, string>>({})
  const [savingFx, setSavingFx] = useState(false)
  const [mergeInfo, setMergeInfo] = useState<any>(null)
  const [merging, setMerging] = useState(false)
  const [scanInfo, setScanInfo] = useState<any>(null)
  const [scanning, setScanning] = useState(false)
  const runScan = async () => {
    setScanning(true)
    try {
      const r = await crmApi.runExpiryScan()
      setScanInfo(r)
      toast.success(`Expiry scan: ${r.total} alert(s) (${r.facilities} facilities, ${r.documents} documents)`)
    } catch (e) { toast.error(parseApiError(e)) } finally { setScanning(false) }
  }
  const downloadBackup = async () => {
    try { await downloadFile('/api/crm/backup/export.json', 'allin1-backup.json') }
    catch (e) { toast.error(parseApiError(e)) }
  }

  const [driveStatus, setDriveStatus] = useState<any>(null)
  const [driveLoading, setDriveLoading] = useState(false)
  const [driveSyncing, setDriveSyncing] = useState(false)
  const checkDrive = async () => {
    setDriveLoading(true)
    try { setDriveStatus(await crmApi.driveStatus()) }
    catch (e) { toast.error(parseApiError(e)) } finally { setDriveLoading(false) }
  }
  const driveSyncNow = async () => {
    setDriveSyncing(true)
    try {
      const r = await crmApi.driveSyncNow()
      const n = r?.bytes ? `${Math.round(r.bytes / 1024)} KB` : ''
      toast.success(`سینک با Google Drive انجام شد ${n ? `(${n})` : ''}`)
      await checkDrive()
    } catch (e) { toast.error(parseApiError(e)) } finally { setDriveSyncing(false) }
  }
  // Connect is a top-level browser navigation (OAuth consent), so the admin JWT
  // is passed as a query param — the backend validates it before redirecting to
  // Google. The API base matches the axios config (same origin in production).
  const connectDrive = () => {
    const base = process.env.NEXT_PUBLIC_API_URL ?? ''
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : ''
    window.location.href = `${base}/api/auth/google/drive/connect?token=${encodeURIComponent(token || '')}`
  }
  const disconnectDrive = async () => {
    if (!confirm('اتصال Google Drive قطع شود؟ سینک تا اتصال مجدد متوقف می‌شود.')) return
    try {
      await crmApi.driveDisconnect()
      toast.success('اتصال Google Drive قطع شد')
      await checkDrive()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const isAdmin = authDisabled || !!user?.is_admin

  useEffect(() => {
    if (isAdmin) {
      crmApi.mergeStatus().then(setMergeInfo).catch(() => {})
      crmApi.driveStatus().then(setDriveStatus).catch(() => {})
    }
  }, [isAdmin])

  // Feedback after returning from the Google "Connect Drive" consent screen.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const drive = new URLSearchParams(window.location.search).get('drive')
    if (!drive) return
    if (drive === 'connected') toast.success('Google Drive با موفقیت متصل شد ✅')
    else if (drive === 'error_no_refresh_token') toast.error('توکن دریافت نشد؛ دوباره تلاش کن و در صفحهٔ گوگل اجازه بده.')
    else if (drive === 'forbidden') toast.error('فقط ادمین می‌تواند Drive را متصل کند.')
    else if (drive === 'google_not_configured') toast.error('GOOGLE_CLIENT_ID/SECRET تنظیم نشده است.')
    // Clean the query param and refresh the live status.
    window.history.replaceState({}, '', window.location.pathname)
    crmApi.driveStatus().then(setDriveStatus).catch(() => {})
  }, [])
  const runMerge = async () => {
    setMerging(true)
    try {
      const r = await crmApi.runMerge()
      toast.success('Data merge complete')
      const s = await crmApi.mergeStatus()
      setMergeInfo(s)
    } catch (e) { toast.error(parseApiError(e)) } finally { setMerging(false) }
  }

  useEffect(() => {
    if (authLoading) return
    if (!authDisabled && user && !user.is_admin) router.replace('/dashboard')
  }, [authLoading, authDisabled, user, router])

  const load = async () => {
    try {
      setLoading(true)
      const [res, fxRes] = await Promise.all([settingsApi.get(), fxApi.list().catch(() => null)])
      setData(res)
      const initial: Record<string, string> = {}
      res.editable.forEach((e) => { initial[e.key] = e.value })
      setForm(initial)
      if (fxRes) {
        setFx(fxRes)
        const f: Record<string, string> = {}
        fxRes.rates.forEach((r) => { f[r.currency] = String(r.rate_to_base) })
        setFxForm(f)
      }
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  const saveFx = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingFx(true)
    try {
      const base = fx?.base_currency
      const rates: Record<string, number> = {}
      Object.entries(fxForm).forEach(([cur, val]) => {
        if (cur !== base) rates[cur] = parseFloat(val) || 0
      })
      await fxApi.update(rates)
      toast.success('Exchange rates saved')
      load()
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSavingFx(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const save = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await settingsApi.update(form)
      toast.success('Settings saved')
      load()
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <Layout><div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div></Layout>
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <SettingsIcon size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">System Settings</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b mb-6">
        <button
          type="button"
          onClick={() => setTab('general')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'general'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <SettingsIcon size={16} /> General
        </button>
        <button
          type="button"
          onClick={() => setTab('ai')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'ai'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Bot size={16} /> AI Models &amp; Providers
        </button>
        <button
          type="button"
          onClick={() => setTab('telegram')}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'telegram'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Send size={16} /> Telegram
        </button>
      </div>

      {/* AI tab — central AI control layer, on its own wider canvas */}
      {tab === 'ai' && (
        <div className="max-w-4xl">
          <AISettings isAdmin={isAdmin} />
        </div>
      )}

      {/* Telegram tab — two-way notifications + bot control */}
      {tab === 'telegram' && (
        <div className="max-w-4xl">
          <TelegramSettings isAdmin={isAdmin} />
        </div>
      )}

      <div className={`max-w-2xl space-y-6 ${tab === 'general' ? '' : 'hidden'}`}>
        {/* Editable settings */}
        <form onSubmit={save} className="bg-white rounded-lg shadow-sm p-6 space-y-4" data-testid="settings-form">
          <h3 className="font-medium">Application settings</h3>
          {data?.editable.map((s) => (
            <div key={s.key}>
              <label className="block text-sm font-medium mb-1">{s.label}</label>
              <input
                type={s.type === 'number' ? 'number' : 'text'}
                value={form[s.key] ?? ''}
                onChange={(e) => setForm({ ...form, [s.key]: e.target.value })}
                disabled={!isAdmin}
                className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
              />
            </div>
          ))}
          {isAdmin ? (
            <button type="submit" disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              <Save size={16} /> {saving ? 'Saving…' : 'Save settings'}
            </button>
          ) : (
            <p className="text-sm text-gray-500 flex items-center gap-1"><Lock size={14} /> Read-only (admin required to edit)</p>
          )}
        </form>

        {/* Exchange rates */}
        {fx && (
          <form onSubmit={saveFx} className="bg-white rounded-lg shadow-sm p-6 space-y-4" data-testid="fx-form">
            <h3 className="font-medium flex items-center gap-2">
              <Coins size={16} /> Exchange rates
              <span className="text-xs text-gray-400">(1 unit = X {fx.base_currency})</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {fx.rates.map((r) => (
                <div key={r.currency}>
                  <label className="block text-sm font-medium mb-1">
                    {r.currency}{r.currency === fx.base_currency ? ' (base)' : ''}
                  </label>
                  <input
                    type="number" step="0.0001" min="0"
                    value={fxForm[r.currency] ?? ''}
                    onChange={(e) => setFxForm({ ...fxForm, [r.currency]: e.target.value })}
                    disabled={!isAdmin || r.currency === fx.base_currency}
                    className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
                  />
                </div>
              ))}
            </div>
            {isAdmin && (
              <button type="submit" disabled={savingFx}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <Save size={16} /> {savingFx ? 'Saving…' : 'Save rates'}
              </button>
            )}
          </form>
        )}

        {/* Legacy data merge (admin) */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="font-medium flex items-center gap-2 mb-1"><Database size={16} /> Legacy data merge</h3>
            <p className="text-sm text-gray-500 mb-3">داده‌های سیستمِ اکسلِ قبلی (ضامن‌ها، تسهیلات، KYC، …) را در دیتابیسِ پنل ادغام/به‌روزرسانی می‌کند. خودکار در هر startup اجرا می‌شود؛ این دکمه برای اجرای دستی و بررسی است.</p>
            {mergeInfo && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm mb-3">
                {Object.entries(mergeInfo).map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded p-2">
                    <div className="text-gray-400 text-xs">{k.replace(/_/g, ' ')}</div>
                    <div className="font-bold tabular-nums">{String(v)}</div>
                  </div>
                ))}
              </div>
            )}
            <button onClick={runMerge} disabled={merging} type="button"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              <RefreshCw size={16} className={merging ? 'animate-spin' : ''} /> {merging ? 'Merging…' : 'Run data merge now'}
            </button>
          </div>
        )}

        {/* Expiry alert scan (admin) */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="font-medium flex items-center gap-2 mb-1"><RefreshCw size={16} /> Expiry alert scan</h3>
            <p className="text-sm text-gray-500 mb-3">تسهیلات و مدارکی که ظرفِ «Expiry warning window» منقضی می‌شوند را به‌صورتِ تسکِ هشدار (اولویت High) در لیستِ کارهای همان مشتری ثبت می‌کند. خودکار در startup اجرا می‌شود؛ این دکمه برای اجرای دستی است.</p>
            {scanInfo && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm mb-3">
                {Object.entries(scanInfo).map(([k, v]) => (
                  <div key={k} className="bg-gray-50 rounded p-2">
                    <div className="text-gray-400 text-xs">{k.replace(/_/g, ' ')}</div>
                    <div className="font-bold tabular-nums">{String(v)}</div>
                  </div>
                ))}
              </div>
            )}
            <button onClick={runScan} disabled={scanning} type="button"
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50">
              <RefreshCw size={16} className={scanning ? 'animate-spin' : ''} /> {scanning ? 'Scanning…' : 'Run expiry scan now'}
            </button>
          </div>
        )}

        {/* Backup export (admin) */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="font-medium flex items-center gap-2 mb-1"><Database size={16} /> Backup export</h3>
            <p className="text-sm text-gray-500 mb-3">یک نسخهٔ کاملِ دادهٔ پنل (مشتریان، تسهیلات، KYC، ضامن‌ها، املاک، چک‌لیست‌ها، …) را به‌صورتِ یک فایلِ JSON روی دستگاهِ خودت دانلود می‌کند (دستی و محلی، بدونِ ارتباط با Google Drive).</p>
            <button onClick={downloadBackup} type="button"
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900">
              <Database size={16} /> Download backup (JSON)
            </button>
          </div>
        )}

        {/* Google Drive sync (admin) */}
        {isAdmin && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-1">
              <h3 className="font-medium flex items-center gap-2">
                {driveStatus?.connected ? <Cloud size={16} className="text-green-600" /> : <CloudOff size={16} className="text-gray-400" />}
                همگام‌سازی با Google Drive
              </h3>
              {driveStatus && (
                <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${driveStatus.connected ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {driveStatus.connected ? <><CheckCircle2 size={13} /> متصل</> : <><XCircle size={13} /> غیرفعال / قطع</>}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mb-3">
              اسنپ‌شاتِ کاملِ دیتابیس و فایل‌های پیوست را به‌صورت خودکار در فولدرِ Drive شما آپلود و همگام نگه می‌دارد.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm mb-4">
              <div className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">فعال در تنظیمات</span>
                <span className="font-medium">{driveStatus ? (driveStatus.enabled ? 'بله' : 'خیر') : '…'}</span>
              </div>
              <div className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">روش اتصال</span>
                <span className="font-medium" dir="ltr">{driveStatus?.mode === 'service_account' ? 'Service Account' : 'OAuth (حساب شخصی)'}</span>
              </div>
              <div className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">{driveStatus?.mode === 'service_account' ? 'حساب سرویس' : 'حساب متصل'}</span>
                <span className="font-medium truncate ltr text-left" dir="ltr">{driveStatus?.account || driveStatus?.service_account || '—'}</span>
              </div>
              <div className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">فولدر مقصد</span>
                <span className="font-medium truncate ltr text-left" dir="ltr">{driveStatus?.folder_name || driveStatus?.root_folder_id || '—'}</span>
              </div>
            </div>

            {driveStatus && !driveStatus.connected && driveStatus.error && driveStatus.error !== 'not_connected' && (
              <p className="text-sm text-red-600 mb-3 break-all">خطا: {driveStatus.error}</p>
            )}
            {driveStatus && !driveStatus.enabled && (
              <p className="text-sm text-amber-600 mb-3">برای فعال‌سازی، در محیطِ سرور (Render) مقدارِ <code dir="ltr">GOOGLE_DRIVE_ENABLED=true</code> را تنظیم کنید (روش پیش‌فرض OAuth است و فقط به <code dir="ltr">GOOGLE_CLIENT_ID/SECRET</code> نیاز دارد).</p>
            )}
            {driveStatus && driveStatus.enabled && driveStatus.mode === 'oauth' && !driveStatus.connected && (
              <p className="text-sm text-blue-700 mb-3">برای اتصال، دکمهٔ «اتصال Google Drive» را بزن و با حساب گوگلِ خودت اجازه بده. فایل‌ها در فضای ۱۵ گیگابایتیِ خودت ذخیره می‌شوند.</p>
            )}

            <div className="flex flex-wrap gap-2">
              {/* OAuth connect/disconnect */}
              {driveStatus?.mode === 'oauth' && !driveStatus?.connected && (
                <button onClick={connectDrive} type="button"
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                  <Cloud size={16} /> اتصال Google Drive
                </button>
              )}
              {driveStatus?.mode === 'oauth' && driveStatus?.connected && (
                <button onClick={disconnectDrive} type="button"
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-red-700 rounded-lg hover:bg-gray-200">
                  <CloudOff size={16} /> قطع اتصال
                </button>
              )}
              <button onClick={checkDrive} disabled={driveLoading} type="button"
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 disabled:opacity-50">
                <RefreshCw size={16} className={driveLoading ? 'animate-spin' : ''} /> {driveLoading ? 'در حال بررسی…' : 'بررسی اتصال'}
              </button>
              <button onClick={driveSyncNow} disabled={driveSyncing || !driveStatus?.connected} type="button"
                title={!driveStatus?.connected ? 'ابتدا اتصال باید برقرار باشد' : ''}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                <Cloud size={16} className={driveSyncing ? 'animate-pulse' : ''} /> {driveSyncing ? 'در حال همگام‌سازی…' : 'همگام‌سازی فوری با Drive'}
              </button>
            </div>
          </div>
        )}

        {/* Read-only runtime config */}
        <div className="bg-white rounded-lg shadow-sm p-6" data-testid="settings-runtime">
          <h3 className="font-medium mb-3">Runtime configuration <span className="text-xs text-gray-400">(read-only · from environment)</span></h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {data && Object.entries(data.runtime).map(([k, v]) => (
              <div key={k} className="flex justify-between border-b py-1.5">
                <span className="text-gray-500">{k.replace(/_/g, ' ')}</span>
                <span className="font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
