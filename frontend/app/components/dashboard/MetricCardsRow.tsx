'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsResponse } from '@/lib/api'
import MetricCard from './MetricCard'
import { Activity, Heart, Moon, Footprints } from 'lucide-react'
import { format, subDays } from 'date-fns'

export default function MetricCardsRow() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getMetrics()
        setMetrics(data)
      } catch (err) {
        console.error('Failed to fetch metrics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-32 bg-card border border-border rounded-lg animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (!metrics) {
    return null
  }

  // Extract today's metrics if available
  // The API might return a summary or array - we'll handle both
  const metricData = metrics as any

  // Calculate trends (simplified - would need historical data for real trends)
  // For now, we'll just show the current values
  const today = new Date()
  const weekAgo = subDays(today, 7)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="HRV"
        value={metricData.hrv}
        icon={<Activity className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)}ms`}
      />
      <MetricCard
        title="Resting HR"
        value={metricData.resting_hr}
        icon={<Heart className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)} bpm`}
      />
      <MetricCard
        title="Sleep Score"
        value={metricData.sleep_score}
        icon={<Moon className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)}/100`}
      />
      <MetricCard
        title="Steps"
        value={metricData.steps}
        icon={<Footprints className="h-5 w-5" />}
        formatValue={(val) => val.toLocaleString()}
      />
    </div>
  )
}

