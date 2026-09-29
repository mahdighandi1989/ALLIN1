'use client'

// گزارش خلاصهٔ پروندهٔ حقوقی — the legal case-file summary report.
//
// The branch's comprehensive report to the Legal & Debt-Recovery department on a
// non-performing account. It is a FIXED 11-section document (see ./sections.ts)
// printed on the bank's letterhead across as many A4 pages as it needs, with the
// header/footer repeated and pages numbered — the same paper the owner supplied
// as a blank PDF template and a filled Word sample.
//
// It deliberately carries the SAME capabilities the official letters carry, because
// that is what the owner asked for: saved under an account or as a general report,
// listed and reopened, edited, attachments, print, Word export, audit trail and a
// recoverable (soft) delete. What it adds is «پیش‌نویس از دیتابیس»: the partners,
// facilities and collateral the database already holds are offered instead of typed
// again, because typing them twice is how the report and the profile drift apart.
//
// 794×1123 px = 210×297 mm @96dpi → prints 1:1.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Layout from '@/components/Layout'
import {
  Download, FilePlus, Loader2, Paperclip, Plus, Printer, RotateCcw, Save, Trash2, Wand2, X,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { caseReportsApi, crmApi, downloadFile, parseApiError } from '@/lib/api'
import type { CaseReportSummary } from '@/lib/api'
import { LH_FOOTER, LH_LOGO, LH_NAME } from '../letter/letterhead'
import { SECTIONS, blankRow, type Section } from './sections'
import { paginate, startsTable, type Block } from './paginate'

const NAZ = "'B Nazanin','BNazanin','Nazanin',serif"
const TITR = "'B Titr','BTitr','Titr','B Nazanin',serif"
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']
const PAGE_W = 794, PAGE_H = 1123      // A4 @96dpi
const HEAD_H = 168                     // letterhead band
const FOOT_H = 86                      // address/contact banner + page number
const PAD_X = 46
const AVAIL = PAGE_H - HEAD_H - FOOT_H
const CONTENT_W = PAGE_W - PAD_X * 2

const fa = (n: number | string) => String(n).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d])

type Fields = Record<string, string>
type Tables = Record<string, Record<string, string>[]>

const emptyTables = (): Tables =>
  Object.fromEntries(SECTIONS.filter((s) => s.kind === 'table').map((s) => [s.key, []])) as Tables

// A block as the page renders it: the pure pagination type plus the element to
// draw. `paginate` only ever needs the id/kind, so the JSX stays out of it.
type PageBlock =
  | (Extract<Block, { t: 'node' }> & { el: JSX.Element })
  | Extract<Block, { t: 'trow' }>

