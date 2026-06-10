'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import AISettings from '@/components/AISettings'
import { settingsApi, fxApi, crmApi, parseApiError, downloadFile } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { SettingsResponse, FxRates } from '@/types'
import { Settings as SettingsIcon, Save, Lock, Coins, Database, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const router = useRouter()
  const { user, authDisabled, loading: authLoading } = useAuth()
  const [data, setData] = useState<SettingsResponse | null>(null)
  const [form, setForm] = useState<Record<string, string>>({})
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

  const isAdmin = authDisabled || !!user?.is_admin

  useEffect(() => {
    if (isAdmin) crmApi.mergeStatus().then(setMergeInfo).catch(() => {})
  }, [isAdmin])
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

      <div className="max-w-2xl space-y-6">
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

        {/* AI models & providers — central AI control layer */}
        <AISettings isAdmin={isAdmin} />

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
            <p className="text-sm text-gray-500 mb-3">یک نسخهٔ کاملِ دادهٔ پنل (مشتریان، تسهیلات، KYC، ضامن‌ها، املاک، چک‌لیست‌ها، …) را به‌صورتِ یک فایلِ JSON دانلود می‌کند تا نگه‌داری یا بازیابی شود.</p>
            <button onClick={downloadBackup} type="button"
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900">
              <Database size={16} /> Download backup (JSON)
            </button>
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
