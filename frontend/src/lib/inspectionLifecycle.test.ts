/**
 * v166 — THE COLOUR ON THE PAGE MUST FOLLOW THE CONVERSATION.
 *
 * Four states, one meaning each, by the owner's own description:
 *
 *   نارنجی  open      «من منتظرم»        ← a follow-up note sends it back here
 *   سبز     answered  «ناظر جواب داده»
 *   آبی     approved  «من تیک زدم»       ← the supervisor files it next round
 *   —       filed     «تمام»             ← the highlight is taken off the page
 *
 * WHY A SOURCE SCAN AND NOT A RENDER TEST
 * ---------------------------------------
 * Two things broke here, and neither was visible to a unit test of one module:
 *
 *   1. TWO PALETTES DISAGREED. The badge on the board (`TONE` in ./inspection)
 *      had answered=emerald / approved=blue; the highlight (`TONE_COLOR`) had
 *      them the other way round. Each module's own tests were green — they
 *      agreed with themselves. So this test compares the two palettes to EACH
 *      OTHER, which is the thing that was actually wrong.
 *   2. THE BOARD REFRESHED ITSELF AND TOLD NOBODY. Ticking a sheet, or writing
 *      under it, changes its colour; the overlay draws that colour on another
 *      part of the app and only refetches when told. The board called `load()`
 *      and stopped there, so the mark kept its old colour until the tab lost and
 *      regained focus — the owner reported exactly that. A scan of the board's
 *      source catches the next action that forgets, too.
 */
import fs from 'fs'
import path from 'path'
import { TONE } from './inspection'
import { TONE_COLOR, toneOf } from './inspectionHighlights'

const BOARD = fs.readFileSync(
  path.join(__dirname, '..', 'app', 'inspection', 'page.tsx'), 'utf8')

/** Tailwind's own values for the classes the badge uses. */
const TAILWIND: Record<string, string> = {
  'bg-amber-500': '245, 158, 11',
  'bg-emerald-600': '16, 185, 129',
  'bg-blue-600': '59, 130, 246',
  'bg-gray-400': '107, 114, 128',
}

describe('the badge and the highlight paint the same lifecycle', () => {
  it.each(['open', 'answered', 'approved', 'filed'])(
    'agrees on «%s»', (status) => {
      const badge = TAILWIND[TONE[status]]
      expect(badge).toBeDefined()                       // the class is one we know
      expect(TONE_COLOR[status]).toBe(badge)
    })

  it('is the owner\'s order: amber → green → blue', () => {
    expect(toneOf({ status: 'open' } as any)).toBe('245, 158, 11')
    expect(toneOf({ status: 'answered' } as any)).toBe('16, 185, 129')
    expect(toneOf({ status: 'approved' } as any)).toBe('59, 130, 246')
  })
})

describe('the board tells the highlight layer when a colour changes', () => {
  it('imports the announcement at all', () => {
    expect(BOARD).toMatch(/import\s*\{[^}]*notifySheetsChanged[^}]*\}\s*from\s*'@\/lib\/inspectionHighlights'/)
  })

  it('announces from the one place every action goes through', () => {
    // `load` is what approve / addNote / remove / attach all await; putting the
    // announcement there covers the next action too, which is the point.
    const load = BOARD.slice(BOARD.indexOf('const load = useCallback'),
                             BOARD.indexOf('useEffect(() => { void load() })'))
    expect(load).toContain('notifySheetsChanged()')
  })

  it('every action that changes a sheet ends by refreshing', () => {
    // If one of these stops calling `load()`, the announcement above never runs
    // for it — so the two halves of the contract are checked together.
    for (const fn of ['const approve =', 'const remove =', 'const addNote =']) {
      const i = BOARD.indexOf(fn)
      expect(i).toBeGreaterThan(-1)
      expect(BOARD.slice(i, i + 700)).toContain('load()')
    }
  })
})
