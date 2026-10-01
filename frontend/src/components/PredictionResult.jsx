import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

const CONFIDENCE_COLORS = {
  high: '#22c55e',
  medium: '#f59e0b',
  low: '#ef4444',
}

export default function PredictionResult({ prediction, onExplain }) {
  const classLabel = prediction.predicted_class || prediction.class || prediction.class_label || 'Unknown'
  const confidence = typeof prediction.confidence === 'number' ? prediction.confidence : null
  const probabilityEntries = Object.entries(prediction.probabilities || {})
    .map(([label, value]) => ({
      label,
      probability: Number(value) * 100,
    }))
    .sort((a, b) => b.probability - a.probability)

  const getConfidenceLevel = (value) => {
    if (value >= 85) return 'high'
    if (value >= 70) return 'medium'
    return 'low'
  }

  const confidenceLevel = getConfidenceLevel(confidence ?? 0)
  const confidenceIcon = {
    high: CheckCircle,
    medium: AlertTriangle,
    low: AlertTriangle,
  }[confidenceLevel]
  const ConfidenceIcon = confidenceIcon

  return (
    <div className="space-y-6 animate-fade-in">
      <div className={`p-4 rounded-lg border ${
        confidenceLevel === 'high'
          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200'
          : confidenceLevel === 'medium'
            ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200'
            : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
      }`}>
        <div className="flex items-start gap-3">
          <ConfidenceIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold mb-1">Predicted Coverage Class</h4>
            <p className="text-sm">{classLabel}</p>
            <p className="text-xs mt-1">
              Confidence: {confidence !== null ? `${confidence.toFixed(2)}%` : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Confidence Score
        </h3>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-300">Model confidence</span>
            <span className="font-semibold text-gray-900 dark:text-white">
              {confidence !== null ? `${confidence.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-1000 ease-out"
              style={{
                width: `${confidence ?? 0}%`,
                backgroundColor: CONFIDENCE_COLORS[confidenceLevel],
              }}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Class Probabilities
        </h3>
        {probabilityEntries.length ? (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={probabilityEntries} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="label" width={160} />
              <Tooltip
                formatter={(value) => [`${value.toFixed(2)}%`, 'Probability']}
                contentStyle={{
                  backgroundColor: 'var(--tw-colors-white)',
                  border: '1px solid var(--tw-colors-gray-200)',
                  borderRadius: '0.5rem',
                }}
              />
              <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                {probabilityEntries.map((entry, index) => {
                  const level = entry.probability >= 70 ? 'high' : entry.probability >= 40 ? 'medium' : 'low'
                  return <Cell key={`cell-${index}`} fill={CONFIDENCE_COLORS[level]} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            No class probability data available.
          </div>
        )}
      </div>

      {onExplain && (
        <div className="flex justify-end">
          <button onClick={onExplain} className="btn-primary flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            Analyze with AI
          </button>
        </div>
      )}
    </div>
  )
}
