'use client'

// Official Bank Saderat LETTER (نامه) — a paginated, editable, flowing document.
// The body flows across DISCRETE A4 pages: page 1 fills to its (resizable) text box,
// the rest continues on a fresh page that starts just below the repeated header, and
// the closing block (امضاکننده + رونوشت + اقدام) appears only on the LAST page. Shrink
// the page-1 text box and the overflow moves to the next page (nothing is lost). Every
// paragraph's first line is indented. «چیدمان» turns on drag/resize/double-click field
// editing; Word-like alignment/justify/direction live in the field panel. 794×1123 px =
// 210×297 mm @96dpi → prints 1:1. Fonts: locally-installed B Nazanin / Titr / B Titr.
import { useState, useRef, useEffect, useLayoutEffect } from 'react'
import Layout from '@/components/Layout'
import { Printer, Eraser, Move, Check, RotateCcw, Save, FilePlus, Table } from 'lucide-react'
import { auditApi, departmentsApi, lettersApi, parseApiError } from '@/lib/api'
import { LetterSummary } from '@/types'
import Combobox from '@/components/Combobox'
import toast from 'react-hot-toast'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const SENDERS = ['سرپرستی منطقه خلیج فارس', 'دایره تسهیلات اعطایی']
const CLASSES = ['داخلی', 'عادی', 'محرمانه', 'خیلی محرمانه']
const NAZ = "'B Nazanin','BNazanin','Nazanin',serif"
const TITR = "'Titr','B Titr','BTitr','B Nazanin',serif"
const BTITR = "'B Titr','BTitr','Titr','B Nazanin',serif"
const FONTS = [{ v: NAZ, n: 'B Nazanin' }, { v: TITR, n: 'Titr' }, { v: BTITR, n: 'B Titr' }]
// Only LATIN LETTERS (a-z/A-Z) render in an English serif; Persian letters, ALL digits
// and punctuation stay in the chosen Persian font. This uses the 'LtrMix' @font-face
// (unicode-range limited to Latin letters) defined in the page's <style>.
const latin = (stack?: string) => stack ? `'LtrMix',${stack}` : stack
const MM = 96 / 25.4 // px per mm at 96dpi
const m = (v: number) => Math.round(v * MM)
const fa =(n: number | string) => String(n).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d])
const useIso = typeof document !== 'undefined' ? useLayoutEffect : useEffect

// An input that shrinks/grows to exactly fit its text (so adjacent words don't leave gaps).
function AutoInput({ value, onChange, placeholder = '', dir, style, cls = 'fld', readOnly = false }:
  { value: string; onChange?: (e: any) => void; placeholder?: string; dir?: 'ltr' | 'rtl'; style?: React.CSSProperties; cls?: string; readOnly?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  const [w, setW] = useState(() => Math.max(12, String(value || placeholder).length * 9))
  useEffect(() => { if (ref.current) setW(Math.max(8, ref.current.offsetWidth + 3)) }, [value, placeholder])
  return (
    <span style={{ position: 'relative', display: 'inline-block', verticalAlign: 'baseline' }}>
      <span ref={ref} aria-hidden className="az-sizer">{value || placeholder || ' '}</span>
      <input className={cls} dir={dir} value={value} onChange={onChange} placeholder={placeholder} readOnly={readOnly} style={{ width: w, ...style }} />
    </span>
  )
}

// ---- contentEditable body cell: renders one page's chunk as indented paragraphs,
//      editable, with caret preserved across re-flows. ----
const escapeHtml = (s: string) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c] as string))
function caretOffset(el: HTMLElement): number | null {
  const s = window.getSelection(); if (!s || !s.rangeCount) return null
  const r = s.getRangeAt(0); const pre = r.cloneRange(); pre.selectNodeContents(el); pre.setEnd(r.endContainer, r.endOffset)
  return pre.toString().length
}
function setCaret(el: HTMLElement, off: number) {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n: Node | null, c = off, last: Node | null = null
  while ((n = w.nextNode())) { last = n; const len = (n.textContent || '').length; if (len >= c) { const r = document.createRange(); r.setStart(n, c); r.collapse(true); const s = window.getSelection(); s?.removeAllRanges(); s?.addRange(r); return } c -= len }
  if (last) { const r = document.createRange(); r.selectNodeContents(last); r.collapse(false); const s = window.getSelection(); s?.removeAllRanges(); s?.addRange(r) }
}
// Plain text → paragraph HTML (legacy bodies are plain); rich bodies already carry tags.
function normalizeBodyHtml(s: string): string {
  if (!s) return ''
  if (s.indexOf('<') === -1) return s.split('\n').map((line) => `<div>${escapeHtml(line) || '<br>'}</div>`).join('')
  return s
}

// Heuristic: a body that arrived hard-wrapped (one paragraph PER VISUAL LINE — e.g. a
// PDF/line-broken paste, or an older saved letter). Signature: several visual lines
// (counting <br>-separated segments too, since one block can hold many <br> lines), few
// of which end in a sentence terminator. Such bodies can't justify until reflowed.
function looksLineBroken(html: string): boolean {
  if (!html || html.indexOf('<') === -1) return false
  const d = document.createElement('div'); d.innerHTML = html
  let lines = 0, term = 0
  for (const c of Array.from(d.children)) {
    if (c.tagName === 'TABLE' || c.querySelector('table')) continue
    for (const seg of (c as HTMLElement).innerHTML.split(/<br\s*\/?>/i)) {
      const t = seg.replace(/<[^>]+>/g, '').replace(/ /g, ' ').trim()
      if (!t) continue
      lines++
      if (/[.؟!]\s*$/.test(t)) term++
    }
  }
  return lines >= 3 && term < lines * 0.6
}

// Clean pasted (Word/Excel) HTML: keep structure (paragraphs, lists, tables, b/u/i)
// and only bold/underline/size/align inline styles; strip Word's mso junk, classes,
// colors and fixed widths/heights (so our CSS makes the table fit the box).
const STYLE_KEEP = new Set(['font-weight', 'font-style', 'text-decoration', 'text-decoration-line', 'font-size', 'text-align'])
let _uid = 0
// A stable per-row id so the table toolbar can locate this exact row inside the body.
const uid = () => `r${(_uid++).toString(36)}${(typeof performance !== 'undefined' ? Math.floor(performance.now()) : 0).toString(36)}`

// Tidy pasted tables so they stay COMPACT and editable: drop Word's blank filler
// paragraphs (which make rows huge and empty), unwrap a cell's lone <p>/<div> (so no
// block margins bloat the row), keep a placeholder <br> in truly empty cells, and give
// every row a stable id for the toolbar. Heights/widths are already gone (not in
// STYLE_KEEP), so cells shrink to their real content.
function normalizeTables(root: HTMLElement) {
  root.querySelectorAll('table').forEach((tbl) => {
    tbl.querySelectorAll('td,th').forEach((cell) => {
      Array.from(cell.children).forEach((ch) => {
        if (/^(P|DIV)$/.test(ch.tagName) && !ch.querySelector('img,table,br') && !(ch.textContent || '').replace(/ /g, '').trim()) ch.remove()
      })
      while (cell.children.length === 1 && /^(P|DIV)$/.test(cell.children[0].tagName) && !cell.children[0].querySelector('table')) {
        const only = cell.children[0]
        while (only.firstChild) cell.insertBefore(only.firstChild, only)
        only.remove()
      }
      // trim trailing <br>/blank nodes Word pads cell bottoms with (→ huge empty rows)
      let last = cell.lastChild
      while (cell.childNodes.length > 1 && last && ((last.nodeType === 1 && (last as HTMLElement).tagName === 'BR') || (last.nodeType === 3 && !(last.textContent || '').replace(/ /g, '').trim()))) {
        const prev = last.previousSibling; cell.removeChild(last); last = prev
      }
      if (!(cell.textContent || '').trim() && !cell.querySelector('img,br')) cell.appendChild(document.createElement('br'))
    })
    tbl.querySelectorAll('tr').forEach((tr) => { if (!tr.getAttribute('data-r')) tr.setAttribute('data-r', uid()) })
  })
}
function cleanPaste(html: string): string {
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html')
    doc.querySelectorAll('style,meta,script,link,title,o\\:p,w\\:sdt').forEach((n) => n.remove())
    doc.body.querySelectorAll('*').forEach((el) => {
      const st = (el as HTMLElement).style, keep: string[] = []
      for (let i = 0; i < st.length; i++) { const p = st[i]; if (STYLE_KEEP.has(p)) keep.push(`${p}:${st.getPropertyValue(p)}`) }
      Array.from(el.attributes).forEach((a) => { const n = a.name.toLowerCase(); if (n !== 'colspan' && n !== 'rowspan') el.removeAttribute(a.name) })
      if (keep.length) el.setAttribute('style', keep.join(';'))
    })
    normalizeTables(doc.body)
    // let letter-body paragraphs inherit the box's justify (Word letters are justified):
    // drop a paragraph's own right/left alignment (keep an explicit center/justify).
    doc.body.querySelectorAll('p,div,li').forEach((el) => {
      if ((el as HTMLElement).closest('table')) return
      const ta = (el as HTMLElement).style.textAlign
      if (ta === 'right' || ta === 'left' || ta === 'start' || ta === 'end') (el as HTMLElement).style.removeProperty('text-align')
    })
    // collapse runs of blank lines Word inserts between paragraphs
    let prevBlank = false
    Array.from(doc.body.children).forEach((ch) => {
      const blank = /^(P|DIV)$/.test(ch.tagName) && !ch.querySelector('img,table') && !(ch.textContent || '').replace(/ /g, '').trim()
      if (blank && prevBlank) ch.remove(); else prevBlank = blank
    })
    return doc.body.innerHTML
  } catch { return html }
}
// A row-selector safe for querySelector (CSS.escape where available).
const cssEsc = (v: string) => (typeof CSS !== 'undefined' && (CSS as any).escape ? (CSS as any).escape(v) : v.replace(/[^\w-]/g, '\\$&'))

