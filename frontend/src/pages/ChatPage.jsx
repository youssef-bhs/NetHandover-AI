import { useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import ChatInterface from '../components/ChatInterface'
import toast from 'react-hot-toast'
import Card from '../components/Card'

export default function ChatPage() {
  const location = useLocation()

  // Check if we arrived with prediction context
  const predictionContext = location.state?.prediction
  const featureContext = location.state?.features
  const prefillMessage = location.state?.prefillMessage

  useEffect(() => {
    if (predictionContext || prefillMessage) {
      toast.success('Context loaded for analysis')
    }
  }, [predictionContext, prefillMessage])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          AI Assistant
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Ask questions about coverage quality or get analysis of your predictions.
          The AI has access to telecom documentation and your project's knowledge base.
        </p>
      </div>

      <div className="card">
        <ChatInterface
          predictionContext={predictionContext || featureContext ? {
            features: featureContext,
            recommendation: predictionContext?.recommendation,
            top_features: predictionContext?.top_features
          } : null}
          prefillMessage={prefillMessage}
          autoSendPrefill={Boolean(prefillMessage)}
        />
      </div>

      {/* Info Banner */}
      <Card>
        <div className="flex items-start gap-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex-shrink-0">
            <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
              How to use
            </h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
              <li>Ask general questions: "What is a good RSRQ threshold?"</li>
              <li>Analyze predictions: Make a prediction first, then click "Analyze with AI"</li>
              <li>The AI cites sources from the knowledge base (UMTS docs + project analysis)</li>
              <li>You can choose different LLM models in Admin settings (Claude, GPT-4, etc.)</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
