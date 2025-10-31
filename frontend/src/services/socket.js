// Socket.IO disabled for serverless deployment (not supported in Vercel)
// Create a mock socket object to prevent errors
const mockSocket = {
  on: () => {},
  off: () => {},
  emit: () => {},
  disconnect: () => {},
}

export function getSocket() {
  return mockSocket
}

export function joinEquipmentRoom(equipmentId) {
  // No-op in serverless
}

export function leaveEquipmentRoom(equipmentId) {
  // No-op in serverless
}


