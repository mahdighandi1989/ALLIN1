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
import {
  BRANCH_SENDERS, CASE_BRANCHES, HOUSE_SENDERS, branchBySender, branchFor, paperOf,
} from './caseLetterhead'

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

  it('names a branch we hold no paper for, but gives it no paper', () => {
    // v170 — these ARE real branches and the letter must be able to name and
    // sign them («شعب دیگه رو هم اضافه کن»). What they must NOT do is borrow
    // another branch's letterhead: printing Ajman's telephone on a Sharjah
    // letter is worse than printing the regional office's.
    for (const other of ['BUR DUBAI', '2533', 'SHARJAH - 2776', 'HEAD OFFICE', 'AL AIN']) {
      const b = branchFor(other)
      expect(b).not.toBeNull()
      expect(paperOf(b)).toBeNull()
    }
  })

  it('does not let a short alias match something unrelated', () => {
    expect(branchFor('TEHRAN')).toBeNull()
    expect(branchFor('عنوان نامه')).toBeNull()
    expect(branchFor('1234567890')).toBeNull()
  })
})

describe('the signature line names the branch, with its code', () => {
  // «اون شعبه سوق مرشد اشتباه و اونجا باید مرشد بازار نوشته بشه و کد هر شعبه هم
  // بعد از یه علامت _ نوشته بشه مثلا مرشد بازار 2898»
  it('reads «name - code»', () => {
    for (const b of CASE_BRANCHES) expect(b.sender).toBe(`${b.faName} - ${b.code}`)
  })

  it('names Murshid Bazar the way the bank says it, not «سوق المرشد»', () => {
    expect(branchFor('2898')!.sender).toBe('مرشد بازار - 2898')
  })

  it('still matches a record that spells it the Arabic way', () => {
    expect(branchFor('سوق المرشد')!.code).toBe('2898')
  })
})

describe('the signature line chooses the paper', () => {
  // «با تغییر اون قسمت در انتهای نامه از لیست هم باید سربرگ و فوتر مناسب همون
  // شعبه بشن» — the account only pre-selects the signatory; this is what decides.
  it('finds the branch a signature line names', () => {
    expect(branchBySender('المکتوم - 2624')!.code).toBe('2624')
    expect(branchBySender('عجمان - 2900')!.code).toBe('2900')
  })

  it('every offered sender resolves back to its own branch', () => {
    for (const b of CASE_BRANCHES) expect(branchBySender(b.sender)).toBe(b)
  })

  it('a house signatory is not a branch — that is the facilities paper', () => {
    for (const h of HOUSE_SENDERS) expect(branchBySender(h)).toBeNull()
  })

  it('an old letter\'s free-text signatory does not crash or guess', () => {
    for (const junk of ['', '   ', 'شعبهٔ سوق المرشد', 'whatever', null, undefined])
      expect(branchBySender(junk as any)).toBeNull()
  })
})

describe('paperOf — a branch prints on its own paper, or on the default', () => {
  it('gives the three images for a branch whose scans we hold', () => {
    const p = paperOf(branchFor('2898'))!
    expect(p.logo).toMatch(/^data:image\/png;base64,/)
    expect(p.name).toMatch(/^data:image\/png;base64,/)
    expect(p.footer).toMatch(/^data:image\/png;base64,/)
  })

  it('gives NOTHING for a branch whose paper has not been supplied', () => {
    // Listed and signable, but we hold no scans — the letter must fall back to
    // the facilities set, never borrow another branch's telephone.
    for (const code of ['2533', '4350', '2776', '2690', '1741', '3535'])
      expect(paperOf(branchFor(code))).toBeNull()
  })

  it('treats a half-supplied branch as having none', () => {
    expect(paperOf({ ...CASE_BRANCHES[0], footer: undefined } as any)).toBeNull()
    expect(paperOf({ ...CASE_BRANCHES[0], name: undefined } as any)).toBeNull()
  })

  it('is safe with nothing at all', () => {
    expect(paperOf(null)).toBeNull()
    expect(paperOf(undefined)).toBeNull()
  })

  it('carries the branch box for the one branch shaped unlike the rest', () => {
    // Ajman prints its emblem beside its name; with the square default box it
    // renders correct-but-tiny, which is what the owner saw.
    expect(paperOf(branchFor('2900'))!.logoBox).toEqual({ x: 14, y: 3, w: 47, h: 18 })
    expect(paperOf(branchFor('2898'))!.logoBox).toBeUndefined()
  })
})

describe('every branch entry is usable', () => {
  it.each(CASE_BRANCHES.map((b) => [b.enName, b] as const))(
    '%s is complete, and complete-or-absent about its paper', (_en, b) => {
      expect(b.code).toMatch(/^\d{3,}$/)
      expect(b.faName.trim()).not.toBe('')
      expect(b.enName.trim()).not.toBe('')
      expect(b.aliases.length).toBeGreaterThan(1)
      const bits = [b.logo, b.name, b.footer].filter(Boolean)
      expect([0, 3]).toContain(bits.length)      // all three, or none
      for (const x of bits) expect(x!.length).toBeGreaterThan(2000)
    })

  it('no two branches share a footer — each carries its own phone and fax', () => {
    const feet = CASE_BRANCHES.map((b) => b.footer).filter(Boolean)
    expect(new Set(feet).size).toBe(feet.length)
  })

  it('no two branches share a code or a sender', () => {
    expect(new Set(CASE_BRANCHES.map((b) => b.code)).size).toBe(CASE_BRANCHES.length)
    expect(new Set(CASE_BRANCHES.map((b) => b.sender)).size).toBe(CASE_BRANCHES.length)
  })

  it('offers every branch in the dropdown — adding one here adds it there', () => {
    expect(BRANCH_SENDERS).toEqual(CASE_BRANCHES.map((b) => b.sender))
  })

  it('covers every branch the rest of the system knows about', () => {
    // The branch-code table is duplicated in three other modules; a branch the
    // system can import but the letter cannot name is a gap the owner finds.
    for (const code of ['2533', '2690', '2776', '2900', '4350', '2624', '2898', '1741', '3535'])
      expect(CASE_BRANCHES.some((b) => b.code === code)).toBe(true)
  })
})
