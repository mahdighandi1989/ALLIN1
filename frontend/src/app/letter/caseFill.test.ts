/**
 * «پر کردن از پروفایلِ حساب» offers, it never overwrites.
 *
 * The owner asked for the report to fill itself from the account's profile. The
 * dangerous version of that feature is the one that also RESETS what they have
 * already written — press it once too often, or after typing, and an hour's work
 * is gone with no undo and no warning. So every test below is about what the
 * filler must LEAVE ALONE.
 */
import { fillCaseBody, fillCaseSubject } from './caseFill'
import { caseReportBody, CASE_SUBJECT } from './caseTemplate'

const PREFILL = {
  fields: {
    company_name: 'AGHA TRADING FZE', established_year: '1997', licence_no: '79',
    free_zone: 'عجمان', activity: 'تجارت عمومی', manager_name: 'مسعود آقا',
    account_open_date: '18/01/1998',
    subject_entity: 'موسسه AGHA TRADING FZE', subject_account: '301432', subject_branch: 'عجمان',
  },
  tables: {
    partners: [{ name: 'مسعود آقا', national_id: '4709861676', share: '100% - ایرانی', role: 'مدیر صاحب امضا' }],
    collaterals: [
      { type: 'چک درهمی', reference_no: '490462', amount: '-/380.000' },
      { type: 'ضمانت شخصی', reference_no: 'فرم 127', amount: 'به میزان بدهی' },
    ],
  },
}

const text = (h: string) => h.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ')

describe('filling the case report from the account profile', () => {
  it('fills the narrative blanks', () => {
    const r = fillCaseBody(caseReportBody(), PREFILL)
    const t = text(r.html)
    expect(t).toContain('AGHA TRADING FZE')
    expect(t).toContain('1997')
    expect(t).toContain('مسعود آقا')
    expect(t).toContain('18/01/1998')
    expect(r.fields).toBeGreaterThanOrEqual(6)
  })

  it('fills a table it finds empty', () => {
    const r = fillCaseBody(caseReportBody(), PREFILL)
    expect(text(r.html)).toContain('4709861676')
    expect(r.rows).toBe(3)
  })

  it('resizes rows to the data: grows past the blanks, drops spare blanks', () => {
    const many = { tables: { collaterals: [1, 2, 3, 4, 5].map((n) => ({ type: 't' + n, reference_no: 'r', amount: '1' })) } }
    const rows = (h: string, k: string) => (new DOMParser().parseFromString(`<div>${h}</div>`, 'text/html')
      .querySelector(`table[data-cr="${k}"] tbody`) as HTMLTableSectionElement).rows.length
    expect(rows(fillCaseBody(caseReportBody(), many).html, 'collaterals')).toBe(5)
    const one = { tables: { collaterals: [{ type: 'x', reference_no: 'r', amount: '1' }] } }
    expect(rows(fillCaseBody(caseReportBody(), one).html, 'collaterals')).toBe(1)
  })

  it('NEVER overwrites a narrative blank the writer already filled', () => {
    const once = fillCaseBody(caseReportBody(), PREFILL).html
    const edited = once.replace('AGHA TRADING FZE', 'نامِ دستیِ من')
    const twice = fillCaseBody(edited, PREFILL)
    expect(text(twice.html)).toContain('نامِ دستیِ من')
    expect(text(twice.html)).not.toContain('AGHA TRADING FZE')
    expect(twice.fields).toBe(0)
  })

  it('NEVER replaces rows the writer has typed into', () => {
    const body = caseReportBody().replace(
      '<table data-cr="partners"><thead>',
      '<table data-cr="partners" data-x="1"><thead>')
    const typed = body.replace(/(<table data-cr="partners"[\s\S]*?<tbody>)<tr>/,
      '$1<tr><td>شریکی که خودم نوشتم</td><td><br></td><td><br></td><td><br></td></tr><tr>')
    const r = fillCaseBody(typed, PREFILL)
    expect(text(r.html)).toContain('شریکی که خودم نوشتم')
    expect(text(r.html)).not.toContain('4709861676')
    expect(r.skipped).toContain('partners')
  })

  it('is safe to press twice — the second press changes nothing', () => {
    const once = fillCaseBody(caseReportBody(), PREFILL)
    const twice = fillCaseBody(once.html, PREFILL)
    expect(twice.fields).toBe(0)
    expect(twice.rows).toBe(0)
    expect(text(twice.html)).toEqual(text(once.html))
  })

  it('does nothing at all when the profile has nothing', () => {
    const before = caseReportBody()
    const r = fillCaseBody(before, { fields: {}, tables: {} })
    expect(r.fields).toBe(0)
    expect(r.rows).toBe(0)
    expect(text(r.html)).toEqual(text(before))
  })

  it('leaves a blank alone when the profile has no value for it', () => {
    const r = fillCaseBody(caseReportBody(), { fields: { company_name: 'x' }, tables: {} })
    expect(text(r.html)).toContain('.....')     // the other blanks still show dots
  })

  it('escapes what it inserts, so a name cannot carry markup into the letter', () => {
    const r = fillCaseBody(caseReportBody(), {
      fields: {}, tables: { partners: [{ name: '<b>bold</b>', national_id: '', share: '', role: '' }] },
    })
    expect(r.html).toContain('&lt;b&gt;bold&lt;/b&gt;')
    expect(r.html).not.toContain('<b>bold</b>')
  })

  it('ignores a table name the template does not have', () => {
    const r = fillCaseBody(caseReportBody(), { fields: {}, tables: { nonesuch: [{ a: 'b' }] } })
    expect(r.rows).toBe(0)
  })
})

describe('the subject line', () => {
  it('is rebuilt from the account while it is still the placeholder', () => {
    const out = fillCaseSubject(CASE_SUBJECT, PREFILL.fields)
    expect(out).toContain('301432')
    expect(out).toContain('موسسه AGHA TRADING FZE')
  })

  it('is left alone once the writer has written it', () => {
    const mine = 'بـدهـی شرکتِ من حـسـاب شـمـاره ۱۲۳ نـزد شـعبـه دبی'
    expect(fillCaseSubject(mine, PREFILL.fields)).toBe(mine)
  })

  it('keeps the placeholder dots for whatever the profile does not know', () => {
    const out = fillCaseSubject(CASE_SUBJECT, { subject_account: '301432' })
    expect(out).toContain('301432')
    expect(out).toContain('..........')
  })
})
