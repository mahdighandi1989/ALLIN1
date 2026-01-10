/**
 * Recent Activity Widget
 * ویجت فعالیت‌های اخیر
 */
import { UserPlus, FileEdit, CheckSquare, Upload, Trash2 } from 'lucide-react'

const mockActivities = [
  {
    id: '1',
    action: 'Customer profile updated',
    target: 'ABC Trading LLC',
    user: 'John Doe',
    time: '10 minutes ago',
    type: 'update',
  },
  {
    id: '2',
    action: 'New facility created',
    target: 'XYZ Corp - OD 2M',
    user: 'Jane Smith',
    time: '1 hour ago',
    type: 'create',
  },
  {
    id: '3',
    action: 'Checklist item completed',
    target: 'Trade License - Gulf Trading',
    user: 'Ahmed Ali',
    time: '2 hours ago',
    type: 'complete',
  },
  {
    id: '4',
    action: 'Document uploaded',
    target: 'Passport - Mohammad Hassan',
    user: 'John Doe',
    time: '3 hours ago',
    type: 'upload',
  },
  {
    id: '5',
    action: 'New customer added',
    target: 'Emirates Trading LLC',
    user: 'Jane Smith',
    time: '5 hours ago',
    type: 'create',
  },
]

const activityIcons: Record<string, JSX.Element> = {
  create: <UserPlus className="w-4 h-4 text-green-600" />,
  update: <FileEdit className="w-4 h-4 text-blue-600" />,
  complete: <CheckSquare className="w-4 h-4 text-purple-600" />,
  upload: <Upload className="w-4 h-4 text-orange-600" />,
  delete: <Trash2 className="w-4 h-4 text-red-600" />,
}

const activityColors: Record<string, string> = {
  create: 'bg-green-100',
  update: 'bg-blue-100',
  complete: 'bg-purple-100',
  upload: 'bg-orange-100',
  delete: 'bg-red-100',
}

export default function RecentActivityWidget() {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>

      <div className="space-y-4">
        {mockActivities.map((activity) => (
          <div key={activity.id} className="flex items-start gap-3">
            <div className={`p-2 rounded-full ${activityColors[activity.type]}`}>
              {activityIcons[activity.type]}
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">{activity.action}</p>
              <p className="text-sm text-gray-600 truncate">{activity.target}</p>
              <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                <span>{activity.user}</span>
                <span>•</span>
                <span>{activity.time}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
