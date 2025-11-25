'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Dot,
} from 'recharts'

interface TimeSeriesChartProps {
  title: string
  data: Array<{ date: string; value: number | null; isAnomaly?: boolean }>
  color?: string
  unit?: string
  height?: number
}

export default function TimeSeriesChart({
  title,
  data,
  color = '#ffffff',
  unit = '',
  height = 300,
}: TimeSeriesChartProps) {
  const chartData = data.map((d) => ({
    date: d.date,
    value: d.value,
    isAnomaly: d.isAnomaly || false,
  }))

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (payload.isAnomaly) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={5}
          fill="#ef4444"
          stroke="#fff"
          strokeWidth={2}
        />
      )
    }
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333333" />
            <XAxis
              dataKey="date"
              stroke="#888888"
              tick={{ fill: '#888888', fontSize: 12 }}
            />
            <YAxis
              stroke="#888888"
              tick={{ fill: '#888888', fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#111111',
                border: '1px solid #333333',
                borderRadius: '6px',
                color: '#ffffff',
              }}
              labelStyle={{ color: '#ffffff' }}
              formatter={(value: any) => [
                `${value}${unit}`,
                title,
              ]}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={<CustomDot />}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

