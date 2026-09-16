import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'

export default function OrderDetail() {
  const { id } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getOrder(id).then(setOrder).catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
      </div>
    )
  }

  if (!order) {
    return <div className="page">Loading order…</div>
  }

  return (
    <div className="page">
      <Link to="/" className="btn btn-ghost" style={{ marginBottom: 24, display: 'inline-flex' }}>
        <ArrowLeft size={15} /> Back to dashboard
      </Link>

      <div className="page-header">
        <div className="eyebrow">Order #{order.id}</div>
        <h1 className="page-title">{order.customer_name || 'Unknown customer'}</h1>
        <div style={{ marginTop: 12 }}>
          <StatusBadge status={order.status} />
        </div>
      </div>

      <div className="two-col">
        <div className="panel">
          <div className="section-title" style={{ color: 'white' }}>Order details</div>
          <div className="kv-row"><span className="kv-label">PO Number</span><span className="mono">{order.purchase_order_number || '—'}</span></div>
          <div className="kv-row"><span className="kv-label">Order date</span><span>{order.order_date || '—'}</span></div>
          <div className="kv-row"><span className="kv-label">Delivery date</span><span>{order.delivery_date || '—'}</span></div>
          <div className="kv-row"><span className="kv-label">Currency</span><span>{order.currency || '—'}</span></div>
          <div className="kv-row" style={{ borderBottom: 'none' }}>
            <span className="kv-label">AI confidence</span>
            <span>{order.confidence_score != null ? `${Math.round(order.confidence_score * 100)}%` : '—'}</span>
          </div>
        </div>

        <div>
          {order.validation_errors?.length > 0 && (
            <div className="alert alert-error">
              <div>
                <strong>Errors</strong>
                <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                  {order.validation_errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </div>
            </div>
          )}
          {order.validation_warnings?.length > 0 && (
            <div className="alert alert-warning">
              <div>
                <strong>Warnings</strong>
                <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                  {order.validation_warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            </div>
          )}
          {!order.validation_errors?.length && !order.validation_warnings?.length && (
            <div className="alert alert-success">Clean extraction — nothing flagged.</div>
          )}
        </div>
      </div>

      <div className="divider" />
      <div className="section-title">Line items</div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Product</th>
              <th>Qty</th>
              <th>Unit price</th>
              <th>Total</th>
              <th>Stock</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item, i) => (
              <tr key={i}>
                <td className="mono">{item.product_code || '—'}</td>
                <td>{item.product_name || '—'}</td>
                <td className="mono">{item.quantity ?? '—'}</td>
                <td className="mono">{item.unit_price ?? '—'}</td>
                <td className="mono">{item.total_price ?? '—'}</td>
                <td>{item.in_stock || 'unknown'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
