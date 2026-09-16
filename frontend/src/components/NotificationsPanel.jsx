import { useEffect, useState } from 'react'
import { Bell, Mail, RefreshCw } from 'lucide-react'
import { api } from '../api'

const LEVEL_COLOR = {
  error: 'var(--red)',
  warning: 'var(--amber)',
  info: 'var(--green)',
}

export default function NotificationsPanel() {
  const [notes, setNotes] = useState([])
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    load()
    const interval = setInterval(load, 20000) // poll every 20s for near-live updates
    return () => clearInterval(interval)
  }, [])

  async function load() {
    try {
      const data = await api.listNotifications()
      setNotes(data)
    } catch (e) {
      // silent - dashboard already shows a connection error if backend is down
    }
  }

  async function checkNow() {
    setChecking(true)
    try {
      await api.checkEmailNow()
      await load()
    } catch (e) {
      // no-op, likely email polling isn't configured
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div className="section-title" style={{ color: 'white', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Bell size={16} /> Notifications
        </div>
        <button className="btn" style={{ padding: '8px 12px', fontSize: 12 }} onClick={checkNow} disabled={checking}>
          {checking ? <span className="loader" /> : <Mail size={13} />}
          Check inbox now
        </button>
      </div>

      {notes.length === 0 ? (
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13.5 }}>
          No notifications yet. They'll appear here as orders are processed.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 260, overflowY: 'auto' }}>
          {notes.map((n) => (
            <div key={n.id} style={{ borderLeft: `3px solid ${LEVEL_COLOR[n.level] || '#888'}`, paddingLeft: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{n.title}</div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.6)' }}>{n.message}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
