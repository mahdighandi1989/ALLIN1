// Build the letter as a REAL, EDITABLE Word document (.docx): every field and
// paragraph is actual text (B Nazanin, RTL, justified), tables are real Word
// tables (borders, header shading, merges, row heights, alignment), inline
// images keep their crop (baked onto a canvas), the letterhead lives in the
// Word header/footer with native «صفحه X از Y» page numbers, attachment tables
// get their own portrait/landscape sections, and behind-text floats become
// floating behind-document images. Loaded lazily from the letter page.
import {
  AlignmentType, BorderStyle, Document, Footer, Header, HorizontalPositionRelativeFrom,
  ImageRun, PageNumber, PageOrientation, Packer, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, TextWrappingType, VerticalAlign, VerticalPositionRelativeFrom, WidthType,
} from 'docx'
import { LH_LOGO, LH_NAME, LH_FOOTER } from './letterhead'

const PX2EMU = 9525          // 96dpi px → EMU
const PX2TW = 15             // 96dpi px → twips (px * 72/96 * 20)
const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const fa = (n: number | string) => String(n).replace(/[0-9]/g, (d) => FA_DIGITS[+d])

export type WordExportArgs = {
  // stamped into docProps (description) so a problematic file tells us WHICH
  // deployed build produced it — deploy-lag debugging without guesswork
  buildTag?: string
  f: Record<string, string>
  labels: Record<string, string>
  L: Record<string, { x: number; y: number; w: number; h?: number; size?: number }>
  attTables: { id: string; title: string; html: string }[]
  attMeta: Record<string, { land: boolean }>
  floats: { id: string; kind: string; html: string; x: number; y: number; w: number; w0: number; page: number }[]
  pageW: number
  pageH: number
  bodyFontPt: number
  // renders a float's html at width w → PNG data-url (uses the page's live CSS)
  renderFloatPng: (html: string, w: number) => Promise<{ png: string; h: number }>
}

const hasPersian = (t: string) => /[\u0600-\u06FF]/.test(t)
// Inside Persian text, ASCII digits must become REAL Persian digits: Word picks
// a Latin fallback font for them (they rendered western/slanted), while the
// letter's B Nazanin shows them Persian-shaped — real ۰-۹ codepoints match the
// letter's look in every Word configuration.
const faDigitsIf = (t: string, on: boolean) => (on ? t.replace(/[0-9]/g, (d) => FA_DIGITS[+d]) : t)
const b64bytes = (dataUrl: string) => Uint8Array.from(atob(dataUrl.split(',')[1]), (c) => c.charCodeAt(0))
// Guard a purely Latin/numeric value (serial, date, phone ext) with LRM marks —
// Word's own zero-width bidi marks — so its segment order never flips inside an
// RTL paragraph. (U+2066/2069 isolates would be more precise, but Word renders
// them as visible LRI/PDI boxes; LRM is invisible and is what Word itself uses.)
// v74 (owner: «در Word همه‌چیز برعکس است»): the page shows the serial/date/ext
// inside a REAL dir="ltr" isolate. The old LRM pair was NOT an isolate — the
// space-separated numeric segments still reordered right-to-left inside the
// RTL paragraph, so Word displayed the MIRROR of the letter
// («2026 / 403 / 4 / 182» with 2026 beside the label instead of 182 on the
// far left). LRE…PDF (U+202A/202C) is a true directional embedding — the
// same semantics as the page's dir="ltr" span — and unlike LRI/PDI Word
// renders it invisibly. Digit CODEPOINTS stay Latin exactly like the page
// (B Nazanin draws them Persian-shaped in Word just as in the browser).
// v77: the owner's v76 file PROVED Word ignores both the LRE/PDF embedding
// and w:rtl=false for segment ordering. LRM (U+200E) is different — not an
// embedding control but a real invisible STRONG-LTR character, honored by
// every bidi engine Word ever shipped. Flanking every non-digit separator
// with LRMs makes each '/', dash and space sit BETWEEN two strong-L chars,
// so UAX#9 N1 locks the whole value left-to-right — «182 / 4 / … / 2026»
// keeps 182 on the far left exactly like the page. Embedding kept as a
// harmless extra layer for engines that do honor it.
const LRM = '\u200E'
const ltrIsolate = (t: string) =>
  '\u202A' + LRM + (t || '').replace(/([^0-9]+)/g, (m) => LRM + m + LRM) + LRM + '\u202C'
