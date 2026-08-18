// v105 — Contra/security-cheque voucher as a REAL, EDITABLE Word (.docx):
// both slips on one A4 page, each slip a bordered form table (the voucher's
// original home was an Excel form — cells are what the officer fills later),
// laid out like the print: kind + logo/INTERNAL VOUCHER, lavender banner,
// DATE, A/c No + amount, the OUR REF box, signature rules.
//
// Direction lessons (letter chain v74→v83, binding): the voucher is an
// ENGLISH, LTR document — every paragraph stays LTR-base (digit groups can
// never reorder, v79), w:jc is literal, NO w:rtl element anywhere (presence =
// ON, v78), NO embedding controls (v74/v78). Any Persian name lands inside an
// LTR-base paragraph unmarked (v81) — UBA renders the segment correctly.
// docProps names the build (v77).
import {
  AlignmentType, BorderStyle, Document, ImageRun, Packer, Paragraph,
  ShadingType, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} from 'docx'
import { BANK_LOGO } from './logo'

export type SlipSpec = {
  kind: string; title: string; date: string; acNo: string
  amount: string; amountBoxed: boolean
  ourRef: string; description: string; acName: string
  extraLines: string[]
}

const FONT = 'Arial'
const run = (text: string, half: number, o: { bold?: boolean } = {}) =>
  new TextRun({
    text,
    font: { ascii: FONT, hAnsi: FONT, cs: FONT } as any,
    size: half, sizeComplexScript: half,
    bold: o.bold, boldComplexScript: o.bold,
  } as any)
const P = (text: string, half: number, o: { bold?: boolean; align?: any; before?: number; after?: number } = {}) =>
  new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { before: o.before, after: o.after ?? 40 },
    children: [run(text, half, { bold: o.bold })],
  })

const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' }
const THIN = { style: BorderStyle.SINGLE, size: 8, color: '000000' }
const MED = { style: BorderStyle.SINGLE, size: 10, color: '000000' }
const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE } as any
const b64bytes = (dataUrl: string) => Uint8Array.from(atob(dataUrl.split(',')[1]), (c) => c.charCodeAt(0))
const loadImg = (src: string) => new Promise<HTMLImageElement>((res, rej) => {
  const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src
})

function cell(paras: Paragraph[], opts: {
  span?: number; borders?: any; fill?: string; width?: number; vAlign?: any
} = {}): TableCell {
  return new TableCell({
    children: paras.length ? paras : [new Paragraph('')],
    columnSpan: opts.span,
    borders: opts.borders || noBorders,
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    verticalAlign: opts.vAlign ?? VerticalAlign.CENTER,
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
  })
}

// column grid inside a slip (≈176 mm usable): [label | mid | mid | right]
const COLS = [2600, 2600, 2400, 2400]
const FULL = COLS.reduce((a, b) => a + b, 0)

