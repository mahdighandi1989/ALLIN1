/**
 * v150 — the display preferences behind the highlights, and the colour rule.
 *
 * The overlay's own geometry is covered in `inspectionSpot.test.ts`; what is
 * tested here is what the owner asked for explicitly: default ON, an opacity
 * that saves, and blocked storage never breaking the feature.
 */
import {
  HL_DEFAULT_OPACITY, HL_ENABLED_KEY, HL_OPACITY_KEY, TONE_COLOR, clampOpacity,
  readHighlightOpacity, readHighlightsEnabled, toneOf,
  writeHighlightOpacity, writeHighlightsEnabled,
} from './inspectionHighlights'

describe('highlight preferences', () => {
  beforeEach(() => { localStorage.clear() })

  it('is ON by default — an absent key means «not set», not «off»', () => {
    expect(readHighlightsEnabled()).toBe(true)
  })

  it('remembers being turned off, and back on', () => {
    writeHighlightsEnabled(false)
    expect(readHighlightsEnabled()).toBe(false)
    writeHighlightsEnabled(true)
    expect(readHighlightsEnabled()).toBe(true)
  })

  it('has a sane default opacity and saves a chosen one', () => {
    expect(readHighlightOpacity()).toBe(HL_DEFAULT_OPACITY)
    writeHighlightOpacity(0.5)
    expect(readHighlightOpacity()).toBe(0.5)
  })

  it('clamps an absurd opacity instead of drawing an invisible or opaque box', () => {
    expect(clampOpacity(0)).toBeGreaterThan(0)      // never fully invisible
    expect(clampOpacity(5)).toBeLessThanOrEqual(0.9) // never fully opaque
    writeHighlightOpacity(99)
    expect(readHighlightOpacity()).toBeLessThanOrEqual(0.9)
  })

  it('falls back to the default when the stored value is junk', () => {
    localStorage.setItem(HL_OPACITY_KEY, 'not-a-number')
    expect(readHighlightOpacity()).toBe(HL_DEFAULT_OPACITY)
  })

  it('keeps working when storage is blocked — a private window still sees them', () => {
    const get = jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const set = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    expect(readHighlightsEnabled()).toBe(true)          // default ON survives
    expect(readHighlightOpacity()).toBe(HL_DEFAULT_OPACITY)
    expect(() => writeHighlightsEnabled(false)).not.toThrow()
    expect(() => writeHighlightOpacity(0.3)).not.toThrow()
    get.mockRestore(); set.mockRestore()
  })

  it('announces a change so an open page updates without a reload', () => {
    const seen: string[] = []
    const h = () => seen.push('changed')
    window.addEventListener('allin1:inspection-highlights', h)
    writeHighlightsEnabled(false)
    writeHighlightOpacity(0.4)
    window.removeEventListener('allin1:inspection-highlights', h)
    expect(seen).toHaveLength(2)
  })
})

describe('v166 — the highlight says whose turn it is', () => {
  const sheet = (status: string, glowTone = 'fixed') =>
    ({ glow: { tone: glowTone, key: '', label: '' }, status } as any)

  // The four states the owner named, each with one meaning.
  it('is amber while it waits for the supervisor', () => {
    expect(toneOf(sheet('open'))).toBe(TONE_COLOR.open)
  })

  it('turns green the moment the supervisor has replied', () => {
    expect(toneOf(sheet('answered'))).toBe(TONE_COLOR.answered)
  })

  it('turns blue when the owner ticks it', () => {
    expect(toneOf(sheet('approved'))).toBe(TONE_COLOR.approved)
  })

  it('goes back to amber when the owner writes again', () => {
    // the server re-opens the sheet on an owner note (v158); the colour follows
    expect(toneOf(sheet('open', 'fixed'))).toBe(TONE_COLOR.open)
  })

  // The regression that started this: the colour used to be the OUTCOME, so an
  // answered sheet came back amber/grey/red and an approved one came out GREEN
  // while its own badge on the board said blue.
  it('does not let the outcome override the state', () => {
    expect(toneOf(sheet('answered', 'partial'))).toBe(TONE_COLOR.answered)
    expect(toneOf(sheet('answered', 'stale'))).toBe(TONE_COLOR.answered)
    expect(toneOf(sheet('answered', 'not-done'))).toBe(TONE_COLOR.answered)
    expect(toneOf(sheet('approved', 'fixed'))).toBe(TONE_COLOR.approved)
  })

  it('agrees with the board badge — green answered, blue approved', () => {
    // bg-emerald-600 = 16,185,129 · bg-blue-600 = 59,130,246 (see TONE in ./inspection)
    expect(TONE_COLOR.answered).toBe('16, 185, 129')
    expect(TONE_COLOR.approved).toBe('59, 130, 246')
  })

  it('still honours an outcome tone for a status it does not know', () => {
    expect(toneOf(sheet('some-future-state', 'needs-owner'))).toBe(TONE_COLOR['needs-owner'])
  })

  it('never returns undefined, whatever it is handed', () => {
    expect(toneOf({ glow: { tone: 'nonsense' }, status: 'nonsense' } as any))
      .toBe(TONE_COLOR.open)
    expect(toneOf({ glow: undefined, status: 'open' } as any)).toBe(TONE_COLOR.open)
  })
})
