import { useEffect, useState } from 'react'
import { formatCOP, parseLooseCOPInput } from '../lib/format'

type Props = {
  value: number | null
  onChange: (n: number | null) => void
  id?: string
  className?: string
  'aria-label'?: string
}

export function CurrencyTextInput({ value, onChange, id, className, 'aria-label': aria }: Props) {
  const [focused, setFocused] = useState(false)
  const [draft, setDraft] = useState('')

  useEffect(() => {
    if (!focused) {
      setDraft(value != null ? formatCOP(value) : '')
    }
  }, [value, focused])

  const display = focused ? draft : value != null ? formatCOP(value) : ''

  return (
    <input
      id={id}
      type="text"
      inputMode="decimal"
      aria-label={aria}
      value={display}
      onFocus={() => {
        setFocused(true)
        setDraft(value != null ? String(Math.round(value)) : '')
      }}
      onChange={(e) => {
        const t = e.target.value
        setDraft(t)
        onChange(parseLooseCOPInput(t))
      }}
      onBlur={() => {
        setFocused(false)
        const n = parseLooseCOPInput(draft)
        onChange(n)
      }}
      className={className}
    />
  )
}
