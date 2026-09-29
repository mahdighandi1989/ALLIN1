// The paper form, described once.
//
// «گزارش خلاصهٔ پروندهٔ حقوقی» is a fixed 11-section document the branch sends to
// the Legal & Debt-Recovery department. Its shape lives HERE — one spec, read by
// the page, the Word export and the print path alike.
//
// The column titles and section headings are copied VERBATIM from the blank PDF
// the owner supplied, and the structures below were read off the rendered pages of
// that PDF, not off a text extraction of it. That distinction matters: a text dump
// told me §4, §5 and §10 were label/value pairs, and they are not — they are real
// bordered tables with their own column layouts, and building from the dump
// produced a document that looked nothing like the paper.

export type Col = {
  key: string
  label: string
  w?: string
  ltr?: boolean
  /** consecutive columns sharing a group render one spanning header cell above them */
  group?: string
}

/** A row of a fixed grid: an optional leading label cell, then one field per column. */
export type GridRow = { label?: string; fields: string[] }

export type Section =
  /** repeating table the user adds rows to; rows live in `tables[key]` */
  | { kind: 'table'; key: string; no: string; title: string; cols: Col[]; note?: string; minRows?: number }
  /** fixed table whose cells are bound to SCALAR fields — same storage as before */
  | { kind: 'grid'; key: string; no: string; title: string; cols: Col[]; rows: GridRow[]
      banner?: { text: string; field?: string }; note?: string }
  | { kind: 'text'; key: string; no: string; title: string; field: string; note?: string }

