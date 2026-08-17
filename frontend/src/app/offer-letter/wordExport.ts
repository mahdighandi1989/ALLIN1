// Build the OFFER LETTER as a REAL, EDITABLE Word document (.docx) from the
// LIVE preview DOM (#offer-print) — every user override (layout-panel text,
// font/size/align tweaks, bold/italic/underline marks) is already applied in
// that DOM, so the export mirrors exactly what the user previewed.
//
// Direction/structure rules are the BINDING letter-page lessons
// (experiences/ai-generated-artifacts-spec-render-and-provenance-guard.md,
// v74→v83 chain) — do not "simplify" them away:
//   • NEVER emit a <w:rtl> element with a val — its mere PRESENCE means
//     rtl-ON (v78). rightToLeft:true goes ONLY on runs of purely-RTL script
//     INSIDE bidi paragraphs (v80/v81), never on runs with digits/Latin (v46).
//   • The English template stays LTR-base throughout: with an LTR paragraph
//     base, digit groups can never reorder (v79) and w:jc is literal.
//   • dir="rtl" blocks (Arabic lines of the bilingual form) become bidi
//     paragraphs whose w:jc is ALWAYS explicit and LOGICAL: visual-right ⇒
//     "left", visual-left ⇒ "right" (v79/v82 — cell defaults ≠ body defaults).
//   • NO LRE/PDF/LRI/PDI embedding controls anywhere (v74/v78 — Word draws
//     them as visible boxes/bars and ignores them for ordering anyway).
//   • Decorative rules stay REAL text (the dotted line already is), never
//     paragraph borders (v83 — not adjustable in Word).
//   • Real Word tables ONLY where the document itself shows a table (the
//     facility grid, the bilingual header/detail grids) — v83.
//   • docProps carries the build tag so a problematic file names its build
//     (v77 process lesson).
import {
  AlignmentType, BorderStyle, Document, Footer, Header, ImageRun, PageNumber,
  Packer, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  VerticalAlign, WidthType,
} from 'docx'
import { LH_LOGO, LH_NAME, LH_FOOTER } from '@/app/letter/letterhead'

const EN_FONT = 'Times New Roman'
const AR_FONT = 'Traditional Arabic'
const MM2TW = 56.7                      // 1 mm ≈ 56.7 twips
const mm = (v: number) => Math.round(v * MM2TW)
const PX2PT = 72 / 96

export type OfferWordArgs = {
  root: HTMLElement       // the live #offer-print element (dir="ltr")
  buildTag: string        // stamped into docProps description
}

// RTL scripts (Arabic/Persian/Hebrew ranges used by this form)
const rtlText = (t: string) => /[֐-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]/.test(t)
// v80: what native Word marks when an RTL user types — RTL script + neutrals
// only. v46/v78: never on digit/Latin runs, never as val="false".
const pureRtl = (t: string) => rtlText(t) && !/[0-9A-Za-z]/.test(t)

type RunSt = { bold?: boolean; italics?: boolean; underline?: boolean }

// inBidi: v81 — the run-level rtl mark is ONLY valid inside w:bidi paragraphs;
// in an LTR-base paragraph it detaches neutral separators to the line start.
const mkRun = (text: string, half: number, st: RunSt, inBidi: boolean) => {
  const font = rtlText(text) ? AR_FONT : EN_FONT
  return new TextRun({
    text,
    font: { ascii: font, hAnsi: font, cs: font } as any,
    size: half, sizeComplexScript: half,
    bold: st.bold, boldComplexScript: st.bold,
    italics: st.italics, italicsComplexScript: st.italics,
    underline: st.underline ? {} : undefined,
    rightToLeft: inBidi && pureRtl(text) ? true : undefined,
  } as any)
}

const b64bytes = (dataUrl: string) => Uint8Array.from(atob(dataUrl.split(',')[1]), (c) => c.charCodeAt(0))
const loadImg = (src: string) => new Promise<HTMLImageElement>((res, rej) => {
  const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src
})

// nearest explicit dir attribute (up to root; root is dir="ltr")
const dirOf = (el: HTMLElement, root: HTMLElement): 'ltr' | 'rtl' => {
  let n: HTMLElement | null = el
  while (n && n !== root) {
    const d = (n.getAttribute('dir') || '').toLowerCase()
    if (d === 'rtl') return 'rtl'
    if (d === 'ltr') return 'ltr'
    n = n.parentElement
  }
  return 'ltr'
}

