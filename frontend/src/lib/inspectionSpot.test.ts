/**
 * v141 — a dragged rectangle over a screen must become an ADDRESS the supervisor
 * can walk back to.
 *
 * This is the load-bearing part of «نظارت و سرکشی»: if the address is wrong, the
 * supervisor goes and looks at the wrong thing and answers the wrong question,
 * which is worse than not answering at all.
 */
import {
  domPath, geometryLabel, matchesSpot, measureSpot, normalizePath, placeSpot, querySelectorPath, samePage,
  resolveSpot, spotAddress, verifiedSelector, visibleText,
} from './inspectionSpot'

function mount(html: string): HTMLElement {
  const root = document.createElement('div')
  root.innerHTML = html
  document.body.appendChild(root)
  return root
}
afterEach(() => { document.body.innerHTML = '' })

const RECT = { x: 10, y: 20, w: 300, h: 120 }
const VIEW = { w: 1500, h: 900 }
const spotOf = (stack: Element[]) => resolveSpot({ rect: RECT, viewport: VIEW, stack })

describe('resolveSpot — the way back', () => {
  it('reads the page and the section from the data attributes', () => {
    const root = mount(`
      <main data-report-surface="/customers" data-report-surface-label="مشتریان">
        <section data-report-section="filters" data-report-section-label="فیلترها">
          <button id="go">جستجو</button>
        </section>
      </main>`)
    const s = spotOf([root.querySelector('#go')!])
    expect(s.page).toBe('/customers')
    expect(s.page_label).toBe('مشتریان')
    expect(s.section_id).toBe('filters')
    expect(s.reopen).toBe('/customers#filters')
  })

  it('falls back to the page alone when the block has no section', () => {
    const root = mount(`
      <main data-report-surface="/reports" data-report-surface-label="گزارش‌ها">
        <div><span id="x">۲۷۶</span></div>
      </main>`)
    expect(spotOf([root.querySelector('#x')!]).reopen).toBe('/reports')
  })

  it('still files a usable sheet when a screen marks nothing at all', () => {
    /* A screen that forgets the attributes must not silently produce a sheet
       nobody can act on — the DOM path is what makes it findable. */
    const root = mount('<div class="panel"><button id="b">برو</button></div>')
    const s = spotOf([root.querySelector('#b')!])
    expect(s.page_label).toBe('جایی در رابط')
    expect(s.dom_path).toContain('button#b')
  })

  it('never stores pixel coordinates as the address', () => {
    const root = mount('<main data-report-surface="/x" data-report-surface-label="X"><b id="i">y</b></main>')
    const s = spotOf([root.querySelector('#i')!])
    expect(s.reopen).not.toMatch(/\d{2,}/)     // the reopen key is not a position
    expect(s.rect).toEqual(RECT)               // the rectangle is kept, but only as context
  })
})

describe('visibleText — what the owner was looking at', () => {
  it('separates neighbours instead of running them together', () => {
    /* `textContent` alone produced «جستجونوع حسابشعبه», which is unreadable and
       therefore useless to whoever has to act on it. */
    const root = mount(`
      <section data-report-section="f" data-report-section-label="فیلترها">
        <span>جستجو</span><span>نوع حساب</span><span>شعبه</span>
      </section>`)
    const text = visibleText(root.querySelector('section'))
    expect(text).toBe('جستجو · نوع حساب · شعبه')
  })

  it('prefers the section over a bare number the rectangle happened to cover', () => {
    const root = mount(`
      <main data-report-surface="/dq" data-report-surface-label="کیفیت داده">
        <section data-report-section="score" data-report-section-label="امتیاز">
          <h3>میانگین</h3><span id="n">۵</span>
        </section>
      </main>`)
    const s = spotOf([root.querySelector('#n')!])
    expect(s.covered_text).toContain('میانگین')
  })

  it('caps a long block instead of sending the whole page', () => {
    const root = mount(`<div id="big">${'الف '.repeat(500)}</div>`)
    expect(visibleText(root.querySelector('#big')).length).toBeLessThanOrEqual(601)
  })
})

describe('helpers', () => {
  it('reads the address on one line', () => {
    expect(spotAddress({ page_label: 'مشتریان', section_label: 'فیلترها', reopen: 'x' }))
      .toBe('مشتریان ← فیلترها')
    expect(spotAddress({ page_label: 'مشتریان', section_label: '', reopen: 'x' })).toBe('مشتریان')
  })

  it('matches a sheet to the section it belongs to, and to nothing else', () => {
    expect(matchesSpot('/customers#filters', '/customers#filters')).toBe(true)
    expect(matchesSpot('/customers#filters', '/customers')).toBe(false)
    expect(matchesSpot(undefined, '/customers')).toBe(false)
  })

  it('keeps the dom path short enough to read', () => {
    const root = mount('<div><div><div><div><div><i id="deep">x</i></div></div></div></div></div>')
    expect(domPath(root.querySelector('#deep')).split(' > ').length).toBeLessThanOrEqual(4)
  })
})

