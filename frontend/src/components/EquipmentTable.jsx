import React from 'react'
import { Table, TableHead, TableRow, TableCell, TableBody, TableContainer, Paper, Chip, Box, Pagination } from '@mui/material'

function CommentIndicator({ count }) {
  if (!count) return null
  const checks = '✓'.repeat(Math.min(3, count))
  const extra = count > 3 ? ` ${count}` : ''
  return <Chip color="success" size="small" label={`${checks}${extra}`} />
}

export default function EquipmentTable({ items, page, totalPages, onPageChange, onRowClick, dynamicHeaders = [] }) {
  // Always show comment indicator; other columns are dynamic from server
  return (
    <>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {dynamicHeaders.length === 0 ? (
                <>
                  <TableCell>Name</TableCell>
                  <TableCell>Code</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell>Location</TableCell>
                  <TableCell>Status</TableCell>
                </>
              ) : (
                dynamicHeaders.map(h => <TableCell key={h}>{h}</TableCell>)
              )}
              <TableCell>Comments</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map(row => (
              <TableRow key={row.id} hover onClick={() => onRowClick(row)} sx={{ cursor: 'pointer' }}>
                {dynamicHeaders.length === 0 ? (
                  <>
                    <TableCell>{row.equipment_name}</TableCell>
                    <TableCell>{row.equipment_code}</TableCell>
                    <TableCell>{row.category}</TableCell>
                    <TableCell>{row.location}</TableCell>
                    <TableCell>{row.status}</TableCell>
                  </>
                ) : (
                  dynamicHeaders.map(h => (
                    <TableCell key={h}>{(row.extra && row.extra[h]) ?? ''}</TableCell>
                  ))
                )}
                <TableCell><CommentIndicator count={row.comment_count} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Box mt={2} display="flex" justifyContent="center">
        <Pagination count={totalPages} page={page} onChange={(e, value) => onPageChange(value)} color="primary" />
      </Box>
    </>
  )
}
