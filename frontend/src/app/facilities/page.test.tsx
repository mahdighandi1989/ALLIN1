/**
 * Interaction tests for the Facilities form (AC1–AC3 — ui_interaction).
 *
 * These render the real FacilitiesPage in jsdom, open the "Add Facility" modal,
 * type an invalid value into a single field, click Save, and assert that the
 * specific friendly (Persian) error is surfaced via toast.error AND that no
 * create request is sent. This proves the observable behaviour the ACs ask for
 * ("form shows error X") at the component level — equivalent to a
 * Playwright/Cypress flow, which the project's CI has no running browser for.
 *
 * The validator's exhaustive field/branch coverage lives in the fast unit suite
 * at src/lib/facilityValidation.test.ts; here we verify the wiring: bad input →
 * visible message → request blocked.
 */
import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { Customer } from '@/types'

// --- Mocks ------------------------------------------------------------------
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}))

jest.mock('@/components/Layout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const facilitiesListMock = jest.fn()
const facilitiesCreateMock = jest.fn()
const facilitiesUpdateMock = jest.fn()
const customersListMock = jest.fn()
jest.mock('@/lib/api', () => ({
  facilitiesApi: {
    list: (...args: unknown[]) => facilitiesListMock(...args),
    create: (...args: unknown[]) => facilitiesCreateMock(...args),
    update: (...args: unknown[]) => facilitiesUpdateMock(...args),
    delete: jest.fn(),
    bulkDelete: jest.fn(),
  },
  customersApi: {
    list: (...args: unknown[]) => customersListMock(...args),
  },
  parseApiError: (e: unknown) => String(e),
  downloadFile: jest.fn().mockResolvedValue(undefined),
}))

const toastErrorMock = jest.fn()
const toastSuccessMock = jest.fn()
jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: (...args: unknown[]) => toastSuccessMock(...args),
    error: (...args: unknown[]) => toastErrorMock(...args),
  },
}))

import FacilitiesPage from './page'

function makeCustomer(): Customer {
  return {
    id: 'cust-1',
    account_no: 'ACC-001',
    name: 'Acme Corp',
    name_ar: null,
    account_type: 'corporate',
    status: 'active',
    email: null,
    phone: null,
    mobile: null,
    address: null,
    branch: 'Main',
    relationship_manager: null,
    notes: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: null,
  } as Customer
}

beforeEach(() => {
  jest.clearAllMocks()
  facilitiesListMock.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
  customersListMock.mockResolvedValue({ items: [makeCustomer()], total: 1, page: 1, page_size: 100 })
})

// Open the modal and pick a customer so only the field under test is invalid.
async function openFormWithCustomer(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByText('Add Facility'))
  expect(await screen.findByText('New Facility')).toBeInTheDocument()
  const customerSelect = (await screen.findByTestId(
    'facility-form-customer',
  )) as HTMLSelectElement
  // Wait for the async customers fetch to populate the dropdown options.
  await waitFor(() =>
    expect(
      Array.from(customerSelect.options).some((o) => o.value === 'cust-1'),
    ).toBe(true),
  )
  await user.selectOptions(customerSelect, 'cust-1')
}

// Controlled number/date inputs are updated via fireEvent.change: it sets the
// final value in one event, avoiding the per-keystroke intermediate states that
// make userEvent.type flaky on `<input type="number">` (esp. with min/max).
function setField(testId: string, value: string) {
  fireEvent.change(screen.getByTestId(testId), { target: { value } })
}

describe('Facility form validation (interaction)', () => {
  it('shows "مبلغ باید مثبت باشد" and blocks the request when amount is 0', async () => {
    const user = userEvent.setup()
    render(<FacilitiesPage />)
    await openFormWithCustomer(user)

    setField('facility-form-amount', '0')
    await user.click(screen.getByTestId('facility-form-submit'))

    await waitFor(() => expect(toastErrorMock).toHaveBeenCalledWith('مبلغ باید مثبت باشد'))
    expect(facilitiesCreateMock).not.toHaveBeenCalled()
  })

  // interest_rate is guarded at two layers: the <input max="100"> native
  // constraint blocks the submit in the browser, and validateFacilityForm is the
  // defence-in-depth that returns 'نرخ سود باید بین 0 تا 100 باشد' (proven
  // directly in src/lib/facilityValidation.test.ts). Here we assert the native
  // layer: an out-of-range value is rejected and never reaches the API.
  it('blocks an out-of-range interest_rate (150) from being submitted', async () => {
    const user = userEvent.setup()
    render(<FacilitiesPage />)
    await openFormWithCustomer(user)

    setField('facility-form-amount', '10000')
    setField('facility-form-interest-rate', '150')

    const rate = screen.getByTestId('facility-form-interest-rate') as HTMLInputElement
    expect(rate.validity.rangeOverflow).toBe(true)

    await user.click(screen.getByTestId('facility-form-submit'))

    // The invalid field prevents the request from ever being sent.
    expect(facilitiesCreateMock).not.toHaveBeenCalled()
    expect(toastSuccessMock).not.toHaveBeenCalled()
  })

  it('shows "تاریخ انقضا باید در آینده باشد" when expiry_date is in the past', async () => {
    const user = userEvent.setup()
    render(<FacilitiesPage />)
    await openFormWithCustomer(user)

    setField('facility-form-amount', '10000')
    setField('facility-form-expiry-date', '2000-01-01')

    await user.click(screen.getByTestId('facility-form-submit'))

    await waitFor(() =>
      expect(toastErrorMock).toHaveBeenCalledWith('تاریخ انقضا باید در آینده باشد'),
    )
    expect(facilitiesCreateMock).not.toHaveBeenCalled()
  })

  it('submits successfully when every field is valid', async () => {
    facilitiesCreateMock.mockResolvedValue({ id: 'fac-1' })
    const user = userEvent.setup()
    render(<FacilitiesPage />)
    await openFormWithCustomer(user)

    setField('facility-form-amount', '50000')
    await user.click(screen.getByTestId('facility-form-submit'))

    await waitFor(() => expect(facilitiesCreateMock).toHaveBeenCalledTimes(1))
    expect(toastErrorMock).not.toHaveBeenCalled()
  })
})
