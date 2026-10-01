import axios from 'axios'

// Create axios instance with base URL (proxied via Vite)
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging (development)
if (import.meta.env.DEV) {
  api.interceptors.request.use(
    (config) => {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
      return config
    },
    (error) => Promise.reject(error)
  )

  api.interceptors.response.use(
    (response) => {
      console.log(`[API Response] ${response.status} ${response.config.url}`)
      return response
    },
    (error) => {
      if (error.response) {
        console.error(
          `[API Error] ${error.response.status} ${error.response.config?.url}:`,
          error.response.data
        )
      } else if (error.request) {
        console.error(`[API Error] No response for ${error.config?.url}`)
      }
      return Promise.reject(error)
    }
  )
}

// Prediction endpoints
export const predictAPI = {
  predict: (features, task = 'both') =>
    api.post('/predict', { features, task }),
  getModels: () => api.get('/models'),
  health: () => api.get('/health'),
}

// Coverage model endpoints
export const coverageAPI = {
  predict: (features) => api.post('/coverage/predict', features),
  health: () => api.get('/coverage/health'),
}

// QoS model endpoints
export const qosAPI = {
  predict: (features) => api.post('/qos/predict', features),
  health: () => api.get('/qos/health'),
}

// Chat endpoints
export const chatAPI = {
  sendMessage: (message, features = null, model = null) =>
    api.post('/chat', { message, features, model }),
  getStatus: () => api.get('/chat/status'),
}

// Training endpoints
export const trainAPI = {
  startTraining: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/train', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getStatus: (jobId) => api.get(`/train/status/${jobId}`),
}

// Data endpoints
export const dataAPI = {
  getSample: (limit = 100) => api.get(`/data/sample?limit=${limit}`),
  getInfo: () => api.get('/data/info'),
  getCells: () => api.get('/cells'),
  getPlot: (plotName) => api.get(`/plots/${plotName}`, {
    responseType: 'blob',
  }),
}

// Utility to handle file download
export const downloadPlot = async (plotName, filename) => {
  try {
    const response = await dataAPI.getPlot(plotName)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename || plotName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Download failed:', error)
    throw error
  }
}

export default api
