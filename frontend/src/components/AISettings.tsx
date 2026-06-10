'use client'

/**
 * AI models & providers — the Settings section for the AI control layer.
 *
 * This is the single place to control which AI providers/models the panel may
 * use and where each one is wired in:
 *   • Providers — enable a provider and paste its API key (kept server-side).
 *   • Models    — toggle individual models, see their capabilities, add custom ones.
 *   • Task routing — point each application task at a specific model (or "Auto").
 *
 * Nothing here calls a provider. The backend resolves a task to the configured
 * model on demand, so future AI features wire to a task id rather than a model.
 */

import { useEffect, useState } from 'react'
import { aiApi, parseApiError } from '@/lib/api'
import { AIOverview, AIModel } from '@/types'
import {
  Bot, Save, Plus, Trash2, Check, X, KeyRound, Cpu, Workflow, AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'

const emptyCustom = {
  provider_key: '',
  model_key: '',
  display_name: '',
  capabilities: [] as string[],
}

export default function AISettings({ isAdmin }: { isAdmin: boolean }) {
  const [data, setData] = useState<AIOverview | null>(null)
  const [loading, setLoading] = useState(true)
  // Per-provider local edits (api key + base url) keyed by provider key.
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({})
  const [urlDrafts, setUrlDrafts] = useState<Record<string, string>>({})
  const [savingProvider, setSavingProvider] = useState<string | null>(null)
  const [showCustom, setShowCustom] = useState(false)
  const [custom, setCustom] = useState(emptyCustom)
  const [savingCustom, setSavingCustom] = useState(false)

  const load = async () => {
    try {
      setLoading(true)
      const res = await aiApi.overview()
      setData(res)
      const urls: Record<string, string> = {}
      res.providers.forEach((p) => { urls[p.key] = p.base_url ?? '' })
      setUrlDrafts(urls)
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() /* eslint-disable-next-line */ }, [])

  const capLabel = (id: string) => data?.capabilities.find((c) => c.id === id)?.label ?? id

  const saveProvider = async (key: string, patch: { enabled?: boolean; api_key?: string; base_url?: string }) => {
    setSavingProvider(key)
    try {
      await aiApi.updateProvider(key, patch)
      toast.success('Provider updated')
      // Clear the secret draft once saved.
      if (patch.api_key !== undefined) setKeyDrafts((d) => ({ ...d, [key]: '' }))
      await load()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSavingProvider(null)
    }
  }

  const toggleModel = async (m: AIModel, enabled: boolean) => {
    try {
      await aiApi.updateModel(m.id, { enabled })
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const deleteModel = async (m: AIModel) => {
    if (!confirm(`Delete custom model "${m.display_name}"?`)) return
    try {
      await aiApi.deleteModel(m.id)
      toast.success('Model deleted')
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const setRoute = async (task: string, modelId: number | null) => {
    try {
      await aiApi.updateRoute(task, { model_id: modelId })
      await load()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  const addCustom = async () => {
    if (!custom.provider_key || !custom.model_key) {
      toast.error('Pick a provider and enter a model id')
      return
    }
    setSavingCustom(true)
    try {
      await aiApi.createModel({
        provider_key: custom.provider_key,
        model_key: custom.model_key.trim(),
        display_name: custom.display_name.trim() || undefined,
        capabilities: custom.capabilities,
      })
      toast.success('Custom model added')
      setCustom(emptyCustom)
      setShowCustom(false)
      await load()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSavingCustom(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4"><Bot size={16} /><h3 className="font-medium">AI models &amp; providers</h3></div>
        <div className="animate-pulse h-24 bg-gray-100 rounded" />
      </div>
    )
  }
  if (!data) return null

  const st = data.status

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center gap-2"><Bot size={18} className="text-blue-600" /> AI models &amp; providers</h3>
        <span
          className={`text-xs px-2 py-1 rounded-full ${st.any_available ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}
        >
          {st.any_available
            ? `${st.usable_model_count} model(s) ready · ${st.configured_providers.length} provider(s)`
            : 'No provider configured yet'}
        </span>
      </div>
      <p className="text-sm text-gray-500">
        مرکز کنترل مدل‌های هوش مصنوعی. هر جای برنامه که از مدل استفاده می‌شود از همین‌جا ریشه می‌گیرد — اینجا
        پروایدر را فعال کنید و کلید بدهید، مدل‌ها را روشن/خاموش کنید، و هر «کار» را به یک مدل وصل کنید.
        {!isAdmin && <span className="flex items-center gap-1 mt-1 text-amber-600"><AlertTriangle size={13} /> فقط مدیر می‌تواند تغییر دهد.</span>}
      </p>

      {/* ---------------- Providers ---------------- */}
      <section>
        <h4 className="text-sm font-semibold flex items-center gap-2 mb-3 text-gray-700"><KeyRound size={15} /> Providers</h4>
        <div className="space-y-3">
          {data.providers.map((p) => (
            <div key={p.key} className="border rounded-lg p-4">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{p.display_name}</span>
                  {p.configured ? (
                    <span className="text-xs text-green-600 flex items-center gap-0.5"><Check size={13} /> configured</span>
                  ) : (
                    <span className="text-xs text-gray-400 flex items-center gap-0.5"><X size={13} /> no key</span>
                  )}
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={p.enabled}
                    disabled={!isAdmin || savingProvider === p.key}
                    onChange={(e) => saveProvider(p.key, { enabled: e.target.checked })}
                    className="h-4 w-4"
                  />
                  Enabled
                </label>
              </div>
              {p.notes && <p className="text-xs text-gray-400 mt-1">{p.notes}</p>}

              {isAdmin && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      API key {p.env_key && <span className="text-gray-400">(env: {p.env_key})</span>}
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder={p.has_api_key ? (p.api_key_masked ?? '••••') : 'Paste API key…'}
                        value={keyDrafts[p.key] ?? ''}
                        onChange={(e) => setKeyDrafts((d) => ({ ...d, [p.key]: e.target.value }))}
                        className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      />
                      <button
                        type="button"
                        disabled={savingProvider === p.key || (keyDrafts[p.key] ?? '') === ''}
                        onClick={() => saveProvider(p.key, { api_key: keyDrafts[p.key] })}
                        className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 text-sm flex items-center gap-1"
                      >
                        <Save size={14} /> Save
                      </button>
                      {p.has_api_key && (
                        <button
                          type="button"
                          disabled={savingProvider === p.key}
                          onClick={() => saveProvider(p.key, { api_key: '' })}
                          className="px-3 py-2 border rounded-lg text-sm text-red-600 hover:bg-red-50"
                          title="Clear stored key"
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Base URL override (optional)</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="default"
                        value={urlDrafts[p.key] ?? ''}
                        onChange={(e) => setUrlDrafts((d) => ({ ...d, [p.key]: e.target.value }))}
                        className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      />
                      <button
                        type="button"
                        disabled={savingProvider === p.key}
                        onClick={() => saveProvider(p.key, { base_url: urlDrafts[p.key] ?? '' })}
                        className="px-3 py-2 border rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1"
                      >
                        <Save size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- Models ---------------- */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700"><Cpu size={15} /> Models</h4>
          {isAdmin && (
            <button
              type="button"
              onClick={() => setShowCustom((s) => !s)}
              className="text-sm text-blue-600 hover:underline flex items-center gap-1"
            >
              <Plus size={14} /> Add custom model
            </button>
          )}
        </div>

        {showCustom && isAdmin && (
          <div className="border rounded-lg p-4 mb-3 bg-gray-50 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <select
                value={custom.provider_key}
                onChange={(e) => setCustom((c) => ({ ...c, provider_key: e.target.value }))}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="">Provider…</option>
                {data.providers.map((p) => <option key={p.key} value={p.key}>{p.display_name}</option>)}
              </select>
              <input
                placeholder="Model id (e.g. gpt-4.1)"
                value={custom.model_key}
                onChange={(e) => setCustom((c) => ({ ...c, model_key: e.target.value }))}
                className="px-3 py-2 border rounded-lg text-sm"
              />
              <input
                placeholder="Display name (optional)"
                value={custom.display_name}
                onChange={(e) => setCustom((c) => ({ ...c, display_name: e.target.value }))}
                className="px-3 py-2 border rounded-lg text-sm"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {data.capabilities.map((c) => {
                const on = custom.capabilities.includes(c.id)
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setCustom((cur) => ({
                      ...cur,
                      capabilities: on ? cur.capabilities.filter((x) => x !== c.id) : [...cur.capabilities, c.id],
                    }))}
                    className={`text-xs px-2 py-1 rounded-full border ${on ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600'}`}
                  >
                    {c.label}
                  </button>
                )
              })}
            </div>
            <div className="flex gap-2">
              <button
                type="button" disabled={savingCustom} onClick={addCustom}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-1"
              >
                <Plus size={14} /> {savingCustom ? 'Adding…' : 'Add model'}
              </button>
              <button type="button" onClick={() => { setShowCustom(false); setCustom(emptyCustom) }} className="px-3 py-2 border rounded-lg text-sm">Cancel</button>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 text-xs border-b">
                <th className="py-2 pr-2">Model</th>
                <th className="py-2 px-2">Provider</th>
                <th className="py-2 px-2">Capabilities</th>
                <th className="py-2 px-2 text-center">Enabled</th>
                {isAdmin && <th className="py-2 pl-2"></th>}
              </tr>
            </thead>
            <tbody>
              {data.models.map((m) => (
                <tr key={m.id} className="border-b last:border-0">
                  <td className="py-2 pr-2">
                    <div className="font-medium">{m.display_name}</div>
                    <div className="text-xs text-gray-400 font-mono">{m.model_key}{m.is_custom && ' · custom'}</div>
                  </td>
                  <td className="py-2 px-2 text-gray-500">{m.provider_key}</td>
                  <td className="py-2 px-2">
                    <div className="flex flex-wrap gap-1">
                      {m.capabilities.map((c) => (
                        <span key={c} className="text-[11px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">{capLabel(c)}</span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <input
                      type="checkbox"
                      checked={m.enabled}
                      disabled={!isAdmin}
                      onChange={(e) => toggleModel(m, e.target.checked)}
                      className="h-4 w-4"
                    />
                  </td>
                  {isAdmin && (
                    <td className="py-2 pl-2 text-right">
                      {m.is_custom && (
                        <button type="button" onClick={() => deleteModel(m)} className="text-red-500 hover:text-red-700" title="Delete custom model">
                          <Trash2 size={15} />
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ---------------- Task routing ---------------- */}
      <section>
        <h4 className="text-sm font-semibold flex items-center gap-2 mb-1 text-gray-700"><Workflow size={15} /> Task routing</h4>
        <p className="text-xs text-gray-400 mb-3">
          هر کارِ برنامه را به یک مدل وصل کنید. «Auto» یعنی بهترین مدلِ فعال و مناسبِ آن کار به‌صورت خودکار انتخاب شود.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {data.tasks.map((t) => {
            const route = data.routes.find((r) => r.task === t.id)
            return (
              <div key={t.id} className="border rounded-lg p-3">
                <div className="font-medium text-sm">{t.label}</div>
                <div className="text-xs text-gray-400 mb-2">{t.description}</div>
                <select
                  value={route?.model_id ?? ''}
                  disabled={!isAdmin}
                  onChange={(e) => setRoute(t.id, e.target.value ? Number(e.target.value) : null)}
                  className="w-full px-2 py-1.5 border rounded-lg text-sm disabled:bg-gray-100"
                >
                  <option value="">Auto (best for: {capLabel(t.preferred)})</option>
                  {data.models.filter((m) => m.enabled).map((m) => (
                    <option key={m.id} value={m.id}>{m.display_name}</option>
                  ))}
                </select>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
