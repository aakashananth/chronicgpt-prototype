'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface DateRangeSelectorProps {
  onDateChange?: (date: string | null) => void
  onDaysChange?: (days: number) => void
  defaultDays?: number
}

const QUICK_PRESETS = [
  { label: '7d', days: 7 },
  { label: '14d', days: 14 },
  { label: '30d', days: 30 },
  { label: '60d', days: 60 },
  { label: '90d', days: 90 },
]

export default function DateRangeSelector({
  onDateChange,
  onDaysChange,
  defaultDays = 30,
}: DateRangeSelectorProps) {
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  )
  const [days, setDays] = useState<number>(defaultDays)

  useEffect(() => {
    if (onDateChange) {
      onDateChange(selectedDate)
    }
  }, [selectedDate, onDateChange])

  useEffect(() => {
    if (onDaysChange) {
      onDaysChange(days)
    }
  }, [days, onDaysChange])

  const handlePresetClick = (presetDays: number) => {
    setDays(presetDays)
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">Quick presets:</span>
            {QUICK_PRESETS.map((preset) => (
              <Button
                key={preset.days}
                variant={days === preset.days ? 'default' : 'outline'}
                size="sm"
                onClick={() => handlePresetClick(preset.days)}
                className="h-7 px-3 text-xs"
              >
                {preset.label}
              </Button>
            ))}
          </div>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="flex items-center gap-2">
              <label htmlFor="datePicker" className="text-sm text-muted-foreground whitespace-nowrap">
                Focus Date:
              </label>
              <input
                id="datePicker"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-background border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="daysSelector" className="text-sm text-muted-foreground whitespace-nowrap">
                Custom Window:
              </label>
              <select
                id="daysSelector"
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
                className="bg-background border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="7">7 days</option>
                <option value="14">14 days</option>
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90">90 days</option>
              </select>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

