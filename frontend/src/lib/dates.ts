// Display rule (owner directive, v47): every English-format date printed on a
// letter/form is DAY/MONTH/YEAR with slashes. Any '-'-separated date the user
// typed — even mid-sentence — converts to slashes, and ISO (year-first) dates
// are reordered day-first. Storage stays whatever the field holds; this is a
// render-time transform.
//   2026-07-11  ->  11/07/2026   (ISO -> DMY, reordered)
//   9-7-2026    ->  09/07/2026   (already day-first: pad + slashes)
//   2026-07-11T10:00  stays untouched beyond the date part it starts with.
export const dmySlash = (s: string | null | undefined): string =>
  String(s ?? '')
    .replace(/(^|[^\d])(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)/g,
      (_, pre, y, m, d) => `${pre}${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`)
    .replace(/(^|[^\d])(\d{1,2})-(\d{1,2})-(\d{4})(?!\d)/g,
      (_, pre, d, m, y) => `${pre}${d.padStart(2, '0')}/${m.padStart(2, '0')}/${y}`)