// NB: per-run rightToLeft is an OVERRIDE in Word — putting it on mixed runs
// reversed dates («2026/07/06» → «06/07/2026»). The paragraph's bidirectional
// flag gives the RTL base; character order is then resolved by the standard
// bidi algorithm, exactly like the browser renders the letter.
const mkRun = (text: string, font: string, half: number, o: { bold?: boolean; italics?: boolean; underline?: boolean; ltrRun?: boolean } = {}) =>
  new TextRun({
    text,
    font: { ascii: font, hAnsi: font, cs: font } as any,
    size: half, sizeComplexScript: half,
    bold: o.bold, boldComplexScript: o.bold,
    italics: o.italics, italicsComplexScript: o.italics,
    underline: o.underline ? {} : undefined,
    // ltrRun: the Word-NATIVE marking of an LTR value inside an RTL paragraph
    // (<w:rtl w:val="0">) — Word's own bidi engine ignores plain control marks
    // for segment ordering (owner's Word screenshot: serial still mirrored with
    // the LRM pair), but honors the explicit run direction, symmetric to the
    // v46 lesson where rightToLeft:true force-REVERSED a date.
    rightToLeft: o.ltrRun === true ? false : undefined,
  } as any)
const plainText = (h: string) => { const d = document.createElement('div'); d.innerHTML = h || ''; return (d.textContent || '').replace(/\s+/g, ' ').trim() }
// like plainText but keeps <br>/<div>/<p> boundaries as separate lines (multi-recipient رونوشت)
const plainLines = (h: string) => {
  const d = document.createElement('div')
  d.innerHTML = (h || '').replace(/<br\s*\/?>/gi, '\n').replace(/<\/(div|p)>/gi, '\n')
  return (d.textContent || '').split('\n').map((s) => s.replace(/\s+/g, ' ').trim()).filter(Boolean)
}

// ---------- inline images: bake the imgcrop window onto a canvas ----------
type ImgMap = Map<HTMLElement, { bytes: Uint8Array; w: number; h: number }>
async function bakeImages(root: HTMLElement): Promise<ImgMap> {
  const out: ImgMap = new Map()
  const wraps = Array.from(root.querySelectorAll('.imgcrop')) as HTMLElement[]
  const loose = (Array.from(root.querySelectorAll('img')) as HTMLImageElement[]).filter((im) => !im.closest('.imgcrop'))
  const px = (v: string) => parseFloat((v || '').replace('px', '')) || 0
  const load = (src: string) => new Promise<HTMLImageElement>((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src })
  for (const wrap of wraps) {
    const imgEl = wrap.querySelector('img') as HTMLImageElement | null
    if (!imgEl) continue
    try {
      const im = await load(imgEl.src)
      const W = Math.max(8, Math.round(px(wrap.style.width) || im.naturalWidth))
      const H = Math.max(8, Math.round(px(wrap.style.height) || im.naturalHeight))
      const iw = px(imgEl.style.width) || W, ih = px(imgEl.style.height) || H
      const ml = px(imgEl.style.marginLeft), mt = px(imgEl.style.marginTop)
      const cv = document.createElement('canvas'); cv.width = W * 2; cv.height = H * 2
      const g = cv.getContext('2d')!
      g.scale(2, 2)
      g.drawImage(im, ml, mt, iw, ih)
      out.set(wrap, { bytes: b64bytes(cv.toDataURL('image/png')), w: W, h: H })
    } catch { /* skip broken image */ }
  }
  for (const imgEl of loose) {
    try {
      const im = await load(imgEl.src)
      const W = Math.round(imgEl.getBoundingClientRect().width || px(imgEl.style.width) || im.naturalWidth)
      const H = Math.round(imgEl.getBoundingClientRect().height || px(imgEl.style.height) || im.naturalHeight)
      out.set(imgEl, { bytes: b64bytes(imgEl.src.startsWith('data:image/png') ? imgEl.src : await (async () => { const cv = document.createElement('canvas'); cv.width = im.naturalWidth; cv.height = im.naturalHeight; cv.getContext('2d')!.drawImage(im, 0, 0); return cv.toDataURL('image/png') })()), w: Math.max(8, W), h: Math.max(8, H) })
    } catch { /* skip */ }
  }
  return out
}

