'use client'

import { useEffect, useState, useCallback } from 'react'
import Layout from '@/components/Layout'
import { staffApi, parseApiError } from '@/lib/api'
import { StaffMember } from '@/types'
import { Contact, Search, Plus, Pencil, Trash2, X, Save } from 'lucide-react'
import toast from 'react-hot-toast'

const REGIONS = ['Persian Gulf', 'Iran']
const BLANK: Partial<StaffMember> = { name: '', name_fa: '', department: '', title: '', telephone: '', ext: '', fax: '', email: '', mobile: '', region: 'Persian Gulf', notes: '' }

export default function StaffDirectoryPage() {
  const [rows, setRows] = useState<StaffMember[]>([])
  const [depts, setDepts] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [region, setRegion] = useState('')
  const [dept, setDept] = useState('')
  const [form, setForm] = useState<Partial<StaffMember> | null>(null) // open modal when not null
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setRows((await staffApi.list({ q: q || undefined, region: region || undefined, department: dept || undefined })).items) }
    catch (e) { toast.error(parseApiError(e)) }
    finally { setLoading(false) }
  }, [q, region, dept])

  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [load])
  useEffect(() => { staffApi.departments(region || undefined).then(setDepts).catch(() => setDepts([])) }, [region])

  const upd = (k: keyof StaffMember) => (e: any) => setForm((s) => ({ ...(s || {}), [k]: e.target.value }))

  const save = async () => {
    if (!form) return
    if (!(form.name || '').trim()) { toast.error('نام (انگلیسی) لازم است'); return }
    setSaving(true)
    try {
      if (form.id) await staffApi.update(form.id, form)
      else await staffApi.create(form)
      toast.success('ذخیره شد')
      setForm(null)
      load()
    } catch (e) { toast.error(parseApiError(e)) } finally { setSaving(false) }
  }

  const del = async (s: StaffMember) => {
    if (!confirm(`حذفِ «${s.name}»؟`)) return
    try { await staffApi.remove(s.id); toast.success('حذف شد'); setRows((r) => r.filter((x) => x.id !== s.id)) }
    catch (e) { toast.error(parseApiError(e)) }
  }

  return (
    <Layout>
      <div dir="rtl" className="max-w-full">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><Contact size={22} /></div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">دفترچۀ کارکنان (Staff Directory)</h1>
            <p className="text-gray-500 text-sm">اسامیِ کارمندان، اداره، تلفن/داخلی، فکس و ایمیل. هر فیلد قابلِ ویرایش است (افراد جابه‌جا یا حذف می‌شوند). «نام فارسی» را هم می‌توانید ثبت کنید تا بدونِ غلطِ املایی استفاده شود.</p>
          </div>
          <button onClick={() => setForm({ ...BLANK })} className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 text-sm whitespace-nowrap"><Plus size={16} /> افزودنِ کارمند</button>
        </div>

        <div className="flex flex-wrap gap-2 my-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search size={15} className="absolute right-2 top-2.5 text-gray-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="جستجو در نام / نام فارسی / اداره / ایمیل / داخلی…"
              className="w-full pr-8 pl-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <select value={region} onChange={(e) => setRegion(e.target.value)} className="px-3 py-2 border rounded-lg text-sm">
            <option value="">همۀ مناطق</option>
            {REGIONS.map((r) => <option key={r} value={r}>{r === 'Persian Gulf' ? 'منطقه خلیج فارس' : 'ایران'}</option>)}
          </select>
          <select value={dept} onChange={(e) => setDept(e.target.value)} className="px-3 py-2 border rounded-lg text-sm max-w-[260px]">
            <option value="">همۀ ادارات</option>
            {depts.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>

        <div className="bg-white border rounded-lg overflow-hidden">
          {loading ? (
            <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>
          ) : rows.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm whitespace-nowrap">
                <thead className="bg-gray-50 text-gray-500">
                  <tr>
                    <th className="px-3 py-2 text-right">نام (EN)</th>
                    <th className="px-3 py-2 text-right">نام فارسی</th>
                    <th className="px-3 py-2 text-right">اداره</th>
                    <th className="px-3 py-2 text-right">سمت</th>
                    <th className="px-3 py-2 text-center">تلفن</th>
                    <th className="px-3 py-2 text-center">داخلی</th>
                    <th className="px-3 py-2 text-center">فکس</th>
                    <th className="px-3 py-2 text-left">ایمیل</th>
                    <th className="px-3 py-2 text-center">موبایل</th>
                    <th className="px-3 py-2 text-center"> </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {rows.map((s) => (
                    <tr key={s.id} className="hover:bg-blue-50/40">
                      <td className="px-3 py-1.5 font-medium" dir="ltr">{s.name}</td>
                      <td className="px-3 py-1.5">{s.name_fa || <span className="text-gray-300">—</span>}</td>
                      <td className="px-3 py-1.5 text-gray-700">{s.department || '—'}</td>
                      <td className="px-3 py-1.5 text-gray-600">{s.title || '—'}</td>
                      <td className="px-3 py-1.5 text-center tabular-nums" dir="ltr">{s.telephone || '—'}</td>
                      <td className="px-3 py-1.5 text-center tabular-nums" dir="ltr">{s.ext || '—'}</td>
                      <td className="px-3 py-1.5 text-center tabular-nums" dir="ltr">{s.fax || '—'}</td>
                      <td className="px-3 py-1.5 text-left text-blue-700" dir="ltr">{s.email || '—'}</td>
                      <td className="px-3 py-1.5 text-center tabular-nums" dir="ltr">{s.mobile || '—'}</td>
                      <td className="px-3 py-1.5">
                        <div className="flex items-center gap-1 justify-center">
                          <button onClick={() => setForm({ ...s })} title="ویرایش" className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"><Pencil size={15} /></button>
                          <button onClick={() => del(s)} title="حذف" className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"><Trash2 size={15} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-12 text-center text-gray-500 text-sm">موردی یافت نشد</div>
          )}
        </div>
        {!loading && <p className="text-xs text-gray-400 mt-2">{rows.length} نفر</p>}

        {/* Add / Edit modal */}
        {form && (
          <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center overflow-auto p-4" onClick={() => setForm(null)}>
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mt-10" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between border-b px-5 py-3">
                <h3 className="font-bold text-gray-900">{form.id ? 'ویرایشِ کارمند' : 'افزودنِ کارمند'}</h3>
                <button onClick={() => setForm(null)} className="p-1 text-gray-400 hover:text-gray-700"><X size={20} /></button>
              </div>
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3" dir="rtl">
                <Field label="نام (انگلیسی) *"><input dir="ltr" value={form.name || ''} onChange={upd('name')} className="fld" placeholder="Ali Reza" /></Field>
                <Field label="نام فارسی"><input value={form.name_fa || ''} onChange={upd('name_fa')} className="fld" placeholder="علی‌رضا" /></Field>
                <Field label="اداره / شعبه"><input value={form.department || ''} onChange={upd('department')} className="fld" placeholder="Credit Facility Dept." /></Field>
                <Field label="سمت"><input value={form.title || ''} onChange={upd('title')} className="fld" placeholder="رئیس اداره / Officer" /></Field>
                <Field label="تلفن"><input dir="ltr" value={form.telephone || ''} onChange={upd('telephone')} className="fld" /></Field>
                <Field label="داخلی"><input dir="ltr" value={form.ext || ''} onChange={upd('ext')} className="fld" /></Field>
                <Field label="فکس"><input dir="ltr" value={form.fax || ''} onChange={upd('fax')} className="fld" /></Field>
                <Field label="ایمیل"><input dir="ltr" value={form.email || ''} onChange={upd('email')} className="fld" placeholder="name@bsi.co.ae" /></Field>
                <Field label="موبایل"><input dir="ltr" value={form.mobile || ''} onChange={upd('mobile')} className="fld" /></Field>
                <Field label="منطقه">
                  <select value={form.region || 'Persian Gulf'} onChange={upd('region')} className="fld">
                    {REGIONS.map((r) => <option key={r} value={r}>{r === 'Persian Gulf' ? 'منطقه خلیج فارس' : 'ایران'}</option>)}
                  </select>
                </Field>
                <div className="sm:col-span-2"><Field label="یادداشت"><textarea value={form.notes || ''} onChange={upd('notes')} className="fld" rows={2} /></Field></div>
              </div>
              <div className="flex justify-end gap-2 border-t px-5 py-3">
                <button onClick={() => setForm(null)} className="px-4 py-2 border rounded-lg text-sm">انصراف</button>
                <button onClick={save} disabled={saving} className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-lg px-4 py-2 text-sm"><Save size={15} /> {saving ? '...' : 'ذخیره'}</button>
              </div>
            </div>
          </div>
        )}
        <style>{`.fld{width:100%;border:1px solid #cbd5e1;border-radius:8px;padding:6px 10px;font-size:14px}.fld:focus{outline:none;border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.2)}`}</style>
      </div>
    </Layout>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs text-gray-500 mb-1">{label}</span>
      {children}
    </label>
  )
}
