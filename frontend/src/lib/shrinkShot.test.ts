/**
 * v175 — «ریشه‌ای درست کن که محدودیتی نباشه».
 *
 * The owner pasted a screenshot and the report was refused: «shot: String should
 * have at most 1400000 characters». Raising the server's number alone would only
 * move the wall; the root is that the page shipped whatever the clipboard held.
 *
 * The arithmetic is tested here because it is the part that can be wrong in a
 * way nobody notices — a squashed screenshot still looks like a screenshot. The
 * canvas work is deliberately not: jsdom has no canvas, and a test that mocked
 * one would be testing the mock.
 */
import {
  SHOT_DECODE_MS, SHOT_MAX_CHARS, SHOT_MAX_PX, SHOT_QUALITIES,
  isSmallEnough, planSize, shrinkShot,
} from './shrinkShot'

describe('planSize — smaller, never a different shape', () => {
  it('leaves a picture that is already small alone', () => {
    expect(planSize(1328, 1123)).toEqual({ w: 1328, h: 1123 })
  })

  it('caps the LONG side, whichever it is', () => {
    expect(planSize(5120, 2880)).toEqual({ w: 2600, h: 1463 })   // wide
    expect(planSize(1328, 6400)).toEqual({ w: 540, h: 2600 })    // the tall letter
  })

  it('keeps the aspect ratio to within a pixel', () => {
    for (const [w, h] of [[3840, 2160], [1125, 2436], [5000, 5000], [7000, 1200]]) {
      const p = planSize(w, h)
      expect(Math.abs(p.w / p.h - w / h)).toBeLessThan(0.01)
      expect(Math.max(p.w, p.h)).toBeLessThanOrEqual(SHOT_MAX_PX)
    }
  })

  it('never returns a zero dimension for a very long thin strip', () => {
    const p = planSize(40000, 30)
    expect(p.w).toBe(SHOT_MAX_PX)
    expect(p.h).toBeGreaterThanOrEqual(1)
  })

  it('is safe with nonsense', () => {
    expect(planSize(0, 0)).toEqual({ w: 0, h: 0 })
    expect(planSize(-5, 10)).toEqual({ w: 0, h: 0 })
    expect(planSize(NaN as unknown as number, 10)).toEqual({ w: 0, h: 0 })
  })
})

describe('isSmallEnough — both tests, not one', () => {
  it('passes a small picture of modest size', () => {
    expect(isSmallEnough('x'.repeat(500_000), 1328, 1123)).toBe(true)
  })

  it('fails on bytes alone', () => {
    // a 1500x1000 PNG can still be 8 MB; pixels are not the only cost
    expect(isSmallEnough('x'.repeat(8_000_000), 1500, 1000)).toBe(false)
  })

  it('fails on pixels alone', () => {
    expect(isSmallEnough('x'.repeat(100), 5120, 2880)).toBe(false)
  })

  it('is well under what the server will take', () => {
    // the server's ceiling is 12_000_000; the page must not be the thing that
    // discovers it
    expect(SHOT_MAX_CHARS).toBeLessThan(12_000_000 / 2)
  })
})

describe('shrinkShot — it never loses the picture', () => {
  it('returns a non-image string untouched', async () => {
    await expect(shrinkShot('')).resolves.toBe('')
    await expect(shrinkShot('not a data url')).resolves.toBe('not a data url')
  })

  it('gives up and returns the original when the decoder never answers', async () => {
    // jsdom fires neither onload nor onerror for a data URL. Without a timeout
    // the promise hung for ever and the dialog would sit there with no picture
    // and no error — this test is why `SHOT_DECODE_MS` exists.
    jest.useFakeTimers()
    const d = 'data:image/png;base64,iVBORw0KGgo='
    const p = shrinkShot(d)
    jest.advanceTimersByTime(SHOT_DECODE_MS + 10)
    await expect(p).resolves.toBe(d)
    jest.useRealTimers()
  })

  it('waits long enough for a real decode, and not for ever', () => {
    expect(SHOT_DECODE_MS).toBeGreaterThanOrEqual(3000)
    expect(SHOT_DECODE_MS).toBeLessThanOrEqual(15000)
  })

  it('tries progressively harder, cheapest first', () => {
    expect([...SHOT_QUALITIES]).toEqual([...SHOT_QUALITIES].sort((a, b) => b - a))
    expect(SHOT_QUALITIES[0]).toBeLessThanOrEqual(0.9)   // never re-encode at ~lossless
    expect(SHOT_QUALITIES[SHOT_QUALITIES.length - 1]).toBeGreaterThan(0.3)  // still readable
  })
})
