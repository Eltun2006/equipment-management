import React, { useState } from 'react'
import { Paper, Box, Typography, Button, Alert, CircularProgress } from '@mui/material'
import api from '../services/api'

export default function ExcelImport({ onImported }) {
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onUpload() {
    setMessage('')
    setError('')
    if (!file) {
      setError('Please select a file')
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    setLoading(true)
    try {
      const res = await api.post('/api/equipment/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      setMessage(res.data.message || 'Import complete')
      if (typeof onImported === 'function') {
        onImported()
      }
    } catch (err) {
      const data = err?.response?.data
      setError(Array.isArray(data?.errors) ? data.errors.join('\n') : (data?.message || 'Import failed'))
    } finally {
      setLoading(false)
    }
  }

  async function downloadTemplate() {
    const res = await api.get('/api/equipment/template', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'equipment_template.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Excel Import (Admin)</Typography>
      {message && <Alert severity="success" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>{message}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>{error}</Alert>}
      <Box display="flex" gap={2} alignItems="center">
        <input type="file" accept=".xlsx,.xls" onChange={e => setFile(e.target.files?.[0] || null)} />
        <Button variant="outlined" onClick={downloadTemplate}>Download Template</Button>
        <Button variant="contained" onClick={onUpload} disabled={loading}>{loading ? <CircularProgress size={20} /> : 'Upload'}</Button>
      </Box>
      <Typography variant="body2" color="text.secondary" mt={1}>Expected columns: Equipment Name | Code | Category | Location | Status | Description</Typography>
    </Paper>
  )
}
