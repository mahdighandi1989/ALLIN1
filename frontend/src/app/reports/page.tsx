'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Layout from '@/components/Layout'
import { reportsApi, parseApiError, downloadFile } from '@/lib/api'
import { PortfolioReport, TopExposures } from '@/types'
import { DonutChart, BarChart } from '@/components/charts'
import { RefreshCw, Download } from 'lucide-react'
import toast from 'react-hot-toast'

function money(n: number, cur = 'AED') {
  return `${cur} ${Number(n || 0).toLocaleString()}`
}

export default function ReportsPage() {
  const router = useRouter()
  const [report, setReport] = useState<PortfolioReport | null>(null)
  const [top, setTop] = useState<TopExposures | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [r, t] = await Promise.all([
        reportsApi.portfolio(),
        reportsApi.topExposures(10),
      ])
      setReport(r)
      setTop(t)
    } catch (e) {
      setError(parseApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </Layout>
    )
  }

  if (error || !report) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto mt-8 bg-red-50 border border-red-200 text-red-800 rounded-lg p-4" data-testid="reports-error">
          {error || 'Unable to load report'}
        </div>
      </Layout>
    )
  }

  const s = report.summary

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Portfolio Report</h2>
        <div className="flex gap-2">
          <button
            data-testid="report-export-pdf"
            onClick={() =>
              downloadFile('/api/reports/portfolio/export.pdf', 'portfolio-report.pdf')
                .catch((e) => toast.error(parseApiError(e)))
            }
            className="flex items-center gap-2 px-3 py-2 border rounded-lg hover:bg-gray-50"
          >
            <Download size={16} /> PDF
          </button>
          <button
            data-testid="report-export-csv"
            onClick={() =>
              downloadFile('/api/reports/portfolio/export.csv', 'portfolio-exposures.csv')
                .catch((e) => toast.error(parseApiError(e)))
            }
            className="flex items-center gap-2 px-3 py-2 border rounded-lg hover:bg-gray-50"
          >
            <Download size={16} /> CSV
          </button>
          <button onClick={load} className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8" data-testid="reports-summary">
        <Kpi label="Customers" value={`${s.total_customers}`} />
        <Kpi label="Facilities" value={`${s.total_facilities}`} />
        <Kpi label="Total Exposure" value={money(s.total_exposure, s.currency)} />
        <Kpi label="Outstanding" value={money(s.total_outstanding, s.currency)} />
        <Kpi label="Utilisation" value={`${s.utilisation_pct}%`} sub={`Headroom ${money(s.available_headroom, s.currency)}`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Panel title="Exposure by Facility Type">
          <DonutChart data={report.facilities_by_type} valueKey="amount" />
        </Panel>
        <Panel title="Exposure by Risk Rating">
          <BarChart data={report.facilities_by_risk} valueKey="amount" />
        </Panel>
        <Panel title="Facilities by Status">
          <BarChart data={report.facilities_by_status} valueKey="count" />
        </Panel>
        <Panel title="Customers by Branch">
          <BarChart data={report.customers_by_branch} valueKey="count" />
        </Panel>
      </div>

      <Panel title="Top 10 Exposures">
        {top && top.items.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left text-gray-500">
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">Customer</th>
                <th className="px-3 py-2">Account</th>
                <th className="px-3 py-2 text-right">Facilities</th>
                <th className="px-3 py-2 text-right">Exposure</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {top.items.map((c, i) => (
                <tr
                  key={c.customer_id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/customer-detail?id=${c.customer_id}`)}
                >
                  <td className="px-3 py-2 text-gray-400">{i + 1}</td>
                  <td className="px-3 py-2 font-medium">{c.name}</td>
                  <td className="px-3 py-2 text-gray-500">{c.account_no || '-'}</td>
                  <td className="px-3 py-2 text-right">{c.facilities}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{money(c.exposure)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-500 py-6 text-center">No exposure data</p>
        )}
      </Panel>
    </Layout>
  )
}

function Kpi({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xl font-bold">{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="px-4 py-3 border-b font-medium">{title}</div>
      <div className="p-4">{children}</div>
    </div>
  )
}
