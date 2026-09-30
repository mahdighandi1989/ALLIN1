// «پر کردن از پروفایلِ حساب» — offer what the database already knows.
//
// The report's §1 narrative and its partner/facility/collateral tables repeat
// facts that already live on the customer's profile. Typing them a second time
// is how the report and the profile drift apart, so this fills them in.
//
// THE RULE, and the reason this is a pure function rather than a re-render:
// it OFFERS, it never overwrites. A narrative blank is filled only while it still
// holds its dots; a table is filled only while every one of its body cells is
// empty. Press it twice, press it after typing, press it on a half-finished
// report — nothing you wrote is touched. That is testable here at every boundary,
// which it would not be if this rebuilt the body from the template.

export type Prefill = {
  fields?: Record<string, string>
  tables?: Record<string, Record<string, string>[]>
}

/** Column order per table, matching caseTemplate's headers left-to-right. */
const COLS: Record<string, string[]> = {
  partners: ['name', 'national_id', 'share', 'role'],
  facilities_granted: ['type', 'amount', 'grant_date', 'rate'],
  facilities_unsettled: ['type', 'principal', 'grant_date', 'rate'],
  collections: ['date', 'amount', 'currency', 'source', 'principal', 'interest', 'legal_cost'],
  collaterals: ['type', 'reference_no', 'amount'],
  approvals: ['authority', 'date', 'subject', 'result'],
  collateral_actions: ['type', 'amount', 'actions'],
  discounted_cheques: ['row', 'cheque_no', 'beneficiary', 'drawer', 'bank', 'amount'],
  commitments: ['subject', 'description', 'amount'],
}

/** Still a blank? i.e. empty, or nothing but the template's dots. */
// The date blanks read «..../..../....», so slashes and dashes are part of a
// placeholder too. Anything containing a digit or a letter is someone's writing
// and is left alone — hence testing what a placeholder is MADE OF rather than
// matching each placeholder's exact text.
const isBlank = (t: string) => !t.trim() || /^[.…/\-\s]+$/.test(t.trim())

/** A body cell with nothing in it (a lone <br> counts as empty). */
const cellEmpty = (td: HTMLElement) => !(td.textContent || '').trim()

export type FillResult = { html: string; fields: number; rows: number; skipped: string[] }

/**
 * Fill `html` from `data`. Returns the new HTML and what was actually done —
 * including which tables were SKIPPED because they already had content, so the
 * caller can say so instead of silently doing nothing.
 */
export function fillCaseBody(html: string, data: Prefill): FillResult {
  const doc = new DOMParser().parseFromString(`<div id="root">${html}</div>`, 'text/html')
  const root = doc.getElementById('root')
  if (!root) return { html, fields: 0, rows: 0, skipped: [] }

  let fields = 0
  const f = data.fields || {}
  root.querySelectorAll<HTMLElement>('span[data-cr]').forEach((el) => {
    const key = el.dataset.cr || ''
    const val = (f[key] || '').trim()
    if (!val) return
    if (!isBlank(el.textContent || '')) return   // the writer got there first
    el.textContent = val
    fields += 1
  })

  let rows = 0
  const skipped: string[] = []
  for (const [key, list] of Object.entries(data.tables || {})) {
    if (!Array.isArray(list) || !list.length) continue
    const table = root.querySelector<HTMLTableElement>(`table[data-cr="${key}"]`)
    if (!table) continue
    const body = table.tBodies[0]
    if (!body) continue
    const existing = Array.from(body.rows)
    const hasContent = existing.some((tr) =>
      Array.from(tr.cells).some((td) => !cellEmpty(td as HTMLElement)))
    if (hasContent) { skipped.push(key); continue }   // never clobber real rows

    const cols = COLS[key] || []
    const width = existing[0]?.cells.length || cols.length
    const made = list.map((r) => {
      const tds = Array.from({ length: width }, (_, i) => {
        const raw = cols[i] ? String(r[cols[i]] ?? '') : ''
        return `<td>${escapeHtml(raw) || '<br>'}</td>`
      })
      return `<tr>${tds.join('')}</tr>`
    })
    // Row count follows the data: the fill adds rows when the account has more
    // than the template's blanks and drops the spare blanks when it has fewer.
    body.innerHTML = made.join('')
    rows += list.length
  }
  return { html: root.innerHTML, fields, rows, skipped }
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c] as string))
}

/** The «موضوع» line, rebuilt from the account's facts — only while it is still
 *  the template's placeholder, for the same reason as the narrative blanks. */
export function fillCaseSubject(subject: string, f: Record<string, string>): string {
  const plain = subject.replace(/<[^>]*>/g, '')
  if (!/\.{3,}/.test(plain)) return subject      // already written over
  const e = (f.subject_entity || '').trim() || '..........'
  const a = (f.subject_account || '').trim() || '..........'
  const b = (f.subject_branch || '').trim() || '..........'
  return `بـدهـی ${e} حـسـاب شـمـاره ${a} نـزد شـعبـه ${b}`
}