// ---------- inline runs (bold/italic/underline survive; Persian font + RTL) ----------
type RunOpts = { bold?: boolean; italics?: boolean; underline?: boolean }
function inlineRuns(node: Node, font: string, half: number, st: RunOpts, imgs: ImgMap, faDig = false): (TextRun | ImageRun)[] {
  const out: (TextRun | ImageRun)[] = []
  node.childNodes.forEach((ch) => {
    if (ch.nodeType === 3) {
      const text = (ch.textContent || '').replace(/ /g, ' ')
      if (text) out.push(mkRun(faDigitsIf(text, faDig), font, half, st))
      return
    }
    if (ch.nodeType !== 1) return
    const el = ch as HTMLElement
    const baked = imgs.get(el)
    if (baked) { out.push(new ImageRun({ data: baked.bytes, transformation: { width: baked.w, height: baked.h } })); return }
    if (el.tagName === 'BR') { out.push(new TextRun({ text: '', break: 1 } as any)); return }
    const next: RunOpts = {
      bold: st.bold || el.tagName === 'B' || el.tagName === 'STRONG' || /(^|;)\s*font-weight:\s*(bold|[7-9]00)/.test(el.getAttribute('style') || ''),
      italics: st.italics || el.tagName === 'I' || el.tagName === 'EM',
      underline: st.underline || el.tagName === 'U' || /text-decoration[^;]*underline/.test(el.getAttribute('style') || ''),
    }
    out.push(...inlineRuns(el, font, half, next, imgs, faDig))
  })
  return out
}

const alignOf = (el: HTMLElement, fallback: (typeof AlignmentType)[keyof typeof AlignmentType]) => {
  const ta = (el.style.textAlign || '').toLowerCase()
  if (ta === 'center') return AlignmentType.CENTER
  if (ta === 'left') return AlignmentType.LEFT
  if (ta === 'right') return AlignmentType.RIGHT
  if (ta === 'justify') return AlignmentType.JUSTIFIED
  return fallback
}

// ---------- one HTML block → docx paragraph(s)/table ----------
function blockToDocx(el: HTMLElement, font: string, half: number, imgs: ImgMap, justify: boolean): (Paragraph | Table)[] {
  if (el.tagName === 'TABLE') return [tableToDocx(el as HTMLTableElement, font, half, imgs)]
  if (el.querySelector('table')) {
    // paste-wrapper: recurse into its children
    const out: (Paragraph | Table)[] = []
    Array.from(el.children).forEach((c) => out.push(...blockToDocx(c as HTMLElement, font, half, imgs, justify)))
    return out
  }
  if (el.tagName === 'UL' || el.tagName === 'OL') {
    return Array.from(el.querySelectorAll('li')).map((li, i) => new Paragraph({
      bidirectional: true, alignment: alignOf(el, AlignmentType.RIGHT),
      children: [mkRun(el.tagName === 'OL' ? `${fa(i + 1)}. ` : '• ', font, half),
        ...inlineRuns(li, font, half, {}, imgs, hasPersian(li.textContent || ''))],
    }))
  }
  const runs = inlineRuns(el, font, half, {}, imgs, hasPersian(el.textContent || ''))
  return [new Paragraph({
    bidirectional: true,
    alignment: alignOf(el, justify ? AlignmentType.JUSTIFIED : AlignmentType.RIGHT),
    spacing: justify ? { line: 360 } : undefined,
    children: runs.length ? runs : [mkRun('', font, half)],
  })]
}