// ---------------------------------------------------------------------------
// v150 — precise geometry. The owner asked for «مختصاتِ فوق‌العاده دقیق» and
// «ابعاد», and for a highlight redrawn on the same spot. A coordinate that has
// silently drifted is worse than one that admits it, so these tests are mostly
// about the difference between exact and approximate.
// ---------------------------------------------------------------------------
describe('measureSpot', () => {
  const base = {
    rect: { x: 100, y: 50, w: 200, h: 80 },
    viewport: { w: 1200, h: 800 },
    scroll: { x: 0, y: 400 },
    doc_size: { w: 1200, h: 5000 },
    dpr: 2,
  }

  it('turns viewport pixels into DOCUMENT pixels by adding the scroll', () => {
    const g = measureSpot({ ...base, anchor: null, anchorRect: null, anchorPath: '' })
    expect(g.doc).toEqual({ x: 100, y: 450, w: 200, h: 80 })
    // and keeps what the owner actually saw, unchanged
    expect(g.view).toEqual({ x: 100, y: 50, w: 200, h: 80 })
    expect(g.scroll).toEqual({ x: 0, y: 400 })
    expect(g.dpr).toBe(2)
  })

  it('stores the box as FRACTIONS of its anchor, which survive a resize', () => {
    const g = measureSpot({
      ...base, anchor: {} as Element, anchorPath: 'body > div:nth-of-type(2)',
      anchorRect: { x: 50, y: 400, w: 400, h: 160 },
    })
    expect(g.anchor.path).toBe('body > div:nth-of-type(2)')
    expect(g.anchor.rel).toEqual({ x: 0.125, y: 0.3125, w: 0.5, h: 0.5 })
  })

  it('refuses to store fractions of a zero-sized anchor', () => {
    const g = measureSpot({
      ...base, anchor: {} as Element, anchorPath: 'body > div',
      anchorRect: { x: 0, y: 0, w: 0, h: 0 },
    })
    // dividing by zero would produce Infinity and a highlight the size of the sky
    expect(g.anchor.path).toBe('')
    expect(g.anchor.rel).toEqual({ x: 0, y: 0, w: 0, h: 0 })
  })

  it('drops the anchor when no selector round-tripped', () => {
    const g = measureSpot({
      ...base, anchor: {} as Element, anchorPath: '',
      anchorRect: { x: 0, y: 0, w: 100, h: 100 },
    })
    expect(g.anchor.path).toBe('')
  })
})

describe('placeSpot', () => {
  const geom = {
    doc: { x: 100, y: 450, w: 200, h: 80 },
    view: { x: 100, y: 50, w: 200, h: 80 },
    scroll: { x: 0, y: 400 }, viewport: { w: 1200, h: 800 },
    doc_size: { w: 1200, h: 5000 }, dpr: 1,
    anchor: {
      path: '#box', rect: { x: 50, y: 400, w: 400, h: 160 },
      rel: { x: 0.125, y: 0.3125, w: 0.5, h: 0.5 },
    },
  }

  it('follows the anchor when the layout has moved it', () => {
    // the same element, now 300px lower and half as wide
    const p = placeSpot(geom, () => ({ x: 50, y: 700, w: 200, h: 160 }))
    expect(p).toEqual({
      rect: { x: 75, y: 750, w: 100, h: 80 },
      basis: 'anchor', approximate: false,
    })
  })

  it('reproduces the original box exactly when nothing moved', () => {
    const p = placeSpot(geom, () => ({ x: 50, y: 400, w: 400, h: 160 }))
    expect(p!.rect).toEqual({ x: 100, y: 450, w: 200, h: 80 })
    expect(p!.approximate).toBe(false)
  })

  it('falls back to document pixels AND SAYS SO when the anchor is gone', () => {
    const p = placeSpot(geom, () => null)
    expect(p).toEqual({ rect: { x: 100, y: 450, w: 200, h: 80 }, basis: 'document', approximate: true })
  })

  it('treats a zero-sized anchor as gone rather than collapsing the box', () => {
    const p = placeSpot(geom, () => ({ x: 0, y: 0, w: 0, h: 0 }))
    expect(p!.basis).toBe('document')
  })

  it('draws nothing at all when there is no geometry', () => {
    // sheets filed before v150 — guessing a position would be worse than none
    expect(placeSpot(null)).toBeNull()
    expect(placeSpot(undefined)).toBeNull()
  })

  it('draws nothing for a degenerate box', () => {
    expect(placeSpot({ ...geom, doc: { x: 1, y: 1, w: 0, h: 0 }, anchor: { ...geom.anchor, path: '' } })).toBeNull()
  })
})