// visual alignment from the LIVE computed style (this is what honors the
// user's layout-panel overrides), mapped later through jcBidi for RTL blocks
const visualAlign = (el: HTMLElement, dir: 'ltr' | 'rtl') => {
  const ta = (getComputedStyle(el).textAlign || '').toLowerCase()
  if (ta === 'center') return AlignmentType.CENTER
  if (ta === 'justify') return AlignmentType.JUSTIFIED
  if (ta === 'right' || ta === 'end') return AlignmentType.RIGHT
  if (ta === 'left') return AlignmentType.LEFT
  return dir === 'rtl' ? AlignmentType.RIGHT : AlignmentType.LEFT   // 'start'
}
// v79/v82 — in a bidi paragraph w:jc is LOGICAL and must ALWAYS be explicit:
// visual-right ⇒ "left" (start), visual-left ⇒ "right" (end).
const jcBidi = (a: any): any =>
  a === AlignmentType.RIGHT ? AlignmentType.LEFT : a === AlignmentType.LEFT ? AlignmentType.RIGHT : a

const halfOf = (el: HTMLElement) => {
  const px = parseFloat(getComputedStyle(el).fontSize) || 12.4
  return Math.max(12, Math.round(px * PX2PT * 2))
}
const boldOf = (el: HTMLElement) => {
  const w = getComputedStyle(el).fontWeight
  return w === 'bold' || parseInt(w, 10) >= 600
}
const underOf = (el: HTMLElement) => /underline/.test(getComputedStyle(el).textDecorationLine || (getComputedStyle(el) as any).textDecoration || '')

// ---------- inline content of one line/paragraph ----------
function inlineRuns(node: Node, half: number, st: RunSt, inBidi: boolean): TextRun[] {
  const out: TextRun[] = []
  node.childNodes.forEach((ch) => {
    if (ch.nodeType === 3) {
      const text = (ch.textContent || '').replace(/ /g, ' ')
      if (text) out.push(mkRun(text, half, st, inBidi))
      return
    }
    if (ch.nodeType !== 1) return
    const el = ch as HTMLElement
    if (el.tagName === 'BR') { out.push(new TextRun({ text: '', break: 1 } as any)); return }
    const cs = getComputedStyle(el)
    const next: RunSt = {
      bold: st.bold || cs.fontWeight === 'bold' || parseInt(cs.fontWeight, 10) >= 600,
      italics: st.italics || cs.fontStyle === 'italic',
      underline: st.underline || /underline/.test(cs.textDecorationLine || ''),
    }
    out.push(...inlineRuns(el, half, next, inBidi))
  })
  return out
}

// one flat line (no block children) → one paragraph
function lineToPara(el: HTMLElement, root: HTMLElement, opts: { spacingBeforeTw?: number } = {}): Paragraph {
  const dir = dirOf(el, root)
  const half = halfOf(el)
  const st: RunSt = { bold: boldOf(el), underline: underOf(el) }
  const runs = inlineRuns(el, half, st, dir === 'rtl')
  const a = visualAlign(el, dir)
  return new Paragraph({
    ...(dir === 'rtl' ? { bidirectional: true, alignment: jcBidi(a) } : { alignment: a }),
    spacing: {
      before: opts.spacingBeforeTw ?? undefined,
      // keep paragraphs tight like the page (line-height 1.2); justified body
      // paragraphs get a touch of breathing room
      after: 40,
    },
    children: runs.length ? runs : [mkRun(' ', half, st, false)],
  })
}

const hasBlockChildren = (el: HTMLElement) =>
  Array.from(el.children).some((c) => {
    const d = getComputedStyle(c as HTMLElement).display
    return d !== 'inline' && d !== 'inline-block' && (c as HTMLElement).tagName !== 'BR'
  })

