'use client'

// Schedule of Charges (تعرفهٔ شارژ تسهیلات) — the editable rule table behind the
// offer letter's automatic processing-charge calculation (term 23). Digitized
// from the bank's scanned booklet (Corporate C01-04-2025 / Individual
// P01-04-2025); the owner edits it here whenever the bank revises tariffs.
import React, { useEffect, useMemo, useState } from 'react'
import Layout from '@/components/Layout'
import { Coins, Plus, Save, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { chargeTariffApi, ChargeRule, parseApiError } from '@/lib/api'

const KEY_FA: Record<string, string> = {
  line_fee: 'کارمزد خط اعتباری (OD/CD/… بدون بخش زیر پوشش سپرده)',
  od_100fd: 'OD با پوشش ۱۰۰٪ سپردهٔ underlien',
  commercial_loan: 'وام تجاری (Processing)',
  personal_loan: 'وام شخصی (Processing)',
  temporary_od: 'تسهیلات موقت — OD',
  temporary_cd: 'تسهیلات موقت — Cheque Discount',
}
const METHOD_FA: Record<string, string> = {
  per_mille: 'به‌ازای هر ۱٬۰۰۰ (AED)',
  percent: 'درصد (٪)',
  flat: 'مبلغ ثابت (AED)',
}

const EMPTY_RULE: Partial<ChargeRule> = {
  id: '', segment: 'corporate', rule_key: 'line_fee', label: '', method: 'percent',
  rate: 0, min_charge: null, max_charge: null, small_threshold: null,
  small_min_charge: null, notes: '', version: '', enabled: true, sort_order: 0,
}

export default function ChargeTariffPage() {
  const [rules, setRules] = useState<ChargeRule[]>([])
  const [keys, setKeys] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState<Partial<ChargeRule> | null>(null)
  const [savingId, setSavingId] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const r = await chargeTariffApi.list()
      setRules(r.rules)
      setKeys(r.rule_keys)
    } catch (e) { toast.error(parseApiError(e)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const save = async (rule: Partial<ChargeRule>) => {
    setSavingId(rule.id || 'new')
    try {
      await chargeTariffApi.save(rule)
      toast.success('قاعدهٔ تعرفه ذخیره شد — محاسبهٔ خودکار افرلترها از همین لحظه با مقادیر جدید است')
      setEditing(null)
      await load()
    } catch (e) { toast.error(parseApiError(e)) } finally { setSavingId('') }
  }
  const remove = async (r: ChargeRule) => {
    if (!confirm(`قاعدهٔ «${r.label || r.rule_key}» قرنطینه شود؟ (حذفِ قطعی نیست)`)) return
    try { await chargeTariffApi.remove(r.id); await load() } catch (e) { toast.error(parseApiError(e)) }
  }

  const groups = useMemo(() => ({
    corporate: rules.filter((r) => r.segment === 'corporate'),
    individual: rules.filter((r) => r.segment === 'individual'),
  }), [rules])

  const num = (v: number | null) => (v == null ? '—' : v.toLocaleString('en-US'))

  const Editor = ({ rule }: { rule: Partial<ChargeRule> }) => {
    const [f, setF] = useState<Partial<ChargeRule>>(rule)
    const set = (k: keyof ChargeRule) => (e: any) => {
      const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value
      setF((s) => ({ ...s, [k]: v }))
    }
    const numOrNull = (v: any) => (v === '' || v == null ? null : Number(v))
    const inp = 'w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm bg-white'
    return (
      <div className="border border-blue-200 bg-blue-50/50 rounded-xl p-4 mb-4" dir="rtl">
        <div className="font-bold text-sm mb-3">{f.id ? 'ویرایش قاعده' : 'قاعدهٔ جدید'}</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <label>بخش
            <select className={inp} value={f.segment} onChange={set('segment')}>
              <option value="corporate">شرکتی (Corporate)</option>
              <option value="individual">حقیقی (Individual)</option>
            </select>
          </label>
          <label>نوع قاعده
            <select className={inp} value={f.rule_key} onChange={set('rule_key')} dir="rtl">
              {keys.map((k) => <option key={k} value={k}>{KEY_FA[k] || k}</option>)}
            </select>
          </label>
          <label>روش محاسبه
            <select className={inp} value={f.method} onChange={set('method')} dir="rtl">
              {Object.entries(METHOD_FA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </label>
          <label>نرخ / مبلغ
            <input className={inp} type="number" step="0.001" value={f.rate ?? 0} onChange={set('rate')} />
          </label>
          <label>کفِ کارمزد (Min)
            <input className={inp} type="number" value={f.min_charge ?? ''} onChange={(e) => setF((s) => ({ ...s, min_charge: numOrNull(e.target.value) }))} />
          </label>
          <label>سقفِ کارمزد (Max)
            <input className={inp} type="number" value={f.max_charge ?? ''} onChange={(e) => setF((s) => ({ ...s, max_charge: numOrNull(e.target.value) }))} />
          </label>
          <label>آستانهٔ مبلغِ کوچک
            <input className={inp} type="number" placeholder="مثلاً 10000" value={f.small_threshold ?? ''} onChange={(e) => setF((s) => ({ ...s, small_threshold: numOrNull(e.target.value) }))} />
          </label>
          <label>کفِ کارمزد برای مبلغ کوچک
            <input className={inp} type="number" placeholder="مثلاً 200" value={f.small_min_charge ?? ''} onChange={(e) => setF((s) => ({ ...s, small_min_charge: numOrNull(e.target.value) }))} />
          </label>
          <label className="col-span-2">عنوان (نمایش)
            <input className={inp} value={f.label ?? ''} onChange={set('label')} />
          </label>
          <label>نسخهٔ بولتن
            <input className={inp} placeholder="C01-04-2025" value={f.version ?? ''} onChange={set('version')} dir="ltr" />
          </label>
          <label className="flex items-end gap-2 pb-1">
            <input type="checkbox" checked={!!f.enabled} onChange={set('enabled')} /> فعال
          </label>
          <label className="col-span-2 md:col-span-4">متن/شرط تعرفه (عین بولتن)
            <textarea className={inp} rows={2} value={f.notes ?? ''} onChange={set('notes')} dir="ltr" />
          </label>
        </div>
        <div className="flex gap-2 mt-3">
          <button onClick={() => save({ ...f, rate: Number(f.rate) || 0, sort_order: Number(f.sort_order) || 0 })}
            disabled={savingId !== ''}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md px-4 py-1.5 text-sm">
            <Save size={14} /> ذخیره
          </button>
          <button onClick={() => setEditing(null)} className="border border-gray-300 rounded-md px-4 py-1.5 text-sm bg-white">انصراف</button>
        </div>
      </div>
    )
  }

  const Table = ({ title, rows }: { title: string; rows: ChargeRule[] }) => (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
      <div className="font-bold text-sm mb-2" dir="rtl">{title}</div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs" dir="rtl">
          <thead>
            <tr className="text-gray-500 border-b">
              <th className="text-right py-1.5 px-2">قاعده</th>
              <th className="text-right px-2">روش</th>
              <th className="px-2">نرخ</th>
              <th className="px-2">کف</th>
              <th className="px-2">سقف</th>
              <th className="px-2">مبلغ کوچک</th>
              <th className="px-2">نسخه</th>
              <th className="px-2">فعال</th>
              <th className="px-2"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={`border-b last:border-0 ${r.enabled ? '' : 'opacity-45'}`}>
                <td className="py-2 px-2">
                  <div className="font-medium">{r.label || KEY_FA[r.rule_key] || r.rule_key}</div>
                  {r.notes && <div className="text-gray-400 text-[10px] mt-0.5" dir="ltr">{r.notes}</div>}
                </td>
                <td className="px-2 whitespace-nowrap">{METHOD_FA[r.method] || r.method}</td>
                <td className="px-2 text-center font-mono" dir="ltr">{r.rate}</td>
                <td className="px-2 text-center" dir="ltr">{num(r.min_charge)}</td>
                <td className="px-2 text-center" dir="ltr">{num(r.max_charge)}</td>
                <td className="px-2 text-center" dir="ltr">{r.small_threshold != null ? `≤${num(r.small_threshold)} → ${num(r.small_min_charge)}` : '—'}</td>
                <td className="px-2 text-center" dir="ltr">{r.version || '—'}</td>
                <td className="px-2 text-center">{r.enabled ? '✓' : '—'}</td>
                <td className="px-2 whitespace-nowrap text-left">
                  <button onClick={() => setEditing(r)} className="text-blue-600 hover:underline ml-2">ویرایش</button>
                  <button onClick={() => remove(r)} className="text-red-500 hover:text-red-700"><Trash2 size={13} /></button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={9} className="py-4 text-center text-gray-400">قاعده‌ای نیست</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-4" dir="rtl">
          <div className="flex items-center gap-2">
            <div className="bg-amber-500 text-white rounded-lg p-2"><Coins size={18} /></div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">تعرفهٔ شارژ تسهیلات (Schedule of Charges)</h1>
              <p className="text-gray-500 text-xs">
                مرجعِ محاسبهٔ خودکارِ کارمزدِ پردازش در افرلتر (بند ۲۳). با هر بازنگریِ سالانه/دوره‌ایِ بانک، همین‌جا مقادیر را ویرایش کن —
                تسهیلاتِ کارمندی خودکار معاف است و پوششِ ۱۰۰٪ سپرده (underlien) قاعدهٔ خودش را دارد. همهٔ مبالغ بدونِ VAT.
              </p>
            </div>
          </div>
          <button onClick={() => setEditing({ ...EMPTY_RULE })}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-2 text-sm">
            <Plus size={15} /> قاعدهٔ جدید
          </button>
        </div>

        {editing && <Editor rule={editing} />}
        {loading ? <p className="text-gray-400 text-sm">در حال بارگیری…</p> : (
          <>
            <Table title={`مشتریان شرکتی — Corporate (${groups.corporate[0]?.version || 'C01-04-2025'})`} rows={groups.corporate} />
            <Table title={`مشتریان حقیقی — Individual (${groups.individual[0]?.version || 'P01-04-2025'})`} rows={groups.individual} />
          </>
        )}
      </div>
    </Layout>
  )
}
