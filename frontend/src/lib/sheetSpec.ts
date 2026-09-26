// v138 — read a rendered "sheet" form (the Credit File Summary pages) out of the
// LIVE DOM into a neutral spec that the Word and Excel exporters both consume.
//
// WHY FROM THE DOM, and not from the page's React state:
//
//   • The owner's requirement is «دقیقاً به همین شکلی که هست» — the file must
//     look like the form on screen. The form's shape lives in JSX: bands, header
//     rows, column counts, merges, the order of sections. Re-describing that
//     shape inside two exporters would create a third and fourth copy of the
//     layout that silently rots the first time somebody adds a row — the failure
//     this project has already paid for elsewhere (see the completeness lesson:
//     a hand-kept shortlist drifted from the real form).
//   • Reading the DOM means a section added to the page tomorrow exports itself.
//
// WHAT IS EXPORTED IS THE **PRINT** VIEW, NOT THE SCREEN VIEW. The page already
// decides what belongs on paper through @media print, and the officer's mental
// model of "as it is" is what they get from پرینت:
//   dropped  .no-print · .screen-only · .addbtn · .tools (whole column) · .pr-hide
//   shown    .print-only  (e.g. the facility tag that is a <select> on screen)
// Getting this wrong is not cosmetic: .pr-hide is the «حذف از پرینت» feature, so
// exporting a hidden row would put back a row the officer deliberately removed.

export type SheetCell = {
  text: string
  span: number            // merged width AFTER print-hidden columns are removed
  rowSpan?: number
  bold?: boolean
  align?: 'left' | 'center' | 'right'
  fill?: string           // 6-hex, no '#'
  wrap?: boolean          // came from a textarea / a wrapping cell
}

export type SheetBlock =
  | { kind: 'table'; rows: SheetCell[][]; widths: number[] }
  | { kind: 'banner'; left: string; leftSub?: string; rightLabel?: string; rightValue?: string }
  | { kind: 'title'; text: string }
  | { kind: 'line'; text: string }
  | { kind: 'signatures'; left: string; right: string }

export type SheetSpec = {
  title: string           // document title, e.g. "CREDIT FILE SUMMARY (Corporate)"
  account: string
  blocks: SheetBlock[]
}

// The sheet's palette, kept in ONE place. These mirror the page CSS
// (.band/.hdr/.sn/.desc); the print stylesheet clears input backgrounds, so a
// value cell is white in the exports too.
const FILL_BAND = 'C7CCD3'
const FILL_HDR = 'DDE1E7'
const FILL_KEY = 'EEF1F5'
const FILL_DATE = 'E5E7EB'

/** Is this element removed from the printed page? */
function printHidden(el: Element): boolean {
  const c = el.classList
  return c.contains('no-print') || c.contains('screen-only') || c.contains('addbtn')
    || c.contains('tools') || c.contains('pr-hide')
}

/** The text a cell shows on PAPER — inputs render their value, not a widget. */
function cellText(td: Element): string {
  const parts: string[] = []
  const walk = (n: Node) => {
    if (n.nodeType === Node.TEXT_NODE) { parts.push(n.nodeValue || ''); return }
    if (n.nodeType !== Node.ELEMENT_NODE) return
    const el = n as HTMLElement
    // .print-only is the page's way of substituting a paper rendering for a
    // widget — keep it even though it is hidden on screen.
    if (!el.classList.contains('print-only') && printHidden(el)) return
    const tag = el.tagName
    if (tag === 'INPUT') {
      const inp = el as HTMLInputElement
      if (inp.type === 'checkbox') { parts.push(inp.checked ? '☑' : '☐'); return }
      parts.push(inp.value || ''); return
    }
    if (tag === 'TEXTAREA') { parts.push((el as HTMLTextAreaElement).value || ''); return }
    if (tag === 'SELECT') {
      const s = el as HTMLSelectElement
      const opt = s.selectedOptions[0]
      // a placeholder option ("— تسهیلات —") is chrome, not content
      parts.push(opt && opt.value ? opt.text : ''); return
    }
    if (tag === 'BUTTON' || tag === 'SVG' || tag === 'DATALIST') return
    el.childNodes.forEach(walk)
  }
  td.childNodes.forEach(walk)
  return parts.join(' ').replace(/ /g, ' ').replace(/\s+/g, ' ').trim()
}

type Anchor = { td: HTMLTableCellElement; c0: number; cols: number; rows: number }

/**
 * Expand a table into the real grid (colspan/rowspan resolved), so columns can
 * be dropped and merges recomputed correctly. Doing this by eye on the JSX is
 * what makes hand-written exporters wrong: a band cell spanning "6" spans a
 * DIFFERENT number of columns once the tools column is gone.
 */
function gridOf(table: HTMLTableElement): { anchors: Anchor[][]; ncols: number } {
  const trs = Array.from(table.querySelectorAll('tr'))
  const occupied: boolean[][] = []
  const anchors: Anchor[][] = []
  let ncols = 0
  trs.forEach((tr, r) => {
    occupied[r] = occupied[r] || []
    anchors[r] = []
    let c = 0
    Array.from(tr.children).forEach((child) => {
      if (child.tagName !== 'TD' && child.tagName !== 'TH') return
      const td = child as HTMLTableCellElement
      while (occupied[r][c]) c += 1
      const cols = Math.max(1, td.colSpan || 1)
      const rows = Math.max(1, td.rowSpan || 1)
      anchors[r].push({ td, c0: c, cols, rows })
      for (let dr = 0; dr < rows; dr += 1) {
        occupied[r + dr] = occupied[r + dr] || []
        for (let dc = 0; dc < cols; dc += 1) occupied[r + dr][c + dc] = true
      }
      c += cols
      ncols = Math.max(ncols, c)
    })
  })
  return { anchors, ncols }
}

