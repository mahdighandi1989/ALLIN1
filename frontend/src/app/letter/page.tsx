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
import { Printer, Eraser, Move, Check, RotateCcw, Save, FilePlus, Table, Sparkles, X, Image as ImageIcon, Download } from 'lucide-react'
import { auditApi, crmApi, departmentsApi, lettersApi, letterAiApi, parseApiError, downloadFile } from '@/lib/api'
import type { LetterAiChange, LetterAiModel, LetterAiTool, LetterAttachment } from '@/lib/api'
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
// Persian digits inside a rich (HTML) value — text nodes only, so tags/attrs
// (style="font-size:12px") are never touched. Used for the SUBJECT field: an
// account number typed there must default to Persian digits, not Latin ones.
const faDigitsHtml = (h: string) => {
  if (!/[0-9٠-٩]/.test(h || '')) return h
  const d = document.createElement('div')
  d.innerHTML = h || ''
  const walk = document.createTreeWalker(d, NodeFilter.SHOW_TEXT)
  let n: Node | null
  while ((n = walk.nextNode())) {
    n.nodeValue = (n.nodeValue || '')
      .replace(/[0-9]/g, (c) => '۰۱۲۳۴۵۶۷۸۹'[+c])
      .replace(/[٠-٩]/g, (c) => '۰۱۲۳۴۵۶۷۸۹'[c.charCodeAt(0) - 0x0660])
  }
  return d.innerHTML
}
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
// Capture the current selection as text offsets within `el` (start & end, so a whole
// selection — not just the caret — survives a re-render and stays highlighted; that lets
// a floating-toolbar button be clicked repeatedly on the same selection).
function selOffsets(el: HTMLElement): { start: number; end: number } | null {
  const s = window.getSelection(); if (!s || !s.rangeCount) return null
  const r = s.getRangeAt(0); if (!el.contains(r.commonAncestorContainer)) return null
  const pre = r.cloneRange(); pre.selectNodeContents(el); pre.setEnd(r.startContainer, r.startOffset)
  const start = pre.toString().length
  return { start, end: start + r.toString().length }
}
// Legacy caret offset (single point) — kept for callers that only need the caret.
function caretOffset(el: HTMLElement): number | null { const o = selOffsets(el); return o ? o.end : null }
function posAt(el: HTMLElement, off: number): { node: Node; off: number } {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n: Node | null, c = off, last: Node | null = null
  while ((n = w.nextNode())) { last = n; const len = (n.textContent || '').length; if (len >= c) return { node: n, off: c }; c -= len }
  return last ? { node: last, off: (last.textContent || '').length } : { node: el, off: 0 }
}
function setSel(el: HTMLElement, start: number, end?: number) {
  const a = posAt(el, start), b = end == null ? a : posAt(el, end)
  try { const r = document.createRange(); r.setStart(a.node, a.off); r.setEnd(b.node, b.off); const s = window.getSelection(); s?.removeAllRanges(); s?.addRange(r) } catch { /* ignore */ }
}
function setCaret(el: HTMLElement, off: number) { setSel(el, off) }
// Plain text → paragraph HTML (legacy bodies are plain); rich bodies already carry tags.
function normalizeBodyHtml(s: string): string {
  if (!s) return ''
  if (s.indexOf('<') === -1) return s.split('\n').map((line) => `<div>${escapeHtml(line) || '<br>'}</div>`).join('')
  return s
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
      const sel = foc ? selOffsets(el) : null
      el.innerHTML = want
      if (sel) setSel(el, sel.start, sel.end)   // keep the whole selection (stays highlighted)
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

// ---- AI-assistant apply helpers ----
// Which letter fields store rich HTML (so a set_field value must be escaped, and a
// text_replace must run on text nodes only, never inside tags).
const RICH_FIELDS = new Set(['subject', 'recipientName', 'recipientTitle', 'recipientDept', 'copyTo', 'actionName', 'body'])
// SURGICAL text replace: only ever rewrites the content of a single TEXT NODE, so
// inline bold/underline spans, tables and every other tag survive untouched. The
// replacement is inserted as literal text (never parsed as HTML). Returns the new
// HTML and how many occurrences were applied (0 = the snippet wasn't locatable in
// one node → the caller skips it, exactly like the backend's find-guard).
function applyTextReplaceHtml(value: string, find: string, replace: string, occurrence: 'first' | 'all'): [string, number] {
  if (!find) return [value, 0]
  const isHtml = value.indexOf('<') !== -1
  const container = document.createElement('div')
  if (isHtml) container.innerHTML = value
  else container.textContent = value  // plain field → safe text node
  let applied = 0
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
  const nodes: Text[] = []
  let n: Node | null
  while ((n = walker.nextNode())) nodes.push(n as Text)
  for (const node of nodes) {
    const text = node.textContent || ''
    if (occurrence === 'all') {
      if (text.indexOf(find) !== -1) { const parts = text.split(find); applied += parts.length - 1; node.textContent = parts.join(replace) }
    } else {
      const idx = text.indexOf(find)
      if (idx !== -1) { node.textContent = text.slice(0, idx) + replace + text.slice(idx + find.length); applied++; break }
    }
  }
  // FUZZY fallback (v51): the model's snippet often differs from the letter in
  // ways invisible to the eye — Arabic ي/ك vs Persian ی/ک, ZWNJ vs space,
  // doubled spaces — or spans SEVERAL text nodes (a whole-paragraph rewrite
  // crossing a <b>/<br>). Match on a canonical, space-collapsed view of the
  // WHOLE field with an index map back to the original characters, then splice
  // across the affected nodes (replacement lands in the first one).
  if (applied === 0) {
    const canon = (c: string) =>
      c === 'ي' ? 'ی' : c === 'ك' ? 'ک'
        : /[\s‌‎‏ ]/.test(c) ? ' ' : c
    const build = (src: string): { out: string; map: number[] } => {
      let out = ''
      const map: number[] = []
      let prevSpace = true
      for (let i = 0; i < src.length; i++) {
        const c = canon(src[i])
        if (c === ' ') { if (prevSpace) continue; prevSpace = true } else prevSpace = false
        out += c
        map.push(i)
      }
      while (out.endsWith(' ')) { out = out.slice(0, -1); map.pop() }
      return { out, map }
    }
    const full = nodes.map((nd) => nd.textContent || '').join('')
    const H = build(full)
    const F = build(find).out
    const at = F ? H.out.indexOf(F) : -1
    if (at !== -1) {
      const s = H.map[at]
      const e = H.map[at + F.length - 1] + 1
      let off = 0
      let inserted = false
      for (const node of nodes) {
        const t = node.textContent || ''
        const ns = off, ne = off + t.length
        off = ne
        if (ne <= s || ns >= e) continue
        const ls = Math.max(0, s - ns), le = Math.min(t.length, e - ns)
        node.textContent = t.slice(0, ls) + (inserted ? '' : replace) + t.slice(le)
        inserted = true
      }
      if (inserted) applied = 1
    }
  }
  return [isHtml ? container.innerHTML : (container.textContent || ''), applied]
}

// An inline, auto-sizing, rich (contentEditable) field. Stores HTML so bold/underline
// can be applied to SELECTED words only (via the floating toolbar). Caret-preserving.
function RichSpan({ value, onChange, placeholder, dir, className, style, multiline }:
  { value: string; onChange: (h: string) => void; placeholder?: string; dir?: 'ltr' | 'rtl'; className?: string; style?: React.CSSProperties; multiline?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  useIso(() => {
    const el = ref.current; if (!el) return
    const want = value || ''
    if (el.innerHTML !== want) {
      const foc = document.activeElement === el
      const sel = foc ? selOffsets(el) : null
      el.innerHTML = want
      if (sel) setSel(el, sel.start, sel.end)
    }
  }, [value])
  return <span ref={ref} className={`rich ${className || ''}`} contentEditable suppressContentEditableWarning dir={dir}
    data-ph={placeholder || ''} onInput={() => { const el = ref.current; if (el) onChange(el.innerHTML) }} style={style}
    onKeyDown={multiline ? (e) => {
      // uniform multi-line: Enter always inserts a <br> (never a nested <div>)
      if (e.key === 'Enter') { e.preventDefault(); document.execCommand('insertLineBreak'); const el = ref.current; if (el) onChange(el.innerHTML) }
    } : undefined} />
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
    classification: 'داخلی', serial: '', year: String(new Date().getFullYear()),
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
  const [subjFit, setSubjFit] = useState<number | null>(null)  // shrunk-to-one-line subject font (pt)
  const [sepShift, setSepShift] = useState(0)                  // separator pushed below a WRAPPED subject
  const [fmt, setFmt] = useState<{ x: number; y: number } | null>(null)        // floating bold/underline toolbar
  const [tbl, setTbl] = useState<{ x: number; y: number } | null>(null)        // floating table toolbar (caret in a cell)
  const [colRz, setColRz] = useState<{ top: number; height: number; left: number; width: number; hdrUid: string; bounds: { x: number; i: number }[]; rowBounds: { y: number; uid: string; topEdge?: boolean }[] } | null>(null) // column/row/edge resize handles
  const [dropInd, setDropInd] = useState<{ x: number; y: number; w: number } | null>(null) // drag-a-table drop line
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

  // --- AI assistant («دستیار هوشمند») — propose reviewable edits, apply only ticked ones ---
  const DEFAULT_TOOLS = ['spelling', 'grammar', 'paragraphs', 'consistency', 'professional', 'complete', 'inline_prompts', 'full_check']
  const [aiOpen, setAiOpen] = useState(false)
  const [aiModels, setAiModels] = useState<LetterAiModel[]>([])
  const [aiTools, setAiTools] = useState<LetterAiTool[]>([])
  const [aiModelsLoaded, setAiModelsLoaded] = useState(false)
  const [aiModelId, setAiModelId] = useState<number | ''>('')     // '' = auto (top-priority model)
  const [aiSelTools, setAiSelTools] = useState<string[]>(DEFAULT_TOOLS)
  const [aiInstruction, setAiInstruction] = useState('')
  // Collected snippets to validate against the DB — the user builds this list by
  // selecting text in the letter and pressing «افزودن به اعتبارسنجی» on the
  // floating toolbar (so MANY, separate pieces can be gathered, not just one).
  const [aiSelections, setAiSelections] = useState<string[]>([])
  const [aiLoading, setAiLoading] = useState(false)
  const [aiRan, setAiRan] = useState(false)
  const [aiError, setAiError] = useState('')
  const [aiModelUsed, setAiModelUsed] = useState('')
  const [aiFactsUsed, setAiFactsUsed] = useState(false)
  const [aiChanges, setAiChanges] = useState<LetterAiChange[]>([])
  const [aiChecked, setAiChecked] = useState<Record<string, boolean>>({})

  const CAT_FA: Record<string, string> = { spelling: 'املایی', grammar: 'نگارشی', paragraphs: 'پاراگراف', tables: 'جدول', consistency: 'مغایرت', professional: 'حرفه‌ای‌سازی', validation: 'اعتبارسنجی', db_extract: 'ثبت در پایگاه‌داده', complete: 'تکمیلِ ناتمام‌ها', inline_prompts: 'دستورِ داخلِ متن', other: 'سایر' }

  // --- Letter attachments (پیوست‌ها) — enabled when the letter says «دارد».
  // Files go through the shared crm attachment endpoint (Drive with traceable
  // names + disk fallback) scoped as facility_id=LTR-<letterId>, so they also
  // show under the customer profile automatically. ---
  const [attsOpen, setAttsOpen] = useState(false)
  const [letterAtts, setLetterAtts] = useState<LetterAttachment[]>([])
  const [attUploading, setAttUploading] = useState(false)
  const [extracting2, setExtracting2] = useState('')   // progress text while extracting attachments
  // Which attachments the extraction tool should read — user-pickable. Default:
  // selected, EXCEPT AI-generated ones (ساختِ AI): their content came OUT of the
  // database, so extracting them back in would be a circular write. Explicit
  // tick still allowed.
  const [aiSelAtts, setAiSelAtts] = useState<Record<string, boolean>>({})
  const attSelected = (a: LetterAttachment) => aiSelAtts[a.id] ?? !a.ai_generated
  const selectedAttCount = letterAtts.filter((a) => attSelected(a)).length

  // --- AI attachment GENERATOR (ساختِ پیوست با هوش مصنوعی): the user describes
  // the file, the model proposes a strict spec from DB facts + the letter's tone,
  // the SERVER validates and renders a real xlsx/docx and registers it like an
  // uploaded پیوست (Drive/دیسک + پروفایل مشتری). ---
  const [genOpen, setGenOpen] = useState(false)
  const [genInstruction, setGenInstruction] = useState('')
  const [genKind, setGenKind] = useState<'' | 'excel' | 'word'>('')   // '' = auto
  const [genBusy, setGenBusy] = useState(false)
  const [genWarnings, setGenWarnings] = useState<string[]>([])
  // v63: optional TEMPLATE/SAMPLE file (e.g. a blank table another department
  // sent) — the generated attachment must reproduce ITS exact format.
  const [genTpl, setGenTpl] = useState<File | null>(null)
  // v65: optional SOURCE/DATA files (any count, any format, added any time) —
  // their CONTENT is an allowed data source for the generation, alongside DB.
  const [genSrcs, setGenSrcs] = useState<File[]>([])

  // --- Tables tool: enumerate the letter's tables (across all pages — the body
  // is the single source of truth) so the user picks WHICH ones the AI works on.
  // Each table is identified by its header row's stable data-r uid.
  type BodyTable = { uid: string; html: string; label: string; attId?: string }
  const getBodyTables = (): BodyTable[] => {
    const out: BodyTable[] = []
    if (f.body && f.body.indexOf('<table') !== -1) {
      const d = document.createElement('div')
      d.innerHTML = normalizeBodyHtml(f.body)
      mergeAdjacentTables(d)
      normalizeTables(d)
      ;(Array.from(d.querySelectorAll('table')) as HTMLTableElement[]).forEach((t, i) => {
        const rows = t.rows.length, cols = t.rows[0]?.cells.length || 0
        const first = (t.rows[0]?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40)
        out.push({
          uid: t.rows[0]?.getAttribute('data-r') || `t${i}`,
          html: t.outerHTML,
          label: `جدول ${fa(i + 1)} — ${fa(rows)}×${fa(cols)}${first ? ` («${first}…»)` : ''}`,
        })
      })
    }
    // attachment tables are just as pickable — the AI gets full control over them too
    attTables.forEach((t, i) => {
      const d = document.createElement('div')
      d.innerHTML = t.html
      normalizeTables(d)
      const tbl = d.querySelector('table') as HTMLTableElement | null
      if (!tbl) return
      const rows = tbl.rows.length, cols = tbl.rows[0]?.cells.length || 0
      out.push({
        uid: tbl.rows[0]?.getAttribute('data-r') || t.id,
        html: tbl.outerHTML,
        label: `جدول ${fa(i + 1)} پیوست — ${fa(rows)}×${fa(cols)}${plain(t.title) ? ` («${plain(t.title).slice(0, 40)}»)` : ''}`,
        attId: t.id,
      })
    })
    return out
  }
  const [aiSelTables, setAiSelTables] = useState<Record<string, boolean>>({})
  const tblSelected = (uid: string) => aiSelTables[uid] !== false   // default: selected
  // the tables actually SENT with the last analyze (index → uid + owner), so
  // table_replace results land on the exact right table — body or attachment.
  const sentTableUidsRef = useRef<{ uid: string; attId?: string }[]>([])

  // --- ATTACHMENT TABLES (جدول‌های پیوست): tables registered as letter پیوست‌ها.
  // Unlike file attachments they are rendered as their OWN letterhead pages after
  // the letter's last (closing) page, in order. Sizing is automatic: a table whose
  // natural width doesn't fit portrait flips the page to LANDSCAPE (on screen the
  // sheet simply becomes wider — text is never rotated, so editing stays normal);
  // a too-tall table steps its font down before admitting defeat with a warning.
  // Stored inside values_json alongside the letter fields. ---
  type AttTable = { id: string; title: string; html: string; offY?: number }
  const [attTables, setAttTables] = useState<AttTable[]>([])
  const [attMeta, setAttMeta] = useState<Record<string, { land: boolean; scale: number; tooTall: boolean }>>({})
  const ATT_MARGIN = m(15)                       // side margins of an attachment page
  const ATT_TOP = m(40)                          // content starts below the letterhead
  const ATT_BOTTOM = m(24)                       // clear of footer + page number
  const ATT_TITLE_H = 46                         // title row above the table
  const PAGE_W = 794, PAGE_H = 1123              // A4 @96dpi (portrait)
  const updateAttTable = (id: string, patch: Partial<AttTable>) =>
    setAttTables((list) => list.map((t) => (t.id === id ? { ...t, ...patch } : t)))
  const removeAttTable = (id: string) => setAttTables((list) => list.filter((t) => t.id !== id))

  // --- BEHIND-TEXT floats (Word's «پشتِ متن»): tables/images lifted OUT of the text
  // flow onto a free layer UNDER the text of one letter page. They never affect
  // pagination; position/size are absolute on the sheet. Stored in values_json. ---
  type FloatObj = { id: string; kind: 'table' | 'image'; html: string; x: number; y: number; w: number; w0: number; page: number }
  const [floats, setFloats] = useState<FloatObj[]>([])
  const [floatSel, setFloatSel] = useState<string | null>(null)
  const updateFloat = (id: string, patch: Partial<FloatObj>) =>
    setFloats((list) => list.map((x) => (x.id === id ? { ...x, ...patch } : x)))
  const removeFloat = (id: string) => { setFloats((list) => list.filter((x) => x.id !== id)); setFloatSel((v) => (v === id ? null : v)) }
  const letterSheets = () => Array.from(document.querySelectorAll('#ltr-edit .lsheet:not(.attsheet)')) as HTMLElement[]
  const letterCells = () => (Array.from(document.querySelectorAll('#ltr-edit .lsheet:not(.attsheet) .bcell')) as HTMLElement[]).filter((c) => !c.closest('.lfloat'))
  // Auto-size every attachment table: orientation by NATURAL width, then font
  // step-down if it's still too tall for one page.
  useEffect(() => {
    if (!attTables.length) { setAttMeta({}); return }
    const holder = document.createElement('div')
    holder.style.cssText = 'position:absolute;left:-99999px;top:0;visibility:hidden'
    document.body.appendChild(holder)
    const meta: Record<string, { land: boolean; scale: number; tooTall: boolean }> = {}
    const PORT_W = PAGE_W - 2 * ATT_MARGIN, LAND_W = PAGE_H - 2 * ATT_MARGIN
    const PORT_H = PAGE_H - ATT_TOP - ATT_TITLE_H - ATT_BOTTOM, LAND_H = PAGE_W - ATT_TOP - ATT_TITLE_H - ATT_BOTTOM
    for (const t of attTables) {
      // natural (unconstrained) width — in a huge container the table shrinks to fit content
      const free = document.createElement('div')
      free.style.cssText = 'width:2600px;font-size:13pt;line-height:1.7'
      free.innerHTML = t.html
      holder.appendChild(free)
      const naturalW = (free.querySelector('table') as HTMLElement | null)?.offsetWidth || 0
      holder.removeChild(free)
      const land = naturalW > PORT_W
      const availW = land ? LAND_W : PORT_W, availH = land ? LAND_H : PORT_H
      // height at the real width (the .measure class carries the exact table CSS)
      let scale = 1, tooTall = false
      for (const s of [1, 0.85, 0.72, 0.6]) {
        scale = s
        const box = document.createElement('div')
        box.className = 'measure'
        box.style.cssText = `position:static;visibility:hidden;width:${availW}px;font-size:${13 * s}pt;line-height:1.7;white-space:pre-wrap`
        box.innerHTML = t.html
        holder.appendChild(box)
        const hh = box.offsetHeight
        holder.removeChild(box)
        if (hh <= availH) { tooTall = false; break }
        tooTall = true
      }
      meta[t.id] = { land, scale, tooTall }
    }
    document.body.removeChild(holder)
    setAttMeta(meta)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attTables])
  const loadAtts = async (id: string | null) => {
    if (!id) { setLetterAtts([]); return }
    try { setLetterAtts(await lettersApi.attachments(id)) } catch { setLetterAtts([]) }
  }
  useEffect(() => { loadAtts(letterId) /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [letterId])
  const uploadAtt = async (file?: File | null) => {
    if (!file) return
    if (!letterId) { toast.error('اول نامه را «ذخیره» کن تا پیوست به آن گره بخورد'); return }
    if (!acct.trim() && !general) { toast.error('شمارهٔ حساب نامه لازم است'); return }
    setAttUploading(true)
    try {
      await crmApi.uploadAttachment(acct.trim() || 'general', file, {
        facility_id: `LTR-${letterId}`,
        notes: `پیوست نامه${plain(f.subject) ? ` — ${plain(f.subject)}` : ''}`,
      })
      toast.success(`پیوست «${file.name}» بارگذاری شد (Drive/آرشیو + پروفایل مشتری)`)
      await loadAtts(letterId)
    } catch (e) { toast.error(parseApiError(e)) } finally { setAttUploading(false) }
  }
  const deleteAtt = async (id: string, name: string) => {
    if (!confirm(`حذفِ پیوست «${name}»؟`)) return
    try { await crmApi.deleteAttachment(id); await loadAtts(letterId) } catch (e) { toast.error(parseApiError(e)) }
  }
  // Open an attachment in a NEW TAB (view, not download) — authed blob, same
  // pattern as the customer profile. The browser shows/prints PDFs and images
  // inline; Office files open in their app.
  const viewAtt = async (id: string) => {
    const win = window.open('', '_blank')
    try {
      const blob = await crmApi.attachmentBlob(id)
      const url = URL.createObjectURL(blob)
      if (win) win.location.href = url
      else window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) { if (win) win.close(); toast.error(parseApiError(e)) }
  }
  const toggleGen = () => {
    setGenOpen((v) => !v)
    // the generator uses the same model list as the assistant — lazy-load it here too
    if (!aiModelsLoaded) {
      letterAiApi.models().then((r) => { setAiModels(r.models || []); setAiTools(r.tools || []); setAiModelsLoaded(true) })
        .catch(() => { setAiTools([]); setAiModelsLoaded(true) })
    }
  }
  const generateAtt = async () => {
    if (!letterId) { toast.error('اول نامه را «ذخیره» کن تا پیوست به آن گره بخورد'); return }
    const inst = genInstruction.trim()
    if (inst.length < 3 && !genTpl) { toast.error('شرحِ پیوست را بنویس یا فایلِ قالب/نمونه را انتخاب کن (حداقل یکی)'); return }
    setGenBusy(true); setGenWarnings([])
    try {
      // TEMPLATE first: the sample file (any format) becomes text the model must
      // reproduce exactly — read server-side, nothing stored.
      let tplText = ''
      let tplName = ''
      if (genTpl) {
        setExtracting2(`خواندنِ قالب: ${genTpl.name}…`)
        const tx = await letterAiApi.templateText(genTpl, aiModelId === '' ? undefined : Number(aiModelId))
        if (!tx.ok || !(tx.text || '').trim()) {
          toast.error(`قالب «${genTpl.name}» خوانده نشد: ${aiErrorText(tx.error)}`)
          return
        }
        tplText = tx.text || ''
        tplName = genTpl.name
      }
      // SOURCE/DATA files: each one becomes text too (same no-store endpoint) —
      // their content is an allowed data source alongside the DB facts. A file
      // that cannot be read aborts with a clear error (silent partial data would
      // produce a wrong attachment).
      const srcTexts: { name: string; text: string }[] = []
      for (let i = 0; i < genSrcs.length; i++) {
        const sf = genSrcs[i]
        setExtracting2(`خواندنِ فایلِ منبع ${fa(i + 1)} از ${fa(genSrcs.length)}: ${sf.name}…`)
        const tx = await letterAiApi.templateText(sf, aiModelId === '' ? undefined : Number(aiModelId))
        if (!tx.ok || !(tx.text || '').trim()) {
          toast.error(`فایلِ منبع «${sf.name}» خوانده نشد: ${aiErrorText(tx.error)}`)
          return
        }
        srcTexts.push({ name: sf.name, text: tx.text || '' })
      }
      setExtracting2('')
      const r = await letterAiApi.generateAttachment({
        letter_id: letterId,
        account_no: general ? undefined : (acct.trim() || undefined),
        instruction: inst,
        kind: genKind || undefined,
        subject: plain(f.subject) || undefined,
        recipient: plain(f.recipientName) || undefined,
        body_excerpt: plain(f.body).slice(0, 1500) || undefined,
        model_id: aiModelId === '' ? undefined : Number(aiModelId),
        template_text: tplText || undefined,
        template_name: tplName || undefined,
        source_files: srcTexts.length ? srcTexts : undefined,
      })
      if (!r.ok) {
        toast.error((r.error || '').startsWith('bad_spec')
          ? 'خروجی مدل ساختارِ معتبری نداشت؛ دستور را شفاف‌تر بنویس یا دوباره تلاش کن.'
          : aiErrorText(r.error))
        return
      }
      setGenWarnings(r.warnings || [])
      toast.success(`پیوست «${r.attachment?.original_name || ''}» ساخته و ثبت شد (${r.kind === 'word' ? 'ورد' : 'اکسل'})`)
      setGenInstruction(''); setGenTpl(null); setGenSrcs([])
      await loadAtts(letterId)
    } catch (e) { toast.error(parseApiError(e)) } finally { setGenBusy(false); setExtracting2('') }
  }
  const hasAttachmentMode = f.attachment === 'دارد'
  const SEV_COLOR: Record<string, string> = { low: '#64748b', medium: '#d97706', high: '#dc2626' }
  const SEV_FA: Record<string, string> = { low: 'کم', medium: 'متوسط', high: 'زیاد' }

  const AI_MAX_SELECTIONS = 12
  // Capture the CURRENT text selection (from the body or any rich field) and add
  // it to the validation list. Called from the floating toolbar's shield button —
  // it reads the live selection BEFORE the click clears it. De-dups + caps.
  const addAiSelection = (): boolean => {
    const raw = (typeof window !== 'undefined' ? window.getSelection()?.toString() : '') || ''
    const t = raw.replace(/\s+/g, ' ').trim()
    if (!t) { toast.error('اول یک عبارت را در متن انتخاب کن'); return false }
    // Enable the validation tool here (synchronously) — NOT inside the setAiSelections
    // updater, which React runs asynchronously during render (a flag set there is
    // still stale on the next line).
    setAiSelTools((s) => s.includes('validation') ? s : [...s, 'validation'])
    setAiSelections((s) => {
      if (s.includes(t)) { toast('این عبارت قبلاً افزوده شده'); return s }
      if (s.length >= AI_MAX_SELECTIONS) { toast.error(`حداکثر ${fa(AI_MAX_SELECTIONS)} مورد`); return s }
      const next = [...s, t.slice(0, 2000)]
      toast.success(`به فهرستِ اعتبارسنجی افزوده شد (${fa(next.length)})`)
      return next
    })
    return true
  }
  const removeAiSelection = (i: number) => setAiSelections((s) => s.filter((_, idx) => idx !== i))

  const openAi = () => {
    // If the user has an active selection when opening, fold it in too (so a quick
    // select→open still works without touching the toolbar).
    const live = ((typeof window !== 'undefined' ? window.getSelection()?.toString() : '') || '').replace(/\s+/g, ' ').trim()
    let sels = aiSelections
    if (live && !aiSelections.includes(live) && aiSelections.length < AI_MAX_SELECTIONS) {
      sels = [...aiSelections, live.slice(0, 2000)]
      setAiSelections(sels)
    }
    // Any collected selection → «اعتبارسنجی» is a relevant tool; turn it on.
    setAiSelTools(sels.length ? Array.from(new Set([...DEFAULT_TOOLS, 'validation'])) : DEFAULT_TOOLS)
    setAiChanges([]); setAiChecked({}); setAiRan(false); setAiError(''); setAiModelUsed('')
    setAiOpen(true)
    if (!aiModelsLoaded) {
      letterAiApi.models().then((r) => { setAiModels(r.models || []); setAiTools(r.tools || []); setAiModelsLoaded(true) })
        .catch(() => { setAiTools([]); setAiModelsLoaded(true) })
    }
  }
  const toggleTool = (id: string) => setAiSelTools((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id])

  const ATT_TOOL = 'attachments_extract'
  const runAi = async () => {
    if (!aiSelTools.length) { toast.error('حداقل یک ابزار را انتخاب کن'); return }
    setAiLoading(true); setAiError(''); setAiRan(false); setExtracting2('')
    try {
      const letterTools = aiSelTools.filter((t) => t !== ATT_TOOL)
      let all: LetterAiChange[] = []
      let modelUsed = ''
      // Send the user-picked tables (full HTML) when the tables tool is on —
      // the model gets full control over exactly these, nothing else.
      const pickedTables = letterTools.includes('tables') ? getBodyTables().filter((t) => tblSelected(t.uid)) : []
      sentTableUidsRef.current = pickedTables.map((t) => ({ uid: t.uid, attId: t.attId }))
      // full_check: gather the attachments' CONTENT so the model can check the
      // letter AND its attachments against the DB and against each other.
      // In-flow attachment tables come from the letter itself; attached FILES
      // are transcribed one bounded request each (never persisted).
      const fcNotes: LetterAiChange[] = []   // read-failures surfaced AFTER analyze (never lost)
      const fcAttTexts: { name: string; text: string }[] = []
      // attachment content is needed by full_check (consistency/conformity) AND
      // by db_extract (KB harvest from the attachments' general material)
      const wantsAttContent = letterTools.includes('full_check') || letterTools.includes('db_extract')
      const fcAttTables = wantsAttContent ? attTables.map((t) => t.html) : []
      if (wantsAttContent && letterAtts.length) {
        const fcAtts = letterAtts.filter((a) => attSelected(a))
        for (let i = 0; i < fcAtts.length; i++) {
          const att = fcAtts[i]
          setExtracting2(`خواندنِ پیوست برای بررسیِ کامل (${fa(i + 1)} از ${fa(fcAtts.length)}): ${att.original_name}…`)
          try {
            const tx = await letterAiApi.attachmentText(att.id, { model_id: aiModelId === '' ? undefined : Number(aiModelId) })
            if (tx.ok && (tx.text || '').trim()) fcAttTexts.push({ name: att.original_name, text: tx.text || '' })
            else if (!tx.ok) fcNotes.push({ id: `fcerr-${att.id}`, op: 'note', category: 'consistency', field: '',
              title: `پیوست «${att.original_name}» برای بررسیِ کامل خوانده نشد`, detail: aiErrorText(tx.error),
              severity: 'medium', applicable: false })
          } catch (e) {
            fcNotes.push({ id: `fcerr-${att.id}`, op: 'note', category: 'consistency', field: '',
              title: `پیوست «${att.original_name}» برای بررسیِ کامل خوانده نشد`, detail: parseApiError(e),
              severity: 'medium', applicable: false })
          }
        }
        setExtracting2('')
      }
      if (letterTools.length) {
        const r = await letterAiApi.analyze({
          account_no: general ? undefined : (acct.trim() || undefined),
          fields: f, tools: letterTools,
          instruction: aiInstruction.trim() || undefined,
          selections: aiSelections.length ? aiSelections : undefined,
          tables: pickedTables.length ? pickedTables.map((t) => t.html) : undefined,
          attachment_tables: fcAttTables.length ? fcAttTables : undefined,
          attachments_text: fcAttTexts.length ? fcAttTexts : undefined,
          model_id: aiModelId === '' ? undefined : Number(aiModelId),
        })
        setAiFactsUsed(!!r.facts_used)
        if (!r.ok) { setAiError(aiErrorText(r.error)); setAiRan(true); setAiChanges([]); return }
        all = (r.changes || []).concat(fcNotes)
        modelUsed = r.model || ''
      }
      // Deep extraction from the letter's attachments — only the ones the user
      // ticked, one attachment per request (bounded), mirroring the Import
      // pipeline's guards server-side.
      const attsToRun = aiSelTools.includes(ATT_TOOL) ? letterAtts.filter((a) => attSelected(a)) : []
      if (aiSelTools.includes(ATT_TOOL) && letterAtts.length && !attsToRun.length) {
        toast.error('هیچ پیوستی برای استخراج انتخاب نشده — در فهرستِ زیرِ ابزار، پیوست(ها) را تیک بزن')
      }
      if (attsToRun.length) {
        for (let i = 0; i < attsToRun.length; i++) {
          const att = attsToRun[i]
          setExtracting2(`استخراج از پیوست ${fa(i + 1)} از ${fa(attsToRun.length)}: ${att.original_name}…`)
          try {
            const rx = await letterAiApi.extractAttachment(att.id, {
              account_no: general ? undefined : (acct.trim() || undefined),
              customer_name: plain(f.recipientName) || undefined,
              subject: plain(f.subject) || undefined,
              body_excerpt: plain(f.body).slice(0, 1500) || undefined,
              model_id: aiModelId === '' ? undefined : Number(aiModelId),
              // an ai_generated attachment only reaches this loop when the user
              // explicitly ticked it — tell the server the override is deliberate
              allow_ai_generated: att.ai_generated ? true : undefined,
            })
            if (rx.ok) {
              all = all.concat(rx.changes || [])
              if (rx.model) modelUsed = modelUsed || rx.model
              if ((rx.chunk_errors || []).length) toast.error(`${att.original_name}: بخشی از قطعات خطا داشت`)
            } else {
              all.push({ id: `err-${att.id}`, op: 'note', category: 'db_extract', field: '',
                title: `استخراج از «${att.original_name}» ناموفق`, detail: aiErrorText(rx.error),
                severity: 'high', applicable: false })
            }
          } catch (e) {
            all.push({ id: `err-${att.id}`, op: 'note', category: 'db_extract', field: '',
              title: `استخراج از «${att.original_name}» ناموفق`, detail: parseApiError(e),
              severity: 'high', applicable: false })
          }
        }
        setExtracting2('')
      }
      setAiRan(true)
      setAiModelUsed(modelUsed)
      setAiChanges(all)
      // pre-tick every applicable change; notes are advisory (never applied)
      const checked: Record<string, boolean> = {}
      for (const c of all) checked[c.id] = !!c.applicable
      setAiChecked(checked)
      if (!all.length) toast.success('موردی برای اصلاح یافت نشد — نامه تمیز است ✓')
    } catch (e) { setAiError(parseApiError(e)); setAiRan(true) }
    finally { setAiLoading(false); setExtracting2('') }
  }
  const aiErrorText = (err?: string) => {
    if (err === 'ai_generated_attachment') return 'این پیوست را خودِ هوش مصنوعی از داده‌های پایگاه‌داده ساخته — استخراجِ دوباره‌اش به دیتابیس بی‌معناست و سرور آن را رد کرد.'
    if (err === 'no_model') return 'هیچ مدلِ هوش مصنوعیِ فعالی پیکربندی نشده — از «تنظیمات ← مدل‌های هوش مصنوعی» یک مدل را فعال کن.'
    if (err === 'no_base_url') return 'آدرسِ سرویس‌دهندهٔ مدل تنظیم نشده است.'
    if (err && /timed out/i.test(err)) return 'پاسخِ مدل به‌موقع نرسید؛ دوباره تلاش کن یا مدلِ سریع‌تری انتخاب کن.'
    return err ? `خطای مدل: ${err}` : 'اجرای مدل ناموفق بود.'
  }

  const applyAiChanges = async () => {
    const nf: any = { ...f }
    let applied = 0, notLocated = 0
    const appliedIds: string[] = []
    // db_write/link items go to the DB via the server (not onto the letter).
    const dbItems: { id: string; account_no: string; customer_name: string; key: string; value: string }[] = []
    const linkItems: { id: string; account_no: string; related_account: string; kind: string; reason: string }[] = []
    const kbItems: { id: string; topic: string; content: string; category: string; source_note: string; account_no: string }[] = []
    // table_insert results: collected here and committed once after the loop.
    const newAttTables: AttTable[] = []
    for (const ch of aiChanges) {
      if (!aiChecked[ch.id] || !ch.applicable) continue
      if (ch.op === 'db_write') {
        if (ch.account_no && ch.key) dbItems.push({ id: ch.id, account_no: ch.account_no, customer_name: ch.customer_name || '', key: ch.key, value: String(ch.value ?? ch.after ?? '') })
        continue
      }
      if (ch.op === 'link') {
        if (ch.account_no && ch.related_account) linkItems.push({ id: ch.id, account_no: ch.account_no, related_account: ch.related_account, kind: ch.kind || 'other', reason: ch.reason || ch.detail || '' })
        continue
      }
      if (ch.op === 'kb_write') {
        if (ch.topic && ch.content) kbItems.push({ id: ch.id, topic: ch.topic, content: ch.content, category: ch.kb_category || '', source_note: ch.source_note || '', account_no: general ? '' : (acct.trim() || '') })
        continue
      }
      if (ch.op === 'table_insert') {
        // A brand-new AI-authored table (whitelist-sanitized server-side):
        // placement 'attachment' → its own پیوست page after the letter (the
        // page auto-handles landscape/font-fit); 'body' → appended to the text
        // flow with the same markup the manual جدول button produces.
        const wrap = document.createElement('div')
        wrap.innerHTML = ch.html || ''
        normalizeTables(wrap)   // stable data-r ids for toolbar/pagination
        const newTbl = wrap.querySelector('table')
        if (!newTbl) { notLocated++; continue }
        if (ch.placement === 'attachment') {
          newAttTables.push({ id: uid(), title: ch.table_title || '', html: newTbl.outerHTML })
          if (nf.attachment !== 'دارد') nf.attachment = 'دارد'
        } else {
          const title = ch.table_title ? `<div style="font-weight:700;text-align:center;text-indent:0">${escapeHtml(ch.table_title)}</div>` : ''
          // the leading blank line keeps the new table from sitting DIRECTLY next
          // to an existing one — mergeAdjacentTables would fuse same-header
          // neighbors (the pagination-split repair) and swallow the new table.
          nf.body = `${normalizeBodyHtml(nf.body || '')}<div><br></div>${title}${newTbl.outerHTML}<div><br></div>`
        }
        applied++; appliedIds.push(ch.id)
        continue
      }
      if (ch.op === 'table_replace') {
        // Replace the EXACT table the user selected (uid-mapped from the list
        // sent with analyze). HTML was whitelist-sanitized server-side.
        const sent = ch.table_index != null ? sentTableUidsRef.current[ch.table_index - 1] : undefined
        if (!sent || !ch.html) { notLocated++; continue }
        const wrap = document.createElement('div')
        wrap.innerHTML = ch.html
        const newTbl = wrap.querySelector('table')
        if (!newTbl) { notLocated++; continue }
        normalizeTables(wrap)   // stable data-r ids for the new rows (toolbar/pagination)
        if (sent.attId) {
          // the redesigned table replaces its ATTACHMENT page's table
          if (!attTables.some((t) => t.id === sent.attId)) { notLocated++; continue }
          updateAttTable(sent.attId, { html: newTbl.outerHTML })
          applied++; appliedIds.push(ch.id)
          continue
        }
        const d = document.createElement('div')
        d.innerHTML = normalizeBodyHtml(nf.body || '')
        mergeAdjacentTables(d); normalizeTables(d)
        const hdr = d.querySelector(`tr[data-r="${cssEsc(sent.uid)}"]`)
        const tbl = hdr?.closest('table')
        if (!tbl) { notLocated++; continue }
        tbl.replaceWith(newTbl)
        nf.body = d.innerHTML
        applied++; appliedIds.push(ch.id)
        continue
      }
      if (!(ch.field in nf)) continue
      if (ch.op === 'set_field') {
        const val = String(ch.after ?? '')
        nf[ch.field] = RICH_FIELDS.has(ch.field) ? escapeHtml(val) : val
        applied++; appliedIds.push(ch.id)
      } else if (ch.op === 'text_replace' && ch.find != null) {
        const [next, cnt] = applyTextReplaceHtml(String(nf[ch.field] ?? ''), ch.find, String(ch.replace ?? ''), (ch.occurrence as any) || 'first')
        if (cnt > 0) { nf[ch.field] = next; applied++; appliedIds.push(ch.id) }
        else notLocated++
      }
    }
    if (newAttTables.length) setAttTables((list) => [...list, ...newAttTables])
    if (applied) { setF(nf); toast.success(`${fa(applied)} مورد روی نامه اعمال شد — بازبینی و «ذخیره» کن`) }
    if (notLocated) toast.error(`${fa(notLocated)} مورد در متنِ فعلی پیدا نشد و رد شد`)

    // Persist the approved extracted facts + profile↔profile links + KB items.
    if (dbItems.length || linkItems.length || kbItems.length) {
      try {
        const r = await letterAiApi.applyDb({
          items: dbItems.map(({ id, ...rest }) => rest),
          links: linkItems.map(({ id, ...rest }) => rest),
          kb_items: kbItems.map(({ id, ...rest }) => rest),
          source_ref: letterId || '',
        })
        const c = r.counts || { added: 0, updated: 0, skipped: 0, profiles_created: 0 }
        const parts: string[] = []
        if (c.added) parts.push(`${fa(c.added)} ثبتِ جدید`)
        if (c.updated) parts.push(`${fa(c.updated)} به‌روزرسانی`)
        if (c.profiles_created) parts.push(`${fa(c.profiles_created)} پروفایلِ نو`)
        if (r.links_created) parts.push(`${fa(r.links_created)} لینکِ پروفایلی`)
        if (r.kb_added) parts.push(`${fa(r.kb_added)} مطلب در پایگاه دانش`)
        if (c.skipped) parts.push(`${fa(c.skipped)} تکراری/کهنه رد شد`)
        toast.success('در پایگاه‌داده: ' + (parts.join(' · ') || 'بدون تغییر') + ' — در لاگ‌ها ثبت شد')
        appliedIds.push(...dbItems.map((d) => d.id), ...linkItems.map((d) => d.id), ...kbItems.map((d) => d.id))
      } catch (e) { toast.error('ثبت در پایگاه‌داده ناموفق: ' + parseApiError(e)) }
    }

    if (!applied && !notLocated && !dbItems.length && !linkItems.length && !kbItems.length) { toast('موردی برای اعمال تیک نخورده است'); return }
    // drop applied rows; keep the rest so the user can iterate
    setAiChanges((cs) => cs.filter((c) => !appliedIds.includes(c.id)))
  }
  const aiApplicableCount = aiChanges.filter((c) => c.applicable && aiChecked[c.id]).length

  const loadLetter = async (id: string) => {
    try {
      const o = await lettersApi.get(id)
      if (o.values) {
        const v: any = { ...o.values }
        // attachment tables live alongside the fields inside values_json but are
        // kept OUT of `f` (they're a list, not a letter field — and analyze sends
        // `fields: f` verbatim).
        setAttTables(Array.isArray(v.attTables) ? v.attTables.filter((t: any) => t && t.id && t.html) : [])
        delete v.attTables
        setFloats(Array.isArray(v.floats) ? v.floats.filter((t: any) => t && t.id && t.html) : [])
        delete v.floats
        // ALWAYS reflow the loaded body into flowing, justified paragraphs (idempotent
        // for already-well-formed text: a paragraph that ends in a terminator stays as
        // one paragraph; only hard-wrapped visual lines get merged). No manual step.
        if (v.body) v.body = reflowBody(normalizeBodyHtml(v.body))
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

  const newLetter = () => { setLetterId(null); setTitle(''); setAttTables([]); setFloats([]); setFloatSel(null); setF((s) => ({ ...s, serial: '', year: String(new Date().getFullYear()), date: todayYMD(), subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '', recipientTitle: 'رئیس محترم' })) }
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
        values: ((attTables.length || floats.length) ? { ...f, ...(attTables.length ? { attTables } : {}), ...(floats.length ? { floats } : {}) } : f) as any, layout: L, labels,
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
  // adjust line spacing of the paragraph(s) touched by the selection (± step)
  const lineSpaceSel = (delta: number) => {
    const s = window.getSelection(); if (!s || !s.rangeCount) return
    const range = s.getRangeAt(0)
    const a = range.commonAncestorContainer
    const host = ((a.nodeType === 3 ? a.parentElement : (a as HTMLElement))?.closest('.bcell')) as HTMLElement | null
    if (!host) return
    let blocks = (Array.from(host.querySelectorAll('div,p,li')) as HTMLElement[]).filter((b) => range.intersectsNode(b))
    if (!blocks.length) { const el = ((a.nodeType === 3 ? a.parentElement : (a as HTMLElement))?.closest('div,p,li')) as HTMLElement | null; if (el && host.contains(el)) blocks = [el] }
    if (!blocks.length) blocks = [host]
    blocks.forEach((b) => { const cur = parseFloat(b.style.lineHeight) || (L.body.lh || 1.7); b.style.lineHeight = String(Math.max(1, Math.round((cur + delta) * 10) / 10)) })
    host.dispatchEvent(new Event('input', { bubbles: true }))
  }

  // ---- Word-like TABLE editing. Structural edits run on the FULL body (the single
  //      source of truth), located by the caret cell's column and the row's stable id,
  //      then the body re-paginates automatically. ----
  const tableOp = (op: 'rowAbove' | 'rowBelow' | 'delRow' | 'colLeft' | 'colRight' | 'delCol' | 'mergeCells' | 'valTop' | 'valMiddle' | 'valBottom' | 'alignRight' | 'alignCenter' | 'alignLeft' | 'delTable') => {
    const s = window.getSelection(); if (!s || !s.rangeCount) return
    const cellOf = (node: Node | null) => { const e = node ? (node.nodeType === 3 ? node.parentElement : (node as HTMLElement)) : null; return (e?.closest('td,th') as HTMLTableCellElement | null) }
    const td = cellOf(s.anchorNode) || cellOf(s.focusNode)
    const trLive = td?.closest('tr') as HTMLTableRowElement | null
    const liveTable = trLive?.closest('table') as HTMLTableElement | null
    if (!td || !trLive || !liveTable) return
    const colIndex = td.cellIndex
    const rowUid = trLive.getAttribute('data-r') || ''
    // every cell the selection touches → (row-id, column) keys (for multi-row/col & merge)
    const range = s.getRangeAt(0)
    const selLive = (Array.from(liveTable.querySelectorAll('td,th')) as HTMLTableCellElement[]).filter((c) => range.intersectsNode(c))
    if (!selLive.includes(td)) selLive.push(td)
    const selKeys = selLive.map((c) => ({ uid: c.closest('tr')?.getAttribute('data-r') || '', ci: c.cellIndex }))

    // Structural edits run on whichever document owns the row: the letter BODY
    // (single source of truth) or one of the ATTACHMENT tables. Same ops either way.
    const runOn = (html: string): string | null => {
    const scratch = document.createElement('div')
    scratch.innerHTML = normalizeBodyHtml(html)
    mergeAdjacentTables(scratch)
    normalizeTables(scratch)
    const tr = rowUid ? (scratch.querySelector(`tr[data-r="${cssEsc(rowUid)}"]`) as HTMLTableRowElement | null) : null
    const table = tr?.closest('table') as HTMLTableElement | null
    if (!table || !tr) return null
    const rows = Array.from(table.rows)
    const rowByUid = (u: string) => scratch.querySelector(`tr[data-r="${cssEsc(u)}"]`) as HTMLTableRowElement | null
    const clean = (h: string) => h.replace(/<[^>]+>/g, '').replace(/ /g, ' ').trim()
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
    else if (op === 'delRow') {
      const uids = Array.from(new Set(selKeys.map((k) => k.uid).filter(Boolean)))
      const trs = (uids.length ? uids : [rowUid]).map(rowByUid).filter(Boolean) as HTMLTableRowElement[]
      if (trs.length >= table.rows.length) table.remove()
      else trs.forEach((x) => x.remove())
    } else if (op === 'colLeft' || op === 'colRight') {
      const at = op === 'colLeft' ? colIndex : colIndex + 1
      rows.forEach((r) => { const proto = r.cells[Math.min(colIndex, r.cells.length - 1)]; const c = mkCell(proto, (proto?.tagName === 'TH' ? 'th' : 'td')); if (at >= r.cells.length) r.appendChild(c); else r.insertBefore(c, r.cells[at]) })
    } else if (op === 'delCol') {
      const cols = Array.from(new Set(selKeys.map((k) => k.ci))).sort((a, b) => b - a)  // high→low so indices stay valid
      cols.forEach((ci) => rows.forEach((r) => { if (r.cells[ci] && r.cells.length > 1) r.deleteCell(ci) }))
      if (!table.rows[0] || table.rows[0].cells.length === 0) table.remove()
    } else if (op === 'mergeCells') {
      const mapped = selKeys.map((k) => { const srow = rowByUid(k.uid); const cell = srow?.cells[k.ci]; const rIdx = srow ? rows.indexOf(srow) : -1; return cell && rIdx >= 0 ? { cell, rIdx, ci: k.ci } : null }).filter(Boolean) as { cell: HTMLTableCellElement; rIdx: number; ci: number }[]
      if (mapped.length >= 2) {
        const minR = Math.min(...mapped.map((m) => m.rIdx)), maxR = Math.max(...mapped.map((m) => m.rIdx))
        const minC = Math.min(...mapped.map((m) => m.ci)), maxC = Math.max(...mapped.map((m) => m.ci))
        const target = table.rows[minR]?.cells[minC]
        if (target) {
          const removeList: HTMLTableCellElement[] = []
          for (let r = minR; r <= maxR; r++) for (let c = minC; c <= maxC; c++) { const cell = table.rows[r]?.cells[c]; if (cell && cell !== target) removeList.push(cell) }
          const parts = [target, ...removeList].map((c) => c.innerHTML).filter((h) => clean(h))
          target.innerHTML = parts.join(' ') || '<br>'
          if (maxC > minC) target.colSpan = maxC - minC + 1; else target.removeAttribute('colspan')
          if (maxR > minR) target.rowSpan = maxR - minR + 1; else target.removeAttribute('rowspan')
          removeList.forEach((c) => c.remove())
        }
      }
    } else if (op === 'valTop' || op === 'valMiddle' || op === 'valBottom') {
      const va = op === 'valTop' ? 'top' : op === 'valMiddle' ? 'middle' : 'bottom'
      const keys = selKeys.length ? selKeys : [{ uid: rowUid, ci: colIndex }]
      keys.forEach((k) => { const srow = rowByUid(k.uid); const cell = srow?.cells[k.ci]; if (cell) cell.style.verticalAlign = va })
    } else if (op === 'alignRight' || op === 'alignCenter' || op === 'alignLeft') {
      // horizontal alignment of the SELECTED cells' text (deterministic — on the
      // cell style, not execCommand, so it survives re-render and printing)
      const ta = op === 'alignRight' ? 'right' : op === 'alignCenter' ? 'center' : 'left'
      const keys = selKeys.length ? selKeys : [{ uid: rowUid, ci: colIndex }]
      keys.forEach((k) => { const srow = rowByUid(k.uid); const cell = srow?.cells[k.ci]; if (cell) cell.style.textAlign = ta })
    } else if (op === 'delTable') table.remove()
    return scratch.innerHTML
    }
    const nextBody = runOn(f.body)
    if (nextBody != null) setF((prev) => ({ ...prev, body: nextBody }))
    else {
      for (const at of attTables) {
        const nextHtml = runOn(at.html)
        if (nextHtml == null) continue
        // an attachment table whose <table> was deleted disappears entirely (its page too)
        if (nextHtml.indexOf('<table') === -1) removeAttTable(at.id)
        else updateAttTable(at.id, { html: nextHtml })
        break
      }
    }
    setTbl(null)
  }

  // ---- Drag a table gridline to resize columns. Live-updates the cell widths in the DOM
  //      while dragging (all fragments of a split table), then persists the % widths onto
  //      every cell of the two affected columns in the full body. ----
  const liveTablesFor = (hdrUid: string) => (Array.from(document.querySelectorAll('#ltr-edit .bcell table')) as HTMLTableElement[]).filter((t) => t.rows[0]?.getAttribute('data-r') === hdrUid)
  const recomputeColRz = (hdrUid: string) => {
    const t = liveTablesFor(hdrUid)[0]
    if (!t || !t.rows[0] || !t.rows[0].cells.length) { setColRz(null); return }
    const tr = t.getBoundingClientRect()
    // i = -1 → OUTER left edge, i = -2 → OUTER right edge: dragging either one
    // resizes the WHOLE table (the opposite edge stays anchored). Default is
    // fit-to-page; this lets the table shrink when its content is small.
    const bounds: { x: number; i: number }[] = [{ x: tr.left, i: -1 }, { x: tr.right, i: -2 }]
    for (let i = 0; i < t.rows[0].cells.length - 1; i++) bounds.push({ x: t.rows[0].cells[i].getBoundingClientRect().left, i })
    // horizontal boundaries: each row's BOTTOM edge drags that row's height; the
    // table's TOP edge drags the first row (delta inverted)
    const rowBounds: { y: number; uid: string; topEdge?: boolean }[] = []
    const rows0 = Array.from(t.rows) as HTMLTableRowElement[]
    if (rows0.length) rowBounds.push({ y: rows0[0].getBoundingClientRect().top, uid: rows0[0].getAttribute('data-r') || '', topEdge: true })
    rows0.forEach((r) => rowBounds.push({ y: r.getBoundingClientRect().bottom, uid: r.getAttribute('data-r') || '' }))
    setColRz({ top: tr.top, height: tr.height, left: tr.left, width: tr.width, hdrUid, bounds, rowBounds })
  }
  // ---- Drag a whole TABLE to a new position in the letter's text flow. The move
  //      happens between top-level blocks (paragraph boundaries) — nothing else on
  //      the page (fields/layout) is touched. Attachment tables own their page and
  //      are not draggable. Persisting goes through the same path as manual edits
  //      (the page cells' HTML joined back into the body). ----
  const startTableDrag = (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation()
    const sel = window.getSelection()
    const n = sel?.anchorNode || sel?.focusNode
    const el = n ? (n.nodeType === 3 ? n.parentElement : (n as HTMLElement)) : null
    const liveTable = el?.closest('table') as HTMLTableElement | null
    const hdrUid = liveTable?.rows[0]?.getAttribute('data-r') || ''
    if (!liveTable || !hdrUid) return
    if (liveTable.closest('.attsheet')) {
      // An attachment table moves WITHIN ITS OWN PAGE: dragging the grip slides it
      // up/down (offY), clamped so it never leaves the page or covers the footer.
      // Horizontal movement = the strip above the table (like body tables).
      const sheet = liveTable.closest('.lsheet') as HTMLElement
      const cellEl = liveTable.closest('.bcell') as HTMLElement | null
      const att = attTables.find((t) => t.html.indexOf(`data-r="${hdrUid}"`) !== -1)
      if (!sheet || !cellEl || !att) return
      const baseTop = ATT_TOP + ATT_TITLE_H
      const tblH = liveTable.getBoundingClientRect().height
      const maxOff = Math.max(0, sheet.offsetHeight - ATT_BOTTOM - tblH - baseTop)
      const off0 = Math.min(att.offY || 0, maxOff)
      const startY = e.clientY
      let off = off0
      const mvA = (ev: PointerEvent) => {
        off = Math.round(Math.min(maxOff, Math.max(0, off0 + (ev.clientY - startY))))
        cellEl.style.top = `${baseTop + off}px`
      }
      const upA = () => {
        document.removeEventListener('pointermove', mvA); document.removeEventListener('pointerup', upA)
        updateAttTable(att.id, { offY: off })
        setTbl(null); setColRz(null)
      }
      document.addEventListener('pointermove', mvA); document.addEventListener('pointerup', upA)
      return
    }
    const frags = liveTablesFor(hdrUid).filter((t) => !t.closest('.attsheet'))
    if (!frags.length) return
    const cells = letterCells()
    let target: { cell: HTMLElement; ref: Element | null } | null = null
    const mv = (ev: PointerEvent) => {
      target = null
      for (const cell of cells) {
        const r = cell.getBoundingClientRect()
        if (ev.clientX < r.left - 40 || ev.clientX > r.right + 40 || ev.clientY < r.top || ev.clientY > r.bottom) continue
        // candidate boundaries = the cell's top-level blocks, minus the dragged table itself
        const kids = (Array.from(cell.children) as HTMLElement[]).filter(
          (k) => !(k.tagName === 'TABLE' && (k as HTMLTableElement).rows[0]?.getAttribute('data-r') === hdrUid))
        let ref: Element | null = null
        let y = kids.length ? kids[kids.length - 1].getBoundingClientRect().bottom : r.top + 4
        for (const k of kids) {
          const kr = k.getBoundingClientRect()
          if (ev.clientY < kr.top + kr.height / 2) { ref = k; y = kr.top; break }
        }
        target = { cell, ref }
        setDropInd({ x: r.left, w: r.width, y })
        break
      }
      if (!target) setDropInd(null)
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      setDropInd(null)
      if (!target) return
      // re-merge the table's page fragments into ONE table (drop the header row
      // that pagination duplicates on continuation pages)
      const combined = frags[0]
      const tb = combined.querySelector('tbody') || combined
      for (let fi = 1; fi < frags.length; fi++) {
        Array.from(frags[fi].rows).forEach((row, ri) => {
          if (ri === 0 && row.getAttribute('data-r') === hdrUid) return
          tb.appendChild(row)
        })
        frags[fi].remove()
      }
      let ref = target.ref
      if (ref === combined) ref = combined.nextElementSibling
      target.cell.insertBefore(combined, ref)
      setF((prev) => ({ ...prev, body: cells.map((c) => c.innerHTML).join('') }))
      setTbl(null); setColRz(null)
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // Drag a row's bottom edge (or the table's top edge) to change that ROW's height.
  // The height lands on the <tr> style (acts as a min-height — content can still
  // grow past it), persisted by the row's stable data-r into body or attachment.
  const startRowResize = (e: React.PointerEvent, uid: string, topEdge?: boolean) => {
    e.preventDefault(); e.stopPropagation()
    if (!uid) return
    const live = document.querySelector(`#ltr-edit .bcell tr[data-r="${cssEsc(uid)}"]`) as HTMLTableRowElement | null
    if (!live) return
    const h0 = live.getBoundingClientRect().height
    const startY = e.clientY
    let hh = h0
    const mv = (ev: PointerEvent) => {
      const d = topEdge ? (startY - ev.clientY) : (ev.clientY - startY)
      hh = Math.max(14, Math.round(h0 + d))
      live.style.height = `${hh}px`
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      const applyH = (html: string): string | null => {
        const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(html)
        mergeAdjacentTables(scratch); normalizeTables(scratch)
        const tr2 = scratch.querySelector(`tr[data-r="${cssEsc(uid)}"]`) as HTMLTableRowElement | null
        if (!tr2) return null
        tr2.style.height = `${hh}px`
        return scratch.innerHTML
      }
      const nextBody = applyH(f.body)
      if (nextBody != null) setF((prev) => ({ ...prev, body: nextBody }))
      else for (const at of attTables) { const nh = applyH(at.html); if (nh != null) { updateAttTable(at.id, { html: nh }); break } }
      const hdr = live.closest('table')?.rows[0]?.getAttribute('data-r') || ''
      requestAnimationFrame(() => recomputeColRz(hdr))
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // Persist a table's whole-geometry (--tw width + --toff offset-from-right) onto
  // the owning document (body OR attachment table); ≥99.5% width = reset to the
  // default fit-to-page.
  const persistTableGeom = (hdrUid: string, pct: number, toff: number) => {
    const applyW = (html: string): string | null => {
      const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(html)
      mergeAdjacentTables(scratch); normalizeTables(scratch)
      const tr2 = scratch.querySelector(`tr[data-r="${cssEsc(hdrUid)}"]`) as HTMLTableRowElement | null
      const table = tr2?.closest('table') as HTMLTableElement | null
      if (!table) return null
      if (pct >= 99.5) {
        table.classList.remove('tblw'); table.style.removeProperty('--tw'); table.style.removeProperty('--toff')
        if (!table.className) table.removeAttribute('class')
        if (!table.getAttribute('style')) table.removeAttribute('style')
      } else {
        table.classList.add('tblw'); table.style.setProperty('--tw', `${pct}%`)
        if (toff > 0.2) table.style.setProperty('--toff', `${toff}%`); else table.style.removeProperty('--toff')
      }
      return scratch.innerHTML
    }
    const nextBody = applyW(f.body)
    if (nextBody != null) setF((prev) => ({ ...prev, body: nextBody }))
    else for (const at of attTables) { const nh = applyW(at.html); if (nh != null) { updateAttTable(at.id, { html: nh }); break } }
    requestAnimationFrame(() => recomputeColRz(hdrUid))
  }
  const readTableGeom = (el: HTMLElement) => ({
    tw: parseFloat((el.style.getPropertyValue('--tw') || '100').replace('%', '')) || 100,
    toff: parseFloat((el.style.getPropertyValue('--toff') || '0').replace('%', '')) || 0,
  })
  // Drag the strip ABOVE the table to move a shrunk table left/right (adjusts the
  // offset-from-right; a full-width table has no room and shows a hint instead).
  const startTableHMove = (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation()
    if (!colRz) return
    const hdrUid = colRz.hdrUid
    const tables = liveTablesFor(hdrUid); if (!tables.length) return
    const t0 = tables[0]
    const host = t0.closest('.bcell') as HTMLElement | null; if (!host) return
    const hostR = host.getBoundingClientRect(); const cw = host.clientWidth || 1
    const rect0 = t0.getBoundingClientRect()
    const tw = +(rect0.width / cw * 100).toFixed(1)
    if (tw >= 99.5) { toast('جدول تمام‌عرض است — اول از لبهٔ بیرونی کوچکش کن تا جای حرکتِ افقی باز شود'); return }
    const toff0 = (hostR.right - rect0.right) / cw * 100
    const startX = e.clientX
    const mv = (ev: PointerEvent) => {
      const toff = +Math.min(100 - tw, Math.max(0, toff0 + (startX - ev.clientX) / cw * 100)).toFixed(1)
      tables.forEach((t) => {
        t.classList.add('tblw'); t.style.setProperty('--tw', `${tw}%`)
        if (toff > 0.2) t.style.setProperty('--toff', `${toff}%`); else t.style.removeProperty('--toff')
      })
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      const live = liveTablesFor(hdrUid)[0]; if (!live) return
      const g = readTableGeom(live)
      persistTableGeom(hdrUid, g.tw, g.toff)
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const startColResize = (e: React.PointerEvent, i: number) => {
    e.preventDefault(); e.stopPropagation()
    if (!colRz) return
    const hdrUid = colRz.hdrUid
    const tables = liveTablesFor(hdrUid); if (!tables.length) return
    const t0 = tables[0]
    if (i === -1 || i === -2) {
      // WHOLE-TABLE resize from EITHER outer edge: the opposite edge stays anchored.
      // Width is a % of the text column (.tblw class + --tw/--toff vars — also
      // applied in .measure/.psheet so pagination and print see the same geometry).
      const host = t0.closest('.bcell') as HTMLElement | null
      if (!host) return
      const hostR = host.getBoundingClientRect()
      const cw = host.clientWidth || 1
      const rect0 = t0.getBoundingClientRect()
      const mvT = (ev: PointerEvent) => {
        let pct: number, toff: number
        if (i === -1) {
          // drag the LEFT edge — right edge anchored (keep current offset)
          toff = (hostR.right - rect0.right) / cw * 100
          const w = Math.min(hostR.right - hostR.left, Math.max(cw * 0.2, rect0.right - ev.clientX))
          pct = w / cw * 100
          if (pct + toff > 100) pct = 100 - toff
        } else {
          // drag the RIGHT edge — left edge anchored; offset follows the pointer
          const leftPct = (rect0.left - hostR.left) / cw * 100
          toff = Math.max(0, (hostR.right - ev.clientX) / cw * 100)
          pct = 100 - leftPct - toff
          if (pct < 20) { pct = 20; toff = Math.max(0, 100 - leftPct - pct) }
        }
        pct = +pct.toFixed(1); toff = +Math.max(0, toff).toFixed(1)
        tables.forEach((t) => {
          t.classList.add('tblw')
          t.style.setProperty('--tw', `${pct}%`)
          if (toff > 0.2) t.style.setProperty('--toff', `${toff}%`); else t.style.removeProperty('--toff')
        })
      }
      const upT = () => {
        document.removeEventListener('pointermove', mvT); document.removeEventListener('pointerup', upT)
        const live = liveTablesFor(hdrUid)[0]; if (!live) return
        const g = readTableGeom(live)
        persistTableGeom(hdrUid, g.tw, g.toff)
      }
      document.addEventListener('pointermove', mvT); document.addEventListener('pointerup', upT)
      return
    }
    if (t0.rows[0].cells.length < 2) return
    const startX = e.clientX
    const w0 = t0.rows[0].cells[i].getBoundingClientRect().width
    const w1 = t0.rows[0].cells[i + 1].getBoundingClientRect().width
    const tableW = t0.getBoundingClientRect().width || 1
    const mv = (ev: PointerEvent) => {
      const d = startX - ev.clientX                                  // RTL: drag left → col i widens
      const nw0 = Math.max(24, w0 + d), nw1 = Math.max(24, w1 - d)
      const p0 = `${(nw0 / tableW * 100).toFixed(2)}%`, p1 = `${(nw1 / tableW * 100).toFixed(2)}%`
      tables.forEach((t) => Array.from(t.rows).forEach((r) => { if (r.cells[i]) r.cells[i].style.width = p0; if (r.cells[i + 1]) r.cells[i + 1].style.width = p1 }))
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      // persist the resulting column widths onto the owning document (body OR an attachment table)
      const live = liveTablesFor(hdrUid)[0]; if (!live) return
      const widths = Array.from(live.rows[0].cells).map((c) => (c as HTMLElement).style.width)
      const applyWidths = (html: string): string | null => {
        const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(html)
        mergeAdjacentTables(scratch); normalizeTables(scratch)
        const tr = scratch.querySelector(`tr[data-r="${cssEsc(hdrUid)}"]`) as HTMLTableRowElement | null
        const table = tr?.closest('table') as HTMLTableElement | null
        if (!table) return null
        Array.from(table.rows).forEach((r) => widths.forEach((w, ci) => { if (w && r.cells[ci]) (r.cells[ci] as HTMLElement).style.width = w }))
        return scratch.innerHTML
      }
      const nextBody = applyWidths(f.body)
      if (nextBody != null) setF((prev) => ({ ...prev, body: nextBody }))
      else for (const at of attTables) { const nh = applyWidths(at.html); if (nh != null) { updateAttTable(at.id, { html: nh }); break } }
      requestAnimationFrame(() => recomputeColRz(hdrUid))   // realign the handles to the re-rendered table
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // ---- Insert a fresh R×C table: a small dialog asks rows/columns, an optional
  //      TITLE, and whether the table is a letter ATTACHMENT (پیوست) — attachment
  //      tables become their own pages after the letter's last page. ----
  const [tblDlg, setTblDlg] = useState<{ rows: string; cols: string; title: string; asAtt: boolean } | null>(null)
  const insertRangeRef = useRef<Range | null>(null)   // caret at the moment the dialog opened
  const insertTable = () => {
    const s = window.getSelection()
    insertRangeRef.current = s && s.rangeCount ? s.getRangeAt(0).cloneRange() : null
    setTblDlg({ rows: '3', cols: '3', title: '', asAtt: false })
  }
  const freshTableHtml = (R: number, C: number) => {
    let html = '<table>'
    for (let r = 0; r < R; r++) { html += `<tr data-r="${uid()}">`; for (let c = 0; c < C; c++) html += '<td><br></td>'; html += '</tr>' }
    return html + '</table>'
  }
  const confirmInsertTable = () => {
    if (!tblDlg) return
    const R = parseInt(tblDlg.rows, 10) || 0, C = parseInt(tblDlg.cols, 10) || 0
    const ttl = tblDlg.title.trim()
    if (!R || !C || R > 200 || C > 30) { toast.error('تعدادِ ردیف/ستون معتبر نیست'); return }
    if (tblDlg.asAtt) {
      // ATTACHMENT table → its own page after the letter; also counted as a پیوست.
      setAttTables((list) => [...list, { id: uid(), title: ttl, html: freshTableHtml(R, C) }])
      if (f.attachment !== 'دارد') setF((s) => ({ ...s, attachment: 'دارد' }))
      toast.success('جدولِ پیوست ساخته شد — صفحهٔ آن بعد از صفحهٔ آخرِ نامه است')
    } else {
      const title = ttl ? `<div style="font-weight:700;text-align:center;text-indent:0">${escapeHtml(ttl)}</div>` : ''
      const html = `${title}${freshTableHtml(R, C)}<div><br></div>`
      const r = insertRangeRef.current
      const host = r ? ((r.commonAncestorContainer.nodeType === 3 ? r.commonAncestorContainer.parentElement : (r.commonAncestorContainer as HTMLElement)) as HTMLElement | null)?.closest?.('.bcell') as HTMLElement | null : null
      if (host && document.contains(host)) {
        const sel = window.getSelection()
        sel?.removeAllRanges(); try { sel?.addRange(r!) } catch { /* stale range → append below */ }
        host.focus()
        document.execCommand('insertHTML', false, html)
      } else setF((prev) => ({ ...prev, body: (prev.body || '') + html }))
    }
    setTblDlg(null); insertRangeRef.current = null
  }

  // ---- Insert an IMAGE at the caret (like tables). The file is downscaled on a
  //      canvas (data-URL kept letter-sized), wrapped in a uniform .imgcrop holder
  //      (one model for resize AND crop), and dropped exactly where the caret was.
  const imgFileRef = useRef<HTMLInputElement>(null)
  const insertImageClick = () => {
    const sl = window.getSelection()
    insertRangeRef.current = sl && sl.rangeCount ? sl.getRangeAt(0).cloneRange() : null
    imgFileRef.current?.click()
  }
  const downscaleImage = async (file: File): Promise<{ url: string; w: number; h: number }> => {
    const raw = await new Promise<string>((res, rej) => { const fr = new FileReader(); fr.onload = () => res(fr.result as string); fr.onerror = rej; fr.readAsDataURL(file) })
    const im = await new Promise<HTMLImageElement>((res, rej) => { const x = new window.Image(); x.onload = () => res(x); x.onerror = rej; x.src = raw })
    const MAX = 1400
    const k = Math.min(1, MAX / Math.max(im.naturalWidth, im.naturalHeight, 1))
    if (k >= 1 && file.size < 500_000) return { url: raw, w: im.naturalWidth, h: im.naturalHeight }
    const cv = document.createElement('canvas')
    cv.width = Math.max(1, Math.round(im.naturalWidth * k)); cv.height = Math.max(1, Math.round(im.naturalHeight * k))
    cv.getContext('2d')!.drawImage(im, 0, 0, cv.width, cv.height)
    const png = file.type === 'image/png'
    return { url: cv.toDataURL(png ? 'image/png' : 'image/jpeg', png ? undefined : 0.87), w: cv.width, h: cv.height }
  }
  const onImageFile = async (file?: File | null) => {
    if (!file) return
    try {
      const d = await downscaleImage(file)
      const dispW = Math.min(d.w, 380)
      const dispH = Math.max(1, Math.round(dispW * d.h / Math.max(1, d.w)))
      const html = `<div style="text-align:center;text-indent:0"><span class="imgcrop" data-im="${uid()}" style="width:${dispW}px;height:${dispH}px"><img src="${d.url}" style="width:${dispW}px;height:${dispH}px;margin:0px 0px"></span></div><div><br></div>`
      const r = insertRangeRef.current
      const host = r ? ((r.commonAncestorContainer.nodeType === 3 ? r.commonAncestorContainer.parentElement : (r.commonAncestorContainer as HTMLElement)) as HTMLElement | null)?.closest?.('.bcell') as HTMLElement | null : null
      if (host && document.contains(host)) {
        const sl = window.getSelection()
        sl?.removeAllRanges(); try { sl?.addRange(r!) } catch { /* stale → append */ }
        host.focus()
        document.execCommand('insertHTML', false, html)
      } else setF((prev) => ({ ...prev, body: (prev.body || '') + html }))
      toast.success('تصویر درج شد — رویش کلیک کن: اندازه/کراپ/جابه‌جایی/پشتِ متن')
    } catch { toast.error('خواندنِ تصویر ناموفق بود') }
    finally { insertRangeRef.current = null }
  }

  // ---- IMAGE tools: click an image → toolbar + 8 handles. Resize mode scales the
  //      window AND the image together; crop mode shrinks the window while margins
  //      keep the image content anchored (Word-like). Everything persists by the
  //      image's stable data-im, mirroring the tables' data-r pattern. ----
  const [imgSel, setImgSel] = useState<string | null>(null)
  const [imgCropMode, setImgCropMode] = useState(false)
  const [imgRz, setImgRz] = useState<{ uid: string; x: number; y: number; w: number; h: number } | null>(null)
  const liveImg = (id: string) => document.querySelector(`#ltr-edit .bcell .imgcrop[data-im="${cssEsc(id)}"]`) as HTMLElement | null
  const recomputeImgRz = () => {
    const el = imgSel ? liveImg(imgSel) : null
    if (!el) { setImgRz(null); return }
    const r = el.getBoundingClientRect()
    setImgRz({ uid: imgSel as string, x: r.left, y: r.top, w: r.width, h: r.height })
  }
  useEffect(() => { recomputeImgRz() /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [imgSel, f.body, attTables])
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const t = e.target as HTMLElement
      if (t.closest?.('.img-bar, .img-hd')) return                       // toolbar/handles keep the selection
      const wrap = t.closest?.('.imgcrop[data-im]') as HTMLElement | null
      if (wrap && wrap.closest('#ltr-edit .bcell')) { setImgSel(wrap.getAttribute('data-im')); setImgCropMode(false); return }
      setImgSel(null); setImgCropMode(false)
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])
  useEffect(() => {
    let raf = 0
    const onScroll = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(recomputeImgRz) }
    window.addEventListener('scroll', onScroll, true)
    return () => { window.removeEventListener('scroll', onScroll, true); cancelAnimationFrame(raf) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imgSel])
  // read/write the wrapper+img geometry (all px)
  const readImgGeom = (wrap: HTMLElement) => {
    const img = wrap.querySelector('img') as HTMLImageElement | null
    const px = (v: string) => parseFloat(v.replace('px', '')) || 0
    return {
      W: px(wrap.style.width) || wrap.getBoundingClientRect().width,
      H: px(wrap.style.height) || wrap.getBoundingClientRect().height,
      iw: img ? (px(img.style.width) || img.getBoundingClientRect().width) : 0,
      ih: img ? (px(img.style.height) || img.getBoundingClientRect().height) : 0,
      ml: img ? px(img.style.marginLeft) : 0,
      mt: img ? px(img.style.marginTop) : 0,
    }
  }
  const applyImgGeom = (wrap: HTMLElement, g: { W: number; H: number; iw: number; ih: number; ml: number; mt: number }) => {
    wrap.style.width = `${Math.round(g.W)}px`; wrap.style.height = `${Math.round(g.H)}px`
    const img = wrap.querySelector('img') as HTMLElement | null
    if (img) {
      img.style.width = `${Math.round(g.iw)}px`; img.style.height = `${Math.round(g.ih)}px`
      img.style.marginLeft = `${Math.round(g.ml)}px`; img.style.marginTop = `${Math.round(g.mt)}px`
    }
  }
  // persist a mutation on the image (located by data-im) into body or attachment
  const persistImg = (id: string, mutate: (wrap: HTMLElement, doc: HTMLElement) => void): boolean => {
    const run = (html: string): string | null => {
      const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(html)
      const wrap = scratch.querySelector(`.imgcrop[data-im="${cssEsc(id)}"]`) as HTMLElement | null
      if (!wrap) return null
      mutate(wrap, scratch)
      return scratch.innerHTML
    }
    const nextBody = run(f.body)
    if (nextBody != null) { setF((prev) => ({ ...prev, body: nextBody })); return true }
    for (const at of attTables) { const nh = run(at.html); if (nh != null) { updateAttTable(at.id, { html: nh }); return true } }
    return false
  }
  // one of the 8 handles: dir ∈ n,s,e,w,ne,nw,se,sw
  const startImgHandle = (e: React.PointerEvent, dir: string) => {
    e.preventDefault(); e.stopPropagation()
    const id = imgSel; if (!id) return
    const el = liveImg(id); if (!el) return
    const g0 = readImgGeom(el)
    const sx = e.clientX, sy = e.clientY
    const crop = imgCropMode
    let cur = { ...g0 }
    const mv = (ev: PointerEvent) => {
      const dx = ev.clientX - sx, dy = ev.clientY - sy
      const g = { ...g0 }
      if (!crop) {
        // RESIZE: sides stretch that dimension; corners scale proportionally
        let W = g0.W, H = g0.H
        if (dir.includes('e')) W = g0.W + dx
        if (dir.includes('w')) W = g0.W - dx
        if (dir.includes('n')) H = g0.H - dy
        if (dir.includes('s')) H = g0.H + dy
        if (dir.length === 2) { const k = Math.max(0.05, (dir.includes('e') || dir.includes('w')) ? W / g0.W : H / g0.H); W = g0.W * k; H = g0.H * k }
        W = Math.max(24, W); H = Math.max(24, H)
        const kx = W / g0.W, ky = H / g0.H
        g.W = W; g.H = H; g.iw = g0.iw * kx; g.ih = g0.ih * ky; g.ml = g0.ml * kx; g.mt = g0.mt * ky
      } else {
        // CROP: the window shrinks/grows from that side; margins keep content anchored
        let { W, H, ml, mt } = g0
        if (dir.includes('w')) { W = g0.W - dx; ml = g0.ml - dx }
        if (dir.includes('e')) { W = g0.W + dx }
        if (dir.includes('n')) { H = g0.H - dy; mt = g0.mt - dy }
        if (dir.includes('s')) { H = g0.H + dy }
        W = Math.max(16, Math.min(W, g0.iw)); H = Math.max(16, Math.min(H, g0.ih))
        ml = Math.max(W - g0.iw, Math.min(0, ml)); mt = Math.max(H - g0.ih, Math.min(0, mt))
        g.W = W; g.H = H; g.ml = ml; g.mt = mt
      }
      cur = g
      applyImgGeom(el, g)
      recomputeImgRz()
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      persistImg(id, (wrap) => applyImgGeom(wrap, cur))
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // reset crop: window snaps back to the full (current-scale) image
  const resetImgCrop = () => {
    const id = imgSel; if (!id) return
    persistImg(id, (wrap) => {
      const g = readImgGeom(wrap)
      applyImgGeom(wrap, { W: g.iw, H: g.ih, iw: g.iw, ih: g.ih, ml: 0, mt: 0 })
    })
  }
  const alignImg = (ta: 'right' | 'center' | 'left') => {
    const id = imgSel; if (!id) return
    persistImg(id, (wrap) => {
      const blk = wrap.closest('div,p') as HTMLElement | null
      if (blk) { blk.style.textAlign = ta; blk.style.textIndent = '0' }
    })
  }
  const deleteImg = () => {
    const id = imgSel; if (!id) return
    if (!confirm('حذفِ این تصویر؟')) return
    persistImg(id, (wrap) => {
      const blk = wrap.closest('div,p') as HTMLElement | null
      wrap.remove()
      if (blk && !(blk.textContent || '').trim() && !blk.querySelector('img,table')) blk.remove()
    })
    setImgSel(null)
  }
  // drag the image between paragraph boundaries (same drop indicator as tables)
  const startImgMove = (e: React.PointerEvent) => {
    e.preventDefault(); e.stopPropagation()
    const id = imgSel; if (!id) return
    const el = liveImg(id); if (!el) return
    const cells = letterCells()
    let target: { cell: HTMLElement; ref: Element | null } | null = null
    const ownBlock = (c: HTMLElement) => { let n: HTMLElement | null = el; while (n && n.parentElement !== c) n = n.parentElement; return n }
    const mv = (ev: PointerEvent) => {
      target = null
      for (const cell of cells) {
        const r = cell.getBoundingClientRect()
        if (ev.clientX < r.left - 40 || ev.clientX > r.right + 40 || ev.clientY < r.top || ev.clientY > r.bottom) continue
        const own = ownBlock(cell)
        const kids = (Array.from(cell.children) as HTMLElement[]).filter((k) => k !== own)
        let ref: Element | null = null
        let y = kids.length ? kids[kids.length - 1].getBoundingClientRect().bottom : r.top + 4
        for (const k of kids) { const kr = k.getBoundingClientRect(); if (ev.clientY < kr.top + kr.height / 2) { ref = k; y = kr.top; break } }
        target = { cell, ref }
        setDropInd({ x: r.left, w: r.width, y })
        break
      }
      if (!target) setDropInd(null)
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      setDropInd(null)
      if (!target) return
      // detach: if the image's block holds ONLY the image, move the whole block;
      // otherwise pull the image out into its own centered block
      const cellOfEl = el.closest('.bcell') as HTMLElement | null
      let node: HTMLElement = el
      if (cellOfEl) {
        const own = (() => { let n: HTMLElement | null = el; while (n && n.parentElement !== cellOfEl) n = n.parentElement; return n })()
        if (own && !(own.textContent || '').trim() && own.querySelectorAll('img').length === 1 && !own.querySelector('table')) node = own
      }
      let carrier: HTMLElement
      if (node === el) { carrier = document.createElement('div'); carrier.style.cssText = 'text-align:center;text-indent:0'; carrier.appendChild(el) }
      else carrier = node
      let ref = target.ref
      if (ref === carrier) ref = carrier.nextElementSibling
      target.cell.insertBefore(carrier, ref)
      setF((prev) => ({ ...prev, body: cells.map((c) => c.innerHTML).join('') }))
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }

  // ---- Download the letter EXACTLY as prepared — as PDF or Word (.docx).
  //      Each print-view sheet is rendered by the browser itself (SVG foreignObject
  //      via html-to-image → real layout: RTL, justify, local fonts, floats, images)
  //      into a 2x PNG; then either placed full-bleed on A4 PDF pages or embedded
  //      one-per-section in a real .docx (portrait/landscape per page). All the
  //      libraries are lazy-loaded on first use. ----
  const [pdfBusy, setPdfBusy] = useState(false)
  const [dlMenu, setDlMenu] = useState(false)
  const exportName = () => (title.trim() || plain(f.subject) || 'نامه').replace(/[\\/:*?"<>|]/g, '-').slice(0, 80)
  const saveBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const aEl = document.createElement('a')
    aEl.href = url; aEl.download = filename
    document.body.appendChild(aEl); aEl.click(); aEl.remove()
    setTimeout(() => URL.revokeObjectURL(url), 5000)
  }
  // one 2x PNG per print sheet, rendered off-screen with the page's real CSS
  const renderSheetPngs = async (tId: string, label: string): Promise<{ png: string; land: boolean }[]> => {
    const { toPng } = await import('html-to-image')
    const sheets = Array.from(document.querySelectorAll('.print-wrap .psheet')) as HTMLElement[]
    if (!sheets.length) throw new Error('empty')
    const host = document.createElement('div')
    host.style.cssText = 'position:absolute;left:-99999px;top:0;background:#fff'
    document.body.appendChild(host)
    try {
      const out: { png: string; land: boolean }[] = []
      for (let i = 0; i < sheets.length; i++) {
        toast.loading(`در حالِ ساختِ ${label} — صفحهٔ ${fa(i + 1)} از ${fa(sheets.length)}…`, { id: tId })
        const src = sheets[i]
        const land = src.classList.contains('land')
        const W = land ? PAGE_H : PAGE_W, H = land ? PAGE_W : PAGE_H
        const clone = src.cloneNode(true) as HTMLElement
        clone.style.margin = '0'; clone.style.boxShadow = 'none'
        host.innerHTML = ''; host.appendChild(clone)
        out.push({ png: await toPng(clone, { pixelRatio: 2, width: W, height: H, backgroundColor: '#ffffff' }), land })
      }
      return out
    } finally { if (host.parentNode) host.parentNode.removeChild(host) }
  }
  const downloadPdf = async () => {
    if (pdfBusy) return
    setPdfBusy(true); setDlMenu(false)
    const tId = toast.loading('در حالِ ساختِ PDF…')
    try {
      const [pngs, { jsPDF }] = await Promise.all([renderSheetPngs(tId, 'PDF'), import('jspdf')])
      let pdf: any = null
      for (const pg of pngs) {
        const orient = pg.land ? 'landscape' : 'portrait'
        if (!pdf) pdf = new jsPDF({ orientation: orient, unit: 'mm', format: 'a4', compress: true })
        else pdf.addPage('a4', orient)
        pdf.addImage(pg.png, 'PNG', 0, 0, pg.land ? 297 : 210, pg.land ? 210 : 297, undefined, 'FAST')
      }
      saveBlob(pdf.output('blob'), `${exportName()}.pdf`)
      toast.success('PDF دانلود شد — دقیقاً با همان ظاهرِ نامه', { id: tId })
      auditApi.logActivity({ action: 'export', entity_type: 'letter', detail: `دانلود PDF نامه${plain(f.subject) ? ` — موضوع: ${plain(f.subject)}` : ''}` })
    } catch {
      toast.error('ساختِ PDF ناموفق بود — دوباره تلاش کن', { id: tId })
    } finally { setPdfBusy(false) }
  }
  // renders ONE behind-text float (its real CSS) → PNG, for the Word export
  const renderFloatPngForWord = async (html: string, w: number): Promise<{ png: string; h: number }> => {
    const { toPng } = await import('html-to-image')
    const host = document.createElement('div')
    host.style.cssText = 'position:absolute;left:-99999px;top:0;background:#fff'
    const box = document.createElement('div')
    box.className = 'lfloat'
    box.style.cssText = `position:static;width:${Math.round(w)}px`
    box.innerHTML = html
    host.appendChild(box)
    document.body.appendChild(host)
    try {
      const h = Math.max(10, Math.ceil(box.getBoundingClientRect().height))
      const png = await toPng(box, { pixelRatio: 2, width: Math.round(w), height: h, backgroundColor: undefined })
      return { png, h }
    } finally { document.body.removeChild(host) }
  }
  const downloadWord = async () => {
    if (pdfBusy) return
    setPdfBusy(true); setDlMenu(false)
    const tId = toast.loading('در حالِ ساختِ فایلِ Word (متنِ قابلِ ویرایش)…')
    try {
      const { buildLetterDocx } = await import('./wordExport')
      const blob = await buildLetterDocx({
        f: f as any, labels, L: L as any, attTables, attMeta: attMeta as any, floats,
        pageW: PAGE_W, pageH: PAGE_H, bodyFontPt: L.body.size || 13,
        renderFloatPng: renderFloatPngForWord,
      })
      saveBlob(blob, `${exportName()}.docx`)
      toast.success('فایلِ Word دانلود شد — متن، جدول‌ها و فیلدها همه قابلِ ویرایش‌اند', { id: tId })
      auditApi.logActivity({ action: 'export', entity_type: 'letter', detail: `دانلود Word نامه${plain(f.subject) ? ` — موضوع: ${plain(f.subject)}` : ''}` })
    } catch {
      toast.error('ساختِ Word ناموفق بود — دوباره تلاش کن', { id: tId })
    } finally { setPdfBusy(false) }
  }

  // ---- Behind-text float interactions ----
  const startFloatDrag = (e: React.PointerEvent, id: string) => {
    e.preventDefault(); e.stopPropagation()
    setFloatSel(id)
    const el = document.querySelector(`[data-flt="${cssEsc(id)}"]`) as HTMLElement | null
    const fl = floats.find((x) => x.id === id)
    if (!el || !fl) return
    const homeSheet = el.closest('.lsheet') as HTMLElement | null
    if (!homeSheet) return
    const homeTop = homeSheet.getBoundingClientRect().top, homeLeft = homeSheet.getBoundingClientRect().left
    const sx = e.clientX, sy = e.clientY
    let dx = 0, dy = 0
    const mv = (ev: PointerEvent) => { dx = ev.clientX - sx; dy = ev.clientY - sy; el.style.transform = `translate(${dx}px, ${dy}px)` }
    const up = (ev: PointerEvent) => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      el.style.transform = ''
      const sheets = letterSheets()
      let pi = Math.min(fl.page, sheets.length - 1)
      // the sheet under the pointer wins (a float can hop to another letter page)
      for (let i = 0; i < sheets.length; i++) { const r = sheets[i].getBoundingClientRect(); if (ev.clientY >= r.top && ev.clientY <= r.bottom) { pi = i; break } }
      const tr = sheets[pi]?.getBoundingClientRect(); if (!tr) return
      const elH = el.getBoundingClientRect().height
      const nx = Math.max(0, Math.min(tr.width - fl.w, (homeLeft + fl.x + dx) - tr.left))
      const ny = Math.max(0, Math.min(tr.height - Math.min(elH, tr.height), (homeTop + fl.y + dy) - tr.top))
      updateFloat(id, { x: Math.round(nx), y: Math.round(ny), page: pi })
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  const startFloatResize = (e: React.PointerEvent, id: string) => {
    e.preventDefault(); e.stopPropagation()
    const el = document.querySelector(`[data-flt="${cssEsc(id)}"]`) as HTMLElement | null
    const fl = floats.find((x) => x.id === id)
    if (!el || !fl) return
    const rightX = el.getBoundingClientRect().right   // RTL: the right edge stays anchored
    let w = fl.w
    const mv = (ev: PointerEvent) => {
      w = Math.max(60, Math.round(rightX - ev.clientX))
      el.style.width = `${w}px`
    }
    const up = () => {
      document.removeEventListener('pointermove', mv); document.removeEventListener('pointerup', up)
      updateFloat(id, { w, x: Math.max(0, Math.round(fl.x + (fl.w - w))) })
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
  }
  // bring a float back INTO the text flow, at the block boundary nearest its position
  const unfloat = (id: string) => {
    const fl = floats.find((x) => x.id === id); if (!fl) return
    const sheets = letterSheets()
    const pi = Math.min(fl.page, sheets.length - 1)
    const cell = (Array.from(sheets[pi]?.querySelectorAll('.bcell') || []) as HTMLElement[]).filter((c) => !c.closest('.lfloat'))[0]
    if (!cell) { toast.error('صفحهٔ مقصد پیدا نشد'); return }
    const holder = document.createElement('div')
    holder.innerHTML = fl.html
    let node: HTMLElement
    if (fl.kind === 'table') node = (holder.querySelector('table') as HTMLElement) || holder
    else { holder.style.cssText = 'text-align:center;text-indent:0'; node = holder }
    const sheetTop = sheets[pi].getBoundingClientRect().top
    const targetY = sheetTop + fl.y
    let ref: Element | null = null
    for (const k of Array.from(cell.children)) { const kr = k.getBoundingClientRect(); if (targetY < kr.top + kr.height / 2) { ref = k; break } }
    cell.insertBefore(node, ref)
    setF((prev) => ({ ...prev, body: letterCells().map((c) => c.innerHTML).join('') }))
    removeFloat(id)
    toast.success('به داخلِ متن برگشت')
  }
  // «پشتِ متن» for the table under the caret (letter-body tables only)
  const floatCurrentTable = () => {
    const sl = window.getSelection(); if (!sl || !sl.rangeCount) return
    const n = sl.anchorNode || sl.focusNode
    const el = n ? (n.nodeType === 3 ? n.parentElement : (n as HTMLElement)) : null
    const liveTable = el?.closest('table') as HTMLTableElement | null
    const hdrUid = liveTable?.rows[0]?.getAttribute('data-r') || ''
    if (!liveTable || !hdrUid) return
    if (liveTable.closest('.attsheet')) { toast('جدولِ پیوست صفحهٔ مستقلِ خودش را دارد'); return }
    if (liveTable.closest('.lfloat')) { toast('این جدول همین حالا پشتِ متن است'); return }
    const sheet = liveTable.closest('.lsheet') as HTMLElement | null
    if (!sheet) return
    const page = Math.max(0, letterSheets().indexOf(sheet))
    // merge page-split fragments into one table html
    const frags = liveTablesFor(hdrUid).filter((t) => !t.closest('.attsheet') && !t.closest('.lfloat'))
    const combined = frags[0].cloneNode(true) as HTMLTableElement
    const tb = combined.querySelector('tbody') || combined
    for (let fi = 1; fi < frags.length; fi++) Array.from(frags[fi].rows).forEach((row, ri) => { if (ri === 0 && row.getAttribute('data-r') === hdrUid) return; tb.appendChild(row.cloneNode(true)) })
    const r = frags[0].getBoundingClientRect(), sr = sheet.getBoundingClientRect()
    const fid = uid()
    setFloats((list) => [...list, { id: fid, kind: 'table', html: combined.outerHTML, x: Math.round(r.left - sr.left), y: Math.round(r.top - sr.top), w: Math.round(r.width), w0: Math.round(r.width), page }])
    // remove from the flow
    const rm = (html: string): string | null => {
      const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(html)
      mergeAdjacentTables(scratch); normalizeTables(scratch)
      const tr2 = scratch.querySelector(`tr[data-r="${cssEsc(hdrUid)}"]`) as HTMLTableRowElement | null
      const table = tr2?.closest('table') as HTMLTableElement | null
      if (!table) return null
      table.remove()
      return scratch.innerHTML
    }
    const nb = rm(f.body)
    if (nb != null) setF((prev) => ({ ...prev, body: nb }))
    setTbl(null); setColRz(null); setFloatSel(fid)
    toast.success('جدول «پشتِ متن» شد — با دستگیرهٔ ⠿ بالای آن آزادانه جابه‌جایش کن')
  }
  // «پشتِ متن» for the selected image
  const floatCurrentImg = () => {
    const id = imgSel; if (!id) return
    const el = liveImg(id); if (!el) return
    if (el.closest('.attsheet')) { toast('تصویرِ داخلِ صفحهٔ پیوست پشتِ متن نمی‌شود'); return }
    const sheet = el.closest('.lsheet') as HTMLElement | null
    if (!sheet) return
    const page = Math.max(0, letterSheets().indexOf(sheet))
    const r = el.getBoundingClientRect(), sr = sheet.getBoundingClientRect()
    const fid = uid()
    setFloats((list) => [...list, { id: fid, kind: 'image', html: el.outerHTML, x: Math.round(r.left - sr.left), y: Math.round(r.top - sr.top), w: Math.round(r.width), w0: Math.round(r.width), page }])
    persistImg(id, (wrap) => {
      const blk = wrap.closest('div,p') as HTMLElement | null
      wrap.remove()
      if (blk && !(blk.textContent || '').trim() && !blk.querySelector('img,table')) blk.remove()
    })
    setImgSel(null); setFloatSel(fid)
    toast.success('تصویر «پشتِ متن» شد — با دستگیرهٔ ⠿ بالای آن آزادانه جابه‌جایش کن')
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
    // flatten paste-wrappers (Word wraps the whole letter in one <div>): promote a
    // block whose children are themselves blocks/tables/lists to the top level, so
    // paragraphs and tables become siblings we can treat individually.
    let changed = true, guard = 0
    while (changed && guard++ < 60) {
      changed = false
      for (const c of Array.from(doc.children)) {
        if (/^(DIV|P)$/.test(c.tagName) && Array.from(c.children).some((g) => /^(DIV|P|TABLE|UL|OL)$/.test(g.tagName))) {
          while (c.firstChild) doc.insertBefore(c.firstChild, c)
          doc.removeChild(c); changed = true
        }
      }
    }
    const out: string[] = []
    let group: string[] = []
    const flush = () => { if (group.length) { out.push(`<div>${group.join(' ')}</div>`); group = [] } }
    const isDash = (t: string) => /^[-–—_.،؛:]{1,3}$/.test(t)
    const isGreet = (t: string) => /^با\s*سلام|^باسلام|سلام\s*و\s*احترام/.test(t)
    const ends = (t: string) => /[.؟!:]\s*$/.test(t)
    for (const el of Array.from(doc.children)) {
      // never reflow structural blocks — keep tables & lists intact
      if (/^(TABLE|UL|OL)$/.test(el.tagName) || el.querySelector('table,ul,ol,img')) { flush(); out.push(el.outerHTML); continue }
      // split on <br> AND newlines (a pre-wrap block can hold \n line breaks too)
      const segs = (el as HTMLElement).innerHTML.split(/<br\s*\/?>|\r?\n/i)
      for (const seg of segs) {
        const t = seg.replace(/<[^>]+>/g, '').replace(/ /g, ' ').trim()
        if (!t && /<img/i.test(seg)) { flush(); out.push(`<div>${seg}</div>`); continue }  // image-only line — keep it
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
    if (!f.body) return
    const needRows = f.body.indexOf('<table') !== -1 && /<tr(?![^>]*data-r)/i.test(f.body)
    const needImgs = /<img/i.test(f.body) && (() => { const d0 = document.createElement('div'); d0.innerHTML = f.body; return Array.from(d0.querySelectorAll('img')).some((im) => !(((im.closest('.imgcrop') as HTMLElement | null) || im).getAttribute('data-im'))) })()
    if (!needRows && !needImgs) return
    const d = document.createElement('div'); d.innerHTML = f.body; normalizeTables(d)
    // every image (or its crop wrapper) gets a stable id so the image toolbar can
    // locate it in the body — the mirror of the tables' data-r
    d.querySelectorAll('img').forEach((im) => {
      const holder = (im.closest('.imgcrop') as HTMLElement | null) || im
      if (!holder.getAttribute('data-im')) holder.setAttribute('data-im', uid())
    })
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
      // table toolbar — while the caret is in a cell we show ONE combined table bar
      // (which includes the text-format buttons) and hide the standalone format bar so
      // the two never overlap.
      const cell = (!designRef.current && el) ? (el.closest('.bcell td, .bcell th') as HTMLElement | null) : null
      if (cell) {
        const table = cell.closest('table') as HTMLTableElement
        const t = table.getBoundingClientRect(); setTbl({ x: t.left + t.width / 2, y: t.top }); setFmt(null)
        recomputeColRz(table.rows[0]?.getAttribute('data-r') || '')   // column-resize handles at the table's borders
        return
      }
      setTbl(null); setColRz(null)
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
  // keep the column-resize handles aligned with the table while scrolling (they're fixed)
  const colRzRef = useRef(colRz); useEffect(() => { colRzRef.current = colRz }, [colRz])
  useEffect(() => {
    let raf = 0
    const onScroll = () => { const c = colRzRef.current; if (!c) return; cancelAnimationFrame(raf); raf = requestAnimationFrame(() => recomputeColRz(c.hdrUid)) }
    window.addEventListener('scroll', onScroll, true)
    return () => { window.removeEventListener('scroll', onScroll, true); cancelAnimationFrame(raf) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // contY = where the body continues on pages 2+ (just below the header; adjustable).
  const contY = L.body.contY ?? (Math.max(L.logo.y + (L.logo.h || 0), L.name.y + (L.name.h || 0)) + m(6))
  const gap = m(4)
  const pageNumLimit = (L.pagenum?.y ?? m(270)) - gap
  // The reserved closing zone starts at the TOPMOST closing field — but only
  // fields that are visible AND actually sit inside/below the body region.
  // A closing box dragged ABOVE the body start (or hidden) must not shrink
  // the text region: it collapsed the last page's capacity to ~zero, so even
  // a half-empty letter banished the whole closing block to a fresh page.
  const closingYs = CLOSING.map((k) => L[k]).filter((b) => b && !b.hidden && b.y >= L.body.y).map((b) => b.y)
  const closingTop = (closingYs.length ? Math.min(...closingYs) : pageNumLimit + gap) - gap
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
  // How far the closing block slides DOWN on the last page to clear the content
  // (0 = exactly where «چیدمان» put it). Bounded by the page-number/footer floor.
  const [closingShift, setClosingShift] = useState(0)
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
    type Unit = { kind: 'block'; h: number; html: string } | { kind: 'trow'; h: number; tid: number; header: string; headerH: number; rowHtml: string; topen: string }
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
            // the OPENING tag keeps the table-level class/style (tblw width/offset) —
            // rebuilding pages with a bare <table> silently reset resized tables
            const topen = c.outerHTML.slice(0, c.outerHTML.indexOf('>') + 1)
            for (let i = 1; i < rows.length; i++) units.push({ kind: 'trow', tid, header, headerH, topen, rowHtml: (rows[i] as HTMLElement).outerHTML, h: (rows[i] as HTMLElement).offsetHeight })
          } else units.push({ kind: 'block', html: c.outerHTML, h: c.offsetHeight })
        } else if (c.querySelector('table')) {
          collect(c)   // unwrap: promote the nested table (+ its siblings) to top-level units
        } else {
          units.push({ kind: 'block', html: c.outerHTML, h: c.offsetHeight })
        }
      }
    }
    collect(el)
    const M = el as HTMLElement
    const measure1 = (h: string) => { M.innerHTML = h; return M.offsetHeight }
    // Split ONE text block so its first part fits `availH`; returns [fits, remainder]
    // (both keep the block's tag/style). Splits at word / inline-element boundaries so
    // bold/underline spans are never sliced. Empty first = nothing fit.
    const splitBlock = (blockHTML: string, availH: number): [string, string] => {
      const tmp = document.createElement('div'); tmp.innerHTML = blockHTML
      const block = tmp.firstElementChild as HTMLElement | null
      if (!block) return [blockHTML, '']
      const tag = block.tagName.toLowerCase(), st = block.getAttribute('style')
      const open = `<${tag}${st ? ` style="${st}"` : ''}>`, close = `</${tag}>`
      const atoms: string[] = []
      block.childNodes.forEach((n) => {
        if (n.nodeType === 3) (n.textContent || '').split(/(\s+)/).forEach((w) => { if (w) atoms.push(w) })
        else if (n.nodeType === 1) atoms.push((n as HTMLElement).outerHTML)
      })
      if (atoms.length <= 1) return [blockHTML, '']
      const build = (k: number) => open + atoms.slice(0, k).join('') + close
      let lo = 1, hi = atoms.length, best = 0
      while (lo <= hi) { const mid = (lo + hi) >> 1; if (measure1(build(mid)) <= availH) { best = mid; lo = mid + 1 } else hi = mid - 1 }
      if (best <= 0) return ['', blockHTML]
      if (best >= atoms.length) return [blockHTML, '']
      return [build(best), open + atoms.slice(best).join('').replace(/^\s+/, '') + close]
    }
    const pageH = (us: Unit[]) => { let h = 0; const seen = new Set<number>(); for (const u of us) { h += u.h; if (u.kind === 'trow' && !seen.has(u.tid)) { h += u.headerH; seen.add(u.tid) } } return h }
    // An invisible block: only whitespace/<br> (contentEditable leftovers; insertTable
    // always appends one after the table so the caret has a place below it).
    const isEmptyBlock = (u: Unit) => u.kind === 'block' && !u.html.replace(/<br\s*\/?>/gi, '').replace(/<[^>]+>/g, '').replace(/&nbsp;| /gi, ' ').trim()
    // Flow the units across pages, packing each page to its FULL text region and SPLITTING
    // any text block taller than the space left so long paragraphs continue on the next
    // page. `lastIdx` marks the page that must leave room for the closing block; pass -1
    // to reserve nothing (pack everything as tightly as possible → lines flow back when
    // space frees). Wall-clock: every page filled to capacity, nothing wasted.
    const distribute = (lastIdx: number): Unit[][] => {
      const pgs: Unit[][] = []
      let cur: Unit[] = [], used = 0, pi = 0
      const seen = new Set<number>()
      const push = () => { pgs.push(cur); cur = []; used = 0; pi++; seen.clear() }
      const cap = () => regionAvail(pi, pi === lastIdx)
      const q: Unit[] = units.slice()
      let dg = 0
      while (q.length && dg++ < 6000) {
        const u = q.shift() as Unit
        if (u.kind === 'trow') {
          const need = u.h + (!seen.has(u.tid) ? u.headerH : 0)
          if (cur.length && used + need > cap()) push()
          used += u.h + (!seen.has(u.tid) ? u.headerH : 0); cur.push(u); seen.add(u.tid); continue
        }
        const avail = cap() - used
        if (u.h <= avail || u.h === 0) { cur.push(u); used += u.h; continue }
        // Trailing INVISIBLE empties must never open a new page (a phantom page
        // that also drags the closing block with it — e.g. the caret line that
        // insertTable appends). Once only empty blocks remain, keep them on the
        // current page over-cap; they're clipped, nothing visible overflows.
        if (isEmptyBlock(u) && q.every((x) => isEmptyBlock(x))) { cur.push(u); continue }
        if (avail < 48 && cur.length) { push(); q.unshift(u); continue }
        const [fit, rest] = splitBlock(u.html, Math.max(48, avail))
        if (!fit) { if (cur.length) { push(); q.unshift(u) } else { cur.push(u); used += u.h }; continue }
        const hf = measure1(fit); cur.push({ kind: 'block', html: fit, h: hf }); used += hf
        if (rest) { push(); q.unshift({ kind: 'block', html: rest, h: measure1(rest) }) }
      }
      if (cur.length || !pgs.length) pgs.push(cur)
      return pgs
    }
    // Pack content tightly (every page filled to its full text region).
    const pages = distribute(-1)
    // KILL-SWITCH invariant: a trailing page whose content is ONLY invisible empty
    // blocks must never exist (it reads as «the closing jumped to an empty page»).
    // Whatever path produced it — fold its empties back onto the previous page.
    while (pages.length > 1) {
      const tail = pages[pages.length - 1]
      if (tail.some((u) => !isEmptyBlock(u))) break
      pages.pop()
      pages[pages.length - 1].push(...tail)
    }
    // The closing block (امضاکننده/رونوشت/اقدام) stays at the position you set in «چیدمان»
    // on the LAST page. A hard cliff here used to banish the whole closing to a fresh
    // page the moment content crossed the zone — even by 2px, and even when the
    // "content" was only invisible trailing empty lines (insertTable always appends
    // one). So, in order: (1) trailing EMPTY blocks don't count against the closing,
    // (2) a small overlap is absorbed by sliding the closing group DOWN into the free
    // space above the page number / footer, (3) only when even that can't clear the
    // content does the closing get its own trailing page.
    const li = pages.length - 1
    let shift = 0
    if (!isHidden('sender') && pages.length) {
      const us = pages[li].slice()
      while (us.length && isEmptyBlock(us[us.length - 1])) us.pop()
      const overflow = pageH(us) - regionAvail(li, true)
      if (overflow > 0) {
        // How far down can the closing go? Measure each visible closing field at its
        // real width/font (copyTo/action can wrap to several lines) and keep the
        // bottom-most one above the page-number line and the footer.
        const tmp = document.createElement('div')
        tmp.style.cssText = 'position:absolute;left:-99999px;top:0;visibility:hidden'
        document.body.appendChild(tmp)
        let closingBottom = 0
        for (const k of CLOSING) {
          const b = L[k]; if (!b || b.hidden) continue
          const inner = document.createElement('div')
          inner.style.cssText = `width:${b.w}px;font-size:${b.size}pt;line-height:1.25;white-space:normal${b.font ? `;font-family:${b.font}` : ''}`
          inner.innerHTML = k === 'sender' ? escapeHtml(f.sender || 'x')
            // mirror the hanging-flex layout (multi-line recipients under the first one)
            : k === 'copyto' ? `<span style="display:flex;align-items:baseline"><span style="white-space:pre;flex:0 0 auto">${labels.copyto || ''}</span><span style="flex:1 1 auto;min-width:0">${f.copyTo || 'x'}</span></span>`
            : (labels.action || '') + (f.actionName || 'x') + (labels.actionExt || '') + escapeHtml(f.actionExt || 'x')
          tmp.appendChild(inner)
          closingBottom = Math.max(closingBottom, b.y + inner.offsetHeight)
          tmp.removeChild(inner)
        }
        document.body.removeChild(tmp)
        const floor = Math.min(pageNumLimit, (L.footer && !L.footer.hidden ? L.footer.y : m(277)) - gap)
        const maxShift = Math.max(0, floor - closingBottom)
        if (overflow <= maxShift) shift = Math.ceil(overflow)
        else pages.push([])
      }
    }
    setClosingShift(shift)
    // Remote-debug aid: open the letter with ?pdbg=1 and read the console to see
    // exactly why pages/closing ended up where they did.
    if (typeof window !== 'undefined' && /[?&]pdbg=1/.test(window.location.search)) {
      // eslint-disable-next-line no-console
      console.info('[letter-pagination]', {
        pages: pages.length, heights: pages.map((p2) => pageH(p2)),
        availLast: regionAvail(pages.length - 1, true), availTight: pages.map((_, i2) => regionAvail(i2, false)),
        closingShift: shift, bodyY: L.body.y, bodyH: L.body.h,
        closingY: { sender: L.sender?.y, copyto: L.copyto?.y, action: L.action?.y },
      })
    }
    // re-group consecutive rows of the same table back into one <table> per page
    const render = (us: Unit[]) => {
      let out = '', i = 0
      while (i < us.length) {
        const u = us[i]
        if (u.kind === 'block') { out += u.html; i++ }
        else { const t = u.tid, hdr = u.header, open = (u as any).topen || '<table>'; let rr = ''; while (i < us.length && us[i].kind === 'trow' && (us[i] as any).tid === t) { rr += (us[i] as any).rowHtml; i++ } out += `${open}${hdr}${rr}</table>` }
      }
      return out
    }
    setPages(pages.length ? pages.map(render) : [''])
    if (temp && el.parentNode) el.parentNode.removeChild(el)
    // NB: the closing fields' own content changes the closing block's measured
    // height (copyTo/action wrap), so they re-run the slide computation too.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f.body, f.sender, f.copyTo, f.actionName, f.actionExt, labels, L])

  // ---- Subject: (1) shrink-to-fit ONE line (down to 75% of the set size, so it
  // never gets unreadably tiny), (2) separator length follows the subject, and
  // (3) if it still has to wrap, slide the separator BELOW the wrapped text so
  // the line never crosses the subject's words. ----
  useEffect(() => {
    const el = subjRef.current
    if (!el) return
    const S = L.subject.size || 12
    const full = L.subject.w
    el.style.whiteSpace = 'nowrap'; el.style.width = ''; el.style.fontSize = `${S}pt`
    el.textContent = plain(labels.subject) + plain(f.subject)
    const natural = el.offsetWidth + 4
    let fit = S
    if (natural > full) fit = Math.max(S * 0.75, (S * full) / natural)
    setSubjFit(fit < S ? Math.round(fit * 100) / 100 : null)
    el.style.fontSize = `${fit}pt`
    const w = Math.max(m(15), Math.min(el.offsetWidth + 4, full))
    setSepGeom({ x: (L.subject.x + L.subject.w) - w, w })
    // wrapped height at the fitted size → keep the separator clear of the text
    el.style.whiteSpace = 'normal'; el.style.width = `${full}px`
    const hWrapped = el.offsetHeight
    el.style.whiteSpace = 'nowrap'; el.style.width = ''
    const sepY = L.separator?.y ?? m(107)
    const bottom = L.subject.y + hWrapped + m(2)
    setSepShift(bottom > sepY ? Math.ceil(bottom - sepY) : 0)
  }, [labels.subject, f.subject, L.subject, L.separator])

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
  const P = (k: string, node: React.ReactNode, extra?: React.CSSProperties) => isHidden(k) ? null : <div style={{ ...boxStyle(k), ...extra }}>{node}</div>  // print: positioned, hide-aware
  const H = (h: string) => <span dangerouslySetInnerHTML={{ __html: h || '' }} />  // render a rich (HTML) value

  const totalPageCount = pages.length + attTables.length

  // Letterhead placement on an ATTACHMENT page. Portrait pages reuse the letter's
  // exact boxes; landscape pages keep each element's anchor: logo stays top-left,
  // the bank name keeps its distance from the RIGHT edge, footer/page-number keep
  // their horizontal balance and their distance from the BOTTOM edge — so the
  // letterhead renders correctly without ever touching the table area.
  const attHeadStyle = (k: string, land: boolean): React.CSSProperties => {
    const st = boxStyle(k)
    if (!land) return st
    const b = L[k], D = PAGE_H - PAGE_W
    if (k === 'name') return { ...st, left: b.x + D }
    if (k === 'footer' || k === 'pagenum') return { ...st, left: b.x + D / 2, top: b.y - D }
    return st
  }

  // Behind-text floats of one letter page: the visual layer sits FIRST inside the
  // sheet (painted under everything); a selected float raises above the text so its
  // table cells become editable. Controls (grip/resize/toolbar) render on top.
  const floatsOf = (pi: number) => floats.filter((fl) => Math.min(Math.max(0, fl.page), pages.length - 1) === pi)
  const floatLayer = (pi: number, editorMode: boolean) => floatsOf(pi).map((fl) => {
    const seld = editorMode && floatSel === fl.id
    return (
      <div key={fl.id} {...(editorMode ? { 'data-flt': fl.id } : {})} className={`lfloat${seld ? ' seld' : ''}`}
        style={{ left: fl.x, top: fl.y, width: fl.w, zIndex: seld ? 30 : 0 }}>
        {fl.kind === 'image'
          ? <div style={{ transform: `scale(${fl.w / Math.max(1, fl.w0)})`, transformOrigin: 'top left', width: fl.w0 }} dangerouslySetInnerHTML={{ __html: fl.html }} />
          : (seld
            ? <BodyCell html={fl.html} editable onChangeHtml={(h) => updateFloat(fl.id, { html: h })}
                style={{ fontFamily: latin(L.body.font), fontSize: `${L.body.size}pt`, direction: 'rtl', lineHeight: 1.35, height: 'auto' }} />
            : <div dangerouslySetInnerHTML={{ __html: fl.html }} />)}
      </div>
    )
  })
  const floatControls = (pi: number) => floatsOf(pi).map((fl) => {
    const seld = floatSel === fl.id
    return (
      <span key={`fc-${fl.id}`}>
        <button className="flt-grip no-print" title="پشتِ متن — کشیدن: جابه‌جاییِ آزاد؛ کلیک: ابزارها"
          style={{ left: fl.x, top: Math.max(0, fl.y - 18) }} onPointerDown={(e) => startFloatDrag(e, fl.id)}>⠿</button>
        {seld && <>
          <button className="flt-grip no-print" title="تغییرِ اندازه (لبهٔ راست ثابت می‌ماند)" style={{ left: fl.x + 24, top: Math.max(0, fl.y - 18), cursor: 'nesw-resize' }}
            onPointerDown={(e) => startFloatResize(e, fl.id)}>⇲</button>
          <div className="flt-bar no-print" dir="rtl" style={{ left: fl.x, top: Math.max(0, fl.y - 46) }}>
            <button onClick={() => unfloat(fl.id)}>بازگشت به متن</button>
            <button onClick={() => { if (confirm('حذفِ این آیتمِ پشتِ متن؟')) removeFloat(fl.id) }}>حذف</button>
            <button onClick={() => setFloatSel(null)}>بستن</button>
          </div>
        </>}
      </span>
    )
  })

  // one attachment-table page in the EDITABLE view — text is never rotated: a
  // landscape page is simply a wider sheet on screen, so editing stays natural.
  const attEditorPage = (t: AttTable, i: number) => {
    const meta = attMeta[t.id]
    const land = !!meta?.land, scale = meta?.scale ?? 1
    const W = land ? PAGE_H : PAGE_W, Hh = land ? PAGE_W : PAGE_H
    const contentW = W - 2 * ATT_MARGIN
    return (
      <div className="lsheet attsheet" key={`att-${t.id}`} style={land ? { width: W, height: Hh } : undefined}>
        {!isHidden('logo') && <div style={attHeadStyle('logo', land)}><img src={LH_LOGO} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        {!isHidden('name') && <div style={attHeadStyle('name', land)}><img src={LH_NAME} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        <div className="att-ttl" dir="rtl" style={{ position: 'absolute', left: ATT_MARGIN, top: ATT_TOP, width: contentW }}>
          <span className="att-badge">جدول {fa(i + 1)} پیوست</span>
          <RichSpan value={t.title} onChange={(h) => updateAttTable(t.id, { title: h })} placeholder="عنوانِ جدولِ پیوست…" style={{ fontFamily: latin(TITR), fontSize: '14pt', fontWeight: 700 }} />
          <button className="att-del no-print" title="حذفِ این جدولِ پیوست (و صفحه‌اش)" onClick={() => { if (confirm(`حذفِ جدول ${fa(i + 1)} پیوست؟`)) removeAttTable(t.id) }}>حذف</button>
        </div>
        {meta?.tooTall && <div className="att-warn no-print">جدول از یک صفحه بلندتر است — چند ردیف را حذف یا جدول را کوچک‌تر کن</div>}
        <BodyCell html={t.html} editable={!design} onChangeHtml={(h) => updateAttTable(t.id, { html: h })} transformPaste={cleanPaste}
          style={{ position: 'absolute', left: ATT_MARGIN, top: ATT_TOP + ATT_TITLE_H + (t.offY || 0), width: contentW, height: Hh - ATT_TOP - ATT_TITLE_H - (t.offY || 0) - ATT_BOTTOM, fontFamily: latin(L.body.font), fontSize: `${13 * scale}pt`, direction: 'rtl', lineHeight: 1.7 }} />
        {!isHidden('footer') && <div style={attHeadStyle('footer', land)}><img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        {!isHidden('pagenum') && <div style={{ ...attHeadStyle('pagenum', land), pointerEvents: 'none' }}>{`صفحه ${fa(pages.length + i + 1)} از ${fa(totalPageCount)}`}</div>}
      </div>
    )
  }

  // one attachment-table page in the PRINT view (landscape pages print via a
  // named @page rule — size:A4 landscape — so nothing is rotated or clipped)
  const attPrintPage = (t: AttTable, i: number) => {
    const meta = attMeta[t.id]
    const land = !!meta?.land, scale = meta?.scale ?? 1
    const W = land ? PAGE_H : PAGE_W, Hh = land ? PAGE_W : PAGE_H
    const contentW = W - 2 * ATT_MARGIN
    return (
      <div className={`psheet${land ? ' land' : ''}`} key={`patt-${t.id}`} style={land ? { width: W, height: Hh } : undefined}>
        {!isHidden('logo') && <div style={attHeadStyle('logo', land)}><img src={LH_LOGO} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        {!isHidden('name') && <div style={attHeadStyle('name', land)}><img src={LH_NAME} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        <div className="att-ttl" dir="rtl" style={{ position: 'absolute', left: ATT_MARGIN, top: ATT_TOP, width: contentW }}>
          <span className="att-badge">جدول {fa(i + 1)} پیوست</span>
          <span style={{ fontFamily: latin(TITR), fontSize: '14pt', fontWeight: 700 }} dangerouslySetInnerHTML={{ __html: t.title || '' }} />
        </div>
        <div className="bcell" dir="rtl" style={{ position: 'absolute', left: ATT_MARGIN, top: ATT_TOP + ATT_TITLE_H + (t.offY || 0), width: contentW, height: Hh - ATT_TOP - ATT_TITLE_H - (t.offY || 0) - ATT_BOTTOM, fontFamily: latin(L.body.font), fontSize: `${13 * scale}pt`, direction: 'rtl', lineHeight: 1.7, ['--ind' as any]: '0' }} dangerouslySetInnerHTML={{ __html: t.html }} />
        {!isHidden('footer') && <div style={attHeadStyle('footer', land)}><img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /></div>}
        {!isHidden('pagenum') && <div style={attHeadStyle('pagenum', land)}>{`صفحه ${fa(pages.length + i + 1)} از ${fa(totalPageCount)}`}</div>}
      </div>
    )
  }

  // one A4 page in the editable view
  const editorPage = (pi: number) => {
    const isLast = pi === pages.length - 1
    return (
      <div className="lsheet" key={pi}>
        {/* behind-text floats — painted first = under everything */}
        {floatLayer(pi, true)}
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
          {Box({ k: 'subject', style: subjFit ? { fontSize: `${subjFit}pt` } : undefined, children: <>{Lbl({ k: 'subject' })}<RichSpan value={f.subject} onChange={(h) => setF((s) => ({ ...s, subject: faDigitsHtml(h) }))} placeholder="موضوعِ نامه…" /></> })}
          {Box({ k: 'separator', style: !design && sepShift ? { top: L.separator.y + sepShift } : undefined, children: <div className="sep-line" /> })}
        </>}

        {/* body chunk for this page — page 1 box is draggable/resizable; others fill the region */}
        {pi === 0
          ? Box({ k: 'body', children: <BodyCell html={pages[0] || ''} editable={!design} indent={L.body.indent} firstPage onChangeHtml={onBody(0)} transformPaste={reflowPaste} style={{ ...bodyTextStyle(), width: '100%', height: '100%' }} /> })
          : (isHidden('body') ? null : <BodyCell html={pages[pi] || ''} editable={!design} indent={L.body.indent} onChangeHtml={onBody(pi)} transformPaste={reflowPaste}
            style={{ ...bodyTextStyle(), position: 'absolute', left: L.body.x, top: contY, width: L.body.w, height: regionAvail(pi, false) }} />)}

        {/* closing block — only on the last page (slid down by closingShift when the
            content would otherwise collide with its designed position; in «چیدمان»
            mode it sits at its TRUE designed spot so dragging isn't confusing) */}
        {isLast && (() => { const cs = design ? 0 : closingShift; return <>
          {Box({ k: 'sender', style: cs ? { top: L.sender.y + cs } : undefined, children: <select className="fld" value={f.sender} onChange={set('sender')}>{SENDERS.map((s) => <option key={s}>{s}</option>)}</select> })}
          {Box({ k: 'copyto', style: cs ? { top: L.copyto.y + cs } : undefined, children: <span className="hangfld"><span className="hlbl">{Lbl({ k: 'copyto' })}</span><span className="hval"><RichSpan multiline value={f.copyTo} onChange={(h) => setF((s) => ({ ...s, copyTo: h }))} placeholder="------ (Enter: گیرندهٔ بعدی)" /></span></span> })}
          {Box({ k: 'action', style: cs ? { top: L.action.y + cs } : undefined, children: <>{Lbl({ k: 'action' })}<RichSpan value={f.actionName} onChange={(h) => setF((s) => ({ ...s, actionName: h }))} placeholder="----" />{Lbl({ k: 'actionExt' })}<AutoInput dir="ltr" value={f.actionExt} onChange={set('actionExt')} placeholder="---" style={{ textAlign: 'right' }} /></> })}
        </> })()}

        {pi === 0 ? Box({ k: 'footer', children: <img src={LH_FOOTER} alt="" style={{ width: '100%', height: '100%' }} /> }) : repImg('footer', LH_FOOTER)}
        {pi === 0
          ? Box({ k: 'pagenum', children: `صفحه ${fa(1)} از ${fa(totalPageCount)}` })
          : (isHidden('pagenum') ? null : <div style={{ ...boxStyle('pagenum'), pointerEvents: 'none' }}>{`صفحه ${fa(pi + 1)} از ${fa(totalPageCount)}`}</div>)}
        {/* float grips/toolbars — always on top, editor only */}
        {floatControls(pi)}
      </div>
    )
  }

  // one A4 page in the print view (read-only values, paragraphs indented)
  const printPage = (pi: number) => {
    const isLast = pi === pages.length - 1
    return (
      <div className="psheet" key={pi}>
        {floatLayer(pi, false)}
        {repImg('logo', LH_LOGO)}{repImg('name', LH_NAME)}
        {pi === 0 && <>
          {P('besmele', H(labels.besmele))}
          {P('shomareh', <>{H(labels.shomareh)}<span dir="ltr">{`182 / 4 / ${f.serial} / ${f.year}`}</span></>)}
          {P('tarikh', <>{H(labels.tarikh)}<span dir="ltr">{f.date}</span></>)}
          {P('peyvast', <>{H(labels.peyvast)}{f.attachment}</>)}
          {P('recName', H(f.recipientName))}
          {P('recTitle', <>{H(f.recipientTitle)} {H(f.recipientDept)}</>)}
          {P('classification', <>{H(labels.classification)}{f.classification}</>)}
          {P('subject', <>{H(labels.subject)}{H(f.subject)}</>, subjFit ? { fontSize: `${subjFit}pt` } : undefined)}
          {P('separator', <div className="sep-line" />, sepShift ? { top: L.separator.y + sepShift } : undefined)}
        </>}
        {!isHidden('body') && <div className={`bcell${pi === 0 ? ' firstpage' : ''}`} style={{ ...bodyTextStyle(), position: 'absolute', left: L.body.x, top: regionTop(pi), width: L.body.w, ['--ind' as any]: L.body.indent ? `${L.body.indent}em` : '0' }} dangerouslySetInnerHTML={{ __html: pages[pi] || '' }} />}
        {isLast && <>
          {P('sender', f.sender, closingShift ? { top: L.sender.y + closingShift } : undefined)}
          {P('copyto', <span className="hangfld"><span className="hlbl">{H(labels.copyto)}</span><span className="hval">{H(f.copyTo)}</span></span>, closingShift ? { top: L.copyto.y + closingShift } : undefined)}
          {P('action', <>{H(labels.action)}{H(f.actionName)}{H(labels.actionExt)}<span dir="ltr">{f.actionExt}</span></>, closingShift ? { top: L.action.y + closingShift } : undefined)}
        </>}
        {repImg('footer', LH_FOOTER)}
        {!isHidden('pagenum') && <div style={boxStyle('pagenum')}>{`صفحه ${fa(pi + 1)} از ${fa(totalPageCount)}`}</div>}
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
        .dl-menu{position:absolute;top:calc(100% + 4px);right:0;z-index:200;background:#fff;border:1px solid #e2e8f0;border-radius:9px;box-shadow:0 10px 28px rgba(15,23,42,.22);display:flex;flex-direction:column;min-width:170px;overflow:hidden}
        .dl-menu button{border:0;background:#fff;color:#0f172a;text-align:right;padding:9px 13px;font-size:13px;cursor:pointer;font-family:inherit}
        .dl-menu button:hover{background:#fff7ed;color:#9a3412}
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
        /* overflow:clip + a small clip-margin instead of overflow:hidden: still clips
           the box (pagination height stays controlled) but paints a few px past the
           edge so the FIRST glyph of a wrapped RTL line (esp. bold, e.g. «ابطال»/
           «مخاطراتی» at line start) isn't shaved off by the right edge. */
        .bcell{width:100%;height:100%;overflow:clip;overflow-clip-margin:4px;outline:none;white-space:pre-wrap;word-break:normal;overflow-wrap:break-word}
        .bcell > div,.bcell > p{text-indent:var(--ind,0)}
        .bcell.firstpage > div:first-child,.bcell.firstpage > p:first-child{text-indent:0}
        /* pasted paragraphs shouldn't carry Word's big block margins (huge line gaps) */
        .bcell p,.psheet p,.measure p{margin:0}
        /* pasted tables fit the box width, stay COMPACT (content-height rows), with
           borders and sensible wrapping (no character-by-character breaking) */
        .bcell table,.psheet table,.measure table{width:100%!important;max-width:100%;border-collapse:collapse;margin:3px 0;font-size:inherit;table-layout:auto}
        /* a user-resized table: width set by the outer-edge drag handles (default
           stays 100% — legacy letters untouched); --toff = distance from the RIGHT
           edge (RTL start) so a shrunk table can be dragged left/right; margin-left
           auto absorbs the remainder. Same vars in measurer + print. */
        .bcell table.tblw,.psheet table.tblw,.measure table.tblw{width:var(--tw)!important;margin-left:auto!important;margin-right:var(--toff,0%)!important}
        .bcell td,.bcell th,.psheet td,.psheet th,.measure td,.measure th{border:0.6px solid #222;padding:2px 5px;vertical-align:top;white-space:normal;word-break:normal;overflow-wrap:break-word;line-height:1.35;text-indent:0!important}
        .bcell td *,.bcell th *,.psheet td *,.psheet th *,.measure td *,.measure th *{text-indent:0!important;margin:0}
        .bcell th,.psheet th,.measure th{font-weight:700;text-align:center;background:#f3f4f6}
        /* Persian underline: the default underline position cuts through the
           descenders/dots of Arabic-script glyphs. Draw it UNDER the script,
           continuous (no ink-skip gaps), slightly thin — everywhere the letter
           renders: editor cells, print sheets, the measurer and rich fields. */
        .bcell u,.psheet u,.measure u,#ltr-edit .rich u{text-underline-position:under;text-underline-offset:1px;text-decoration-thickness:.8px;text-decoration-skip-ink:none}
        .bcell img,.psheet img{max-width:100%}
        /* uniform image holder: resize scales it, crop shrinks the window while the
           inner img is offset by margins — the img may exceed the window on purpose */
        .bcell .imgcrop,.psheet .imgcrop,.measure .imgcrop{display:inline-block;overflow:hidden;max-width:100%;vertical-align:middle}
        .bcell .imgcrop img,.psheet .imgcrop img,.measure .imgcrop img{display:block;max-width:none!important}
        /* hanging field (رونوشت): label fixed at the RTL start, value column grows —
           every extra line (<br>) aligns under the FIRST recipient, not the label */
        .hangfld{display:flex;align-items:baseline;width:100%}
        .hangfld .hlbl{white-space:pre;flex:0 0 auto}
        .hangfld .hval{flex:1 1 auto;min-width:0}
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
        .tbl-bar{position:fixed;transform:translate(-50%,-135%);z-index:121;display:flex;gap:2px;align-items:center;flex-wrap:wrap;justify-content:center;max-width:min(92vw,760px);background:#0f766e;border-radius:7px;padding:3px 4px;box-shadow:0 6px 18px rgba(0,0,0,.32)}
        .drop-ind{position:fixed;height:3px;background:#7c3aed;border-radius:2px;z-index:130;pointer-events:none;box-shadow:0 0 6px rgba(124,58,237,.55)}
        .col-rz{position:fixed;width:6px;z-index:122;cursor:col-resize;background:transparent}
        .tbl-hmove{position:fixed;height:6px;z-index:122;cursor:ew-resize;background:transparent;border-radius:3px}
        .tbl-hmove:hover{background:rgba(15,118,110,.4)}
        /* image selection: floating bar, sizing handles, outline */
        .img-bar{position:fixed;transform:translate(-50%,-125%);z-index:124;display:flex;gap:2px;align-items:center;background:#334155;border-radius:7px;padding:3px 4px;box-shadow:0 6px 18px rgba(0,0,0,.32)}
        .img-bar button{border:0;background:transparent;color:#fff;height:24px;min-width:26px;padding:0 6px;border-radius:5px;cursor:pointer;font-size:12px;line-height:1;white-space:nowrap}
        .img-bar button:hover{background:#475569}
        .img-bar button.on{background:#0d9488}
        .img-bar button.del:hover{background:#b91c1c}
        .img-hd{position:fixed;width:10px;height:10px;background:#fff;border:2px solid #334155;border-radius:50%;z-index:125}
        .img-hd.crop{border-color:#0d9488;border-radius:2px}
        .img-outline{position:fixed;border:1.5px dashed #334155;z-index:120;pointer-events:none}
        /* behind-text floats: painted under the text (DOM-first, z 0); selected one
           raises so its cells are editable; controls live on top */
        .lfloat{position:absolute;z-index:0}
        .lfloat.seld{outline:2px dashed #7c3aed;background:#fff}
        .lfloat table{width:100%!important;border-collapse:collapse;margin:0;table-layout:auto}
        .lfloat td,.lfloat th{border:0.6px solid #222;padding:2px 5px;vertical-align:top;white-space:normal;overflow-wrap:break-word;line-height:1.35;text-indent:0!important}
        .lfloat th{font-weight:700;text-align:center;background:#f3f4f6}
        .lfloat .imgcrop{display:inline-block;overflow:hidden}
        .lfloat .imgcrop img{display:block;max-width:none}
        .lfloat .bcell{width:100%;height:auto;overflow:visible}
        .flt-grip{position:absolute;z-index:40;width:22px;height:17px;font-size:11px;line-height:1;border:1px solid #c7d2fe;background:#eef2ff;color:#4338ca;border-radius:5px;cursor:grab;padding:0}
        .flt-grip:hover{background:#e0e7ff}
        .flt-bar{position:absolute;z-index:42;display:flex;gap:3px;background:#312e81;border-radius:7px;padding:3px 5px;white-space:nowrap}
        .flt-bar button{border:0;background:transparent;color:#fff;font-size:11.5px;border-radius:4px;padding:2px 8px;cursor:pointer}
        .flt-bar button:hover{background:#4338ca}
        .row-rz{position:fixed;height:5px;z-index:121;cursor:row-resize;background:transparent}
        .row-rz:hover{background:rgba(15,118,110,.4)}
        .col-rz:hover{background:rgba(15,118,110,.45)}
        .tbl-bar button{border:0;background:transparent;color:#fff;height:24px;min-width:26px;padding:0 5px;border-radius:5px;cursor:pointer;font-size:12px;font-family:sans-serif;line-height:1}
        .tbl-bar button:hover{background:#115e59}
        .tbl-bar button.del:hover{background:#b91c1c}
        .az-sizer{position:absolute;visibility:hidden;white-space:pre;top:0;right:0;font:inherit;letter-spacing:inherit;pointer-events:none}
        /* ---- AI assistant — right-docked side panel (non-blocking: the letter
           stays selectable so you can gather validation snippets while it's open) ---- */
        .lai-panelwrap{position:fixed;inset:0;z-index:400;pointer-events:none;font-family:${NAZ}}
        .lai-modal{position:fixed;top:0;right:0;height:100vh;width:min(470px,96vw);background:#fff;box-shadow:-12px 0 40px rgba(15,23,42,.28);display:flex;flex-direction:column;overflow:hidden;pointer-events:auto;border-left:1px solid #e2e8f0}
        .lai-selhint{margin-top:4px;font-size:11.5px;color:#6d5bb5;line-height:1.7}
        .lai-attpick{margin-top:8px;background:#f0fdfa;border:1px solid #99f6e4;border-radius:10px;padding:9px 11px;display:flex;flex-direction:column;gap:5px}
        .lai-attrow{display:flex;align-items:center;gap:8px;font-size:12.5px;color:#134e4a;cursor:pointer}
        .lai-attrow input{accent-color:#0d9488}
        .lai-attname{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:230px;font-weight:600}
        .lai-tblprev{margin-top:7px;max-height:180px;overflow:auto;border:1px solid #e2e8f0;border-radius:8px;padding:6px;background:#fff;font-size:11px}
        .lai-tblprev table{width:100%;border-collapse:collapse}
        .lai-tblprev td,.lai-tblprev th{border:0.6px solid #94a3b8;padding:2px 5px;vertical-align:top}
        .lai-tblprev th{background:#f1f5f9;font-weight:700}
        .lai-chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
        .lai-chip{display:inline-flex;align-items:center;gap:4px;background:#fff;border:1px solid #c7d2fe;border-radius:20px;padding:2px 4px 2px 9px;font-size:11.5px;color:#3730a3;max-width:100%}
        .lai-chiptext{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:300px}
        .lai-chipx{border:0;background:#eef2ff;color:#4338ca;border-radius:50%;width:16px;height:16px;line-height:14px;cursor:pointer;flex:0 0 auto;font-size:13px}
        .lai-chipx:hover{background:#c7d2fe}
        .lai-head{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #e2e8f0;background:#faf5ff}
        .lai-sub{font-size:11px;color:#7c3aed;background:#f3e8ff;padding:1px 7px;border-radius:20px}
        .lai-x{border:0;background:transparent;cursor:pointer;color:#64748b;padding:4px;border-radius:6px}
        .lai-x:hover{background:#e2e8f0}
        .lai-body{padding:14px 16px;overflow:auto;flex:1 1 auto;min-height:0}
        .lai-setup{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px}
        .lai-row{display:flex;flex-direction:column;gap:4px}
        .lai-lbl{font-size:12px;font-weight:700;color:#334155}
        .lai-inp{width:100%;border:1px solid #cbd5e1;border-radius:8px;padding:7px 9px;font-size:13px;background:#fff;color:#0f172a;font-family:inherit}
        .lai-inp:focus{outline:none;border-color:#7c3aed}
        .lai-warn{margin-top:8px;font-size:12px;color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:7px 9px}
        .lai-tools{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-top:6px}
        .lai-tool{display:flex;align-items:center;gap:7px;font-size:12.5px;color:#334155;border:1px solid #e2e8f0;border-radius:8px;padding:6px 9px;cursor:pointer;background:#fff}
        .lai-tool.on{border-color:#7c3aed;background:#faf5ff;color:#5b21b6;font-weight:600}
        .lai-tool input{accent-color:#7c3aed}
        .lai-selbox{margin-top:8px;font-size:12px;background:#eef2ff;border:1px solid #c7d2fe;border-radius:8px;padding:7px 9px;color:#3730a3}
        .lai-seltext{display:block;margin-top:3px;color:#475569;max-height:54px;overflow:auto}
        .lai-run{display:inline-flex;align-items:center;gap:6px;background:linear-gradient(90deg,#7c3aed,#4f46e5);color:#fff;border:0;border-radius:8px;padding:9px 16px;font-weight:700;cursor:pointer;font-size:13px}
        .lai-run:disabled{opacity:.6;cursor:default}
        .lai-hint{font-size:11.5px;color:#64748b}
        .lai-err{margin-top:12px;font-size:13px;color:#b91c1c;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 12px}
        .lai-results{margin-top:12px}
        .lai-resbar{display:flex;align-items:center;gap:10px;font-size:12.5px;font-weight:700;color:#334155;margin-bottom:8px}
        .lai-mini{border:1px solid #cbd5e1;background:#fff;border-radius:6px;padding:3px 8px;font-size:11.5px;cursor:pointer;color:#475569}
        .lai-mini:hover{background:#f1f5f9}
        .lai-list{display:flex;flex-direction:column;gap:8px}
        .lai-item{border:1px solid #e2e8f0;border-radius:10px;padding:9px 11px;background:#fff}
        .lai-item.note{background:#f8fafc;border-style:dashed}
        .lai-itemhead{display:flex;align-items:center;gap:8px}
        .lai-itemhead input{accent-color:#7c3aed;width:16px;height:16px;flex:0 0 auto}
        .lai-noteicon{width:16px;text-align:center;color:#0ea5e9;font-weight:800;flex:0 0 auto}
        .lai-cat{font-size:10.5px;background:#ede9fe;color:#5b21b6;border-radius:20px;padding:1px 8px;white-space:nowrap;font-weight:700}
        .lai-sev{font-size:10px;color:#fff;border-radius:20px;padding:1px 7px;white-space:nowrap}
        .lai-title{font-size:13px;font-weight:700;color:#0f172a}
        .lai-detail{font-size:12px;color:#475569;margin-top:5px;line-height:1.6}
        .lai-item.dbw{border-color:#a7f3d0;background:#f0fdf9}
        .lai-dbbadge{font-size:10px;background:#0d9488;color:#fff;border-radius:20px;padding:1px 7px;white-space:nowrap}
        .lai-dbtarget{font-size:12px;color:#0f766e;margin-top:5px}
        .lai-newprof{color:#b45309;background:#fffbeb;border:1px solid #fde68a;border-radius:20px;padding:0 6px;font-size:11px;margin-inline-start:6px}
        .lai-key{background:#e2e8f0;color:#334155;border-radius:6px;padding:2px 7px;font-size:11.5px;font-family:monospace}
        .lai-diff{display:flex;align-items:center;gap:8px;margin-top:7px;flex-wrap:wrap;font-size:12.5px}
        .lai-before{background:#fef2f2;color:#991b1b;border:1px solid #fecaca;border-radius:6px;padding:2px 7px;text-decoration:line-through;max-width:100%;overflow-wrap:anywhere}
        .lai-after{background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:6px;padding:2px 7px;max-width:100%;overflow-wrap:anywhere}
        .lai-arrow{color:#94a3b8}
        .lai-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;border-top:1px solid #e2e8f0;background:#f8fafc}
        .lai-cancel{border:1px solid #cbd5e1;background:#fff;color:#475569;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer}
        .lai-apply{display:inline-flex;align-items:center;gap:6px;background:#16a34a;color:#fff;border:0;border-radius:8px;padding:9px 18px;font-weight:700;cursor:pointer;font-size:13px}
        .lai-apply:disabled{opacity:.5;cursor:default}
        .sep-line{width:100%;border-top:1px dashed #000}
        /* ---- attachment-table pages (جدول‌های پیوست) ---- */
        .att-ttl{display:flex;align-items:center;justify-content:center;gap:10px;text-align:center;min-height:34px}
        .att-badge{font-size:10pt;background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe;border-radius:16px;padding:1px 10px;font-family:${NAZ};font-weight:600;white-space:nowrap}
        .att-del{border:1px solid #fecaca;background:#fff;color:#dc2626;cursor:pointer;font-size:11px;border-radius:6px;padding:1px 8px;opacity:.75}
        .att-del:hover{opacity:1;background:#fef2f2}
        .att-warn{position:absolute;top:6px;left:10px;background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;border-radius:8px;padding:3px 9px;font-size:11px;z-index:5}
        /* ---- new-table dialog ---- */
        .tdlg-wrap{position:fixed;inset:0;z-index:420;background:rgba(15,23,42,.35);display:flex;align-items:center;justify-content:center;font-family:${NAZ}}
        .tdlg{background:#fff;border-radius:14px;box-shadow:0 18px 50px rgba(15,23,42,.35);padding:16px 18px;width:min(360px,92vw);display:flex;flex-direction:column;gap:10px}
        .tdlg h5{font-size:15px;font-weight:800;color:#0f172a;margin:0}
        .tdlg .trow2{display:flex;gap:8px}
        .tdlg label{font-size:12px;color:#334155;display:flex;flex-direction:column;gap:3px;flex:1}
        .tdlg input[type=number],.tdlg input[type=text]{border:1px solid #cbd5e1;border-radius:8px;padding:6px 9px;font-size:13px;width:100%;box-sizing:border-box}
        .tdlg .tchk{flex-direction:row;align-items:center;gap:7px;font-size:12.5px;background:#f0fdfa;border:1px solid #99f6e4;border-radius:9px;padding:8px 10px;cursor:pointer;color:#134e4a}
        .tdlg .tchk input{accent-color:#0d9488}
        .tdlg .tbtns{display:flex;justify-content:flex-start;gap:8px;margin-top:2px}
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
          .print-wrap{display:block!important;padding:0!important;margin:0!important}
          /* drop the on-screen bottom padding — sheet + 20px padding pushed past A4 onto a
             blank extra page */
          .canvas-wrap{overflow:visible;padding:0!important;margin:0!important}
          /* keep each sheet strictly UNDER A4 height (1123px≈297.1mm overflowed); clip any
             sub-pixel overflow so one sheet = exactly one printed page */
          .psheet{box-shadow:none;margin:0!important;height:296mm;overflow:hidden;break-after:page;page-break-after:always}
          .psheet:last-child{break-after:auto;page-break-after:auto}
          /* attachment-table pages that flipped to LANDSCAPE print on their own named
             page (A4 landscape) — content stays unrotated, nothing overflows the edges */
          @page attland { size: A4 landscape; margin: 0 }
          .psheet.land{page:attland;width:296mm;height:209mm}
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
          <span style={{ position: 'relative', display: 'inline-block' }}>
            <button onClick={() => setDlMenu((v) => !v)} disabled={pdfBusy} className="ltr-btn" style={{ background: '#9a3412', opacity: pdfBusy ? 0.6 : 1 }}
              title="دانلودِ نامه — دقیقاً با همان ظاهر، صفحه‌بندی و سربرگ؛ فرمت را انتخاب کن"><Download size={15} /> {pdfBusy ? '⏳ در حالِ ساخت…' : 'دانلود ▾'}</button>
            {dlMenu && !pdfBusy && (
              <div className="dl-menu" dir="rtl">
                <button onClick={downloadPdf}>PDF — چاپیِ دقیق</button>
                <button onClick={downloadWord}>Word (.docx) — قابلِ ویرایش</button>
              </div>
            )}
          </span>
          <button onClick={insertTable} className="ltr-btn gray" title="افزودنِ جدولِ نو (بعد کلیک داخلِ متن)"><Table size={14} /> جدول</button>
          <button onClick={insertImageClick} className="ltr-btn gray" title="درجِ تصویر در محلِ نشانگر — بعد از درج با کلیک روی تصویر: اندازه، کراپ، جابه‌جایی و «پشتِ متن»"><ImageIcon size={14} /> تصویر</button>
          <input ref={imgFileRef} type="file" accept="image/*" style={{ display: 'none' }}
            onChange={(e) => { onImageFile(e.target.files?.[0]); e.currentTarget.value = '' }} />
          <button onClick={openAi} className="ltr-btn" style={{ background: 'linear-gradient(90deg,#7c3aed,#4f46e5)' }} title="بازبینی و اصلاحِ هوشمندِ نامه با هوش مصنوعی — پیش از اعمال، فهرست را می‌بینی و تیک می‌زنی"><Sparkles size={15} /> دستیارِ هوشمند</button>
          {hasAttachmentMode && (
            <button onClick={() => setAttsOpen((v) => !v)} className="ltr-btn" style={{ background: '#0d9488' }}
              title="بارگذاری پیوست‌های نامه — در Drive با نامِ قابل‌ردیابی ذخیره و ذیلِ پروفایلِ مشتری ثبت می‌شود">
              📎 پیوست‌ها{(letterAtts.length + attTables.length) ? ` (${fa(letterAtts.length + attTables.length)})` : ''}
            </button>
          )}
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={14} /> پاک‌کردن</button>
          <span className="ltr-hint">{`متن را بنویس؛ هر صفحه که پر شود، خودکار صفحهٔ جدید ساخته می‌شود (الان ${fa(totalPageCount)} صفحه). «چیدمان» = جابه‌جایی/تنظیمِ فیلدها (با دبل‌کلیک: چینش/جهت/تورفتگی).`}</span>
          <span className="ltr-hint" style={{ fontWeight: 700, color: '#16a34a', direction: 'ltr' }} title="نسخهٔ کد — برای تأییدِ استقرار">build: reflow-v68</span>
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

        {/* ---- Letter attachments panel (پیوست‌ها) — only when پیوست=دارد ---- */}
        {hasAttachmentMode && attsOpen && (
          <div className="ltr-controls no-print" style={{ marginTop: -4, borderColor: '#99f6e4', background: '#f0fdfa', display: 'block' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span className="ltr-hint" style={{ fontWeight: 700, color: '#0f766e' }}>پیوست‌های نامه</span>
              <label className="ltr-btn" style={{ background: '#0d9488', cursor: 'pointer' }}>
                {attUploading ? '⏳ در حال بارگذاری…' : '⬆ افزودن پیوست'}
                <input type="file" className="hidden" style={{ display: 'none' }} disabled={attUploading}
                  onChange={(e) => { uploadAtt(e.target.files?.[0]); e.currentTarget.value = '' }} />
              </label>
              <button className="ltr-btn" style={{ background: 'linear-gradient(90deg,#7c3aed,#4f46e5)' }} onClick={toggleGen}
                title="هوش مصنوعی بر اساس دستور تو و داده‌های پایگاه‌داده یک فایل واقعی (اکسل یا ورد) می‌سازد و پیوستِ نامه می‌کند">
                <Sparkles size={14} /> ساختِ پیوست با هوش مصنوعی
              </button>
              {!letterId && <span className="ltr-hint" style={{ color: '#b45309' }}>اول نامه را «ذخیره» کن تا پیوست به آن گره بخورد.</span>}
              <span className="ltr-hint">فایل در Google Drive (پوشهٔ مشتری، نامِ قابل‌ردیابی) ذخیره و ذیلِ پروفایلِ مشتری هم ثبت می‌شود؛ در نبودِ Drive روی آرشیو دیسک.</span>
            </div>
            {/* ---- AI attachment generator (ساختِ پیوست) ---- */}
            {genOpen && (
              <div style={{ marginTop: 8, background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: 8, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                <span className="ltr-hint" style={{ fontWeight: 700, color: '#6d28d9' }}>
                  چه پیوستی ساخته شود؟ (مثلاً: «جدولِ تسهیلاتِ این مشتری با ستون‌های قرارداد، مبلغ و وضعیت»، «لیستِ املاکِ رهنیِ شعبهٔ X با وضعیتِ بیمه‌نامه و مدیرِ حساب» یا «توضیحی دربارهٔ وضعیتِ وثایق بنویس»)
                </span>
                <textarea className="meta-in" rows={2} value={genInstruction} disabled={genBusy}
                  onChange={(e) => setGenInstruction(e.target.value)} style={{ width: '100%', resize: 'vertical', font: 'inherit' }}
                  placeholder={genTpl ? 'شرحِ اضافه (اختیاری — قالبِ انتخاب‌شده مبناست)…' : 'شرحِ دقیقِ جدول یا متنِ درخواستی…'} />
                {/* v63: optional TEMPLATE/SAMPLE file — e.g. the blank table another
                    department sent; the output reproduces ITS exact format from DB data */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <label className="ltr-btn" style={{ background: genTpl ? '#0d9488' : '#64748b', cursor: genBusy ? 'default' : 'pointer' }}>
                    📄 {genTpl ? 'قالب: انتخاب شد' : 'قالب/نمونه (اختیاری)'}
                    <input type="file" style={{ display: 'none' }} disabled={genBusy}
                      accept=".xlsx,.xlsm,.xls,.csv,.docx,.pdf,.png,.jpg,.jpeg,.txt"
                      onChange={(e) => { const ff = e.target.files?.[0] || null; setGenTpl(ff); e.target.value = '' }} />
                  </label>
                  {genTpl && <>
                    <span className="ltr-hint" style={{ fontWeight: 700, color: '#0f766e' }} dir="ltr">{genTpl.name}</span>
                    <button type="button" className="ltr-hint" style={{ border: 0, background: 'transparent', color: '#dc2626', cursor: 'pointer' }}
                      onClick={() => setGenTpl(null)} disabled={genBusy}>✕ حذفِ قالب</button>
                  </>}
                  {/* v65: SOURCE/DATA files — any count, any format, appendable any time */}
                  <label className="ltr-btn" style={{ background: genSrcs.length ? '#b45309' : '#64748b', cursor: genBusy ? 'default' : 'pointer' }}>
                    🗂 {genSrcs.length ? `فایل‌های منبع (${fa(genSrcs.length)})` : 'فایل‌های منبعِ داده (اختیاری)'}
                    <input type="file" multiple style={{ display: 'none' }} disabled={genBusy}
                      accept=".xlsx,.xlsm,.xls,.csv,.docx,.pdf,.png,.jpg,.jpeg,.txt"
                      onChange={(e) => {
                        const picked = Array.from(e.target.files || [])
                        if (picked.length) setGenSrcs((s) => {
                          // append, never replace — the user adds files over several picks
                          const have = new Set(s.map((x) => `${x.name}|${x.size}`))
                          return [...s, ...picked.filter((x) => !have.has(`${x.name}|${x.size}`))]
                        })
                        e.target.value = ''
                      }} />
                  </label>
                  <span className="ltr-hint">
                    اگر اداره/مرجعی فایلِ نمونه (جدولِ خالی با ستون‌های مشخص و…) داده، «قالب» بده — خروجی دقیقاً به همان شکل پر می‌شود. «فایل‌های منبع» هم داده‌های خام‌اند (هر فرمت و هر تعداد): پیوست از محتوای آن‌ها + پایگاه‌داده و طبقِ شرحِ باکس ساخته می‌شود؛ اگر قالب هم باشد، داده‌ها دقیقاً در همان قالب می‌نشینند.
                  </span>
                </div>
                {genSrcs.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    {genSrcs.map((sf, i) => (
                      <span key={`${sf.name}-${i}`} className="ltr-hint" style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 6, padding: '2px 8px', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                        <span dir="ltr" style={{ fontWeight: 700, color: '#92400e' }}>{sf.name}</span>
                        <button type="button" style={{ border: 0, background: 'transparent', color: '#dc2626', cursor: 'pointer' }} disabled={genBusy}
                          onClick={() => setGenSrcs((s) => s.filter((_, j) => j !== i))} title="حذفِ این فایلِ منبع">✕</button>
                      </span>
                    ))}
                    <button type="button" className="ltr-hint" style={{ border: 0, background: 'transparent', color: '#dc2626', cursor: 'pointer' }}
                      onClick={() => setGenSrcs([])} disabled={genBusy}>پاک‌کردنِ همه</button>
                  </div>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <label className="ltr-hint">قالب:</label>
                  <select className="meta-in" style={{ width: 150 }} value={genKind} disabled={genBusy}
                    onChange={(e) => setGenKind(e.target.value as '' | 'excel' | 'word')}>
                    <option value="">خودکار (بسته به دستور)</option>
                    <option value="excel">اکسل (xlsx)</option>
                    <option value="word">ورد (docx)</option>
                  </select>
                  <label className="ltr-hint">مدل:</label>
                  <select className="meta-in" style={{ width: 210 }} value={aiModelId} disabled={genBusy}
                    onChange={(e) => setAiModelId(e.target.value === '' ? '' : Number(e.target.value))}>
                    <option value="">خودکار (بهترین مدلِ فعال)</option>
                    {aiModels.map((mm) => <option key={mm.id} value={mm.id}>{mm.display_name} — {mm.provider_name}</option>)}
                  </select>
                  <button className="ltr-btn" style={{ background: '#7c3aed' }} onClick={generateAtt} disabled={genBusy || !letterId}>
                    {genBusy ? '⏳ در حالِ ساخت… (ممکن است تا چند دقیقه طول بکشد)' : '🪄 بساز و پیوست کن'}
                  </button>
                  {(general || !acct.trim())
                    ? <span className="ltr-hint">نامهٔ عمومی — دادهٔ تک‌مشتری ندارد، ولی فهرست‌های سراسری (مثلاً املاک/تسهیلاتِ یک شعبه یا همهٔ مشتریان) از پایگاه‌داده خوانده می‌شود.</span>
                    : <span className="ltr-hint">داده‌ها از پروندهٔ حسابِ {acct.trim()} (و در صورتِ نیاز فهرست‌های سراسری/شعبه‌ای) خوانده می‌شود؛ چیزی اختراع نمی‌شود.</span>}
                </div>
                {genWarnings.length > 0 && (
                  <div style={{ fontSize: 11.5, color: '#92400e', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 6, padding: '4px 8px' }}>
                    {genWarnings.map((w, i) => <div key={i}>⚠ {w}</div>)}
                  </div>
                )}
                <span className="ltr-hint" style={{ color: '#7c3aed' }}>
                  پیوست‌های ساختهٔ AI چون داده‌شان از خودِ پایگاه‌داده آمده، در ابزارِ «استخراج از پیوست‌ها» به‌صورت پیش‌فرض تیک نمی‌خورند (برای جلوگیری از ثبتِ دوباره) — ولی می‌توانی دستی تیکشان بزنی.
                </span>
              </div>
            )}
            {(letterAtts.length > 0 || attTables.length > 0) && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {letterAtts.map((a) => (
                  <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, background: '#fff', border: '1px solid #ccfbf1', borderRadius: 8, padding: '5px 9px' }}>
                    <span>📄</span>
                    <b>{a.original_name}</b>
                    {a.ai_generated && <span title="این فایل را هوش مصنوعی از روی داده‌های پایگاه‌داده ساخته است"
                      style={{ fontSize: 10.5, fontWeight: 700, color: '#6d28d9', background: '#f3e8ff', border: '1px solid #e9d5ff', borderRadius: 999, padding: '1px 8px', whiteSpace: 'nowrap' }}>🪄 ساختِ AI</span>}
                    <span className="ltr-hint">{a.storage === 'drive' ? 'Drive' : 'دیسک'}{a.file_size ? ` · ${a.file_size} بایت` : ''}{a.upload_date ? ` · ${a.upload_date}` : ''}</span>
                    {/* authed fetch → blob (a plain <a href> would drop the JWT → 401 in production) */}
                    <button onClick={() => viewAtt(a.id)} title="بازکردن در تبِ جدید — PDF/تصویر همان‌جا دیده و پرینت می‌شود"
                      style={{ border: 0, background: 'transparent', color: '#0d9488', cursor: 'pointer', marginInlineStart: 'auto' }}>مشاهده</button>
                    <button onClick={() => downloadFile(`/api/crm/attachments/${a.id}/download`, a.original_name).catch((e) => toast.error(parseApiError(e)))}
                      style={{ border: 0, background: 'transparent', color: '#0d9488', cursor: 'pointer' }}>دانلود</button>
                    <button onClick={() => deleteAtt(a.id, a.original_name)} style={{ border: 0, background: 'transparent', color: '#dc2626', cursor: 'pointer' }}>حذف</button>
                  </div>
                ))}
                {/* attachment TABLES — rendered as pages after the letter (not files) */}
                {attTables.map((t, i) => (
                  <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, background: '#fff', border: '1px solid #fde68a', borderRadius: 8, padding: '5px 9px' }}>
                    <span>▦</span>
                    <b>جدول {fa(i + 1)} پیوست{plain(t.title) ? ` — ${plain(t.title)}` : ''}</b>
                    <span className="ltr-hint">صفحهٔ {fa(pages.length + i + 1)}{attMeta[t.id]?.land ? ' · افقی (landscape)' : ''}</span>
                    <button onClick={() => { if (confirm(`حذفِ جدول ${fa(i + 1)} پیوست؟`)) removeAttTable(t.id) }}
                      style={{ border: 0, background: 'transparent', color: '#dc2626', cursor: 'pointer', marginInlineStart: 'auto' }}>حذف</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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
            <span className="sep2" />
            <button title="کاهشِ فاصلهٔ خطوط" onMouseDown={(e) => { e.preventDefault(); lineSpaceSel(-0.1) }}>خ−</button>
            <button title="افزایشِ فاصلهٔ خطوط" onMouseDown={(e) => { e.preventDefault(); lineSpaceSel(0.1) }}>خ＋</button>
            <span className="sep2" />
            {/* preventDefault keeps the selection alive so addAiSelection can read it */}
            <button title="افزودنِ این انتخاب به فهرستِ اعتبارسنجیِ هوش مصنوعی" style={{ color: '#c4b5fd' }}
              onMouseDown={(e) => { e.preventDefault(); addAiSelection() }}><Sparkles size={13} /></button>
          </div>
        )}

        {tbl && (
          <div className="tbl-bar no-print" style={{ left: tbl.x, top: tbl.y }} onMouseDown={(e) => e.preventDefault()}>
            <button title="جابه‌جاییِ جدول در متن — بگیر و بکش، بینِ بندها رها کن" style={{ cursor: 'grab', fontSize: 14 }} onPointerDown={startTableDrag}>⠿</button>
            <button title="پشتِ متن (مثل Word): جدول از جریانِ متن جدا و آزادانه روی صفحه، زیرِ متن‌ها و فیلدها، جابه‌جا می‌شود" onClick={floatCurrentTable}>پشتِ متن</button>
            <span className="sep2" />
            <button title="توپُر" style={{ fontWeight: 700 }} onClick={() => document.execCommand('bold')}>B</button>
            <button title="کج" style={{ fontStyle: 'italic' }} onClick={() => document.execCommand('italic')}>I</button>
            <button title="زیرخط" style={{ textDecoration: 'underline' }} onClick={() => document.execCommand('underline')}>U</button>
            <button title="کوچک‌تر" onClick={() => bumpSel(0.85)}>A−</button>
            <button title="بزرگ‌تر" onClick={() => bumpSel(1.18)}>A＋</button>
            <span className="sep2" />
            <button title="تراز عمودی: بالا" onClick={() => tableOp('valTop')}>⤒</button>
            <button title="تراز عمودی: وسط" onClick={() => tableOp('valMiddle')}>⇳</button>
            <button title="تراز عمودی: پایین" onClick={() => tableOp('valBottom')}>⤓</button>
            <span className="sep2" />
            <button title="راست‌چینِ متنِ خانه‌های انتخاب‌شده" onClick={() => tableOp('alignRight')}>≡▸</button>
            <button title="وسط‌چینِ متنِ خانه‌های انتخاب‌شده" onClick={() => tableOp('alignCenter')}>≡▾</button>
            <button title="چپ‌چینِ متنِ خانه‌های انتخاب‌شده" onClick={() => tableOp('alignLeft')}>◂≡</button>
            <span className="sep2" />
            <button title="افزودنِ ردیف بالا" onClick={() => tableOp('rowAbove')}>▤↑</button>
            <button title="افزودنِ ردیف پایین" onClick={() => tableOp('rowBelow')}>▤↓</button>
            <button title="حذفِ ردیف‌های انتخاب‌شده" className="del" onClick={() => tableOp('delRow')}>▤✕</button>
            <span className="sep2" />
            <button title="افزودنِ ستون (راست)" onClick={() => tableOp('colRight')}>▥←</button>
            <button title="افزودنِ ستون (چپ)" onClick={() => tableOp('colLeft')}>▥→</button>
            <button title="حذفِ ستون‌های انتخاب‌شده" className="del" onClick={() => tableOp('delCol')}>▥✕</button>
            <span className="sep2" />
            <button title="ادغامِ خانه‌های انتخاب‌شده (Merge)" onClick={() => tableOp('mergeCells')}>⧉</button>
            <button title="حذفِ کلِ جدول" className="del" onClick={() => tableOp('delTable')}>🗑</button>
          </div>
        )}

        {/* draggable gridlines to resize table columns (shown while the caret is in a table) */}
        {dropInd && <div className="drop-ind no-print" style={{ left: dropInd.x, top: dropInd.y - 2, width: dropInd.w }} />}
        {colRz && !design && colRz.bounds.map((b) => (
          <div key={b.i} className="col-rz no-print" style={{ left: b.x - 3, top: colRz.top, height: colRz.height }}
            title={b.i < 0 ? 'کشیدن برای کوچک/بزرگ‌کردنِ کلِ جدول (از هر دو لبه)' : 'کشیدن برای تغییرِ عرضِ ستون'} onPointerDown={(e) => startColResize(e, b.i)} />
        ))}
        {/* thin strip above the table: drag LEFT/RIGHT to move a shrunk table horizontally */}
        {colRz && !design && (
          <div className="tbl-hmove no-print" style={{ left: colRz.left, top: colRz.top - 7, width: colRz.width }}
            title="کشیدن به چپ/راست برای جابه‌جاییِ افقیِ جدول (وقتی جدول کوچک‌تر از عرضِ صفحه است)" onPointerDown={startTableHMove} />
        )}
        {/* ---- image toolbar + 8 resize/crop handles (shown when an image is selected) ---- */}
        {imgRz && !design && (
          <div className="img-bar no-print" dir="rtl" style={{ left: imgRz.x + imgRz.w / 2, top: imgRz.y }} onMouseDown={(e) => e.preventDefault()}>
            <button title="جابه‌جاییِ تصویر در متن — بگیر و بینِ بندها رها کن" style={{ cursor: 'grab' }} onPointerDown={startImgMove}>⠿</button>
            <span className="sep2" />
            <button className={imgCropMode ? 'on' : ''} title="حالتِ کراپ: لبه‌ها پنجرهٔ برش را جابه‌جا می‌کنند" onClick={() => setImgCropMode((v) => !v)}>✂ کراپ</button>
            <button title="بازنشانیِ کراپ (نمایشِ کاملِ تصویر)" onClick={resetImgCrop}>↺</button>
            <span className="sep2" />
            <button title="راست‌چین" onClick={() => alignImg('right')}>≡▸</button>
            <button title="وسط‌چین" onClick={() => alignImg('center')}>≡▾</button>
            <button title="چپ‌چین" onClick={() => alignImg('left')}>◂≡</button>
            <span className="sep2" />
            <button title="پشتِ متن (مثل Word): تصویر آزادانه روی صفحه، زیرِ متن‌ها" onClick={floatCurrentImg}>پشتِ متن</button>
            <span className="sep2" />
            <button className="del" title="حذفِ تصویر" onClick={deleteImg}>حذف</button>
          </div>
        )}
        {imgRz && !design && (['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'] as const).map((d) => {
          const cx = d.includes('w') ? imgRz.x : d.includes('e') ? imgRz.x + imgRz.w : imgRz.x + imgRz.w / 2
          const cy = d.includes('n') ? imgRz.y : d.includes('s') ? imgRz.y + imgRz.h : imgRz.y + imgRz.h / 2
          const cur = d === 'n' || d === 's' ? 'ns-resize' : d === 'e' || d === 'w' ? 'ew-resize' : (d === 'ne' || d === 'sw') ? 'nesw-resize' : 'nwse-resize'
          return <div key={d} className={`img-hd no-print${imgCropMode ? ' crop' : ''}`} style={{ left: cx - 5, top: cy - 5, cursor: cur }} onPointerDown={(e) => startImgHandle(e, d)} />
        })}
        {imgRz && !design && <div className="img-outline no-print" style={{ left: imgRz.x, top: imgRz.y, width: imgRz.w, height: imgRz.h }} />}

        {/* horizontal strips at each row boundary (+ table top): drag to change ROW heights */}
        {colRz && !design && colRz.rowBounds.map((rb, k) => (
          <div key={`r${k}`} className="row-rz no-print" style={{ left: colRz.left, top: rb.y - 2, width: colRz.width }}
            title="کشیدن برای کم/زیادکردنِ ارتفاعِ ردیف" onPointerDown={(e) => startRowResize(e, rb.uid, rb.topEdge)} />
        ))}

        {/* hidden measurers — body height/pagination and subject width (for the separator) */}
        <div ref={measureRef} aria-hidden className="measure" style={{ width: L.body.w, fontFamily: L.body.font, fontSize: `${L.body.size}pt`, lineHeight: L.body.lh || 1.7, letterSpacing: L.body.ls ? `${L.body.ls}px` : undefined, whiteSpace: 'pre-wrap' }} />
        <span ref={subjRef} aria-hidden className="measure" style={{ whiteSpace: 'nowrap', fontFamily: L.subject.font, fontSize: `${L.subject.size}pt` }} />

        {/* ---- EDITABLE PAGINATED VIEW (screen) — attachment-table pages follow
             the letter's last (closing) page, in order ---- */}
        <div id="ltr-edit" className="canvas-wrap" onDoubleClick={exitEditing}>
          {pages.map((_, pi) => editorPage(pi))}
          {attTables.map((t, i) => attEditorPage(t, i))}
        </div>

        {/* ---- PRINT VIEW (read-only values) ---- */}
        <div className="canvas-wrap print-wrap">
          {pages.map((_, pi) => printPage(pi))}
          {attTables.map((t, i) => attPrintPage(t, i))}
        </div>

        {/* ---- NEW-TABLE DIALOG: rows/columns + optional title + «به‌عنوانِ پیوست» ---- */}
        {tblDlg && (
          <div className="tdlg-wrap no-print" dir="rtl" onClick={() => setTblDlg(null)}>
            <div className="tdlg" onClick={(e) => e.stopPropagation()}>
              <h5>جدولِ جدید</h5>
              <div className="trow2">
                <label>تعدادِ ردیف
                  <input type="number" min={1} max={200} value={tblDlg.rows} autoFocus
                    onChange={(e) => setTblDlg((d) => d && { ...d, rows: e.target.value })} />
                </label>
                <label>تعدادِ ستون
                  <input type="number" min={1} max={30} value={tblDlg.cols}
                    onChange={(e) => setTblDlg((d) => d && { ...d, cols: e.target.value })} />
                </label>
              </div>
              <label>عنوانِ جدول (اختیاری — بالای جدول، قابلِ ویرایش)
                <input type="text" value={tblDlg.title} placeholder="مثلاً: جدولِ اقساطِ تسهیلات"
                  onChange={(e) => setTblDlg((d) => d && { ...d, title: e.target.value })} />
              </label>
              <label className="tchk">
                <input type="checkbox" checked={tblDlg.asAtt} onChange={(e) => setTblDlg((d) => d && { ...d, asAtt: e.target.checked })} />
                <span>ثبت به‌عنوانِ <b>پیوستِ نامه</b> — جدول صفحهٔ جداگانه‌ای بعد از صفحهٔ آخرِ نامه می‌گیرد؛ اگر عریض باشد صفحه خودکار افقی (landscape) می‌شود</span>
              </label>
              <div className="tbtns">
                <button className="ltr-btn green" onClick={confirmInsertTable}><Table size={14} /> ساختِ جدول</button>
                <button className="ltr-btn gray" onClick={() => setTblDlg(null)}>انصراف</button>
              </div>
            </div>
          </div>
        )}

        {/* ---- AI ASSISTANT MODAL («دستیار هوشمند») ---- */}
        {aiOpen && (
          // A non-blocking wrapper: pointer-events pass THROUGH to the letter (so you
          // can still select text while the panel is open); only the panel captures.
          <div className="lai-panelwrap no-print" dir="rtl">
            <div className="lai-modal" dir="rtl">
              <div className="lai-head">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Sparkles size={18} color="#7c3aed" />
                  <b>دستیارِ هوشمندِ نامه</b>
                  <span className="lai-sub">پیشنهاد می‌دهد؛ پیش از اعمال، خودت تیک می‌زنی</span>
                </div>
                <button className="lai-x" onClick={() => setAiOpen(false)}><X size={18} /></button>
              </div>

              <div className="lai-body">
                {/* ---- setup panel ---- */}
                <div className="lai-setup">
                  <div className="lai-row">
                    <label className="lai-lbl">مدلِ هوش مصنوعی</label>
                    <select className="lai-inp" value={aiModelId} onChange={(e) => setAiModelId(e.target.value === '' ? '' : Number(e.target.value))}>
                      <option value="">خودکار (بهترین مدلِ فعال بر اساس اولویت)</option>
                      {aiModels.map((m) => <option key={m.id} value={m.id}>{m.display_name} — {m.provider_name}</option>)}
                    </select>
                  </div>
                  {aiModelsLoaded && aiModels.length === 0 && (
                    <div className="lai-warn">هیچ مدلِ فعالی یافت نشد. از «تنظیمات ← مدل‌های هوش مصنوعی» یک مدل را فعال کن؛ فعلاً می‌توانی روی حالتِ خودکار اجرا کنی ولی احتمالاً خطا می‌دهد.</div>
                  )}

                  <label className="lai-lbl" style={{ marginTop: 8 }}>ابزارها (چه کارهایی انجام شود)</label>
                  <div className="lai-tools">
                    {(aiTools.length ? aiTools : DEFAULT_TOOLS.map((id) => ({ id, label: id }))).map((t) => (
                      <label key={t.id} className={`lai-tool${aiSelTools.includes(t.id) ? ' on' : ''}`}>
                        <input type="checkbox" checked={aiSelTools.includes(t.id)} onChange={() => toggleTool(t.id)} />
                        <span>{t.label}</span>
                      </label>
                    ))}
                    {/* Deep attachment extraction — only offered when the letter actually has enclosures */}
                    {hasAttachmentMode && letterAtts.length > 0 && (
                      <label className={`lai-tool${aiSelTools.includes(ATT_TOOL) ? ' on' : ''}`} style={{ borderColor: '#5eead4' }}
                        title="مانند صفحهٔ Import: همهٔ داده‌های مرتبط با موضوع نامه و همهٔ حساب‌های نام‌برده، کامل و بدون خلاصه‌سازی، استخراج و پس از تیکِ شما ثبت می‌شود">
                        <input type="checkbox" checked={aiSelTools.includes(ATT_TOOL)} onChange={() => toggleTool(ATT_TOOL)} />
                        <span>استخراجِ کامل از پیوست‌ها ({fa(selectedAttCount)} از {fa(letterAtts.length)})</span>
                      </label>
                    )}
                  </div>

                  {/* Which tables the AI works on — pick exactly the ones you mean */}
                  {aiSelTools.includes('tables') && (() => { const bt = getBodyTables(); return bt.length > 0 ? (
                    <div className="lai-attpick" style={{ background: '#fefce8', borderColor: '#fde68a' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                        <span className="lai-lbl">کدام جدول‌ها بررسی/اصلاح شوند؟ ({fa(bt.filter((t) => tblSelected(t.uid)).length)} از {fa(bt.length)})</span>
                        <span style={{ display: 'flex', gap: 6 }}>
                          <button className="lai-mini" onClick={() => setAiSelTables({})}>همه</button>
                          <button className="lai-mini" onClick={() => { const off: Record<string, boolean> = {}; bt.forEach((t) => { off[t.uid] = false }); setAiSelTables(off) }}>هیچ‌کدام</button>
                        </span>
                      </div>
                      {bt.map((t) => (
                        <label key={t.uid} className="lai-attrow">
                          <input type="checkbox" checked={tblSelected(t.uid)}
                            onChange={(e) => setAiSelTables((s) => ({ ...s, [t.uid]: e.target.checked }))} />
                          <span className="lai-attname" style={{ maxWidth: 320 }}>▦ {t.label}</span>
                        </label>
                      ))}
                      <div className="lai-selhint" style={{ color: '#92400e' }}>
                        اگر در «دستورِ اختصاصی» خواسته‌ای دربارهٔ جدول بنویسی، هوش مصنوعی همان جدول(های)
                        انتخاب‌شده را همه‌جانبه (ساختار + محتوا + چیدمان) بازطراحی می‌کند؛ بدونِ دستور،
                        فقط بررسیِ پیش‌فرض (گزارشِ ناهماهنگی + اصلاحِ جزئی) انجام می‌شود.
                      </div>
                    </div>
                  ) : null })()}

                  {/* Which attachments to extract — pick exactly the ones you need */}
                  {(aiSelTools.includes(ATT_TOOL) || aiSelTools.includes('full_check') || aiSelTools.includes('db_extract')) && letterAtts.length > 0 && (
                    <div className="lai-attpick">
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                        <span className="lai-lbl">کدام پیوست‌ها استخراج شوند؟</span>
                        <span style={{ display: 'flex', gap: 6 }}>
                          <button className="lai-mini" onClick={() => { const on: Record<string, boolean> = {}; letterAtts.forEach((a) => { on[a.id] = true }); setAiSelAtts(on) }}>همه</button>
                          <button className="lai-mini" onClick={() => { const off: Record<string, boolean> = {}; letterAtts.forEach((a) => { off[a.id] = false }); setAiSelAtts(off) }}>هیچ‌کدام</button>
                        </span>
                      </div>
                      {letterAtts.map((a) => (
                        <label key={a.id} className="lai-attrow">
                          <input type="checkbox" checked={attSelected(a)}
                            onChange={(e) => setAiSelAtts((s) => ({ ...s, [a.id]: e.target.checked }))} />
                          <span className="lai-attname">📄 {a.original_name}</span>
                          {a.ai_generated && <span title="ساختهٔ هوش مصنوعی از روی داده‌های پایگاه‌داده — پیش‌فرض از استخراج کنار گذاشته می‌شود تا داده دوباره ثبت نشود"
                            style={{ fontSize: 10, fontWeight: 700, color: '#6d28d9', background: '#f3e8ff', border: '1px solid #e9d5ff', borderRadius: 999, padding: '0 7px', whiteSpace: 'nowrap' }}>🪄 ساختِ AI</span>}
                          <span className="lai-hint">{a.storage === 'drive' ? 'Drive' : 'دیسک'}{a.file_size ? ` · ${a.file_size} بایت` : ''}</span>
                        </label>
                      ))}
                      {letterAtts.some((a) => a.ai_generated) && (
                        <div className="lai-selhint" style={{ color: '#6d28d9' }}>
                          پیوست‌های «ساختِ AI» چون داده‌شان از خودِ پایگاه‌داده آمده، پیش‌فرض تیک ندارند (جلوگیری از ثبتِ دوباره)؛ در صورت نیاز دستی تیک بزن.
                        </div>
                      )}
                    </div>
                  )}

                  <div className="lai-selbox">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                      <b>موارد انتخاب‌شده برای اعتبارسنجی {aiSelections.length ? `(${fa(aiSelections.length)})` : ''}</b>
                      {aiSelections.length > 0 && <button className="lai-mini" onClick={() => setAiSelections([])}>پاک‌کردنِ همه</button>}
                    </div>
                    {aiSelections.length === 0
                      ? <div className="lai-selhint">این پنجره را باز بگذار، در متنِ نامه یک عبارت را انتخاب کن و روی <Sparkles size={11} style={{ verticalAlign: 'middle', color: '#7c3aed' }} /> در نوارِ شناور بزن تا این‌جا اضافه شود. می‌توانی چند عبارتِ جدا اضافه کنی؛ هرکدام مستقل با پایگاه‌داده اعتبارسنجی می‌شود.</div>
                      : <div className="lai-chips">
                          {aiSelections.map((s, i) => (
                            <span key={i} className="lai-chip" title={s}>
                              <span className="lai-chiptext">{s.length > 60 ? s.slice(0, 60) + '…' : s}</span>
                              <button className="lai-chipx" onClick={() => removeAiSelection(i)} title="حذف">×</button>
                            </span>
                          ))}
                        </div>}
                  </div>

                  <label className="lai-lbl" style={{ marginTop: 8 }}>دستورِ اختصاصی (اختیاری)</label>
                  <textarea className="lai-inp" rows={2} value={aiInstruction} onChange={(e) => setAiInstruction(e.target.value)}
                    placeholder="مثلاً: لحن را رسمی‌تر کن؛ مبلغ و نرخ را با پرونده تطبیق بده؛ جملهٔ آخر را کوتاه کن…" />

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 10 }}>
                    <button className="lai-run" onClick={runAi} disabled={aiLoading}>
                      {aiLoading ? (extracting2 || '⏳ در حالِ بررسی…') : <><Sparkles size={15} /> بررسیِ نامه</>}
                    </button>
                    {(general || !acct.trim())
                      ? <span className="lai-hint">نامهٔ عمومی — بدونِ حقایقِ پایگاه‌داده (اعتبارسنجیِ مالی محدود است).</span>
                      : <span className="lai-hint">حسابِ {acct.trim()} — اصلاحات با حقایقِ پایگاه‌داده تطبیق داده می‌شوند.</span>}
                  </div>
                </div>

                {/* ---- results ---- */}
                {aiError && <div className="lai-err">{aiError}</div>}

                {aiRan && !aiError && (
                  <div className="lai-results">
                    <div className="lai-resbar">
                      <span>{aiChanges.length ? `${fa(aiChanges.length)} پیشنهاد` : 'پیشنهادی نیست'}</span>
                      {aiModelUsed && <span className="lai-hint">مدل: {aiModelUsed}{aiFactsUsed ? ' · با حقایقِ پایگاه‌داده' : ''}</span>}
                      {aiChanges.length > 0 && <div style={{ marginInlineStart: 'auto', display: 'flex', gap: 6 }}>
                        <button className="lai-mini" onClick={() => { const all: Record<string, boolean> = {}; aiChanges.forEach((c) => { all[c.id] = c.applicable }); setAiChecked(all) }}>تیکِ همه</button>
                        <button className="lai-mini" onClick={() => setAiChecked({})}>برداشتنِ همه</button>
                      </div>}
                    </div>

                    <div className="lai-list">
                      {aiChanges.map((c) => (
                        <div key={c.id} className={`lai-item${c.applicable ? '' : ' note'}${c.op === 'db_write' ? ' dbw' : ''}`}>
                          <div className="lai-itemhead">
                            {c.applicable
                              ? <input type="checkbox" checked={!!aiChecked[c.id]} onChange={(e) => setAiChecked((s) => ({ ...s, [c.id]: e.target.checked }))} />
                              : <span className="lai-noteicon" title="فقط تذکر — اعمال نمی‌شود">ℹ</span>}
                            <span className="lai-cat">{CAT_FA[c.category] || c.category}</span>
                            {c.op === 'db_write' && <span className="lai-dbbadge">{c.action === 'update' ? 'به‌روزرسانی' : 'ثبتِ نو'}</span>}
                            <span className="lai-sev" style={{ background: SEV_COLOR[c.severity] || '#64748b' }}>{SEV_FA[c.severity] || c.severity}</span>
                            <span className="lai-title">{c.title}</span>
                          </div>
                          {/* db_write: show the resolved target customer + the field/value going to the DB */}
                          {c.op === 'db_write' && (
                            <div className="lai-dbtarget">→ پروفایلِ <b>{c.customer_name || '—'}</b> <span dir="ltr">({c.account_no})</span>{!c.exists && <span className="lai-newprof"> پروفایلِ جدید ساخته می‌شود</span>}{c.source_file && <span className="lai-hint"> · از {c.source_file}</span>}</div>
                          )}
                          {/* link: profile↔profile relationship with its exact reason */}
                          {c.op === 'link' && (
                            <div className="lai-dbtarget">🔗 <b>{c.customer_name || c.account_no}</b> <span dir="ltr">({c.account_no})</span> ↔ <b>{c.related_name || c.related_account}</b> <span dir="ltr">({c.related_account})</span> — در هر دو پروفایل با ذکرِ علت ثبت می‌شود</div>
                          )}
                          {/* kb_write: the EXACT content going into the Knowledge Base, under its topic */}
                          {c.op === 'kb_write' && (
                            <div className="lai-dbtarget">📚 پایگاه دانش ← موضوعِ <b>{c.topic}</b>{c.kb_category ? ` (${c.kb_category})` : ''}
                              <div style={{ marginTop: 4, whiteSpace: 'pre-wrap', color: '#334155' }}>{c.content}</div>
                              {c.source_note && <div className="lai-hint" style={{ marginTop: 2 }}>منبع: {c.source_note}</div>}
                            </div>
                          )}
                          {c.detail && <div className="lai-detail">{c.detail}</div>}
                          {c.applicable && (c.op === 'text_replace' || c.op === 'set_field') && (
                            <div className="lai-diff">
                              <span className="lai-before">{c.before || '—'}</span>
                              <span className="lai-arrow">←</span>
                              <span className="lai-after">{c.after || '—'}</span>
                            </div>
                          )}
                          {c.op === 'db_write' && (
                            <div className="lai-diff">
                              <span className="lai-key">{c.key}</span>
                              {c.action === 'update' && <><span className="lai-before">{c.before || '—'}</span><span className="lai-arrow">←</span></>}
                              <span className="lai-after">{c.value || c.after || '—'}</span>
                            </div>
                          )}
                          {/* table_replace / table_insert: live preview of the (re)designed table (server-sanitized HTML) */}
                          {(c.op === 'table_replace' || c.op === 'table_insert') && c.html && (
                            <div className="lai-tblprev" dir="rtl" dangerouslySetInnerHTML={{ __html: c.html }} />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="lai-foot">
                <button className="lai-cancel" onClick={() => setAiOpen(false)}>بستن</button>
                <button className="lai-apply" onClick={applyAiChanges} disabled={aiApplicableCount === 0}>
                  <Check size={15} /> اعمالِ {aiApplicableCount ? fa(aiApplicableCount) + ' ' : ''}موردِ انتخاب‌شده
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