// ---------- tables (facility grid, bilingual header/detail grids) ----------
const CELL_BORDER = { style: BorderStyle.SINGLE, size: 4, color: '000000' }
function tableToDocx(tbl: HTMLTableElement, root: HTMLElement): Table {
  const trs = Array.from(tbl.rows)
  const nCols = Math.max(1, ...trs.map((r) => Array.from(r.cells).reduce((acc, c) => acc + (c.colSpan || 1), 0)))
  const rows = trs.map((tr) => new TableRow({
    children: Array.from(tr.cells).map((td) => {
      const isTh = td.tagName === 'TH'
      const bg = getComputedStyle(td).backgroundColor
      const dark = /rgb\((\d+),\s*(\d+),\s*(\d+)/.exec(bg || '')
      const lum = dark ? (+dark[1] + +dark[2] + +dark[3]) / 3 : 255
      // one paragraph per block child (bilingual label cells stack EN over AR);
      // a flat cell becomes a single paragraph
      const paras: Paragraph[] = []
      const digits = td.querySelector('.pl-digits')
      if (digits) {
        // account-number digit boxes → plain spaced digits in an LTR paragraph
        // (an LTR base can never reorder digit groups — v79)
        const txt = Array.from(digits.children).map((s) => (s.textContent || '').trim() || '_').join(' ')
        paras.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [mkRun(txt, halfOf(td), { bold: true }, false)] }))
      } else if (hasBlockChildren(td)) {
        Array.from(td.children).forEach((c) => paras.push(lineToPara(c as HTMLElement, root)))
      } else {
        paras.push(lineToPara(td, root))
      }
      return new TableCell({
        children: paras.length ? paras : [new Paragraph('')],
        columnSpan: td.colSpan > 1 ? td.colSpan : undefined,
        rowSpan: td.rowSpan > 1 ? td.rowSpan : undefined,
        verticalAlign: VerticalAlign.CENTER,
        shading: isTh || lum < 240
          ? { fill: isTh ? 'E9E9EE' : lum < 120 ? '333333' : 'EFEFEF', type: ShadingType.CLEAR, color: 'auto' }
          : undefined,
        margins: { top: 40, bottom: 40, left: 80, right: 80 },
      })
    }),
  }))
  return new Table({
    // English document base — the table is LTR exactly like the page
    alignment: AlignmentType.CENTER,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: CELL_BORDER, bottom: CELL_BORDER, left: CELL_BORDER, right: CELL_BORDER,
      insideHorizontal: CELL_BORDER, insideVertical: CELL_BORDER,
    },
    rows: rows.length ? rows : [new TableRow({ children: [new TableCell({ children: [new Paragraph('')] })] })],
    columnWidths: Array.from({ length: nCols }, () => Math.round(9360 / nCols)),
  })
}

// invisible 2-column table for side-by-side pairs (signature row, EN|AR row):
// borderless except an optional top rule on each cell (the signature line)
const NO_BORDER = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }
function pairTable(left: Paragraph[], right: Paragraph[], topRule: boolean): Table {
  const cell = (paras: Paragraph[]) => new TableCell({
    children: paras.length ? paras : [new Paragraph('')],
    borders: {
      top: topRule ? { style: BorderStyle.SINGLE, size: 6, color: '000000' } : NO_BORDER,
      bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER,
    } as any,
    margins: { top: topRule ? 60 : 0, bottom: 0, left: 80, right: 80 },
  })
  return new Table({
    alignment: AlignmentType.CENTER,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: NO_BORDER, bottom: NO_BORDER, left: NO_BORDER, right: NO_BORDER,
      insideHorizontal: NO_BORDER, insideVertical: NO_BORDER,
    } as any,
    rows: [new TableRow({ children: [cell(left), cell(right)] })],
    columnWidths: [4680, 4680],
  })
}

