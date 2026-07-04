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
import { Printer, Eraser, Move, Check, RotateCcw, Save, FilePlus, Table, Sparkles, X } from 'lucide-react'
import { auditApi, departmentsApi, lettersApi, letterAiApi, parseApiError } from '@/lib/api'
import type { LetterAiChange, LetterAiModel, LetterAiTool } from '@/lib/api'
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
  return [isHtml ? container.innerHTML : (container.textContent || ''), applied]
}

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
      const sel = foc ? selOffsets(el) : null
      el.innerHTML = want
      if (sel) setSel(el, sel.start, sel.end)
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
  const [fmt, setFmt] = useState<{ x: number; y: number } | null>(null)        // floating bold/underline toolbar
  const [tbl, setTbl] = useState<{ x: number; y: number } | null>(null)        // floating table toolbar (caret in a cell)
  const [colRz, setColRz] = useState<{ top: number; height: number; hdrUid: string; bounds: { x: number; i: number }[] } | null>(null) // column-resize handles
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
  const DEFAULT_TOOLS = ['spelling', 'grammar', 'paragraphs', 'consistency', 'professional']
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

  const CAT_FA: Record<string, string> = { spelling: 'املایی', grammar: 'نگارشی', paragraphs: 'پاراگراف', tables: 'جدول', consistency: 'مغایرت', professional: 'حرفه‌ای‌سازی', validation: 'اعتبارسنجی', other: 'سایر' }
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

  const runAi = async () => {
    if (!aiSelTools.length) { toast.error('حداقل یک ابزار را انتخاب کن'); return }
    setAiLoading(true); setAiError(''); setAiRan(false)
    try {
      const r = await letterAiApi.analyze({
        account_no: general ? undefined : (acct.trim() || undefined),
        fields: f, tools: aiSelTools,
        instruction: aiInstruction.trim() || undefined,
        selections: aiSelections.length ? aiSelections : undefined,
        model_id: aiModelId === '' ? undefined : Number(aiModelId),
      })
      setAiRan(true)
      setAiModelUsed(r.model || ''); setAiFactsUsed(!!r.facts_used)
      if (!r.ok) { setAiError(aiErrorText(r.error)); setAiChanges([]); return }
      setAiChanges(r.changes || [])
      // pre-tick every applicable change; notes are advisory (never applied)
      const checked: Record<string, boolean> = {}
      for (const c of r.changes || []) checked[c.id] = !!c.applicable
      setAiChecked(checked)
      if (!(r.changes || []).length) toast.success('موردی برای اصلاح یافت نشد — نامه تمیز است ✓')
    } catch (e) { setAiError(parseApiError(e)); setAiRan(true) }
    finally { setAiLoading(false) }
  }
  const aiErrorText = (err?: string) => {
    if (err === 'no_model') return 'هیچ مدلِ هوش مصنوعیِ فعالی پیکربندی نشده — از «تنظیمات ← مدل‌های هوش مصنوعی» یک مدل را فعال کن.'
    if (err === 'no_base_url') return 'آدرسِ سرویس‌دهندهٔ مدل تنظیم نشده است.'
    if (err && /timed out/i.test(err)) return 'پاسخِ مدل به‌موقع نرسید؛ دوباره تلاش کن یا مدلِ سریع‌تری انتخاب کن.'
    return err ? `خطای مدل: ${err}` : 'اجرای مدل ناموفق بود.'
  }

  const applyAiChanges = () => {
    const nf: any = { ...f }
    let applied = 0, notLocated = 0
    const appliedIds: string[] = []
    for (const ch of aiChanges) {
      if (!aiChecked[ch.id] || !ch.applicable) continue
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
    if (applied) { setF(nf); toast.success(`${fa(applied)} مورد روی نامه اعمال شد — بازبینی و «ذخیره» کن`) }
    if (notLocated) toast.error(`${fa(notLocated)} مورد در متنِ فعلی پیدا نشد و رد شد`)
    if (!applied && !notLocated) { toast('موردی برای اعمال تیک نخورده است'); return }
    // drop applied rows; keep the rest so the user can iterate
    setAiChanges((cs) => cs.filter((c) => !appliedIds.includes(c.id)))
  }
  const aiApplicableCount = aiChanges.filter((c) => c.applicable && aiChecked[c.id]).length

  const loadLetter = async (id: string) => {
    try {
      const o = await lettersApi.get(id)
      if (o.values) {
        const v: any = { ...o.values }
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

  const newLetter = () => { setLetterId(null); setTitle(''); setF((s) => ({ ...s, serial: '', year: String(new Date().getFullYear()), date: todayYMD(), subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '', recipientTitle: 'رئیس محترم' })) }
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
  const tableOp = (op: 'rowAbove' | 'rowBelow' | 'delRow' | 'colLeft' | 'colRight' | 'delCol' | 'mergeCells' | 'valTop' | 'valMiddle' | 'valBottom' | 'delTable') => {
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

    const scratch = document.createElement('div')
    scratch.innerHTML = normalizeBodyHtml(f.body)
    mergeAdjacentTables(scratch)
    normalizeTables(scratch)
    const tr = rowUid ? (scratch.querySelector(`tr[data-r="${cssEsc(rowUid)}"]`) as HTMLTableRowElement | null) : null
    const table = tr?.closest('table') as HTMLTableElement | null
    if (!table || !tr) return
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
    } else if (op === 'delTable') table.remove()
    setF((prev) => ({ ...prev, body: scratch.innerHTML }))
    setTbl(null)
  }

  // ---- Drag a table gridline to resize columns. Live-updates the cell widths in the DOM
  //      while dragging (all fragments of a split table), then persists the % widths onto
  //      every cell of the two affected columns in the full body. ----
  const liveTablesFor = (hdrUid: string) => (Array.from(document.querySelectorAll('#ltr-edit .bcell table')) as HTMLTableElement[]).filter((t) => t.rows[0]?.getAttribute('data-r') === hdrUid)
  const recomputeColRz = (hdrUid: string) => {
    const t = liveTablesFor(hdrUid)[0]
    if (!t || !t.rows[0] || t.rows[0].cells.length < 2) { setColRz(null); return }
    const tr = t.getBoundingClientRect(); const bounds: { x: number; i: number }[] = []
    for (let i = 0; i < t.rows[0].cells.length - 1; i++) bounds.push({ x: t.rows[0].cells[i].getBoundingClientRect().left, i })
    setColRz({ top: tr.top, height: tr.height, hdrUid, bounds })
  }
  const startColResize = (e: React.PointerEvent, i: number) => {
    e.preventDefault(); e.stopPropagation()
    if (!colRz) return
    const hdrUid = colRz.hdrUid
    const tables = liveTablesFor(hdrUid); if (!tables.length) return
    const t0 = tables[0]
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
      // persist the resulting column widths onto the full body
      const live = liveTablesFor(hdrUid)[0]; if (!live) return
      const widths = Array.from(live.rows[0].cells).map((c) => (c as HTMLElement).style.width)
      const scratch = document.createElement('div'); scratch.innerHTML = normalizeBodyHtml(f.body)
      mergeAdjacentTables(scratch); normalizeTables(scratch)
      const tr = scratch.querySelector(`tr[data-r="${cssEsc(hdrUid)}"]`) as HTMLTableRowElement | null
      const table = tr?.closest('table') as HTMLTableElement | null
      if (table) { Array.from(table.rows).forEach((r) => widths.forEach((w, ci) => { if (w && r.cells[ci]) (r.cells[ci] as HTMLElement).style.width = w })); setF((prev) => ({ ...prev, body: scratch.innerHTML })) }
      requestAnimationFrame(() => recomputeColRz(hdrUid))   // realign the handles to the re-rendered table
    }
    document.addEventListener('pointermove', mv); document.addEventListener('pointerup', up)
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
      if (/^(TABLE|UL|OL)$/.test(el.tagName) || el.querySelector('table,ul,ol')) { flush(); out.push(el.outerHTML); continue }
      // split on <br> AND newlines (a pre-wrap block can hold \n line breaks too)
      const segs = (el as HTMLElement).innerHTML.split(/<br\s*\/?>|\r?\n/i)
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
    // The closing block (امضاکننده/رونوشت/اقدام) stays at the position you set in «چیدمان»
    // (drag it to the bottom, wherever you like) on the LAST page. If the last page's
    // content would reach into that zone, give the closing its own trailing page so nothing
    // overlaps. (No auto-flow — dragging the sender/body box won't move the other fields.)
    const li = pages.length - 1
    if (!isHidden('sender') && pages.length && pageH(pages[li]) > regionAvail(li, true)) pages.push([])
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
  const P = (k: string, node: React.ReactNode, extra?: React.CSSProperties) => isHidden(k) ? null : <div style={{ ...boxStyle(k), ...extra }}>{node}</div>  // print: positioned, hide-aware
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
            style={{ ...bodyTextStyle(), position: 'absolute', left: L.body.x, top: contY, width: L.body.w, height: regionAvail(pi, false) }} />)}

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
        .tbl-bar{position:fixed;transform:translate(-50%,-135%);z-index:121;display:flex;gap:2px;align-items:center;flex-wrap:wrap;justify-content:center;max-width:min(92vw,760px);background:#0f766e;border-radius:7px;padding:3px 4px;box-shadow:0 6px 18px rgba(0,0,0,.32)}
        .col-rz{position:fixed;width:6px;z-index:122;cursor:col-resize;background:transparent}
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
        .lai-diff{display:flex;align-items:center;gap:8px;margin-top:7px;flex-wrap:wrap;font-size:12.5px}
        .lai-before{background:#fef2f2;color:#991b1b;border:1px solid #fecaca;border-radius:6px;padding:2px 7px;text-decoration:line-through;max-width:100%;overflow-wrap:anywhere}
        .lai-after{background:#f0fdf4;color:#166534;border:1px solid #bbf7d0;border-radius:6px;padding:2px 7px;max-width:100%;overflow-wrap:anywhere}
        .lai-arrow{color:#94a3b8}
        .lai-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;border-top:1px solid #e2e8f0;background:#f8fafc}
        .lai-cancel{border:1px solid #cbd5e1;background:#fff;color:#475569;border-radius:8px;padding:8px 16px;font-size:13px;cursor:pointer}
        .lai-apply{display:inline-flex;align-items:center;gap:6px;background:#16a34a;color:#fff;border:0;border-radius:8px;padding:9px 18px;font-weight:700;cursor:pointer;font-size:13px}
        .lai-apply:disabled{opacity:.5;cursor:default}
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
          .print-wrap{display:block!important;padding:0!important;margin:0!important}
          /* drop the on-screen bottom padding — sheet + 20px padding pushed past A4 onto a
             blank extra page */
          .canvas-wrap{overflow:visible;padding:0!important;margin:0!important}
          /* keep each sheet strictly UNDER A4 height (1123px≈297.1mm overflowed); clip any
             sub-pixel overflow so one sheet = exactly one printed page */
          .psheet{box-shadow:none;margin:0!important;height:296mm;overflow:hidden;break-after:page;page-break-after:always}
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
          <button onClick={openAi} className="ltr-btn" style={{ background: 'linear-gradient(90deg,#7c3aed,#4f46e5)' }} title="بازبینی و اصلاحِ هوشمندِ نامه با هوش مصنوعی — پیش از اعمال، فهرست را می‌بینی و تیک می‌زنی"><Sparkles size={15} /> دستیارِ هوشمند</button>
          <button onClick={() => setF((s) => ({ ...s, subject: '', body: '', copyTo: '', actionName: '', actionExt: '', recipientName: '', recipientDept: '' }))} className="ltr-btn gray"><Eraser size={14} /> پاک‌کردن</button>
          <span className="ltr-hint">{`متن را بنویس؛ هر صفحه که پر شود، خودکار صفحهٔ جدید ساخته می‌شود (الان ${fa(pages.length)} صفحه). «چیدمان» = جابه‌جایی/تنظیمِ فیلدها (با دبل‌کلیک: چینش/جهت/تورفتگی).`}</span>
          <span className="ltr-hint" style={{ fontWeight: 700, color: '#16a34a', direction: 'ltr' }} title="نسخهٔ کد — برای تأییدِ استقرار">build: reflow-v16</span>
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
        {colRz && !design && colRz.bounds.map((b) => (
          <div key={b.i} className="col-rz no-print" style={{ left: b.x - 3, top: colRz.top, height: colRz.height }}
            title="کشیدن برای تغییرِ عرضِ ستون" onPointerDown={(e) => startColResize(e, b.i)} />
        ))}

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
                  </div>

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
                      {aiLoading ? '⏳ در حالِ بررسی…' : <><Sparkles size={15} /> بررسیِ نامه</>}
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
                        <div key={c.id} className={`lai-item${c.applicable ? '' : ' note'}`}>
                          <div className="lai-itemhead">
                            {c.applicable
                              ? <input type="checkbox" checked={!!aiChecked[c.id]} onChange={(e) => setAiChecked((s) => ({ ...s, [c.id]: e.target.checked }))} />
                              : <span className="lai-noteicon" title="فقط تذکر — اعمال نمی‌شود">ℹ</span>}
                            <span className="lai-cat">{CAT_FA[c.category] || c.category}</span>
                            <span className="lai-sev" style={{ background: SEV_COLOR[c.severity] || '#64748b' }}>{SEV_FA[c.severity] || c.severity}</span>
                            <span className="lai-title">{c.title}</span>
                          </div>
                          {c.detail && <div className="lai-detail">{c.detail}</div>}
                          {c.applicable && (c.op === 'text_replace' || c.op === 'set_field') && (
                            <div className="lai-diff">
                              <span className="lai-before">{c.before || '—'}</span>
                              <span className="lai-arrow">←</span>
                              <span className="lai-after">{c.after || '—'}</span>
                            </div>
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
