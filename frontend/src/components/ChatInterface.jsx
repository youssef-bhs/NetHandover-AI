import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

const QUICK_QUESTIONS = [
  'How to interpret RSRQ for coverage?',
  'What causes low coverage quality?',
  'How does PCI planning impact coverage?',
  'What is a good RLC DL range?',
  'How to improve coverage confidence?',
  'Explain the coverage prediction results',
]

export default function ChatInterface({
  onAnalyzePrediction,
  predictionContext,
  prefillMessage,
  autoSendPrefill = false
}) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your network coverage assistant. I can analyze coverage predictions or answer questions about signal quality and performance. How can I help?',
      sources: []
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedSource, setExpandedSource] = useState(null)
  const messagesEndRef = useRef(null)
  const prefillSentRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (!prefillMessage || prefillSentRef.current || !autoSendPrefill) return
    prefillSentRef.current = true
    sendMessage(prefillMessage, false)
  }, [prefillMessage, autoSendPrefill])

  const sendMessage = async (messageText = input, withPrediction = !!predictionContext) => {
    if (!messageText.trim()) return

    const userMessage = { role: 'user', content: messageText }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const payload = { message: messageText }
      if (withPrediction && predictionContext) {
        payload.features = predictionContext.features
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        prediction_used: data.prediction_used,
        model_used: data.model_used
      }

      setMessages(prev => [...prev, assistantMessage])

    } catch (error) {
      console.error('Chat error:', error)
      toast.error('Failed to get response. Please try again.')
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to get response'}`,
        sources: []
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleQuickQuestion = (question) => {
    if (predictionContext) {
      // If we have a prediction, automatically include it in analysis
      setInput(question)
      sendMessage(question, true)
    } else {
      setInput(question)
    }
  }

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Chat cleared. How else can I help?',
        sources: []
      }
    ])
  }

  // Show prediction context banner if available
  const hasPrediction = predictionContext && Object.keys(predictionContext).length > 0
  const coverageLabel = predictionContext?.class_label || predictionContext?.class

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      {/* Prediction Context Banner */}
      {hasPrediction && (
        <div className="mb-4 p-3 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-primary-800 dark:text-primary-200">
            <AlertCircle className="w-4 h-4" />
            <span className="font-medium">Analyzing prediction:</span>
            {coverageLabel ? (
              <span>Coverage class: {coverageLabel}</span>
            ) : (
              <span>Prediction context attached</span>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-sm'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 border-t border-gray-300 dark:border-gray-600 pt-2">
                  <button
                    onClick={() => setExpandedSource(expandedSource === idx ? null : idx)}
                    className="flex items-center gap-1 text-xs font-medium text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                  >
                    {expandedSource === idx ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                    {expandedSource === idx ? 'Hide' : 'Show'} sources ({msg.sources.length})
                  </button>
                  {expandedSource === idx && (
                    <div className="mt-2 space-y-1">
                      {msg.sources.map((source, sIdx) => (
                        <div key={sIdx} className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded font-mono">
                          {source}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Prediction used indicator */}
              {msg.prediction_used && (
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-300 dark:border-gray-600 pt-2">
                  {msg.prediction_used.predicted_class ? (
                    <>Based on prediction: {msg.prediction_used.predicted_class} ({typeof msg.prediction_used.confidence === 'number'
                      ? `${msg.prediction_used.confidence.toFixed(0)}%`
                      : 'N/A'})</>
                  ) : (
                    <>Based on prediction context</>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-gray-600 dark:text-gray-300">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Questions */}
      <div className="mb-3 flex flex-wrap gap-2">
        {QUICK_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleQuickQuestion(q)}
            disabled={loading}
            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full text-gray-700 dark:text-gray-300 disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={
            predictionContext
              ? "Ask about this prediction... (e.g., 'Why low coverage?')"
              : "Ask about coverage, RSRQ, PCI, throughput..."
          }
          rows={3}
          className="input resize-none flex-1"
          disabled={loading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="btn-primary self-end"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      {/* Clear button */}
      <div className="mt-2 flex justify-end">
        <button onClick={clearChat} className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
          Clear chat
        </button>
      </div>
    </div>
  )
}
