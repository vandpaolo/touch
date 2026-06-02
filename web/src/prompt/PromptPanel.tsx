// web/prompt — the prompt panel anchored to the current selection (F6).
// Collects the prompt text and, on submit, the app sends one `plan` message
// {selection, prompt_text} to the backend. Chat-thread continuation for
// clarifications (F7) lands in T5.
import { useEffect, useRef, useState } from 'react'
import type { MsgPlan, Selection } from '../protocol-types'

/** The single `plan` message dispatched on submit (F6). */
export function buildPlanMessage(selection: Selection | null, promptText: string): MsgPlan {
  return { type: 'plan', prompt_text: promptText, selection }
}

export function PromptPanel({
  x,
  y,
  busy = false,
  onSubmit,
  onCancel,
}: {
  x: number
  y: number
  busy?: boolean
  onSubmit: (text: string) => void
  onCancel: () => void
}) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    ref.current?.focus()
  }, [])

  const submit = () => {
    const trimmed = text.trim()
    if (trimmed) onSubmit(trimmed)
  }

  return (
    <div className="prompt-panel" style={{ left: x, top: y }} role="dialog" aria-label="Prompt">
      <textarea
        ref={ref}
        className="prompt-input"
        placeholder="Describe the change… (e.g. add a 5 mm chamfer here)"
        value={text}
        rows={2}
        disabled={busy}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (busy) return
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          } else if (e.key === 'Escape') {
            e.preventDefault()
            onCancel()
          }
        }}
      />
      <div className="prompt-actions">
        {busy ? (
          <span className="prompt-working" aria-live="polite">
            <span className="prompt-spinner" aria-hidden="true" /> working…
          </span>
        ) : (
          <>
            <button type="button" className="prompt-btn prompt-cancel" onClick={onCancel}>
              Cancel
            </button>
            <button type="button" className="prompt-btn prompt-submit" onClick={submit}>
              Submit
            </button>
          </>
        )}
      </div>
    </div>
  )
}
