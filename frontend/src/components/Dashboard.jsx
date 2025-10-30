import React, { useEffect, useMemo, useState } from 'react'
import { Container, Paper, Box, TextField, MenuItem, Grid, CircularProgress, Alert, Button } from '@mui/material'
import { Download } from 'lucide-react'
import EquipmentTable from './EquipmentTable'
import CommentModal from './CommentModal'
import { fetchEquipment, me } from '../services/api'
import { getSocket } from '../services/socket'
import ExcelImport from './ExcelImport'
import { exportEquipment } from '../services/api'

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [commentCount, setCommentCount] = useState('')
  const [filtersMeta, setFiltersMeta] = useState({ statuses: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [dynamicHeaders, setDynamicHeaders] = useState([])

  const socket = useMemo(() => getSocket(), [])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const params = { page, q, status, category, comment_count: commentCount }
      const data = await fetchEquipment(params)
      setItems(data.items)
      setTotalPages(data.total_pages)
      setFiltersMeta({ statuses: data.filters.statuses })
      setDynamicHeaders(data.dynamic_headers || [])
    } catch (err) {
      setError(err?.response?.data?.message || 'Failed to load equipment')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { me().then(setUser).catch(() => {}) }, [])
  useEffect(() => { load() }, [page, q, status, category, commentCount])

  useEffect(() => {
    function onCountUpdated(payload) {
      setItems(prev => prev.map(it => it.id === payload.equipment_id ? { ...it, comment_count: payload.count } : it))
    }
    socket.on('comment_count_updated', onCountUpdated)
    return () => { socket.off('comment_count_updated', onCountUpdated) }
  }, [socket])

  return (
    <Container sx={{ mt: 3 }}>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <TextField fullWidth label="Search" value={q} onChange={e => { setQ(e.target.value); setPage(1) }} />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField select fullWidth label="Status" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
              <MenuItem value="">All</MenuItem>
              {filtersMeta.statuses.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField fullWidth label="Category" value={category} onChange={e => { setCategory(e.target.value); setPage(1) }} />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField select fullWidth label="Comment Count" value={commentCount} onChange={e => { setCommentCount(e.target.value); setPage(1) }}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="0">0</MenuItem>
              <MenuItem value="1">1</MenuItem>
              <MenuItem value="2">2</MenuItem>
              <MenuItem value="3">3+</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} md={12} display="flex" justifyContent="flex-end" gap={1}>
            <Button variant="outlined" startIcon={<Download size={16} />} disabled={exporting} onClick={async () => {
              try {
                setExporting(true)
                const blob = await exportEquipment()
                const url = window.URL.createObjectURL(new Blob([blob]))
                const link = document.createElement('a')
                const today = new Date().toISOString().slice(0,10)
                link.href = url
                link.setAttribute('download', `equipment_export_${today}.xlsx`)
                document.body.appendChild(link)
                link.click()
                link.remove()
                window.URL.revokeObjectURL(url)
              } catch (e) {
                setError('Failed to export Excel')
              } finally {
                setExporting(false)
              }
            }}>
              {exporting ? 'Exporting…' : 'Export to Excel'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {user?.role === 'admin' && (
        <Box mb={2}><ExcelImport onImported={load} /></Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}><CircularProgress /></Box>
      ) : (
        <EquipmentTable
          items={items}
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
          onRowClick={setSelected}
          dynamicHeaders={dynamicHeaders}
        />
      )}

      <CommentModal open={!!selected} onClose={() => setSelected(null)} equipment={selected} />
    </Container>
  )
}