export default function CaseReportPage() {
  const [f, setF] = useState<Fields>({})
  const [tb, setTb] = useState<Tables>(emptyTables)
  const [id, setId] = useState<string>('')
  const [account, setAccount] = useState('')
  const [general, setGeneral] = useState(false)
  const [saving, setSaving] = useState(false)
  const [busy, setBusy] = useState('')
  const [list, setList] = useState<CaseReportSummary[]>([])
  const [atts, setAtts] = useState<any[]>([])
  const [pages, setPages] = useState<PageBlock[][]>([])
  const measurer = useRef<HTMLDivElement>(null)

  const set = (k: string, v: string) => setF((p) => ({ ...p, [k]: v }))
  const setRow = (sec: string, i: number, k: string, v: string) =>
    setTb((p) => ({ ...p, [sec]: p[sec].map((r, j) => (j === i ? { ...r, [k]: v } : r)) }))
  const addRow = (s: Section) =>
    setTb((p) => ({ ...p, [s.key]: [...(p[s.key] || []), blankRow(s)] }))
  const delRow = (sec: string, i: number) =>
    setTb((p) => ({ ...p, [sec]: p[sec].filter((_, j) => j !== i) }))

  // ── the URL decides which bucket this report belongs to, exactly like the
  //    letter's ?general=1 — so the two entrances stay symmetrical.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search)
    if (q.get('general') === '1') setGeneral(true)
    const acc = q.get('account') || ''
    if (acc) setAccount(acc)
    const open = q.get('id') || ''
    if (open) void load(open)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshList = useCallback(async () => {
    try {
      setList(await caseReportsApi.list(general ? { general: true } : (account ? { account_no: account } : {})))
    } catch { /* the list is a convenience; never block the document on it */ }
  }, [general, account])
  useEffect(() => { void refreshList() }, [refreshList])

  const refreshAtts = useCallback(async (rid: string) => {
    if (!rid) { setAtts([]); return }
    try { setAtts(await caseReportsApi.attachments(rid)) } catch { setAtts([]) }
  }, [])

  async function load(rid: string) {
    setBusy('load')
    try {
      const r = await caseReportsApi.get(rid)
      setId(r.id)
      setAccount(r.account_no || '')
      setGeneral(r.category === 'general')
      setF(Object.fromEntries(Object.entries(r.fields || {}).map(([k, v]) => [k, v ?? ''])))
      setTb({ ...emptyTables(), ...Object.fromEntries(
        Object.entries(r.tables || {}).map(([k, v]) => [k, Array.isArray(v) ? v : []])) })
      await refreshAtts(r.id)
      toast.success('گزارش باز شد')
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy('') }
  }

  async function save() {
    if (!general && !account.trim()) { toast.error('شمارهٔ حساب را وارد کنید یا «گزارش عمومی» را بزنید'); return }
    setSaving(true)
    try {
      const r = await caseReportsApi.save({
        id: id || undefined, general, account_no: general ? undefined : account.trim(),
        fields: f, tables: tb,
      })
      setId(r.id)
      toast.success(id ? 'گزارش به‌روزرسانی شد' : 'گزارش ذخیره شد')
      await refreshList()
      await refreshAtts(r.id)
    } catch (e) { toast.error(parseApiError(e)) } finally { setSaving(false) }
  }

  async function prefill() {
    const acc = account.trim()
    if (!acc) { toast.error('برای پیش‌نویس، شمارهٔ حساب لازم است'); return }
    setBusy('prefill')
    try {
      const p = await caseReportsApi.prefill(acc)
      // Offer, never overwrite: a field the user already filled stays as it is.
      setF((prev) => {
        const next = { ...prev }
        for (const [k, v] of Object.entries(p.fields || {})) if (!((next[k] || '').trim()) && v) next[k] = v
        return next
      })
      setTb((prev) => {
        const next = { ...prev }
        for (const [k, rows] of Object.entries(p.tables || {})) {
          if (!Array.isArray(rows) || !rows.length) continue
          if ((next[k] || []).length) continue      // the user's rows win
          next[k] = rows as Record<string, string>[]
        }
        return next
      })
      const n = Object.values(p.sources || {}).reduce((a, b) => a + (b || 0), 0)
      toast.success(p.found || n
        ? `از دیتابیس پر شد — ${fa(p.sources?.partners || 0)} شریک، ${fa(p.sources?.facilities || 0)} تسهیلات، ${fa(p.sources?.collateral || 0)} وثیقه`
        : 'برای این حساب چیزی در دیتابیس نبود')
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy('') }
  }

  async function remove() {
    if (!id) return
    if (!window.confirm('این گزارش به سطلِ بازیافت می‌رود. مطمئنید؟')) return
    try {
      await caseReportsApi.remove(id)
      toast.success('به سطلِ بازیافت رفت')
      setId(''); await refreshList()
    } catch (e) { toast.error(parseApiError(e)) }
  }

  async function upload(file: File) {
    if (!id) { toast.error('اول گزارش را ذخیره کنید تا پیوست به آن بچسبد'); return }
    if (!account.trim()) { toast.error('پیوست به پروندهٔ حساب می‌چسبد — گزارشِ بدونِ حساب پیوست نمی‌گیرد'); return }
    setBusy('upload')
    try {
      await crmApi.uploadAttachment(account.trim(), file, { facility_id: `CASE-${id}` })
      toast.success('پیوست شد')
      await refreshAtts(id)
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy('') }
  }

  async function exportWord() {
    setBusy('word')
    try {
      const { buildCaseDocx } = await import('./wordExport')
      const blob = await buildCaseDocx({ f, tables: tb, sections: SECTIONS })
      const name = `گزارش خلاصه پرونده${account ? ' - ' + account : ''}.docx`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = name; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 4000)
      toast.success('فایل Word ساخته شد')
    } catch (e) { toast.error(parseApiError(e)) } finally { setBusy('') }
  }

  function reset() {
    if (!window.confirm('همهٔ فیلدهای این فرم پاک می‌شوند. گزارشِ ذخیره‌شده دست نمی‌خورد.')) return
    setF({}); setTb(emptyTables()); setId(''); setAtts([])
  }

  // ── the flowing document, as measurable blocks ────────────────────────────
  const blocks: PageBlock[] = useMemo(() => {
    const out: PageBlock[] = []
    out.push({ t: 'node', id: 'basmala', el: <div className="cr-basmala">با سمه تعالی</div> })
    out.push({ t: 'node', id: 'recipient', el: (
      <div className="cr-recipient">
        <div className="cr-bold">جناب آقای {f.recipient_name || '----'}</div>
        <div className="cr-bold">{f.recipient_title || 'ریاست محترم دایره حقوقی و پیگیری وصول مطالبات'}</div>
      </div>
    ) })
    out.push({ t: 'node', id: 'subject', el: (
      <div className="cr-subject">
        <div className="cr-bold">
          مــوضـوع : بـدهـی {f.subject_entity || '--------------'} حـسـاب شـمـاره {f.subject_account || '----------'} نـزد شـعبـه {f.subject_branch || '---------'}
        </div>
        <div className="cr-rule" />
      </div>
    ) })
    out.push({ t: 'node', id: 'intro', el: (
      <p className="cr-p">
        با سلام، احتراماً عطف به نامه شماره {f.ref_letter_no || '-------/---'} مورخ {f.ref_letter_date || '--/--/---'} اداره {f.ref_letter_dept || '----------'} در خصوص بدهی شرکت صدرالاشاره، بدینوسیله گزارش جامع وضعیت پرونده، وفق مفاد نامه {f.basis_letter_no || '-------/----'} مورخ {f.basis_letter_date || '---/---/-----'}، به شرح زیر ایفاد می گردد:
      </p>
    ) })

    for (const s of SECTIONS) {
      out.push({ t: 'node', id: `h-${s.key}`, el: (
        <div className="cr-h">{s.no ? `${s.no}- ` : ''}{s.title}</div>
      ) })
      if (s.kind === 'text') {
        out.push({ t: 'node', id: `t-${s.key}`, el: (
          <p className="cr-p cr-free">{f[s.field] || ''}</p>
        ) })
      } else if (s.kind === 'fields') {
        out.push({ t: 'node', id: `g-${s.key}`, el: (
          <table className="cr-tbl"><tbody>
            {s.rows.map((r) => (
              <tr key={r.key}>
                <th style={{ width: '42%' }}>{r.label}</th>
                <td dir={r.ltr ? 'ltr' : undefined}>{f[r.key] || ''}</td>
              </tr>
            ))}
          </tbody></table>
        ) })
      } else {
        const rows = tb[s.key] || []
        if (!rows.length) {
          out.push({ t: 'node', id: `e-${s.key}`, el: (
            <table className="cr-tbl">
              <thead><tr>{s.cols.map((c) => <th key={c.key} style={c.w ? { width: c.w } : undefined}>{c.label}</th>)}</tr></thead>
              <tbody><tr>{s.cols.map((c) => <td key={c.key}>&nbsp;</td>)}</tr></tbody>
            </table>
          ) })
        } else {
          rows.forEach((_, i) => out.push({ t: 'trow', id: `${s.key}-${i}`, sec: s.key, idx: i }))
        }
      }
      if (s.note) out.push({ t: 'node', id: `n-${s.key}`, el: <div className="cr-note">{s.note}</div> })
    }

    out.push({ t: 'node', id: 'sign', el: (
      <div className="cr-sign">
        <div>شعبه {f.branch_name || '-----'} {f.branch_code || '-----'}</div>
        <div className="cr-doer">اقدام کننده : {f.prepared_by || ''}</div>
      </div>
    ) })
    return out
  }, [f, tb])

  const secOf = (key: string) => SECTIONS.find((s) => s.key === key) as Extract<Section, { kind: 'table' }>

  const renderTRow = (b: Extract<PageBlock, { t: 'trow' }>, withHead: boolean) => {
    const s = secOf(b.sec)
    const row = (tb[b.sec] || [])[b.idx] || {}
    return (
      <table className="cr-tbl cr-tbl-part" key={b.id}>
        {withHead && <thead><tr>{s.cols.map((c) => (
          <th key={c.key} style={c.w ? { width: c.w } : undefined}>{c.label}</th>
        ))}</tr></thead>}
        <tbody><tr>{s.cols.map((c) => (
          <td key={c.key} dir={c.ltr ? 'ltr' : undefined}>{row[c.key] || ''}</td>
        ))}</tr></tbody>
      </table>
    )
  }

  // ── pagination: measure each block once, then pack with the pure packer.
  //    Measuring is the DOM's job; deciding where the breaks fall is not, so the
  //    rule «a split table keeps its column titles» lives in ./paginate.ts where
  //    it can be tested at every boundary instead of only when a report happens
  //    to be long enough to print wrong.
  useEffect(() => {
    const host = measurer.current
    if (!host) return
    const h: Record<string, number> = {}
    const head: Record<string, number> = {}
    host.querySelectorAll<HTMLElement>('[data-mid]').forEach((el) => {
      h[el.dataset.mid as string] = el.getBoundingClientRect().height
    })
    host.querySelectorAll<HTMLElement>('[data-head]').forEach((el) => {
      head[el.dataset.head as string] = el.getBoundingClientRect().height
    })
    const byId = new Map(blocks.map((b) => [b.id, b]))
    setPages(paginate(blocks, { h, head }, AVAIL)
      .map((pg) => pg.map((b) => byId.get(b.id) as PageBlock)))
  }, [blocks])

  const Sheet = ({ page, n, total }: { page: PageBlock[]; n: number; total: number }) => (
    <div className="csheet">
      <div className="cr-head">
        <div className="cr-head-l">
          <img src={LH_LOGO} alt="" className="cr-logo" />
          <img src={LH_NAME} alt="" className="cr-name" />
        </div>
        <div className="cr-head-r" dir="rtl">
          <div>فرع عجمان</div>
          <div dir="ltr">AJMAN BRANCH</div>
          <div dir="ltr">“Licensed by CBUAE”</div>
        </div>
      </div>
      {n === 1 && (
        <div className="cr-meta" dir="rtl">
          <div>تاریخ: <b dir="ltr">{f.letter_date || ''}</b></div>
          <div>شماره: <b dir="ltr">{f.letter_no || ''}</b></div>
          <div>طبقه بندی: <b>{f.classification || ''}</b></div>
        </div>
      )}
      <div className="cr-body">
        {page.map((b, i) => b.t === 'node'
          ? <div key={b.id}>{b.el}</div>
          : renderTRow(b, startsTable(page, i)))}
      </div>
      <div className="cr-foot">
        <img src={LH_FOOTER} alt="" className="cr-foot-img" />
        <div className="cr-pageno" dir="ltr">Page | {n}</div>
      </div>
    </div>
  )

  return (
    <Layout>
      <div dir="rtl" className="cr-wrap">
        <style>{`
          .cr-wrap{font-family:${NAZ}}
          .cr-controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
          .cr-btn{display:inline-flex;align-items:center;gap:6px;border:1px solid #cbd5e1;background:#fff;color:#0f172a;
                  border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;font-family:inherit}
          .cr-btn:hover{background:#f8fafc}
          .cr-btn.blue{background:#2563eb;border-color:#2563eb;color:#fff}
          .cr-btn.green{background:#059669;border-color:#059669;color:#fff}
          .cr-btn.amber{background:#f59e0b;border-color:#f59e0b;color:#fff}
          .cr-btn.red{background:#fff;border-color:#fecaca;color:#b91c1c}
          .cr-btn:disabled{opacity:.55;cursor:default}
          .cr-in{border:1px solid #cbd5e1;border-radius:7px;padding:6px 9px;font-size:13px;font-family:inherit;background:#fff;color:#0f172a}
          .cr-in:focus{outline:none;border-color:#2563eb}
          .cr-form{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px;margin-bottom:14px}
          .cr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
          .cr-lab{display:block;font-size:12px;color:#475569;margin-bottom:3px}
          .cr-secttl{font-size:13px;font-weight:700;color:#0f172a;margin:14px 0 8px;padding-bottom:5px;border-bottom:1px solid #e2e8f0}
          .cr-editrow{display:grid;gap:6px;align-items:start;margin-bottom:6px}
          .cr-x{border:0;background:#fee2e2;color:#b91c1c;border-radius:6px;cursor:pointer;padding:6px 8px}

          /* ── the printed sheet ─────────────────────────────────────────── */
          .csheet{position:relative;width:${PAGE_W}px;height:${PAGE_H}px;margin:0 auto 18px;background:#fff;
                  box-shadow:0 0 8px rgba(0,0,0,.18);color:#000;font-family:${NAZ};line-height:1.35;overflow:hidden}
          .cr-head{position:absolute;top:0;right:0;left:0;height:${HEAD_H}px;padding:10px ${PAD_X}px 0;
                   display:flex;justify-content:space-between;align-items:flex-start}
          .cr-head-l{display:flex;align-items:center;gap:8px}
          .cr-logo{height:54px}.cr-name{height:26px}
          .cr-head-r{text-align:left;font-size:12px;line-height:1.5;font-family:${TITR}}
          .cr-meta{position:absolute;top:${HEAD_H - 52}px;right:${PAD_X}px;font-size:12.5px;line-height:1.6}
          .cr-body{position:absolute;top:${HEAD_H}px;right:${PAD_X}px;left:${PAD_X}px;height:${AVAIL}px;
                   font-size:12.5px;text-align:justify;overflow:hidden}
          .cr-foot{position:absolute;bottom:0;right:0;left:0;height:${FOOT_H}px;padding:0 ${PAD_X}px 8px;
                   display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px}
          .cr-foot-img{max-width:100%;max-height:${FOOT_H - 26}px}
          .cr-pageno{font-size:11px;color:#333}
          .cr-basmala{text-align:center;font-family:${TITR};font-size:13px;margin-bottom:10px}
          .cr-recipient{margin-bottom:8px;font-family:${TITR};font-size:13px;line-height:1.7}
          .cr-bold{font-weight:700}
          .cr-subject{margin:8px 0}
          .cr-rule{border-top:2px double #000;margin-top:4px}
          .cr-p{margin:0 0 8px;text-indent:1.2em;white-space:pre-wrap}
          .cr-free{text-indent:0}
          .cr-h{font-weight:700;font-family:${TITR};font-size:12.5px;margin:10px 0 5px}
          .cr-note{font-size:11px;margin:4px 0 8px}
          .cr-tbl{width:100%;border-collapse:collapse;margin:0 0 8px;font-size:11.5px;table-layout:fixed}
          .cr-tbl-part{margin-bottom:0}
          .cr-tbl th,.cr-tbl td{border:.6px solid #222;padding:3px 5px;vertical-align:top;
                                word-break:normal;overflow-wrap:break-word;line-height:1.35}
          .cr-tbl th{background:#f1f5f9;font-weight:700;text-align:center}
          .cr-sign{margin-top:16px;font-size:12.5px}
          .cr-doer{margin-top:22px}
          .cr-measure{position:absolute;visibility:hidden;pointer-events:none;top:-99999px;right:0;
                      width:${CONTENT_W}px;font-size:12.5px;line-height:1.35;font-family:${NAZ}}

          @media print {
            @page { size:A4; margin:0 }
            html,body{margin:0!important;padding:0!important;background:#fff!important}
            .no-print{display:none!important}
            .csheet{box-shadow:none;margin:0!important;height:296mm;overflow:hidden;
                    break-after:page;page-break-after:always}
            .csheet:last-child{break-after:auto;page-break-after:auto}
          }
        `}</style>

        {/* ── controls ─────────────────────────────────────────────────── */}
        <div className="cr-controls no-print">
          <button className="cr-btn blue" onClick={save} disabled={saving}>
            {saving ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
            {id ? 'به‌روزرسانی' : 'ذخیره'}
          </button>
          <button className="cr-btn" onClick={() => window.print()}><Printer size={15} /> چاپ / PDF</button>
          <button className="cr-btn green" onClick={exportWord} disabled={busy === 'word'}>
            {busy === 'word' ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />} خروجی Word
          </button>
          <button className="cr-btn amber" onClick={prefill} disabled={busy === 'prefill'}>
            {busy === 'prefill' ? <Loader2 size={15} className="animate-spin" /> : <Wand2 size={15} />} پیش‌نویس از دیتابیس
          </button>
          <button className="cr-btn" onClick={reset}><RotateCcw size={14} /> فرمِ خالی</button>
          {id && <button className="cr-btn red" onClick={remove}><Trash2 size={14} /> حذف</button>}
          <span style={{ flex: 1 }} />
          <label className="cr-lab" style={{ margin: 0 }}>
            <input type="checkbox" checked={general} onChange={(e) => setGeneral(e.target.checked)} /> گزارشِ عمومی (بدونِ حساب)
          </label>
          {!general && (
            <input className="cr-in" placeholder="شمارهٔ حساب" value={account}
                   onChange={(e) => setAccount(e.target.value)} dir="ltr" style={{ width: 130 }} />
          )}
          <select className="cr-in" value="" onChange={(e) => { if (e.target.value) void load(e.target.value) }}>
            <option value="">گزارش‌های ذخیره‌شده…</option>
            {list.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title || r.subject_entity || r.subject_account || r.id.slice(0, 8)}
                {r.letter_date ? ` — ${r.letter_date}` : ''}
              </option>
            ))}
          </select>
          <button className="cr-btn" onClick={() => { setId(''); setF({}); setTb(emptyTables()); setAtts([]) }}>
            <FilePlus size={14} /> گزارشِ تازه
          </button>
        </div>

        {/* ── the form ─────────────────────────────────────────────────── */}
        <div className="cr-form no-print">
          <div className="cr-secttl">سربرگ و گیرنده</div>
          <div className="cr-grid">
            <Fld l="عنوان (برای فهرست)" k="title" f={f} set={set} />
            <Fld l="تاریخ" k="letter_date" f={f} set={set} ltr />
            <Fld l="شماره" k="letter_no" f={f} set={set} ltr />
            <div>
              <label className="cr-lab">طبقه بندی</label>
              <select className="cr-in" style={{ width: '100%' }} value={f.classification || ''}
                      onChange={(e) => set('classification', e.target.value)}>
                <option value="">—</option>
                {CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <Fld l="گیرنده (جناب آقای …)" k="recipient_name" f={f} set={set} />
            <Fld l="سمت گیرنده" k="recipient_title" f={f} set={set} />
            <Fld l="موضوع — نام شرکت/موسسه" k="subject_entity" f={f} set={set} />
            <Fld l="موضوع — شماره حساب" k="subject_account" f={f} set={set} ltr />
            <Fld l="موضوع — شعبه" k="subject_branch" f={f} set={set} />
            <Fld l="عطف به نامه شماره" k="ref_letter_no" f={f} set={set} ltr />
            <Fld l="عطف به نامه مورخ" k="ref_letter_date" f={f} set={set} ltr />
            <Fld l="اداره صادرکنندهٔ نامه" k="ref_letter_dept" f={f} set={set} />
            <Fld l="وفق مفاد نامه شماره" k="basis_letter_no" f={f} set={set} ltr />
            <Fld l="وفق مفاد نامه مورخ" k="basis_letter_date" f={f} set={set} ltr />
          </div>

          {SECTIONS.map((s) => (
            <div key={s.key}>
              <div className="cr-secttl">{s.no ? `${s.no}- ` : ''}{s.title}</div>
              {s.kind === 'text' && (
                <textarea className="cr-in" style={{ width: '100%', minHeight: 90 }}
                          value={f[s.field] || ''} onChange={(e) => set(s.field, e.target.value)} />
              )}
              {s.kind === 'fields' && (
                <div className="cr-grid">
                  {s.rows.map((r) => <Fld key={r.key} l={r.label} k={r.key} f={f} set={set} ltr={r.ltr} />)}
                </div>
              )}
              {s.kind === 'table' && (
                <>
                  {(tb[s.key] || []).map((row, i) => (
                    <div key={i} className="cr-editrow"
                         style={{ gridTemplateColumns: `repeat(${s.cols.length},1fr) auto` }}>
                      {s.cols.map((c) => (
                        <input key={c.key} className="cr-in" placeholder={c.label} dir={c.ltr ? 'ltr' : undefined}
                               value={row[c.key] || ''} onChange={(e) => setRow(s.key, i, c.key, e.target.value)} />
                      ))}
                      <button className="cr-x" onClick={() => delRow(s.key, i)} title="حذفِ سطر"><X size={14} /></button>
                    </div>
                  ))}
                  <button className="cr-btn" onClick={() => addRow(s)}><Plus size={14} /> افزودنِ سطر</button>
                </>
              )}
            </div>
          ))}

          <div className="cr-secttl">پانویس</div>
          <div className="cr-grid">
            <Fld l="شعبه" k="branch_name" f={f} set={set} />
            <Fld l="کد شعبه" k="branch_code" f={f} set={set} ltr />
            <Fld l="اقدام کننده" k="prepared_by" f={f} set={set} />
          </div>

          <div className="cr-secttl">پیوست‌ها</div>
          {!id && <div style={{ fontSize: 12, color: '#64748b' }}>اول گزارش را ذخیره کنید تا بتوانید پیوست اضافه کنید.</div>}
          {id && !account.trim() && (
            <div style={{ fontSize: 12, color: '#b45309' }}>
              پیوست به پروندهٔ حساب می‌چسبد؛ گزارشِ بدونِ حساب پیوست نمی‌گیرد.
            </div>
          )}
          {id && !!account.trim() && (
            <>
              <label className="cr-btn" style={{ display: 'inline-flex' }}>
                {busy === 'upload' ? <Loader2 size={15} className="animate-spin" /> : <Paperclip size={15} />} افزودنِ پیوست
                <input type="file" style={{ display: 'none' }}
                       onChange={(e) => { const x = e.target.files?.[0]; if (x) void upload(x); e.currentTarget.value = '' }} />
              </label>
              <ul style={{ fontSize: 12, marginTop: 8, listStyle: 'none', padding: 0 }}>
                {atts.map((a) => (
                  <li key={a.id} style={{ padding: '3px 0' }}>
                    <button className="cr-btn" style={{ padding: '3px 8px' }}
                            onClick={() => downloadFile(`/api/crm/attachments/${a.id}/view`, a.original_name)}>
                      <Download size={12} /> {a.original_name}
                    </button>
                    <span style={{ color: '#64748b', marginRight: 6 }}>
                      {a.storage === 'drive' ? 'در درایو' : 'روی دیسک'}
                    </span>
                  </li>
                ))}
                {!atts.length && <li style={{ color: '#64748b' }}>هنوز پیوستی نیست.</li>}
              </ul>
            </>
          )}
        </div>

        {/* hidden measurer — every block rendered once at the real content width */}
        <div ref={measurer} className="cr-measure" aria-hidden>
          {blocks.map((b) => b.t === 'node'
            ? <div key={b.id} data-mid={b.id}>{b.el}</div>
            : <div key={b.id} data-mid={b.id}>{renderTRow(b, false)}</div>)}
          {SECTIONS.filter((s) => s.kind === 'table').map((s) => (
            <table className="cr-tbl" key={`hd-${s.key}`} data-head={s.key}>
              <thead><tr>{(s as any).cols.map((c: any) => (
                <th key={c.key} style={c.w ? { width: c.w } : undefined}>{c.label}</th>
              ))}</tr></thead>
            </table>
          ))}
        </div>

        <div className="cr-canvas">
          {pages.map((p, i) => <Sheet key={i} page={p} n={i + 1} total={pages.length} />)}
        </div>
      </div>
    </Layout>
  )
}

function Fld({ l, k, f, set, ltr }: {
  l: string; k: string; f: Fields; set: (k: string, v: string) => void; ltr?: boolean
}) {
  return (
    <div>
      <label className="cr-lab">{l}</label>
      <input className="cr-in" style={{ width: '100%' }} dir={ltr ? 'ltr' : undefined}
             value={f[k] || ''} onChange={(e) => set(k, e.target.value)} />
    </div>
  )
}
