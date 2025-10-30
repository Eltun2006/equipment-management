import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const api = axios.create({ baseURL: API_BASE_URL })

export function getToken() {
  return localStorage.getItem('access_token')
}

export function setToken(token) {
  localStorage.setItem('access_token', token)
}

export function clearToken() {
  localStorage.removeItem('access_token')
}

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export async function login(loginId, password) {
  const res = await api.post('/api/auth/login', { login: loginId, password })
  setToken(res.data.access_token)
  return res.data
}

export async function registerUser(payload) {
  return (await api.post('/api/auth/register', payload)).data
}

export async function me() {
  return (await api.get('/api/auth/me')).data
}

export async function fetchEquipment(params) {
  return (await api.get('/api/equipment', { params })).data
}

export async function fetchEquipmentById(id) {
  return (await api.get(`/api/equipment/${id}`)).data
}

export async function fetchComments(equipmentId) {
  return (await api.get(`/api/comments/equipment/${equipmentId}`)).data
}

export async function addComment(equipmentId, comment_text) {
  return (await api.post('/api/comments', { equipment_id: equipmentId, comment_text })).data
}

export async function deleteComment(commentId) {
  return (await api.delete(`/api/comments/${commentId}`)).data
}

export async function importExcel(formData) {
  return (await api.post('/api/equipment/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })).data
}

export async function exportEquipment() {
  // return blob from export endpoint
  const res = await api.get('/api/equipment/export', { responseType: 'blob' })
  return res.data
}

export default api
