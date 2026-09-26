// v138 — the Credit File Summary as a REAL, EDITABLE Word document (.docx).
//
// Built from the neutral spec that `sheetSpec.ts` reads out of the live sheet,
// so Word and Excel always show the same thing the print preview shows, and a
// section added to the form tomorrow exports itself.
//
// Direction rules, inherited from the letter/voucher chain (v74→v83, binding —
// they were each paid for by a broken document):
//   • this is an ENGLISH, LTR form. Every paragraph stays LTR-base, so digit
//     groups (amounts, account numbers, dates) can never reorder (v79).
//   • NO w:rtl element anywhere — in OOXML its mere PRESENCE means ON (v78).
//   • NO embedding controls (v74/v78).
//   • Persian text (a partner's name, «املاک» in a band) sits inside an LTR-base
//     paragraph unmarked (v81); the Unicode bidi algorithm renders that segment
//     right-to-left by itself, which is exactly what the browser does on screen.
// docProps carries the build tag so a problematic file names the build that made
// it (v77) — deploy-lag debugging without guesswork.
import {
  AlignmentType, BorderStyle, Document, Packer, Paragraph, ShadingType, Table,
  TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} from 'docx'
import type { SheetBlock, SheetCell, SheetSpec } from './sheetSpec'

const FONT = 'Arial'
// A4 portrait minus the page's own 7 mm print margins → the usable width in
// twips, so the Word table fills the same measure as the printed sheet.
const PAGE_MARGIN_TW = 397            // 7 mm
const USABLE_TW = 11906 - PAGE_MARGIN_TW * 2

const HALF = (pt: number) => Math.round(pt * 2)   // docx sizes are half-points
const BODY_PT = 8
const BAND_PT = 9
const TITLE_PT = 11

const run = (text: string, pt: number, bold?: boolean) =>
  new TextRun({
    text,
    font: { ascii: FONT, hAnsi: FONT, cs: FONT } as any,
    size: HALF(pt), sizeComplexScript: HALF(pt),
    bold, boldComplexScript: bold,
  } as any)

const ALIGN = {
  left: AlignmentType.LEFT, center: AlignmentType.CENTER, right: AlignmentType.RIGHT,
} as const

const P = (text: string, pt: number, o: { bold?: boolean; align?: keyof typeof ALIGN } = {}) =>
  new Paragraph({
    alignment: ALIGN[o.align || 'left'],
    spacing: { before: 0, after: 0, line: Math.round(pt * 1.25 * 20), lineRule: 'auto' } as any,
    children: [run(text || '', pt, o.bold)],
  })

const THIN = { style: BorderStyle.SINGLE, size: 6, color: '000000' }
const allThin = { top: THIN, bottom: THIN, left: THIN, right: THIN } as any

function td(c: SheetCell, pt: number, widthTw?: number): TableCell {
  // A blank paragraph is required — an empty cell with no child is invalid OOXML
  // and Word repairs the file (it opens with a "we found a problem" banner).
  const text = c.text || ' '
  return new TableCell({
    children: [P(text, pt, { bold: c.bold, align: c.align })],
    columnSpan: c.span > 1 ? c.span : undefined,
    rowSpan: c.rowSpan,
    width: widthTw ? { size: widthTw, type: WidthType.DXA } : undefined,
    borders: allThin,
    shading: c.fill ? { fill: c.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 20, bottom: 20, left: 50, right: 50 },
  })
}

function tableOf(rows: SheetCell[][], widths: number[]): Table {
  // proportions → twips, with the rounding drift pushed into the last column so
  // the row total is exact (Word silently rescales a table whose columns do not
  // add up, which shows as columns that do not line up with the screen)
  const cols = widths.map((w) => Math.max(240, Math.round(w * USABLE_TW)))
  const drift = USABLE_TW - cols.reduce((s, w) => s + w, 0)
  if (cols.length) cols[cols.length - 1] += drift

  return new Table({
    width: { size: USABLE_TW, type: WidthType.DXA },
    columnWidths: cols,
    borders: allThin,
    rows: rows.map((cells) => {
      let col = 0
      return new TableRow({
        cantSplit: true,           // a form row split across pages is unreadable
        children: cells.map((c) => {
          const w = cols.slice(col, col + c.span).reduce((s, x) => s + x, 0)
          col += c.span
          return td(c, c.fill === undefined ? BODY_PT : BAND_PT, w)
        }),
      })
    }),
  })
}

