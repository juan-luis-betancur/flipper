import { useEffect, useState } from 'react'
import { formatAreaM2, parseLooseIntegerInput } from '../lib/format'

type Props = {
  value: number | null
  onChange: (n: number | null) => void
  id?: string
  className?: string
  'aria-label'?: string
}

export function AreaM2TextInput({ value, onChange, id, className, 'aria-label': aria }: Props) {
  const [focused, setFocused] = useState(false)
  const [draft, setDraft] = useState('')

  useEffect(() => {
    if (!focused) {
      setDraft(value != null ? formatAreaM2(value) : '')
    }
  }, [value, focused])

  const display = focused ? draft : value != null ? formatAreaM2(value) : ''

  return (
    <input
      id={id}
      type="text"
      inputMode="numeric"
      aria-label={aria}
      value={display}
      onFocus={() => {
        setFocused(true)
        setDraft(value != null ? String(Math.round(value)) : '')
      }}
      onChange={(e) => {
        const t = e.target.value
        setDraft(t)
        onChange(parseLooseIntegerInput(t))
      }}
      onBlur={() => {
        setFocused(false)
        const n = parseLooseIntegerInput(draft)
        onChange(n)
      }}
      className={className}
    />
  )
}