// Re-merge tables that were split across pages (same header) so storage stays clean.
function mergeAdjacentTables(container: HTMLElement) {
  let node = container.firstElementChild
  while (node) {
    const next = node.nextElementSibling
    if (node.tagName === 'TABLE' && next && next.tagName === 'TABLE') {
      const h1 = node.querySelector('tr'), h2 = next.querySelector('tr')
      if (h1 && h2 && (h1.textContent || '').trim() === (h2.textContent || '').trim()) {
        const tb = node.querySelector('tbody') || node
        Array.from(next.querySelectorAll('tr')).slice(1).forEach((r) => tb.appendChild(r))
        next.remove()
        continue // re-check the (now-extended) node against its new sibling
      }
    }
    node = next
  }
}
// A rich (contentEditable) page-cell. The body stores HTML so bold/underline can be
// applied to SELECTED words only (via the floating toolbar / execCommand). Caret is
// preserved across re-flows.
function BodyCell({ html, editable, indent, firstPage, style, onChangeHtml, transformPaste }:
  { html: string; editable: boolean; indent?: number; firstPage?: boolean; style?: React.CSSProperties; onChangeHtml: (h: string) => void; transformPaste?: (html: string) => string }) {
  const ref = useRef<HTMLDivElement>(null)
  useIso(() => {
    const el = ref.current; if (!el) return
    const want = html || '<div><br></div>'
    if (el.innerHTML !== want) {
      const foc = document.activeElement === el
      const off = foc ? caretOffset(el) : null
      el.innerHTML = want
      if (off != null) setCaret(el, off)
    }
  }, [html])
  return (
    <div ref={ref} className={`bcell${firstPage ? ' firstpage' : ''}`} contentEditable={editable} suppressContentEditableWarning
      onPaste={(e) => { const h = e.clipboardData.getData('text/html'); if (h) { e.preventDefault(); document.execCommand('insertHTML', false, (transformPaste || cleanPaste)(h)) } }}
      onInput={() => { const el = ref.current; if (el) onChangeHtml(el.innerHTML) }}
      style={{ ...style, ['--ind' as any]: indent ? `${indent}em` : '0' }} />
  )
}

// Strip tags → plain text (for the departments DB, the letter title, comboboxes…).
const plain = (h: string) => (h || '').replace(/<br\s*\/?>/gi, ' ').replace(/<[^>]+>/g, '').replace(/&nbsp;/gi, ' ').replace(/&amp;/gi, '&').replace(/&lt;/gi, '<').replace(/&gt;/gi, '>').replace(/\s+/g, ' ').trim()

// An inline, auto-sizing, rich (contentEditable) field. Stores HTML so bold/underline
// can be applied to SELECTED words only (via the floating toolbar). Caret-preserving.
function RichSpan({ value, onChange, placeholder, dir, className, style }:
  { value: string; onChange: (h: string) => void; placeholder?: string; dir?: 'ltr' | 'rtl'; className?: string; style?: React.CSSProperties }) {
  const ref = useRef<HTMLSpanElement>(null)
  useIso(() => {
    const el = ref.current; if (!el) return
    const want = value || ''
    if (el.innerHTML !== want) {
      const foc = document.activeElement === el
      const off = foc ? caretOffset(el) : null
      el.innerHTML = want
      if (off != null) setCaret(el, off)
    }
  }, [value])
  return <span ref={ref} className={`rich ${className || ''}`} contentEditable suppressContentEditableWarning dir={dir}
    data-ph={placeholder || ''} onInput={() => { const el = ref.current; if (el) onChange(el.innerHTML) }} style={style} />
}

type Boxn = { x: number; y: number; w: number; h?: number; size: number; font?: string; bold?: boolean; underline?: boolean; align?: 'right' | 'center' | 'left'; ls?: number; lh?: number; dir?: 'rtl' | 'ltr'; justify?: boolean; indent?: number; contY?: number; hidden?: boolean }
const KEY_FA: Record<string, string> = {
  logo: 'لوگو', name: 'نامِ بانک', footer: 'فوتر', besmele: 'بسمه تعالی', shomareh: 'شماره', tarikh: 'تاریخ',
  peyvast: 'پیوست', recName: 'نامِ گیرنده', recTitle: 'سمت/ادارهٔ گیرنده', classification: 'طبقه‌بندی', subject: 'موضوع',
  separator: 'خطِ جداکننده', body: 'متنِ نامه', sender: 'امضاکننده', copyto: 'رونوشت', action: 'اقدام‌کننده', pagenum: 'شمارهٔ صفحه',
}
const DEFAULT_LAYOUT: Record<string, Boxn> = {
  logo: { x: m(4.8), y: m(4), w: m(28.5), h: m(27.6), size: 0 },
  name: { x: m(138.8), y: m(6.3), w: m(65.8), h: m(20.4), size: 0 },
  footer: { x: m(22.2), y: m(277.2), w: m(167.4), h: m(17.7), size: 0 },
  besmele: { x: m(85), y: m(29), w: m(40), size: 13, font: NAZ, align: 'center' },
  shomareh: { x: m(8), y: m(44.8), w: m(62), size: 12, font: NAZ, align: 'right' },
  tarikh: { x: m(8), y: m(51), w: m(62), size: 12, font: NAZ, align: 'right' },
  peyvast: { x: m(20), y: m(57.3), w: m(50), size: 12, font: NAZ, align: 'right' },
  recName: { x: m(128.2), y: m(57.6), w: m(62), size: 12, font: BTITR, bold: true, align: 'right' },
  recTitle: { x: m(118), y: m(65), w: m(72), size: 12, font: BTITR, bold: true, align: 'right' },
  classification: { x: m(16), y: m(66.8), w: m(54), size: 11, font: NAZ, bold: true, align: 'right' },
  subject: { x: m(28), y: m(78), w: m(162.5), size: 12, font: TITR, align: 'right' },
  separator: { x: m(133.8), y: m(107), w: m(56.7), h: 1, size: 0 },
  body: { x: m(25), y: m(118), w: m(160), h: m(148), size: 13, font: NAZ, align: 'right', justify: true, lh: 1.7, dir: 'rtl', indent: 1.5, contY: m(40) },
  sender: { x: m(40), y: m(234), w: m(120), size: 13, font: BTITR, bold: true, align: 'center' },
  copyto: { x: m(124.7), y: m(250), w: m(60), size: 10, font: NAZ, align: 'right' },
  action: { x: m(93.8), y: m(264), w: m(90), size: 10, font: NAZ, align: 'right' },
  pagenum: { x: m(85), y: m(270), w: m(40), size: 10, font: NAZ, align: 'center' },
}
const DEFAULT_LABELS: Record<string, string> = {
  besmele: 'بسمه تعالی',
  shomareh: 'شماره : ', tarikh: 'تاریخ : ', peyvast: 'پیوست : ',
  classification: 'نوع طبقه بندی – ', subject: 'موضوع : ',
  copyto: 'رونوشت : ', action: 'اقدام کننده : ', actionExt: ' / داخلی ',
}
const LS_KEY = 'letterTemplate_v4'
const CLOSING = ['sender', 'copyto', 'action']

function todayYMD() { const d = new Date(); const p = (n: number) => String(n).padStart(2, '0'); return `${d.getFullYear()}/${p(d.getMonth() + 1)}/${p(d.getDate())}` }

