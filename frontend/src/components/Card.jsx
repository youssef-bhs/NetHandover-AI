export default function Card({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  className = '',
  children
}) {
  const variantStyles = {
    default: 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700',
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    warning: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
    danger: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    primary: 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800',
  }

  const hasChildren = children !== undefined && children !== null

  return (
    <div className={`card border ${variantStyles[variant]} ${className}`}>
      {hasChildren ? (
        <>
          {title && (
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h3>
              {Icon && (
                <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700">
                  <Icon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                </div>
              )}
            </div>
          )}
          {children}
        </>
      ) : (
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {title}
            </p>
            <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
              {value}
            </p>
            {subtitle && (
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {subtitle}
              </p>
            )}
          </div>
          {Icon && (
            <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700">
              <Icon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
