'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

interface HrvTrendChartProps {
  data: Array<{ date: string; value: number; isAnomaly?: boolean }>
  height?: number
}

export default function HrvTrendChart({ data, height = 300 }: HrvTrendChartProps) {
  // Calculate baseline (7-day rolling median)
  const baseline = useMemo(() => {
    if (data.length === 0) return null
    const values = data.map((d) => d.value).filter((v) => v !== null) as number[]
    if (values.length === 0) return null
    
    // Calculate median of all values as baseline
    const sorted = [...values].sort((a, b) => a - b)
    const mid = Math.floor(sorted.length / 2)
    return sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid]
  }, [data])

  // Custom dot component for anomalies
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (payload.isAnomaly) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={5}
          fill="#ef4444"
          stroke="#ffffff"
          strokeWidth={2}
        />
      )
    }
    return (
      <circle
        cx={cx}
        cy={cy}
        r={3}
        fill="#ffffff"
      />
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">HRV Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
            <XAxis
              dataKey="date"
              stroke="#888888"
              tick={{ fill: '#888888', fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              stroke="#888888"
              tick={{ fill: '#888888', fontSize: 12 }}
              label={{ value: 'ms', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111111',
                border: '1px solid #333333',
                borderRadius: '6px',
                color: '#ffffff',
              }}
              labelStyle={{ color: '#ffffff' }}
              formatter={(value: any, name: string, props: any) => {
                const parts = [`${value}ms`, 'HRV']
                if (props.payload.isAnomaly) {
                  parts.push('⚠️ Anomaly')
                }
                return parts
              }}
            />
            {baseline && (
              <ReferenceLine
                y={baseline}
                stroke="#888888"
                strokeDasharray="5 5"
                strokeWidth={1}
                label={{ value: 'Baseline', position: 'right', fill: '#888888', fontSize: 10 }}
              />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke="#ffffff"
              strokeWidth={2}
              dot={<CustomDot />}
              activeDot={{ r: 6, fill: '#ffffff' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

