/**
 * v141 — a dragged rectangle over a screen must become an ADDRESS the supervisor
 * can walk back to.
 *
 * This is the load-bearing part of «نظارت و سرکشی»: if the address is wrong, the
 * supervisor goes and looks at the wrong thing and answers the wrong question,
 * which is worse than not answering at all.
 */
import {
  CAPTURE_DEADLINE_MS, CAPTURE_MAX_NODES, CAPTURE_MAX_PX, CAPTURE_MAX_SIDE, CAPTURE_MIN_H,
  bandAround,
  boundedCaptureTarget, captureChain, captureRatio, withDeadline,
  domPath, geometryLabel, isOurOverlay, matchesSpot, measureSpot, normalizePath, pageElementsAt,
  pickCaptureTarget, pickCropSheet, placeSpot, querySelectorPath, samePage, resolveSpot,
  spotAddress, verifiedSelector, visibleText,
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

// v165 — «فقط همان صفحه باید باشه». The picture must show ONE sheet of a
// multi-sheet document. The camera still points at the whole surface (pointing
// it at a sheet makes the rasteriser render that sheet wrongly — see the module);
// the sheet is what the finished picture is cropped to.
describe('pickCaptureTarget / pickCropSheet — one sheet, from a faithful picture', () => {
  const stack = () => mount(`
    <main data-report-surface="/letter">
      <div class="print-wrap">
        <div class="psheet" id="p1"><p id="a">page one</p></div>
        <div class="psheet" id="p2"><p id="b">page two</p></div>
        <div class="psheet" id="p3"><p id="c">page three</p></div>
      </div>
    </main>`)

  it('rasterises the whole surface, never a single sheet', () => {
    const root = stack()
    const t = pickCaptureTarget(root.querySelector('#b'))!
    expect(t.getAttribute('data-report-surface')).toBe('/letter')
  })

  it('crops to the sheet the box landed on', () => {
    const root = stack()
    const t = pickCaptureTarget(root.querySelector('#b'))!
    expect(pickCropSheet(root.querySelector('#b'), t)!.id).toBe('p2')
    expect(pickCropSheet(root.querySelector('#c'), t)!.id).toBe('p3')
  })

  it('does not crop an ordinary screen that is not a stack of sheets', () => {
    const root = mount(`
      <main data-report-surface="/customers">
        <section data-report-section="filters"><input id="q" /></section>
      </main>`)
    const t = pickCaptureTarget(root.querySelector('#q'))!
    expect(t.getAttribute('data-report-surface')).toBe('/customers')
    expect(pickCropSheet(root.querySelector('#q'), t)).toBeNull()
  })

  it('accepts a sheet that opts in with data-report-page', () => {
    const root = mount(`
      <main data-report-surface="/x">
        <div data-report-page="2" id="sheet"><b id="k">k</b></div>
      </main>`)
    const t = pickCaptureTarget(root.querySelector('#k'))!
    expect(pickCropSheet(root.querySelector('#k'), t)!.id).toBe('sheet')
  })

  it('refuses to crop to a sheet that is not inside the picture', () => {
    const root = mount(`
      <div>
        <div class="psheet" id="loose"><b id="k">k</b></div>
        <main data-report-surface="/x"><p>x</p></main>
      </div>`)
    const t = pickCaptureTarget(null)!          // falls back to the surface
    expect(pickCropSheet(root.querySelector('#k'), t)).toBeNull()
  })

  it('falls back to the surface when the box is off any element', () => {
    mount('<main data-report-surface="/x"><p>x</p></main>')
    expect(pickCaptureTarget(null)!.getAttribute('data-report-surface')).toBe('/x')
  })

  it('returns the element itself when nothing is reportable', () => {
    const root = mount('<div><span id="s">s</span></div>')
    expect(pickCaptureTarget(root.querySelector('#s'))!.id).toBe('s')
  })
})

// v171 — THE ROOT OF «همه صفحات فرم در اسکرین گزارش دیده میشه».
//
// The capture asks the DOM what is under the drawn box, and it asks AFTER the
// report dialog has opened. The old check (`el.hasAttribute`) only asked about
// the element itself, so the dialog's own card — a child of the layer — read as
// page content: no surface above it, no sheet around it, so the crop was
// dropped and the whole multi-sheet document was photographed. Fixing it at the
// two call sites would have left the next overlay to repeat it.
describe('pageElementsAt — our own UI is never mistaken for the page', () => {
  // jsdom has no hit-testing, so the stack is supplied — what is under test is
  // the FILTER, which is where the bug was.
  const at = (els: Element[]) =>
    pageElementsAt(10, 10, { elementsFromPoint: () => els } as unknown as Document)

  it('drops a NESTED element of an inspection layer, not just its root', () => {
    const root = mount(`
      <div>
        <div data-inspection-layer="1" id="layer">
          <div class="card" id="card"><button id="btn">ثبت</button></div>
        </div>
        <main data-report-surface="/letter"><div class="lsheet" id="sheet">x</div></main>
      </div>`)
    const btn = root.querySelector('#btn')!
    const card = root.querySelector('#card')!
    const layer = root.querySelector('#layer')!
    const sheet = root.querySelector('#sheet')!
    expect(at([btn, card, layer, sheet]).map((e) => e.id)).toEqual(['sheet'])
  })

  it('keeps the page element that was underneath', () => {
    const root = mount(`
      <div>
        <div data-inspection-layer="1"><div id="backdrop">.</div></div>
        <main data-report-surface="/x"><p id="target">متن</p></main>
      </div>`)
    const got = at([root.querySelector('#backdrop')!, root.querySelector('#target')!])
    expect(got[0].id).toBe('target')
  })

  it('is unchanged for a page with no overlay at all', () => {
    const root = mount('<main data-report-surface="/x"><p id="p">x</p></main>')
    expect(at([root.querySelector('#p')!]).map((e) => e.id)).toEqual(['p'])
  })

  it('isOurOverlay answers about ancestors, which is the question', () => {
    const root = mount(`
      <div data-inspection-layer="1"><span><b id="deep">x</b></span></div>
      <p id="page">y</p>`)
    expect(isOurOverlay(root.querySelector('#deep'))).toBe(true)
    expect(isOurOverlay(root.querySelector('#page'))).toBe(false)
    expect(isOurOverlay(null)).toBe(false)
    expect(isOurOverlay(undefined)).toBe(false)
  })

  // The whole point: with the dialog open, the box must STILL resolve to the
  // sheet it was drawn on, so the capture is cropped to that one page.
  it('still finds the sheet to crop to while the dialog is open', () => {
    const root = mount(`
      <div>
        <div data-inspection-layer="1"><div class="dlg" id="dlg">گزارش</div></div>
        <main data-report-surface="/letter">
          <div class="lsheet" id="p1"><p id="a">one</p></div>
          <div class="lsheet" id="p2"><p id="b">two</p></div>
        </main>
      </div>`)
    const el = at([root.querySelector('#dlg')!, root.querySelector('#b')!])[0]
    const target = pickCaptureTarget(el)!
    expect(target.getAttribute('data-report-surface')).toBe('/letter')
    expect(pickCropSheet(el, target)!.id).toBe('p2')
  })
})

// v172 — THE FIELD THAT SAID «you drew a box around a stylesheet».
//
// A real sheet reached the supervisor with covered_text =
// «/* English serif for LATIN LETTERS ONLY — Persian letters, digits …».
// The owner had drawn a box on the letter toolbar; the page keeps its CSS in a
// <style> block; textContent folds that in; and the text was taken from the
// whole SURFACE because that page declares no data-report-section. So the one
// field that says WHAT was pointed at was noise, and that round placed the new
// control by taste — «سلیقه رفتی». A confidently wrong field is worse than an
// empty one.
describe('v172 — what was in the box, and nothing nobody can see', () => {
  it('never reports a stylesheet as the thing that was covered', () => {
    const root = mount(`
      <main data-report-surface="/letter">
        <style>/* English serif for LATIN LETTERS ONLY — keep the Persian font */</style>
        <div class="ltr-controls"><button>پرینت</button><button>پاک‌کردن</button></div>
      </main>`)
    const text = visibleText(root.querySelector('main'))
    expect(text).not.toContain('English serif')
    expect(text).toContain('پرینت')
  })

  it.each(['style', 'script', 'noscript', 'template'])('skips <%s>', (tag) => {
    const root = mount(`<div id="w"><${tag}>NOISE_TOKEN</${tag}><span>دیده می‌شود</span></div>`)
    expect(visibleText(root.querySelector('#w'))).not.toContain('NOISE_TOKEN')
  })

  it('drops an unseen subtree even from a single-child chain', () => {
    // the branch that takes `textContent` wholesale — where the bug actually was
    const root = mount('<div id="w"><style>NOISE_TOKEN</style>متنِ واقعی</div>')
    const t = visibleText(root.querySelector('#w'))
    expect(t).not.toContain('NOISE_TOKEN')
    expect(t).toContain('متنِ واقعی')
  })

  it('still separates neighbours instead of running them together', () => {
    const root = mount('<div id="w"><span>جستجو</span><span>نوع حساب</span><span>شعبه</span></div>')
    expect(visibleText(root.querySelector('#w'))).toBe('جستجو · نوع حساب · شعبه')
  })
})

describe('v172 — the description comes from the spot, not from the whole page', () => {
  const spotOn = (stack: Element[]) =>
    resolveSpot({ rect: RECT, viewport: VIEW, stack })

  it('describes the control under the box, not the entire surface', () => {
    const root = mount(`
      <main data-report-surface="/letter" data-report-surface-label="نامه">
        <style>/* a long stylesheet nobody can see */</style>
        <div class="ltr-controls" id="row">
          <button id="print">پرینت</button><button>پاک‌کردن</button>
        </div>
        <div class="lsheet">برگهٔ نامه</div>
      </main>`)
    const btn = root.querySelector('#print')!
    const got = spotOn([btn, root.querySelector('#row')!, root.querySelector('main')!])
    expect(got.covered_text).toContain('پرینت')
    expect(got.covered_text).not.toContain('stylesheet')
    expect(got.covered_text).not.toContain('برگهٔ نامه')     // not the whole page
  })

  it('climbs out of a bare number to the label beside it', () => {
    // «۲۷۶» on its own tells a supervisor nothing; the row does.
    const root = mount(`
      <main data-report-surface="/x">
        <div id="row"><span>مانده حساب</span><span id="n">۲۷۶</span></div>
      </main>`)
    const got = spotOn([root.querySelector('#n')!, root.querySelector('#row')!,
                        root.querySelector('main')!])
    expect(got.covered_text).toContain('مانده حساب')
  })

  it('still prefers a declared section when the page has one', () => {
    const root = mount(`
      <main data-report-surface="/customers">
        <section data-report-section="filters" data-report-section-label="فیلترها" id="sec">
          <span>جستجو</span><span>نوع حساب</span>
        </section>
      </main>`)
    const got = spotOn([root.querySelector('#sec')!, root.querySelector('main')!])
    expect(got.section_id).toBe('filters')
    expect(got.covered_text).toContain('جستجو')
  })

  it('does not climb past the surface into the rest of the document', () => {
    const root = mount(`
      <div>
        <nav>منوی کناری · داشبورد · مشتریان</nav>
        <main data-report-surface="/x" id="m"><div id="empty"></div></main>
      </div>`)
    const got = spotOn([root.querySelector('#empty')!, root.querySelector('#m')!])
    expect(got.covered_text).not.toContain('منوی کناری')
  })
})

// v176 — «صفحه قفل میکنه و هنگ میکنه و بعدشم صفحه میره» → «Aw, Snap!».
//
// That is the renderer running out of memory. Measured cause: the Knowledge Base
// surface is 1112×19096 px — 21.2 MEGAPIXELS — and the capture rasterised it,
// then marked it on a second canvas of the same size, then shrank it on a third.
// Data Quality is 16 MP and sat on the same edge, so this was never one page.
describe('v176 — a capture can never be big enough to kill the tab', () => {
  const S = (w: number, h: number) => ({ w, h })

  it('still photographs an ordinary surface whole', () => {
    const chain = [S(1328, 1200), S(800, 400), S(200, 60)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBe(chain[0])
  })

  it('steps inward on the page that actually crashed', () => {
    // surface 1112×19096 (21 MP) → the card the box is in
    const surface = S(1112, 19096)
    const card = S(1000, 1400)
    const para = S(900, 80)
    expect(boundedCaptureTarget([surface, card, para], (x) => x)).toBe(card)
  })

  it('keeps the MOST context that fits, not the least', () => {
    const big = S(1200, 9000), mid = S(1100, 3000), small = S(400, 200)
    expect(boundedCaptureTarget([big, mid, small], (x) => x)).toBe(mid)
  })

  it('refuses a very long thin strip even when its area is modest', () => {
    // 600 × 30000 is only 18 MP but blows past per-dimension limits
    const strip = S(600, 30000), card = S(600, 900)
    expect(boundedCaptureTarget([strip, card], (x) => x)).toBe(card)
  })

  it('takes the biggest view when nothing fits but everything is cheap to draw', () => {
    // v177 — «never no picture» was v176's rule and it was wrong: a huge subtree
    // CANNOT be drawn in time and no timer can cut it short. Pixels alone are
    // survivable, so these are kept and `captureRatio` scales them.
    const chain = [S(20000, 20000), S(12000, 12000)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBe(chain[0])
  })

  it('skips an element that has not been laid out', () => {
    const hidden = S(0, 0), card = S(900, 600)
    expect(boundedCaptureTarget([hidden, card], (x) => x)).toBe(card)
  })

  it('has nothing to choose from an empty chain', () => {
    expect(boundedCaptureTarget([], (x: any) => x)).toBeNull()
  })
})

describe('captureRatio — the backstop when even the inner element is huge', () => {
  it('is 1:1 for anything of a normal size', () => {
    expect(captureRatio({ w: 1328, h: 1123 })).toBe(1)
    expect(captureRatio({ w: 2000, h: 2000 })).toBe(1)
  })

  it('brings a 21-megapixel surface inside the budget', () => {
    const s = { w: 1112, h: 19096 }
    const r = captureRatio(s)
    expect(r).toBeLessThan(1)
    expect(s.w * r * s.h * r).toBeLessThanOrEqual(CAPTURE_MAX_PX * 1.01)
  })

  it('respects the per-side limit as well as the area', () => {
    const s = { w: 300, h: 40000 }
    const r = captureRatio(s)
    expect(s.h * r).toBeLessThanOrEqual(CAPTURE_MAX_SIDE + 1)
  })

  it('never returns 0 or a negative, whatever it is handed', () => {
    for (const s of [{ w: 0, h: 0 }, { w: -1, h: 10 }, { w: NaN, h: 10 }] as any[])
      expect(captureRatio(s)).toBe(1)
  })
})

describe('captureChain — outermost first, so the widest view that fits wins', () => {
  it('runs from the surface down to the element under the box', () => {
    const root = mount(`
      <main data-report-surface="/knowledge" id="surface">
        <section id="card"><p id="para">متن</p></section>
      </main>`)
    const chain = captureChain(root.querySelector('#para'), root.querySelector('#surface'))
    expect(chain.map((n) => n.id)).toEqual(['surface', 'card', 'para'])
  })

  it('still includes the target when the element is not inside it', () => {
    const root = mount(`
      <div><main data-report-surface="/x" id="surface"></main><p id="stray">x</p></div>`)
    const chain = captureChain(root.querySelector('#stray'), root.querySelector('#surface'))
    expect(chain.map((n) => n.id)).toContain('surface')
    expect(chain.map((n) => n.id)).toContain('stray')
  })

  it('is empty for nothing at all', () => {
    expect(captureChain(null, null)).toEqual([])
  })
})

// v177 — the sweep after v176: the tab no longer died, but THREE pages were
// still wrong, each for its own reason. Measured on the real app:
//
//   /staff/      → 1343×40   a `<tr>` is «within budget» and is not evidence
//   /data-quality/ → 193×2600  a 14000px page shrunk whole, 193 pixels wide
//   /properties/ → 21 SECONDS  0.83 MP, but 9165 nodes and 610 SVGs to serialise
describe('v177 — the three the sweep found', () => {
  const S = (w: number, h: number, nodes = 0) => ({ w, h, nodes })

  it('never picks a strip too short to read (/staff/: 1343×40)', () => {
    const chain = [S(1112, 7731, 4000), S(1343, 7515, 3800), S(1343, 40, 8), S(259, 40, 2)]
    const got = boundedCaptureTarget(chain, (x) => x)
    expect(got!.h).toBeGreaterThanOrEqual(CAPTURE_MIN_H)
  })

  it('steps over a subtree that is cheap in pixels and ruinous in nodes', () => {
    // main is only 0.83 MP but holds a 9165-node table; the small one is both
    const main = S(1112, 747, 9165)
    const inner = S(1064, 451, 300)
    expect(boundedCaptureTarget([main, inner], (x) => x)).toBe(inner)
  })

  it('over the PIXEL budget is survivable — take the biggest affordable view', () => {
    // /data-quality/: nothing fits outright; the two big ones are cheap to
    // serialise, so the largest of them wins and `captureRatio` scales it.
    const chain = [S(1112, 14385, 3100), S(1064, 14337, 3000), S(900, 42, 5)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBe(chain[0])
  })

  it('REFUSES rather than freezing when every candidate is ruinous to serialise', () => {
    // /properties/, measured: toJpeg takes 16.25 SECONDS on this subtree, and it
    // is synchronous, so no timer can cut it short. Returning null lets the page
    // say so at once instead of hanging.
    const chain = [S(1112, 747, 9165), S(1064, 699, 9164), S(1683, 10533, 9066),
                   S(1683, 35, 29), S(104, 35, 0)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBeNull()
  })

  it('keeps a heavy-but-usable page rather than refusing everything', () => {
    // /staff/: 4555 nodes → 5.6 s. Unpleasant, not a freeze.
    const chain = [S(1112, 7731, 4555), S(1343, 40, 8)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBe(chain[0])
  })

  it('still takes the whole surface on an ordinary page', () => {
    const chain = [S(1112, 1431, 900), S(800, 400, 100)]
    expect(boundedCaptureTarget(chain, (x) => x)).toBe(chain[0])
  })
})

describe('bandAround — full width, and only the height that was asked about', () => {
  const IMG = { width: 1064, height: 14337 }

  it('keeps the whole width — that is where the text is', () => {
    const b = bandAround({ x: 100, y: 7000, w: 400, h: 100 }, IMG)!
    expect(b.x).toBe(0)
    expect(b.w).toBe(IMG.width)
  })

  it('is centred on the box and stays inside the picture', () => {
    const b = bandAround({ x: 0, y: 7000, w: 400, h: 100 }, IMG)!
    expect(b.y).toBeLessThan(7050)
    expect(b.y + b.h).toBeGreaterThan(7050)
    expect(b.y).toBeGreaterThanOrEqual(0)
    expect(b.y + b.h).toBeLessThanOrEqual(IMG.height)
  })

  it('does not run off the top for a box at the very start', () => {
    const b = bandAround({ x: 0, y: 5, w: 400, h: 40 }, IMG)!
    expect(b.y).toBe(0)
  })

  it('does not run off the bottom for a box at the very end', () => {
    const b = bandAround({ x: 0, y: IMG.height - 60, w: 400, h: 50 }, IMG)!
    expect(b.y + b.h).toBeLessThanOrEqual(IMG.height)
  })

  it('gives a tall box enough room to be seen whole', () => {
    const b = bandAround({ x: 0, y: 5000, w: 400, h: 900 }, IMG)!
    expect(b.h).toBeGreaterThanOrEqual(900)
  })

  it('does nothing when the picture is already about that tall', () => {
    expect(bandAround({ x: 0, y: 100, w: 400, h: 100 }, { width: 800, height: 700 })).toBeNull()
  })

  it('is safe with an empty picture', () => {
    expect(bandAround({ x: 0, y: 0, w: 1, h: 1 }, { width: 0, height: 0 })).toBeNull()
  })
})

describe('withDeadline — the bound that covers the page nobody has tested', () => {
  it('passes the value through when the work finishes in time', async () => {
    await expect(withDeadline(Promise.resolve('ok'), 1000)).resolves.toBe('ok')
  })

  it('cannot interrupt synchronous work — which is why the node budget exists', () => {
    // Measured: the rasteriser blocks the main thread for 16.25 s on the
    // Properties subtree, so the timer does not run until after the work it was
    // meant to cut short has finished. The first version of this fix relied on
    // this deadline alone and did nothing at all.
    expect(CAPTURE_MAX_NODES).toBeGreaterThan(0)
  })

  it('gives up rather than waiting for ever', async () => {
    jest.useFakeTimers()
    const p = withDeadline(new Promise(() => {}), CAPTURE_DEADLINE_MS)
    jest.advanceTimersByTime(CAPTURE_DEADLINE_MS + 10)
    await expect(p).resolves.toBeNull()
    jest.useRealTimers()
  })

  it('turns a rejection into «no picture», never an unhandled error', async () => {
    await expect(withDeadline(Promise.reject(new Error('boom')), 1000)).resolves.toBeNull()
  })

  it('waits long enough for the slowest page measured, and not much longer', () => {
    expect(CAPTURE_DEADLINE_MS).toBeGreaterThanOrEqual(5000)
    expect(CAPTURE_DEADLINE_MS).toBeLessThanOrEqual(10000)
  })
})
