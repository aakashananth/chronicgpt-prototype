'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsHistoryResponse } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import MetricCard from './MetricCard'
import { Activity, Heart, Moon, Footprints, Calendar } from 'lucide-react'
import { format, parseISO } from 'date-fns'

interface MetricCardsRowProps {
  refreshKey?: number
}

export default function MetricCardsRow({ refreshKey }: MetricCardsRowProps) {
  const [history, setHistory] = useState<MetricsHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  useEffect(() => {
    const fetchTodayMetrics = async () => {
      try {
        setLoading(true)
        setError(null)
        // Get last 7 days to calculate trends
        const data = await apiClient.getMetricsHistory({ days: 7 })
        setHistory(data)
        // Reset selected date if it's no longer in the available dates
        if (selectedDate && data.dates && !data.dates.includes(selectedDate)) {
          setSelectedDate(null)
        }
      } catch (err) {
        let errorMessage = 'Failed to fetch metrics'
        if (err instanceof Error) {
          errorMessage = err.message
          // Check if it's a patient_id configuration error
          if (err.message.includes('patient_id') || err.message.includes('not configured')) {
            errorMessage = 'Backend configuration error: patient_id not set. Please configure ULTRAHUMAN_PATIENT_ID or ULTRAHUMAN_EMAIL in Azure App Service settings.'
          } else if (err.message.includes('400')) {
            errorMessage = 'Bad request: Check backend configuration and ensure patient_id is set.'
          }
        }
        setError(errorMessage)
        console.error('Failed to fetch metrics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchTodayMetrics()
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  // Find the date to show - use selectedDate if set, otherwise prefer today, otherwise most recent date with any data
  const todayStr = format(new Date(), 'yyyy-MM-dd')
  
  // Determine which date to display
  let displayDateIndex = -1
  let displayDate = todayStr
  let isToday = false
  let isSelected = false

  // If user selected a date, use that
  if (selectedDate) {
    const selectedIndex = history.dates.findIndex(d => d === selectedDate)
    if (selectedIndex >= 0) {
      displayDateIndex = selectedIndex
      displayDate = selectedDate
      isSelected = true
      isToday = selectedDate === todayStr
    }
  }

  // If no selection or selection not found, try today first
  if (displayDateIndex === -1) {
    const todayIndex = history.dates.findIndex(d => d === todayStr)
    if (todayIndex >= 0) {
      // Check if today has at least one non-null value
      const hasData = 
        (history.hrv?.[todayIndex] !== null && history.hrv?.[todayIndex] !== undefined) ||
        (history.resting_hr?.[todayIndex] !== null && history.resting_hr?.[todayIndex] !== undefined) ||
        (history.sleep_score?.[todayIndex] !== null && history.sleep_score?.[todayIndex] !== undefined) ||
        (history.steps?.[todayIndex] !== null && history.steps?.[todayIndex] !== undefined)
      
      if (hasData) {
        displayDateIndex = todayIndex
        displayDate = todayStr
        isToday = true
      }
    }
  }

  // If today doesn't have data, find the most recent date with any data
  if (displayDateIndex === -1) {
    for (let i = history.dates.length - 1; i >= 0; i--) {
      const hasData = 
        (history.hrv?.[i] !== null && history.hrv?.[i] !== undefined) ||
        (history.resting_hr?.[i] !== null && history.resting_hr?.[i] !== undefined) ||
        (history.sleep_score?.[i] !== null && history.sleep_score?.[i] !== undefined) ||
        (history.steps?.[i] !== null && history.steps?.[i] !== undefined)
      
      if (hasData) {
        displayDateIndex = i
        displayDate = history.dates[i]
        break
      }
    }
  }

  // Get values for the selected date
  const todayHrv = displayDateIndex >= 0 ? history.hrv?.[displayDateIndex] ?? null : null
  const todayRhr = displayDateIndex >= 0 ? history.resting_hr?.[displayDateIndex] ?? null : null
  const todaySleep = displayDateIndex >= 0 ? history.sleep_score?.[displayDateIndex] ?? null : null
  const todaySteps = displayDateIndex >= 0 ? history.steps?.[displayDateIndex] ?? null : null

  // Format the display date
  const displayDateFormatted = displayDateIndex >= 0 
    ? format(parseISO(displayDate), 'MMM d, yyyy')
    : 'No data'

  // Calculate trends for the selected date (compare selected date value with average of previous 6 days)
  const calculateTrend = (values: (number | null)[], currentIndex: number): number | null => {
    if (currentIndex < 1) return null
    const current = values[currentIndex]
    if (current === null || current === undefined || isNaN(current)) return null
    
    // Get previous 6 days (or as many as available) up to but not including currentIndex
    const start = Math.max(0, currentIndex - 6)
    const previous = values.slice(start, currentIndex).filter((v): v is number => 
      v !== null && v !== undefined && !isNaN(v)
    )
    
    if (previous.length === 0) return null
    const avg = previous.reduce((a, b) => a + b, 0) / previous.length
    if (avg === 0) return null
    return ((current - avg) / avg) * 100
  }
  
  // Calculate trends for the selected date (displayDateIndex)
  const hrvTrend = displayDateIndex >= 0 ? calculateTrend(history.hrv || [], displayDateIndex) : null
  const rhrTrend = displayDateIndex >= 0 ? calculateTrend(history.resting_hr || [], displayDateIndex) : null
  const sleepTrend = displayDateIndex >= 0 ? calculateTrend(history.sleep_score || [], displayDateIndex) : null
  const stepsTrend = displayDateIndex >= 0 ? calculateTrend(history.steps || [], displayDateIndex) : null

  // Get last 7 values for sparklines up to the selected date
  const getSparklineData = (values: (number | null)[], currentIndex: number): number[] => {
    if (currentIndex < 0) return []
    const start = Math.max(0, currentIndex - 6)
    return values
      .slice(start, currentIndex + 1)
      .filter((v): v is number => v !== null && v !== undefined && !isNaN(v))
  }

  // Get available dates for the date picker (only dates with data)
  const availableDates = history.dates.filter((date, index) => {
    return (
      (history.hrv?.[index] !== null && history.hrv?.[index] !== undefined) ||
      (history.resting_hr?.[index] !== null && history.resting_hr?.[index] !== undefined) ||
      (history.sleep_score?.[index] !== null && history.sleep_score?.[index] !== undefined) ||
      (history.steps?.[index] !== null && history.steps?.[index] !== undefined)
    )
  })

  // Determine the section title based on what's being shown
  const sectionTitle = isToday && !isSelected 
    ? "Today's Snapshot"
    : isSelected
    ? `Snapshot for ${displayDateFormatted}`
    : "Most Recent Snapshot"

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-4">
        <h2 className="text-xl font-semibold text-foreground">{sectionTitle}</h2>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="text-sm text-muted-foreground">
            {isToday && !isSelected ? (
              <span>Showing: <span className="text-foreground font-medium">Today ({displayDateFormatted})</span></span>
            ) : isSelected ? (
              <span>Showing: <span className="text-foreground font-medium">{displayDateFormatted}</span></span>
            ) : (
              <span>Showing: <span className="text-foreground font-medium">{displayDateFormatted}</span> <span className="text-xs">(most recent data)</span></span>
            )}
          </div>
          {availableDates.length > 0 && (
            <div className="flex items-center gap-2.5">
              <label htmlFor="snapshot-date-picker" className="text-xs text-muted-foreground flex items-center gap-1.5 whitespace-nowrap">
                <Calendar className="h-3.5 w-3.5" />
                <span>Select date:</span>
              </label>
              <input
                id="snapshot-date-picker"
                type="date"
                value={selectedDate || displayDate}
                onChange={(e) => setSelectedDate(e.target.value || null)}
                min={availableDates[0]}
                max={availableDates[availableDates.length - 1]}
                className="bg-background border border-border rounded-md px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-100 [&::-webkit-calendar-picker-indicator]:invert [&::-webkit-calendar-picker-indicator]:brightness-0 [&::-webkit-calendar-picker-indicator]:contrast-100"
              />
              {selectedDate && (
                <button
                  onClick={() => setSelectedDate(null)}
                  className="text-xs text-muted-foreground hover:text-foreground underline whitespace-nowrap"
                >
                  Reset
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="HRV"
          value={todayHrv}
          trend={hrvTrend}
          icon={<Activity className="h-5 w-5" />}
          formatValue={(val) => `${val.toFixed(0)}ms`}
          sparklineData={displayDateIndex >= 0 ? getSparklineData(history.hrv || [], displayDateIndex) : undefined}
        />
        <MetricCard
          title="Resting HR"
          value={todayRhr}
          trend={rhrTrend}
          invertTrend={true}
          icon={<Heart className="h-5 w-5" />}
          formatValue={(val) => `${val.toFixed(0)} bpm`}
          sparklineData={displayDateIndex >= 0 ? getSparklineData(history.resting_hr || [], displayDateIndex) : undefined}
        />
        <MetricCard
          title="Sleep Score"
          value={todaySleep}
          trend={sleepTrend}
          icon={<Moon className="h-5 w-5" />}
          formatValue={(val) => `${val.toFixed(0)}/100`}
          sparklineData={displayDateIndex >= 0 ? getSparklineData(history.sleep_score || [], displayDateIndex) : undefined}
        />
        <MetricCard
          title="Steps"
          value={todaySteps}
          trend={stepsTrend}
          icon={<Footprints className="h-5 w-5" />}
          formatValue={(val) => val.toLocaleString()}
          sparklineData={displayDateIndex >= 0 ? getSparklineData(history.steps || [], displayDateIndex) : undefined}
        />
      </div>
    </div>
  )
}

