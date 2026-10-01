import { useEffect, useMemo, useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const DEFAULT_FEATURE_META = {
  rsrp: {
    label: 'RSRP (dBm)',
    default: -95.0,
    example: -95.0,
    min: -140,
    max: -40,
    step: 0.1,
    help: 'Reference Signal Received Power',
    group: 'RSRP History',
  },
  rsrq: {
    label: 'RSRQ (dB)',
    default: -11.2,
    example: -11.2,
    min: -30,
    max: 0,
    step: 0.1,
    help: 'Reference Signal Received Quality',
    group: 'Signal and Cell',
  },
  rlc_dl: {
    label: 'RLC DL',
    default: 320,
    example: 320,
    min: 0,
    max: 10000,
    step: 1,
    help: 'Downlink throughput indicator',
    group: 'Signal and Cell',
  },
  pci: {
    label: 'PCI',
    default: 101,
    example: 101,
    min: 0,
    max: 503,
    step: 1,
    help: 'Physical Cell Identity',
    group: 'Signal and Cell',
  },
  band_enc: {
    label: 'Band Enc',
    default: 3,
    example: 3,
    min: 0,
    max: 10,
    step: 1,
    help: 'Encoded band index',
    group: 'Signal and Cell',
  },
  hour: {
    label: 'Hour',
    default: 14,
    example: 14,
    min: 0,
    max: 23,
    step: 1,
    help: 'Hour of day',
    group: 'Time',
  },
  minute: {
    label: 'Minute',
    default: 30,
    example: 30,
    min: 0,
    max: 59,
    step: 1,
    help: 'Minute of hour',
    group: 'Time',
  },
  second: {
    label: 'Second',
    default: 12,
    example: 12,
    min: 0,
    max: 59,
    step: 1,
    help: 'Second of minute',
    group: 'Time',
  },
  rsrq_lag1: {
    label: 'RSRQ Lag 1',
    default: -11.0,
    example: -11.0,
    min: -30,
    max: 0,
    step: 0.1,
    help: 'Previous sample',
    group: 'RSRQ History',
  },
  rsrq_lag2: {
    label: 'RSRQ Lag 2',
    default: -10.8,
    example: -10.8,
    min: -30,
    max: 0,
    step: 0.1,
    help: 'Two samples back',
    group: 'RSRQ History',
  },
  rsrq_roll3: {
    label: 'RSRQ Roll 3',
    default: -11.1,
    example: -11.1,
    min: -30,
    max: 0,
    step: 0.1,
    help: 'Rolling mean over 3 samples',
    group: 'RSRQ History',
  },
  rsrq_roll5: {
    label: 'RSRQ Roll 5',
    default: -11.3,
    example: -11.3,
    min: -30,
    max: 0,
    step: 0.1,
    help: 'Rolling mean over 5 samples',
    group: 'RSRQ History',
  },
  rlc_dl_lag1: {
    label: 'RLC DL Lag 1',
    default: 315,
    example: 315,
    min: 0,
    max: 10000,
    step: 1,
    help: 'Previous sample',
    group: 'RLC DL History',
  },
  rlc_dl_lag2: {
    label: 'RLC DL Lag 2',
    default: 310,
    example: 310,
    min: 0,
    max: 10000,
    step: 1,
    help: 'Two samples back',
    group: 'RLC DL History',
  },
  rlc_dl_roll3: {
    label: 'RLC DL Roll 3',
    default: 318,
    example: 318,
    min: 0,
    max: 10000,
    step: 1,
    help: 'Rolling mean over 3 samples',
    group: 'RLC DL History',
  },
  rlc_dl_roll5: {
    label: 'RLC DL Roll 5',
    default: 322,
    example: 322,
    min: 0,
    max: 10000,
    step: 1,
    help: 'Rolling mean over 5 samples',
    group: 'RLC DL History',
  },
  rsrp_lag1: {
    label: 'RSRP Lag 1',
    default: -95.5,
    example: -95.5,
    min: -140,
    max: -40,
    step: 0.1,
    help: 'Previous sample',
    group: 'RSRP History',
  },
  rsrp_lag2: {
    label: 'RSRP Lag 2',
    default: -96.0,
    example: -96.0,
    min: -140,
    max: -40,
    step: 0.1,
    help: 'Two samples back',
    group: 'RSRP History',
  },
  rsrp_roll3: {
    label: 'RSRP Roll 3',
    default: -95.3,
    example: -95.3,
    min: -140,
    max: -40,
    step: 0.1,
    help: 'Rolling mean over 3 samples',
    group: 'RSRP History',
  },
  rsrp_roll5: {
    label: 'RSRP Roll 5',
    default: -95.2,
    example: -95.2,
    min: -140,
    max: -40,
    step: 0.1,
    help: 'Rolling mean over 5 samples',
    group: 'RSRP History',
  },
}

const GROUP_ORDER = [
  'Signal and Cell',
  'Time',
  'RSRP History',
  'RSRQ History',
  'RLC DL History',
  'Other Features',
]

const FALLBACK_FEATURE_COLS = [
  'RSRP',
  'RSRQ',
  'RLC_DL',
  'PCI',
  'Band_enc',
  'hour',
  'minute',
  'second',
  'RSRP_lag1',
  'RSRP_lag2',
  'RSRP_roll3',
  'RSRP_roll5',
  'RSRQ_lag1',
  'RSRQ_lag2',
  'RSRQ_roll3',
  'RSRQ_roll5',
  'RLC_DL_lag1',
  'RLC_DL_lag2',
  'RLC_DL_roll3',
  'RLC_DL_roll5',
]

const buildClassExample = (rsrp, rsrq, rlc) => ({
  RSRP: rsrp,
  RSRQ: rsrq,
  RLC_DL: rlc,
  PCI: 227,
  Band_enc: 1,
  hour: 10,
  minute: 30,
  second: 15,
  RSRP_lag1: rsrp - 0.5,
  RSRP_lag2: rsrp - 1.0,
  RSRP_roll3: rsrp - 0.3,
  RSRP_roll5: rsrp - 0.2,
  RSRQ_lag1: rsrq - 0.2,
  RSRQ_lag2: rsrq - 0.4,
  RSRQ_roll3: rsrq - 0.1,
  RSRQ_roll5: rsrq - 0.1,
  RLC_DL_lag1: rlc - 0.5,
  RLC_DL_lag2: rlc - 0.8,
  RLC_DL_roll3: rlc - 0.3,
  RLC_DL_roll5: rlc - 0.2,
})

const CLASS_EXAMPLES = {
  'Tres bonne': buildClassExample(-72.0, -5.0, 25.0),
  Bonne: buildClassExample(-85.0, -8.3, 11.8),
  Moyenne: buildClassExample(-95.0, -9.3, 10.3),
  Mauvaise: buildClassExample(-110.0, -10.4, 8.5),
}

const normalizeKey = (key) => String(key).toLowerCase().replace(/[^a-z0-9]/g, '')

const toLabel = (key) => key.replace(/_/g, ' ')

const buildFeatureDefs = (featureCols, featureStats) => {
  const cols = Array.isArray(featureCols) && featureCols.length
    ? featureCols
    : FALLBACK_FEATURE_COLS
  const metaMap = new Map(
    Object.entries(DEFAULT_FEATURE_META).map(([key, value]) => [normalizeKey(key), value])
  )
  const statsMap = new Map()
  if (featureStats && typeof featureStats === 'object') {
    Object.entries(featureStats).forEach(([key, value]) => {
      if (value && typeof value.mean === 'number') {
        statsMap.set(normalizeKey(key), value)
      }
    })
  }
  return cols.map((col) => {
    const meta = metaMap.get(normalizeKey(col))
    const stats = statsMap.get(normalizeKey(col))
    const mean = stats?.mean
    const std = stats?.std
    const stepValue = meta?.step ?? 0.1
    const defaultValue = Number.isFinite(mean) ? mean : meta?.default
    const exampleValue = Number.isFinite(mean) ? mean : meta?.example
    const minValue = meta?.min ?? (Number.isFinite(mean) && Number.isFinite(std)
      ? mean - std * 3
      : undefined)
    const maxValue = meta?.max ?? (Number.isFinite(mean) && Number.isFinite(std)
      ? mean + std * 3
      : undefined)
    const resolvedDefault = Number.isFinite(defaultValue) ? defaultValue : meta?.default
    const resolvedExample = Number.isFinite(exampleValue) ? exampleValue : meta?.example
    const normalizedDefault = Number.isFinite(resolvedDefault)
      ? (stepValue === 1 ? Math.round(resolvedDefault) : resolvedDefault)
      : meta?.default
    const normalizedExample = Number.isFinite(resolvedExample)
      ? (stepValue === 1 ? Math.round(resolvedExample) : resolvedExample)
      : meta?.example

    if (meta) {
      return {
        key: col,
        ...meta,
        default: normalizedDefault,
        example: normalizedExample,
        min: Number.isFinite(minValue) ? minValue : meta.min,
        max: Number.isFinite(maxValue) ? maxValue : meta.max,
        step: stepValue,
      }
    }
    return {
      key: col,
      label: toLabel(col),
      default: Number.isFinite(defaultValue) ? defaultValue : 0,
      example: Number.isFinite(exampleValue) ? exampleValue : 0,
      step: stepValue,
      help: 'Model feature',
      group: 'Other Features',
      min: Number.isFinite(minValue) ? minValue : undefined,
      max: Number.isFinite(maxValue) ? maxValue : undefined,
    }
  })
}

const buildInitialState = (defs, valueKey = 'default') => {
  const initial = {}
  defs.forEach((def) => {
    const value = def[valueKey]
    if (typeof value === 'number' && !Number.isNaN(value)) {
      initial[def.key] = value
      return
    }
    if (typeof def.default === 'number' && !Number.isNaN(def.default)) {
      initial[def.key] = def.default
      return
    }
    initial[def.key] = 0
  })
  return initial
}

const groupFeatures = (defs) => {
  const groups = new Map()
  defs.forEach((def) => {
    const name = def.group || 'Other Features'
    if (!groups.has(name)) {
      groups.set(name, [])
    }
    groups.get(name).push(def)
  })

  const ordered = []
  GROUP_ORDER.forEach((name) => {
    if (groups.has(name)) {
      ordered.push({ name, features: groups.get(name) })
    }
  })

  for (const [name, features] of groups.entries()) {
    if (!GROUP_ORDER.includes(name)) {
      ordered.push({ name, features })
    }
  }

  return ordered
}

const coerceNumber = (value) => {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim() !== '') {
    const num = Number(value)
    return Number.isFinite(num) ? num : null
  }
  return null
}

