// Re-merge tables that were split across pages (same header) so storage stays clean:
// the split is a VIEW concern — what gets saved is always one whole table.
export function mergeAdjacentTables(container: HTMLElement) {
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

// v124 — PAGINATE ONE ATTACHMENT TABLE ACROSS AS MANY A4 PAGES AS IT NEEDS.
// Before v124 an attachment table was locked to exactly ONE page: it stepped its
// font down to 60% and, when even that didn't fit, gave up with a red warning and
// rendered a clipped table. A genuinely long table (a real list of properties,
// facilities, instalments…) simply could not be printed.
// This mirrors the letter body's own row-level pagination: plain blocks stay whole
// and a tall table is cut BETWEEN rows, with its HEADER ROW repeated at the top of
// every page — so page 2+ is still readable on its own. Returns one HTML string per
// page (never an empty array) and `oversize` for the only case nothing can fix
// automatically: a SINGLE row taller than a whole page.
// `holder` is a caller-owned off-screen node (one per measuring pass) so the DOM is
// touched once instead of per table.
export type AttSplit = { chunks: string[]; oversize: boolean }
export function paginateAttHtml(html: string, holder: HTMLElement, widthPx: number, heightPx: number, fontPt: number): AttSplit {
  const box = document.createElement('div')
  box.className = 'measure'
  box.style.cssText = `position:static;visibility:hidden;width:${widthPx}px;font-size:${fontPt}pt;line-height:1.7;white-space:pre-wrap`
  box.innerHTML = html || ''
  holder.appendChild(box)
  // Atomic units: a plain block, or ONE table body-row carrying its table's opening
  // tag + header (so a chunk can rebuild a valid, styled <table> on its own).
  type U = { html: string; h: number; tid: number; header: string; headerH: number; topen: string }
  const units: U[] = []
  let tid = 0
  let oversize = false
  const collect = (node: Element) => {
    for (const child of Array.from(node.children)) {
      const c = child as HTMLElement
      if (c.tagName === 'TABLE') {
        const rows = Array.from(c.querySelectorAll('tr')) as HTMLElement[]
        if (rows.length > 1) {
          tid++
          const header = rows[0].outerHTML, headerH = rows[0].offsetHeight
          // keep the table-level class/style (resized widths live there)
          const topen = c.outerHTML.slice(0, c.outerHTML.indexOf('>') + 1)
          for (let i = 1; i < rows.length; i++) units.push({ html: rows[i].outerHTML, h: rows[i].offsetHeight, tid, header, headerH, topen })
          continue
        }
      }
      if (c.tagName !== 'TABLE' && c.querySelector('table')) { collect(c); continue }   // unwrap paste-wrappers
      units.push({ html: c.outerHTML, h: c.offsetHeight, tid: 0, header: '', headerH: 0, topen: '' })
    }
  }
  collect(box)
  holder.removeChild(box)
  // Pack greedily; the header's height is charged once per table per page.
  const pgs: U[][] = []
  let cur: U[] = [], used = 0
  let seen = new Set<number>()
  for (const u of units) {
    const need = () => u.h + (u.tid && !seen.has(u.tid) ? u.headerH : 0)
    if (need() > heightPx) oversize = true
    if (cur.length && used + need() > heightPx) { pgs.push(cur); cur = []; used = 0; seen = new Set<number>() }
    used += need()
    cur.push(u)
    if (u.tid) seen.add(u.tid)
  }
  if (cur.length || !pgs.length) pgs.push(cur)
  // A trailing page holding only invisible leftovers (contentEditable always keeps a
  // caret line under a table) must never become a real blank page — fold it back.
  const blank = (u: U) => !u.tid && !u.html.replace(/<br\s*\/?>/gi, '').replace(/<[^>]+>/g, '').replace(/&nbsp;|\u00a0/gi, ' ').trim()
  while (pgs.length > 1 && pgs[pgs.length - 1].every(blank)) {
    const tail = pgs.pop() as U[]
    pgs[pgs.length - 1].push(...tail)
  }
  const render = (us: U[]) => {
    let out = '', i = 0
    while (i < us.length) {
      const u = us[i]
      if (!u.tid) { out += u.html; i++; continue }
      const t = u.tid
      let rr = ''
      while (i < us.length && us[i].tid === t) { rr += us[i].html; i++ }
      out += `${u.topen}${u.header}${rr}</table>`
    }
    return out
  }
  return { chunks: pgs.map(render), oversize }
}
