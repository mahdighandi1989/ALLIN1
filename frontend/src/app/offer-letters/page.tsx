'use client'

import { useEffect, useState } from 'react'
import Layout from '@/components/Layout'
import { offerLettersApi, customersApi, parseApiError } from '@/lib/api'
import { OfferLetter, OfferLetterList, OfferLetterDetail, OfferLetterForm as OfferForm, Customer } from '@/types'
import { Plus, FileText, Trash2, Eye } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  pending_approval: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  sent: 'bg-blue-100 text-blue-700',
  accepted: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  expired: 'bg-orange-100 text-orange-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

function money(n: number | null, cur = 'AED') {
  return `${cur} ${Number(n || 0).toLocaleString()}`
}

export default function OfferLettersPage() {
  const [data, setData] = useState<OfferLetterList | null>(null)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [detail, setDetail] = useState<OfferLetterDetail | null>(null)

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const load = async () => {
    try {
      setLoading(true)
      setData(await offerLettersApi.list({ page, page_size: 20 }))
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  const openDetail = async (id: string) => {
    try {
      // Generate the schedule so the detail always shows an amortisation table.
      const d = await offerLettersApi.generateSchedule(id)
      setDetail(d)
    } catch {
      try {
        setDetail(await offerLettersApi.get(id))
      } catch (e) {
        toast.error(parseApiError(e))
      }
    }
  }

  const handleDelete = async (o: OfferLetter) => {
    if (!confirm(`Delete offer ${o.id}?`)) return
    try {
      await offerLettersApi.delete(o.id)
      toast.success('Offer deleted')
      load()
    } catch (e) {
      toast.error(parseApiError(e))
    }
  }

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Offer Letters</h2>
        <button
          type="button"
          data-testid="add-offer-btn"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          New Offer
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden" data-testid="offer-letters-content">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Offer</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Principal</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Rate</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Tenor</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Installment</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <FileText size={15} className="text-gray-400" />
                        {o.id}
                      </div>
                      <span className="text-xs text-gray-400">{o.purpose_of_facility || ''}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right tabular-nums">{money(o.principal_amount, o.currency)}</td>
                    <td className="px-4 py-3 text-sm text-right">{o.interest_rate}%</td>
                    <td className="px-4 py-3 text-sm text-right">{o.tenor_months}m</td>
                    <td className="px-4 py-3 text-sm text-right tabular-nums">{money(o.monthly_installment, o.currency)}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[o.status || 'draft'] || 'bg-gray-100'}`}>
                        {(o.status || 'draft').replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        data-testid={`view-offer-${o.id}`}
                        aria-label="View offer"
                        onClick={() => openDetail(o.id)}
                        className="text-gray-500 hover:text-blue-600 mr-2"
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        type="button"
                        aria-label="Delete offer"
                        onClick={() => handleDelete(o)}
                        className="text-gray-500 hover:text-red-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t flex justify-between items-center">
              <span className="text-sm text-gray-500">
                Page {data.page} of {Math.ceil((data.total ?? 0) / (data.page_size || 1)) || 1}
              </span>
              <div className="flex gap-2">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50">Previous</button>
                <button onClick={() => setPage((p) => p + 1)}
                  disabled={page >= Math.ceil((data.total ?? 0) / (data.page_size || 1))}
                  className="px-3 py-1 border rounded disabled:opacity-50">Next</button>
              </div>
            </div>
          </>
        ) : (
          <div className="py-12 text-center text-gray-500">No offer letters yet</div>
        )}
      </div>

      {showForm && (
        <OfferFormModal onClose={() => setShowForm(false)} onSaved={() => { setShowForm(false); load() }} />
      )}
      {detail && <OfferDetailModal offer={detail} onClose={() => setDetail(null)} />}
    </Layout>
  )
}

function OfferFormModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<OfferForm>({
    customer_id: '',
    expiry_date: '',
    principal_amount: 0,
    interest_rate: 0,
    tenor_months: 12,
    currency: 'AED',
    repayment_type: 'monthly',
    grace_period_months: 0,
    purpose_of_facility: '',
  })

  useEffect(() => {
    customersApi.list({ page: 1, page_size: 100 }).then((r) => setCustomers(r.items)).catch(() => setCustomers([]))
  }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await offerLettersApi.create(form)
      toast.success('Offer created')
      onSaved()
    } catch (err) {
      toast.error(parseApiError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b"><h3 className="text-lg font-semibold">New Offer Letter</h3></div>
        <form onSubmit={submit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Customer *</label>
            <select value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg" required>
              <option value="">Select a customer…</option>
              {customers.map((c) => <option key={c.id} value={c.id}>{c.name} ({c.account_no})</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Principal *</label>
              <input type="number" min="1" step="0.01" value={form.principal_amount}
                onChange={(e) => setForm({ ...form, principal_amount: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Interest Rate % *</label>
              <input type="number" min="0" max="100" step="0.01" value={form.interest_rate}
                onChange={(e) => setForm({ ...form, interest_rate: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Tenor (months) *</label>
              <input type="number" min="1" max="600" value={form.tenor_months}
                onChange={(e) => setForm({ ...form, tenor_months: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Grace (months)</label>
              <input type="number" min="0" max="120" value={form.grace_period_months}
                onChange={(e) => setForm({ ...form, grace_period_months: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Repayment</label>
              <select value={form.repayment_type}
                onChange={(e) => setForm({ ...form, repayment_type: e.target.value as OfferForm['repayment_type'] })}
                className="w-full px-3 py-2 border rounded-lg">
                {['monthly', 'quarterly', 'semi_annual', 'annual', 'bullet'].map((r) => (
                  <option key={r} value={r}>{r.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium mb-1">Expiry Date *</label>
              <input type="date" value={form.expiry_date}
                onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg" required />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Currency</label>
              <input type="text" maxLength={3} value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Purpose</label>
            <input type="text" value={form.purpose_of_facility}
              onChange={(e) => setForm({ ...form, purpose_of_facility: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
            <button type="submit" disabled={saving}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function OfferDetailModal({ offer, onClose }: { offer: OfferLetterDetail; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold">Offer {offer.id}</h3>
          <span className="text-sm text-gray-500">{offer.customer_name}</span>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-b">
          <div><p className="text-gray-500">Principal</p><p className="font-semibold">{money(offer.principal_amount, offer.currency)}</p></div>
          <div><p className="text-gray-500">Rate</p><p className="font-semibold">{offer.interest_rate}%</p></div>
          <div><p className="text-gray-500">Tenor</p><p className="font-semibold">{offer.tenor_months} months</p></div>
          <div><p className="text-gray-500">Installment</p><p className="font-semibold">{money(offer.monthly_installment, offer.currency)}</p></div>
          <div><p className="text-gray-500">Total Repayment</p><p className="font-semibold">{money(offer.total_repayment_amount, offer.currency)}</p></div>
          <div><p className="text-gray-500">Repayment</p><p className="font-semibold">{(offer.repayment_type || '').replace('_', ' ')}</p></div>
          <div><p className="text-gray-500">Status</p><p className="font-semibold">{(offer.status || '').replace('_', ' ')}</p></div>
          <div><p className="text-gray-500">Expiry</p><p className="font-semibold">{offer.expiry_date || '-'}</p></div>
        </div>
        <div className="p-4">
          <h4 className="font-medium mb-2">Repayment Schedule</h4>
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 sticky top-0">
                <tr className="text-right text-gray-500">
                  <th className="px-2 py-2 text-left">#</th>
                  <th className="px-2 py-2 text-left">Date</th>
                  <th className="px-2 py-2">Opening</th>
                  <th className="px-2 py-2">Principal</th>
                  <th className="px-2 py-2">Interest</th>
                  <th className="px-2 py-2">Payment</th>
                  <th className="px-2 py-2">Closing</th>
                </tr>
              </thead>
              <tbody className="divide-y tabular-nums">
                {offer.schedule.map((s) => (
                  <tr key={s.installment_number} className="text-right">
                    <td className="px-2 py-1 text-left">{s.installment_number}</td>
                    <td className="px-2 py-1 text-left">{s.payment_date || '-'}</td>
                    <td className="px-2 py-1">{Math.round(s.opening_balance).toLocaleString()}</td>
                    <td className="px-2 py-1">{Math.round(s.principal_payment).toLocaleString()}</td>
                    <td className="px-2 py-1">{Math.round(s.interest_payment).toLocaleString()}</td>
                    <td className="px-2 py-1 font-medium">{Math.round(s.total_payment).toLocaleString()}</td>
                    <td className="px-2 py-1">{Math.round(s.closing_balance).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="p-4 border-t text-right">
          <button onClick={onClose} className="px-4 py-2 border rounded-lg hover:bg-gray-50">Close</button>
        </div>
      </div>
    </div>
  )
}
