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

export const forgotPassword = async (email, password, confirmPassword) => {
  const response = await api.post('/admin/forgot-password', {
    email,
    password,
    confirm_password: confirmPassword
  })
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

export const exportVolunteers = async (token, filters = {}) => {
  const params = new URLSearchParams()
  if (filters.ministry_area) params.append('ministry_area', filters.ministry_area)

  const response = await api.get(`/admin/reports/export?${params.toString()}`, {
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

// Admin user management endpoints

export const getAdminUsers = async (token) => {
  const response = await api.get('/admin/users', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const createAdminUser = async (token, adminData) => {
  const response = await api.post('/admin/users', adminData, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const updateAdminUser = async (token, adminId, updateData) => {
  const response = await api.patch(`/admin/users/${adminId}`, updateData, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const transferSuperAdmin = async (token, targetAdminId) => {
  const response = await api.post('/admin/transfer-super', { target_admin_id: targetAdminId }, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

// Volunteer management endpoints

export const getVolunteer = async (token, volunteerId) => {
  const response = await api.get(`/admin/volunteers/${volunteerId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const updateVolunteer = async (token, volunteerId, updateData) => {
  const response = await api.patch(`/admin/volunteers/${volunteerId}`, updateData, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const deleteVolunteer = async (token, volunteerId) => {
  const response = await api.delete(`/admin/volunteers/${volunteerId}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const getVolunteerNotes = async (token, volunteerId) => {
  const response = await api.get(`/admin/volunteers/${volunteerId}/notes`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const addVolunteerNote = async (token, volunteerId, noteText) => {
  const response = await api.post(`/admin/volunteers/${volunteerId}/notes`, { note_text: noteText }, {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

// Ministry Reports endpoints

export const getMinistryReport = async (token) => {
  const response = await api.get('/admin/reports/by-ministry', {
    headers: { Authorization: `Bearer ${token}` }
  })
  return response.data
}

export const exportAllMinistries = async (token) => {
  const response = await api.get('/admin/reports/export-all', {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  })

  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'all_ministries_report.csv')
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export const exportMinistry = async (token, ministryName) => {
  const response = await api.get(`/admin/reports/export-ministry/${encodeURIComponent(ministryName)}`, {
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  })

  const safeName = ministryName.replace(/[/\\]/g, '-')
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `${safeName}_volunteers.csv`)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default api