// ---------- block dispatcher ----------
function blockToDocx(el: HTMLElement, root: HTMLElement): (Paragraph | Table)[] {
  const cls = el.classList
  if (cls.contains('ol-head') || cls.contains('ol-foot')) return []   // header/footer handled per-section
  if (el.tagName === 'TABLE') return [tableToDocx(el as HTMLTableElement, root)]

  // numbered terms: CSS counters don't exist in Word → REAL text numbers,
  // honoring the page-3 start offset (start=18)
  if (el.tagName === 'OL' && cls.contains('ol-terms')) {
    const start = parseInt(el.getAttribute('start') || '1', 10) || 1
    return Array.from(el.children).filter((c) => c.tagName === 'LI').map((li, i) => {
      const half = halfOf(li as HTMLElement)
      return new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { after: 50 },
        children: [
          mkRun(`${start + i}) `, half, {}, false),
          ...inlineRuns(li, half, {}, false),
        ],
      })
    })
  }

  // signature row: two spans side-by-side, each with a top rule → invisible
  // 2-col table with top-bordered cells (the native "signature line" shape)
  if (cls.contains('ol-sign')) {
    const spans = Array.from(el.children) as HTMLElement[]
    const mk = (sp?: HTMLElement) => sp && (sp.textContent || '').trim()
      ? [new Paragraph({ alignment: AlignmentType.CENTER, children: inlineRuns(sp, halfOf(sp), { bold: true }, false) })]
      : [new Paragraph('')]
    const topPx = parseFloat(getComputedStyle(el).marginTop) || 0
    const out: (Paragraph | Table)[] = []
    if (topPx > 4) out.push(new Paragraph({ spacing: { before: Math.round(topPx * 15) }, children: [] }))
    out.push(pairTable(mk(spans[0]), mk(spans[1]), true))
    return out
  }

  // page-1 signature stack: two underlined bold lines with stamp room between
  if (cls.contains('ol-sign-stack')) {
    const lines = Array.from(el.children) as HTMLElement[]
    return lines.map((ln, i) => lineToPara(ln, root, {
      spacingBeforeTw: i > 0 ? mm(14) : mm(8),
    }))
  }

  // bilingual EN|AR side-by-side line
  if (cls.contains('bi-row2')) {
    const kids = Array.from(el.children) as HTMLElement[]
    const enP = kids[0] ? [lineToPara(kids[0], root)] : []
    const arP = kids[1] ? [lineToPara(kids[1], root)] : []
    return [pairTable(enP, arP, false)]
  }

  // standalone digit boxes (outside a table cell)
  if (cls.contains('pl-digits')) {
    const txt = Array.from(el.children).map((s) => (s.textContent || '').trim() || '_').join(' ')
    return [new Paragraph({ children: [mkRun(txt, halfOf(el), { bold: true }, false)] })]
  }

  // pre-wrap securities text: keep the user's line breaks as separate paragraphs
  if (cls.contains('ol-sec')) {
    const lines = (el.textContent || '').split('\n').map((s) => s.trimEnd())
    const half = halfOf(el)
    const out = lines.filter((s, i) => s.trim() || (i > 0 && i < lines.length - 1))
      .map((s) => new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 30 }, children: [mkRun(s || ' ', half, {}, false)] }))
    return out.length ? out : [lineToPara(el, root)]
  }

  // guarantor stack and other block containers: one paragraph per block child
  if (hasBlockChildren(el)) {
    const out: (Paragraph | Table)[] = []
    Array.from(el.children).forEach((c) => out.push(...blockToDocx(c as HTMLElement, root)))
    return out
  }
  return [lineToPara(el, root)]
}

// ---------- per-section header (letterhead) & footer ----------
async function buildHeader(head: HTMLElement | null, root: HTMLElement): Promise<Header> {
  const kids: Paragraph[] = []
  if (head) {
    const logo = await loadImg(LH_LOGO)
    const name = await loadImg(LH_NAME)
    const en = head.classList.contains('ol-head--en')
    // emblem ~26mm high (en) / 16mm (bi); wordmark 64mm / 44mm wide — the same
    // proportions the page CSS uses
    const logoH = en ? 98 : 60                          // px @96dpi ≈ 26mm/16mm
    const logoW = Math.round(logoH * (logo.naturalWidth / Math.max(1, logo.naturalHeight)))
    const nameW = en ? 242 : 166                        // ≈ 64mm/44mm
    const nameH = Math.round(nameW * (name.naturalHeight / Math.max(1, name.naturalWidth)))
    if (en) {
      // logo floats at the left margin; wordmark + REF/DATE right-aligned text
      kids.push(new Paragraph({
        children: [new ImageRun({
          data: b64bytes(LH_LOGO),
          transformation: { width: logoW, height: logoH },
          floating: {
            horizontalPosition: { relative: 'margin' as any, offset: 0 },
            verticalPosition: { relative: 'paragraph' as any, offset: 0 },
            wrap: { type: 'square' as any },
          },
        } as any)],
      }))
      kids.push(new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new ImageRun({ data: b64bytes(LH_NAME), transformation: { width: nameW, height: nameH } } as any)],
      }))
      const refs = Array.from(head.querySelectorAll('.ol-refline')) as HTMLElement[]
      refs.forEach((r) => kids.push(new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: inlineRuns(r, 17, {}, false),
      })))
    } else {
      // bilingual: stacked images left; BSI code + bordered ref grid right
      kids.push(new Paragraph({ children: [new ImageRun({ data: b64bytes(LH_LOGO), transformation: { width: logoW, height: logoH } } as any)] }))
      kids.push(new Paragraph({ children: [new ImageRun({ data: b64bytes(LH_NAME), transformation: { width: nameW, height: nameH } } as any)] }))
      const bsi = head.querySelector('.ol-bsi') as HTMLElement | null
      if (bsi) kids.push(new Paragraph({ alignment: AlignmentType.RIGHT, children: inlineRuns(bsi, 15, {}, false) }))
    }
  }
  return new Header({ children: kids.length ? kids : [new Paragraph('')] })
}

