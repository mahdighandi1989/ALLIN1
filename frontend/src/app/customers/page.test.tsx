/**
 * Interaction tests for the Customers page (AC3 — ui_interaction).
 *
 * Background: the automated stale_detector flagged the "Add Customer" button
 * (`onClick={() => { setEditingCustomer(null); setShowForm(true) }}`) as having
 * no handler. `git blame` on that line (commit 7f29d58, 2026-05-30) shows the
 * onClick has been attached since the button was introduced — the detector
 * tripped on a multi-line JSX attribute and never saw it. This is **case (a)**:
 * the handler is present and works.
 *
 * Rather than only asserting the wiring in source (see
 * tests/test_customers_buttons_wired.py), these tests render the real component
 * in jsdom and actually *click* the buttons, then assert on the resulting DOM —
 * the behaviour-level contract AC3 asks for. React Testing Library + userEvent
 * is the Next.js-recommended, equivalent alternative to a Playwright/Cypress
 * end-to-end harness (the project ships no running browser/dev-server in CI),
 * and exercises the exact same observable outcome: clicking a button does
 * something visible.
 */
import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { Customer, CustomerList } from '@/types'

// --- Mocks ------------------------------------------------------------------
// Isolate the page from routing, layout chrome and the network layer so the
// test observes only the page's own click behaviour.

const pushMock = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushMock }),
}))

// Layout pulls in auth/notification chrome that is irrelevant here; render its
// children straight through.
jest.mock('@/components/Layout', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const listMock = jest.fn()
const createMock = jest.fn()
const updateMock = jest.fn()
const deleteMock = jest.fn()
jest.mock('@/lib/api', () => ({
  customersApi: {
    list: (...args: unknown[]) => listMock(...args),
    create: (...args: unknown[]) => createMock(...args),
    update: (...args: unknown[]) => updateMock(...args),
    delete: (...args: unknown[]) => deleteMock(...args),
    bulkDelete: jest.fn(),
  },
  parseApiError: (e: unknown) => String(e),
  downloadFile: jest.fn().mockResolvedValue(undefined),
}))

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: { success: jest.fn(), error: jest.fn() },
}))

import CustomersPage from './page'

function makeCustomer(overrides: Partial<Customer> = {}): Customer {
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
    ...overrides,
  }
}

function makeList(items: Customer[]): CustomerList {
  return { items, total: items.length, page: 1, page_size: 20 }
}

beforeEach(() => {
  jest.clearAllMocks()
  listMock.mockResolvedValue(makeList([makeCustomer()]))
})

describe('Customers page button interactions', () => {
  it('opens a blank "New Customer" form when the Add Customer button is clicked', async () => {
    const user = userEvent.setup()
    render(<CustomersPage />)

    // Wait for the initial load to settle (row rendered).
    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()

    // No form on screen before the click.
    expect(screen.queryByText('New Customer')).not.toBeInTheDocument()

    await user.click(screen.getByTestId('add-customer-btn'))

    // Clicking the flagged button must reveal the new-customer form.
    expect(await screen.findByText('New Customer')).toBeInTheDocument()
    // It's a *blank* form: account number empty (not pre-filled from a row).
    const accountInput = screen.getByTestId('customer-form-account-no') as HTMLInputElement
    expect(accountInput.value).toBe('')
  })

  it('opens a pre-filled "Edit Customer" form when a row edit button is clicked', async () => {
    const user = userEvent.setup()
    render(<CustomersPage />)

    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()

    await user.click(screen.getByTestId('edit-customer-cust-1'))

    expect(await screen.findByText('Edit Customer')).toBeInTheDocument()
    const nameInput = screen.getByTestId('customer-form-name') as HTMLInputElement
    expect(nameInput.value).toBe('Acme Corp')
  })

  it('calls the delete API when the row delete button is confirmed', async () => {
    const user = userEvent.setup()
    deleteMock.mockResolvedValue(undefined)
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true)

    render(<CustomersPage />)
    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()

    await user.click(screen.getByTestId('delete-customer-cust-1'))

    await waitFor(() => expect(deleteMock).toHaveBeenCalledWith('cust-1'))
    confirmSpy.mockRestore()
  })

  it('navigates to the customer detail page when the name button is clicked', async () => {
    const user = userEvent.setup()
    render(<CustomersPage />)

    await user.click(await screen.findByTestId('view-customer-cust-1'))

    expect(pushMock).toHaveBeenCalledWith('/customer-detail?id=cust-1')
  })

  it('submitting the new-customer form invokes the create API', async () => {
    const user = userEvent.setup()
    createMock.mockResolvedValue(makeCustomer())
    render(<CustomersPage />)

    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()
    await user.click(screen.getByTestId('add-customer-btn'))

    await screen.findByText('New Customer')
    const form = screen.getByTestId('customer-form')

    await user.type(screen.getByTestId('customer-form-account-no'), 'ACC-999')
    await user.type(screen.getByTestId('customer-form-name'), 'New Client')
    await user.click(within(form).getByRole('button', { name: /^Save$/i }))

    await waitFor(() =>
      expect(createMock).toHaveBeenCalledWith(
        expect.objectContaining({ account_no: 'ACC-999', name: 'New Client' }),
      ),
    )
  })
})