function blockToElements(b: SheetBlock): (Table | Paragraph)[] {
  if (b.kind === 'table') return [tableOf(b.rows, b.widths), spacer()]

  if (b.kind === 'banner') {
    const left = Math.round(USABLE_TW * 0.72)
    const lbl = Math.round(USABLE_TW * 0.09)
    const val = USABLE_TW - left - lbl
    return [new Table({
      width: { size: USABLE_TW, type: WidthType.DXA },
      columnWidths: [left, lbl, val],
      borders: allThin,
      rows: [new TableRow({
        cantSplit: true,
        children: [
          new TableCell({
            children: [P(b.left, 10, { bold: true }), ...(b.leftSub ? [P(b.leftSub, 7)] : [])],
            width: { size: left, type: WidthType.DXA }, borders: allThin,
            verticalAlign: VerticalAlign.CENTER, margins: { top: 40, bottom: 40, left: 60, right: 60 },
          }),
          td({ text: b.rightLabel || 'Date', span: 1, bold: true, align: 'center', fill: 'E5E7EB' }, BODY_PT, lbl),
          td({ text: b.rightValue || '', span: 1, align: 'center' }, BODY_PT, val),
        ],
      })],
    }), spacer()]
  }

  if (b.kind === 'title' || b.kind === 'line') {
    const centered = b.kind === 'title'
    return [new Table({
      width: { size: USABLE_TW, type: WidthType.DXA },
      columnWidths: [USABLE_TW],
      borders: allThin,
      rows: [new TableRow({
        cantSplit: true,
        children: [td(
          { text: b.text, span: 1, bold: true, align: centered ? 'center' : 'left' },
          centered ? TITLE_PT : BAND_PT, USABLE_TW,
        )],
      })],
    }), spacer()]
  }

  // signatures — ruled lines, no box, like the printed foot
  const half = Math.round(USABLE_TW / 2)
  const sign = (text: string, align: 'left' | 'right') => new TableCell({
    children: [P(text, BODY_PT, { bold: true, align }), P(' ', BODY_PT), P(' ', BODY_PT)],
    width: { size: half, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, left: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, right: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }, bottom: THIN } as any,
    margins: { top: 200, bottom: 20, left: 50, right: 50 },
  })
  return [new Paragraph({ spacing: { before: 300, after: 0 }, children: [] }), new Table({
    width: { size: USABLE_TW, type: WidthType.DXA },
    columnWidths: [half, USABLE_TW - half],
    rows: [new TableRow({ cantSplit: true, children: [sign(b.left, 'left'), sign(b.right, 'right')] })],
  })]
}

// Word glues consecutive tables into one unless a paragraph separates them —
// without this every section of the form merges into a single grid.
const spacer = () => new Paragraph({ spacing: { before: 0, after: 60 }, children: [] })

export async function buildSheetDocx(spec: SheetSpec, buildTag = ''): Promise<Blob> {
  const children: (Table | Paragraph)[] = []
  spec.blocks.forEach((b) => children.push(...blockToElements(b)))

  const doc = new Document({
    title: spec.title,
    description: `ALLIN1 credit-file export${buildTag ? ` — build ${buildTag}` : ''}`,
    styles: {
      default: {
        document: {
          run: { font: { ascii: FONT, hAnsi: FONT, cs: FONT }, size: HALF(BODY_PT), sizeComplexScript: HALF(BODY_PT) } as any,
          paragraph: { spacing: { after: 0 } },
        },
      },
    },
    sections: [{
      properties: { page: { margin: { top: PAGE_MARGIN_TW, bottom: PAGE_MARGIN_TW, left: PAGE_MARGIN_TW, right: PAGE_MARGIN_TW } } },
      children,
    }],
  })
  return Packer.toBlob(doc)
}
