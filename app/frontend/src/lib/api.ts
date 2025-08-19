import axios from 'axios'

export const api = axios.create({ 
  baseURL: 'http://localhost:8000/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    }
    throw error
  }
)

export type Dataset = {
  id: string
  filename: string
  source_system: string
  record_count: number
}

export async function listDatasets() {
  const { data } = await api.get<Dataset[]>('/api/datasets/')
  return data
}

export async function uploadDataset(file: File, source?: string) {
  const form = new FormData()
  form.append('file', file)
  if (source) form.append('source_system', source)
  const { data } = await api.post('/api/datasets/', form, { 
    headers: { 'Content-Type': 'multipart/form-data' } 
  })
  return data
}

export async function runPipeline(file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/api/pipeline/run', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  return data as { candidates: any[]; metrics: any; rejections_count: number }
}

export async function lastPipeline() {
  const { data } = await api.get('/api/pipeline/last')
  return data as { candidates: any[]; metrics: any; rejections_count: number }
}
export async function healthCheck() {
  const { data } = await api.get('/api/datasets/health')
  return data
}

export async function getClaims(datasetId: string) {
  const { data } = await api.get(`/api/datasets/${datasetId}/claims`)
  return data
}

export async function getCandidates(datasetId: string) {
  const { data } = await api.get(`/api/datasets/${datasetId}/candidates`)
  return data
}



