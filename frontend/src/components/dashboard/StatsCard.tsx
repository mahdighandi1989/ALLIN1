/**
 * Stats Card Component
 * کامپوننت کارت آمار
 */
import { ReactNode } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  change?: string
  changeType?: 'increase' | 'decrease' | 'neutral' | 'warning'
  icon: ReactNode
  color: 'blue' | 'green' | 'orange' | 'red' | 'purple'
}

const colorStyles = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-green-50 text-green-600',
  orange: 'bg-orange-50 text-orange-600',
  red: 'bg-red-50 text-red-600',
  purple: 'bg-purple-50 text-purple-600',
}

const changeColors = {
  increase: 'text-green-600',
  decrease: 'text-green-600',
  neutral: 'text-gray-500',
  warning: 'text-red-600',
}

export default function StatsCard({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  color,
}: StatsCardProps) {
  const ChangeIcon =
    changeType === 'increase' ? TrendingUp :
    changeType === 'decrease' ? TrendingDown : Minus

  return (
    <div className="card card-hover">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>

          {change && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${changeColors[changeType]}`}>
              <ChangeIcon size={14} />
              <span>{change}</span>
            </div>
          )}
        </div>

        <div className={`p-3 rounded-lg ${colorStyles[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
