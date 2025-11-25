'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsResponse } from '@/lib/api'
import TimeSeriesChart from './TimeSeriesChart'
import { format, parseISO, subDays } from 'date-fns'

interface ChartsGridProps {
  timeRange?: number
  selectedDate?: string
}

export default function ChartsGrid({
  timeRange = 7,
  selectedDate,
}: ChartsGridProps) {
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
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-80 bg-card border border-border rounded-lg animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        No metrics data available. Run the pipeline to generate charts.
      </div>
    )
  }

  // Transform metrics data for charts
  // This is a simplified version - in production, you'd want to fetch
  // time-series data from the API
  const metricData = metrics as any

  // Mock time-series data structure
  // In production, this would come from the API
  const generateMockData = (metricName: string, baseValue: number) => {
    const days = Array.from({ length: timeRange }, (_, i) => {
      const date = subDays(new Date(), timeRange - i - 1)
      return {
        date: format(date, 'MMM d'),
        value: baseValue + (Math.random() - 0.5) * baseValue * 0.2,
        isAnomaly: false,
      }
    })
    return days
  }

  const hrvData = metricData.hrv
    ? generateMockData('hrv', metricData.hrv)
    : []
  const rhrData = metricData.resting_hr
    ? generateMockData('resting_hr', metricData.resting_hr)
    : []
  const sleepData = metricData.sleep_score
    ? generateMockData('sleep_score', metricData.sleep_score)
    : []
  const stepsData = metricData.steps
    ? generateMockData('steps', metricData.steps)
    : []

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <TimeSeriesChart
        title="HRV Trend"
        data={hrvData}
        color="#ffffff"
        unit="ms"
      />
      <TimeSeriesChart
        title="Resting HR Trend"
        data={rhrData}
        color="#888888"
        unit=" bpm"
      />
      <TimeSeriesChart
        title="Sleep Score Trend"
        data={sleepData}
        color="#cccccc"
        unit="/100"
      />
      <TimeSeriesChart
        title="Steps Trend"
        data={stepsData}
        color="#aaaaaa"
        unit=""
      />
    </div>
  )
}

