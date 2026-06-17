// web/prompt — the prompt panel anchored to the current selection (F6).
// Collects the prompt text and, on submit, the app sends one `plan` message
// {selection, prompt_text}. When the backend replies with a clarifying question
// (F7), the app feeds the running `thread` here and the panel becomes a short
// chat: each submit is a reply that resumes planning.
import { useEffect, useRef, useState } from 'react'
import type { MsgPlan, Selection } from '../protocol-types'

/** The single `plan` message dispatched on submit (F6). */
export function buildPlanMessage(selection: Selection | null, promptText: string): MsgPlan {
  return { type: 'plan', prompt_text: promptText, selection }
}

export interface ThreadTurn {
  from: 'assistant' | 'user'
  text: string
}

export function PromptPanel({
  x,
  y,
  busy = false,
  thread = [],
  onSubmit,
  onCancel,
}: {
  x: number
  y: number
  busy?: boolean
  thread?: ThreadTurn[]
  onSubmit: (text: string) => void
  onCancel: () => void
}) {
  const [text, setText] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)
  const inDialogue = thread.length > 0

  // Re-focus the input whenever a new turn arrives (and on first open).
  useEffect(() => {
    ref.current?.focus()
  }, [thread.length])

  const submit = () => {
    const trimmed = text.trim()
    if (trimmed) {
      onSubmit(trimmed)
      setText('') // a multi-turn reply box starts empty for the next turn
    }
  }

  return (
    <div className="prompt-panel" style={{ left: x, top: y }} role="dialog" aria-label="Prompt">
      {inDialogue && (
        <div className="prompt-thread" aria-live="polite">
          {thread.map((turn, i) => (
            <div key={i} className={`prompt-turn prompt-turn-${turn.from}`}>
              {turn.text}
            </div>
          ))}
        </div>
      )}
      <textarea
        ref={ref}
        className="prompt-input"
        placeholder={
          inDialogue ? 'Your reply…' : 'Describe the change… (e.g. add a 5 mm chamfer here)'
        }
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
              {inDialogue ? 'Reply' : 'Submit'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
