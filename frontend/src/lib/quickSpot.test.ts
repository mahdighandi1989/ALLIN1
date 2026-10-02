import {
  headingAbove, layoutKeysUnder, overlapArea, rectOnSheet, rowsInRect, sheetIndexFor, spotTouches, textInRect,
  type Item, type R,
} from './quickSpot'

const items: Item[] = [
  { key: 'logo', rect: { x: 18, y: 15, w: 108, h: 104 } },
  { key: 'subject', rect: { x: 106, y: 295, w: 614, h: 30 } },
  { key: 'body', rect: { x: 95, y: 446, w: 605, h: 560 } },
]

describe('quickSpot', () => {
  it('finds the layout box a tight box is drawn around', () => {
    expect(layoutKeysUnder({ x: 10, y: 10, w: 130, h: 120 }, items)).toEqual(['logo'])
  })
  it('finds a big field with a small box drawn INSIDE it', () => {
    expect(layoutKeysUnder({ x: 200, y: 600, w: 200, h: 100 }, items)).toEqual(['body'])
  })
  it('returns nothing for a box over empty space (outside the sheet)', () => {
    expect(layoutKeysUnder({ x: 900, y: 10, w: 100, h: 100 }, items)).toEqual([])
  })
  it('ranks the better-covered box first when two are really covered', () => {
    const keys = layoutKeysUnder({ x: 100, y: 290, w: 620, h: 400 }, items)
    expect(keys[0]).toBe('subject')
    expect(keys).toContain('body')
  })
  it('ignores a box that merely grazes a big field', () => {
    expect(layoutKeysUnder({ x: 100, y: 290, w: 300, h: 200 }, items)).toEqual(['subject'])
  })
  it('overlapArea is zero for touching edges', () => {
    expect(overlapArea({ x: 0, y: 0, w: 10, h: 10 }, { x: 10, y: 0, w: 10, h: 10 })).toBe(0)
  })
  it('expresses a box relative to its sheet, not the window', () => {
    expect(rectOnSheet({ x: 150.4, y: 1300, w: 50, h: 20 }, { x: 100, y: 1000, w: 794, h: 1123 }))
      .toEqual({ x: 50, y: 300, w: 50, h: 20 })
  })
  it('picks the sheet holding most of the box', () => {
    const sheets = [{ x: 0, y: 0, w: 794, h: 1123 }, { x: 0, y: 1150, w: 794, h: 1123 }]
    expect(sheetIndexFor({ x: 10, y: 1100, w: 50, h: 100 }, sheets)).toBe(2)
    expect(sheetIndexFor({ x: 2000, y: 0, w: 5, h: 5 }, sheets)).toBe(0)
  })
})

// v173 — «کادر دو مثلاً در فرم حول یه جدول، ولی پیش‌نمایشش جایی دیگه رو شناسایی
// کرده … این خیلی افتضاح».
//
// The box was drawn around the table in §3 and the preview reported §1. The
// cause was climbing the DOM: the whole letter body is ONE `[data-lbox]`, so
// every box on it returned the body's text, which begins at §1. Position inside
// a single element cannot come from ancestry — it has to come from geometry.
//
// jsdom has no layout, so the rects are injected. A test using the real
// getClientRects here would pass while proving nothing.
describe('textInRect — the lines the box is actually around', () => {
  const doc = () => {
    const root = document.createElement('div')
    root.innerHTML = `
      <p id="s1">۱- خلاصه وضعیت شرکت: مؤسسه … بر اساس مستندات ثبتی</p>
      <p id="s2">۲- مشخصات شرکا</p>
      <p id="s3">۳- مشخصات تسهیلات اعطائی تسویه نشده (مطالباتی):</p>
      <table id="t3"><tr><td>نوع تسهیلات</td><td>مانده اصل</td><td>نرخ سود</td></tr></table>
      <p id="s4">۴- وصولی‌ها</p>`
    document.body.appendChild(root)
    return root
  }
  // a plausible column of lines down the sheet
  const Y: Record<string, number> = { s1: 100, s2: 200, s3: 300, t3: 340, s4: 500 }
  const rectsOf = (n: Node): R[] => {
    const el = n.nodeType === 3 ? (n.parentElement as Element) : (n as Element)
    const host = el?.closest('[id]') as HTMLElement | null
    const y = host ? Y[host.id] : undefined
    return y === undefined ? [] : [{ x: 40, y, w: 700, h: 30 }]
  }

  it('reports the table the box was drawn around, not the first paragraph', () => {
    const root = doc()
    const box = { x: 32, y: 330, w: 681, h: 60 }      // around §3's table
    const got = textInRect(root, box, rectsOf)
    expect(got).toContain('نوع تسهیلات')
    expect(got).not.toContain('خلاصه وضعیت شرکت')      // the bug, named
  })

  it('reports §1 only when the box is actually on §1', () => {
    const root = doc()
    expect(textInRect(root, { x: 32, y: 95, w: 681, h: 40 }, rectsOf))
      .toContain('خلاصه وضعیت شرکت')
  })

  it('does not drag in a neighbour it merely grazes', () => {
    const root = doc()
    // 4 pixels of §2's line — a stray overlap, not what the owner pointed at
    const got = textInRect(root, { x: 32, y: 296, w: 681, h: 40 }, rectsOf)
    expect(got).toContain('مشخصات تسهیلات')
    expect(got).not.toContain('مشخصات شرکا')
  })

  it('keeps document order when the box spans several lines', () => {
    const root = doc()
    const got = textInRect(root, { x: 32, y: 190, w: 700, h: 200 }, rectsOf)
    expect(got.indexOf('شرکا')).toBeLessThan(got.indexOf('تسویه نشده'))
  })

  it('is empty rather than wrong when the box is over blank space', () => {
    expect(textInRect(doc(), { x: 32, y: 800, w: 681, h: 60 }, rectsOf)).toBe('')
  })

  it('caps its length instead of shipping the whole document', () => {
    const root = document.createElement('div')
    root.innerHTML = `<p id="long">${'ت'.repeat(2000)}</p>`
    document.body.appendChild(root)
    const got = textInRect(root, { x: 0, y: 0, w: 900, h: 900 },
      () => [{ x: 0, y: 0, w: 800, h: 30 }], 100)
    expect(got.length).toBeLessThanOrEqual(101)
    expect(got.endsWith('…')).toBe(true)
  })

  it('survives a null root', () => {
    expect(textInRect(null, { x: 0, y: 0, w: 1, h: 1 }, rectsOf)).toBe('')
  })
})

