/**
 * Data Import Page
 * صفحه وارد کردن داده‌ها از فایل‌های اکسل
 */
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Layout from '@/components/Layout'
import api from '@/services/api'
import { toast } from 'react-hot-toast'
import {
  Database, Upload, Play, CheckCircle, XCircle, RefreshCw,
  FileSpreadsheet, BarChart3, Loader2, AlertCircle, File
} from 'lucide-react'

interface FileInfo {
  name: string
  size: number
  modified: string
}

interface ImportStats {
  customers: number
  facilities: number
  properties: number
  guarantors: number
  tasks: number
  securities: number
  journal: number
  total: number
  errors: string[]
}

interface ImportResponse {
  success: boolean
  message: string
  stats: ImportStats
  files_processed: string[]
}

interface DbStats {
  customers: number
  facilities: number
  properties: number
  guarantors: number
  tasks: number
  securities: number
  journal: number
  total: number
}

export default function DataImportPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [files, setFiles] = useState<FileInfo[]>([])
  const [dbStats, setDbStats] = useState<DbStats | null>(null)
  const [importResult, setImportResult] = useState<ImportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [filesRes, statsRes] = await Promise.all([
        api.get('/data-import/files'),
        api.get('/data-import/stats'),
      ])
      setFiles(filesRes.data.files || [])
      setDbStats(statsRes.data)
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login')
        return
      }
      setError('Failed to load data: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const runImport = async () => {
    setImporting(true)
    setImportResult(null)
    setError(null)
    try {
      const res = await api.post('/data-import/run')
      setImportResult(res.data)
      toast.success(`Imported ${res.data.stats.total} records successfully!`)
      // Refresh stats after import
      const statsRes = await api.get('/data-import/stats')
      setDbStats(statsRes.data)
      // Refresh files list
      const filesRes = await api.get('/data-import/files')
      setFiles(filesRes.data.files || [])
    } catch (err: any) {
      if (err.response?.status === 401) {
        router.push('/login')
        return
      }
      const errorMsg = 'Import failed: ' + (err.response?.data?.detail || err.message)
      setError(errorMsg)
      toast.error(errorMsg)
    } finally {
      setImporting(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleString('en-US')
  }

  const statItems = [
    { key: 'customers', label: 'Customers', color: 'bg-blue-500' },
    { key: 'facilities', label: 'Facilities', color: 'bg-purple-500' },
    { key: 'properties', label: 'Properties', color: 'bg-green-500' },
    { key: 'guarantors', label: 'Guarantors', color: 'bg-cyan-500' },
    { key: 'tasks', label: 'Tasks', color: 'bg-yellow-500' },
    { key: 'securities', label: 'Securities', color: 'bg-red-500' },
    { key: 'journal', label: 'Journal', color: 'bg-gray-500' },
  ]

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-8 h-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">Data Import</h1>
              <p className="text-gray-500 text-sm">Import data from Excel files</p>
            </div>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <div className="flex-1">
              <p className="text-red-700">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              <XCircle className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Database Statistics */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold">Database Statistics</h2>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : dbStats ? (
            <div className="flex flex-wrap gap-3">
              {statItems.map(({ key, label, color }) => (
                <span
                  key={key}
                  className={`inline-flex items-center px-3 py-1.5 rounded-full text-white text-sm ${color}`}
                >
                  {label}: {dbStats[key as keyof DbStats]}
                </span>
              ))}
              <span className="inline-flex items-center px-3 py-1.5 rounded-full border-2 border-gray-300 text-gray-700 text-sm font-semibold">
                Total: {dbStats.total}
              </span>
            </div>
          ) : (
            <p className="text-gray-500">No data</p>
          )}
        </div>

        {/* Available Files */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileSpreadsheet className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold">Available Files for Import</h2>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : files.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-gray-600">File Name</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Size</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-600">Modified</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file) => (
                    <tr key={file.name} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <File className="w-4 h-4 text-green-600" />
                          {file.name}
                        </div>
                      </td>
                      <td className="text-right py-3 px-4 text-gray-600">{formatFileSize(file.size)}</td>
                      <td className="text-right py-3 px-4 text-gray-600">{formatDate(file.modified)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-700">
                No Excel files found in the data-import directory.
                <br />
                Please upload files to the <code className="bg-blue-100 px-1 rounded">data-import/</code> folder in the repository.
              </p>
            </div>
          )}
        </div>

        {/* Import Action */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-2 mb-4">
            <Upload className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold">Run Import</h2>
          </div>
          <p className="text-gray-600 mb-4">
            Click the button below to import data from all available Excel files into the database.
            This will create new records for customers, facilities, properties, guarantors, tasks, and securities.
          </p>
          <button
            onClick={runImport}
            disabled={importing || files.length === 0}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {importing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Start Import
              </>
            )}
          </button>
        </div>

        {/* Import Result */}
        {importResult && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-2 mb-4">
              {importResult.success ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <h2 className="text-lg font-semibold">Import Result</h2>
            </div>

            <div className={`rounded-lg p-4 mb-4 ${importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className={importResult.success ? 'text-green-700' : 'text-red-700'}>
                {importResult.message}
              </p>
            </div>

            {importResult.files_processed.length > 0 && (
              <div className="mb-4">
                <h3 className="font-medium text-gray-700 mb-2">Files Processed:</h3>
                <div className="flex flex-wrap gap-2">
                  {importResult.files_processed.map((file) => (
                    <span key={file} className="inline-flex items-center px-2 py-1 bg-gray-100 rounded text-sm">
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-4">
              <h3 className="font-medium text-gray-700 mb-2">Records Imported:</h3>
              <div className="flex flex-wrap gap-2">
                {statItems.map(({ key, label, color }) => (
                  <span
                    key={key}
                    className={`inline-flex items-center px-2 py-1 rounded text-white text-sm ${color}`}
                  >
                    {label}: {importResult.stats[key as keyof ImportStats]}
                  </span>
                ))}
                <span className="inline-flex items-center px-2 py-1 border rounded text-sm font-semibold">
                  Total: {importResult.stats.total}
                </span>
              </div>
            </div>

            {importResult.stats.errors.length > 0 && (
              <div>
                <h3 className="font-medium text-red-700 mb-2">Errors:</h3>
                <ul className="list-disc list-inside space-y-1">
                  {importResult.stats.errors.map((err, i) => (
                    <li key={i} className="text-red-600 text-sm">{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}