function tableBlock(table: HTMLTableElement): SheetBlock | null {
  const { anchors, ncols } = gridOf(table)
  if (!ncols) return null

  // --- which grid columns leave the printed page? ---------------------------
  // A tools/screen-only cell is always a single-width cell in its own column;
  // a band cell spans across it, so "every cell here is tools" would never be
  // true. One single-width tools cell is therefore the reliable signal.
  const drop = new Set<number>()
  anchors.forEach((row) => row.forEach((a) => {
    if (a.cols === 1 && (a.td.classList.contains('tools') || a.td.classList.contains('screen-only'))) {
      drop.add(a.c0)
    }
  }))
  const keep: number[] = []
  for (let c = 0; c < ncols; c += 1) if (!drop.has(c)) keep.push(c)
  if (!keep.length) return null
  const newIndex = new Map<number, number>()
  keep.forEach((c, i) => newIndex.set(c, i))

  // --- measured column widths, so the file matches what the eye sees ---------
  const widths = new Array(keep.length).fill(0)
  anchors.forEach((row) => row.forEach((a) => {
    if (a.cols !== 1 || !newIndex.has(a.c0)) return
    const w = a.td.getBoundingClientRect().width
    const i = newIndex.get(a.c0)!
    if (w > widths[i]) widths[i] = w
  }))
  const total = widths.reduce((s, w) => s + w, 0)
  const norm = total > 0
    ? widths.map((w) => (w > 0 ? w / total : 1 / keep.length))
    : widths.map(() => 1 / keep.length)

  // --- rows ------------------------------------------------------------------
  const trs = Array.from(table.querySelectorAll('tr'))
  const rows: SheetCell[][] = []
  anchors.forEach((rowAnchors, r) => {
    const tr = trs[r]
    if (!tr || printHidden(tr)) return          // .pr-hide — deliberately off the page
    const cells: SheetCell[] = []
    rowAnchors.forEach((a) => {
      const span = Array.from({ length: a.cols }, (_, k) => a.c0 + k).filter((c) => !drop.has(c)).length
      if (!span) return                          // the cell lived only in dropped columns
      const cl = a.td.classList
      const isBand = cl.contains('band')
      const isHdr = tr.classList.contains('hdr')
      const isKey = cl.contains('sn') || cl.contains('desc')
      cells.push({
        text: cellText(a.td),
        span,
        rowSpan: a.rows > 1 ? a.rows : undefined,
        bold: isBand || isHdr || isKey || undefined,
        align: isBand ? 'left' : (isHdr || cl.contains('sn')) ? 'center' : undefined,
        fill: isBand ? FILL_BAND : isHdr ? FILL_HDR : isKey ? FILL_KEY : undefined,
        wrap: !!a.td.querySelector('textarea') || undefined,
      })
    })
    if (cells.length) rows.push(cells)
  })
  if (!rows.length) return null
  return { kind: 'table', rows, widths: norm }
}

/**
 * Walk the sheet's own children IN ORDER. Anything the page adds later — a new
 * table, a new band — is picked up without touching this file.
 */
export function readSheetSpec(root: HTMLElement, account = ''): SheetSpec {
  const blocks: SheetBlock[] = []
  let title = ''

  const visit = (el: Element) => {
    if (printHidden(el)) return
    const cl = el.classList

    if (cl.contains('cf-row-top')) {
      const logo = el.querySelector('.cf-logo')
      const date = el.querySelector('.cf-date')
      blocks.push({
        kind: 'banner',
        left: (logo?.querySelector('b')?.textContent || '').trim(),
        leftSub: (logo?.querySelector('span')?.textContent || '').trim(),
        rightLabel: (date?.querySelector('.l')?.textContent || '').trim(),
        rightValue: (date?.querySelector('input') as HTMLInputElement | null)?.value || '',
      })
      return
    }
    if (cl.contains('cf-title')) {
      const t = cellText(el)
      title = title || t
      blocks.push({ kind: 'title', text: t })
      return
    }
    if (cl.contains('cf-branch')) { blocks.push({ kind: 'line', text: cellText(el) }); return }
    if (cl.contains('cf-foot')) {
      const signs = Array.from(el.querySelectorAll('.cf-sign'))
      blocks.push({
        kind: 'signatures',
        left: (signs[0]?.childNodes[0]?.nodeValue || 'Prepared By:').trim(),
        right: (signs[1]?.childNodes[0]?.nodeValue || 'Authorized:').trim(),
      })
      return
    }
    if (el.tagName === 'TABLE' && cl.contains('cf')) {
      const b = tableBlock(el as HTMLTableElement)
      if (b) blocks.push(b)
      return
    }
    // a wrapper (e.g. a fragment div) — look inside rather than lose its content
    Array.from(el.children).forEach(visit)
  }

  Array.from(root.children).forEach(visit)
  return { title: title || 'CREDIT FILE SUMMARY', account, blocks }
}

/** A safe, informative file name: form + account + date. */
export function sheetFileBase(spec: SheetSpec): string {
  const kind = /retail/i.test(spec.title) ? 'Retail' : /corporate/i.test(spec.title) ? 'Corporate' : 'Summary'
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  const stamp = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`
  const acc = (spec.account || '').replace(/[^\w-]/g, '') || 'no-account'
  return `CreditFile-${kind}-${acc}-${stamp}`
}

export const SHEET_FILLS = { band: FILL_BAND, hdr: FILL_HDR, key: FILL_KEY, date: FILL_DATE }
