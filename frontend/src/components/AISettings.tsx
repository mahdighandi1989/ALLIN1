'use client'

/**
 * AI models & providers — the Settings tab for the AI control layer.
 *
 * Layout is provider-centric so the hierarchy is obvious:
 *   Provider (enable + API key)
 *     └─ its Models (toggle, capabilities, add custom)
 *   Task routing  — point each application task at a model (or "Auto").
 *
 * Nothing here calls a provider. The backend resolves a task to the configured
 * model on demand, so future AI features wire to a task id rather than a model.
 */

import { useEffect, useState } from 'react'
import { aiApi, parseApiError } from '@/lib/api'
import { AIOverview, AIModel, AIProvider } from '@/types'
import {
  Bot, Save, Plus, Trash2, Check, X, Workflow, AlertTriangle, ChevronRight,
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function AISettings({ isAdmin }: { isAdmin: boolean }) {
  const [data, setData] = useState<AIOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({})
  const [urlDrafts, setUrlDrafts] = useState<Record<string, string>>({})
  const [savingProvider, setSavingProvider] = useState<string | null>(null)
  // Inline "add custom model" form, scoped to one provider key.
  const [addingFor, setAddingFor] = useState<string | null>(null)
  const [draft, setDraft] = useState({ model_key: '', display_name: '', capabilities: [] as string[] })
  const [savingModel, setSavingModel] = useState(false)

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
      if (patch.api_key !== undefined) setKeyDrafts((d) => ({ ...d, [key]: '' }))
      await load()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSavingProvider(null)
    }
  }

  const toggleModel = async (m: AIModel, enabled: boolean) => {
    try { await aiApi.updateModel(m.id, { enabled }); await load() }
    catch (e) { toast.error(parseApiError(e)) }
  }

  const deleteModel = async (m: AIModel) => {
    if (!confirm(`Delete custom model "${m.display_name}"?`)) return
    try { await aiApi.deleteModel(m.id); toast.success('Model deleted'); await load() }
    catch (e) { toast.error(parseApiError(e)) }
  }

  const setRoute = async (task: string, modelId: number | null) => {
    try { await aiApi.updateRoute(task, { model_id: modelId }); await load() }
    catch (e) { toast.error(parseApiError(e)) }
  }

  const openAdd = (providerKey: string) => {
    setAddingFor(providerKey)
    setDraft({ model_key: '', display_name: '', capabilities: [] })
  }

  const addModel = async (providerKey: string) => {
    if (!draft.model_key.trim()) { toast.error('Enter a model id'); return }
    setSavingModel(true)
    try {
      await aiApi.createModel({
        provider_key: providerKey,
        model_key: draft.model_key.trim(),
        display_name: draft.display_name.trim() || undefined,
        capabilities: draft.capabilities,
      })
      toast.success('Custom model added')
      setAddingFor(null)
      await load()
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setSavingModel(false)
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
    <div className="space-y-6">
      {/* Intro / status */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h3 className="font-medium flex items-center gap-2">
            <Bot size={18} className="text-blue-600" /> AI models &amp; providers
          </h3>
          <span className={`text-xs px-2.5 py-1 rounded-full ${st.any_available ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
            {st.any_available
              ? `${st.usable_model_count} model(s) ready · ${st.configured_providers.length} provider(s) configured`
              : 'No provider configured yet'}
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-2 leading-relaxed">
          مرکز کنترل مدل‌های هوش مصنوعی. هر جای برنامه که از مدل استفاده می‌شود از همین‌جا ریشه می‌گیرد.
          برای هر پروایدر کلید را بدهید و فعالش کنید، مدل‌های دلخواه را روشن/خاموش کنید، و در پایین هر «کار»
          را به یک مدل وصل کنید.
          {!isAdmin && <span className="flex items-center gap-1 mt-1 text-amber-600"><AlertTriangle size={13} /> فقط مدیر می‌تواند تغییر دهد.</span>}
        </p>
      </div>

      {/* Providers — each card holds the provider config + its own models */}
      {data.providers.map((p) => {
        const models = data.models.filter((m) => m.provider_key === p.key)
        return (
          <ProviderCard
            key={p.key}
            provider={p}
            models={models}
            isAdmin={isAdmin}
            saving={savingProvider === p.key}
            keyDraft={keyDrafts[p.key] ?? ''}
            urlDraft={urlDrafts[p.key] ?? ''}
            onKeyDraft={(v) => setKeyDrafts((d) => ({ ...d, [p.key]: v }))}
            onUrlDraft={(v) => setUrlDrafts((d) => ({ ...d, [p.key]: v }))}
            onSave={(patch) => saveProvider(p.key, patch)}
            capLabel={capLabel}
            onToggleModel={toggleModel}
            onDeleteModel={deleteModel}
            adding={addingFor === p.key}
            draft={draft}
            setDraft={setDraft}
            savingModel={savingModel}
            onOpenAdd={() => openAdd(p.key)}
            onCancelAdd={() => setAddingFor(null)}
            onAddModel={() => addModel(p.key)}
            capabilities={data.capabilities}
          />
        )
      })}

      {/* Task routing */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h4 className="text-sm font-semibold flex items-center gap-2 mb-1 text-gray-700"><Workflow size={16} /> Task routing</h4>
        <p className="text-xs text-gray-400 mb-4">
          هر کارِ برنامه را به یک مدل وصل کنید. «Auto» یعنی بهترین مدلِ فعالِ مناسبِ آن کار به‌صورت خودکار انتخاب شود.
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
                  <option value="">Auto — best for {capLabel(t.preferred)}</option>
                  {data.models.filter((m) => m.enabled).map((m) => (
                    <option key={m.id} value={m.id}>{m.display_name} ({m.provider_key})</option>
                  ))}
                </select>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// One provider, with its key config and the models that belong to it.
// ---------------------------------------------------------------------------
function ProviderCard(props: {
  provider: AIProvider
  models: AIModel[]
  isAdmin: boolean
  saving: boolean
  keyDraft: string
  urlDraft: string
  onKeyDraft: (v: string) => void
  onUrlDraft: (v: string) => void
  onSave: (patch: { enabled?: boolean; api_key?: string; base_url?: string }) => void
  capLabel: (id: string) => string
  onToggleModel: (m: AIModel, enabled: boolean) => void
  onDeleteModel: (m: AIModel) => void
  adding: boolean
  draft: { model_key: string; display_name: string; capabilities: string[] }
  setDraft: (d: { model_key: string; display_name: string; capabilities: string[] }) => void
  savingModel: boolean
  onOpenAdd: () => void
  onCancelAdd: () => void
  onAddModel: () => void
  capabilities: { id: string; label: string }[]
}) {
  const {
    provider: p, models, isAdmin, saving, keyDraft, urlDraft, onKeyDraft, onUrlDraft, onSave,
    capLabel, onToggleModel, onDeleteModel, adding, draft, setDraft, savingModel,
    onOpenAdd, onCancelAdd, onAddModel, capabilities,
  } = props

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Header + config */}
      <div className={`p-5 ${p.enabled ? 'bg-blue-50/40' : 'bg-gray-50'} border-b`}>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{p.display_name}</span>
            {p.notes?.startsWith('Recommended') && (
              <span className="text-[11px] px-1.5 py-0.5 bg-blue-600 text-white rounded">Recommended</span>
            )}
            {p.configured ? (
              <span className="text-xs text-green-600 flex items-center gap-0.5"><Check size={13} /> key set</span>
            ) : (
              <span className="text-xs text-gray-400 flex items-center gap-0.5"><X size={13} /> no key</span>
            )}
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <span className={p.enabled ? 'text-blue-700 font-medium' : 'text-gray-500'}>
              {p.enabled ? 'Enabled' : 'Disabled'}
            </span>
            <input
              type="checkbox"
              checked={p.enabled}
              disabled={!isAdmin || saving}
              onChange={(e) => onSave({ enabled: e.target.checked })}
              className="h-4 w-4"
            />
          </label>
        </div>
        {p.notes && <p className="text-xs text-gray-400 mt-1">{p.notes}</p>}

        {isAdmin && (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                API key {p.env_key && <span className="text-gray-400">· falls back to env {p.env_key}</span>}
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  placeholder={p.has_api_key ? (p.api_key_masked ?? '••••') : 'Paste API key…'}
                  value={keyDraft}
                  onChange={(e) => onKeyDraft(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg text-sm bg-white"
                />
                <button
                  type="button"
                  disabled={saving || keyDraft === ''}
                  onClick={() => onSave({ api_key: keyDraft })}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 text-sm flex items-center gap-1"
                >
                  <Save size={14} /> Save
                </button>
                {p.has_api_key && (
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => onSave({ api_key: '' })}
                    className="px-3 py-2 border rounded-lg text-sm text-red-600 hover:bg-red-50 bg-white"
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
                  value={urlDraft}
                  onChange={(e) => onUrlDraft(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg text-sm bg-white"
                />
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => onSave({ base_url: urlDraft })}
                  className="px-3 py-2 border rounded-lg text-sm hover:bg-gray-50 bg-white flex items-center gap-1"
                >
                  <Save size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Models belonging to this provider */}
      <div className="p-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Models</span>
          {isAdmin && !adding && (
            <button type="button" onClick={onOpenAdd} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
              <Plus size={13} /> Add custom model
            </button>
          )}
        </div>

        {models.length === 0 && !adding && (
          <p className="text-sm text-gray-400 py-2">
            No preset models. {isAdmin ? 'Add the ones you want with “Add custom model”.' : ''}
          </p>
        )}

        <div className="divide-y">
          {models.map((m) => (
            <div key={m.id} className="flex items-start gap-3 py-2.5">
              <input
                type="checkbox"
                checked={m.enabled}
                disabled={!isAdmin}
                onChange={(e) => onToggleModel(m, e.target.checked)}
                className="h-4 w-4 mt-1 shrink-0"
                title={m.enabled ? 'Enabled' : 'Disabled'}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium flex items-center gap-2 flex-wrap">
                  {m.display_name}
                  <span className="text-[11px] font-mono text-gray-400">{m.model_key}</span>
                  {m.is_custom && <span className="text-[10px] px-1 py-0.5 bg-gray-100 text-gray-500 rounded">custom</span>}
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {m.capabilities.map((c) => (
                    <span key={c} className="text-[11px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">{capLabel(c)}</span>
                  ))}
                </div>
              </div>
              {isAdmin && m.is_custom && (
                <button type="button" onClick={() => onDeleteModel(m)} className="text-red-500 hover:text-red-700 mt-1 shrink-0" title="Delete custom model">
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Inline add form */}
        {adding && isAdmin && (
          <div className="mt-3 border rounded-lg p-3 bg-gray-50 space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                placeholder="Model id (e.g. gpt-4.1)"
                value={draft.model_key}
                onChange={(e) => setDraft({ ...draft, model_key: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              />
              <input
                placeholder="Display name (optional)"
                value={draft.display_name}
                onChange={(e) => setDraft({ ...draft, display_name: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {capabilities.map((c) => {
                const on = draft.capabilities.includes(c.id)
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setDraft({
                      ...draft,
                      capabilities: on ? draft.capabilities.filter((x) => x !== c.id) : [...draft.capabilities, c.id],
                    })}
                    className={`text-xs px-2 py-1 rounded-full border ${on ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-600'}`}
                  >
                    {c.label}
                  </button>
                )
              })}
            </div>
            <div className="flex gap-2">
              <button
                type="button" disabled={savingModel} onClick={onAddModel}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-1"
              >
                <ChevronRight size={14} /> {savingModel ? 'Adding…' : `Add to ${p.display_name}`}
              </button>
              <button type="button" onClick={onCancelAdd} className="px-3 py-2 border rounded-lg text-sm bg-white">Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