export const SECTIONS: Section[] = [
  { kind: 'text', key: 'company', no: '۱', title: 'خلاصه وضعیت شرکت:', field: 'company_summary' },
  {
    kind: 'table', key: 'partners', no: '',
    title: 'اسامی شرکا و مدیران شرکت طبق رخصه تجاری موجود در پرونده:', minRows: 1,
    cols: [
      { key: 'name', label: 'نام شرکا' },
      { key: 'national_id', label: 'شماره ملی ایران', ltr: true, w: '18%' },
      { key: 'share', label: 'درصد سهام و ملیت', w: '20%' },
      { key: 'role', label: 'سمت/توضیحات', w: '28%' },
    ],
  },
  {
    kind: 'table', key: 'facilities_granted', no: '۲',
    title: 'مشخصات آخرین تسهیلات اعطایی به مشتری:', minRows: 2,
    cols: [
      { key: 'type', label: 'نوع تسهیلات' },
      { key: 'amount', label: 'مبلغ تسهیلات', w: '22%' },
      { key: 'grant_date', label: 'تاریخ اعطاء تسهیلات', w: '24%', ltr: true },
      { key: 'rate', label: 'نرخ تسهیلات', w: '18%' },
    ],
  },
  {
    kind: 'table', key: 'facilities_unsettled', no: '۳',
    title: 'مشخصات تسهیلات اعطائی تسویه نشده (مطالباتی):', minRows: 2,
    cols: [
      { key: 'type', label: 'نوع تسهیلات' },
      { key: 'principal', label: 'مانده اصل در زمان طبقه بندی', w: '26%' },
      { key: 'grant_date', label: 'تاریخ اعطاء تسهیلات', w: '22%', ltr: true },
      { key: 'rate', label: 'نرخ سود', w: '20%' },
    ],
  },
  {
    // A 3-column table with two FIXED rows, not four loose fields.
    kind: 'grid', key: 'stagnation', no: '۴', title: 'وضعیت رکود و طبقه بندی حساب:',
    cols: [
      { key: 'c0', label: 'عنوان', w: '40%' },
      { key: 'c1', label: 'تاریخ', w: '28%', ltr: true },
      { key: 'c2', label: 'مانده بدهی (درهم)', w: '32%' },
    ],
    rows: [
      { label: 'تاریخ رکود حساب', fields: ['stagnation_date', 'stagnation_balance'] },
      { label: 'تاریخ طبقه بندی حساب', fields: ['classification_date', 'classification_balance'] },
    ],
    note: '** تاریخ رکود به طور سیستماتیک نبوده و بر حسب بررسی روی تراکنش ها به صورت قضاوتی تعیین می گردد',
  },
  {
    // Six columns under a full-width banner row carrying the off-balance note.
    kind: 'grid', key: 'books', no: '۵', title: 'مانده بدهی طبق دفاتر بانک به تاریخ تنظیم گزارش',
    banner: { text: 'تعهدات مستقیم  -  * حساب در تاریخ {} به زیر خط ترازنامه انتقال یافته است',
              field: 'offbalance_date' },
    cols: [
      { key: 'c0', label: 'اصل بدهی\n( + سود قبل از طبقه بندی)', w: '22%' },
      { key: 'c1', label: 'سود معوق و جرایم تأخیر', w: '18%' },
      { key: 'c2', label: 'هزینه های درهمی', w: '14%' },
      { key: 'c3', label: 'جمع کل', w: '16%' },
      { key: 'c4', label: 'ذخایر', w: '12%' },
      { key: 'c5', label: 'هزینه های ریالی', w: '18%' },
    ],
    rows: [{ fields: ['books_principal', 'books_overdue_interest', 'books_aed_costs',
                      'books_total', 'books_provisions', 'books_irr_costs'] }],
  },
  {
    kind: 'grid', key: 'court', no: '',
    title: '- مانده بدهی طبق حکم دادگاه به تاریخ روز تنظیم گزارش:',
    cols: [
      { key: 'c0', label: 'اصل بدهی', w: '18%' },
      // the rate and the from-date are printed INSIDE this header, as on the paper
      { key: 'c1', label: 'سود با نرخ {court_interest_rate}\nاز تاریخ {court_interest_from}', w: '24%' },
      { key: 'c2', label: 'هزینه های قانونی', w: '18%' },
      { key: 'c3', label: 'مبالغ وصول شده\nاز تاریخ محاسبه حکم', w: '22%' },
      { key: 'c4', label: 'جمع کل', w: '18%' },
    ],
    rows: [{ fields: ['court_principal', 'court_interest', 'court_legal_costs',
                      'court_collected', 'court_total'] }],
  },
  {
    kind: 'table', key: 'collections', no: '۶',
    title: 'مبالغ دریافتی از مدیونین/ضامنین (از تاریخ رکود):', minRows: 2,
    cols: [
      { key: 'date', label: 'تاریخ وصولی', w: '13%', ltr: true },
      { key: 'amount', label: 'مبالغ وصولی', w: '15%' },
      { key: 'currency', label: 'نوع ارز', w: '9%' },
      { key: 'source', label: 'منشأ وصولی' },
      // one spanning header «نحوه کارسازی (درهم)» above these three, as on the paper
      { key: 'principal', label: 'اصل', w: '10%', group: 'نحوه کارسازی (درهم)' },
      { key: 'interest', label: 'سود', w: '10%', group: 'نحوه کارسازی (درهم)' },
      { key: 'legal_cost', label: 'هزینه قانونی', w: '11%', group: 'نحوه کارسازی (درهم)' },
    ],
  },
  {
    kind: 'table', key: 'collaterals', no: '۷',
    title: 'وثایق و پشتوانه های مأخوذه به تفکیک نوع و مبلغ در هر بخش:', minRows: 6,
    cols: [
      { key: 'type', label: 'نوع وثیقه' },
      { key: 'reference_no', label: 'شماره رفرنس', w: '28%', ltr: true },
      { key: 'amount', label: 'مبلغ وثیقه (درهم)', w: '26%' },
    ],
  },
  {
    kind: 'table', key: 'approvals', no: '۸',
    title: 'مشخصات مصوبات اخذ شده تاکنون جهت تعیین تکلیف مطالبات:', minRows: 4,
    cols: [
      { key: 'authority', label: 'مرجع مصوبه', w: '20%' },
      { key: 'date', label: 'تاریخ مصوبه', w: '13%', ltr: true },
      { key: 'subject', label: 'موضوع مصوبه' },
      { key: 'result', label: 'نتیجه' },
    ],
  },
  {
    kind: 'table', key: 'collateral_actions', no: '',
    title: 'اقدامات صورت گرفته بر روی وثایق و نتایج حاصله:', minRows: 3,
    cols: [
      { key: 'type', label: 'نوع وثیقه', w: '24%' },
      { key: 'amount', label: 'مبلغ وثیقه (درهم)', w: '16%' },
      { key: 'actions', label: 'اقدامات صورت گرفته بر روی وثایق و نتایج حاصله' },
    ],
  },
  {
    kind: 'table', key: 'discounted_cheques', no: '', title: '❖ چکهای تنزیل شده:', minRows: 1,
    cols: [
      { key: 'row', label: 'ردیف', w: '8%' },
      { key: 'cheque_no', label: 'شماره چک', w: '15%', ltr: true },
      { key: 'beneficiary', label: 'ذینفع' },
      { key: 'drawer', label: 'صادر کننده چک' },
      { key: 'bank', label: 'نام بانک و شعبه' },
      { key: 'amount', label: 'مبلغ به درهم', w: '15%' },
    ],
  },
  {
    kind: 'table', key: 'commitments', no: '۹',
    title: 'تعهدات مستقیم و غیر مستقیم — ج) سایر تعهدات:', minRows: 1,
    cols: [
      { key: 'subject', label: 'موضوع تعهد', w: '30%' },
      { key: 'description', label: 'توضیحات' },
      { key: 'amount', label: 'مبلغ تعهد', w: '20%' },
    ],
    note: '**اطلاعات مندرج درخصوص تعهدات مستقیم و غیر مستقیم حسب بررسی در سوابق این شعبه می باشد',
  },
  {
    kind: 'grid', key: 'judgment', no: '۱۰', title: 'مشخصات حکم:',
    cols: [
      { key: 'c0', label: 'تاریخ اقدام', w: '33%', ltr: true },
      { key: 'c1', label: 'تاریخ صدور حکم نهایی', w: '33%', ltr: true },
      { key: 'c2', label: 'تاریخ ارسال حکم به ایران', w: '34%', ltr: true },
    ],
    rows: [{ fields: ['judgment_action_date', 'judgment_final_date', 'judgment_sent_iran_date'] }],
  },
  { kind: 'text', key: 'other', no: '۱۱', title: 'سایر توضیحات', field: 'other_notes' },
]

export const TABLE_KEYS = SECTIONS.filter((s) => s.kind === 'table').map((s) => s.key)

export const blankRow = (s: Section): Record<string, string> =>
  s.kind === 'table' ? Object.fromEntries(s.cols.map((c) => [c.key, ''])) : {}

/** Header groups for a table, as [label, span] pairs; null label = no group cell. */
export function headerGroups(cols: Col[]): { label: string | null; span: number }[] {
  const out: { label: string | null; span: number }[] = []
  for (const c of cols) {
    const g = c.group || null
    const last = out[out.length - 1]
    if (last && last.label === g && g !== null) last.span += 1
    else out.push({ label: g, span: 1 })
  }
  return out
}

export const hasGroups = (cols: Col[]) => cols.some((c) => c.group)
