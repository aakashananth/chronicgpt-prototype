'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsHistoryResponse } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import MetricCard from './MetricCard'
import { Activity, Heart, Moon, Footprints, TrendingUp, TrendingDown } from 'lucide-react'

interface MetricCardsRowProps {
  refreshKey?: number
}

export default function MetricCardsRow({ refreshKey }: MetricCardsRowProps) {
  const [history, setHistory] = useState<MetricsHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTodayMetrics = async () => {
      try {
        setLoading(true)
        setError(null)
        // Get last 7 days to calculate trends
        const data = await apiClient.getMetricsHistory({ days: 7 })
        setHistory(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
        console.error('Failed to fetch metrics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchTodayMetrics()
  }, [refreshKey])

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

  if (error || !history || history.total_records === 0) {
    return (
      <Card>
        <CardContent className="py-12">
          <div className="text-center">
            <Activity className="h-10 w-10 mx-auto mb-3 text-muted-foreground opacity-50" />
            <h3 className="text-base font-semibold mb-2">No Metrics Available</h3>
            <p className="text-sm text-muted-foreground">
              {error || 'Run the pipeline to start tracking your health metrics.'}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Get today's values (last entry in arrays)
  const lastIndex = history.dates.length - 1
  const todayHrv = history.hrv[lastIndex]
  const todayRhr = history.resting_hr[lastIndex]
  const todaySleep = history.sleep_score[lastIndex]
  const todaySteps = history.steps[lastIndex]

  // Calculate trends (compare last value with average of previous 6 days)
  const calculateTrend = (values: number[], currentIndex: number): number | null => {
    if (currentIndex < 1 || values.length < 2) return null
    const current = values[currentIndex]
    const previous = values.slice(0, currentIndex)
    const avg = previous.reduce((a, b) => a + b, 0) / previous.length
    if (avg === 0) return null
    return ((current - avg) / avg) * 100
  }

  const hrvTrend = calculateTrend(history.hrv, lastIndex)
  const rhrTrend = calculateTrend(history.resting_hr, lastIndex)
  const sleepTrend = calculateTrend(history.sleep_score, lastIndex)
  const stepsTrend = calculateTrend(history.steps, lastIndex)

  // Get last 7 values for sparklines
  const getSparklineData = (values: number[], currentIndex: number): number[] => {
    const start = Math.max(0, currentIndex - 6)
    return values.slice(start, currentIndex + 1)
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="HRV"
        value={todayHrv}
        trend={hrvTrend}
        icon={<Activity className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)}ms`}
        sparklineData={getSparklineData(history.hrv, lastIndex)}
      />
      <MetricCard
        title="Resting HR"
        value={todayRhr}
        trend={rhrTrend ? -rhrTrend : null}
        icon={<Heart className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)} bpm`}
        sparklineData={getSparklineData(history.resting_hr, lastIndex)}
      />
      <MetricCard
        title="Sleep Score"
        value={todaySleep}
        trend={sleepTrend}
        icon={<Moon className="h-5 w-5" />}
        formatValue={(val) => `${val.toFixed(0)}/100`}
        sparklineData={getSparklineData(history.sleep_score, lastIndex)}
      />
      <MetricCard
        title="Steps"
        value={todaySteps}
        trend={stepsTrend}
        icon={<Footprints className="h-5 w-5" />}
        formatValue={(val) => val.toLocaleString()}
        sparklineData={getSparklineData(history.steps, lastIndex)}
      />
    </div>
  )
}