export default function LetterPage() {
  const [f, setF] = useState({
    classification: 'داخلی', serial: '----', year: String(new Date().getFullYear()),
    date: todayYMD(), attachment: 'دارد',
    recipientName: '', recipientTitle: 'رئیس محترم', recipientDept: '', subject: '', body: '',
    sender: SENDERS[0], copyTo: '', actionName: '', actionExt: '',
  })
  const set = (k: keyof typeof f) => (e: any) => setF((s) => ({ ...s, [k]: e.target.value }))
  const [L, setL] = useState<Record<string, Boxn>>(DEFAULT_LAYOUT)
  const [labels, setLabels] = useState<Record<string, string>>(DEFAULT_LABELS)
  const [design, setDesign] = useState(false)
  const [sel, setSel] = useState<string | null>(null)
  const [editing, setEditing] = useState<string | null>(null)
  const [sepGeom, setSepGeom] = useState<{ x: number; w: number } | null>(null)
  const [fmt, setFmt] = useState<{ x: number; y: number } | null>(null)        // floating bold/underline toolbar
  const [tbl, setTbl] = useState<{ x: number; y: number } | null>(null)        // floating table toolbar (caret in a cell)
  const [ppPos, setPpPos] = useState<{ x: number; y: number } | null>(null)    // draggable field panel
  // --- saving the letter under an account (or general) ---
  const [acct, setAcct] = useState('')
  const [title, setTitle] = useState('')
  const [general, setGeneral] = useState(false)
  const [letterId, setLetterId] = useState<string | null>(null)
  const [letterList, setLetterList] = useState<LetterSummary[]>([])
  const [savingLetter, setSavingLetter] = useState(false)
  const [letterQuery, setLetterQuery] = useState('')
  const LRef = useRef(L); useEffect(() => { LRef.current = L }, [L])
  const designRef = useRef(design); useEffect(() => { designRef.current = design }, [design])

  const loadLetter = async (id: string) => {
    try {
      const o = await lettersApi.get(id)
      if (o.values) {
        const v: any = { ...o.values }
        // auto-fix line-broken bodies so they flow & justify like Word (no manual step).
        // normalize first so legacy plain-text (\n) bodies are detected too.
        if (v.body) { const nb = normalizeBodyHtml(v.body); if (looksLineBroken(nb)) v.body = reflowBody(nb) }
        setF((s) => ({ ...s, ...v }))
      }
      if (o.layout) { const mm2: Record<string, Boxn> = { ...DEFAULT_LAYOUT }; for (const k in o.layout) mm2[k] = { ...(DEFAULT_LAYOUT[k] || {}), ...o.layout[k] }; mm2.body = { ...mm2.body, justify: true }; setL(mm2) }
      if (o.labels) setLabels((s) => ({ ...DEFAULT_LABELS, ...o.labels }))
      setAcct(o.account_no || ''); setTitle(o.title || ''); setGeneral(o.category === 'general'); setLetterId(o.id)
    } catch { toast.error('بارگذاریِ نامه ناموفق بود') }
  }
  // deep-link ?account=… / ?id=… and load the right letter list
  useEffect(() => {
    const q = new URLSearchParams(window.location.search)
    const a = q.get('account'); const id = q.get('id')
    if (a) setAcct(a)
    if (q.get('general') === '1') setGeneral(true)
    if (id) loadLetter(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    if (general) lettersApi.list({ general: true }).then(setLetterList).catch(() => setLetterList([]))
    else if (acct.trim()) lettersApi.list({ account_no: acct.trim() }).then(setLetterList).catch(() => setLetterList([]))
    else lettersApi.list({}).then(setLetterList).catch(() => setLetterList([]))  // no account → recent letters (all)
  }, [acct, general, letterId])

  const newLetter = () => { setLetterId(null); setTitle(''); setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' })) }
  const saveLetter = async () => {
    if (!general && !acct.trim()) { toast.error('شمارهٔ حساب را وارد کن، یا «نامهٔ عمومی» را تیک بزن'); return }
    setSavingLetter(true)
    try {
      const pDept = plain(f.recipientDept), pMgr = plain(f.recipientName), pSubj = plain(f.subject)
      if (pDept) {
        await departmentsApi.resolve({ name: pDept, manager: pMgr || undefined, manager_title: plain(f.recipientTitle) || undefined })
      }
      const saved = await lettersApi.save({
        id: letterId || undefined, account_no: general ? undefined : acct.trim(), general,
        title: title.trim() || pSubj || 'نامه', subject: pSubj,
        recipient_dept: pDept, recipient_manager: pMgr,
        values: f, layout: L, labels,
      })
      setLetterId(saved.id)
      toast.success(general ? 'نامه در «نامه‌های عمومی» ذخیره شد' : `نامه ذیلِ حسابِ ${acct.trim()} ذخیره شد`)
    } catch (e) { toast.error(parseApiError(e)) } finally { setSavingLetter(false) }
  }
  const fetchDepts = async (q: string) => (await departmentsApi.list(q)).map((d) => ({ value: d.name, label: d.name, sub: d.current_manager || '', data: d }))
  const fetchMgrs = async (q: string) => (await departmentsApi.list(q)).filter((d) => d.current_manager).map((d) => ({ value: d.current_manager as string, label: d.current_manager as string, sub: d.name, data: d }))

  useEffect(() => {
    try {
      let raw = localStorage.getItem(LS_KEY)        // current (v4)
      let fromOld = false
      if (!raw) { raw = localStorage.getItem('letterTemplate_v3'); fromOld = true } // fall back to the previous arrangement
      if (raw) {
        const o = JSON.parse(raw)
        if (o.L) {
          const merged: Record<string, Boxn> = { ...DEFAULT_LAYOUT }
          for (const k in o.L) {
            if (fromOld && k === 'body') continue   // body geometry changed (now drives pagination) — keep the new default
            merged[k] = { ...(DEFAULT_LAYOUT[k] || {}), ...o.L[k] }
          }
          setL(merged)
        }
        if (o.labels) setLabels({ ...DEFAULT_LABELS, ...o.labels })
      }
    } catch { /* ignore */ }
  }, [])
  const saveTemplate = () => { try { localStorage.setItem(LS_KEY, JSON.stringify({ L, labels })); alert('چیدمان ذخیره شد') } catch { /* ignore */ } }
  const resetTemplate = () => { if (confirm('بازگشت به چیدمانِ پیش‌فرض؟')) { setL(DEFAULT_LAYOUT); setLabels(DEFAULT_LABELS); setEditing(null); localStorage.removeItem(LS_KEY) } }
  const setBox = (k: string, patch: Partial<Boxn>) => setL((p) => ({ ...p, [k]: { ...p[k], ...patch } }))
  const bump = (k: string, d: number) => setBox(k, { size: Math.max(6, (L[k].size || 12) + d) })
  const spc = (k: string, d: number) => setBox(k, { ls: Math.max(0, Math.round(((L[k].ls || 0) + d) * 10) / 10) })
  const lnh = (k: string, d: number) => setBox(k, { lh: Math.max(1, Math.round(((L[k].lh || 1.7) + d) * 10) / 10) })

  const startDrag = (k: string) => (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); setSel(k)
    const sx = e.clientX, sy = e.clientY, o = { x: LRef.current[k].x, y: LRef.current[k].y }
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], x: Math.round(o.x + (ev.clientX - sx)), y: Math.round(o.y + (ev.clientY - sy)) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const startResize = (k: string) => (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation(); setSel(k)
    const sx = e.clientX, sy = e.clientY, o = { ...LRef.current[k] }
    const mv = (ev: PointerEvent) => setL((p) => ({ ...p, [k]: { ...p[k], w: Math.max(20, Math.round(o.w + (ev.clientX - sx))), ...(o.h != null ? { h: Math.max(8, Math.round((o.h || 0) + (ev.clientY - sy))) } : {}) } }))
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const openPanel = (k: string) => { setSel(k); setEditing(k); setDesign(true) } // double-click a field → arrange (handles) + panel
  const exitEditing = () => { setEditing(null); setSel(null); setDesign(false) } // double-click empty area → leave design/edit mode
  const startPanelDrag = (e: React.PointerEvent) => {
    e.preventDefault()
    const sx = e.clientX, sy = e.clientY, o = ppPos || { x: window.innerWidth - 16 - 212, y: 118 }
    const mv = (ev: PointerEvent) => setPpPos({ x: o.x + (ev.clientX - sx), y: o.y + (ev.clientY - sy) })
    const up = () => { document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up) }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // apply a DOM change to the current selection (in any rich field) and notify React
  const applySel = (mutate: (r: Range) => void) => {
    const sel = window.getSelection(); if (!sel || sel.isCollapsed || !sel.rangeCount) return
    const range = sel.getRangeAt(0)
    const cac = range.commonAncestorContainer
    const node = cac.nodeType === 3 ? cac.parentElement : (cac as HTMLElement)
    const host = node?.closest('.bcell, .rich') as HTMLElement | null
    if (!host) return
    mutate(range)
    host.dispatchEvent(new Event('input', { bubbles: true }))  // → React onInput → save
  }
  const bumpSel = (factor: number) => applySel((range) => {
    const span = document.createElement('span'); span.style.fontSize = `${factor}em`
    try {
      span.appendChild(range.extractContents()); range.insertNode(span)
      const s = window.getSelection(); s?.removeAllRanges(); const r = document.createRange(); r.selectNodeContents(span); s?.addRange(r)
    } catch { /* ignore */ }
  })

  // ---- Word-like TABLE editing. Structural edits run on the FULL body (the single
  //      source of truth), located by the caret cell's column and the row's stable id,
  //      then the body re-paginates automatically. ----
  const tableOp = (op: 'rowAbove' | 'rowBelow' | 'delRow' | 'colLeft' | 'colRight' | 'delCol' | 'delTable') => {
    const s = window.getSelection(); if (!s || !s.rangeCount) return
    const n = s.anchorNode
    const el = n ? (n.nodeType === 3 ? n.parentElement : (n as HTMLElement)) : null
    const td = el?.closest('td,th') as HTMLTableCellElement | null
    const trLive = el?.closest('tr') as HTMLTableRowElement | null
    if (!td || !trLive) return
    const colIndex = td.cellIndex
    const rowUid = trLive.getAttribute('data-r') || ''
    const scratch = document.createElement('div')
    scratch.innerHTML = normalizeBodyHtml(f.body)
    mergeAdjacentTables(scratch)
    normalizeTables(scratch)
    const tr = rowUid ? (scratch.querySelector(`tr[data-r="${cssEsc(rowUid)}"]`) as HTMLTableRowElement | null) : null
    const table = tr?.closest('table') as HTMLTableElement | null
    if (!table || !tr) return
    const rows = Array.from(table.rows)
    const mkCell = (proto: HTMLTableCellElement | undefined, tag: 'td' | 'th') => {
      const c = document.createElement(tag); const st = proto?.getAttribute('style'); if (st) c.setAttribute('style', st)
      c.appendChild(document.createElement('br')); return c
    }
    const newRow = () => {
      const r = document.createElement('tr'); r.setAttribute('data-r', uid())
      const cols = table.rows[0].cells.length
      for (let i = 0; i < cols; i++) r.appendChild(mkCell(table.rows[0].cells[i], 'td'))
      return r
    }
    if (op === 'rowAbove') tr.parentElement!.insertBefore(newRow(), tr)
    else if (op === 'rowBelow') tr.parentElement!.insertBefore(newRow(), tr.nextSibling)
    else if (op === 'delRow') { if (table.rows.length > 1) tr.remove(); else table.remove() }
    else if (op === 'colLeft' || op === 'colRight') {
      const at = op === 'colLeft' ? colIndex : colIndex + 1
      rows.forEach((r) => { const proto = r.cells[Math.min(colIndex, r.cells.length - 1)]; const c = mkCell(proto, (proto?.tagName === 'TH' ? 'th' : 'td')); if (at >= r.cells.length) r.appendChild(c); else r.insertBefore(c, r.cells[at]) })
    } else if (op === 'delCol') {
      rows.forEach((r) => { if (r.cells[colIndex] && r.cells.length > 1) r.deleteCell(colIndex) })
      if (!table.rows[0] || table.rows[0].cells.length === 0) table.remove()
    } else if (op === 'delTable') table.remove()
    setF((prev) => ({ ...prev, body: scratch.innerHTML }))
    setTbl(null)
  }
  // insert a fresh R×C table at the caret (or append to the body)
  const insertTable = () => {
    const R = parseInt(prompt('چند ردیف؟ (rows)', '3') || '0', 10)
    const C = parseInt(prompt('چند ستون؟ (columns)', '3') || '0', 10)
    if (!R || !C || R > 200 || C > 30) return
    let html = '<table>'
    for (let r = 0; r < R; r++) { html += `<tr data-r="${uid()}">`; for (let c = 0; c < C; c++) html += '<td><br></td>'; html += '</tr>' }
    html += '</table><div><br></div>'
    const sn = window.getSelection()?.anchorNode
    const host = sn ? ((sn.nodeType === 3 ? (sn as any).parentElement : (sn as HTMLElement)) as HTMLElement | null)?.closest?.('.bcell') as HTMLElement | null : null
    if (host) { host.focus(); document.execCommand('insertHTML', false, html) }
    else setF((prev) => ({ ...prev, body: (prev.body || '') + html }))
  }

  // ---- Reflow: merge hard-wrapped LINES (from PDF/line-broken pastes, or older saved
  //      letters) back into real flowing PARAGRAPHS so they justify like Word. A whole
  //      already-wrapping paragraph (one long block) is left untouched; the greeting,
  //      dash separators and tables stay on their own. Inline bold/underline survive. ----
  const reflowBody = (html: string): string => {
    if (!html || html.indexOf('<') === -1) return html
    const doc = document.createElement('div'); doc.innerHTML = html
    // wrap stray top-level text nodes so the block loop below never drops them
    Array.from(doc.childNodes).forEach((n) => { if (n.nodeType === 3 && (n.textContent || '').trim()) { const d = document.createElement('div'); d.textContent = n.textContent!; doc.replaceChild(d, n) } })
    const out: string[] = []
    let group: string[] = []
    const flush = () => { if (group.length) { out.push(`<div>${group.join(' ')}</div>`); group = [] } }
    const isDash = (t: string) => /^[-–—_.،؛:]{1,3}$/.test(t)
    const isGreet = (t: string) => /^با\s*سلام|^باسلام|سلام\s*و\s*احترام/.test(t)
    const ends = (t: string) => /[.؟!:]\s*$/.test(t)
    for (const el of Array.from(doc.children)) {
      if (el.tagName === 'TABLE') { flush(); out.push(el.outerHTML); continue }
      const segs = (el as HTMLElement).innerHTML.split(/<br\s*\/?>/i)
      for (const seg of segs) {
        const t = seg.replace(/<[^>]+>/g, '').replace(/ /g, ' ').trim()
        if (!t) { flush(); continue }                                   // blank line → paragraph break
        if (isDash(t)) { flush(); out.push(`<div>${seg}</div>`); continue }
        if (isGreet(t)) { flush(); out.push(`<div>${seg}</div>`); continue }
        group.push(seg)                                                 // a single visual line → merge…
        if (ends(t)) flush()                                            // …until a sentence terminator ends the paragraph
      }
    }
    flush()
    return out.join('') || html
  }
  const reflowPaste = (h: string) => reflowBody(cleanPaste(h))
  // one-time: make sure every table row in the body has a stable id (older saved letters
  // & fresh manual edits) so the table toolbar can find rows reliably.
  useEffect(() => {
    if (!f.body || f.body.indexOf('<table') === -1) return
    if (!/<tr(?![^>]*data-r)/i.test(f.body)) return
    const d = document.createElement('div'); d.innerHTML = f.body; normalizeTables(d)
    setF((s) => ({ ...s, body: d.innerHTML }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f.body])
  // show the floating format toolbar (on text selection) and the table toolbar (whenever
  // the caret sits inside a body table cell — even with nothing selected).
  useEffect(() => {
    const onSel = () => {
      const s = window.getSelection()
      const n = s?.anchorNode
      const el = n ? (n.nodeType === 3 ? n.parentElement : (n as HTMLElement)) : null
      // table toolbar
      const cell = (!designRef.current && el) ? (el.closest('.bcell td, .bcell th') as HTMLElement | null) : null
      if (cell) { const t = cell.closest('table')!.getBoundingClientRect(); setTbl({ x: t.left + t.width / 2, y: t.top }) }
      else setTbl(null)
      // selection format toolbar
      if (!s || s.isCollapsed || !s.rangeCount) { setFmt(null); return }
      if (!el || !el.closest('.bcell, .rich')) { setFmt(null); return }
      const r = s.getRangeAt(0).getBoundingClientRect()
      if (!r || (r.width === 0 && r.height === 0)) { setFmt(null); return }
      setFmt({ x: r.left + r.width / 2, y: r.top })
    }
    document.addEventListener('selectionchange', onSel)
    return () => document.removeEventListener('selectionchange', onSel)
  }, [])

  // contY = where the body continues on pages 2+ (just below the header; adjustable).
  const contY = L.body.contY ?? (Math.max(L.logo.y + (L.logo.h || 0), L.name.y + (L.name.h || 0)) + m(6))
  const gap = m(4)
  const pageNumLimit = (L.pagenum?.y ?? m(270)) - gap
  const closingTop = Math.min(L.sender.y, L.copyto.y, L.action.y) - gap
  // available body height on page `pi` (isLast pages reserve room for the closing block)
  const regionTop = (pi: number) => (pi === 0 ? L.body.y : contY)
  const regionAvail = (pi: number, isLast: boolean) => {
    const top = regionTop(pi)
    let base = pi === 0 ? (L.body.h || m(150)) : (pageNumLimit - top)
    if (isLast) base = Math.min(base, closingTop - top)
    return Math.max(24, base)
  }

  const boxStyle = (k: string): React.CSSProperties => {
    const b = L[k]
    let left = b.x, width = b.w
    if (k === 'separator' && sepGeom) { left = sepGeom.x; width = sepGeom.w }
    return {
      position: 'absolute', left, top: b.y, width, height: b.h,
      fontFamily: latin(b.font), fontSize: b.size ? `${b.size}pt` : undefined,
      // No field-level bold/underline — emphasis is applied INLINE to selected words.
      textAlign: b.justify ? 'justify' : b.align, direction: b.dir,
      textIndent: b.indent ? `${b.indent}em` : undefined,
      letterSpacing: b.ls ? `${b.ls}px` : undefined, lineHeight: b.lh || undefined,
      whiteSpace: k === 'subject' ? 'normal' : 'nowrap',
    }
  }
  const isHidden = (k: string) => !!L[k]?.hidden  // field removed for this letter
  // body text styling shared by every page's editable cell
  const bodyTextStyle = (): React.CSSProperties => {
    const b = L.body
    // NB: no fontWeight / textDecoration here — body bold/underline is INLINE only
    // (selected words), never the whole field.
    return {
      fontFamily: latin(b.font), fontSize: `${b.size}pt`,
      textAlign: b.justify ? 'justify' : b.align, direction: b.dir,
      lineHeight: b.lh || 1.7, letterSpacing: b.ls ? `${b.ls}px` : undefined,
    }
  }

  // ---- Pagination: distribute whole PARAGRAPHS across pages (so inline bold/
  //      underline tags are never sliced), reserving the closing block on the last page. ----
  const measureRef = useRef<HTMLDivElement>(null)
  const subjRef = useRef<HTMLSpanElement>(null)
  const [pages, setPages] = useState<string[]>([''])
  useEffect(() => {
    // Use the rendered off-screen measurer; if it isn't attached yet (e.g. a letter
    // loaded during mount, before refs settle), fall back to a temporary one so
    // pagination never silently no-ops and leaves the body blank.
    let el = measureRef.current
    const temp = !el
    if (!el) {
      el = document.createElement('div'); el.className = 'measure'
      el.style.cssText = `position:absolute;left:-99999px;top:0;visibility:hidden;white-space:pre-wrap;width:${L.body.w}px;font-size:${L.body.size}pt;line-height:${L.body.lh || 1.7}${L.body.font ? `;font-family:${L.body.font}` : ''}${L.body.ls ? `;letter-spacing:${L.body.ls}px` : ''}`
      document.body.appendChild(el)
    }
    el.innerHTML = normalizeBodyHtml(f.body || '') || '<div><br></div>'
    mergeAdjacentTables(el)
    // Flatten into atomic UNITS: plain blocks, and one unit per table body-row (so a
    // tall table can split across pages, its header repeated on each page).
    type Unit = { kind: 'block'; h: number; html: string } | { kind: 'trow'; h: number; tid: number; header: string; headerH: number; rowHtml: string }
    const units: Unit[] = []
    let tid = 0
    // recurse into wrappers so a table nested in a paste-wrapper <div> is still split
    const collect = (node: Element) => {
      for (const child of Array.from(node.children)) {
        const c = child as HTMLElement
        if (c.tagName === 'TABLE') {
          const rows = Array.from(c.querySelectorAll('tr'))
          if (rows.length > 1) {
            tid++
            const header = (rows[0] as HTMLElement).outerHTML, headerH = (rows[0] as HTMLElement).offsetHeight
            for (let i = 1; i < rows.length; i++) units.push({ kind: 'trow', tid, header, headerH, rowHtml: (rows[i] as HTMLElement).outerHTML, h: (rows[i] as HTMLElement).offsetHeight })
          } else units.push({ kind: 'block', html: c.outerHTML, h: c.offsetHeight })
        } else if (c.querySelector('table')) {
          collect(c)   // unwrap: promote the nested table (+ its siblings) to top-level units
        } else {
          units.push({ kind: 'block', html: c.outerHTML, h: c.offsetHeight })
        }
      }
    }
    collect(el)
    const pageH = (us: Unit[]) => { let h = 0; const seen = new Set<number>(); for (const u of us) { h += u.h; if (u.kind === 'trow' && !seen.has(u.tid)) { h += u.headerH; seen.add(u.tid) } } return h }
    const pages: Unit[][] = []
    let cur: Unit[] = [], used = 0, pi = 0
    const seen = new Set<number>()
    for (const u of units) {
      const need = u.h + ((u.kind === 'trow' && !seen.has(u.tid)) ? u.headerH : 0)
      if (cur.length && used + need > regionAvail(pi, false)) { pages.push(cur); cur = []; used = 0; pi++; seen.clear() }
      used += u.h + ((u.kind === 'trow' && !seen.has(u.tid)) ? u.headerH : 0)
      cur.push(u); if (u.kind === 'trow') seen.add(u.tid)
    }
    if (cur.length || !pages.length) pages.push(cur)
    // push trailing units off the last page until the closing block fits
    let guard = 0
    while (guard++ < 300) {
      const li = pages.length - 1
      if (pageH(pages[li]) <= regionAvail(li, true) || pages[li].length <= 1) break
      const moved: Unit[] = []
      while (pages[li].length > 1 && pageH(pages[li]) > regionAvail(li, true)) moved.unshift(pages[li].pop() as Unit)
      pages.push(moved)
    }
    // re-group consecutive rows of the same table back into one <table> per page
    const render = (us: Unit[]) => {
      let out = '', i = 0
      while (i < us.length) {
        const u = us[i]
        if (u.kind === 'block') { out += u.html; i++ }
        else { const t = u.tid, hdr = u.header; let rr = ''; while (i < us.length && us[i].kind === 'trow' && (us[i] as any).tid === t) { rr += (us[i] as any).rowHtml; i++ } out += `<table>${hdr}${rr}</table>` }
      }
      return out
    }
    setPages(pages.length ? pages.map(render) : [''])
    if (temp && el.parentNode) el.parentNode.removeChild(el)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f.body, L])

  // ---- Subject separator length follows the subject (capped at one full line) ----
  useEffect(() => {
    const el = subjRef.current
    if (!el) return
    el.textContent = plain(labels.subject) + plain(f.subject)
    const full = L.subject.w
    const w = Math.max(m(15), Math.min(el.offsetWidth + 4, full))
    setSepGeom({ x: (L.subject.x + L.subject.w) - w, w })
  }, [labels.subject, f.subject, L.subject])

  // replace one page's chunk and rebuild the whole body (chunks are consecutive slices)
  const onBody = (pi: number) => (val: string) => setF((s) => { const next = pages.slice(); next[pi] = val; return { ...s, body: next.join('') } })

  const Lbl = ({ k }: { k: string }) => (
    <RichSpan className="lbl-in" value={labels[k] ?? ''} onChange={(h) => setLabels((p) => ({ ...p, [k]: h }))} />
  )

  // an editable, draggable field box (page-1 top block, body, last-page closing)
  const Box = ({ k, children, style }: { k: string; children?: React.ReactNode; style?: React.CSSProperties }) => {
    const b = L[k]
    if (b.hidden) return null   // field removed for this letter
    return (
      <div className={`lbox${design ? ' dz' : ''}${sel === k && design ? ' seld' : ''}`} style={{ ...boxStyle(k), ...style }}
        onPointerDown={() => design && setSel(k)} onDoubleClick={(e) => { e.stopPropagation(); openPanel(k) }}>
        <div className="field-content">{children}</div>
        {design && <>
          <span className="bk-label">{k}</span>
          <span className="mv" onPointerDown={startDrag(k)} title="جابه‌جایی"><Move size={11} /></span>
          <span className="rs" onPointerDown={startResize(k)} title="تغییر اندازه" />
          {sel === k && b.size > 0 && <span className="fs-btns" onPointerDown={(e) => e.stopPropagation()}>
            <button className="fs-btn" onClick={() => bump(k, -1)}>A−</button>
            <button className="fs-btn" onClick={() => bump(k, +1)}>A＋</button>
            <button className="fs-btn" onClick={() => spc(k, -0.5)}>ف−</button>
            <button className="fs-btn" onClick={() => spc(k, +0.5)}>ف＋</button>
            {k === 'body' && <><button className="fs-btn" onClick={() => lnh(k, -0.1)}>خ−</button><button className="fs-btn" onClick={() => lnh(k, +0.1)}>خ＋</button></>}
          </span>}
        </>}
      </div>
    )
  }

  const eb = editing ? L[editing] : null
  const repImg = (k: string, src: string) => isHidden(k) ? null : <div style={boxStyle(k)}><img src={src} alt="" style={{ width: '100%', height: '100%' }} /></div>
  const P = (k: string, node: React.ReactNode) => isHidden(k) ? null : <div style={boxStyle(k)}>{node}</div>  // print: positioned, hide-aware
  const H = (h: string) => <span dangerouslySetInnerHTML={{ __html: h || '' }} />  // render a rich (HTML) value

  // one A4 page in the editable view
  const editorPage = (pi: number) => {
    const isLast = pi === pages.length - 1
    return (
      <div className="lsheet" key={pi}>
        {/* header + footer + page number repeat on every page (editable on page 1, mirrored after) */}
        {pi === 0 ? <>{Box({ k: 'logo', children: <img src={LH_LOGO} alt="" style={{ width: '100%', height: '100%' }} /> })}{Box({ k: 'name', children: <img src={LH_NAME} alt="" style={{ width: '100%', height: '100%' }} /> })}</>
          : <>{repImg('logo', LH_LOGO)}{repImg('name', LH_NAME)}</>}

        {pi === 0 && <>
          {Box({ k: 'besmele', children: Lbl({ k: 'besmele' }) })}
          {Box({ k: 'shomareh', children: <>{Lbl({ k: 'shomareh' })}<span dir="ltr" style={{ direction: 'ltr', unicodeBidi: 'isolate' }}>182 / 4 / <AutoInput dir="ltr" value={f.serial} onChange={set('serial')} placeholder="----" style={{ textAlign: 'center' }} /> / <AutoInput dir="ltr" value={f.year} onChange={set('year')} placeholder="2026" style={{ textAlign: 'center' }} /></span></> })}
          {Box({ k: 'tarikh', children: <>{Lbl({ k: 'tarikh' })}<AutoInput dir="ltr" value={f.date} onChange={set('date')} placeholder="2026/--/--" style={{ textAlign: 'right' }} /></> })}
          {Box({ k: 'peyvast', children: <>{Lbl({ k: 'peyvast' })}<select className="fld" value={f.attachment} onChange={set('attachment')}><option>دارد</option><option>ندارد</option></select></> })}
          {Box({ k: 'recName', children: <RichSpan value={f.recipientName} onChange={(h) => setF((s) => ({ ...s, recipientName: h }))} placeholder="سرکار خانم / جناب آقای …" /> })}
          {Box({ k: 'recTitle', children: <><RichSpan value={f.recipientTitle} onChange={(h) => setF((s) => ({ ...s, recipientTitle: h }))} placeholder="رئیس محترم" /> <RichSpan value={f.recipientDept} onChange={(h) => setF((s) => ({ ...s, recipientDept: h }))} placeholder="اداره کل خارجه" /></> })}
          {Box({ k: 'classification', children: <>{Lbl({ k: 'classification' })}<select className="fld" value={f.classification} onChange={set('classification')}>{CLASSES.map((c) => <option key={c}>{c}</option>)}</select></> })}
          {Box({ k: 'subject', children: <>{Lbl({ k: 'subject' })}<RichSpan value={f.subject} onChange={(h) => setF((s) => ({ ...s, subject: h }))} placeholder="موضوعِ نامه…" /></> })}
          {Box({ k: 'separator', children: <div className="sep-line" /> })}
        </>}

        {/* body chunk for this page — page 1 box is draggable/resizable; others fill the region */}
        {pi === 0
          ? Box({ k: 'body', children: <BodyCell html={pages[0] || ''} editable={!design} indent={L.body.indent} firstPage onChangeHtml={onBody(0)} transformPaste={reflowPaste} style={{ ...bodyTextStyle(), width: '100%', height: '100%' }} /> })
          : (isHidden('body') ? null : <BodyCell html={pages[pi] || ''} editable={!design} indent={L.body.indent} onChangeHtml={onBody(pi)} transformPaste={reflowPaste}
            style={{ ...bodyTextStyle(), position: 'absolute', left: L.body.x, top: contY, width: L.body.w, height: regionAvail(pi, isLast) }} />)}

        {/* closing block — only on the last page */}
        {isLast && <>
          {Box({ k: 'sender', children: <select className="fld" value={f.sender} onChange={set('sender')}>{SENDERS.map((s) => <option key={s}>{s}</option>)}</select> })}
          {Box({ k: 'copyto', children: <>{Lbl({ k: 'copyto' })}<RichSpan value={f.copyTo} onChange={(h) => setF((s) => ({ ...s, copyTo: h }))} placeholder="------" /></> })}
          {Box({ k: 'action', children: <>{Lbl({ k: 'action' })}<RichSpan value={f.actionName} onChange={(h) => setF((s) => ({ ...s, actionName: h }))} placeholder="----" />{Lbl({ k: 'actionExt' })}<AutoInput dir="ltr" value={f.actionExt} onChange={set('actionExt')} placeholder="---" style={{ textAlign: 'right' }} /></> })}
        </>}

        {pi === 0 ? Box({ k: 'footer', children: <img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /> }) : repImg('footer', LH_FOOTER)}
        {pi === 0
          ? Box({ k: 'pagenum', children: `صفحه ${fa(1)} از ${fa(pages.length)}` })
          : (isHidden('pagenum') ? null : <div style={{ ...boxStyle('pagenum'), pointerEvents: 'none' }}>{`صفحه ${fa(pi + 1)} از ${fa(pages.length)}`}</div>)}
      </div>
    )
  }

  // one A4 page in the print view (read-only values, paragraphs indented)
  const printPage = (pi: number) => {
    const isLast = pi === pages.length - 1
    return (
      <div className="psheet" key={pi}>
        {repImg('logo', LH_LOGO)}{repImg('name', LH_NAME)}
        {pi === 0 && <>
          {P('besmele', H(labels.besmele))}
          {P('shomareh', <>{H(labels.shomareh)}<span dir="ltr">{`182 / 4 / ${f.serial} / ${f.year}`}</span></>)}
          {P('tarikh', <>{H(labels.tarikh)}<span dir="ltr">{f.date}</span></>)}
          {P('peyvast', <>{H(labels.peyvast)}{f.attachment}</>)}
          {P('recName', H(f.recipientName))}
          {P('recTitle', <>{H(f.recipientTitle)} {H(f.recipientDept)}</>)}
          {P('classification', <>{H(labels.classification)}{f.classification}</>)}
          {P('subject', <>{H(labels.subject)}{H(f.subject)}</>)}
          {P('separator', <div className="sep-line" />)}
        </>}
        {!isHidden('body') && <div className={`bcell${pi === 0 ? ' firstpage' : ''}`} style={{ ...bodyTextStyle(), position: 'absolute', left: L.body.x, top: regionTop(pi), width: L.body.w, ['--ind' as any]: L.body.indent ? `${L.body.indent}em` : '0' }} dangerouslySetInnerHTML={{ __html: pages[pi] || '' }} />}
        {isLast && <>
          {P('sender', f.sender)}
          {P('copyto', <>{H(labels.copyto)}{H(f.copyTo)}</>)}
          {P('action', <>{H(labels.action)}{H(f.actionName)}{H(labels.actionExt)}<span dir="ltr">{f.actionExt}</span></>)}
        </>}
        {repImg('footer', LH_FOOTER)}
        {!isHidden('pagenum') && <div style={boxStyle('pagenum')}>{`صفحه ${fa(pi + 1)} از ${fa(pages.length)}`}</div>}
      </div>
    )
  }

  return (
    <Layout>
      <div dir="rtl">
        <style>{`
        /* English serif for LATIN LETTERS ONLY — Persian letters, digits (both ۰-۹ and
           0-9) and punctuation keep the chosen Persian font. */
        @font-face{font-family:'LtrMix';src:local('Times New Roman'),local('Times New Roman Regular'),local('Times');unicode-range:U+0041-005A,U+0061-007A,U+00C0-024F}
        .ltr-controls { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; }
        .ltr-btn { padding:8px 12px; border-radius:6px; font-weight:600; cursor:pointer; border:0; display:inline-flex; align-items:center; gap:6px; color:#fff; }
        .ltr-btn.blue{background:#2563eb}.ltr-btn.green{background:#16a34a}.ltr-btn.gray{background:#475569}.ltr-btn.amber{background:#d97706}
        .ltr-hint{font-size:12px;color:#64748b}
        .meta-in{border:1px solid #cbd5e1;border-radius:6px;padding:5px 8px;font-size:13px;background:#fff;color:#0f172a}
        .meta-in:focus{outline:none;border-color:#2563eb}
        .canvas-wrap { overflow:auto; padding-bottom:20px; }
        .lsheet,.psheet { position:relative; width:794px; height:1123px; margin:0 auto 18px; background:#fff; box-shadow:0 0 8px rgba(0,0,0,.18);
                          color:#000; font-family:${NAZ}; line-height:1.25; overflow:hidden; }
        .lbox .field-content { width:100%; height:100%; }
        #ltr-edit input.fld, #ltr-edit select, #ltr-edit .lbl-in { border:0; background:transparent; font:inherit; color:#000; padding:0; }
        #ltr-edit .lbl-in,#ltr-edit input.fld{text-align:inherit;letter-spacing:inherit}
        #ltr-edit select{cursor:pointer;width:auto}
        #ltr-edit input.fld::placeholder{color:#c7cfdb}
        #ltr-edit input.fld:focus,#ltr-edit .lbl-in:focus,#ltr-edit .bcell:focus{background:rgba(37,99,235,.06);border-radius:2px;outline:none}
        .bcell{width:100%;height:100%;overflow:hidden;outline:none;white-space:pre-wrap;word-break:normal;overflow-wrap:break-word}
        .bcell > div,.bcell > p{text-indent:var(--ind,0)}
        .bcell.firstpage > div:first-child,.bcell.firstpage > p:first-child{text-indent:0}
        /* pasted paragraphs shouldn't carry Word's big block margins (huge line gaps) */
        .bcell p,.psheet p,.measure p{margin:0}
        /* pasted tables fit the box width, stay COMPACT (content-height rows), with
           borders and sensible wrapping (no character-by-character breaking) */
        .bcell table,.psheet table,.measure table{width:100%!important;max-width:100%;border-collapse:collapse;margin:3px 0;font-size:inherit;table-layout:auto}
        .bcell td,.bcell th,.psheet td,.psheet th,.measure td,.measure th{border:0.6px solid #222;padding:2px 5px;vertical-align:top;white-space:normal;word-break:normal;overflow-wrap:break-word;line-height:1.35;text-indent:0!important}
        .bcell td *,.bcell th *,.psheet td *,.psheet th *,.measure td *,.measure th *{text-indent:0!important;margin:0}
        .bcell th,.psheet th,.measure th{font-weight:700;text-align:center;background:#f3f4f6}
        .bcell img,.psheet img{max-width:100%}
        /* inline rich fields (labels + values) — bold/underline per selected word */
        #ltr-edit .rich{display:inline;outline:none;text-align:inherit;letter-spacing:inherit;white-space:normal;overflow-wrap:break-word}
        #ltr-edit .rich:empty::before{content:attr(data-ph);color:#c7cfdb}
        #ltr-edit .rich:focus{background:rgba(37,99,235,.07);border-radius:2px}
        /* Word-like floating format toolbar (shown on text selection) */
        .fmt-bar{position:fixed;transform:translate(-50%,-118%);z-index:120;display:flex;gap:2px;align-items:center;background:#1f2937;border-radius:7px;padding:3px;box-shadow:0 6px 18px rgba(0,0,0,.32)}
        .fmt-bar button{border:0;background:transparent;color:#fff;min-width:26px;height:26px;padding:0 4px;border-radius:5px;cursor:pointer;font-size:14px}
        .fmt-bar button:hover{background:#374151}
        .fmt-bar .sep2,.tbl-bar .sep2{width:1px;height:16px;background:rgba(255,255,255,.28);margin:0 2px;flex:0 0 auto}
        /* floating TABLE toolbar (shown when the caret is inside a cell) */
        .tbl-bar{position:fixed;transform:translate(-50%,-135%);z-index:121;display:flex;gap:2px;align-items:center;background:#0f766e;border-radius:7px;padding:3px 4px;box-shadow:0 6px 18px rgba(0,0,0,.32)}
        .tbl-bar button{border:0;background:transparent;color:#fff;height:24px;min-width:26px;padding:0 5px;border-radius:5px;cursor:pointer;font-size:12px;font-family:sans-serif;line-height:1}
        .tbl-bar button:hover{background:#115e59}
        .tbl-bar button.del:hover{background:#b91c1c}
        .az-sizer{position:absolute;visibility:hidden;white-space:pre;top:0;right:0;font:inherit;letter-spacing:inherit;pointer-events:none}
        .sep-line{width:100%;border-top:1px dashed #000}
        .measure{position:absolute;left:-99999px;top:0;visibility:hidden;word-break:normal;overflow-wrap:break-word}
        .print-wrap{display:none}
        .lbox.dz{outline:1px dashed #93c5fd}
        .lbox.seld{outline:2px solid #2563eb;background:rgba(37,99,235,.05)}
        .bk-label{position:absolute;top:-15px;right:0;font-size:9px;color:#2563eb;background:#eff6ff;padding:0 3px;border-radius:3px;white-space:nowrap;font-family:sans-serif}
        .mv{position:absolute;top:-9px;left:-9px;width:18px;height:18px;background:#2563eb;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:move;z-index:6}
        .rs{position:absolute;right:-5px;bottom:-5px;width:13px;height:13px;background:#2563eb;border:2px solid #fff;border-radius:50%;cursor:nwse-resize;z-index:6}
        .fs-btns{position:absolute;bottom:-17px;left:0;display:flex;gap:2px;z-index:7}
        .fs-btn{font-size:9px;font-family:sans-serif;border:0;background:#2563eb;color:#fff;border-radius:3px;cursor:pointer;padding:1px 4px}
        .pp{position:fixed;top:108px;right:16px;z-index:60;width:194px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 10px 30px rgba(15,23,42,.22);padding:8px 9px 9px;font-family:sans-serif}
        .pp h4{font-size:11px;font-weight:700;margin:-2px -3px 7px;padding:5px 7px;color:#fff;background:linear-gradient(90deg,#2563eb,#1e40af);border-radius:8px;display:flex;justify-content:space-between;align-items:center;cursor:move;user-select:none}
        .pp .lblrow,.pp .selrow{margin-bottom:6px}
        .pp .lblrow input,.pp .selrow select{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:6px;padding:4px 6px;font-size:12px;background:#fff;color:#0f172a}
        .pp .pp-seg{display:flex;gap:3px;margin-bottom:6px}
        .pp .pp-seg input{flex:0 0 44px;border:1px solid #cbd5e1;border-radius:5px;padding:3px 4px;font-size:11px;text-align:center;min-width:0}
        .pp .pp-seg button{flex:1;border:1px solid #cbd5e1;background:#f8fafc;border-radius:5px;padding:4px 0;cursor:pointer;font-size:11px;color:#334155;line-height:1}
        .pp .pp-seg button.on{background:#2563eb;color:#fff;border-color:#2563eb}
        .pp .pp-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px 6px;margin-bottom:6px}
        .pp .pp-f{display:flex;flex-direction:column;gap:1px}
        .pp .pp-f>span{font-size:8.5px;color:#94a3b8;padding-right:2px}
        .pp .pp-f input,.pp .pp-f select{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:5px;padding:3px 4px;font-size:11px;background:#fff;color:#0f172a}
        .pp .x{border:0;background:rgba(255,255,255,.25);color:#fff;border-radius:5px;width:20px;height:20px;cursor:pointer;font-size:13px;line-height:1}
        .pp .pp-del{width:100%;border:0;background:#fee2e2;color:#b91c1c;border-radius:6px;padding:5px;cursor:pointer;font-size:11px;font-weight:600;margin-top:2px}
        .pp .pp-del:hover{background:#fecaca}
        .pp .pp-save{width:100%;border:0;background:#2563eb;color:#fff;border-radius:6px;padding:6px;cursor:pointer;font-size:12px;font-weight:600;margin-top:5px}
        @media print {
          @page { size:A4; margin:0; }
          html,body{margin:0!important;padding:0!important;background:#fff!important}
          .no-print,.pp{display:none!important}
          #ltr-edit{display:none!important}
          .print-wrap{display:block!important}
          .canvas-wrap{overflow:visible}
          .psheet{box-shadow:none;margin:0;break-after:page;page-break-after:always}
          .psheet:last-child{break-after:auto;page-break-after:auto}
        }
        `}</style>

        <div className="ltr-controls no-print">
          {!design
            ? <button onClick={() => setDesign(true)} className="ltr-btn amber"><Move size={15} /> چیدمان (جابه‌جایی فیلدها)</button>
            : <button onClick={() => { setDesign(false); setEditing(null) }} className="ltr-btn green"><Check size={15} /> پایانِ چیدمان</button>}
          {design && <button onClick={saveTemplate} className="ltr-btn blue">ذخیرهٔ چیدمان</button>}
          {design && <button onClick={resetTemplate} className="ltr-btn gray"><RotateCcw size={14} /> بازنشانی</button>}
          {design && Object.keys(L).some((k) => L[k].hidden) && (
            <select value="" onChange={(e) => { if (e.target.value) setBox(e.target.value, { hidden: false }) }} className="meta-in" title="بازگرداندنِ فیلدِ حذف‌شده">
              <option value="">بازگرداندنِ فیلدِ حذف‌شده…</option>
              {Object.keys(L).filter((k) => L[k].hidden).map((k) => <option key={k} value={k}>{KEY_FA[k] || k}</option>)}
            </select>
          )}
          <button onClick={() => { const subj = plain(f.subject), dept = plain(f.recipientDept); auditApi.logActivity({ action: 'print', entity_type: 'letter', detail: `صدورِ نامهٔ رسمی${subj ? ` — موضوع: ${subj}` : ''}${dept ? ` — به ${dept}` : ''}` }); window.print() }} className="ltr-btn blue"><Printer size={15} /> پرینت</button>
          <button onClick={insertTable} className="ltr-btn gray" title="افزودنِ جدولِ نو (بعد کلیک داخلِ متن)"><Table size={14} /> جدول</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={14} /> پاک‌کردن</button>
          <span className="ltr-hint">{`متن را بنویس؛ هر صفحه که پر شود، خودکار صفحهٔ جدید ساخته می‌شود (الان ${fa(pages.length)} صفحه). «چیدمان» = جابه‌جایی/تنظیمِ فیلدها (با دبل‌کلیک: چینش/جهت/تورفتگی).`}</span>
        </div>

        <div className="ltr-controls no-print" style={{ marginTop: -4 }}>
          <span className="ltr-hint" style={{ fontWeight: 600 }}>ذخیرهٔ نامه:</span>
          <input value={acct} onChange={(e) => setAcct(e.target.value)} disabled={general} placeholder="شمارهٔ حساب" className="meta-in" style={{ width: 120 }} />
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="عنوانِ نامه (اختیاری)" className="meta-in" style={{ width: 160 }} />
          <label className="ltr-hint" style={{ display: 'flex', alignItems: 'center', gap: 4 }}><input type="checkbox" checked={general} onChange={(e) => setGeneral(e.target.checked)} /> نامهٔ عمومی</label>
          <div style={{ width: 180 }}><Combobox value={plain(f.recipientDept)} placeholder="اداره/دایرهٔ گیرنده" fetch={fetchDepts}
            onChange={(v) => setF((s) => ({ ...s, recipientDept: v }))}
            onPick={(o) => setF((s) => ({ ...s, recipientDept: o.value, recipientName: o.data?.current_manager || plain(s.recipientName), recipientTitle: o.data?.manager_title || plain(s.recipientTitle) }))} /></div>
          <div style={{ width: 160 }}><Combobox value={plain(f.recipientName)} placeholder="مدیرِ دایره" fetch={fetchMgrs}
            onChange={(v) => setF((s) => ({ ...s, recipientName: v }))}
            onPick={(o) => setF((s) => ({ ...s, recipientName: o.value, recipientDept: o.data?.name || plain(s.recipientDept), recipientTitle: o.data?.manager_title || plain(s.recipientTitle) }))} /></div>
          <button onClick={saveLetter} disabled={savingLetter} className="ltr-btn green"><Save size={15} /> {savingLetter ? '...' : (letterId ? 'به‌روزرسانی' : 'ذخیره')}</button>
          <button onClick={newLetter} className="ltr-btn gray"><FilePlus size={14} /> نامهٔ جدید</button>
          {letterList.length > 0 && <div style={{ width: 230 }}>
            <Combobox value={letterQuery} placeholder="📂 بازکردنِ نامهٔ ذخیره‌شده…"
              fetch={async (q) => { const s = q.trim().toLowerCase(); return letterList.filter((l) => !s || `${l.title || ''} ${l.subject || ''} ${l.account_no || ''}`.toLowerCase().includes(s)).slice(0, 200).map((l) => ({ value: l.id, label: l.title || l.subject || 'نامه', sub: `${l.account_no || 'عمومی'}${l.updated_at ? ' — ' + new Date(l.updated_at).toLocaleDateString('en-GB') : ''}`, data: l })) }}
              onChange={setLetterQuery}
              onPick={(o) => { loadLetter(o.value); setLetterQuery('') }} />
          </div>}
        </div>

        {editing && eb && (
          <div className="pp no-print" style={ppPos ? { left: ppPos.x, top: ppPos.y, right: 'auto' } : undefined}>
            <h4 onPointerDown={startPanelDrag}><span>⠿ {KEY_FA[editing] || editing}</span><button className="x" onPointerDown={(e) => e.stopPropagation()} onClick={() => setEditing(null)}>×</button></h4>
            {labels[editing] !== undefined && (
              <div className="lblrow"><input value={labels[editing]} placeholder="متن/برچسب" onChange={(e) => setLabels((p) => ({ ...p, [editing]: e.target.value }))} /></div>
            )}
            {eb.size > 0 && <>
              <div className="selrow"><select value={eb.font || NAZ} onChange={(e) => setBox(editing, { font: e.target.value })}>{FONTS.map((ft) => <option key={ft.n} value={ft.v}>{ft.n}</option>)}</select></div>
              <div className="pp-seg">
                <input type="number" title="اندازهٔ فونت" value={eb.size} onChange={(e) => setBox(editing, { size: +e.target.value || 0 })} />
                <span style={{ flex: 1, fontSize: 9, color: '#94a3b8', alignSelf: 'center', textAlign: 'center' }}>بولد/زیرخط: کلمه را انتخاب کن</span>
              </div>
              <div className="pp-seg" title="چینش">
                {(['right', 'center', 'left'] as const).map((a) => <button key={a} className={(!eb.justify && (eb.align || 'right') === a) ? 'on' : ''} onClick={() => setBox(editing, { align: a, justify: false })}>{a === 'right' ? '≡راست' : a === 'center' ? 'وسط' : 'چپ≡'}</button>)}
                <button className={eb.justify ? 'on' : ''} onClick={() => setBox(editing, { justify: true })}>تراز</button>
              </div>
              <div className="pp-seg" title="جهتِ نوشتار">
                <button className={(eb.dir || 'rtl') === 'rtl' ? 'on' : ''} onClick={() => setBox(editing, { dir: 'rtl' })}>راست‑چپ</button>
                <button className={eb.dir === 'ltr' ? 'on' : ''} onClick={() => setBox(editing, { dir: 'ltr' })}>چپ‑راست</button>
              </div>
              <div className="pp-grid">
                <label className="pp-f"><span>فاصلهٔ حروف</span><input type="number" step="0.5" value={eb.ls || 0} onChange={(e) => setBox(editing, { ls: +e.target.value || 0 })} /></label>
                <label className="pp-f"><span>فاصلهٔ خط</span><input type="number" step="0.1" value={eb.lh || 1.25} onChange={(e) => setBox(editing, { lh: +e.target.value || undefined })} /></label>
                <label className="pp-f"><span>تورفتگیِ بند</span><input type="number" step="0.5" value={eb.indent ?? 0} onChange={(e) => setBox(editing, { indent: +e.target.value || 0 })} /></label>
                {editing === 'body' && <label className="pp-f"><span>Y صفحاتِ بعد</span><input type="number" value={Math.round(contY)} onChange={(e) => setBox('body', { contY: +e.target.value || 0 })} /></label>}
              </div>
            </>}
            <div className="pp-grid">
              <label className="pp-f"><span>عرض</span><input type="number" value={eb.w} onChange={(e) => setBox(editing, { w: +e.target.value || 0 })} /></label>
              {eb.h != null && <label className="pp-f"><span>ارتفاع</span><input type="number" value={eb.h} onChange={(e) => setBox(editing, { h: +e.target.value || 0 })} /></label>}
              <label className="pp-f"><span>X افقی</span><input type="number" value={eb.x} onChange={(e) => setBox(editing, { x: +e.target.value || 0 })} /></label>
              <label className="pp-f"><span>Y عمودی</span><input type="number" value={eb.y} onChange={(e) => setBox(editing, { y: +e.target.value || 0 })} /></label>
            </div>
            <button className="pp-del" onClick={() => { setBox(editing, { hidden: true }); setEditing(null) }}>🗑 حذفِ این فیلد از نامه</button>
            <button className="pp-save" onClick={saveTemplate}>ذخیرهٔ چیدمان</button>
          </div>
        )}

        {fmt && (
          <div className="fmt-bar no-print" style={{ left: fmt.x, top: fmt.y }}>
            <button title="توپُر (Ctrl+B)" style={{ fontWeight: 700 }} onMouseDown={(e) => { e.preventDefault(); document.execCommand('bold') }}>B</button>
            <button title="کج (Ctrl+I)" style={{ fontStyle: 'italic' }} onMouseDown={(e) => { e.preventDefault(); document.execCommand('italic') }}>I</button>
            <button title="زیرخط (Ctrl+U)" style={{ textDecoration: 'underline' }} onMouseDown={(e) => { e.preventDefault(); document.execCommand('underline') }}>U</button>
            <span className="sep2" />
            <button title="کوچک‌تر" onMouseDown={(e) => { e.preventDefault(); bumpSel(0.85) }}>A−</button>
            <button title="بزرگ‌تر" onMouseDown={(e) => { e.preventDefault(); bumpSel(1.18) }}>A＋</button>
            <span className="sep2" />
            <button title="راست‌چین" onMouseDown={(e) => { e.preventDefault(); document.execCommand('justifyRight') }}>▷</button>
            <button title="وسط‌چین" onMouseDown={(e) => { e.preventDefault(); document.execCommand('justifyCenter') }}>▽</button>
            <button title="چپ‌چین" onMouseDown={(e) => { e.preventDefault(); document.execCommand('justifyLeft') }}>◁</button>
            <button title="ترازِ دوطرفه (Justify)" onMouseDown={(e) => { e.preventDefault(); document.execCommand('justifyFull') }}>≣</button>
            <span className="sep2" />
            <button title="فهرستِ نقطه‌ای" onMouseDown={(e) => { e.preventDefault(); document.execCommand('insertUnorderedList') }}>•</button>
            <button title="فهرستِ شماره‌دار" onMouseDown={(e) => { e.preventDefault(); document.execCommand('insertOrderedList') }}>۱.</button>
          </div>
        )}

        {tbl && (
          <div className="tbl-bar no-print" style={{ left: tbl.x, top: tbl.y }} onMouseDown={(e) => e.preventDefault()}>
            <button title="افزودنِ ردیف بالا" onClick={() => tableOp('rowAbove')}>▤↑</button>
            <button title="افزودنِ ردیف پایین" onClick={() => tableOp('rowBelow')}>▤↓</button>
            <button title="حذفِ ردیف" className="del" onClick={() => tableOp('delRow')}>▤✕</button>
            <span className="sep2" />
            <button title="افزودنِ ستون (راست)" onClick={() => tableOp('colRight')}>▥←</button>
            <button title="افزودنِ ستون (چپ)" onClick={() => tableOp('colLeft')}>▥→</button>
            <button title="حذفِ ستون" className="del" onClick={() => tableOp('delCol')}>▥✕</button>
            <span className="sep2" />
            <button title="حذفِ کلِ جدول" className="del" onClick={() => tableOp('delTable')}>🗑</button>
          </div>
        )}

        {/* hidden measurers — body height/pagination and subject width (for the separator) */}
        <div ref={measureRef} aria-hidden className="measure" style={{ width: L.body.w, fontFamily: L.body.font, fontSize: `${L.body.size}pt`, lineHeight: L.body.lh || 1.7, letterSpacing: L.body.ls ? `${L.body.ls}px` : undefined, whiteSpace: 'pre-wrap' }} />
        <span ref={subjRef} aria-hidden className="measure" style={{ whiteSpace: 'nowrap', fontFamily: L.subject.font, fontSize: `${L.subject.size}pt` }} />

        {/* ---- EDITABLE PAGINATED VIEW (screen) ---- */}
        <div id="ltr-edit" className="canvas-wrap" onDoubleClick={exitEditing}>
          {pages.map((_, pi) => editorPage(pi))}
        </div>

        {/* ---- PRINT VIEW (read-only values) ---- */}
        <div className="canvas-wrap print-wrap">
          {pages.map((_, pi) => printPage(pi))}
        </div>
      </div>
    </Layout>
  )
}
