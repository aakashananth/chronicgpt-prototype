'use client'

import { Card, CardContent } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface MetricCardProps {
  title: string
  value: string | number | null | undefined
  trend?: number | null
  trendLabel?: string
  icon?: React.ReactNode
  className?: string
  formatValue?: (val: number) => string
  sparklineData?: number[]
  invertTrend?: boolean // If true, lower values are better (e.g., Resting HR)
}

export default function MetricCard({
  title,
  value,
  trend,
  trendLabel,
  icon,
  className,
  formatValue,
  sparklineData,
  invertTrend = false,
}: MetricCardProps) {
  const displayValue =
    value !== null && value !== undefined
      ? formatValue && typeof value === 'number'
        ? formatValue(value)
        : typeof value === 'number'
        ? value.toLocaleString()
        : value
      : 'N/A'

  // For metrics where lower is better (like Resting HR), invert the trend interpretation
  const isGoodTrend = (trendValue: number) => {
    if (invertTrend) {
      // Lower is better: negative trend (decrease) is good
      return trendValue < 0
    } else {
      // Higher is better: positive trend (increase) is good
      return trendValue > 0
    }
  }

  const getTrendIcon = () => {
    if (trend === null || trend === undefined) return null
    const isGood = isGoodTrend(trend)
    if (trend > 0) {
      return <TrendingUp className={`h-4 w-4 ${isGood ? 'text-success' : 'text-destructive'}`} />
    }
    if (trend < 0) {
      return <TrendingDown className={`h-4 w-4 ${isGood ? 'text-success' : 'text-destructive'}`} />
    }
    return <Minus className="h-4 w-4 text-muted-foreground" />
  }

  const getTrendColor = () => {
    if (trend === null || trend === undefined) return 'text-muted-foreground'
    const isGood = isGoodTrend(trend)
    return isGood ? 'text-success' : 'text-destructive'
  }

  return (
    <Card className={cn('hover:border-border/80 transition-colors', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {icon && <div className="text-muted-foreground">{icon}</div>}
        </div>
        <div className="flex items-baseline gap-2">
          <p className="text-3xl font-bold">{displayValue}</p>
          {trend !== null && trend !== undefined && (
            <div className={cn('flex items-center gap-1 text-sm', getTrendColor())}>
              {getTrendIcon()}
              <span>{Math.abs(trend).toFixed(1)}%</span>
            </div>
          )}
        </div>
        {trendLabel && (
          <p className="text-xs text-muted-foreground mt-2">{trendLabel}</p>
        )}
        {sparklineData && sparklineData.length > 0 && (
          <div 
            className="mt-3 h-12 w-full opacity-60 relative group cursor-help"
            title={`7-day trend: Shows the last ${sparklineData.length} data points leading up to the selected date`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sparklineData.map((val, i) => ({ value: val ?? 0, index: i }))}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#888888"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
            {/* Tooltip on hover */}
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              <div className="bg-black/80 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                Last {sparklineData.length} days trend
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

