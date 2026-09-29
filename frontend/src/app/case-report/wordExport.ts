// The case report as a REAL, EDITABLE Word document (.docx).
//
// Not a picture of the report and not HTML renamed to .doc: every heading is a
// paragraph and every section is a native Word table with borders, shaded header
// rows and RTL cells, so the receiving department can edit it. The bank letterhead
// sits in the Word header/footer with native page numbers, exactly as the printed
// page repeats it.
//
// It deliberately does NOT reuse the letter's `buildLetterDocx`: that builder is
// wired to the letter's own shape — its «182 / 4 / …» serial line, its recipient
// frame, its single flowing body — and forcing this eleven-table report through it
// would distort both. The letterhead assets ARE shared, which is what has to match.
import {
  AlignmentType, BorderStyle, Document, Footer, Header, ImageRun, PageNumber, Packer,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, VerticalAlign, WidthType,
} from 'docx'
import { LH_FOOTER, LH_LOGO, LH_NAME } from '../letter/letterhead'
import type { Section } from './sections'

const FONT = 'B Nazanin'
const TITR = 'B Titr'
const FA = '۰۱۲۳۴۵۶۷۸۹'
// ASCII digits inside Persian text get a Latin fallback font in Word (they render
// western and slanted next to B Nazanin). Real Persian codepoints match the page.
const faDigits = (t: string) => t.replace(/[0-9]/g, (d) => FA[+d])
const b64 = (u: string) => Uint8Array.from(atob(u.split(',')[1]), (c) => c.charCodeAt(0))

const BORDER = { style: BorderStyle.SINGLE, size: 4, color: '222222' }
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER }

const run = (text: string, o: { bold?: boolean; font?: string; pt?: number; ltr?: boolean } = {}) =>
  new TextRun({
    text: o.ltr ? text : faDigits(text),
    bold: o.bold, font: o.font || FONT, size: Math.round((o.pt || 11) * 2),
    rightToLeft: !o.ltr,
  })

const P = (text: string, o: { bold?: boolean; font?: string; pt?: number; align?: any; ltr?: boolean; indent?: boolean } = {}) =>
  new Paragraph({
    bidirectional: !o.ltr,
    alignment: o.align ?? AlignmentType.RIGHT,
    indent: o.indent ? { firstLine: 280 } : undefined,
    spacing: { after: 60 },
    children: [run(text, o)],
  })

const cell = (text: string, o: { head?: boolean; ltr?: boolean; w?: number } = {}) =>
  new TableCell({
    borders: BORDERS,
    verticalAlign: VerticalAlign.TOP,
    width: o.w ? { size: o.w, type: WidthType.PERCENTAGE } : undefined,
    shading: o.head ? { type: ShadingType.CLEAR, fill: 'F1F5F9' } : undefined,
    children: [new Paragraph({
      bidirectional: !o.ltr,
      alignment: o.head ? AlignmentType.CENTER : (o.ltr ? AlignmentType.LEFT : AlignmentType.RIGHT),
      spacing: { before: 20, after: 20 },
      children: [run(text || ' ', { bold: o.head, pt: 10, ltr: o.ltr })],
    })],
  })

const table = (rows: TableRow[]) =>
  new Table({ rows, width: { size: 100, type: WidthType.PERCENTAGE }, borders: BORDERS })

export type CaseDocxArgs = {
  f: Record<string, string>
  tables: Record<string, Record<string, string>[]>
  sections: Section[]
}