export default function PredictionForm({ onSubmit, loading, onExplain, featureCols, featureStats }) {
  const featureDefs = useMemo(
    () => buildFeatureDefs(featureCols, featureStats),
    [featureCols, featureStats]
  )
  const featureGroups = useMemo(() => groupFeatures(featureDefs), [featureDefs])
  const [features, setFeatures] = useState(() => buildInitialState(featureDefs))

  useEffect(() => {
    setFeatures((prev) => {
      const next = {}
      featureDefs.forEach((def) => {
        if (Object.prototype.hasOwnProperty.call(prev, def.key)) {
          next[def.key] = prev[def.key]
        } else {
          next[def.key] = def.default ?? 0
        }
      })
      return next
    })
  }, [featureDefs])

  const updateFeature = (key, value) => {
    setFeatures(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const normalized = {}
      const invalid = []

      featureDefs.forEach((def) => {
        if (def.type === 'checkbox') {
          normalized[def.key] = features[def.key] ? 1 : 0
          return
        }
        const rawValue = features[def.key]
        if (
          rawValue === '' ||
          rawValue === null ||
          typeof rawValue === 'undefined' ||
          (typeof rawValue === 'string' && rawValue.trim() === '')
        ) {
          normalized[def.key] = 0
          return
        }
        const numericValue = coerceNumber(rawValue)
        if (numericValue === null) {
          invalid.push(def.label || def.key)
          return
        }
        normalized[def.key] = numericValue
      })

      if (invalid.length) {
        toast.error(`Please enter a valid number for: ${invalid.join(', ')}`)
        return
      }

      const result = await onSubmit(normalized)
      toast.success('Coverage prediction completed!')
      return result
    } catch (error) {
      toast.error(`Coverage prediction failed: ${error.response?.data?.detail || error.message}`)
      throw error
    }
  }

  const handleExplain = () => {
    if (onExplain) {
      onExplain(features)
    }
  }

  const resetForm = () => {
    setFeatures(buildInitialState(featureDefs))
  }

  const loadExample = (label) => {
    const example = CLASS_EXAMPLES[label]
    if (!example) return
    const base = buildInitialState(featureDefs)
    const exampleMap = new Map(
      Object.entries(example).map(([key, value]) => [normalizeKey(key), value])
    )
    const mappedExample = {}
    featureDefs.forEach((def) => {
      const match = exampleMap.get(normalizeKey(def.key))
      if (typeof match === 'number' && Number.isFinite(match)) {
        mappedExample[def.key] = match
      }
    })
    setFeatures({ ...base, ...mappedExample })
    toast.success(`Loaded ${label} example`)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {featureGroups.map((group) => (
        <div key={group.name} className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 pb-2">
            {group.name}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {group.features.map((feature) => (
              <div key={feature.key} className="space-y-2">
                <label className="input-label flex items-center gap-1" title={feature.help}>
                  {feature.label}
                  <span className="text-gray-400 cursor-help">ⓘ</span>
                </label>
                {feature.type === 'checkbox' ? (
                  <input
                    type="checkbox"
                    checked={!!features[feature.key]}
                    onChange={(e) => updateFeature(feature.key, e.target.checked ? 1 : 0)}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  />
                ) : (
                  <input
                    type="number"
                    step="any"
                    min={Number.isFinite(feature.min) ? feature.min : undefined}
                    max={Number.isFinite(feature.max) ? feature.max : undefined}
                    value={features[feature.key] ?? feature.default ?? 0}
                    onChange={(e) => updateFeature(feature.key, e.target.value)}
                    className="input"
                  />
                )}
                <div className="text-xs text-gray-500">
                  {Number.isFinite(feature.min) && Number.isFinite(feature.max)
                    ? `Range: [${feature.min}, ${feature.max}]`
                    : 'Range: model-defined'}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="submit"
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Predicting...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Predict
            </>
          )}
        </button>

        <button
          type="button"
          onClick={handleExplain}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <span className="text-base">🤖</span>
          Explain with AI
        </button>

        <button
          type="button"
          onClick={resetForm}
          className="btn-secondary"
        >
          Clear
        </button>

      </div>

      <div className="flex flex-wrap gap-2">
        {Object.keys(CLASS_EXAMPLES).map((label) => (
          <button
            key={label}
            type="button"
            onClick={() => loadExample(label)}
            className="btn-secondary"
          >
            Load {label}
          </button>
        ))}
      </div>
    </form>
  )
}
