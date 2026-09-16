import { useEffect, useRef, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { api } from '../api'

const SUGGESTIONS = [
  'Which orders are pending review?',
  'What is the total revenue so far?',
  'Are there any stock shortages right now?',
  'Show me the latest order from any customer.',
]

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi, I'm the SmartOrder assistant. Ask me about any order that's been processed — status, stock, totals, anything on file.",
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  async function send(question) {
    const q = (question ?? input).trim()
    if (!q || sending) return

    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setInput('')
    setSending(true)

    try {
      const response = await api.sendChat(q)
      const text = response.status === 'success'
        ? response.answer
        : `I couldn't get an answer (${response.message || 'unknown error'}).`
      setMessages((prev) => [...prev, { role: 'assistant', text }])
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', text: `Something went wrong: ${e.message}` }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="eyebrow">Conversation Agent</div>
        <h1 className="page-title">Ask about your orders</h1>
        <p className="page-subtitle">
          Grounded entirely in what's actually in the database — no invented order numbers or totals.
        </p>
      </div>

      <div className="chat-shell">
        <div className="chat-messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div className={`chat-bubble ${m.role}`} key={i}>
              {m.text}
            </div>
          ))}
          {sending && <div className="chat-bubble assistant thinking">Checking the order records…</div>}
        </div>

        <div className="chat-inputbar">
          <input
            className="chat-input"
            placeholder="e.g. Which orders need review this week?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <button className="btn" onClick={() => send()} disabled={sending || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
      </div>

      <div className="chat-suggestions">
        {SUGGESTIONS.map((s) => (
          <button className="chip-btn" key={s} onClick={() => send(s)} disabled={sending}>
            <Sparkles size={12} style={{ marginRight: 6, verticalAlign: -2 }} />
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
