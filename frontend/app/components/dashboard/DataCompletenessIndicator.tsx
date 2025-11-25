'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, AlertCircle } from 'lucide-react'
import { apiClient, MetricsHistoryResponse } from '@/lib/api'

interface DataCompletenessIndicatorProps {
  days: number
  endDate?: string | null
  refreshKey?: number
}

export default function DataCompletenessIndicator({
  days,
  endDate,
  refreshKey,
}: DataCompletenessIndicatorProps) {
  const [completeness, setCompleteness] = useState<{
    total: number
    available: number
    percentage: number
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchCompleteness = async () => {
      try {
        setLoading(true)
        const history = await apiClient.getMetricsHistory({
          days,
          end_date: endDate || undefined,
        })
        
        const total = days
        const available = history.total_records
        const percentage = total > 0 ? Math.round((available / total) * 100) : 0

        setCompleteness({ total, available, percentage })
      } catch (err) {
        console.error('Failed to fetch completeness:', err)
        setCompleteness(null)
      } finally {
        setLoading(false)
      }
    }

    fetchCompleteness()
  }, [days, endDate, refreshKey])

  if (loading || !completeness) {
    return null
  }

  const getStatusColor = () => {
    if (completeness.percentage >= 90) return 'success'
    if (completeness.percentage >= 70) return 'warning'
    return 'destructive'
  }

  const StatusIcon = completeness.percentage >= 90 ? CheckCircle : AlertCircle

  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon className={`h-4 w-4 ${
              completeness.percentage >= 90 ? 'text-success' : 'text-warning'
            }`} />
            <span className="text-sm text-muted-foreground">Data completeness:</span>
            <span className="text-sm font-medium">
              {completeness.available} of {completeness.total} days
            </span>
          </div>
          <Badge variant={getStatusColor()}>
            {completeness.percentage}%
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}

