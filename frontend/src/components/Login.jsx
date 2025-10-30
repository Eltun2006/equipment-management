import React, { useState } from 'react'
import { Container, Box, TextField, Button, Typography, Paper, Alert, CircularProgress } from '@mui/material'
import { login } from '../services/api'
import { useNavigate, useLocation, Link } from 'react-router-dom'

export default function Login() {
  const [loginId, setLoginId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (!loginId || !password) {
      setError('Please fill in all fields')
      return
    }
    setLoading(true)
    try {
      await login(loginId, password)
      const redirectTo = location.state?.from?.pathname || '/dashboard'
      navigate(redirectTo)
    } catch (err) {
      setError(err?.response?.data?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm">
      <Box mt={8} component={Paper} p={4}>
        <Typography variant="h5" mb={2}>Login</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={onSubmit}>
          <TextField fullWidth margin="normal" label="Username or Email" value={loginId} onChange={e => setLoginId(e.target.value)} />
          <TextField fullWidth margin="normal" label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          <Button variant="contained" color="primary" type="submit" fullWidth disabled={loading} sx={{ mt: 2 }}>
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
          <Box mt={2}><Typography variant="body2">No account? <Link to="/register">Register</Link></Typography></Box>
        </form>
      </Box>
    </Container>
  )
}
