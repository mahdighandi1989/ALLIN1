// Packing the flowing report onto A4 sheets.
//
// Kept as a PURE function, separate from the page, for one reason: the rule that
// matters here — a table split across a page boundary must carry its column
// titles onto the continuation — is invisible on screen until a report happens to
// be long enough, and by then it is printed. A pure function can be tested at
// every boundary without rendering anything.

export type Block =
  | { t: 'node'; id: string }
  | { t: 'trow'; id: string; sec: string; idx: number }

export type Measured = {
  /** measured height of each block, by id */
  h: Record<string, number>
  /** measured height of each table's header row, by section key */
  head: Record<string, number>
}

/**
 * Greedily fill pages of `avail` px.
 *
 * A `trow` that STARTS a run of its table costs its own height plus the header
 * row that will be drawn above it. That is why the header cost is charged at pack
 * time rather than baked into the row: whether a row needs a header depends on
 * where the page break lands, which is exactly what this function decides.
 *
 * A block taller than a whole page is placed on a page of its own rather than
 * dropped — an oversized row must still print, even imperfectly. Losing a row of
 * a legal report silently would be far worse than an overfull page.
 */
export function paginate(blocks: Block[], m: Measured, avail: number): Block[][] {
  const pages: Block[][] = []
  let cur: Block[] = []
  let used = 0
  let openTable = ''          // the table whose header is already on THIS page run

  for (const b of blocks) {
    const own = m.h[b.id] || 0
    const needsHead = b.t === 'trow' && openTable !== b.sec
    const cost = own + (needsHead ? (m.head[(b as any).sec] || 0) : 0)

    if (used + cost > avail && cur.length) {
      pages.push(cur)
      cur = []
      used = 0
      openTable = ''
    }
    // Re-decide AFTER a possible break: a row that did not need a header on the
    // previous page does need one now that it starts a fresh page.
    const headNow = b.t === 'trow' && openTable !== b.sec
    cur.push(b)
    used += own + (headNow ? (m.head[(b as any).sec] || 0) : 0)
    openTable = b.t === 'trow' ? b.sec : ''
  }
  if (cur.length) pages.push(cur)
  return pages.length ? pages : [[]]
}

/** Does this block start a run of its table on its page (i.e. needs the header)? */
export function startsTable(page: Block[], i: number): boolean {
  const b = page[i]
  if (!b || b.t !== 'trow') return false
  const prev = page[i - 1]
  return !prev || prev.t !== 'trow' || prev.sec !== b.sec
}
