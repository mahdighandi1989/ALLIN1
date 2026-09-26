/**
 * v138 — the Credit File Summary exports are built from whatever the sheet is
 * actually showing. That makes the DOM reader load-bearing: if it mis-reads the
 * grid, BOTH the Word and the Excel file are wrong, and the officer only finds
 * out after sending the file.
 *
 * The two things worth pinning are the ones a hand-written exporter gets wrong:
 *   • the «tools» column exists only on screen, so every band cell that spans
 *     "6 columns" must come out spanning 5 once it is gone;
 *   • .pr-hide is the «حذف از پرینت» feature — exporting such a row would put
 *     back a row the officer deliberately removed.
 */
import { readSheetSpec, sheetFileBase } from './sheetSpec'

function mount(html: string): HTMLElement {
  const root = document.createElement('div')
  root.id = 'cf-sheet'
  root.innerHTML = html
  document.body.appendChild(root)
  return root
}

afterEach(() => { document.body.innerHTML = '' })

const table = (rows: string) => `<table class="cf"><tbody>${rows}</tbody></table>`

describe('readSheetSpec — the printed sheet, not the screen', () => {
  it('drops the screen-only tools column and shrinks the band span to match', () => {
    const root = mount(table(`
      <tr><td class="band" colspan="4">Facility Details</td></tr>
      <tr class="hdr"><td>S/No.</td><td>Description</td><td>Amount</td><td class="tools">حذف</td></tr>
      <tr><td class="sn">1</td><td class="desc">Overdraft</td><td><input value="1,000"></td><td class="tools"><button>x</button></td></tr>
    `))
    const spec = readSheetSpec(root, '351394')
    const t = spec.blocks[0] as any
    expect(t.kind).toBe('table')
    expect(t.widths).toHaveLength(3)                 // tools column gone
    expect(t.rows[0][0].span).toBe(3)                // band was colspan=4
    expect(t.rows[1].map((c: any) => c.text)).toEqual(['S/No.', 'Description', 'Amount'])
    expect(t.rows[2].map((c: any) => c.text)).toEqual(['1', 'Overdraft', '1,000'])
  })

  it('never exports a row the officer removed from the print', () => {
    const root = mount(table(`
      <tr class="hdr"><td>S/No.</td><td>Description</td></tr>
      <tr><td class="sn">1</td><td>Kept</td></tr>
      <tr class="pr-hide"><td class="sn">2</td><td>Removed</td></tr>
    `))
    const t = readSheetSpec(root) as any
    const texts = JSON.stringify(t.blocks[0].rows)
    expect(texts).toContain('Kept')
    expect(texts).not.toContain('Removed')
  })

  it('renders widgets the way paper shows them', () => {
    const root = mount(table(`
      <tr>
        <td><input value="Abu Amir Furnishing"></td>
        <td><textarea>line one</textarea></td>
        <td><input type="checkbox" checked><label>GUARANTOR/S</label></td>
        <td><input type="checkbox"><label>PARTNER/S</label></td>
      </tr>
    `))
    // jsdom does not reflect a value attribute into .value for textarea children
    ;(document.querySelector('textarea') as HTMLTextAreaElement).value = 'line one'
    const t = readSheetSpec(root) as any
    const row = t.blocks[0].rows[0].map((c: any) => c.text)
    expect(row[0]).toBe('Abu Amir Furnishing')
    expect(row[1]).toBe('line one')
    expect(row[2]).toBe('☑ GUARANTOR/S')
    expect(row[3]).toBe('☐ PARTNER/S')
  })

  it('substitutes the print-only text for the on-screen select', () => {
    const root = mount(table(`
      <tr><td>
        <select class="screen-only"><option value="x" selected>— dropdown —</option></select>
        <span class="print-only">Overdraft</span>
      </td></tr>
    `))
    const t = readSheetSpec(root) as any
    expect(t.blocks[0].rows[0][0].text).toBe('Overdraft')
  })

  it('carries the band / header / key fills so the file looks like the form', () => {
    const root = mount(table(`
      <tr><td class="band" colspan="2">Account Details</td></tr>
      <tr class="hdr"><td>S/No.</td><td>Description</td></tr>
      <tr><td class="sn">1</td><td><input value="v"></td></tr>
    `))
    const t = readSheetSpec(root) as any
    expect(t.blocks[0].rows[0][0].fill).toBe('C7CCD3')
    expect(t.blocks[0].rows[1][0].fill).toBe('DDE1E7')
    expect(t.blocks[0].rows[2][0].fill).toBe('EEF1F5')
    expect(t.blocks[0].rows[2][1].fill).toBeUndefined()   // a value cell is white
  })

  it('reads the banner, title, branch line and signatures in page order', () => {
    const root = mount(`
      <div class="cf-row-top">
        <div class="cf-logo"><b>BANK SADERAT IRAN</b><span>U.A.E.</span></div>
        <div class="cf-date"><div class="l">Date</div><input value="26/09/2026"></div>
      </div>
      <div class="cf-title">CREDIT FILE SUMMARY (Corporate)</div>
      <div class="cf-branch">Branch Code and Name: <input value="2690"></div>
      ${table('<tr><td>x</td></tr>')}
      <div class="cf-foot"><div class="cf-sign">Prepared By:<div class="line"> </div></div><div class="cf-sign">Authorized:<div class="line"> </div></div></div>
    `)
    const spec = readSheetSpec(root, '351394')
    expect(spec.blocks.map((b: any) => b.kind))
      .toEqual(['banner', 'title', 'line', 'table', 'signatures'])
    expect(spec.title).toBe('CREDIT FILE SUMMARY (Corporate)')
    expect((spec.blocks[0] as any).rightValue).toBe('26/09/2026')
    expect((spec.blocks[2] as any).text).toContain('2690')
    expect((spec.blocks[4] as any).left).toBe('Prepared By:')
  })

  it('keeps rowspans, and skips a cell that lived only in dropped columns', () => {
    const root = mount(table(`
      <tr><td rowspan="2">merged</td><td>a</td><td class="tools">t</td></tr>
      <tr><td>b</td><td class="tools">t</td></tr>
    `))
    const t = readSheetSpec(root) as any
    expect(t.rows).toBeUndefined()
    expect(t.blocks[0].rows[0][0].rowSpan).toBe(2)
    expect(t.blocks[0].rows[0]).toHaveLength(2)          // tools cell dropped
    expect(t.blocks[0].rows[1]).toHaveLength(1)          // only "b" survives
  })

  it('names the file after the form, the account and the date', () => {
    const root = mount('<div class="cf-title">CREDIT FILE SUMMARY (Retail)</div>')
    const base = sheetFileBase(readSheetSpec(root, '351394'))
    expect(base).toMatch(/^CreditFile-Retail-351394-\d{8}$/)
  })

  it('survives an account number with path characters in it', () => {
    const root = mount('<div class="cf-title">CREDIT FILE SUMMARY (Corporate)</div>')
    expect(sheetFileBase(readSheetSpec(root, '../../etc/passwd'))).not.toContain('/')
  })
})
