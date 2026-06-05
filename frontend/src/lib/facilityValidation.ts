import { FacilityForm as FacilityFormData } from '@/types'

// Allowed ISO 4217 currency codes. Kept as a frozen Set so the client can reject
// obviously-invalid codes (e.g. "ZZZ", "US", "12A") before hitting the API and
// producing an opaque database / 422 error. This mirrors the 3-letter ISO rule
// enforced server-side in backend/app/schemas/validators.py (validate_currency).
export const ISO_4217_CURRENCIES = new Set<string>([
  'AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN',
  'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL',
  'BSD', 'BTN', 'BWP', 'BYN', 'BZD', 'CAD', 'CDF', 'CHF', 'CLP', 'CNY',
  'COP', 'CRC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP', 'DZD', 'EGP',
  'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GHS', 'GIP', 'GMD',
  'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 'IDR', 'ILS',
  'INR', 'IQD', 'IRR', 'ISK', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR',
  'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD',
  'LSL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRU',
  'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK',
  'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG',
  'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD', 'SCR', 'SDG', 'SEK',
  'SGD', 'SHP', 'SLE', 'SOS', 'SRD', 'SSP', 'STN', 'SVC', 'SYP', 'SZL',
  'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH',
  'UGX', 'USD', 'UYU', 'UZS', 'VED', 'VES', 'VND', 'VUV', 'WST', 'XAF',
  'XCD', 'XOF', 'XPF', 'YER', 'ZAR', 'ZMW', 'ZWL',
])

/**
 * Validate a facility form on the client before it is sent to the API.
 *
 * Returns a user-facing (Persian) error message for the first invalid field, or
 * `null` when every field passes. Mirrors the server-side constraints
 * (amount > 0, 0 <= interest_rate <= 100, 3-letter ISO currency) so users get a
 * friendly message instead of a raw 422 / database constraint error.
 */
export function validateFacilityForm(form: FacilityFormData): string | null {
  // amount must be a positive number.
  if (
    form.amount === undefined ||
    form.amount === null ||
    Number.isNaN(form.amount) ||
    form.amount <= 0
  ) {
    return 'مبلغ باید مثبت باشد'
  }
  // interest_rate is optional, but when provided must be within [0, 100].
  if (
    form.interest_rate !== undefined &&
    form.interest_rate !== null &&
    (Number.isNaN(form.interest_rate) || form.interest_rate < 0 || form.interest_rate > 100)
  ) {
    return 'نرخ سود باید بین 0 تا 100 باشد'
  }
  // currency is required and must be a known ISO 4217 code.
  const currency = (form.currency || '').trim().toUpperCase()
  if (!ISO_4217_CURRENCIES.has(currency)) {
    return 'کد ارز باید یک کد معتبر ISO 4217 باشد'
  }
  // expiry_date is optional, but when provided must be in the future and after
  // start_date (when a start_date is present on the form).
  if (form.expiry_date) {
    const expiry = new Date(form.expiry_date)
    if (Number.isNaN(expiry.getTime())) {
      return 'تاریخ انقضا نامعتبر است'
    }
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    if (expiry <= today) {
      return 'تاریخ انقضا باید در آینده باشد'
    }
    if (form.start_date) {
      const start = new Date(form.start_date)
      if (!Number.isNaN(start.getTime()) && expiry <= start) {
        return 'تاریخ انقضا باید بعد از تاریخ شروع باشد'
      }
    }
  }
  return null
}
