// v141 — a dragged rectangle over a screen → an ADDRESS the supervisor can walk
// back to.
//
// A screen has no coordinates worth recording: pixel positions change with the
// window, so storing them would hand the supervisor a number that points
// somewhere else by the time it looks. What is stored is the way BACK — which
// page, which section, one string that reopens it, and the text the owner's
// rectangle actually covered.
//
// Screens mark themselves with two data attributes, so nothing here has to know
// the names of the app's pages:
//
//     data-report-surface="/customers"   data-report-surface-label="مشتریان"
//     data-report-section="filters"      data-report-section-label="فیلترها"
//
// Adding a screen to the reportable set is one attribute; a screen that forgets
// them still files a usable sheet — one that says «جایی در رابط» and carries the
// DOM path, which is enough to find it.
//
// Pure on purpose: it takes elements and returns the record, so a test can put a
// fake DOM in front of it.

export type Rect = { x: number; y: number; w: number; h: number }

export type UiSpot = {
  page: string
  page_label: string
  section_id: string
  section_label: string
  /** THE load-bearing field: one string that puts a supervisor back here. */
  reopen: string
  dom_path: string
  covered_text: string
  rect: Rect
  viewport: { w: number; h: number }
}

export const CROP_MIN_PX = 24
const MAX_TEXT = 600
const JOIN = ' · '
const MAX_DEPTH = 4

function attrUp(el: Element | null, name: string): { el: Element; value: string } | null {
  let node: Element | null = el
  while (node) {
    const v = node.getAttribute?.(name)
    if (v) return { el: node, value: v }
    node = node.parentElement
  }
  return null
}

/** `section#filters > div.row > button` — short, and enough to find. */
export function domPath(el: Element | null, depth = 4): string {
  const parts: string[] = []
  let node: Element | null = el
  while (node && parts.length < depth) {
    const tag = node.tagName.toLowerCase()
    if (tag === 'body' || tag === 'html') break
    const id = node.id ? `#${node.id}` : ''
    const cls = !id && typeof node.className === 'string' && node.className.trim()
      ? `.${node.className.trim().split(/\s+/).slice(0, 2).join('.')}`
      : ''
    parts.unshift(`${tag}${id}${cls}`)
    node = node.parentElement
  }
  return parts.join(' > ')
}

/**
 * The visible text of what was covered, collapsed and capped.
 *
 * `textContent` on its own runs neighbours together — a filter bar came out as
 * «جستجونوع حسابشعبه», which is unreadable and therefore useless. So the tree is
 * walked and each level's children are joined with a separator, down to a small
 * depth: deep enough to reach the rows of a table, shallow enough not to split a
 * sentence into words.
 */
export function visibleText(el: Element | null, depth = MAX_DEPTH): string {
  if (!el) return ''
  const flat = (el.textContent ?? '').replace(/\s+/g, ' ').trim()
  const kids = Array.from(el.children ?? [])
  const raw = depth > 0 && kids.length > 1
    ? kids.map((k) => visibleText(k, depth - 1)).filter(Boolean).join(JOIN)
    : flat
  return raw.length > MAX_TEXT ? `${raw.slice(0, MAX_TEXT)}…` : raw
}

export function resolveSpot(input: {
  rect: Rect
  viewport: { w: number; h: number }
  stack: readonly Element[]
}): UiSpot {
  const innermost = input.stack[0] ?? null
  const surface = attrUp(innermost, 'data-report-surface')
  const section = attrUp(innermost, 'data-report-section')
  const page = surface?.value ?? 'ui'
  const sectionId = section?.value ?? ''
  // The reopen key is `page#section`, or just the page when it has no sections.
  // Deliberately the same shape a URL fragment uses, so the supervisor's tool
  // has nothing to translate.
  const reopen = sectionId ? `${page}#${sectionId}` : page
  // The text comes from the SECTION when the rectangle landed on one: the
  // innermost element under a 200-pixel box is usually a <span>, and «۲۷۶» on
  // its own tells a supervisor nothing.
  const textFrom = section?.el ?? surface?.el ?? innermost
  return {
    page,
    page_label: surface?.el.getAttribute('data-report-surface-label') ?? 'جایی در رابط',
    section_id: sectionId,
    section_label: section?.el.getAttribute('data-report-section-label') ?? '',
    reopen,
    dom_path: domPath(innermost),
    covered_text: visibleText(textFrom),
    rect: input.rect,
    viewport: input.viewport,
  }
}

/** How a sheet's address reads on one line. */
export function spotAddress(s: Pick<UiSpot, 'page_label' | 'section_label' | 'reopen'>): string {
  return s.section_label ? `${s.page_label} ← ${s.section_label}` : s.page_label
}

/** Does a stored sheet belong to the section being rendered? */
export function matchesSpot(reopen: string | undefined, want: string): boolean {
  return !!reopen && reopen === want
}
