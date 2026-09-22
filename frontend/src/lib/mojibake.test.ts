/**
 * v126 — repairing "custom PDF font encoding" mojibake in an existing letter.
 *
 * The repair runs over a letter the user already built, so the two things that
 * matter are: the text must come back EXACTLY right, and the table around it —
 * column widths, styles, merged cells — must not be touched at all.
 */
import { repairText, repairBlock, repairHtml, countGarbledHtml, looksGarbled, mightBeGarbled } from './mojibake'

// Read off a real garbled bank-statement table rendered in the app.
const REAL: [string, string][] = [
  ['Í¬¿¬»³»²¬ ÒÑ', 'Statement NO'],
  ['ß½½±«²¬ Ò¿³»', 'Account Name'],
  ['ß³±«²¬ (×ÎÎ)', 'Amount (IRR)'],
  ['Ê¿´«» Ü¿¬»', 'Value Date'],
  ['Ð®±°»®¬§ Ò±', 'Property No'],
  ['ÒÑ', 'NO'],
  ['ßÓ×Î ØÑÍÍÛ×Ò ÓÑÌßÙØ×', 'AMIR HOSSEIN MOTAGHI'],
]

describe('repairText', () => {
  it.each(REAL)('repairs %s exactly', (garbled, plain) => {
    expect(repairText(garbled)).toBe(plain)
  })

  it('reproduces the corruption from first principles (0x120 reflection)', () => {
    for (const [garbled, plain] of REAL) {
      const forged = plain.split('').map((c) => (/[A-Za-z]/.test(c) ? String.fromCodePoint(0x120 - c.charCodeAt(0)) : c)).join('')
      expect(forged).toBe(garbled)
    }
  })

  it('leaves clean Latin and Persian alone', () => {
    for (const s of ['Statement NO', 'Amount (IRR)', 'مشخصات املاک و صورت حساب', 'شمارهٔ حساب ۲۷۱۵۲۰']) {
      expect(repairText(s)).toBe(s)
    }
  })

  it('never mistakes Persian «quotes» for mojibake', () => {
    const s = 'نامِ شرکت «Alpha Trading LLC» ثبت شد'
    expect(repairText(s)).toBe(s)
    expect(looksGarbled(s)).toBe(false)
  })

  it('ignores isolated typographic characters', () => {
    for (const s of ['۳۶°C', '±۵ درصد', 'm² و m³', '5 ± 1']) expect(repairText(s)).toBe(s)
  })
})

describe('repairBlock', () => {
  it('judges each cell of a pipe-separated block on its own', () => {
    expect(repairBlock('نامِ مشتری | ß½½±«²¬ Ò¿³» | ۱۲۳۴')).toBe('نامِ مشتری | Account Name | ۱۲۳۴')
  })

  it('leaves numbers and dates untouched', () => {
    const s = '182/4/567/2026 | 14/09/2026 | 4,819,650 | 56'
    expect(repairBlock(s)).toBe(s)
  })
})

describe('repairHtml', () => {
  const table =
    '<table class="tblw" style="width:96%">' +
    '<tr><th style="width:12%">ÒÑ</th><th style="width:30%">ß½½±«²¬ Ò¿³»</th><th>ß³±«²¬ (×ÎÎ)</th></tr>' +
    '<tr><td>1</td><td colspan="1">ßÓ×Î ØÑÍÍÛ×Ò ÓÑÌßÙØ×</td><td>4,819,650</td></tr>' +
    '</table>'

  it('repairs every garbled cell', () => {
    const { html, fixed } = repairHtml(table)
    expect(fixed).toBe(4)
    expect(html).toContain('>NO<')
    expect(html).toContain('>Account Name<')
    expect(html).toContain('>Amount (IRR)<')
    expect(html).toContain('>AMIR HOSSEIN MOTAGHI<')
  })

  it('does not touch the table structure, widths or styles', () => {
    const { html } = repairHtml(table)
    expect(html).toContain('class="tblw"')
    expect(html).toContain('width:96%')
    expect(html).toContain('width:12%')
    expect(html).toContain('width:30%')
    expect(html).toContain('colspan="1"')
    expect((html.match(/<tr/g) || []).length).toBe(2)
    expect((html.match(/<t[hd]/g) || []).length).toBe(6)
  })

  it('leaves numeric cells exactly as they were', () => {
    const { html } = repairHtml(table)
    expect(html).toContain('>4,819,650<')
    expect(html).toContain('>1<')
  })

  it('returns the input unchanged when nothing is garbled', () => {
    const clean = '<table><tr><th>ردیف</th><th>شرح</th></tr><tr><td>۱</td><td>تسهیلات</td></tr></table>'
    const { html, fixed } = repairHtml(clean)
    expect(fixed).toBe(0)
    expect(html).toBe(clean)
  })

  it('is idempotent — repairing twice changes nothing more', () => {
    const once = repairHtml(table)
    const twice = repairHtml(once.html)
    expect(twice.fixed).toBe(0)
    expect(twice.html).toBe(once.html)
  })

  it('handles empty input', () => {
    expect(repairHtml('')).toEqual({ html: '', fixed: 0 })
  })
})

describe('countGarbledHtml', () => {
  it('counts what a repair would change, without changing anything', () => {
    const src = '<p>گزارشِ شعبه</p><table><tr><th>ÒÑ</th><th>ß³±«²¬ (×ÎÎ)</th></tr></table>'
    expect(countGarbledHtml(src)).toBe(2)
    expect(countGarbledHtml('<p>همه‌چیز سالم است</p>')).toBe(0)
  })
})

describe('mightBeGarbled (the cheap pre-filter)', () => {
  it('lets every real garbled string through', () => {
    for (const [garbled] of REAL) expect(mightBeGarbled(garbled)).toBe(true)
  })

  it('rejects ordinary Persian and Latin, so no DOM work is done while typing', () => {
    for (const s of [
      'مشخصات املاک و صورت حساب',
      'نامِ شرکت «Alpha Trading LLC» ثبت شد',
      'Statement NO | Account Name | 4,819,650',
      '۳۶°C و ±۵ درصد',
      '<p>گزارشِ شعبه — ۱۴۰۵/۰۶/۳۱</p>',
    ]) expect(mightBeGarbled(s)).toBe(false)
  })

  it('is consistent with the full check: anything repairable passes the filter', () => {
    const table = '<table><tr><th>ÒÑ</th></tr></table>'
    expect(mightBeGarbled(table)).toBe(true)
    expect(countGarbledHtml(table)).toBe(1)
  })
})

describe('repairHtml is safe to run repeatedly on live content', () => {
  it('reaches a fixed point after one repair (no edit loop)', () => {
    let html = '<table><tr><th>ß½½±«²¬ Ò¿³»</th></tr></table>'
    const first = repairHtml(html)
    expect(first.fixed).toBe(1)
    const second = repairHtml(first.html)
    expect(second.fixed).toBe(0)
    expect(second.html).toBe(first.html)
  })
})
