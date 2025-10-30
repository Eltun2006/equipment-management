import React, { useEffect, useState, useMemo } from 'react'
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, List, ListItem, ListItemText, Box, Typography, IconButton } from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { fetchComments, addComment, deleteComment } from '../services/api'
import { getSocket, joinEquipmentRoom, leaveEquipmentRoom } from '../services/socket'

export default function CommentModal({ open, onClose, equipment }) {
  const [comments, setComments] = useState([])
  const [text, setText] = useState('')
  const socket = useMemo(() => getSocket(), [])

  useEffect(() => {
    if (!equipment?.id || !open) return
    let active = true

    async function load() {
      const data = await fetchComments(equipment.id)
      if (active) setComments(data)
    }
    load()

    joinEquipmentRoom(equipment.id)

    function onNewComment(payload) {
      if (payload.equipment_id === equipment.id) {
        setComments(prev => [payload, ...prev])
      }
    }
    function onCommentDeleted(payload) {
      if (payload.equipment_id === equipment.id) {
        setComments(prev => prev.filter(c => c.id !== payload.id))
      }
    }
    socket.on('new_comment', onNewComment)
    socket.on('comment_deleted', onCommentDeleted)

    return () => {
      active = false
      leaveEquipmentRoom(equipment.id)
      socket.off('new_comment', onNewComment)
      socket.off('comment_deleted', onCommentDeleted)
    }
  }, [equipment, open, socket])

  async function onAdd() {
    const value = text.trim()
    if (!value) return
    await addComment(equipment.id, value)
    setText('')
  }

  async function onDelete(id) {
    await deleteComment(id)
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Comments - {equipment?.equipment_name}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>{equipment?.description}</Typography>
        <Box display="flex" gap={1} mb={2}>
          <TextField fullWidth size="small" label="Add a comment" value={text} onChange={e => setText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') onAdd() }} />
          <Button variant="contained" onClick={onAdd}>Send</Button>
        </Box>
        <List>
          {comments.map(c => (
            <ListItem key={c.id} secondaryAction={<IconButton edge="end" aria-label="delete" onClick={() => onDelete(c.id)}><DeleteIcon /></IconButton>}>
              <ListItemText
                primary={<>
                  <Typography component="span" fontWeight={600}>{c.username}</Typography>
                  <Typography component="span" ml={1} color="text.secondary">{new Date(c.created_at).toLocaleString()}</Typography>
                </>}
                secondary={c.comment_text}
              />
            </ListItem>
          ))}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
