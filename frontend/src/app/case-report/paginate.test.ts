import { paginate, startsTable, type Block } from './paginate'
import { SECTIONS, TABLE_KEYS, blankRow } from './sections'

const node = (id: string): Block => ({ t: 'node', id })
const row = (sec: string, idx: number): Block => ({ t: 'trow', id: `${sec}-${idx}`, sec, idx })
const heights = (bs: Block[], each: number) =>
  Object.fromEntries(bs.map((b) => [b.id, each])) as Record<string, number>

describe('paginate — packing the report onto A4 sheets', () => {
  it('keeps everything on one page when it fits', () => {
    const bs = [node('a'), node('b'), node('c')]
    const pages = paginate(bs, { h: heights(bs, 100), head: {} }, 900)
    expect(pages).toHaveLength(1)
    expect(pages[0].map((b) => b.id)).toEqual(['a', 'b', 'c'])
  })

  it('breaks to a new page instead of overflowing', () => {
    const bs = [node('a'), node('b'), node('c')]
    const pages = paginate(bs, { h: heights(bs, 400), head: {} }, 900)
    expect(pages.map((p) => p.map((b) => b.id))).toEqual([['a', 'b'], ['c']])
  })

  it('never drops a block, whatever the boundary', () => {
    const bs = Array.from({ length: 37 }, (_, i) => node(`n${i}`))
    for (const avail of [50, 99, 100, 101, 250, 1000]) {
      const flat = paginate(bs, { h: heights(bs, 100), head: {} }, avail).flat()
      expect(flat.map((b) => b.id)).toEqual(bs.map((b) => b.id))
    }
  })

  it('places an oversized block rather than losing it', () => {
    // A single row taller than a whole page must still print. Silently dropping
    // a row of a legal report is far worse than an overfull page.
    const bs = [node('small'), node('huge')]
    const pages = paginate(bs, { h: { small: 100, huge: 5000 }, head: {} }, 900)
    expect(pages.flat().map((b) => b.id)).toEqual(['small', 'huge'])
    expect(pages).toHaveLength(2)
  })

  it('charges the header only for the row that opens the table', () => {
    const bs = [row('t', 0), row('t', 1), row('t', 2)]
    // rows 100 each, header 200: with the header charged once, all three fit in 500
    const pages = paginate(bs, { h: heights(bs, 100), head: { t: 200 } }, 500)
    expect(pages).toHaveLength(1)
  })

  it('re-charges the header when a table spills onto the next page', () => {
    const bs = [row('t', 0), row('t', 1), row('t', 2), row('t', 3)]
    // header 100 + 4 rows × 100 = 500; a 350px page must break, and the
    // continuation pays for its own header again.
    const pages = paginate(bs, { h: heights(bs, 100), head: { t: 100 } }, 350)
    expect(pages.length).toBeGreaterThan(1)
    for (const pg of pages) {
      const used = pg.length * 100 + 100     // every page here opens the table
      expect(used).toBeLessThanOrEqual(350)
    }
  })

  it('a table continued on the next page carries its column titles', () => {
    const bs = [row('t', 0), row('t', 1), row('t', 2), row('t', 3)]
    const pages = paginate(bs, { h: heights(bs, 100), head: { t: 100 } }, 350)
    for (const pg of pages) {
      // the FIRST row on every page must be flagged as starting the table, or the
      // continuation prints columns of numbers with no headings above them
      expect(startsTable(pg, 0)).toBe(true)
    }
  })

  it('does not repeat the header in the middle of an uninterrupted run', () => {
    const pg = [row('t', 0), row('t', 1), row('t', 2)]
    expect(startsTable(pg, 0)).toBe(true)
    expect(startsTable(pg, 1)).toBe(false)
    expect(startsTable(pg, 2)).toBe(false)
  })

  it('starts a new header when a different table follows on the same page', () => {
    const pg = [row('a', 0), row('b', 0)]
    expect(startsTable(pg, 0)).toBe(true)
    expect(startsTable(pg, 1)).toBe(true)
  })

  it('a heading immediately before a table does not swallow its header', () => {
    const bs = [node('h'), row('t', 0)]
    const pages = paginate(bs, { h: { h: 40, 't-0': 100 }, head: { t: 60 } }, 900)
    expect(startsTable(pages[0], 1)).toBe(true)
  })

  it('always returns at least one page, so the sheet still renders when empty', () => {
    expect(paginate([], { h: {}, head: {} }, 900)).toEqual([[]])
  })
})

describe('the paper form is described completely', () => {
  it('covers all eleven numbered sections of the template', () => {
    const numbered = SECTIONS.filter((s) => s.no).map((s) => s.no)
    for (const n of ['۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹', '۱۰', '۱۱']) {
      expect(numbered.some((x) => x === n || x.startsWith(n + '-'))).toBe(true)
    }
  })

  it('every section key is unique', () => {
    const keys = SECTIONS.map((s) => s.key)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('every table column key is unique within its section', () => {
    for (const s of SECTIONS) {
      if (s.kind !== 'table') continue
      const keys = s.cols.map((c) => c.key)
      expect(new Set(keys).size).toBe(keys.length)
    }
  })

  it('blankRow gives a cell for every column, so a new row is never half-shaped', () => {
    for (const s of SECTIONS) {
      if (s.kind !== 'table') continue
      expect(Object.keys(blankRow(s)).sort()).toEqual(s.cols.map((c) => c.key).sort())
    }
  })

  it('TABLE_KEYS matches the repeating sections the backend stores', () => {
    // These are the exact keys the API's `tables` object uses; a rename that
    // happened on only one side would silently stop saving a whole section.
    expect(TABLE_KEYS.sort()).toEqual([
      'approvals', 'collateral_actions', 'collaterals', 'collections',
      'commitments', 'discounted_cheques', 'facilities_granted',
      'facilities_unsettled', 'partners',
    ].sort())
  })
})
