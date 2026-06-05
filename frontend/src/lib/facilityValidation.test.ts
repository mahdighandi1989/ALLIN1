/**
 * Unit tests for the facility form client-side validator.
 *
 * These assert the exact, behaviour-level contract the Acceptance Criteria ask
 * for: each invalid field produces the specific friendly (Persian) message that
 * the form surfaces via `toast.error(...)` before any request reaches the API.
 * They mirror the server-side guards in backend/app/schemas/facility.py
 * (amount gt=0, 0<=interest_rate<=100, 3-letter ISO currency) so the two layers
 * stay in sync — see backend/tests/test_facilities.py for the 422 side.
 */
import { validateFacilityForm, ISO_4217_CURRENCIES } from './facilityValidation'
import type { FacilityForm } from '@/types'

// A fully-valid baseline; each test mutates exactly one field so the message
// under assertion is unambiguously caused by that field.
function makeForm(overrides: Partial<FacilityForm> = {}): FacilityForm {
  return {
    customer_id: 'cust-1',
    facility_type: 'loan',
    name: 'Test facility',
    amount: 10000,
    currency: 'AED',
    interest_rate: 5,
    notes: '',
    ...overrides,
  }
}

describe('validateFacilityForm', () => {
  it('accepts a fully valid form (returns null)', () => {
    expect(validateFacilityForm(makeForm())).toBeNull()
  })

  // --- amount (AC1) ---------------------------------------------------------
  it('rejects amount = 0 with "مبلغ باید مثبت باشد"', () => {
    expect(validateFacilityForm(makeForm({ amount: 0 }))).toBe('مبلغ باید مثبت باشد')
  })

  it('rejects a negative amount', () => {
    expect(validateFacilityForm(makeForm({ amount: -1000 }))).toBe('مبلغ باید مثبت باشد')
  })

  it('rejects a NaN / missing amount', () => {
    expect(validateFacilityForm(makeForm({ amount: NaN }))).toBe('مبلغ باید مثبت باشد')
    // Exercise the runtime guard against an absent value (amount is the only
    // hard-required numeric field).
    expect(validateFacilityForm(makeForm({ amount: undefined }))).toBe('مبلغ باید مثبت باشد')
  })

  // --- interest_rate (AC3) --------------------------------------------------
  it('rejects interest_rate = 150 with "نرخ سود باید بین 0 تا 100 باشد"', () => {
    expect(validateFacilityForm(makeForm({ interest_rate: 150 }))).toBe(
      'نرخ سود باید بین 0 تا 100 باشد',
    )
  })

  it('rejects a negative interest_rate', () => {
    expect(validateFacilityForm(makeForm({ interest_rate: -5 }))).toBe(
      'نرخ سود باید بین 0 تا 100 باشد',
    )
  })

  it('accepts the inclusive bounds 0 and 100 for interest_rate', () => {
    expect(validateFacilityForm(makeForm({ interest_rate: 0 }))).toBeNull()
    expect(validateFacilityForm(makeForm({ interest_rate: 100 }))).toBeNull()
  })

  it('treats interest_rate as optional (undefined passes)', () => {
    expect(validateFacilityForm(makeForm({ interest_rate: undefined }))).toBeNull()
  })

  // --- currency (AC — ISO 4217) ---------------------------------------------
  it('rejects an unknown ISO 4217 currency code', () => {
    expect(validateFacilityForm(makeForm({ currency: 'ZZZ' }))).toBe(
      'کد ارز باید یک کد معتبر ISO 4217 باشد',
    )
    expect(validateFacilityForm(makeForm({ currency: 'US' }))).toBe(
      'کد ارز باید یک کد معتبر ISO 4217 باشد',
    )
    expect(validateFacilityForm(makeForm({ currency: '12A' }))).toBe(
      'کد ارز باید یک کد معتبر ISO 4217 باشد',
    )
  })

  it('accepts known ISO 4217 codes case-insensitively', () => {
    expect(validateFacilityForm(makeForm({ currency: 'usd' }))).toBeNull()
    expect(validateFacilityForm(makeForm({ currency: ' eur ' }))).toBeNull()
    expect(ISO_4217_CURRENCIES.has('IRR')).toBe(true)
  })

  // --- expiry_date (AC2) ----------------------------------------------------
  it('rejects an expiry_date in the past with "تاریخ انقضا باید در آینده باشد"', () => {
    // A safely-past fixed date (no reliance on the clock beyond "before today").
    expect(validateFacilityForm(makeForm({ expiry_date: '2000-01-01' }))).toBe(
      'تاریخ انقضا باید در آینده باشد',
    )
  })

  it('rejects an expiry_date that is not after start_date', () => {
    expect(
      validateFacilityForm(
        makeForm({ start_date: '2999-06-01', expiry_date: '2999-05-01' }),
      ),
    ).toBe('تاریخ انقضا باید بعد از تاریخ شروع باشد')
  })

  it('accepts a future expiry_date', () => {
    expect(validateFacilityForm(makeForm({ expiry_date: '2999-12-31' }))).toBeNull()
  })

  it('treats expiry_date as optional (undefined passes)', () => {
    expect(validateFacilityForm(makeForm({ expiry_date: undefined }))).toBeNull()
  })
})
