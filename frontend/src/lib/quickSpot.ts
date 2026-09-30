// v171 — «نوار دستورِ سریع»: what a box drawn over the letter form COVERS.
//
// The assistant cannot see the screen, so a box has to be turned into words it can
// act on: which layout boxes (logo, subject, body…) sit under it — most overlap
// first — which A4 sheet it is on, its position ON THAT SHEET (not the window: the
// window scrolls, the sheet does not) and the text underneath. Pure on purpose: it
// takes plain rectangles, so a test can drive it without a browser.

export type R = { x: number; y: number; w: number; h: number }
export type Item = { key: string; rect: R }

export const overlapArea = (a: R, b: R): number => {
  const w = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x)
  const h = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y)
  return w > 0 && h > 0 ? w * h : 0
}

/**
 * Layout keys under `box`, best first. A key counts when the box covers at least
 * `minShare` of it OR a good part of the box lies inside it — so both a tight box
 * around a small caption and a loose box around a big field find their target.
 */
export function layoutKeysUnder(box: R, items: readonly Item[], minShare = 0.25, max = 6): string[] {
  const boxArea = Math.max(1, box.w * box.h)
  const scored: { key: string; score: number }[] = []
  for (const it of items) {
    const a = overlapArea(box, it.rect)
    if (a <= 0) continue
    const ofItem = a / Math.max(1, it.rect.w * it.rect.h)
    const ofBox = a / boxArea
    if (ofItem >= minShare || ofBox >= 0.5) scored.push({ key: it.key, score: Math.max(ofItem, ofBox) + a / 1e9 })
  }
  scored.sort((p, q) => q.score - p.score)
  const seen = new Set<string>()
  const out: string[] = []
  for (const s of scored) if (!seen.has(s.key)) { seen.add(s.key); out.push(s.key); if (out.length >= max) break }
  return out
}

/** The box re-expressed relative to the sheet it landed on, rounded to whole px. */
export function rectOnSheet(box: R, sheet: R): R {
  const r = (n: number) => Math.round(n)
  return { x: r(box.x - sheet.x), y: r(box.y - sheet.y), w: r(box.w), h: r(box.h) }
}

/** The sheet holding most of the box (1-based page number), or 0 when none does. */
export function sheetIndexFor(box: R, sheets: readonly R[]): number {
  let best = 0
  let bestA = 0
  sheets.forEach((s, i) => {
    const a = overlapArea(box, s)
    if (a > bestA) { bestA = a; best = i + 1 }
  })
  return best
}

// v173 — WHAT IS *ACTUALLY* UNDER THE BOX.
//
// «کادر دو مثلاً در فرم حول یه جدول، ولی پیش‌نمایشش جایی دیگه رو شناسایی کرده».
//
// The first version answered this by climbing the DOM: take the element under
// the box's centre, walk up to its `[data-lbox]`, and use that element's text.
// On this form the whole letter body IS one layout box, so a box drawn around
// the table in §3 reported the body's text — which starts at §1. Every box on
// the body described the same paragraph, confidently and wrongly.
//
// The body is ONE element, so position inside it cannot come from ancestry. It
// has to come from GEOMETRY: which pieces of text actually intersect the
// rectangle. A Range over each text node gives exactly that, including inside
// tables, and it is the same answer a human gives by looking.
//
// The rect source is injected so this can be tested without a layout engine —
// jsdom returns nothing from getClientRects, which would make a test that used
// the real one pass while proving nothing.

/** Client rects of a node, as the browser lays it out. */
export const domRects = (n: Node): R[] => {
  try {
    if (n.nodeType === 3) {
      const r = (n.ownerDocument || document).createRange()
      r.selectNodeContents(n)
      return Array.from(r.getClientRects()).map((b) => ({ x: b.left, y: b.top, w: b.width, h: b.height }))
    }
    const b = (n as Element).getBoundingClientRect()
    return [{ x: b.left, y: b.top, w: b.width, h: b.height }]
  } catch { return [] }
}

const clean = (s: string) => s.replace(/\s+/g, ' ').trim()

/**
 * The text whose own rectangles fall inside `box`, in document order.
 *
 * `minShare` is of the LINE, not of the box: a box drawn a little wide must
 * still report the line it is around, while a line merely grazed at the edge
 * must not drag a neighbouring paragraph in.
 */
export function textInRect(
  root: Element | null,
  box: R,
  rects: (n: Node) => R[] = domRects,
  max = 400,
  minShare = 0.4,
): string {
  if (!root) return ''
  const out: string[] = []
  const walk = (root.ownerDocument || document).createTreeWalker(root, 4 /* TEXT */)
  let n: Node | null
  while ((n = walk.nextNode())) {
    const t = clean(n.textContent || '')
    if (!t) continue
    const hit = rects(n).some((r) => {
      const a = overlapArea(box, r)
      return a > 0 && a / Math.max(1, r.w * r.h) >= minShare
    })
    if (hit) out.push(t)
  }
  const joined = clean(out.join(' '))
  return joined.length > max ? `${joined.slice(0, max)}…` : joined
}

/**
 * The nearest heading-like line at or ABOVE the box, inside the same sheet.
 *
 * On a numbered form («۳- مشخصات تسهیلات اعطائی تسویه نشده») this is the single
 * most useful thing to tell the model: it names the section the owner pointed
 * at, even when the box covers only empty table cells and so has no text of its
 * own — which is exactly the case the owner hit.
 */
export function headingAbove(
  root: Element | null,
  box: R,
  rects: (n: Node) => R[] = domRects,
  maxGap = 400,
): string {
  if (!root) return ''
  let best = ''
  let bestY = -Infinity
  const walk = (root.ownerDocument || document).createTreeWalker(root, 4 /* TEXT */)
  let n: Node | null
  while ((n = walk.nextNode())) {
    const t = clean(n.textContent || '')
    if (t.length < 3 || t.length > 120) continue
    for (const r of rects(n)) {
      const bottom = r.y + r.h
      // The line must START above the box. A line that begins inside it is part
      // of what the box is around — `textInRect` already reports those — and
      // taking one as the «heading» named a table column («مانده اصل در زمان
      // طبقه بندی») instead of the section it sits in. Starting above still
      // allows a heading the box clips by a pixel or two, which is common.
      // The gap cap keeps it from reaching back into another part of the form.
      if (r.y < box.y && Math.max(0, box.y - bottom) <= maxGap && r.y > bestY) {
        bestY = r.y
        best = t
      }
    }
  }
  return best
}
