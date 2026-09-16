import { Check, X } from 'lucide-react'

export const STAGES = [
  { key: 'intake', label: 'Intake' },
  { key: 'extraction', label: 'Extraction' },
  { key: 'validation', label: 'Validation' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'billing', label: 'Billing' },
  { key: 'saved', label: 'Saved' },
]

/**
 * stageStatus: 'pending' | 'active' | 'done' | 'failed'
 * statuses: object keyed by stage key -> stageStatus
 */
export default function PipelineTracker({ statuses }) {
  return (
    <div className="pipeline">
      {STAGES.map((stage) => {
        const state = statuses[stage.key] || 'pending'
        return (
          <div className="pipeline-stage" key={stage.key}>
            <div className={`pipeline-track ${state === 'done' ? 'done' : ''}`} />
            <div className={`pipeline-node ${state}`}>
              {state === 'done' && <Check size={16} strokeWidth={3} />}
              {state === 'failed' && <X size={16} strokeWidth={3} />}
              {state !== 'done' && state !== 'failed' && stage.label[0]}
            </div>
            <div className="pipeline-label">{stage.label}</div>
          </div>
        )
      })}
    </div>
  )
}

export function PipelineMini({ status }) {
  // Compact dot-row used inside the orders table
  const doneCount =
    status === 'validated' || status === 'invoiced' || status === 'checked'
      ? STAGES.length
      : status === 'validation_failed'
      ? 3
      : 1

  const failed = status === 'validation_failed'

  return (
    <div className="pipeline-mini">
      {STAGES.map((s, i) => (
        <span
          key={s.key}
          className={`pipeline-mini-dot ${
            i < doneCount ? (failed && i === doneCount - 1 ? 'failed' : 'done') : ''
          }`}
          title={s.label}
        />
      ))}
    </div>
  )
}
