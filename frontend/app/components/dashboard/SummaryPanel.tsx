'use client'

import { useEffect, useState, useMemo } from 'react'
import { apiClient, MetricsHistoryResponse } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react'
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subWeeks, subMonths } from 'date-fns'

interface SummaryPanelProps {
  days: number
  endDate?: string | null
  refreshKey?: number
}

export default function SummaryPanel({ days, endDate, refreshKey }: SummaryPanelProps) {
  const [history, setHistory] = useState<MetricsHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getMetricsHistory({
          days,
          end_date: endDate || undefined,
        })
        setHistory(data)
      } catch (err) {
        console.error('Failed to fetch summary:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [days, endDate, refreshKey])

  const summary = useMemo(() => {
    if (!history || history.total_records === 0) return null

    const values = {
      hrv: history.hrv.filter(v => v !== null) as number[],
      resting_hr: history.resting_hr.filter(v => v !== null) as number[],
      sleep_score: history.sleep_score.filter(v => v !== null) as number[],
      steps: history.steps.filter(v => v !== null) as number[],
    }

    const calculateStats = (arr: number[]) => {
      if (arr.length === 0) return null
      const sorted = [...arr].sort((a, b) => a - b)
      const avg = arr.reduce((a, b) => a + b, 0) / arr.length
      const median = sorted.length % 2 === 0
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[Math.floor(sorted.length / 2)]
      return {
        avg: Math.round(avg * 10) / 10,
        median: Math.round(median * 10) / 10,
        min: sorted[0],
        max: sorted[sorted.length - 1],
      }
    }

    // Calculate trends (compare last 7 days vs previous 7 days)
    const getTrend = (arr: number[]) => {
      if (arr.length < 14) return null
      const recent = arr.slice(-7)
      const previous = arr.slice(-14, -7)
      if (previous.length === 0) return null
      const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length
      const previousAvg = previous.reduce((a, b) => a + b, 0) / previous.length
      if (previousAvg === 0) return null
      return ((recentAvg - previousAvg) / previousAvg) * 100
    }

    return {
      hrv: { stats: calculateStats(values.hrv), trend: getTrend(values.hrv) },
      resting_hr: { stats: calculateStats(values.resting_hr), trend: getTrend(values.resting_hr) },
      sleep_score: { stats: calculateStats(values.sleep_score), trend: getTrend(values.sleep_score) },
      steps: { stats: calculateStats(values.steps), trend: getTrend(values.steps) },
      anomalyCount: history.is_anomalous.filter(Boolean).length,
      totalDays: history.total_records,
    }
  }, [history])

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse text-muted-foreground">Loading summary...</div>
        </CardContent>
      </Card>
    )
  }

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No data available for summary
          </div>
        </CardContent>
      </Card>
    )
  }

  const StatRow = ({ label, stats, trend, formatValue }: {
    label: string
    stats: { avg: number; median: number; min: number; max: number } | null
    trend: number | null
    formatValue?: (val: number) => string
  }) => {
    if (!stats) return null
    const format = formatValue || ((v: number) => v.toFixed(1))
    const TrendIcon = trend && trend > 0 ? TrendingUp : trend && trend < 0 ? TrendingDown : null
    const trendColor = trend && trend > 0 ? 'text-success' : trend && trend < 0 ? 'text-destructive' : 'text-muted-foreground'

    return (
      <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
        <div className="flex-1">
          <div className="text-sm font-medium">{label}</div>
          <div className="text-xs text-muted-foreground mt-0.5">
            Avg: {format(stats.avg)} | Med: {format(stats.median)} | Range: {format(stats.min)}-{format(stats.max)}
          </div>
        </div>
        {trend !== null && TrendIcon && (
          <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
            <TrendIcon className="h-3 w-3" />
            <span>{Math.abs(trend).toFixed(1)}%</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-foreground" />
          <CardTitle>Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-muted-foreground">
              {summary.totalDays} days analyzed
            </span>
            {summary.anomalyCount > 0 && (
              <Badge variant={summary.anomalyCount > 5 ? 'destructive' : 'warning'}>
                {summary.anomalyCount} anomalies
              </Badge>
            )}
          </div>
          <StatRow
            label="HRV"
            stats={summary.hrv.stats}
            trend={summary.hrv.trend}
            formatValue={(v) => `${v.toFixed(0)}ms`}
          />
          <StatRow
            label="Resting HR"
            stats={summary.resting_hr.stats}
            trend={summary.resting_hr.trend ? -summary.resting_hr.trend : null}
            formatValue={(v) => `${v.toFixed(0)} bpm`}
          />
          <StatRow
            label="Sleep Score"
            stats={summary.sleep_score.stats}
            trend={summary.sleep_score.trend}
            formatValue={(v) => `${v.toFixed(0)}/100`}
          />
          <StatRow
            label="Steps"
            stats={summary.steps.stats}
            trend={summary.steps.trend}
            formatValue={(v) => v.toLocaleString()}
          />
        </div>
      </CardContent>
    </Card>
  )
}

