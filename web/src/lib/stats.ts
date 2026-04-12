export function median(nums: number[]): number | null {
  const a = nums.filter((n) => Number.isFinite(n)).sort((x, y) => x - y)
  if (!a.length) return null
  const m = Math.floor(a.length / 2)
  return a.length % 2 ? a[m]! : (a[m - 1]! + a[m]!) / 2
}

export function mean(nums: number[]): number | null {
  const a = nums.filter((n) => Number.isFinite(n))
  if (!a.length) return null
  return a.reduce((s, n) => s + n, 0) / a.length
}

export function sum(nums: number[]): number | null {
  const a = nums.filter((n) => Number.isFinite(n))
  if (!a.length) return null
  return a.reduce((s, n) => s + n, 0)
}

export function medianByGroup<T>(
  rows: T[],
  groupKey: (t: T) => string | null,
  valueKey: (t: T) => number | null,
): Record<string, number> {
  const map = new Map<string, number[]>()
  for (const r of rows) {
    const g = groupKey(r)
    const v = valueKey(r)
    if (!g || v == null) continue
    if (!map.has(g)) map.set(g, [])
    map.get(g)!.push(v)
  }
  const out: Record<string, number> = {}
  for (const [k, arr] of map) {
    const m = median(arr)
    if (m != null) out[k] = m
  }
  return out
}
