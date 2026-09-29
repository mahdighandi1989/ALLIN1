// «گزارش خلاصهٔ پروندهٔ حقوقی» — the body of the letter, as the template draws it.
//
// This is a LETTER TEMPLATE, not a separate document type. The owner said it
// twice: «قرار شد مثل یه نوعی از همین نامه ها باشه … وقتی اوردمش ذیل نامه ها یعنی
// نوعی از نامه ها فقط با یه فرمت خاص خودش». So the eleven sections are produced
// as ordinary letter-body HTML and dropped into the letter editor, which already
// knows how to do everything that was missing before: click into any cell and
// type, the table toolbar, «چیدمان», the AI assistant, attachments, the real
// .docx export, pagination with the letterhead repeated, and B Nazanin at the
// letter's own sizes.
//
// Structure read off the RENDERED pages of the owner's PDF, not a text dump of
// it: §4, §5, §5-ب and §10 are bordered tables (a text extraction makes them look
// like label/value pairs, which is how the first attempt went wrong), §5 carries
// a full-width banner row above six columns, and §6 has a two-level header.

const EMPTY = '<br>'

/** One bordered table: a header row (or two) and `rows` empty body rows. */
function table(cols: string[], rows: number, opts: { widths?: string[]; group?: [string, number, number] } = {}): string {
  const w = opts.widths || []
  const head = opts.group
    ? (() => {
        const [label, from, span] = opts.group
        const cells: string[] = []
        cols.forEach((c, i) => {
          if (i < from) cells.push(`<th rowspan="2">${c}</th>`)
          else if (i === from) cells.push(`<th colspan="${span}">${label}</th>`)
          else if (i > from + span - 1) cells.push(`<th rowspan="2">${c}</th>`)
        })
        const sub = cols.slice(from, from + span).map((c) => `<th>${c}</th>`).join('')
        return `<tr>${cells.join('')}</tr><tr>${sub}</tr>`
      })()
    : `<tr>${cols.map((c, i) => `<th${w[i] ? ` style="width:${w[i]}"` : ''}>${c}</th>`).join('')}</tr>`
  const body = Array.from({ length: rows }, () =>
    `<tr>${cols.map(() => `<td>${EMPTY}</td>`).join('')}</tr>`).join('')
  return `<table><thead>${head}</thead><tbody>${body}</tbody></table>`
}

const h = (n: string, t: string) => `<div><b>${n ? `${n}- ` : ''}${t}</b></div>`
const p = (t = EMPTY) => `<div>${t}</div>`

/**
 * The body of a blank case report.
 *
 * Everything is editable in place — this is only the starting paper. The
 * introduction keeps the template's dashes so the writer can see exactly which
 * blanks to fill, which is how the owner's own filled sample reads.
 */
