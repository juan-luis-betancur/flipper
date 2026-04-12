import { useEffect } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster'
import type { Property } from '../types/db'

import icon2x from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import shadow from 'leaflet/dist/images/marker-shadow.png'

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: icon, iconRetinaUrl: icon2x, shadowUrl: shadow })

type Pt = Pick<Property, 'id' | 'latitud' | 'longitud' | 'precio_por_m2' | 'url' | 'title' | 'price'>

function colorForM2(
  v: number | null,
  min: number,
  max: number,
): string {
  if (v == null || max <= min) return '#5a5a68'
  const t = (v - min) / (max - min)
  const g = Math.round(34 + (1 - t) * 80)
  const r = Math.round(40 + t * 200)
  const b = Math.round(50 + (1 - t) * 40)
  return `rgb(${r},${g},${b})`
}

function ClusterLayer({ points }: { points: Pt[] }) {
  const map = useMap()

  useEffect(() => {
    const vals = points.map((p) => p.precio_por_m2).filter((x): x is number => x != null)
    const min = vals.length ? Math.min(...vals) : 0
    const max = vals.length ? Math.max(...vals) : 1
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const group = (L as any).markerClusterGroup({ chunkedLoading: true })
    for (const p of points) {
      if (p.latitud == null || p.longitud == null) continue
      const col = colorForM2(p.precio_por_m2, min, max)
      const m = L.circleMarker([p.latitud, p.longitud], {
        radius: 8,
        color: col,
        fillColor: col,
        fillOpacity: 0.85,
        weight: 1,
      })
      m.bindPopup(
        `<div style="font-size:12px;color:#111"><strong>${p.title ?? ''}</strong><br/>${p.price ?? ''}<br/><a href="${p.url}" target="_blank" rel="noreferrer">Ver anuncio</a></div>`,
      )
      group.addLayer(m)
    }
    map.addLayer(group)
    return () => {
      map.removeLayer(group)
    }
  }, [map, points])

  return null
}

export function MarketMap({ properties }: { properties: Property[] }) {
  const pts: Pt[] = properties.filter((p) => p.latitud != null && p.longitud != null)
  if (!pts.length) {
    return (
      <div className="flex h-[360px] items-center justify-center rounded-lg border border-border bg-bg-secondary text-sm text-text-muted">
        Sin coordenadas para mostrar en mapa
      </div>
    )
  }
  const center: [number, number] = [6.2442, -75.5812]
  return (
    <MapContainer center={center} zoom={11} className="h-[360px] w-full rounded-lg" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClusterLayer points={pts} />
    </MapContainer>
  )
}
