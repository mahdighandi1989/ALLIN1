'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import Breadcrumb from '@/components/Breadcrumb'
import { customersApi, parseApiError } from '@/lib/api'
import { CustomerDetail } from '@/types'
import { ArrowLeft, Building, FileText, Wallet } from 'lucide-react'

function money(n: number | null | undefined, cur = 'AED') {
  return `${cur} ${Number(n || 0).toLocaleString()}`
}

function statusBadge(s: string | null | undefined) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return 'bg-green-100 text-green-700'
  if (v === 'closed' || v === 'inactive') return 'bg-gray-100 text-gray-700'
  return 'bg-yellow-100 text-yellow-700'
}

function CustomerDetailInner() {
  const params = useSearchParams()
  const router = useRouter()
  const id = params.get('id')
  const [data, setData] = useState<CustomerDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) {
      setError('No customer specified')
      setLoading(false)
      return
    }
    customersApi
      .detail(id)
      .then(setData)
      .catch((e) => setError(parseApiError(e)))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-lg mx-auto mt-8">
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4" data-testid="customer-detail-error">
          {error || 'Customer not found'}
        </div>
        <button onClick={() => router.push('/customers')} className="mt-4 px-4 py-2 border rounded-lg">
          Back to Customers
        </button>
      </div>
    )
  }

  const { customer, facilities, offer_letters, summary } = data

  return (
    <div data-testid="customer-detail-content">
      <Breadcrumb
        items={[
          { label: 'Customers', href: '/customers' },
          { label: customer.name },
        ]}
      />
      <button
        onClick={() => router.push('/customers')}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 mb-4"
      >
        <ArrowLeft size={16} /> Back to Customers
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">{customer.name}</h2>
          <p className="text-gray-500">
            {customer.account_no} · <span className="capitalize">{customer.account_type}</span>
            {customer.branch ? ` · ${customer.branch}` : ''}
          </p>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm ${statusBadge(customer.status)}`}>
          {customer.status}
        </span>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <SummaryCard icon={<Building size={16} />} label="Facilities"
          value={`${summary.total_facilities}`} sub={`${summary.active_facilities} active`} />
        <SummaryCard icon={<Wallet size={16} />} label="Total Exposure"
          value={money(summary.total_exposure, summary.currency)} />
        <SummaryCard icon={<Wallet size={16} />} label="Outstanding"
          value={money(summary.total_outstanding, summary.currency)} />
        <SummaryCard icon={<FileText size={16} />} label="Offer Letters"
          value={`${summary.total_offers}`} />
      </div>

      {/* Contact */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-8 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div><p className="text-gray-500">Email</p><p>{customer.email || '-'}</p></div>
        <div><p className="text-gray-500">Phone</p><p>{customer.phone || '-'}</p></div>
        <div><p className="text-gray-500">Mobile</p><p>{customer.mobile || '-'}</p></div>
        <div><p className="text-gray-500">Relationship Manager</p><p>{customer.relationship_manager || '-'}</p></div>
      </div>

      {/* Facilities */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-8">
        <div className="px-4 py-3 border-b font-medium">Facilities</div>
        {facilities.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left text-gray-500">
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2 text-right">Amount</th>
                <th className="px-4 py-2 text-right">Outstanding</th>
                <th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {facilities.map((f) => (
                <tr key={f.id}>
                  <td className="px-4 py-2">{f.name || '-'}</td>
                  <td className="px-4 py-2 uppercase">{f.facility_type}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{money(f.amount, f.currency)}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{money(f.outstanding, f.currency)}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${statusBadge(f.status)}`}>{f.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="px-4 py-6 text-gray-500 text-center">No facilities</p>
        )}
      </div>

      {/* Offer letters */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b font-medium">Offer Letters</div>
        {offer_letters.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left text-gray-500">
                <th className="px-4 py-2">Offer</th>
                <th className="px-4 py-2 text-right">Principal</th>
                <th className="px-4 py-2 text-right">Rate</th>
                <th className="px-4 py-2 text-right">Installment</th>
                <th className="px-4 py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {offer_letters.map((o) => (
                <tr
                  key={o.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push('/offer-letters')}
                >
                  <td className="px-4 py-2">{o.id}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{money(o.principal_amount, o.currency)}</td>
                  <td className="px-4 py-2 text-right">{o.interest_rate}%</td>
                  <td className="px-4 py-2 text-right tabular-nums">{money(o.monthly_installment, o.currency)}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${statusBadge(o.status)}`}>
                      {(o.status || '').replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="px-4 py-6 text-gray-500 text-center">No offer letters</p>
        )}
      </div>
    </div>
  )
}

function SummaryCard({ icon, label, value, sub }: {
  icon: React.ReactNode; label: string; value: string; sub?: string
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex items-center justify-between text-gray-500 mb-1">
        <span className="text-sm">{label}</span>
        {icon}
      </div>
      <div className="text-xl font-bold">{value}</div>
      {sub && <p className="text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

export default function CustomerDetailPage() {
  return (
    <Layout>
      <Suspense fallback={<div className="py-16 text-center text-gray-500">Loading…</div>}>
        <CustomerDetailInner />
      </Suspense>
    </Layout>
  )
}
