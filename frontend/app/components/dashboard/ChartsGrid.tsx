'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsHistoryResponse } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import HrvTrendChart from '../charts/HrvTrendChart'
import RestingHrTrendChart from '../charts/RestingHrTrendChart'
import SleepScoreTrendChart from '../charts/SleepScoreTrendChart'
import StepsTrendChart from '../charts/StepsTrendChart'
import { BarChart3 } from 'lucide-react'
import { format } from 'date-fns'

interface ChartsGridProps {
  days?: number
  endDate?: string | null
  refreshKey?: number
}

export default function ChartsGrid({ days = 30, endDate, refreshKey }: ChartsGridProps) {
  const [history, setHistory] = useState<MetricsHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getMetricsHistory({
          days,
          end_date: endDate || undefined,
        })
        setHistory(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics history')
        console.error('Failed to fetch metrics history:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [days, endDate, refreshKey])

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

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-destructive mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!history || history.total_records === 0) {
    return (
      <Card>
        <CardContent className="py-16">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
            <p className="text-muted-foreground mb-4">
              Run the pipeline to start tracking your health metrics.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Transform data for charts - format dates and combine with values
  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM d')
    } catch {
      return dateStr
    }
  }

  const hrvData = history.dates.map((date, i) => ({
    date: formatDate(date),
    value: history.hrv[i] ?? null,
    isAnomaly: history.is_anomalous[i] || false,
  })).filter(d => d.value !== null)

  const rhrData = history.dates.map((date, i) => ({
    date: formatDate(date),
    value: history.resting_hr[i] ?? null,
    isAnomaly: history.is_anomalous[i] || false,
  })).filter(d => d.value !== null)

  const sleepData = history.dates.map((date, i) => ({
    date: formatDate(date),
    value: history.sleep_score[i] ?? null,
    isAnomaly: history.is_anomalous[i] || false,
  })).filter(d => d.value !== null)

  const stepsData = history.dates.map((date, i) => ({
    date: formatDate(date),
    value: history.steps[i] ?? null,
    isAnomaly: history.is_anomalous[i] || false,
  })).filter(d => d.value !== null)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <HrvTrendChart data={hrvData} />
      <RestingHrTrendChart data={rhrData} />
      <SleepScoreTrendChart data={sleepData} />
      <StepsTrendChart data={stepsData} />
    </div>
  )
}

