'use client'

import { useState } from 'react'
import Layout from '@/components/Layout'
import { importsApi, downloadFile, parseApiError } from '@/lib/api'
import { ImportResult } from '@/types'
import { Upload, Download, FileSpreadsheet, CheckCircle2, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

type Kind = 'customers' | 'facilities'

export default function ImportPage() {
  const [kind, setKind] = useState<Kind>('customers')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)

  const run = async (dryRun: boolean) => {
    if (!file) {
      toast.error('Please choose a file first')
      return
    }
    setBusy(true)
    setResult(null)
    try {
      const res = kind === 'customers'
        ? await importsApi.customers(file, dryRun)
        : await importsApi.facilities(file, dryRun)
      setResult(res)
      if (dryRun) {
        toast.success(`Validated: ${res.would_create} would be created`)
      } else {
        toast.success(`Imported ${res.created} ${kind}`)
      }
    } catch (e) {
      toast.error(parseApiError(e))
    } finally {
      setBusy(false)
    }
  }

  const downloadTemplate = () => {
    downloadFile(`/api/imports/${kind}/template`, `${kind}-template.csv`)
      .catch((e) => toast.error(parseApiError(e)))
  }

  return (
    <Layout>
      <div className="flex items-center gap-2 mb-6">
        <FileSpreadsheet size={22} className="text-gray-500" />
        <h2 className="text-2xl font-bold">Import from Excel</h2>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">What to import</label>
            <div className="flex gap-2" data-testid="import-kind">
              {(['customers', 'facilities'] as Kind[]).map((k) => (
                <button key={k} type="button"
                  onClick={() => { setKind(k); setResult(null) }}
                  className={`px-4 py-2 rounded-lg border text-sm capitalize ${
                    kind === k ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'
                  }`}>
                  {k}
                </button>
              ))}
            </div>
          </div>

          <div className="text-sm text-gray-500">
            {kind === 'customers'
              ? 'Columns: account_no, name, account_type, email, phone, branch, status. account_no + name required.'
              : 'Columns: account_no (existing customer), name, facility_type, amount, currency, interest_rate, status. account_no + amount required.'}
            <button onClick={downloadTemplate} className="ml-2 inline-flex items-center gap-1 text-blue-600 hover:underline">
              <Download size={14} /> template
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Excel file (.xlsx / .xlsm)</label>
            <input type="file" accept=".xlsx,.xlsm" data-testid="import-file"
              onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null) }}
              className="block w-full text-sm border rounded-lg p-2" />
          </div>

          <div className="flex gap-2">
            <button onClick={() => run(true)} disabled={busy || !file}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50">
              {busy ? 'Working…' : 'Validate (dry run)'}
            </button>
            <button onClick={() => run(false)} disabled={busy || !file} data-testid="import-run"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
              <Upload size={16} /> {busy ? 'Importing…' : 'Import'}
            </button>
          </div>
        </div>

        {result && (
          <div className="bg-white rounded-lg shadow-sm p-6" data-testid="import-result">
            <div className="flex items-center gap-2 mb-3">
              {result.errors.length === 0
                ? <CheckCircle2 size={18} className="text-green-600" />
                : <AlertTriangle size={18} className="text-yellow-600" />}
              <h3 className="font-medium">
                {result.dry_run ? 'Validation result' : 'Import result'}
              </h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm mb-4">
              <Stat label="Rows" value={result.total_rows} />
              <Stat label={result.dry_run ? 'Would create' : 'Created'} value={result.dry_run ? result.would_create : result.created} />
              {result.skipped_existing != null && <Stat label="Skipped (existing)" value={result.skipped_existing} />}
              <Stat label="Errors" value={result.errors.length} />
            </div>
            {result.errors.length > 0 && (
              <div className="max-h-60 overflow-y-auto border rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50"><tr className="text-left text-gray-500">
                    <th className="px-3 py-2 w-20">Row</th><th className="px-3 py-2">Error</th>
                  </tr></thead>
                  <tbody className="divide-y">
                    {result.errors.map((e, i) => (
                      <tr key={i}>
                        <td className="px-3 py-1.5 text-gray-500">{e.row}</td>
                        <td className="px-3 py-1.5 text-red-600">{e.error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xl font-bold">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}
