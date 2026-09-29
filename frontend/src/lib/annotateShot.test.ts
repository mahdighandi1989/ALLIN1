/**
 * v153 — the mark on the picture.
 *
 * The maths is what matters and what can silently drift, so it is tested apart
 * from the canvas: a wrong mapping would put the rectangle somewhere the owner
 * never clicked, which is worse than leaving the picture bare.
 */
import { boxInImage } from './annotateShot'

const rect = (left: number, top: number, width: number, height: number) =>
  ({ left, top, width, height })

describe('boxInImage', () => {
  it('moves a viewport box into the image, 1:1', () => {
    expect(boxInImage({ x: 150, y: 220, w: 80, h: 40 },
      rect(100, 200, 800, 600), { width: 800, height: 600 }))
      .toEqual({ x: 50, y: 20, w: 80, h: 40 })
  })

  it('scales when the capture was rendered larger than the element', () => {
    // a 2× capture must put the mark at 2× the offset AND 2× the size
    expect(boxInImage({ x: 150, y: 220, w: 80, h: 40 },
      rect(100, 200, 800, 600), { width: 1600, height: 1200 }))
      .toEqual({ x: 100, y: 40, w: 160, h: 80 })
  })

  it('handles a box at the very origin of the element', () => {
    expect(boxInImage({ x: 100, y: 200, w: 10, h: 10 },
      rect(100, 200, 400, 300), { width: 400, height: 300 }))
      .toEqual({ x: 0, y: 0, w: 10, h: 10 })
  })

  it('refuses a box that lies outside the captured element', () => {
    // marking empty space would point at something the owner never selected
    expect(boxInImage({ x: 2000, y: 220, w: 40, h: 40 },
      rect(100, 200, 800, 600), { width: 800, height: 600 })).toBeNull()
    expect(boxInImage({ x: 10, y: 10, w: 20, h: 20 },
      rect(100, 200, 800, 600), { width: 800, height: 600 })).toBeNull()
  })

  it('keeps a box that only partly overlaps — the visible part still helps', () => {
    const out = boxInImage({ x: 80, y: 220, w: 60, h: 40 },
      rect(100, 200, 800, 600), { width: 800, height: 600 })
    expect(out).not.toBeNull()
    expect(out!.x).toBeLessThan(0)          // starts left of the capture
    expect(out!.x + out!.w).toBeGreaterThan(0)
  })

  it('returns null rather than dividing by zero', () => {
    expect(boxInImage({ x: 1, y: 1, w: 1, h: 1 },
      rect(0, 0, 0, 0), { width: 100, height: 100 })).toBeNull()
    expect(boxInImage({ x: 1, y: 1, w: 1, h: 1 },
      rect(0, 0, 100, 100), { width: 0, height: 0 })).toBeNull()
  })
})
