/**
 * Reports Page v2.0
 * صفحه گزارشات
 */
import { useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import {
  BarChart3,
  Users,
  Wallet,
  Download,
  FileText,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import { reportsApi } from '@/services/api'

export default function ReportsPage() {
  const { isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [downloading, setDownloading] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    router.push('/login')
    return null
  }

  const downloadReport = async (type: 'customers' | 'facilities', format: 'json' | 'csv') => {
    setDownloading(`${type}-${format}`)
    try {
      const response = type === 'customers'
        ? await reportsApi.customers({ format })
        : await reportsApi.facilities({ format })

      if (format === 'csv') {
        // Handle CSV download
        const blob = new Blob([response.data], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_report.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        toast.success('Report downloaded successfully')
      } else {
        // Handle JSON - show data or download
        const jsonStr = JSON.stringify(response.data, null, 2)
        const blob = new Blob([jsonStr], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${type}_report.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        toast.success('Report downloaded successfully')
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to download report')
    } finally {
      setDownloading(null)
    }
  }

  const reportCards = [
    {
      title: 'Customers Report',
      description: 'Export all customer data including account info, status, and contact details.',
      icon: Users,
      color: 'blue',
      type: 'customers' as const,
    },
    {
      title: 'Facilities Report',
      description: 'Export all facility data including amounts, types, and expiry dates.',
      icon: Wallet,
      color: 'green',
      type: 'facilities' as const,
    },
  ]

  const colorClasses: Record<string, { bg: string; icon: string; border: string }> = {
    blue: { bg: 'bg-blue-50', icon: 'text-blue-600', border: 'border-blue-200' },
    green: { bg: 'bg-green-50', icon: 'text-green-600', border: 'border-green-200' },
    orange: { bg: 'bg-orange-50', icon: 'text-orange-600', border: 'border-orange-200' },
    purple: { bg: 'bg-purple-50', icon: 'text-purple-600', border: 'border-purple-200' },
  }

  return (
    <Layout>
      <Head>
        <title>Reports | Banking Operations System</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-500">Generate and download system reports</p>
        </div>

        {/* Report Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reportCards.map((report) => {
            const Icon = report.icon
            const colors = colorClasses[report.color]
            return (
              <div
                key={report.type}
                className={`bg-white rounded-xl shadow-sm border ${colors.border} p-6`}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 ${colors.bg} rounded-xl`}>
                    <Icon className={`w-6 h-6 ${colors.icon}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{report.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{report.description}</p>
                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={() => downloadReport(report.type, 'csv')}
                        disabled={downloading !== null}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 text-sm"
                      >
                        {downloading === `${report.type}-csv` ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                        CSV
                      </button>
                      <button
                        onClick={() => downloadReport(report.type, 'json')}
                        disabled={downloading !== null}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 text-sm"
                      >
                        {downloading === `${report.type}-json` ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <FileText className="w-4 h-4" />
                        )}
                        JSON
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Expiring Report Section */}
        <div className="bg-white rounded-xl shadow-sm border border-orange-200 p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-orange-50 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Expiring Facilities Report</h3>
              <p className="text-sm text-gray-500 mt-1">
                View facilities expiring within the next 30, 60, or 90 days.
              </p>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => router.push('/reports/expiring?days=30')}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm"
                >
                  30 Days
                </button>
                <button
                  onClick={() => router.push('/reports/expiring?days=60')}
                  className="px-4 py-2 border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 transition-colors text-sm"
                >
                  60 Days
                </button>
                <button
                  onClick={() => router.push('/reports/expiring?days=90')}
                  className="px-4 py-2 border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 transition-colors text-sm"
                >
                  90 Days
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="w-6 h-6" />
            <h3 className="font-semibold text-lg">Quick Tip</h3>
          </div>
          <p className="text-blue-100">
            Export your data regularly to maintain backups. CSV format works best for Excel,
            while JSON is ideal for data processing and integrations.
          </p>
        </div>
      </div>
    </Layout>
  )
}
