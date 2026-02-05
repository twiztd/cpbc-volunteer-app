import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Public endpoints

export const getMinistryAreas = async () => {
  const response = await api.get('/ministry-areas')
  return response.data
}

export const submitVolunteer = async (volunteerData) => {
  const response = await api.post('/volunteers', volunteerData)
  return response.data
}

// Admin endpoints

export const adminLogin = async (email, password) => {
  const response = await api.post('/admin/login', { email, password })
  return response.data
}

export const getVolunteers = async (token, filters = {}) => {
  const params = new URLSearchParams()
  if (filters.ministry_area) params.append('ministry_area', filters.ministry_area)
  if (filters.sort_by) params.append('sort_by', filters.sort_by)

  const response = await api.get(`/admin/volunteers?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const exportVolunteers = async (token) => {
  const response = await api.get('/admin/reports/export', {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  })

  // Download the CSV file
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'volunteers_export.csv')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default api