async function slipTable(s: SlipSpec): Promise<Table> {
  const logo = await loadImg(BANK_LOGO)
  const logoH = 53                                    // ≈14 mm @96dpi
  const logoW = Math.round(logoH * (logo.naturalWidth / Math.max(1, logo.naturalHeight)))
  const rows: TableRow[] = []

  // header: kind (left) | logo + INTERNAL VOUCHER (right)
  rows.push(new TableRow({
    children: [
      cell([P(s.kind.toUpperCase(), 52, { bold: true })], { span: 2 }),
      cell([
        new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new ImageRun({ data: b64bytes(BANK_LOGO), transformation: { width: logoW, height: logoH } } as any)],
        }),
        P('INTERNAL VOUCHER', 22, { bold: true, align: AlignmentType.RIGHT, after: 0 }),
      ], { span: 2 }),
    ],
  }))
  // lavender banner
  rows.push(new TableRow({
    children: [cell([P(s.title, 32, { bold: true, align: AlignmentType.CENTER, after: 0 })],
      { span: 4, fill: 'CCCCFF', borders: { top: THIN, bottom: THIN, left: THIN, right: THIN } })],
  }))
  // DATE
  rows.push(new TableRow({
    children: [cell([P(`DATE :  ${s.date}`, 22, { bold: true, align: AlignmentType.RIGHT, after: 0 })], { span: 4 })],
  }))
  // A/c No + amount
  rows.push(new TableRow({
    children: [
      cell([P(`A/c No. :   ${s.acNo}`, 26, { bold: true, after: 0 })], { span: s.amountBoxed ? 2 : 3 }),
      ...(s.amountBoxed
        ? [
            cell([P('AMOUNT / QUANTITY', 18, { bold: true, align: AlignmentType.RIGHT, after: 0 })]),
            cell([P(s.amount || '—', 24, { bold: true, align: AlignmentType.CENTER, after: 0 })],
              { borders: { top: MED, bottom: MED, left: MED, right: MED } }),
          ]
        : [cell([P(s.amount || '**********', 24, { bold: true, align: AlignmentType.RIGHT, after: 0 })])]),
    ],
  }))
  // OUR REF box: label cell (with its separator) + body lines
  const bodyParas: Paragraph[] = [
    P(s.ourRef || ' ', 22, { bold: true, after: 0 }),
    P(s.description || ' ', 19, { after: 0 }),
  ]
  const refBody = [
    cell(bodyParas, { span: 3, borders: { top: MED, bottom: NONE, left: MED, right: MED } }),
  ]
  rows.push(new TableRow({
    children: [
      cell([P('OUR REF :', 20, { bold: true, after: 0 })], { borders: { top: MED, bottom: NONE, left: MED, right: MED } }),
      ...refBody,
    ],
  }))
  // name line (top rule, like the form) + extra stamp lines
  rows.push(new TableRow({
    children: [
      cell([new Paragraph('')], { borders: { top: NONE, bottom: MED, left: MED, right: MED } }),
      cell([
        P(s.acName || ' ', 21, { bold: true, after: 0 }),
        ...s.extraLines.map((ln) => P(ln, 19, { bold: true, after: 0 })),
      ], { span: 3, borders: { top: THIN, bottom: MED, left: MED, right: MED } }),
    ],
  }))
  // stamp room
  rows.push(new TableRow({ children: [cell([P(' ', 22, { after: 0 }), P(' ', 22, { after: 0 }), P(' ', 22, { after: 0 })], { span: 4 })] }))
  // signature labels + rules
  rows.push(new TableRow({
    children: [
      cell([P('Prepared By.', 20, { bold: true, after: 0 })], { span: 2 }),
      cell([P('Authorized Signatures', 20, { bold: true, align: AlignmentType.RIGHT, after: 0 })], { span: 2 }),
    ],
  }))
  rows.push(new TableRow({
    children: [
      cell([new Paragraph('')], { borders: { ...noBorders, top: THIN } }),
      cell([new Paragraph('')]),
      cell([new Paragraph('')]),
      cell([new Paragraph('')], { borders: { ...noBorders, top: THIN } }),
    ],
  }))

  return new Table({
    alignment: AlignmentType.CENTER,
    width: { size: FULL, type: WidthType.DXA },
    columnWidths: COLS,
    // thick outer frame — the slip's 1.6pt border
    borders: {
      top: { style: BorderStyle.SINGLE, size: 13, color: '000000' },
      bottom: { style: BorderStyle.SINGLE, size: 13, color: '000000' },
      left: { style: BorderStyle.SINGLE, size: 13, color: '000000' },
      right: { style: BorderStyle.SINGLE, size: 13, color: '000000' },
      insideHorizontal: NONE, insideVertical: NONE,
    } as any,
    rows,
  })
}

export async function buildVoucherDocx(slips: SlipSpec[], buildTag: string): Promise<Blob> {
  const children: (Table | Paragraph)[] = []
  for (let i = 0; i < slips.length; i++) {
    if (i > 0) children.push(new Paragraph({ spacing: { before: 60, after: 60 }, children: [] }))
    children.push(await slipTable(slips[i]))
  }
  const doc = new Document({
    description: `ALLIN1 voucher export — build ${buildTag}`,
    styles: { default: { document: { run: { font: { ascii: FONT, hAnsi: FONT, cs: FONT }, size: 20, sizeComplexScript: 20 } as any } } },
    sections: [{
      properties: {
        page: { margin: { top: 454, bottom: 454, left: 624, right: 624 } },   // 8mm / 11mm
      },
      children,
    }],
  })
  return Packer.toBlob(doc)
}
