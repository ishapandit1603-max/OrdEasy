import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { PackageSearch, Wallet, ShieldAlert, ListChecks } from 'lucide-react'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge'
import { PipelineMini } from '../components/PipelineTracker'
import NotificationsPanel from '../components/NotificationsPanel'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    load()
  }, [])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [summaryData, ordersData] = await Promise.all([
        api.getDashboard(),
        api.listOrders(),
      ])
      setSummary(summaryData)
      setOrders(ordersData)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const shortageCount = orders.filter((o) => o.status === 'validation_failed').length

  const chartData = (summary?.top_products || []).map((p) => ({
    name: p.product_code,
    quantity: p.total_quantity,
  }))

  return (
    <div className="page">
      <div className="page-header">
        <div className="eyebrow">Live Operations</div>
        <h1 className="page-title">Order Intelligence Dashboard</h1>
        <p className="page-subtitle">
          Every purchase order that comes through the intake pipeline, tracked end to end —
          from raw upload to invoiced and shipped.
        </p>
      </div>

      {error && (
        <div className="alert alert-error">
          Couldn't reach the backend at the configured API address. Make sure
          <code style={{ margin: '0 4px' }}>uvicorn app.main:app --reload</code> is running. ({error})
        </div>
      )}

      <div className="card-grid">
        <StatCard
          icon={<ListChecks size={18} />}
          label="Total Orders"
          value={summary?.total_orders ?? '—'}
          foot="Processed since launch"
        />
        <StatCard
          icon={<Wallet size={18} />}
          label="Total Revenue"
          value={summary ? `₹${summary.total_revenue.toLocaleString('en-IN')}` : '—'}
          foot="From billed line items"
        />
        <StatCard
          icon={<ShieldAlert size={18} />}
          label="Needs Review"
          value={shortageCount}
          foot="Failed validation or has shortages"
        />
        <StatCard
          icon={<PackageSearch size={18} />}
          label="Top Product"
          value={chartData[0]?.name || '—'}
          foot={chartData[0] ? `${chartData[0].quantity} units moved` : 'No data yet'}
        />
      </div>

      <div className="two-col">
        <div className="panel">
          <div className="section-title" style={{ color: 'white' }}>Top products by quantity</div>
          {chartData.length === 0 ? (
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13.5 }}>
              Process a few orders to see product demand here.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" fontSize={11} />
                <YAxis stroke="rgba(255,255,255,0.5)" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: '#1A1512', border: '1px solid #FFB100', borderRadius: 6 }}
                  labelStyle={{ color: '#FFB100' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="quantity" fill="#FFB100" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="panel">
          <div className="section-title" style={{ color: 'white' }}>Status breakdown</div>
          {!summary || Object.keys(summary.status_breakdown || {}).length === 0 ? (
            <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13.5 }}>No orders yet.</div>
          ) : (
            Object.entries(summary.status_breakdown).map(([status, count]) => (
              <div className="kv-row" key={status}>
                <span className="kv-label">{status.replace('_', ' ')}</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{count}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="divider" />

      <div className="two-col">
        <NotificationsPanel />
        <div className="panel-cream">
          <div className="section-title">Data sources</div>
          <p style={{ fontSize: 13.5, opacity: 0.8, marginTop: 0 }}>
            Orders can arrive two ways: someone uploads a file on the Upload page,
            or the system automatically checks a connected inbox and pulls in any
            PDF/Excel/image attachments on its own.
          </p>
          <p style={{ fontSize: 13, opacity: 0.7 }}>
            Email polling is off by default — turn it on with
            <code style={{ margin: '0 4px' }}>ENABLE_EMAIL_POLLING=true</code>
            in the backend's <code>.env</code> file.
          </p>
        </div>
      </div>

      <div className="divider" />

      <div className="section-title">Recent orders</div>

      {orders.length === 0 && !loading ? (
        <div className="table-wrap">
          <div className="empty-state">
            <div className="empty-state-title">No orders processed yet</div>
            <div>Upload a purchase order to see it move through the pipeline.</div>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Pipeline</th>
                <th>Items</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} onClick={() => navigate(`/orders/${o.id}`)}>
                  <td className="mono">#{o.id} · {o.purchase_order_number || '—'}</td>
                  <td>{o.customer_name || '—'}</td>
                  <td><StatusBadge status={o.status} /></td>
                  <td><PipelineMini status={o.status} /></td>
                  <td className="mono">{o.item_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, label, value, foot }) {
  return (
    <div className="stat-card">
      <div className="stat-label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {icon} {label}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-foot">{foot}</div>
    </div>
  )
}
