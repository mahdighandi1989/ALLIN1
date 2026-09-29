// The paper form, described once.
//
// «گزارش خلاصهٔ پروندهٔ حقوقی» is a fixed 11-section document the branch sends to
// the Legal & Debt-Recovery department. Its shape lives HERE — one spec, read by
// the page, the Word export and the print path alike — so the screen, the print
// and the .docx can never drift into three different documents. Adding section 12
// means adding one entry, not editing three renderers.
//
// The column titles and the section headings are copied verbatim from the blank
// PDF template the owner supplied; they are what the receiving department reads,
// so they are not paraphrased.

export type Col = { key: string; label: string; w?: string; ltr?: boolean }

export type Section =
  | { kind: 'table'; key: string; no: string; title: string; cols: Col[]; note?: string }
  | { kind: 'fields'; key: string; no: string; title: string; rows: Col[]; note?: string }
  | { kind: 'text'; key: string; no: string; title: string; field: string; note?: string }

// §4 and the two balance blocks are fixed-shape grids rather than repeating
// tables — they always have exactly these rows, so they are scalar fields, not
// a table the user adds rows to.
export const SECTIONS: Section[] = [
  {
    kind: 'text', key: 'company', no: '۱', title: 'خلاصه وضعیت شرکت:',
    field: 'company_summary',
  },
  {
    kind: 'table', key: 'partners', no: '', title: 'اسامی شرکا و مدیران شرکت طبق رخصه تجاری موجود در پرونده:',
    cols: [
      { key: 'name', label: 'نام شرکا' },
      { key: 'national_id', label: 'شماره ملی ایران', ltr: true, w: '20%' },
      { key: 'share', label: 'درصد سهام و ملیت', w: '22%' },
      { key: 'role', label: 'سمت/توضیحات', w: '25%' },
    ],
  },
  {
    kind: 'table', key: 'facilities_granted', no: '۲', title: 'مشخصات آخرین تسهیلات اعطایی به مشتری:',
    cols: [
      { key: 'type', label: 'نوع تسهیلات' },
      { key: 'amount', label: 'مبلغ تسهیلات', w: '24%' },
      { key: 'grant_date', label: 'تاریخ اعطاء تسهیلات', w: '24%', ltr: true },
      { key: 'rate', label: 'نرخ تسهیلات', w: '16%' },
    ],
  },
  {
    kind: 'table', key: 'facilities_unsettled', no: '۳', title: 'مشخصات تسهیلات اعطائی تسویه نشده (مطالباتی):',
    cols: [
      { key: 'type', label: 'نوع تسهیلات' },
      { key: 'principal', label: 'مانده اصل در زمان طبقه بندی', w: '26%' },
      { key: 'grant_date', label: 'تاریخ اعطاء تسهیلات', w: '22%', ltr: true },
      { key: 'rate', label: 'نرخ سود', w: '20%' },
    ],
  },
  {
    kind: 'fields', key: 'stagnation', no: '۴', title: 'وضعیت رکود و طبقه بندی حساب:',
    rows: [
      { key: 'stagnation_date', label: 'تاریخ رکود حساب' },
      { key: 'stagnation_balance', label: 'مانده بدهی (درهم) — رکود' },
      { key: 'classification_date', label: 'تاریخ طبقه بندی حساب' },
      { key: 'classification_balance', label: 'مانده بدهی (درهم) — طبقه بندی' },
    ],
    note: '** تاریخ رکود به طور سیستماتیک نبوده و بر حسب بررسی روی تراکنش ها به صورت قضاوتی تعیین می گردد',
  },
  {
    kind: 'fields', key: 'books', no: '۵', title: 'مانده بدهی طبق دفاتر بانک به تاریخ تنظیم گزارش:',
    rows: [
      { key: 'books_principal', label: 'اصل بدهی (+ سود قبل از طبقه بندی)' },
      { key: 'books_overdue_interest', label: 'سود معوق و جرایم تأخیر' },
      { key: 'books_aed_costs', label: 'هزینه های درهمی' },
      { key: 'books_total', label: 'جمع کل' },
      { key: 'books_provisions', label: 'ذخایر' },
      { key: 'books_irr_costs', label: 'هزینه های ریالی' },
    ],
  },
  {
    kind: 'fields', key: 'court', no: '۵-ب', title: 'مانده بدهی طبق حکم دادگاه به تاریخ روز تنظیم گزارش:',
    rows: [
      { key: 'court_principal', label: 'اصل بدهی' },
      { key: 'court_interest', label: 'سود' },
      { key: 'court_interest_rate', label: 'با نرخ' },
      { key: 'court_interest_from', label: 'از تاریخ' },
      { key: 'court_legal_costs', label: 'هزینه های قانونی' },
      { key: 'court_collected', label: 'مبالغ وصول شده از تاریخ محاسبه حکم' },
      { key: 'court_total', label: 'جمع کل' },
    ],
  },
  {
    kind: 'table', key: 'collections', no: '۶', title: 'مبالغ دریافتی از مدیونین/ضامنین (از تاریخ رکود):',
    cols: [
      { key: 'date', label: 'تاریخ وصولی', w: '14%', ltr: true },
      { key: 'amount', label: 'مبالغ وصولی', w: '14%' },
      { key: 'currency', label: 'نوع ارز', w: '9%' },
      { key: 'source', label: 'منشأ وصولی' },
      { key: 'principal', label: 'کارسازی: اصل', w: '11%' },
      { key: 'interest', label: 'کارسازی: سود', w: '11%' },
      { key: 'legal_cost', label: 'کارسازی: هزینه قانونی', w: '12%' },
    ],
  },
  {
    kind: 'table', key: 'collaterals', no: '۷', title: 'وثایق و پشتوانه های مأخوذه به تفکیک نوع و مبلغ در هر بخش:',
    cols: [
      { key: 'type', label: 'نوع وثیقه' },
      { key: 'reference_no', label: 'شماره رفرنس', w: '26%', ltr: true },
      { key: 'amount', label: 'مبلغ وثیقه (درهم)', w: '22%' },
    ],
  },
  {
    kind: 'table', key: 'approvals', no: '۸', title: 'مشخصات مصوبات اخذ شده تاکنون جهت تعیین تکلیف مطالبات:',
    cols: [
      { key: 'authority', label: 'مرجع مصوبه', w: '20%' },
      { key: 'date', label: 'تاریخ مصوبه', w: '12%', ltr: true },
      { key: 'subject', label: 'موضوع مصوبه' },
      { key: 'result', label: 'نتیجه' },
    ],
  },
  {
    kind: 'table', key: 'collateral_actions', no: '۸-ب',
    title: 'اقدامات صورت گرفته بر روی وثایق و نتایج حاصله:',
    cols: [
      { key: 'type', label: 'نوع وثیقه', w: '24%' },
      { key: 'amount', label: 'مبلغ وثیقه (درهم)', w: '16%' },
      { key: 'actions', label: 'اقدامات صورت گرفته بر روی وثایق و نتایج حاصله' },
    ],
  },
  {
    kind: 'table', key: 'discounted_cheques', no: '۸-ج', title: '❖ چکهای تنزیل شده:',
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
    kind: 'table', key: 'commitments', no: '۹', title: 'تعهدات مستقیم و غیر مستقیم — ج) سایر تعهدات:',
    cols: [
      { key: 'subject', label: 'موضوع تعهد', w: '30%' },
      { key: 'description', label: 'توضیحات' },
      { key: 'amount', label: 'مبلغ تعهد', w: '20%' },
    ],
    note: '**اطلاعات مندرج درخصوص تعهدات مستقیم و غیر مستقیم حسب بررسی در سوابق این شعبه می باشد',
  },
  {
    kind: 'fields', key: 'judgment', no: '۱۰', title: 'مشخصات حکم:',
    rows: [
      { key: 'judgment_action_date', label: 'تاریخ اقدام', ltr: true },
      { key: 'judgment_final_date', label: 'تاریخ صدور حکم نهایی', ltr: true },
      { key: 'judgment_sent_iran_date', label: 'تاریخ ارسال حکم به ایران', ltr: true },
    ],
  },
  {
    kind: 'text', key: 'other', no: '۱۱', title: 'سایر توضیحات', field: 'other_notes',
  },
]

// Which spec key maps to which API `tables` key. They are the same string today;
// naming it once means a rename cannot half-happen.
export const TABLE_KEYS = SECTIONS.filter((s) => s.kind === 'table').map((s) => s.key)

export const blankRow = (s: Section): Record<string, string> =>
  s.kind === 'table' ? Object.fromEntries(s.cols.map((c) => [c.key, ''])) : {}
