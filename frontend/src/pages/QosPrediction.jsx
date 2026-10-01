import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import Card from '../components/Card'
import QosPredictionResult from '../components/QosPredictionResult'
import { qosAPI } from '../services/api'

const INITIAL_FORM = {
  rsrp: '',
  rsrq: '',
  rlc_downlink_throughput: '',
  band: '',
  physical_cell_identity: '',
}

const QOS_EXAMPLES = [
  {
    label: 'Tres bonne',
    values: {
      rsrp: -75,
      rsrq: -4,
      rlc_downlink_throughput: 60,
      band: 3,
      physical_cell_identity: 100,
    },
  },
  {
    label: 'Acceptable',
    values: {
      rsrp: -90,
      rsrq: -8,
      rlc_downlink_throughput: 25,
      band: 3,
      physical_cell_identity: 100,
    },
  },
  {
    label: 'Assez bien',
    values: {
      rsrp: -102,
      rsrq: -12,
      rlc_downlink_throughput: 10,
      band: 3,
      physical_cell_identity: 100,
    },
  },
  {
    label: 'Mauvaise',
    values: {
      rsrp: -115,
      rsrq: -17,
      rlc_downlink_throughput: 2,
      band: 3,
      physical_cell_identity: 100,
    },
  },
]

const FIELDS = [
  {
    key: 'rsrp',
    label: 'RSRP',
    type: 'number',
    step: 'any',
  },
  {
    key: 'rsrq',
    label: 'RSRQ',
    type: 'number',
    step: 'any',
  },
  {
    key: 'rlc_downlink_throughput',
    label: 'RLC Downlink Throughput',
    type: 'number',
    step: 'any',
  },
  {
    key: 'band',
    label: 'Band',
    type: 'number',
    step: '1',
  },
  {
    key: 'physical_cell_identity',
    label: 'Physical Cell ID',
    type: 'number',
    step: '1',
  },
]

export default function QosPrediction() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState(INITIAL_FORM)
  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState(null)
  const [lastFeatures, setLastFeatures] = useState(null)

  const updateField = (key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }

  const validateAndBuildPayload = () => {
    const payload = {}
    for (const field of FIELDS) {
      const rawValue = formData[field.key]
      const numericValue = Number.parseFloat(rawValue)
      if (!Number.isFinite(numericValue)) {
        toast.error(`${field.label} should be numeric`)
        return null
      }
      payload[field.key] = numericValue
    }
    return payload
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    const payload = validateAndBuildPayload()
    if (!payload) return

    setLoading(true)
    try {
      const response = await qosAPI.predict(payload)
      const result = response.data
      if (result?.success) {
        setPrediction(result.prediction)
        setLastFeatures(payload)
        toast.success('QoS prediction complete!')
      } else {
        throw new Error(result?.message || 'QoS prediction failed')
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message)
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFormData(INITIAL_FORM)
  }

  const loadExample = (example) => {
    setFormData({ ...example.values })
    toast.success(`Loaded ${example.label} example`)
  }

  const handleExplain = () => {
    if (!prediction || !lastFeatures) {
      toast.error('Please make a prediction first')
      return
    }

    const inputs = [
      `RSRP: ${lastFeatures.rsrp}`,
      `RSRQ: ${lastFeatures.rsrq}`,
      `RLC Downlink Throughput: ${lastFeatures.rlc_downlink_throughput}`,
      `Band: ${lastFeatures.band}`,
      `Physical Cell ID: ${lastFeatures.physical_cell_identity}`,
    ].join(', ')

    const message = [
      'Please analyze this QoS prediction.',
      `Predicted QoS: ${prediction.predicted_class || 'Unknown'}`,
      `Inputs: ${inputs}`,
    ].join('\n')

    navigate('/chat', { state: { prefillMessage: message, features: lastFeatures } })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          QoS Prediction
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Provide the latest radio and throughput metrics to predict QoS class.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Input Metrics">
          <form onSubmit={handleSubmit} className="space-y-4">
            {FIELDS.map((field) => (
              <div key={field.key} className="space-y-2">
                <label className="input-label">{field.label}</label>
                <input
                  type={field.type}
                  step={field.step}
                  value={formData[field.key]}
                  onChange={(event) => updateField(field.key, event.target.value)}
                  className="input"
                  placeholder={field.label}
                />
              </div>
            ))}

            <div className="pt-2">
              <button
                type="submit"
                className="btn-primary flex items-center gap-2"
                disabled={loading}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                Predict QoS
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="btn-secondary ml-3"
                disabled={loading}
              >
                Clear
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {QOS_EXAMPLES.map((example) => (
                <button
                  key={example.label}
                  type="button"
                  onClick={() => loadExample(example)}
                  className="btn-secondary"
                  disabled={loading}
                >
                  Load {example.label}
                </button>
              ))}
            </div>
          </form>
        </Card>

        {prediction?.predicted_class ? (
          <QosPredictionResult
            prediction={prediction}
            onExplain={handleExplain}
          />
        ) : (
          <Card className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-900/50">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Prediction Yet
              </h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-xs mx-auto">
                Fill in the feature values on the left and click "Predict" to see results.
              </p>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