describe('headingAbove — naming the section a box of empty cells sits in', () => {
  const root = () => {
    const r = document.createElement('div')
    r.innerHTML = `
      <p id="s3">۳- مشخصات تسهیلات اعطائی تسویه نشده (مطالباتی):</p>
      <table id="t3"><tr><td id="c1"></td><td id="c2"></td></tr></table>`
    document.body.appendChild(r)
    return r
  }
  const Y: Record<string, number> = { s3: 300, t3: 340, c1: 340, c2: 340 }
  const rectsOf = (n: Node): R[] => {
    const el = n.nodeType === 3 ? (n.parentElement as Element) : (n as Element)
    const host = el?.closest('[id]') as HTMLElement | null
    const y = host ? Y[host.id] : undefined
    return y === undefined ? [] : [{ x: 40, y, w: 700, h: 30 }]
  }

  it('names the section above an otherwise wordless box', () => {
    expect(headingAbove(root(), { x: 32, y: 335, w: 681, h: 60 }, rectsOf))
      .toContain('تسویه نشده')
  })

  it('never takes a line from INSIDE the box as the heading', () => {
    // A box around the §3 table contains its header cells. Taking one of those
    // named «مانده اصل در زمان طبقه بندی» as the section — which is a column
    // title, not a section — and `textInRect` already reports it anyway.
    const got = headingAbove(root(), { x: 32, y: 320, w: 681, h: 80 }, rectsOf)
    expect(got).toContain('تسویه نشده')
  })

  it('does not reach back across half the page', () => {
    expect(headingAbove(root(), { x: 32, y: 1200, w: 681, h: 60 }, rectsOf)).toBe('')
  })

  it('ignores a line far too long to be a heading', () => {
    const r = document.createElement('div')
    r.innerHTML = `<p id="s3">${'کلمه '.repeat(60)}</p>`
    document.body.appendChild(r)
    expect(headingAbove(r, { x: 32, y: 400, w: 681, h: 60 },
      () => [{ x: 40, y: 300, w: 700, h: 30 }])).toBe('')
  })
})


// v178 — «حتی کادر هم کشیدم»: the box must name the TABLE it was drawn round.
describe('quickSpot — table under the box', () => {
  const mk = (rows: { id: string; top: number }[]) => {
    const d = document.createElement('div')
    d.innerHTML = `<table>${rows.map((r) => `<tr data-r="${r.id}"><td>x</td></tr>`).join('')}</table>`
    const trs = Array.from(d.querySelectorAll('tr')) as HTMLElement[]
    trs.forEach((tr, i) => {
      tr.getBoundingClientRect = () => ({ left: 100, top: rows[i].top, width: 500, height: 30, right: 600, bottom: rows[i].top + 30, x: 100, y: rows[i].top, toJSON: () => ({}) }) as DOMRect
    })
    return d
  }
  it('collects only the rows the box overlaps', () => {
    const d = mk([{ id: 'a', top: 100 }, { id: 'b', top: 130 }, { id: 'c', top: 400 }])
    expect(rowsInRect(d, { x: 90, y: 95, w: 300, h: 60 })).toEqual(['a', 'b'])
    expect(rowsInRect(d, { x: 700, y: 95, w: 50, h: 60 })).toEqual([])
    expect(rowsInRect(null, { x: 0, y: 0, w: 1, h: 1 })).toEqual([])
  })
  it('matches a sent table by any of its rows, or by its attachment page', () => {
    const body = { html: '<table><tr data-r="a"></tr><tr data-r="b"></tr></table>' }
    const att = { html: '<table><tr data-r="z"></tr></table>', attId: 'att1' }
    expect(spotTouches({ rows: ['b'] }, body)).toBe(true)
    expect(spotTouches({ rows: ['b'] }, att)).toBe(false)
    expect(spotTouches({ att_id: 'att1', rows: [] }, att)).toBe(true)
    expect(spotTouches({}, body)).toBe(false)
  })
})
