/**
 * v151 — every FormData upload must ask for `multipart/form-data`.
 *
 * WHY THIS TEST EXISTS, AND WHY IT IS A SOURCE SCAN
 * -------------------------------------------------
 * The shared axios client defaults to `Content-Type: application/json`, and
 * axios only fills in the multipart boundary when the caller has NOT set a type.
 * So a FormData post that omits the header goes up as JSON with no boundary, the
 * server's parser finds no parts, and the request fails with «Field required» —
 * which is exactly what happened to the owner on the first real use of the
 * inspection upload, after the backend tests were green. Those tests built the
 * multipart body themselves and never exercised the browser's call.
 *
 * A per-function mock would only ever cover the functions someone remembered to
 * mock. Scanning the source covers the NEXT upload too, which is the one that
 * will otherwise repeat this.
 */
import fs from 'fs'
import path from 'path'

const SRC = fs.readFileSync(path.join(__dirname, 'api.ts'), 'utf8')

/**
 * Each `new FormData()` and the code that sends it.
 *
 * Deliberately NOT a clever regex over the whole call: a pattern with a length
 * window silently stops matching when someone adds a comment, and a scan that
 * quietly matches nothing passes forever. Each FormData simply owns the source
 * up to the next one (or the end), which cannot fall out of step.
 */
function uploadBlocks(source: string): { line: number; text: string }[] {
  const marks: number[] = []
  const re = /new FormData\(\)/g
  let m: RegExpExecArray | null
  while ((m = re.exec(source))) marks.push(m.index)
  return marks.map((start, i) => ({
    line: source.slice(0, start).split('\n').length,
    text: source.slice(start, marks[i + 1] ?? Math.min(source.length, start + 2000)),
  }))
}

describe('FormData uploads', () => {
  it('finds the uploads in the client at all (the scan must not be vacuous)', () => {
    // a test that silently matches nothing would pass forever while the bug it
    // guards walks straight back in
    expect(uploadBlocks(SRC).length).toBeGreaterThanOrEqual(5)
  })

  it('every one of them sets multipart/form-data', () => {
    const missing = uploadBlocks(SRC)
      .filter((b) => !b.text.includes('multipart/form-data'))
      .map((b) => `api.ts:${b.line}`)
    expect(missing).toEqual([])
  })

  it('the inspection upload specifically — the one the owner hit', () => {
    // Matching on «contains /api/inspection/» is NOT enough: a block runs to the
    // next FormData, so an earlier upload's block also contains this text along
    // with its OWN header, and the assertion passed while the bug was present.
    // Verified by reintroducing the bug: this now fails, that did not.
    const block = uploadBlocks(SRC).find((b) => b.text.includes('/api/inspection/${id}/files`'))
    expect(block).toBeDefined()
    const call = block!.text.slice(block!.text.indexOf('/api/inspection/${id}/files`'))
    const upToEndOfCall = call.slice(0, call.indexOf('return data'))
    expect(upToEndOfCall).toContain("'Content-Type': 'multipart/form-data'")
  })
})

describe('the shared client is why this is needed', () => {
  it('still defaults to application/json', () => {
    // If this ever stops being true, the rule above can be relaxed — but until
    // then, «no header» means «JSON», not «let the browser decide».
    const ax = fs.readFileSync(path.join(__dirname, 'axios.ts'), 'utf8')
    expect(ax).toContain("'Content-Type': 'application/json'")
  })
})
