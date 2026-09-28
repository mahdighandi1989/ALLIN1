/**
 * v141 — a dragged rectangle over a screen must become an ADDRESS the supervisor
 * can walk back to.
 *
 * This is the load-bearing part of «نظارت و سرکشی»: if the address is wrong, the
 * supervisor goes and looks at the wrong thing and answers the wrong question,
 * which is worse than not answering at all.
 */
import { domPath, matchesSpot, resolveSpot, spotAddress, visibleText } from './inspectionSpot'

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
