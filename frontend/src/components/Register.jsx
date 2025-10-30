import React, { useState } from 'react'
import { Container, Box, TextField, Button, Typography, Paper, Alert, CircularProgress } from '@mui/material'
import { registerUser } from '../services/api'
import { useNavigate, Link } from 'react-router-dom'

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  function update(field, value) {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (!form.username || !form.email || !form.password) {
      setError('Username, Email and Password are required')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    setLoading(true)
    try {
      await registerUser(form)
      setSuccess('Registered successfully. Redirecting to login...')
      setTimeout(() => navigate('/login'), 1000)
    } catch (err) {
      setError(err?.response?.data?.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box mt={8} component={Paper} p={4}>
        <Typography variant="h5" mb={2}>Register</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        <form onSubmit={onSubmit}>
          <TextField fullWidth margin="normal" label="Username" value={form.username} onChange={e => update('username', e.target.value)} />
          <TextField fullWidth margin="normal" label="Email" value={form.email} onChange={e => update('email', e.target.value)} />
          <TextField fullWidth margin="normal" label="Full Name" value={form.full_name} onChange={e => update('full_name', e.target.value)} />
          <TextField fullWidth margin="normal" label="Password" type="password" value={form.password} onChange={e => update('password', e.target.value)} />
          <Button variant="contained" color="primary" type="submit" fullWidth disabled={loading} sx={{ mt: 2 }}>
            {loading ? <CircularProgress size={24} /> : 'Register'}
          </Button>
          <Box mt={2}><Typography variant="body2">Have an account? <Link to="/login">Login</Link></Typography></Box>
        </form>
      </Box>
    </Container>
  )
}