export function caseReportBody(): string {
  return [
    h('۱', 'خلاصه وضعیت شرکت:'),
    p('موسسه ......... بر اساس مستندات ثبتی در سال ..... به شماره رخصه ..... در منطقه آزاد ......... تاسیس گردیده و در زمینه ......... فعالیت داشته است. مدیر شرکت آقای ......... در تاریخ ..../..../.... برای موسسه نزد این شعبه گشایش حساب نموده و از سال ..... به تدریج از تسهیلات بانک استفاده نموده است.'),
    p(),
    p('<b>اسامی شرکا و مدیران شرکت طبق رخصه تجاری موجود در پرونده:</b>'),
    table(['نام شرکا', 'شماره ملی ایران', 'درصد سهام و ملیت', 'سمت/توضیحات'], 2,
          { widths: ['32%', '20%', '22%', '26%'] }),
    p(),
    h('۲', 'مشخصات آخرین تسهیلات اعطایی به مشتری:'),
    table(['نوع تسهیلات', 'مبلغ تسهیلات', 'تاریخ اعطاء تسهیلات', 'نرخ تسهیلات'], 2,
          { widths: ['34%', '22%', '26%', '18%'] }),
    p(),
    h('۳', 'مشخصات تسهیلات اعطائی تسویه نشده (مطالباتی):'),
    table(['نوع تسهیلات', 'مانده اصل در زمان طبقه بندی', 'تاریخ اعطاء تسهیلات', 'نرخ سود'], 2,
          { widths: ['32%', '26%', '24%', '18%'] }),
    p(),
    h('۴', 'وضعیت رکود و طبقه بندی حساب:'),
    `<table><thead><tr><th style="width:40%">عنوان</th><th style="width:28%">تاریخ</th><th style="width:32%">مانده بدهی (درهم)</th></tr></thead><tbody>` +
      `<tr><td>تاریخ رکود حساب</td><td>${EMPTY}</td><td>${EMPTY}</td></tr>` +
      `<tr><td>تاریخ طبقه بندی حساب</td><td>${EMPTY}</td><td>${EMPTY}</td></tr>` +
      `</tbody></table>`,
    p('<span style="font-size:10px">** تاریخ رکود به طور سیستماتیک نبوده و بر حسب بررسی روی تراکنش ها به صورت قضاوتی تعیین می گردد</span>'),
    p(),
    h('۵', 'مانده بدهی طبق دفاتر بانک به تاریخ تنظیم گزارش'),
    `<table><thead>` +
      `<tr><th colspan="6">تعهدات مستقیم  -  * حساب در تاریخ ..../..../.... به زیر خط ترازنامه انتقال یافته است</th></tr>` +
      `<tr><th style="width:22%">اصل بدهی<br>( + سود قبل از طبقه بندی)</th><th style="width:18%">سود معوق و جرایم تأخیر</th>` +
      `<th style="width:14%">هزینه های درهمی</th><th style="width:16%">جمع کل</th>` +
      `<th style="width:12%">ذخایر</th><th style="width:18%">هزینه های ریالی</th></tr>` +
      `</thead><tbody><tr>${'<td>' + EMPTY + '</td>'.repeat(6)}</tr></tbody></table>`,
    p(),
    p('<b>- مانده بدهی طبق حکم دادگاه به تاریخ روز تنظیم گزارش:</b>'),
    `<table><thead><tr>` +
      `<th style="width:18%">اصل بدهی</th><th style="width:24%">سود با نرخ ....٪<br>از تاریخ ..../..../....</th>` +
      `<th style="width:18%">هزینه های قانونی</th><th style="width:22%">مبالغ وصول شده<br>از تاریخ محاسبه حکم</th>` +
      `<th style="width:18%">جمع کل</th></tr></thead>` +
      `<tbody><tr>${'<td>' + EMPTY + '</td>'.repeat(5)}</tr></tbody></table>`,
    p(),
    h('۶', 'مبالغ دریافتی از مدیونین/ضامنین (از تاریخ رکود):'),
    table(['تاریخ وصولی', 'مبالغ وصولی', 'نوع ارز', 'منشأ وصولی', 'اصل', 'سود', 'هزینه قانونی'], 2,
          { group: ['نحوه کارسازی (درهم)', 4, 3] }),
    `<table><tbody><tr><td style="width:62%"><b>جمع وصولی ها از تاریخ رکود به درهم:</b></td><td>${EMPTY}</td></tr></tbody></table>`,
    p(),
    h('۷', 'وثایق و پشتوانه های مأخوذه به تفکیک نوع و مبلغ در هر بخش:'),
    table(['نوع وثیقه', 'شماره رفرنس', 'مبلغ وثیقه (درهم)'], 6, { widths: ['46%', '28%', '26%'] }),
    p(),
    h('۸', 'مشخصات مصوبات اخذ شده تاکنون جهت تعیین تکلیف مطالبات:'),
    table(['مرجع مصوبه', 'تاریخ مصوبه', 'موضوع مصوبه', 'نتیجه'], 4,
          { widths: ['20%', '13%', '37%', '30%'] }),
    p(),
    p('<b>اقدامات صورت گرفته بر روی وثایق و نتایج حاصله:</b>'),
    table(['نوع وثیقه', 'مبلغ وثیقه (درهم)', 'اقدامات صورت گرفته بر روی وثایق و نتایج حاصله'], 3,
          { widths: ['24%', '16%', '60%'] }),
    p(),
    p('<b>❖ چکهای تنزیل شده:</b>'),
    table(['ردیف', 'شماره چک', 'ذینفع', 'صادر کننده چک', 'نام بانک و شعبه', 'مبلغ به درهم'], 1,
          { widths: ['8%', '15%', '20%', '20%', '22%', '15%'] }),
    p(),
    h('۹', 'تعهدات مستقیم و غیر مستقیم — ج) سایر تعهدات:'),
    table(['موضوع تعهد', 'توضیحات', 'مبلغ تعهد'], 1, { widths: ['30%', '50%', '20%'] }),
    p('<span style="font-size:10px">**اطلاعات مندرج درخصوص تعهدات مستقیم و غیر مستقیم حسب بررسی در سوابق این شعبه می باشد</span>'),
    p(),
    h('۱۰', 'مشخصات حکم:'),
    table(['تاریخ اقدام', 'تاریخ صدور حکم نهایی', 'تاریخ ارسال حکم به ایران'], 1,
          { widths: ['33%', '33%', '34%'] }),
    p(),
    h('۱۱', 'سایر توضیحات'),
    p(),
    p(),
  ].join('')
}

/** The «موضوع» line, in the template's spaced-out lettering. */
export const CASE_SUBJECT =
  'مــوضـوع : بـدهـی .......... حـسـاب شـمـاره .......... نـزد شـعبـه ..........'

export const CASE_RECIPIENT_TITLE = 'ریاست محترم'
export const CASE_RECIPIENT_DEPT = 'دایره حقوقی و پیگیری وصول مطالبات'
