/**
 * Expiring Documents Widget
 * ویجت مدارک در حال انقضا
 */
import { AlertTriangle, FileWarning, Calendar } from 'lucide-react'
import Link from 'next/link'

const mockExpiring = [
  {
    id: '1',
    document: 'Trade License',
    customer: 'ABC Trading LLC',
    expiryDate: '2025-01-25',
    daysRemaining: 17,
  },
  {
    id: '2',
    document: 'Passport',
    customer: 'Mohammad Ali',
    expiryDate: '2025-02-10',
    daysRemaining: 33,
  },
  {
    id: '3',
    document: 'Visa',
    customer: 'Ahmed Hassan',
    expiryDate: '2025-01-20',
    daysRemaining: 12,
  },
  {
    id: '4',
    document: 'Emirates ID',
    customer: 'Gulf Trading FZE',
    expiryDate: '2025-02-28',
    daysRemaining: 51,
  },
]

function getUrgencyColor(days: number) {
  if (days <= 7) return 'text-red-600 bg-red-50'
  if (days <= 30) return 'text-orange-600 bg-orange-50'
  return 'text-yellow-600 bg-yellow-50'
}

export default function ExpiringDocsWidget() {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-orange-500" />
          Expiring Documents
        </h3>
        <span className="badge bg-orange-100 text-orange-800">
          {mockExpiring.length} items
        </span>
      </div>

      <div className="space-y-3">
        {mockExpiring.map((doc) => (
          <div
            key={doc.id}
            className={`p-3 rounded-lg ${getUrgencyColor(doc.daysRemaining)}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">{doc.document}</p>
                <p className="text-sm opacity-75">{doc.customer}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">{doc.daysRemaining} days</p>
                <p className="text-xs opacity-75">{doc.expiryDate}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {mockExpiring.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileWarning className="w-12 h-12 mx-auto mb-2 text-green-500" />
          <p>No expiring documents</p>
        </div>
      )}

      <Link
        href="/reports/expiring"
        className="block text-center mt-4 text-blue-600 text-sm hover:underline"
      >
        View Full Report
      </Link>
    </div>
  )
}
