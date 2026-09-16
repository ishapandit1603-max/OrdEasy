const LABELS = {
  validated: 'Validated',
  validation_failed: 'Needs review',
  received: 'Received',
  checked: 'Checked',
  invoiced: 'Invoiced',
}

export default function StatusBadge({ status }) {
  const cls = `badge badge-${status || 'received'}`
  return (
    <span className={cls}>
      <span className="badge-dot" />
      {LABELS[status] || status || 'Unknown'}
    </span>
  )
}
