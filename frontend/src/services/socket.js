import { io } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

let socket

export function getSocket() {
  if (!socket) {
    socket = io(SOCKET_URL, { transports: ['websocket'], withCredentials: false })
  }
  return socket
}

export function joinEquipmentRoom(equipmentId) {
  getSocket().emit('join_equipment', { equipment_id: equipmentId })
}

export function leaveEquipmentRoom(equipmentId) {
  getSocket().emit('leave_equipment', { equipment_id: equipmentId })
}
