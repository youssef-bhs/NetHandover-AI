import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react'

const QOS_META = {
  'Tres bonne': {
    tone: 'high',
    title: 'Excellent QoS',
    description: 'Strong signal quality and throughput headroom.',
  },
  Acceptable: {
    tone: 'medium',
    title: 'Acceptable QoS',
    description: 'Stable performance with room for improvement.',
  },
  'Assez bien': {
    tone: 'medium',
    title: 'Fair QoS',
    description: 'Moderate quality; monitor for degradation.',
  },
  Mauvaise: {
    tone: 'low',
    title: 'Poor QoS',
    description: 'Likely user impact; investigate causes.',
  },
}

const TONE_STYLES = {
  high: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200',
  medium: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200',
  low: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200',
}

const TONE_BADGE = {
  high: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
  low: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
}

export default function QosPredictionResult({ prediction, onExplain }) {
  const classLabel = prediction?.predicted_class || 'Unknown'
  const meta = QOS_META[classLabel] || {
    tone: 'medium',
    title: 'QoS Result',
    description: 'Prediction complete.',
  }
  const tone = meta.tone
  const ConfidenceIcon = {
    high: CheckCircle,
    medium: AlertTriangle,
    low: AlertTriangle,
  }[tone]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className={`p-5 rounded-lg border ${TONE_STYLES[tone]}`}>
        <div className="flex items-start gap-3">
          <ConfidenceIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold mb-1">{meta.title}</h4>
            <p className="text-sm">Predicted QoS: {classLabel}</p>
            <p className="text-xs mt-1">{meta.description}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Result Details</h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              Quality tier and summary based on the latest inputs.
            </p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${TONE_BADGE[tone]}`}>
            {classLabel}
          </span>
        </div>
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
