/**
 * v124 — attachment-table pagination.
 *
 * jsdom has no layout engine, so `offsetHeight` is always 0. We install a real
 * getter that reads a `data-h` attribute, which lets us drive the packer with
 * exact, deliberate heights — a genuine test of the flow decisions (where the
 * cut falls, whether the header repeats, whether a blank tail page appears),
 * not a source scan.
 */
import { paginateAttHtml, mergeAdjacentTables } from './attPaginate'

beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    get(this: HTMLElement) {
      const own = this.getAttribute('data-h')
      if (own !== null) return Number(own)
      // a container's height = sum of its children (good enough for these shapes)
      return Array.from(this.children).reduce((n, c) => n + Number((c as HTMLElement).getAttribute('data-h') || 0), 0)
    },
  })
})

const holderOf = () => {
  const h = document.createElement('div')
  document.body.appendChild(h)
  return h
}

/** a table with `n` body rows, each `rowH` tall, header `hdrH` tall */
const tableHtml = (n: number, rowH = 30, hdrH = 40) =>
  `<table class="tblw"><tr data-h="${hdrH}"><th>ردیف</th><th>شرح</th></tr>` +
  Array.from({ length: n }, (_, i) => `<tr data-h="${rowH}"><td>${i + 1}</td><td>مورد ${i + 1}</td></tr>`).join('') +
  `</table>`

describe('paginateAttHtml', () => {
  it('keeps a short table on a single page (no behaviour change)', () => {
    const holder = holderOf()
    const { chunks, oversize } = paginateAttHtml(tableHtml(5), holder, 764, 800, 13)
    expect(chunks).toHaveLength(1)
    expect(oversize).toBe(false)
    expect((chunks[0].match(/<tr/g) || []).length).toBe(6)   // header + 5 rows
  })

  it('flows a long table over several pages instead of clipping it', () => {
    const holder = holderOf()
    // 40 rows x 30px + 40px header = 1240px of content in a 400px-tall region
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    expect(chunks.length).toBeGreaterThan(3)
    // every body row survives exactly once across the pages
    const bodyRows = chunks.reduce((n, c) => n + (c.match(/<td>/g) || []).length / 2, 0)
    expect(bodyRows).toBe(40)
  })

  it('repeats the header row at the top of every page', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    for (const c of chunks) {
      expect(c.indexOf('<th>')).toBeGreaterThan(-1)
      expect((c.match(/<th>ردیف<\/th>/g) || []).length).toBe(1)
      // the header must be the FIRST row of the chunk
      expect(c.indexOf('<th>')).toBeLessThan(c.indexOf('<td>'))
    }
  })

  it('keeps the table opening tag (resized widths/classes) on every page', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    for (const c of chunks) expect(c).toContain('<table class="tblw">')
  })

  it('never fills a page past its height', () => {
    const holder = holderOf()
    const rowH = 30, hdrH = 40, avail = 400
    const { chunks } = paginateAttHtml(tableHtml(40, rowH, hdrH), holder, 764, avail, 13)
    for (const c of chunks) {
      const rows = (c.match(/<td>/g) || []).length / 2
      expect(hdrH + rows * rowH).toBeLessThanOrEqual(avail)
    }
  })

  it('flags a single row taller than a whole page (nothing can auto-fix that)', () => {
    const holder = holderOf()
    const { oversize, chunks } = paginateAttHtml(tableHtml(3, 900), holder, 764, 400, 13)
    expect(oversize).toBe(true)
    expect(chunks.length).toBe(3)            // still emitted — never dropped
  })

  it('does not open a blank trailing page for the caret line under a table', () => {
    const holder = holderOf()
    const html = tableHtml(13) + '<div data-h="24"><br></div>'
    // 13 rows x 30 + 40 header = 430 → exactly two pages of content; the trailing
    // empty block must NOT become a third, visually blank page.
    const { chunks } = paginateAttHtml(html, holder, 764, 220, 13)
    expect(chunks[chunks.length - 1]).toContain('<table')
  })

  it('handles plain blocks and an empty input without crashing', () => {
    const holder = holderOf()
    expect(paginateAttHtml('', holder, 764, 400, 13).chunks).toEqual([''])
    const p = paginateAttHtml('<div data-h="100">سلام</div><div data-h="100">دنیا</div>', holder, 764, 120, 13)
    expect(p.chunks).toHaveLength(2)
  })

  it('unwraps a table nested in a paste-wrapper div', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(`<div>${tableHtml(20)}</div>`, holder, 764, 400, 13)
    expect(chunks.length).toBeGreaterThan(1)
    for (const c of chunks) expect(c.startsWith('<table')).toBe(true)
  })
})

describe('split → edit one page → merge back (what storage actually keeps)', () => {
  /** mirrors onAttChunk: put the edited chunk back, re-join, fuse same-header tables */
  const rejoin = (chunks: string[]) => {
    const d = document.createElement('div')
    d.innerHTML = chunks.join('')
    mergeAdjacentTables(d)
    return d.innerHTML
  }

  it('round-trips a multi-page table back into ONE table with every row intact', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    expect(chunks.length).toBeGreaterThan(3)
    const merged = rejoin(chunks)
    expect((merged.match(/<table/g) || []).length).toBe(1)
    expect((merged.match(/<td>/g) || []).length / 2).toBe(40)   // nothing lost
  })

  it('an edit on page 2 survives the merge and does not disturb the other rows', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    const edited = chunks.slice()
    edited[1] = edited[1].replace('مورد ', 'ویرایش‌شده ')
    const merged = rejoin(edited)
    expect((merged.match(/<table/g) || []).length).toBe(1)
    expect((merged.match(/<td>/g) || []).length / 2).toBe(40)
    expect(merged).toContain('ویرایش‌شده ')
    expect(merged).toContain('مورد 1<')                          // page-1 rows untouched
  })

  it('a row DELETED on one page is really gone after the merge', () => {
    const holder = holderOf()
    const { chunks } = paginateAttHtml(tableHtml(40), holder, 764, 400, 13)
    const edited = chunks.slice()
    edited[0] = edited[0].replace(/<tr data-h="30"><td>1<\/td><td>مورد 1<\/td><\/tr>/, '')
    const merged = rejoin(edited)
    expect((merged.match(/<td>/g) || []).length / 2).toBe(39)
  })
})