async function buildFooter(en: boolean, total: number): Promise<Footer> {
  const kids: Paragraph[] = []
  if (en) {
    const banner = await loadImg(LH_FOOTER)
    const w = 560                                        // ≈ 148mm inside margins
    const h = Math.round(w * (banner.naturalHeight / Math.max(1, banner.naturalWidth)))
    kids.push(new Paragraph({
      children: [
        new TextRun({ children: [PageNumber.CURRENT], font: { ascii: 'Georgia', hAnsi: 'Georgia' } as any, size: 18 } as any),
        new TextRun({ text: ' | Page', font: { ascii: 'Georgia', hAnsi: 'Georgia' } as any, size: 18 } as any),
      ],
    }))
    kids.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({ data: b64bytes(LH_FOOTER), transformation: { width: w, height: h } } as any)],
    }))
  } else {
    kids.push(new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [
        new TextRun({ text: 'Page ', font: { ascii: 'Arial', hAnsi: 'Arial' } as any, size: 17, bold: true } as any),
        new TextRun({ children: [PageNumber.CURRENT], font: { ascii: 'Arial', hAnsi: 'Arial' } as any, size: 17, bold: true } as any),
        new TextRun({ text: ` of ${total}`, font: { ascii: 'Arial', hAnsi: 'Arial' } as any, size: 17, bold: true } as any),
      ],
    }))
  }
  return new Footer({ children: kids })
}

// ---------- the whole document ----------
export async function buildOfferDocx(a: OfferWordArgs): Promise<Blob> {
  const pages = Array.from(a.root.querySelectorAll('.ol-page')) as HTMLElement[]
  const total = pages.length
  const sections: any[] = []
  for (const page of pages) {
    const bordered = page.classList.contains('ol-page--bordered')
    const head = page.querySelector('.ol-head') as HTMLElement | null
    const en = !!page.querySelector('.ol-foot--en') || !!(head && head.classList.contains('ol-head--en'))
    const fit = (page.querySelector('.ol-fit') || page) as HTMLElement
    const children: (Paragraph | Table)[] = []
    Array.from(fit.children).forEach((c) => children.push(...blockToDocx(c as HTMLElement, a.root)))
    sections.push({
      properties: {
        page: {
          margin: { top: mm(9), bottom: mm(14), left: mm(13), right: mm(13), header: mm(5), footer: mm(5) },
          ...(bordered ? {
            borders: {
              pageBorders: { display: 'allPages', offsetFrom: 'page', zOrder: 'front' },
              pageBorderTop: { style: BorderStyle.SINGLE, size: 8, color: '111111', space: 24 },
              pageBorderBottom: { style: BorderStyle.SINGLE, size: 8, color: '111111', space: 24 },
              pageBorderLeft: { style: BorderStyle.SINGLE, size: 8, color: '111111', space: 24 },
              pageBorderRight: { style: BorderStyle.SINGLE, size: 8, color: '111111', space: 24 },
            },
          } : {}),
        },
      },
      headers: { default: await buildHeader(head, a.root) },
      footers: { default: await buildFooter(en, total) },
      children: children.length ? children : [new Paragraph('')],
    })
  }

  const doc = new Document({
    // v77 process lesson: the artefact itself names its build
    description: `ALLIN1 offer-letter export — build ${a.buildTag}`,
    styles: {
      default: {
        document: {
          run: { font: { ascii: EN_FONT, hAnsi: EN_FONT, cs: AR_FONT }, size: 19, sizeComplexScript: 19 } as any,
        },
      },
    },
    sections,
  })
  return Packer.toBlob(doc)
}
