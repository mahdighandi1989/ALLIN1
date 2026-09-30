// v141 — a dragged rectangle over a screen → an ADDRESS the supervisor can walk
// back to.
//
// v150 — AND NOW THE GEOMETRY TOO, by the owner's explicit instruction: «صرفاً
// آدرسِ اون صفحه ثبت نشه بلکه مختصاتِ فوق‌العاده دقیقِ جایی که کادر کشیده شده و
// ابعاد و اینها هم ذکر بشه … شاید چیزی که دارم بهش اشاره می‌کنم مربوط به همون
// قسمتِ خاص باشه».
//
// The original note below — «a screen has no coordinates worth recording» — was
// right about ONE number and wrong as a conclusion. Raw viewport pixels really do
// point somewhere else by the time anyone looks: a different window width, a
// scrolled page, a browser zoom, and `x: 412` is meaningless. But that is an
// argument for recording the RIGHT geometry, not for recording none. So a box now
// carries four things, strongest first:
//
//   1. `anchor.path` + `anchor.rel` — the box as FRACTIONS of the element it
//      landed on. Survives resizing, responsive reflow and scrolling, because it
//      is not a pixel measurement at all. The selector is round-trip verified at
//      capture: if re-querying it does not return the same element, it is not
//      stored, because a selector that does not resolve is worse than none.
//   2. `doc` — absolute document pixels (viewport + scroll). Survives scrolling,
//      not resizing. The fallback when the anchor is gone.
//   3. `view` + `scroll` + `viewport` + `dpr` — exactly what the owner was
//      looking at, so a supervisor can reproduce the conditions.
//   4. `doc_size` — the document at capture time, which is what makes (2)
//      interpretable at all.
//
// Whoever re-places the box must say WHICH of these it used — see `placeSpot`.
// A coordinate that has silently drifted is worse than one that admits it has.
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

/** Where the box sat, measured every way that survives something different. */
export type SpotGeometry = {
  /** absolute document pixels — viewport coordinates plus the scroll offset */
  doc: Rect
  /** what the owner literally saw, in viewport pixels */
  view: Rect
  /** the page scroll when the box was drawn */
  scroll: { x: number; y: number }
  /** the window at capture time */
  viewport: { w: number; h: number }
  /** the whole document at capture time — what makes `doc` interpretable */
  doc_size: { w: number; h: number }
  /** device pixel ratio, so a retina capture is not mistaken for a huge one */
  dpr: number
  /**
   * The element the box landed on, and the box expressed as FRACTIONS of it.
   * `path` is empty when no selector round-tripped to the same element — then
   * only `doc` is usable, and the placer must say so.
   */
  anchor: {
    path: string
    /** the anchor's own document rect at capture */
    rect: Rect
    /** x/y/w/h as fractions of the anchor's box (may fall outside 0..1) */
    rel: Rect
  }
}

