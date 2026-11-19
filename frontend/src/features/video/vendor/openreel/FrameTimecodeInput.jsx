/* Adapted from OpenReel apps/web/src/components/editor/PreviewTimecode.tsx
 * 367d7e90b61b5181f9861b852bb8b9d7a7d2954a, MIT © 2024–2026 Augustus Otu and Contributors.
 * No OpenReel stores, credentials, storage, export or auth are imported.
 */
import { useId, useRef, useState } from 'react'
import { formatFrameTimecode, parseFrameTimecode } from './frame-timecode.mjs'
import { stepEditingFrame } from './editing-frame-rate.mjs'

export function FrameTimecodeInput({ position, duration, frameRate, onSeek }) {
  const id = useId()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState(false)
  const cancel = useRef(false)
  const seek = seconds => onSeek(Math.min(duration, Math.max(0, seconds)))
  return <div className="f4-frame-timecode">
    <input aria-label="Playhead timecode" aria-describedby={id}
      title={`Go to a frame · ${frameRate} fps · HH:MM:SS:FF (non-drop-frame); seconds accepted`}
      value={editing ? draft : formatFrameTimecode(position, frameRate)}
      aria-invalid={error} spellCheck={false}
      onFocus={() => {
        cancel.current = false
        setError(false)
        setDraft(formatFrameTimecode(position, frameRate))
        setEditing(true)
      }}
      onChange={event => { setDraft(event.currentTarget.value); setError(false) }}
      onBlur={() => {
        setEditing(false)
        if (cancel.current) { cancel.current = false; return }
        const time = parseFrameTimecode(draft, frameRate)
        if (time === null) { setError(true); return }
        seek(time)
      }}
      onKeyDown={event => {
        if (event.key === 'Enter') { event.preventDefault(); event.currentTarget.blur() }
        else if (event.key === 'Escape') {
          event.preventDefault()
          cancel.current = true
          setError(false)
          event.currentTarget.blur()
        } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
          event.preventDefault()
          const direction = event.key === 'ArrowUp' ? 1 : -1
          let time = parseFrameTimecode(draft, frameRate) ?? position
          for (let count = 0; count < (event.shiftKey ? 10 : 1); count++)
            time = stepEditingFrame(time, direction, frameRate)
          time = Math.min(duration, time)
          setDraft(formatFrameTimecode(time, frameRate))
          seek(time)
        }
      }} />
    <span aria-hidden="true">/</span>
    <output aria-label="Project duration">{formatFrameTimecode(duration, frameRate)}</output>
    <span id={id} className="f4-sr-only">Enter HH:MM:SS:FF or seconds. Up/down move one frame; Shift moves ten.</span>
    {error && <span role="alert" className="f4-frame-error">Enter valid HH:MM:SS:FF or seconds, such as 12.5.</span>}
  </div>
}
