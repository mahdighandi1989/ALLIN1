/**
 * v137 — the 📎 پیوست‌ها button must always be reachable on the letter toolbar.
 *
 * From v65 until v137 the button (and the whole attachments panel, and the AI
 * deep-extraction tool) was wrapped in `hasAttachmentMode &&`, i.e. it only
 * rendered when the letter's «پیوست : دارد/ندارد» select happened to read
 * «دارد». Opening any letter saved with «ندارد» therefore made the button
 * VANISH from between the other buttons, with nothing on screen explaining why —
 * the owner hit exactly that and asked where the attachment button had gone.
 *
 * The relationship is now the other way round: the select FOLLOWS the
 * attachments (attaching or generating one flips it to «دارد»), it never gates
 * the UI that creates them. A green build cannot catch a re-gating, so the
 * contract is pinned here against the page source.
 */
import { readFileSync } from 'fs'
import { join } from 'path'

const PAGE = readFileSync(join(__dirname, 'page.tsx'), 'utf8')

/** The JSX line that renders the toolbar button, plus the line above it. */
function buttonBlock(): string {
  const i = PAGE.indexOf('📎 پیوست‌ها')
  expect(i).toBeGreaterThan(-1)
  return PAGE.slice(Math.max(0, i - 500), i)
}

describe('letter toolbar: the attachments button is never hidden', () => {
  it('still renders the 📎 پیوست‌ها button', () => {
    expect(PAGE).toContain('📎 پیوست‌ها')
  })

  it('does not gate the button on the «پیوست» select', () => {
    // no `hasAttachmentMode &&` in the 500 chars of JSX preceding the label
    expect(buttonBlock()).not.toContain('hasAttachmentMode &&')
  })

  it('opens the panel on nothing but the open/closed state', () => {
    expect(PAGE).toContain('{attsOpen && (')
    expect(PAGE).not.toContain('hasAttachmentMode && attsOpen')
  })

  it('offers the deep-extraction tool whenever real enclosures exist', () => {
    expect(PAGE).toContain('{letterAtts.length > 0 && (')
    expect(PAGE).not.toContain('hasAttachmentMode && letterAtts.length > 0')
  })

  it('lets the «پیوست» field follow reality instead of gating it', () => {
    // the helper exists, and both creation paths call it
    expect(PAGE).toContain('const markHasAttachment = ()')
    // both creation paths call it: a real file upload and the AI generator
    const calls = PAGE.match(/^\s*markHasAttachment\(\)$/gm) || []
    expect(calls.length).toBeGreaterThanOrEqual(2)
    // and the panel's one-click fix hands it to onClick directly
    expect(PAGE).toContain('onClick={markHasAttachment}')
  })

  it('never flips the field back to «ندارد» on its own', () => {
    expect(PAGE).not.toContain("attachment: 'ندارد'")
  })
})