export type UiSpot = {
  page: string
  page_label: string
  section_id: string
  section_label: string
  /** THE load-bearing field: one string that puts a supervisor back here. */
  reopen: string
  dom_path: string
  covered_text: string
  /** kept exactly as it was — viewport pixels (v141 callers still read it) */
  rect: Rect
  viewport: { w: number; h: number }
  /** v150 — the precise record. Optional so an older client still files a sheet. */
  geometry?: SpotGeometry
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
 * A selector that can actually be queried back — unlike `domPath`, which is for
 * a human to read.
 *
 * VERIFIED, NOT ASSUMED: the caller re-queries it and keeps it only if it returns
 * the same element. A stored selector that does not resolve is worse than an
 * empty one, because the placer would trust it and land the highlight somewhere
 * arbitrary. `nth-of-type` is used rather than classes, which are generated and
 * change between builds.
 */
export function querySelectorPath(el: Element | null, maxDepth = 8): string {
  if (!el || !el.tagName) return ''
  const parts: string[] = []
  let node: Element | null = el
  while (node && parts.length < maxDepth) {
    const tag = node.tagName.toLowerCase()
    if (tag === 'html') break
    if (tag === 'body') { parts.unshift('body'); break }
    // an id ends the walk — it is unique and stable enough to anchor on
    if (node.id && /^[A-Za-z][\w-]*$/.test(node.id)) {
      parts.unshift(`#${node.id}`)
      break
    }
    const parent: Element | null = node.parentElement
    if (!parent) { parts.unshift(tag); break }
    const sameTag = Array.from(parent.children).filter((c) => c.tagName === node!.tagName)
    const idx = sameTag.indexOf(node) + 1
    parts.unshift(sameTag.length > 1 ? `${tag}:nth-of-type(${idx})` : tag)
    node = parent
  }
  return parts.join(' > ')
}

/** `querySelectorPath`, kept only if re-querying it returns the same element. */
export function verifiedSelector(el: Element | null, root?: ParentNode): string {
  if (!el) return ''
  const path = querySelectorPath(el)
  if (!path) return ''
  try {
    const scope = root ?? (typeof document !== 'undefined' ? document : null)
    if (!scope) return ''
    return scope.querySelector(path) === el ? path : ''
  } catch {
    // an unqueryable selector (exotic tag name, odd id) — treat as none
    return ''
  }
}

/**
 * Measure the box every way that survives something different.
 *
 * `rel` is the one that matters most: fractions of the anchor element survive a
 * resize, a responsive reflow and any scroll, because they are not pixels. `doc`
 * is the fallback for when the anchor is gone. Both are stored; the placer
 * chooses and reports which it used.
 */
export function measureSpot(input: {
  rect: Rect
  viewport: { w: number; h: number }
  scroll: { x: number; y: number }
  doc_size: { w: number; h: number }
  dpr: number
  anchor: Element | null
  anchorRect: Rect | null
  anchorPath: string
}): SpotGeometry {
  const { rect, scroll } = input
  const doc: Rect = {
    x: round2(rect.x + scroll.x), y: round2(rect.y + scroll.y),
    w: round2(rect.w), h: round2(rect.h),
  }
  const ar = input.anchorRect
  // a zero-sized anchor cannot carry fractions — guard rather than divide by 0
  const usable = !!(input.anchorPath && ar && ar.w > 0 && ar.h > 0)
  const rel: Rect = usable && ar
    ? {
      x: round4((doc.x - ar.x) / ar.w), y: round4((doc.y - ar.y) / ar.h),
      w: round4(doc.w / ar.w), h: round4(doc.h / ar.h),
    }
    : { x: 0, y: 0, w: 0, h: 0 }
  return {
    doc,
    view: { x: round2(rect.x), y: round2(rect.y), w: round2(rect.w), h: round2(rect.h) },
    scroll: { x: round2(scroll.x), y: round2(scroll.y) },
    viewport: input.viewport,
    doc_size: input.doc_size,
    dpr: input.dpr,
    anchor: {
      path: usable ? input.anchorPath : '',
      rect: ar && usable ? { x: round2(ar.x), y: round2(ar.y), w: round2(ar.w), h: round2(ar.h) }
        : { x: 0, y: 0, w: 0, h: 0 },
      rel,
    },
  }
}

const round2 = (n: number) => Math.round(n * 100) / 100
const round4 = (n: number) => Math.round(n * 10000) / 10000

/** How a placement was arrived at — shown to the owner, never hidden. */
export type Placement = {
  rect: Rect
  /** `anchor` = re-measured from the element · `document` = stored page pixels */
  basis: 'anchor' | 'document'
  /** true when the anchor was gone and the position may have drifted */
  approximate: boolean
}

/**
 * Put a stored box back on the page, in DOCUMENT coordinates.
 *
 * Prefers the anchor: re-measuring the element and applying the stored fractions
 * follows the content wherever the layout has since put it. Falls back to the
 * stored document pixels, and SAYS it did — a highlight that has quietly drifted
 * would send the reader to the wrong control with full confidence.
 */
export function placeSpot(
  geom: SpotGeometry | null | undefined,
  lookup?: (sel: string) => { x: number; y: number; w: number; h: number } | null,
): Placement | null {
  if (!geom) return null
  const path = geom.anchor?.path
  if (path && lookup) {
    const now = lookup(path)
    if (now && now.w > 0 && now.h > 0) {
      const rel = geom.anchor.rel
      return {
        rect: {
          x: now.x + rel.x * now.w, y: now.y + rel.y * now.h,
          w: rel.w * now.w, h: rel.h * now.h,
        },
        basis: 'anchor',
        approximate: false,
      }
    }
  }
  if (!geom.doc || geom.doc.w <= 0 || geom.doc.h <= 0) return null
  return { rect: { ...geom.doc }, basis: 'document', approximate: true }
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
  /** v150 — supplied by the browser caller; omitted in tests that only need the address */
  geometry?: SpotGeometry
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
    ...(input.geometry ? { geometry: input.geometry } : {}),
  }
}

