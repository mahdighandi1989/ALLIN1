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