const CELL_BORDER = { style: BorderStyle.SINGLE, size: 4, color: '222222' }
function tableToDocx(tbl: HTMLTableElement, font: string, half: number, imgs: ImgMap): Table {
  const trs = Array.from(tbl.rows)
  const nCols = Math.max(1, ...trs.map((r) => Array.from(r.cells).reduce((acc, c) => acc + (c.colSpan || 1), 0)))
  const rows = trs.map((tr) => {
    const hPx = parseFloat((tr.style.height || '').replace('px', '')) || 0
    return new TableRow({
      height: hPx ? { value: Math.round(hPx * PX2TW), rule: 'atLeast' as any } : undefined,
      children: Array.from(tr.cells).map((td) => {
        const isTh = td.tagName === 'TH'
        const wPct = /%$/.test(td.style.width || '') ? parseFloat(td.style.width) : 0
        const va = (td.style.verticalAlign || '').toLowerCase()
        const inner = td.childNodes.length ? td : null
        const para = new Paragraph({
          bidirectional: true,
          alignment: alignOf(td, isTh ? AlignmentType.CENTER : AlignmentType.RIGHT),
          children: inner ? inlineRuns(td, font, half, isTh ? { bold: true } : {}, imgs, hasPersian(td.textContent || '')) : [mkRun('', font, half)],
        })
        return new TableCell({
          children: [para],
          columnSpan: td.colSpan > 1 ? td.colSpan : undefined,
          rowSpan: td.rowSpan > 1 ? td.rowSpan : undefined,
          verticalAlign: va === 'middle' ? VerticalAlign.CENTER : va === 'bottom' ? VerticalAlign.BOTTOM : VerticalAlign.TOP,
          shading: isTh ? { fill: 'F3F4F6', type: ShadingType.CLEAR, color: 'auto' } : undefined,
          width: wPct ? { size: wPct, type: WidthType.PERCENTAGE } : undefined,
          margins: { top: 40, bottom: 40, left: 80, right: 80 },
        })
      }),
    })
  })
  // custom table width (tblw --tw var) → percentage of the text column
  const tw = parseFloat((tbl.style.getPropertyValue('--tw') || '100').replace('%', '')) || 100
  return new Table({
    visuallyRightToLeft: true,
    alignment: AlignmentType.RIGHT,
    width: { size: Math.min(100, Math.max(10, tw)), type: WidthType.PERCENTAGE },
    borders: {
      top: CELL_BORDER, bottom: CELL_BORDER, left: CELL_BORDER, right: CELL_BORDER,
      insideHorizontal: CELL_BORDER, insideVertical: CELL_BORDER,
    },
    rows: rows.length ? rows : [new TableRow({ children: [new TableCell({ children: [new Paragraph('')] })] })],
    columnWidths: Array.from({ length: nCols }, () => Math.round(9026 / nCols)),
  })
}

// ---------- header/footer with the letterhead at its designed positions ----------
function letterheadHeader(L: WordExportArgs['L']) {
  const img = (data: string, box: { x: number; y: number; w: number; h?: number }) => new ImageRun({
    data: b64bytes(data),
    transformation: { width: Math.round(box.w), height: Math.round(box.h || 60) },
    floating: {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: Math.round(box.x * PX2EMU) },
      verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(box.y * PX2EMU) },
      behindDocument: true,
      wrap: { type: TextWrappingType.NONE },
    },
  })
  const kids: ImageRun[] = []
  if (L.logo) kids.push(img(LH_LOGO, L.logo as any))
  if (L.name) kids.push(img(LH_NAME, L.name as any))
  return new Header({ children: [new Paragraph({ children: kids })] })
}
function letterheadFooter(L: WordExportArgs['L'], font: string) {
  const kids: (ImageRun | TextRun)[] = []
  if (L.footer) kids.push(new ImageRun({
    data: b64bytes(LH_FOOTER),
    transformation: { width: Math.round(L.footer.w), height: Math.round(L.footer.h || 60) },
    floating: {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: Math.round(L.footer.x * PX2EMU) },
      verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(L.footer.y * PX2EMU) },
      behindDocument: true,
      wrap: { type: TextWrappingType.NONE },
    },
  }))
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER, bidirectional: true,
      children: [
        ...kids,
        mkRun('صفحه ', font, 20),
        new TextRun({ children: [PageNumber.CURRENT], font: { ascii: font, hAnsi: font, cs: font } as any, size: 20, sizeComplexScript: 20 }),
        mkRun(' از ', font, 20),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], font: { ascii: font, hAnsi: font, cs: font } as any, size: 20, sizeComplexScript: 20 }),
      ],
    })],
  })
}

