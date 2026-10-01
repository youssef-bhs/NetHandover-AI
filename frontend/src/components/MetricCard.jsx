import { TrendingUp, TrendingDown } from 'lucide-react'

export default function MetricCard({
  title,
  value,
  unit = '',
  change,
  changeType = 'increase', // 'increase' or 'decrease' - good or bad
  icon: Icon,
  description
}) {
  const isPositive = changeType === 'increase'
  const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
  const changeIcon = isPositive ? TrendingUp : TrendingDown

  return (
    <div className="card-hover">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
          )}
          <div>
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-gray-900 dark:text-white">
                {value}
              </span>
              {unit && (
                <span className="text-sm text-gray-500 dark:text-gray-400">{unit}</span>
              )}
            </div>
            {description && (
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {description}
              </p>
            )}
          </div>
        </div>

        {change !== undefined && (
          <div className={`flex items-center gap-1 ${changeColor}`}>
            <changeIcon className="w-4 h-4" />
            <span className="text-sm font-medium">{change}%</span>
          </div>
        )}
      </div>
    </div>
  )
}
