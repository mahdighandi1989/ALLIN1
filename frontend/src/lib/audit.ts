// Shared presentation helpers for the activity/audit log — used by both the
// per-customer «Logs» tab and the global Audit page so the two stay consistent.
import { AuditEntry } from '@/types'

// A human-readable Persian summary of "what happened" for one entry.
const ENTITY_FA: Record<string, string> = {
  customer: 'مشتری', profile: 'پروفایل/مدارک', facility: 'تسهیلات', guarantor: 'ضامن',
  offer_letter: 'نامهٔ پیشنهادِ تسهیلات', offer_letter_data: 'دادهٔ نامهٔ پیشنهاد',
  sanction: 'مصوبهٔ کمیتهٔ اعتباری', note: 'یادداشت', attachment: 'مدرک', task: 'تسکِ پیگیری',
  checklist: 'چک‌لیست', document: 'استخراجِ سند', voucher: 'سندِ انتظامی', letter: 'نامهٔ رسمی',
  user: 'کاربر', auth: 'ورود/خروج',
}
const VERB_FA: Record<string, string> = {
  create: 'ایجاد', update: 'ویرایش', delete: 'حذف', upload: 'بارگذاری',
  import: 'ورودِ اطلاعات', print: 'چاپ', login: 'ورود', logout: 'خروج',
}

export function auditWhat(e: AuditEntry): string {
  const ent = ENTITY_FA[e.entity_type || ''] || e.entity_type || ''
  const verb = VERB_FA[e.action] || e.action
  const head = ent ? `${verb} ${ent}` : verb
  return head
}

// A concise label for the action chip.
export function auditActionLabel(action: string): string {
  return VERB_FA[action] || action
}

export const ACTION_COLORS: Record<string, string> = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  upload: 'bg-teal-100 text-teal-700',
  import: 'bg-indigo-100 text-indigo-700',
  print: 'bg-amber-100 text-amber-700',
  login: 'bg-purple-100 text-purple-700',
  logout: 'bg-purple-100 text-purple-700',
}

// Which profile tab a given entity belongs to (for deep-linking).
function tabFor(entity?: string | null): string {
  switch (entity) {
    case 'attachment': case 'document': return 'attachments'
    case 'note': return 'notes'
    case 'facility': return 'facilities'
    case 'guarantor': return 'guarantors'
    case 'task': return 'tasks'
    case 'checklist': return 'checklist'
    case 'profile': return 'kyc'
    default: return 'overview'
  }
}

// Deep-link for an entry: the owning customer's profile, opened on the relevant
// tab (and the specific facility when the action targets one). Returns '' when
// there is no customer to link to (user/auth/system events).
export function auditLink(e: AuditEntry): string {
  if (!e.customer_id) return ''
  const tab = tabFor(e.entity_type)
  let href = `/customer-detail?id=${encodeURIComponent(e.customer_id)}&tab=${tab}`
  if (e.entity_type === 'facility' && e.entity_id) href += `&facility=${encodeURIComponent(e.entity_id)}`
  return href
}
