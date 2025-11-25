'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Play, RefreshCw } from 'lucide-react'
import { apiClient, PipelineRunResponse } from '@/lib/api'

interface ControlsBarProps {
  onPipelineRun?: (result: PipelineRunResponse) => void
  onRefresh?: () => void
  onTimeRangeChange?: (range: number) => void
  onDateChange?: (date: string) => void
}

export default function ControlsBar({
  onPipelineRun,
  onRefresh,
  onTimeRangeChange,
  onDateChange,
}: ControlsBarProps) {
  const [loading, setLoading] = useState(false)
  const [timeRange, setTimeRange] = useState('7')
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split('T')[0]
  )

  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value)
    if (onTimeRangeChange) {
      onTimeRangeChange(parseInt(value))
    }
  }

  const handleDateChange = (value: string) => {
    setSelectedDate(value)
    if (onDateChange) {
      onDateChange(value)
    }
  }

  const handleRunPipeline = async () => {
    try {
      setLoading(true)
      const result = await apiClient.runPipeline(parseInt(timeRange))
      if (onPipelineRun) {
        onPipelineRun(result)
      }
      // Update last updated timestamp
      localStorage.setItem('lastDataUpdate', new Date().toISOString())
      // Trigger refresh
      if (onRefresh) {
        onRefresh()
      }
    } catch (error) {
      console.error('Failed to run pipeline:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh()
    }
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            <div className="flex items-center gap-2">
              <label htmlFor="timeRange" className="text-sm text-muted-foreground whitespace-nowrap">
                Time Range:
              </label>
              <select
                id="timeRange"
                value={timeRange}
                onChange={(e) => handleTimeRangeChange(e.target.value)}
                className="bg-background border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="7">Last 7 days</option>
                <option value="14">Last 14 days</option>
                <option value="30">Last 30 days</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="datePicker" className="text-sm text-muted-foreground whitespace-nowrap">
                Date:
              </label>
              <input
                id="datePicker"
                type="date"
                value={selectedDate}
                onChange={(e) => handleDateChange(e.target.value)}
                className="bg-background border border-border rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleRunPipeline}
              disabled={loading}
              size="sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Pipeline
                </>
              )}
            </Button>
            <Button
              onClick={handleRefresh}
              variant="outline"
              size="sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

