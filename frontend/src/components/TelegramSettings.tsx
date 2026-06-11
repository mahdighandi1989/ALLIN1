'use client'

/**
 * Telegram integration — the Settings tab that controls the two-way bot.
 *
 * It lets an admin choose, per event type, whether it is sent at all and whether
 * it rings (sound) or arrives silently; set a global minimum priority; manage the
 * allow-list of chat ids that may drive the bot; point Telegram's webhook at the
 * backend; and fire a test message. Channel readiness (bot token / chat id from
 * the environment) is surfaced so misconfiguration is obvious.
 */

import { useEffect, useState } from 'react'
import { telegramApi, parseApiError, TelegramStatus, TelegramPrefs } from '@/lib/api'
import {
  Send, Bell, BellOff, Volume2, VolumeX, Save, Loader2, CheckCircle2, XCircle,
  Link2, Plus, Trash2, MessageCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'

const PRIORITIES: TelegramPrefs['min_priority'][] = ['low', 'medium', 'high', 'critical']
const PRIORITY_LABEL: Record<string, string> = {
  low: 'کم', medium: 'متوسط', high: 'زیاد', critical: 'بحرانی',
}

export default function TelegramSettings({ isAdmin }: { isAdmin: boolean }) {
  const [status, setStatus] = useState<TelegramStatus | null>(null)
  const [prefs, setPrefs] = useState<TelegramPrefs | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [webhookUrl, setWebhookUrl] = useState('')
  const [newChatId, setNewChatId] = useState('')

  const load = async () => {
    try {
      setLoading(true)
      const s = await telegramApi.status()
      setStatus(s)
      setPrefs(s.prefs)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const save = async (partial: Partial<TelegramPrefs>) => {
    if (!isAdmin) return
    setSaving(true)
    try {
      const { prefs: updated } = await telegramApi.updatePrefs(partial)
      setPrefs(updated)
      toast.success('تنظیمات تلگرام ذخیره شد')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSaving(false)
    }
  }

  const toggleEvent = (key: string, kind: 'events' | 'sound') => {
    if (!prefs) return
    const next = { ...prefs[kind], [key]: !prefs[kind][key] }
    setPrefs({ ...prefs, [kind]: next })
    save({ [kind]: { [key]: !prefs[kind][key] } } as Partial<TelegramPrefs>)
  }

  const toggleChannel = (name: string) => {
    if (!prefs) return
    const cur = prefs.channels[name]?.enabled ?? true
    setPrefs({ ...prefs, channels: { ...prefs.channels, [name]: { enabled: !cur } } })
    save({ channels: { [name]: { enabled: !cur } } })
  }

  const test = async () => {
    setTesting(true)
    try {
      const r = await telegramApi.test()
      r.ok ? toast.success('پیام تست ارسال شد ✅') : toast.error('ارسال تست ناموفق بود — توکن/چت‌آی‌دی را بررسی کنید')
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setTesting(false)
    }
  }

  const setWebhook = async () => {
    const url = webhookUrl.trim()
    if (!url) return
    try {
      const r = await telegramApi.setWebhook(url)
      r.ok ? toast.success('وب‌هوک تنظیم شد') : toast.error('تنظیم وب‌هوک ناموفق بود')
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  const addChatId = () => {
    const id = newChatId.trim()
    if (!id || !prefs) return
    if (prefs.allowed_chat_ids.includes(id)) { setNewChatId(''); return }
    const next = [...prefs.allowed_chat_ids, id]
    setPrefs({ ...prefs, allowed_chat_ids: next })
    setNewChatId('')
    save({ allowed_chat_ids: next })
  }

  const removeChatId = (id: string) => {
    if (!prefs) return
    const next = prefs.allowed_chat_ids.filter((c) => c !== id)
    setPrefs({ ...prefs, allowed_chat_ids: next })
    save({ allowed_chat_ids: next })
  }

  if (loading || !status || !prefs) {
    return <div className="flex justify-center py-12"><Loader2 className="animate-spin text-blue-600" /></div>
  }

  const tg = status.channels.telegram
  const email = status.channels.email

  return (
    <div className="space-y-6" dir="rtl">
      {/* Channel status */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
        <h3 className="font-medium flex items-center gap-2"><MessageCircle size={18} /> وضعیت کانال‌ها</h3>
        <div className="grid sm:grid-cols-2 gap-4">
          {[['telegram', 'تلگرام', tg], ['email', 'ایمیل', email]].map(([name, label, ch]: any) => (
            <div key={name} className="border rounded-lg p-4 flex items-center justify-between">
              <div>
                <div className="font-medium flex items-center gap-2">
                  {ch?.ready ? <CheckCircle2 size={16} className="text-green-600" /> : <XCircle size={16} className="text-gray-400" />}
                  {label}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {ch?.configured_via_env ? 'پیکربندی‌شده در سرور' : 'در سرور پیکربندی نشده'}
                </div>
              </div>
              <label className="inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" checked={ch?.enabled_pref ?? true}
                  onChange={() => toggleChannel(name)} disabled={!isAdmin} />
                <div className="w-11 h-6 bg-gray-200 peer-checked:bg-blue-600 rounded-full peer relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-5" />
              </label>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={test} disabled={testing || !tg?.ready}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {testing ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />} ارسال پیام تست
          </button>
          {saving && <span className="text-xs text-gray-400 flex items-center gap-1"><Loader2 size={12} className="animate-spin" /> در حال ذخیره…</span>}
        </div>
      </div>

      {/* Global options */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
        <h3 className="font-medium">گزینه‌های کلی</h3>
        <div className="flex flex-wrap items-center gap-6">
          <label className="text-sm">
            حداقل اولویت ارسال
            <select value={prefs.min_priority} disabled={!isAdmin}
              onChange={(e) => { const v = e.target.value as TelegramPrefs['min_priority']; setPrefs({ ...prefs, min_priority: v }); save({ min_priority: v }) }}
              className="mr-2 px-3 py-1.5 border rounded-lg">
              {PRIORITIES.map((p) => <option key={p} value={p}>{PRIORITY_LABEL[p]}</option>)}
            </select>
          </label>
          <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={prefs.include_buttons} disabled={!isAdmin}
              onChange={() => { setPrefs({ ...prefs, include_buttons: !prefs.include_buttons }); save({ include_buttons: !prefs.include_buttons }) }} />
            دکمه‌های لینک به پنل
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">آدرس پایهٔ پنل (برای دکمه‌های لینک)</label>
          <input type="text" value={prefs.app_base_url} disabled={!isAdmin}
            onChange={(e) => setPrefs({ ...prefs, app_base_url: e.target.value })}
            onBlur={() => save({ app_base_url: prefs.app_base_url })}
            placeholder="https://banking.example.com"
            className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100" dir="ltr" />
        </div>
      </div>

      {/* Allowed chat ids (security) */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-3">
        <h3 className="font-medium">کاربران مجاز (chat_id)</h3>
        <p className="text-xs text-gray-500">
          فقط این شناسه‌ها (به‌علاوهٔ مقدار <code>TELEGRAM_CHAT_ID</code> در سرور) می‌توانند ربات را کنترل کنند.
          برای یافتن chat_id، یک پیام به ربات بفرستید؛ اگر هنوز هیچ شناسه‌ای مجاز نباشد، ربات شناسه را برمی‌گرداند.
        </p>
        <div className="flex flex-wrap gap-2">
          {status.allowed_chat_ids.length === 0 && (
            <span className="text-xs text-amber-600">هیچ شناسهٔ مجازی تنظیم نشده — حالت راه‌اندازی فعال است.</span>
          )}
          {prefs.allowed_chat_ids.map((id) => (
            <span key={id} className="inline-flex items-center gap-1 bg-gray-100 rounded-full px-3 py-1 text-sm" dir="ltr">
              {id}
              {isAdmin && <button onClick={() => removeChatId(id)} className="text-gray-400 hover:text-red-600"><Trash2 size={13} /></button>}
            </span>
          ))}
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <input type="text" value={newChatId} onChange={(e) => setNewChatId(e.target.value)}
              placeholder="مثلاً 123456789" className="px-3 py-2 border rounded-lg text-sm" dir="ltr"
              onKeyDown={(e) => { if (e.key === 'Enter') addChatId() }} />
            <button onClick={addChatId} className="flex items-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50 text-sm">
              <Plus size={14} /> افزودن
            </button>
          </div>
        )}
      </div>

      {/* Per-event matrix */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-5">
        <h3 className="font-medium flex items-center gap-2"><Bell size={18} /> رویدادها — ارسال و صدا</h3>
        <p className="text-xs text-gray-500">برای هر رویداد مشخص کنید ارسال شود یا نه، و با صدا باشد یا بی‌صدا.</p>
        {status.event_groups.map((group) => {
          const keys = Object.keys(status.events_registry).filter((k) => status.events_registry[k].group === group.id)
          if (keys.length === 0) return null
          return (
            <div key={group.id} className="space-y-2">
              <div className="text-sm font-semibold text-gray-700 border-b pb-1">{group.icon} {group.title}</div>
              {keys.map((key) => {
                const meta = status.events_registry[key]
                const enabled = prefs.events[key]
                const sound = prefs.sound[key]
                return (
                  <div key={key} className="flex items-center justify-between gap-3 py-1.5">
                    <div className="min-w-0">
                      <div className="text-sm">{meta.label}</div>
                      <div className="text-xs text-gray-400 truncate">{meta.help}</div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button onClick={() => toggleEvent(key, 'events')} disabled={!isAdmin}
                        title={enabled ? 'ارسال فعال' : 'ارسال غیرفعال'}
                        className={`p-2 rounded-lg border ${enabled ? 'bg-blue-50 border-blue-300 text-blue-600' : 'bg-gray-50 border-gray-200 text-gray-400'}`}>
                        {enabled ? <Bell size={15} /> : <BellOff size={15} />}
                      </button>
                      <button onClick={() => toggleEvent(key, 'sound')} disabled={!isAdmin || !enabled}
                        title={sound ? 'با صدا' : 'بی‌صدا'}
                        className={`p-2 rounded-lg border ${sound && enabled ? 'bg-green-50 border-green-300 text-green-600' : 'bg-gray-50 border-gray-200 text-gray-400'}`}>
                        {sound ? <Volume2 size={15} /> : <VolumeX size={15} />}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {/* Webhook management */}
      {isAdmin && (
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-3">
          <h3 className="font-medium flex items-center gap-2"><Link2 size={18} /> وب‌هوک تلگرام</h3>
          <p className="text-xs text-gray-500">
            آدرس وب‌هوک باید به <code dir="ltr">/api/telegram/webhook</code> این سرور اشاره کند تا دستورها از تلگرام دریافت شوند.
            معمولاً در استارتاپ خودکار تنظیم می‌شود؛ این‌جا برای تنظیم دستی است.
          </p>
          <div className="flex gap-2">
            <input type="text" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://your-backend/api/telegram/webhook"
              className="flex-1 px-3 py-2 border rounded-lg text-sm" dir="ltr" />
            <button onClick={setWebhook} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Save size={15} /> تنظیم
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
