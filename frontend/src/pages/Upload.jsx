import { useCallback, useRef, useState } from 'react'
import { UploadCloud, FileText, AlertTriangle, CheckCircle2, RefreshCcw } from 'lucide-react'
import { api } from '../api'
import PipelineTracker from '../components/PipelineTracker'

const STAGE_ORDER = ['intake', 'extraction', 'validation', 'inventory', 'billing', 'saved']

const initialStatuses = () =>
  Object.fromEntries(STAGE_ORDER.map((s) => [s, 'pending']))

export default function Upload() {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [statuses, setStatuses] = useState(initialStatuses())
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const timerRef = useRef(null)

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files?.[0]) {
      setFile(e.dataTransfer.files[0])
      setResult(null)
      setError(null)
    }
  }, [])

  function onPick(e) {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  function startSimulatedProgress() {
    let index = 0
    setStatuses(initialStatuses())
    timerRef.current = setInterval(() => {
      setStatuses((prev) => {
        const next = { ...prev }
        if (index > 0) next[STAGE_ORDER[index - 1]] = 'done'
        if (index < STAGE_ORDER.length - 1) next[STAGE_ORDER[index]] = 'active'
        return next
      })
      index += 1
      if (index >= STAGE_ORDER.length) clearInterval(timerRef.current)
    }, 700)
  }

  async function handleProcess() {
    if (!file) return
    setProcessing(true)
    setResult(null)
    setError(null)
    startSimulatedProgress()

    try {
      const response = await api.uploadOrder(file)
      clearInterval(timerRef.current)

      if (response.status !== 'success') {
        markFailedAt(response.stage)
        setError(response.message || 'Processing failed.')
      } else {
        const allDone = Object.fromEntries(STAGE_ORDER.map((s) => [s, 'done']))
        if (!response.validation.valid) {
          allDone.validation = 'failed'
        }
        setStatuses(allDone)
        setResult(response)
      }
    } catch (e) {
      clearInterval(timerRef.current)
      setError(e.message)
      markFailedAt('extraction')
    } finally {
      setProcessing(false)
    }
  }

  function markFailedAt(stageGuess) {
    const idx = STAGE_ORDER.indexOf(stageGuess === 'pdf_service' || stageGuess === 'excel_service' || stageGuess === 'ocr_service' ? 'intake' : stageGuess)
    const next = initialStatuses()
    for (let i = 0; i < STAGE_ORDER.length; i++) {
      if (idx === -1) break
      if (i < idx) next[STAGE_ORDER[i]] = 'done'
      else if (i === idx) next[STAGE_ORDER[i]] = 'failed'
    }
    setStatuses(next)
  }

  function reset() {
    setFile(null)
    setResult(null)
    setError(null)
    setStatuses(initialStatuses())
  }

  return (
    <div className="page">
      <div className="page-header">
        <div className="eyebrow">Intake</div>
        <h1 className="page-title">Upload a Purchase Order</h1>
        <p className="page-subtitle">
          Drop in a PDF or Excel order. It runs through Intake, Extraction, Validation, Inventory
          and Billing automatically — no manual data entry.
        </p>
      </div>

      <div className="two-col">
        <div>
          <div
            className={`dropzone ${dragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
          >
            <div className="dropzone-icon">
              <UploadCloud size={26} />
            </div>
            <div className="dropzone-title">
              {file ? 'File ready to process' : 'Drag a file here, or click to browse'}
            </div>
            <div className="dropzone-sub">Supports .pdf, .xlsx, .xls, .csv</div>

            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg"
              style={{ display: 'none' }}
              onChange={onPick}
            />

            {file && (
              <div style={{ marginTop: 20 }}>
                <span className="file-chip">
                  <FileText size={15} /> {file.name}
                </span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
            <button className="btn" disabled={!file || processing} onClick={handleProcess}>
              {processing && <span className="loader" />}
              {processing ? 'Processing order…' : 'Process order'}
            </button>
            <button className="btn btn-ghost" onClick={reset} disabled={processing}>
              <RefreshCcw size={15} /> Reset
            </button>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginTop: 20 }}>
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              <div>{error}</div>
            </div>
          )}
        </div>

        <div className="panel-cream">
          <div className="section-title">Pipeline status</div>
          <PipelineTracker statuses={statuses} />
        </div>
      </div>

      {result && (
        <>
          <div className="divider" />
          <ResultPanel result={result} />
        </>
      )}
    </div>
  )
}

function ResultPanel({ result }) {
  const { validation, inventory, invoice, order_id } = result

  return (
    <div>
      <div className="section-title">
        Order #{order_id} — {validation.valid ? 'Validated' : 'Needs review'}
      </div>

      {validation.errors.length > 0 && (
        <div className="alert alert-error">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>{validation.errors.length} issue(s) found:</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              {validation.errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        </div>
      )}

      {validation.warnings.length > 0 && (
        <div className="alert alert-warning">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>{validation.warnings.length} warning(s):</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              {validation.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}

      {inventory.has_shortages && (
        <div className="alert alert-warning">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong>Stock shortages:</strong>
            <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              {inventory.shortages.map((s, i) => (
                <li key={i}>{s.product_code}: requested {s.requested}, only {s.available} in stock</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {!validation.errors.length && !inventory.has_shortages && (
        <div className="alert alert-success">
          <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          <div>Order extracted cleanly and stock is fully available.</div>
        </div>
      )}

      <div className="two-col" style={{ marginTop: 20 }}>
        <div className="panel">
          <div className="section-title" style={{ color: 'white' }}>Invoice</div>
          <div className="kv-row"><span className="kv-label">Customer</span><span>{invoice.customer_name || '—'}</span></div>
          <div className="kv-row"><span className="kv-label">PO Number</span><span className="mono">{invoice.purchase_order_number || '—'}</span></div>
          <div className="kv-row"><span className="kv-label">Subtotal</span><span className="mono">{invoice.currency} {invoice.subtotal.toLocaleString()}</span></div>
          <div className="kv-row"><span className="kv-label">GST ({invoice.gst_rate * 100}%)</span><span className="mono">{invoice.currency} {invoice.gst_amount.toLocaleString()}</span></div>
          <div className="kv-row" style={{ fontWeight: 700, borderBottom: 'none' }}>
            <span className="kv-label" style={{ color: 'var(--amber)' }}>Grand total</span>
            <span className="mono">{invoice.currency} {invoice.grand_total.toLocaleString()}</span>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Code</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Stock</th>
              </tr>
            </thead>
            <tbody>
              {invoice.items.map((item, i) => (
                <tr key={i}>
                  <td className="mono">{item.product_code || '—'}</td>
                  <td className="mono">{item.quantity ?? '—'}</td>
                  <td className="mono">{item.unit_price ?? '—'}</td>
                  <td>{item.in_stock || 'unknown'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
