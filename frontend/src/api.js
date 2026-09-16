const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function handle(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.message || `Request failed (${response.status})`)
  }
  return data
}

export const api = {
  async uploadOrder(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/api/orders/upload`, {
      method: 'POST',
      body: formData,
    })
    return handle(response)
  },

  async listOrders() {
    const response = await fetch(`${API_BASE}/api/orders`)
    return handle(response)
  },

  async getOrder(id) {
    const response = await fetch(`${API_BASE}/api/orders/${id}`)
    return handle(response)
  },

  async getDashboard() {
    const response = await fetch(`${API_BASE}/api/dashboard`)
    return handle(response)
  },

  async sendChat(question) {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    return handle(response)
  },

  async listNotifications() {
    const response = await fetch(`${API_BASE}/api/notifications`)
    return handle(response)
  },

  async checkEmailNow() {
    const response = await fetch(`${API_BASE}/api/system/check-email-now`, { method: 'POST' })
    return handle(response)
  },
}

export { API_BASE }
