/**
 * v153 — the mark on the picture.
 *
 * The maths is what matters and what can silently drift, so it is tested apart
 * from the canvas: a wrong mapping would put the rectangle somewhere the owner
 * never clicked, which is worse than leaving the picture bare.
 */
import { boxInImage, clampCrop } from './annotateShot'

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

describe('v165 — the mark lands where the owner drew, not where it fits', () => {
  it('is unchanged for a plain element that neither scrolls nor scales', () => {
    const box = boxInImage(
      { x: 150, y: 250, w: 100, h: 40 },
      { left: 100, top: 200, width: 800, height: 600 },
      { width: 800, height: 600 })!
    expect(box).toEqual({ x: 50, y: 50, w: 100, h: 40 })
  })

  it('needs no special case for a scroll container', () => {
    // Its border box IS its visible box, and the rasteriser renders that same
    // border box — so layout and viewport agree and nothing has to be added back.
    const box = boxInImage(
      { x: 150, y: 250, w: 100, h: 40 },
      { left: 100, top: 200, width: 800, height: 600,
        layoutWidth: 800, layoutHeight: 600 },
      { width: 800, height: 600 })!
    expect(box).toEqual({ x: 50, y: 50, w: 100, h: 40 })
  })

  it('accounts for a CSS transform that shrank the element on screen', () => {
    // laid out 1000 wide, displayed 500 wide ⇒ everything on screen is half size
    const box = boxInImage(
      { x: 150, y: 100, w: 50, h: 20 },
      { left: 100, top: 100, width: 500, height: 500,
        layoutWidth: 1000, layoutHeight: 1000 },
      { width: 1000, height: 1000 })!
    expect(box).toEqual({ x: 100, y: 0, w: 100, h: 40 })
  })

  it('scales with the picture when it was rasterised above 1x', () => {
    const box = boxInImage(
      { x: 150, y: 250, w: 100, h: 40 },
      { left: 100, top: 200, width: 800, height: 600,
        layoutWidth: 800, layoutHeight: 600 },
      { width: 1600, height: 1200 })!
    expect(box).toEqual({ x: 100, y: 100, w: 200, h: 80 })
  })

  it('handles a transform AND a high-density raster together', () => {
    const box = boxInImage(
      { x: 200, y: 100, w: 50, h: 50 },
      { left: 100, top: 100, width: 500, height: 500,
        layoutWidth: 1000, layoutHeight: 1000 },
      { width: 2000, height: 2000 })!
    expect(box).toEqual({ x: 400, y: 0, w: 200, h: 200 })
  })

  it('still refuses a box that falls outside the picture', () => {
    expect(boxInImage(
      { x: 5000, y: 5000, w: 10, h: 10 },
      { left: 0, top: 0, width: 800, height: 600, layoutWidth: 800, layoutHeight: 600 },
      { width: 800, height: 600 })).toBeNull()
  })
})

// v165 — the crop that turns «every sheet» into «the sheet you pointed at».
describe('clampCrop — cutting one sheet out of the picture', () => {
  it('keeps a crop that sits inside the picture', () => {
    expect(clampCrop({ x: 24, y: 1200, w: 794, h: 1123 }, 1328, 3500))
      .toEqual({ x: 24, y: 1200, w: 794, h: 1123 })
  })

  it('never reads past the edge — that would come out black on a JPEG', () => {
    expect(clampCrop({ x: 24, y: 3000, w: 794, h: 1123 }, 1328, 3500))
      .toEqual({ x: 24, y: 3000, w: 794, h: 500 })
  })

  it('pulls a negative origin back to zero', () => {
    expect(clampCrop({ x: -30, y: -10, w: 200, h: 200 }, 400, 400))
      .toEqual({ x: 0, y: 0, w: 200, h: 200 })
  })

  it('drops a crop that is already the whole picture', () => {
    expect(clampCrop({ x: 0, y: 0, w: 400, h: 400 }, 400, 400)).toBeNull()
  })

  it('drops a degenerate crop rather than producing a sliver', () => {
    expect(clampCrop({ x: 0, y: 0, w: 8, h: 300 }, 400, 400)).toBeNull()
    expect(clampCrop({ x: 399, y: 0, w: 100, h: 300 }, 400, 400)).toBeNull()
  })

  it('has nothing to do when there is no crop', () => {
    expect(clampCrop(null, 400, 400)).toBeNull()
    expect(clampCrop(undefined, 400, 400)).toBeNull()
  })
})