describe('geometryLabel', () => {
  it('reads as size, position and window', () => {
    const s = geometryLabel({
      doc: { x: 100.4, y: 450.6, w: 200.2, h: 80.8 },
      view: { x: 100, y: 50, w: 200, h: 80 },
      scroll: { x: 0, y: 400 }, viewport: { w: 1200, h: 800 },
      doc_size: { w: 1200, h: 5000 }, dpr: 1,
      anchor: { path: '', rect: { x: 0, y: 0, w: 0, h: 0 }, rel: { x: 0, y: 0, w: 0, h: 0 } },
    })
    expect(s).toContain('200×81')
    expect(s).toContain('x=100')
    expect(s).toContain('y=451')
    expect(s).toContain('1200×800')
  })

  it('is empty rather than fabricated when nothing was measured', () => {
    expect(geometryLabel(null)).toBe('')
  })
})

describe('querySelectorPath / verifiedSelector', () => {
  beforeEach(() => { document.body.innerHTML = '' })

  it('builds a selector that finds the same element again', () => {
    document.body.innerHTML = `
      <div><section><p>one</p><p id="target">two</p><p>three</p></section></div>`
    const el = document.getElementById('target')!
    const path = querySelectorPath(el)
    expect(document.querySelector(path)).toBe(el)
  })

  it('distinguishes siblings of the same tag by position', () => {
    document.body.innerHTML = '<div><span>a</span><span>b</span><span>c</span></div>'
    const spans = Array.from(document.querySelectorAll('span'))
    for (const s of spans) expect(document.querySelector(querySelectorPath(s))).toBe(s)
  })

  it('verifiedSelector returns the path only when it round-trips', () => {
    document.body.innerHTML = '<div><button>go</button></div>'
    const b = document.querySelector('button')!
    expect(verifiedSelector(b)).toBeTruthy()
    expect(document.querySelector(verifiedSelector(b))).toBe(b)
  })

  it('verifiedSelector returns EMPTY for a detached element rather than a wrong answer', () => {
    // a selector that resolves to something else would place the highlight on
    // the wrong control with full confidence — empty is the honest answer
    const orphan = document.createElement('div')
    expect(verifiedSelector(orphan)).toBe('')
  })

  it('returns empty for nothing', () => {
    expect(querySelectorPath(null)).toBe('')
    expect(verifiedSelector(null)).toBe('')
  })
})

describe('normalizePath / samePage', () => {
  it('treats a trailing slash as the same page — the bug that hid every highlight', () => {
    // the static export serves `/dashboard/`, so usePathname() returns it with a
    // slash while a stored sheet says `/dashboard`. Raw comparison answered «a
    // different page» and nothing was ever drawn.
    expect(samePage('/dashboard', '/dashboard/')).toBe(true)
    expect(samePage('/dashboard/', '/dashboard')).toBe(true)
  })

  it('levels case but not identity', () => {
    expect(samePage('/Customers', '/customers')).toBe(true)
    expect(samePage('/customers', '/facilities')).toBe(false)
  })

  it('ignores a query or fragment on the route', () => {
    expect(samePage('/customers?page=2', '/customers/')).toBe(true)
    expect(samePage('/customers#x', '/customers')).toBe(true)
  })

  it('never collapses everything to one page', () => {
    expect(samePage('', '/customers')).toBe(false)
    expect(samePage(null, undefined)).toBe(true)      // both «no page»
    expect(normalizePath('/')).toBe('/')
    expect(normalizePath('')).toBe('/')
  })

  it('matchesSpot compares the SECTION exactly and the route loosely', () => {
    expect(matchesSpot('/customers#filters', '/customers/#filters')).toBe(true)
    expect(matchesSpot('/customers#filters', '/customers#rows')).toBe(false)
    // a section id is the page author's own string — not case-levelled
    expect(matchesSpot('/customers#Filters', '/customers#filters')).toBe(false)
    expect(matchesSpot(undefined, '/customers')).toBe(false)
  })
})