// ---------- the whole document ----------
export async function buildLetterDocx(a: WordExportArgs): Promise<Blob> {
  const FONT = 'B Nazanin'
  const TITR = 'B Titr'
  const half = Math.round(a.bodyFontPt * 2)           // pt → half-points
  const bodyDiv = document.createElement('div')
  bodyDiv.innerHTML = a.f.body || ''
  const imgs = await bakeImages(bodyDiv)

  // label (Persian) + optional VALUE kept in an LTR isolate (mirrors the page's
  // dir="ltr" spans: serial line, date, phone extension never get bidi-flipped)
  const P = (text: string, opts: { bold?: boolean; align?: any; font?: string; pt?: number; ltrValue?: string } = {}) =>
    new Paragraph({
      bidirectional: true, alignment: opts.align || AlignmentType.RIGHT,
      children: [
        mkRun(text, opts.font || FONT, Math.round((opts.pt || a.bodyFontPt) * 2), { bold: opts.bold }),
        ...(opts.ltrValue != null ? [mkRun(ltrIsolate(opts.ltrValue), opts.font || FONT, Math.round((opts.pt || a.bodyFontPt) * 2), { bold: opts.bold, ltrRun: true })] : []),
      ],
    })

  // -- top block: right column (شماره/تاریخ/پیوست/طبقه‌بندی) + left column (گیرنده) --
  const lbl = (k: string) => { const t = plainText(a.labels[k] || ''); return t && !/[\s:،–-]$/.test(t) ? t + ' ' : (t ? t + ' ' : t) }
  const metaCol = [
    P(lbl('shomareh'), { pt: 12, ltrValue: `182 / 4 / ${a.f.serial || '----'} / ${a.f.year || ''}` }),
    P(lbl('tarikh'), { pt: 12, ltrValue: a.f.date || '' }),
    P(`${lbl('peyvast')}${a.f.attachment || ''}`, { pt: 12 }),
    P(`${lbl('classification')}${a.f.classification || ''}`, { pt: 11, bold: true }),
  ]
  const recCol = [
    P(plainText(a.f.recipientName) || ' ', { pt: 12, bold: true, font: TITR }),
    P(`${plainText(a.f.recipientTitle)} ${plainText(a.f.recipientDept)}`.trim() || ' ', { pt: 12, bold: true, font: TITR }),
  ]
  // the letter starts the recipient block LOWER than the شماره line — mirror
  // that stagger with blank lines derived from the letter's own layout
  const staggerPx = Math.max(0, (a.L.recName?.y ?? 0) - (a.L.shomareh?.y ?? 0))
  const nBlank = Math.min(4, Math.round(staggerPx / 26))
  for (let i = 0; i < nBlank; i++) recCol.unshift(P(' ', { pt: 10 }))
  // column order follows the letter's OWN layout: in an RTL table the FIRST cell
  // renders on the RIGHT — put whichever block the letter has on its right there.
  const recOnRight = (a.L.recName?.x ?? 480) >= (a.L.shomareh?.x ?? 30)
  const rightCol = recOnRight ? recCol : metaCol
  const leftCol = recOnRight ? metaCol : recCol
  const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }
  const topTable = new Table({
    visuallyRightToLeft: true,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder, insideHorizontal: noBorder, insideVertical: noBorder },
    rows: [new TableRow({
      children: [
        new TableCell({ children: rightCol, width: { size: 50, type: WidthType.PERCENTAGE }, borders: { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder } }),
        new TableCell({ children: leftCol, width: { size: 50, type: WidthType.PERCENTAGE }, verticalAlign: VerticalAlign.CENTER, borders: { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder } }),
      ],
    })],
  })

  const subjectPara = new Paragraph({
    bidirectional: true, alignment: AlignmentType.RIGHT,
    border: { bottom: { style: BorderStyle.DASHED, size: 4, color: '000000', space: 4 } },
    children: [mkRun(`${lbl('subject')}${plainText(a.f.subject)}`, TITR, 24, { bold: true })],
  })

  // -- body --
  const bodyBlocks: (Paragraph | Table)[] = []
  Array.from(bodyDiv.children).forEach((c) => bodyBlocks.push(...blockToDocx(c as HTMLElement, FONT, half, imgs, true)))
  if (!bodyDiv.children.length && (bodyDiv.textContent || '').trim()) bodyBlocks.push(P(bodyDiv.textContent || ''))

  // -- behind-text floats → floating behind-document images (anchored to page) --
  const floatRuns: ImageRun[] = []
  for (const fl of a.floats) {
    try {
      const r = await a.renderFloatPng(fl.html, fl.w)
      floatRuns.push(new ImageRun({
        data: b64bytes(r.png),
        transformation: { width: Math.round(fl.w), height: Math.round(r.h) },
        floating: {
          horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: Math.round(fl.x * PX2EMU) },
          verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: Math.round(fl.y * PX2EMU) },
          behindDocument: true,
          wrap: { type: TextWrappingType.NONE },
        },
      }))
    } catch { /* skip failed float */ }
  }

  // -- closing --
  const copyLines = plainLines(a.f.copyTo)
  const closing = [
    P(a.f.sender || '', { bold: true, align: AlignmentType.CENTER, font: TITR, pt: 13 }),
    P(`${lbl('copyto')}${copyLines[0] || ''}`, { pt: 10 }),
    // extra recipients: one paragraph each, stacked under the first
    ...copyLines.slice(1).map((li) => P(li, { pt: 10 })),
    P(`${lbl('action')}${plainText(a.f.actionName)} ${lbl('actionExt')}`, { pt: 10, ltrValue: a.f.actionExt || '' }),
  ]

  // -- letter section margins from the designed body box --
  const mLeft = Math.round(a.L.body.x * PX2TW)
  const mRight = Math.round((a.pageW - (a.L.body.x + a.L.body.w)) * PX2TW)
  const mTop = Math.round(Math.max(120, a.L.besmele?.y ?? 110) * PX2TW)

  const sections: any[] = [{
    properties: {
      page: {
        margin: { top: mTop, bottom: Math.round((a.pageH - (a.L.pagenum?.y ?? a.pageH - 100)) * PX2TW), left: mLeft, right: mRight, header: 200, footer: 300 },
      },
    },
    headers: { default: letterheadHeader(a.L) },
    footers: { default: letterheadFooter(a.L, FONT) },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, children: [...floatRuns, mkRun(plainText(a.labels.besmele || '') || 'بسمه تعالی', FONT, 26)] }),
      topTable,
      subjectPara,
      P(' ', { pt: 6 }),
      ...bodyBlocks,
      P(' ', { pt: 8 }),
      ...closing,
    ],
  }]

  // -- attachment tables: own sections with per-page orientation --
  for (let i = 0; i < a.attTables.length; i++) {
    const t = a.attTables[i]
    const land = !!a.attMeta[t.id]?.land
    const attDiv = document.createElement('div')
    attDiv.innerHTML = t.html
    const attImgs = await bakeImages(attDiv)
    const tblEl = attDiv.querySelector('table') as HTMLTableElement | null
    sections.push({
      properties: {
        page: {
          size: land ? { orientation: PageOrientation.LANDSCAPE } : {},
          margin: { top: 1100, bottom: 900, left: 850, right: 850, header: 200, footer: 300 },
        },
      },
      headers: { default: letterheadHeader(a.L) },
      footers: { default: letterheadFooter(a.L, FONT) },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, bidirectional: true,
          children: [mkRun(`جدول ${fa(i + 1)} پیوست${plainText(t.title) ? ` — ${plainText(t.title)}` : ''}`, TITR, 28, { bold: true })],
        }),
        P(' ', { pt: 6 }),
        tblEl ? tableToDocx(tblEl, FONT, half, attImgs) : P(''),
      ],
    })
  }

  const doc = new Document({
    description: `ALLIN1 letter export — build ${a.buildTag || '?'}`,
    styles: { default: { document: { run: { font: { ascii: FONT, hAnsi: FONT, cs: FONT }, size: half, sizeComplexScript: half } as any } } },
    sections,
  })
  return Packer.toBlob(doc)
}