export async function buildCaseDocx(a: CaseDocxArgs): Promise<Blob> {
  const f = (k: string) => (a.f[k] || '').trim()
  const body: (Paragraph | Table)[] = []

  body.push(P('با سمه تعالی', { align: AlignmentType.CENTER, font: TITR, pt: 12 }))
  body.push(P(''))
  body.push(P(`تاریخ: ${f('letter_date')}`, { pt: 11 }))
  body.push(P(`شماره: ${f('letter_no')}`, { pt: 11 }))
  body.push(P(`طبقه بندی: ${f('classification')}`, { pt: 11, bold: true }))
  body.push(P(''))
  body.push(P(`جناب آقای ${f('recipient_name') || '----'}`, { bold: true, font: TITR, pt: 12 }))
  body.push(P(f('recipient_title') || 'ریاست محترم دایره حقوقی و پیگیری وصول مطالبات',
              { bold: true, font: TITR, pt: 12 }))
  body.push(P(''))
  body.push(P(
    `مــوضـوع : بـدهـی ${f('subject_entity') || '--------------'} حـسـاب شـمـاره ${f('subject_account') || '----------'} نـزد شـعبـه ${f('subject_branch') || '---------'}`,
    { bold: true, pt: 12 }))
  body.push(P('='.repeat(62), { pt: 10 }))
  body.push(P(
    `با سلام، احتراماً عطف به نامه شماره ${f('ref_letter_no') || '-------/---'} مورخ ${f('ref_letter_date') || '--/--/---'} اداره ${f('ref_letter_dept') || '----------'} در خصوص بدهی شرکت صدرالاشاره، بدینوسیله گزارش جامع وضعیت پرونده، وفق مفاد نامه ${f('basis_letter_no') || '-------/----'} مورخ ${f('basis_letter_date') || '---/---/-----'}، به شرح زیر ایفاد می گردد:`,
    { align: AlignmentType.JUSTIFIED, indent: true, pt: 11 }))
  body.push(P(''))

  for (const s of a.sections) {
    body.push(P(`${s.no ? s.no + '- ' : ''}${s.title}`, { bold: true, font: TITR, pt: 11.5 }))
    if (s.kind === 'text') {
      const txt = f(s.field)
      for (const line of (txt ? txt.split('\n') : [''])) {
        body.push(P(line, { align: AlignmentType.JUSTIFIED, indent: true, pt: 11 }))
      }
    } else if (s.kind === 'fields') {
      body.push(table(s.rows.map((r) => new TableRow({
        children: [cell(r.label, { head: true, w: 42 }), cell(f(r.key), { ltr: r.ltr })],
      }))))
    } else {
      const head = new TableRow({
        tableHeader: true,     // repeats on every page the table spills onto
        children: s.cols.map((c) => cell(c.label, { head: true })),
      })
      const rows = a.tables[s.key] || []
      const dataRows = rows.length
        ? rows.map((r) => new TableRow({
            children: s.cols.map((c) => cell((r[c.key] || '').toString(), { ltr: c.ltr })),
          }))
        : [new TableRow({ children: s.cols.map(() => cell(' ')) })]
      body.push(table([head, ...dataRows]))
    }
    if (s.note) body.push(P(s.note, { pt: 9.5 }))
    body.push(P(''))
  }

  body.push(P(''))
  body.push(P(`شعبه ${f('branch_name') || '-----'} ${f('branch_code') || '-----'}`, { pt: 11 }))
  body.push(P(''))
  body.push(P(`اقدام کننده : ${f('prepared_by')}`, { pt: 11 }))

  const header = new Header({
    children: [new Paragraph({
      alignment: AlignmentType.LEFT,
      children: [
        new ImageRun({ data: b64(LH_LOGO), transformation: { width: 72, height: 72 } }),
        new ImageRun({ data: b64(LH_NAME), transformation: { width: 150, height: 26 } }),
      ],
    })],
  })
  const footer = new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new ImageRun({ data: b64(LH_FOOTER), transformation: { width: 560, height: 46 } })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: ['Page | ', PageNumber.CURRENT], font: FONT, size: 18 })],
      }),
    ],
  })

  const doc = new Document({
    styles: { default: { document: { run: { font: FONT, size: 22 } } } },
    sections: [{
      properties: {
        page: { margin: { top: 1900, bottom: 1500, left: 900, right: 900 } },
      },
      headers: { default: header },
      footers: { default: footer },
      children: body,
    }],
  })
  return Packer.toBlob(doc)
}
