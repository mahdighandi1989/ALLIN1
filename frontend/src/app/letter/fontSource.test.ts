/**
 * v129 — the letter must never render with a font taken from the VIEWER'S machine.
 *
 * The 'LtrMix' face used to be declared as
 *     src: local('Times New Roman'), local('Times')
 * which asks the user's PC for a font BY NAME. On a machine where that name
 * resolves to a broken/legacy font, every Latin letter in a letter drew as
 * garbage ("Account Name" appeared as "ß½½±«²¬ Ò¿³»") even though the stored
 * text was perfectly correct — copying it out of the browser returned clean
 * ASCII. Digits looked fine only because they sit outside the unicode-range.
 *
 * This is a rendering contract that a green build cannot catch, so it is pinned
 * here: the page source must ship the font itself and must not fall back to a
 * name lookup.
 */
import { readFileSync, existsSync, statSync } from 'fs'
import { join } from 'path'

const PAGE = readFileSync(join(__dirname, 'page.tsx'), 'utf8')
const FONT_DIR = join(__dirname, '..', '..', '..', 'public', 'fonts')

describe('the letter page ships its Latin font', () => {
  it('declares LtrMix from a bundled url(), never from local()', () => {
    const faces = PAGE.match(/@font-face\{font-family:'LtrMix';[^}]*\}/g) || []
    expect(faces.length).toBeGreaterThanOrEqual(1)
    for (const face of faces) {
      expect(face).toContain("url('/fonts/ltrmix-")
      expect(face).not.toContain('local(')
    }
  })

  it('has no local() font lookup anywhere on the page', () => {
    expect(PAGE).not.toMatch(/src:\s*local\(/)
  })

  it('keeps the face limited to Latin letters, so Persian and digits are untouched', () => {
    const faces = PAGE.match(/@font-face\{font-family:'LtrMix';[^}]*\}/g) || []
    for (const face of faces) {
      expect(face).toContain('unicode-range:U+0041-005A,U+0061-007A,U+00C0-024F')
      // digits must NOT be in the range — they belong to the Persian font
      expect(face).not.toContain('U+0030-0039')
    }
  })

  it('every url() it references actually exists in public/fonts', () => {
    const urls = Array.from(PAGE.matchAll(/url\('\/fonts\/([^']+)'\)/g)).map((m) => m[1])
    expect(urls.length).toBe(3)                       // regular, bold, italic
    for (const u of urls) {
      const p = join(FONT_DIR, u)
      expect(existsSync(p)).toBe(true)
      expect(statSync(p).size).toBeGreaterThan(5000)  // a real subset, not a stub
    }
  })

  it('ships the font licence alongside the files', () => {
    expect(existsSync(join(FONT_DIR, 'LICENSE-LiberationSerif.txt'))).toBe(true)
  })
})
