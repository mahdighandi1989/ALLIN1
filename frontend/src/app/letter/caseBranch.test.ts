/**
 * v169 — which branch's paper a case report is printed on.
 *
 * «در صورتی که اکانتی که وارد کردم برای اون شعب بود این سربرگ ها ظاهر بشه و در
 * حالت عادی اگر چیزی نزده بودم سربرگ تسهیلات باشه».
 *
 * The stored branch is FREE TEXT — imported from spreadsheets over years, so it
 * can be a code, an English name, «AL MAKTOUM - 2624», or nothing at all. The
 * matching has to survive that, and it must never guess: a legal report on the
 * wrong branch's paper carries the wrong telephone and fax to a court.
 */
import { BRANCH_SENDERS, CASE_BRANCHES, branchFor } from './caseLetterhead'

describe('branchFor — the paper the account is on', () => {
  it.each([
    ['2898', 'MURSHID BAZAR BRANCH'],
    ['2624', 'AL MAKTOUM BRANCH'],
    ['2900', 'AJMAN BRANCH'],
  ])('matches the bare branch code %s', (code, en) => {
    expect(branchFor(code)!.enName).toBe(en)
  })

  it.each([
    ['MURSHID BAZAR', 'MURSHID BAZAR BRANCH'],
    ['Murshid Bazar - 2898', 'MURSHID BAZAR BRANCH'],
    ['AL MAKTOUM', 'AL MAKTOUM BRANCH'],
    ['al maktoum - 2624', 'AL MAKTOUM BRANCH'],
    ['AJMAN', 'AJMAN BRANCH'],
    ['شعبه عجمان', 'AJMAN BRANCH'],
    ['فرع المكتوم', 'AL MAKTOUM BRANCH'],
  ])('matches the name as the record actually writes it: %s', (raw, en) => {
    expect(branchFor(raw)!.enName).toBe(en)
  })

  it('matches the Arabic and the Persian spelling of المكتوم/المکتوم', () => {
    // ك (Arabic kaf) and ک (Persian keheh) are DIFFERENT characters, and imported
    // records contain both — one spelling matching and the other not would be a
    // silent, account-by-account failure.
    expect(branchFor('المكتوم')!.code).toBe('2624')
    expect(branchFor('المکتوم')!.code).toBe('2624')
  })

  it('falls back to the usual paper when there is no account', () => {
    expect(branchFor('')).toBeNull()
    expect(branchFor(null)).toBeNull()
    expect(branchFor(undefined)).toBeNull()
    expect(branchFor('   ')).toBeNull()
  })

  it('falls back rather than guessing at a branch we have no paper for', () => {
    // Bur Dubai, Sharjah, Abu Dhabi… are real branches whose letterhead we do
    // NOT hold. Printing Ajman's phone number on one would be worse than
    // printing the regional office's.
    for (const other of ['BUR DUBAI', '2533', 'SHARJAH - 2776', 'HEAD OFFICE', '3535'])
      expect(branchFor(other)).toBeNull()
  })

  it('does not let a short alias match something unrelated', () => {
    expect(branchFor('AL AIN')).toBeNull()
    expect(branchFor('ABU DHABI')).toBeNull()
  })
})

describe('every branch is complete', () => {
  it.each(CASE_BRANCHES.map((b) => [b.enName, b] as const))(
    '%s has its own paper and its own footer', (_en, b) => {
      for (const k of ['logo', 'name', 'footer'] as const) {
        expect(b[k]).toMatch(/^data:image\/png;base64,/)
        expect(b[k].length).toBeGreaterThan(2000)
      }
      expect(b.sender.trim()).not.toBe('')
      expect(b.code).toMatch(/^\d{3,}$/)
    })

  it('no two branches share a footer — each carries its own phone and fax', () => {
    const feet = CASE_BRANCHES.map((b) => b.footer)
    expect(new Set(feet).size).toBe(feet.length)
  })

  it('no two branches share a code or a sender', () => {
    expect(new Set(CASE_BRANCHES.map((b) => b.code)).size).toBe(CASE_BRANCHES.length)
    expect(new Set(CASE_BRANCHES.map((b) => b.sender)).size).toBe(CASE_BRANCHES.length)
  })

  it('offers every branch in the dropdown — adding one here adds it there', () => {
    expect(BRANCH_SENDERS).toEqual(CASE_BRANCHES.map((b) => b.sender))
  })
})
