import { layoutKeysUnder, overlapArea, rectOnSheet, sheetIndexFor, type Item } from './quickSpot'

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
