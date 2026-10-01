import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import PredictionForm from '../components/PredictionForm'
import PredictionResult from '../components/PredictionResult'
import Card from '../components/Card'
import { coverageAPI } from '../services/api'

export default function PredictPage() {
  const navigate = useNavigate()
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastFeatures, setLastFeatures] = useState(null)
  const [featureCols, setFeatureCols] = useState(null)
  const [featureStats, setFeatureStats] = useState(null)
  const [featureLoading, setFeatureLoading] = useState(true)
  const [featureError, setFeatureError] = useState(null)

  useEffect(() => {
    let isMounted = true

    const loadFeatureCols = async () => {
      try {
        const response = await coverageAPI.health()
        if (!isMounted) return
        const cols = response.data?.feature_cols
        const stats = response.data?.feature_stats
        if (Array.isArray(cols) && cols.length) {
          setFeatureCols(cols)
        } else {
          setFeatureCols(null)
        }
        if (stats && typeof stats === 'object') {
          setFeatureStats(stats)
        } else {
          setFeatureStats(null)
        }
      } catch (error) {
        if (!isMounted) return
        setFeatureError('Failed to load model feature list. Using defaults.')
      } finally {
        if (isMounted) setFeatureLoading(false)
      }
    }

    loadFeatureCols()
    return () => {
      isMounted = false
    }
  }, [])

  const handlePredict = async (features) => {
    setLoading(true)
    try {
      const payload = Object.fromEntries(
        Object.entries(features).map(([key, value]) => [key, parseFloat(value)])
      )
      const response = await coverageAPI.predict(payload)
      const result = response.data

      if (result.success) {
        setPrediction(result.prediction)
        setLastFeatures(payload)
        toast.success('Coverage prediction complete!')
        return result
      } else {
        throw new Error(result.message || 'Coverage prediction failed')
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const handleExplain = () => {
    if (!prediction) {
      toast.error('Please make a prediction first')
      return
    }

    const classLabel = prediction.predicted_class || prediction.class || prediction.class_label || 'Unknown'
    const confidenceValue = typeof prediction.confidence === 'number'
      ? prediction.confidence.toFixed(2)
      : null
    const probabilities = prediction.probabilities || {}
    const probabilityText = Object.keys(probabilities).length
      ? Object.entries(probabilities)
          .map(([label, value]) => `${label}: ${(value * 100).toFixed(2)}%`)
          .join(', ')
      : 'N/A'
    const featureText = lastFeatures
      ? Object.entries(lastFeatures)
          .map(([key, value]) => `${key}=${value}`)
          .join(', ')
      : 'N/A'

    const message = [
      'Please analyze this network coverage prediction.',
      `Predicted class: ${classLabel}`,
      `Confidence: ${confidenceValue ? `${confidenceValue}%` : 'N/A'}`,
      `Probabilities: ${probabilityText}`,
      `Features: ${featureText}`,
    ].join('\n')

    navigate('/chat', { state: { prefillMessage: message } })
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Coverage Prediction
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Enter network measurements to predict the coverage class and confidence.
          The model uses signal quality, throughput, and temporal patterns.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input Form */}
        <div className="space-y-6">
          <Card title="Input Features">
            {featureError && (
              <div className="mb-4 text-sm text-amber-600 dark:text-amber-400">
                {featureError}
              </div>
            )}
            {featureLoading && (
              <div className="mb-4 text-sm text-gray-500 dark:text-gray-400">
                Loading model feature list...
              </div>
            )}
            <PredictionForm
              onSubmit={handlePredict}
              loading={loading}
              onExplain={handleExplain}
              featureCols={featureCols}
              featureStats={featureStats}
            />
          </Card>

          {/* Feature Legend */}
          <Card title="Feature Reference">
            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div>
                <strong className="text-gray-900 dark:text-white">RSRQ:</strong> Reference Signal Received Quality (dB). Higher is better.
              </div>
              <div>
                <strong className="text-gray-900 dark:text-white">RLC DL:</strong> Downlink throughput indicator.
              </div>
              <div>
                <strong className="text-gray-900 dark:text-white">PCI:</strong> Physical cell identity.
              </div>
              <div>
                <strong className="text-gray-900 dark:text-white">Band Enc:</strong> Encoded frequency band index.
              </div>
              <div>
                <strong className="text-gray-900 dark:text-white">Lags/Rolls:</strong> Temporal context for recent samples.
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Results */}
        <div className="space-y-6">
          {prediction ? (
            <PredictionResult
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

          {/* Tips */}
          {!prediction && (
            <Card title="Tips for Accurate Predictions">
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 list-disc list-inside">
                <li>Use realistic values based on your measurement logs</li>
                <li>RSRQ is typically between -20 and -3 dB</li>
                <li>Use the correct PCI and band encoding for the cell</li>
                <li>Include recent lag and rolling values for stability</li>
                <li>Click "Load Example" for a representative sample</li>
              </ul>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
