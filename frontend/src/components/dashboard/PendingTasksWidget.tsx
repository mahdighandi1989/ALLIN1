/**
 * Pending Tasks Widget
 * ویجت تسک‌های معلق
 */
import { Clock, AlertCircle, CheckCircle } from 'lucide-react'
import Link from 'next/link'

const mockTasks = [
  {
    id: '1',
    title: 'Follow up - ABC Trading Trade License',
    customer: 'ABC Trading LLC',
    priority: 'high',
    dueDate: '2025-01-15',
    daysOverdue: 0,
  },
  {
    id: '2',
    title: 'Collect financial statements',
    customer: 'XYZ Corporation',
    priority: 'medium',
    dueDate: '2025-01-20',
    daysOverdue: 0,
  },
  {
    id: '3',
    title: 'KYC Review - Annual Update',
    customer: 'Mohammad Ali',
    priority: 'high',
    dueDate: '2025-01-10',
    daysOverdue: 2,
  },
  {
    id: '4',
    title: 'Insurance renewal follow-up',
    customer: 'Gulf Trading FZE',
    priority: 'low',
    dueDate: '2025-01-25',
    daysOverdue: 0,
  },
]

const priorityColors: Record<string, string> = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
}

export default function PendingTasksWidget() {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Pending Tasks</h3>
        <Link href="/tasks" className="text-blue-600 text-sm hover:underline">
          View All
        </Link>
      </div>

      <div className="space-y-3">
        {mockTasks.map((task) => (
          <div
            key={task.id}
            className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="mt-0.5">
              {task.daysOverdue > 0 ? (
                <AlertCircle className="w-5 h-5 text-red-500" />
              ) : (
                <Clock className="w-5 h-5 text-gray-400" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">{task.title}</p>
              <p className="text-sm text-gray-500">{task.customer}</p>

              <div className="flex items-center gap-2 mt-2">
                <span className={`badge ${priorityColors[task.priority]}`}>
                  {task.priority}
                </span>
                <span className="text-xs text-gray-500">
                  {task.daysOverdue > 0 ? (
                    <span className="text-red-600">
                      {task.daysOverdue} days overdue
                    </span>
                  ) : (
                    `Due: ${task.dueDate}`
                  )}
                </span>
              </div>
            </div>

            <button className="p-1 hover:bg-green-100 rounded text-gray-400 hover:text-green-600">
              <CheckCircle size={18} />
            </button>
          </div>
        ))}
      </div>

      {mockTasks.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
          <p>All tasks completed!</p>
        </div>
      )}
    </div>
  )
}
