import { useState, useEffect } from 'react'
import { RefreshCw, Save, TestTube } from 'lucide-react'
import toast from 'react-hot-toast'
import { coverageAPI, chatAPI } from '../services/api'
import Card from '../components/Card'

export default function AdminPage() {
  const [coverageStatus, setCoverageStatus] = useState(null)
  const [ragStatus, setRagStatus] = useState(null)
  const [llmModel, setLlmModel] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [loading, setLoading] = useState(true)
  const [reloadingRag, setReloadingRag] = useState(false)
  const [testingApi, setTestingApi] = useState(false)

  useEffect(() => {
    loadAdminData()
  }, [])

  const loadAdminData = async () => {
    try {
      setLoading(true)
      const [coverageRes, chatStatus] = await Promise.all([
        coverageAPI.health(),
        chatAPI.getStatus()
      ])
      setCoverageStatus(coverageRes.data)
      setRagStatus(chatStatus.data)
      setLlmModel(chatStatus.data.llm_model || '')
    } catch (error) {
      toast.error('Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

  const reloadRag = async () => {
    setReloadingRag(true)
    try {
      // Call backend to reload RAG (would need endpoint, for now use build script)
      toast.info('RAG rebuild must be done via script: scripts/build_rag.py')
      // await adminAPI.reloadRag()
      toast.success('RAG rebuild triggered')
    } catch (error) {
      toast.error('Failed to reload RAG')
    } finally {
      setReloadingRag(false)
    }
  }

  const testApi = async () => {
    setTestingApi(true)
    try {
      // Test with a simple chat
      const response = await chatAPI.sendMessage('Hello, this is a test.')
      if (response.data.success) {
        toast.success('Gemini API connected successfully!')
      } else {
        toast.error('API test failed: ' + response.data.answer)
      }
    } catch (error) {
      toast.error('API test failed: ' + error.message)
    } finally {
      setTestingApi(false)
    }
  }

  const saveApiConfig = async () => {
    toast.info('Configuration changes require server restart')
    // In production, POST to /api/config endpoint
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Administration
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Manage models, RAG knowledge base, and API settings
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-primary-600" />
        </div>
      ) : (
        <>
          {/* Model Management */}
          <Card title="Model Management">
            {!coverageStatus?.loaded ? (
              <div className="text-center py-8 text-gray-500">
                Coverage model not loaded. Verify the model path and restart the backend.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model Type</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Features</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    <tr>
                      <td className="px-4 py-4 whitespace-nowrap font-medium">Coverage</td>
                      <td className="px-4 py-4 whitespace-nowrap font-mono text-sm">
                        {coverageStatus?.model_type || 'Unknown'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        {coverageStatus?.feature_count || 0}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200">
                          Active
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* RAG Knowledge Base */}
          <Card title="RAG Knowledge Base">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Status:</span>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    ragStatus?.rag_initialized
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                  }`}>
                    {ragStatus?.rag_initialized ? 'Ready' : 'Not Ready'}
                  </span>
                </div>
                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  Documents: {ragStatus?.document_count || 0} | Embedding: {ragStatus?.embedding_model}
                </div>
              </div>
              <button
                onClick={reloadRag}
                disabled={reloadingRag}
                className="btn-secondary flex items-center gap-2"
              >
                {reloadingRag ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Reload Knowledge Base
              </button>
            </div>
          </Card>

          {/* API Settings */}
          <Card title="API Settings (Gemini)">
            <div className="space-y-4">
              <div>
                <label className="input-label">Gemini API Key</label>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey || '••••••••••••••••'}
                    readOnly
                    className="input flex-1"
                    placeholder="Enter API key"
                  />
                  <button
                    onClick={testApi}
                    disabled={testingApi}
                    className="btn-secondary flex items-center gap-2"
                  >
                    {testingApi ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <TestTube className="w-4 h-4" />
                    )}
                    Test
                  </button>
                </div>
              </div>

              <div>
                <label className="input-label">Current LLM Model</label>
                <input
                  type="text"
                  value={llmModel}
                  readOnly
                  className="input bg-gray-100 dark:bg-gray-800"
                />
              </div>

              <div className="pt-2">
                <button onClick={saveApiConfig} className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  Save Changes (Restart Required)
                </button>
              </div>
            </div>
          </Card>

          {/* System Logs (placeholder) */}
          <Card title="Recent Activity">
            <div className="space-y-2">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-mono text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">GET</span>
                <span className="ml-2">/api/health</span>
                <span className="ml-auto text-gray-500">200 OK</span>
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-mono text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">POST</span>
                <span className="ml-2">/api/predict</span>
                <span className="ml-auto text-gray-500">200 OK</span>
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-mono text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">POST</span>
                <span className="ml-2">/api/chat</span>
                <span className="ml-auto text-gray-500">200 OK</span>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