/** The geometry as one line a human can read — used on the sheet and in tooltips. */
export function geometryLabel(g: SpotGeometry | null | undefined): string {
  if (!g) return ''
  const d = g.doc
  const size = `${Math.round(d.w)}×${Math.round(d.h)}`
  const at = `x=${Math.round(d.x)} y=${Math.round(d.y)}`
  const win = `پنجره ${g.viewport.w}×${g.viewport.h}`
  const dpr = g.dpr && g.dpr !== 1 ? ` · dpr ${g.dpr}` : ''
  return `${size} پیکسل در ${at} (مختصاتِ سند) · ${win}${dpr}`
}

/** How a sheet's address reads on one line. */
export function spotAddress(s: Pick<UiSpot, 'page_label' | 'section_label' | 'reopen'>): string {
  return s.section_label ? `${s.page_label} ← ${s.section_label}` : s.page_label
}

/**
 * One spelling for a route, so two spellings of the same page are one page.
 *
 * v150 — this exists because the highlights did not appear and the reason was a
 * slash. The static export serves `/dashboard/`, so `usePathname()` returns
 * `/dashboard/`, while a sheet stored a moment earlier — or by any other code
 * path — says `/dashboard`. Comparing the raw strings quietly answered «a
 * different page», and the highlight was simply never drawn. Case is levelled
 * too: a route is not two routes because of capitalisation.
 */
export function normalizePath(p: string | null | undefined): string {
  const raw = (p || '').trim()
  if (!raw) return '/'
  const [path] = raw.split(/[?#]/)
  const cut = path.replace(/\/+$/, '')
  return (cut || '/').toLowerCase()
}

/** Are these the same page, whatever the trailing slash or case? */
export function samePage(a: string | null | undefined, b: string | null | undefined): boolean {
  return normalizePath(a) === normalizePath(b)
}

/** Does a stored sheet belong to the section being rendered?
 *
 *  The section part is compared exactly — `#filters` and `#Filters` are two
 *  different anchors a page author chose — but the route part is normalised. */
export function matchesSpot(reopen: string | undefined, want: string): boolean {
  if (!reopen) return false
  if (reopen === want) return true
  const [ra, rb] = [reopen, want].map((v) => {
    const i = v.indexOf('#')
    return i === -1 ? [v, ''] : [v.slice(0, i), v.slice(i)]
  })
  return ra[1] === rb[1] && samePage(ra[0], rb[0])
}

// v165 — ONE SHEET OUT OF A STACK, WITHOUT POINTING THE CAMERA AT IT.
//
// «الان مثلا از یه فرم چند صفحه ای اسکرین گرفتم فقط یه قسمت از یه صفحه، تو
// اسکرین و عکس ثبت شده همه صفحات داره نشون میده که لزومی نداره و فقط همون صفحه
// باید باشه».
//
// The obvious fix — rasterise the sheet instead of the surface — is WRONG, and a
// real browser said so. html-to-image re-renders the node inside an SVG
// foreignObject, and the deeper the node, the more of the page's layout context
// it loses: pointed at one `.psheet`, Chromium dropped the heading and the
// paragraph outright and pushed the table 240px off the right edge, while the
// very same rasteriser pointed at the surface rendered all three sheets
// perfectly. A picture that is itself wrong cannot be rescued by any amount of
// coordinate arithmetic.
//
// So the camera stays where v153 put it — on the whole surface, which renders
// faithfully — and the SHEET is cut out of the finished picture afterwards. The
// owner gets the one page they pointed at, drawn correctly.
//
// A sheet is a page of paper on screen. Sheets opt in with `data-report-page`;
// the selectors of the existing printable pages are listed too, so they work
// without being edited one by one. A screen that is not a stack of sheets has no
// crop and is captured whole, exactly as v153 decided.
export const PAGE_SEL =
  '[data-report-page], .psheet, .lsheet, .csheet, .ol-page, .sn-page, #cf-sheet'

/** The element to rasterise: the whole reportable surface, else the element itself. */
export function pickCaptureTarget(
  el: Element | null | undefined,
  doc: ParentNode = document,
): HTMLElement | null {
  const surface = el?.closest?.('[data-report-surface]')
  if (surface) return surface as HTMLElement
  return (doc.querySelector('[data-report-surface]') ?? el ?? null) as HTMLElement | null
}

/**
 * The sheet to cut the finished picture down to, or null when this screen is not
 * a stack of sheets — in which case the whole capture is kept.
 *
 * Never returns a sheet that is not inside the captured target: cropping to
 * something outside the picture would cut out empty space.
 */
export function pickCropSheet(
  el: Element | null | undefined,
  target: Element | null | undefined,
): HTMLElement | null {
  const sheet = el?.closest?.(PAGE_SEL) as HTMLElement | null
  if (!sheet || !target) return null
  if (sheet === target || !target.contains(sheet)) return null
  return sheet
}
