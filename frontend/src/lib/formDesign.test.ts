/**
 * v131 — layout-editor and print contracts.
 *
 * These are RENDER guarantees a green build cannot catch, so they are pinned
 * against the source: the settings panel must not burst out of its own box, the
 * voucher's tinted heading must survive printing, and every part of a slip must
 * be grabbable with the mouse.
 *
 * The panel fix itself was verified by rendering the real shipped CSS in headless
 * Chromium and measuring the boxes — the rules below are what that measurement
 * showed to be necessary.
 */
import { readFileSync } from 'fs'
import { join } from 'path'

const FD = readFileSync(join(__dirname, 'formDesign.tsx'), 'utf8')
const VOUCHER = readFileSync(join(__dirname, '..', 'app', 'voucher', 'page.tsx'), 'utf8')

const rule = (src: string, sel: string) => {
  const i = src.indexOf(sel)
  if (i < 0) return ''
  return src.slice(i, src.indexOf('}', i) + 1).replace(/\s+/g, ' ')
}

describe('the «تنظیمِ فیلد» panel cannot overflow', () => {
  it('caps its width to the viewport and scrolls instead of spilling', () => {
    const r = rule(FD, '.mv-pp{')
    expect(r).toContain('box-sizing:border-box')
    expect(r).toMatch(/width:min\(\d+px,calc\(100vw - \d+px\)\)/)
    expect(r).toContain('max-height:calc(100vh - 110px)')
    expect(r).toContain('overflow:auto')
  })

  it('releases every level of the flex chain, not just the input', () => {
    // A flex item's automatic minimum is its content's min-content size, and an
    // <input> carries a large intrinsic width — measured in Chromium, min-width:0
    // on the input ALONE left each row ~240px inside a 206px box, which is what
    // pushed the second column off the panel.
    expect(rule(FD, '.mv-pp .r{')).toContain('min-width:0')
    expect(rule(FD, '.mv-pp .two{')).toContain('min-width:0')
    expect(FD).toContain('.mv-pp .two .r{flex:1 1 0;min-width:0}')
    const inp = rule(FD, '.mv-pp input{')
    expect(inp).toContain('min-width:0')
    expect(inp).toContain('box-sizing:border-box')
  })

  it('lets the label shrink instead of pinning it to a fixed width', () => {
    const lbl = rule(FD, '.mv-pp .r>label{')
    expect(lbl).not.toMatch(/width:\d+px/)
    expect(lbl).toContain('text-overflow:ellipsis')
  })
})

describe('group drag — moving one part carries the ones below it', () => {
  it('each Movable exposes its id to the DOM so document order is authoritative', () => {
    expect(FD).toContain('data-mvid={id}')
    expect(FD).toContain("querySelectorAll<HTMLElement>('[data-mvid]')")
  })

  it('followers are the parts AFTER the dragged one, scoped to its group', () => {
    expect(FD).toContain(".closest('.mv-group')")
    expect(FD).toContain('all.slice(at + 1)')
  })

  it('vertical movement carries followers; horizontal stays local', () => {
    // the follower patch only ever sets dy — dx must not shove the whole column
    expect(FD).toMatch(/patch\[fid\] = \{ dy: origin\[fid\] \+ ddy \}/)
  })

  it('Alt is the escape hatch for moving a single part', () => {
    expect(FD).toContain('e.altKey')
  })

  it('applies the whole group in ONE state update', () => {
    expect(FD).toContain('setBoxes')
    expect(FD).toMatch(/setBoxes:\s*\(patch: Record<string, Partial<Boxn>>\) => void/)
  })
})

describe('the voucher slips', () => {
  it('every slip is a drag group', () => {
    const groups = VOUCHER.match(/className="vch mv-group"/g) || []
    expect(groups.length).toBe(3)          // normal, reversal, IRR
  })

  it('the parts that used to be un-grabbable are movable now', () => {
    for (const id of ['logo', 'aclbl', 'reflbl', 'sigprep', 'sigauth']) {
      expect(VOUCHER).toContain(`M('${id}'`)
    }
  })

  it('no signature block is left outside the editor', () => {
    const feet = VOUCHER.match(/<div className="vch-foot">([\s\S]*?)<\/div>\s*<\/div>/g) || []
    expect(feet.length).toBeGreaterThanOrEqual(3)
    for (const f of feet) expect(f).toContain("M('sig")
  })
})

describe('printing keeps the heading tinted', () => {
  it('the banner asks for its colour to be printed', () => {
    const r = rule(VOUCHER, '.vch-banner {')
    expect(r).toContain('background: #CCCCFF')
    expect(r).toContain('print-color-adjust: exact')
    expect(r).toContain('-webkit-print-color-adjust: exact')
  })

  it('the whole printed sheet keeps its colours', () => {
    expect(VOUCHER).toMatch(/#voucher-print, #voucher-print \* \{[^}]*print-color-adjust: exact !important/)
  })

  it('the tint is a light shade, so black-and-white prints a grey band not a black bar', () => {
    const m = VOUCHER.match(/\.vch-banner \{ background: #([0-9A-Fa-f]{6})/)
    expect(m).toBeTruthy()
    const hex = m![1]
    const lum = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16)).reduce((a, b) => a + b, 0) / 3
    expect(lum).toBeGreaterThan(170)     // clearly lighter than mid-grey
    expect(lum).toBeLessThan(250)        // but clearly not white
  })
})
