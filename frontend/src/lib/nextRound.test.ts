/**
 * v168 — the sentence the owner reads after pressing ⚡.
 *
 * «باید ناظر بگه چند دقیقه دیگه میره سراغش … هر دور دقیق به ساعت محلی بسنجه».
 * Two things have to be right: the number, and how honest the number is about
 * itself. A countdown that keeps promising «۱۹ دقیقهٔ دیگر» while the routine is
 * switched off is the failure this is written against.
 */
import { humanGap, localClock, rushMessage, type NextRound } from './nextRound'

const iso = (h: number, m: number, day = 30) =>
  new Date(2026, 8, day, h, m, 0).toISOString()      // LOCAL time in, ISO out

const nr = (o: Partial<NextRound> = {}): NextRound => ({
  at: iso(10, 23), in_seconds: 19 * 60, in_minutes: 19,
  every_minutes: 60, basis: 'observed', last_seen: iso(9, 23), ...o,
})

describe('localClock — the owner\'s clock, not the server\'s', () => {
  it('reads an instant in local time, in Persian digits', () => {
    expect(localClock(iso(10, 23))).toBe('۱۰:۲۳')
  })

  it('pads to two digits so the column never jumps', () => {
    expect(localClock(iso(9, 5))).toBe('۰۹:۰۵')
  })

  it('says «فردا» when the next round is past midnight', () => {
    expect(localClock(iso(0, 23, 31), new Date(2026, 8, 30, 23, 50)))
      .toBe('۰۰:۲۳ (فردا)')
  })

  it('returns nothing rather than «Invalid Date» for junk', () => {
    expect(localClock('not-a-time')).toBe('')
  })
})

describe('humanGap', () => {
  it.each([[19, '۱۹ دقیقهٔ دیگر'], [1, '۱ دقیقهٔ دیگر'], [59, '۵۹ دقیقهٔ دیگر']])(
    '%i minutes → %s', (m, out) => expect(humanGap(m as number)).toBe(out))

  it('rolls over into hours', () => {
    expect(humanGap(65)).toBe('۱ ساعت و ۵ دقیقهٔ دیگر')
    expect(humanGap(120)).toBe('۲ ساعتِ دیگر')
  })

  it('never shows a negative or a zero countdown', () => {
    expect(humanGap(0)).toBe('همین حالا')
    expect(humanGap(-5)).toBe('همین حالا')
  })
})

describe('rushMessage — what the owner actually reads', () => {
  it('says the place in the queue AND when the round comes', () => {
    const m = rushMessage(1, nr())
    expect(m).toContain('نفرِ اول')
    expect(m).toContain('ساعتِ ۱۰:۲۳')
    expect(m).toContain('۱۹ دقیقهٔ دیگر')
  })

  it('does not invent a second arrival time for the second sheet', () => {
    // the round works through the queue in one visit — «نوبتِ دوم», not «+1 hour»
    const m = rushMessage(2, nr())
    expect(m).toContain('نفرِ ۲')
    expect(m).toContain('ساعتِ ۱۰:۲۳')
  })

  it('admits when the time is only assumed', () => {
    expect(rushMessage(1, nr({ basis: 'assumed' }))).toContain('تخمینی')
  })

  it('does not hedge once it has actually been watched', () => {
    expect(rushMessage(1, nr({ basis: 'observed' }))).not.toContain('تخمینی')
  })

  it('warns instead of counting down when the routine has gone quiet', () => {
    const m = rushMessage(1, nr({ basis: 'stale', last_seen: iso(3, 23) }))
    expect(m).toContain('سر نزده')
    expect(m).not.toContain('دقیقهٔ دیگر')       // no false promise
    expect(m).toContain('۰۳:۲۳')
  })

  it('still says something useful when the server sent nothing', () => {
    expect(rushMessage(1, null)).toContain('بازبینیِ بعدی')
    expect(rushMessage(1, { ...nr(), at: '' })).toContain('بازبینیِ بعدی')
  })
})
