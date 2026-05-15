import axios from 'axios'

const client = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 15000,
})

export async function searchPoi(keyword, city = '') {
  const { data } = await client.get('/poi/search', { params: { keyword, city } })
  return data.results || []
}

export async function planRoute(payload) {
  const { data } = await client.post('/plan', payload)
  return data.plans || []
}
