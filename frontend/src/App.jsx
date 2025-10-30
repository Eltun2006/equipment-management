import React from 'react'
import { Routes, Route, Navigate, useLocation, Link } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, Typography, Button } from '@mui/material'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import { getToken, clearToken } from './services/api'

const theme = createTheme({
  palette: {
    primary: { main: '#2563eb' },
  },
})

function RequireAuth({ children }) {
  const location = useLocation()
  if (!getToken()) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}

function TopBar() {
  const authed = !!getToken()
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>Equipment Manager</Typography>
        {authed ? (
          <Button color="inherit" onClick={() => { clearToken(); window.location.href = '/login' }}>Logout</Button>
        ) : (
          <Button component={Link} to="/login" color="inherit">Login</Button>
        )}
      </Toolbar>
    </AppBar>
  )
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <TopBar />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </ThemeProvider>
  )
}
