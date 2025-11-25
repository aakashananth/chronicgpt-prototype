'use client'

import { useEffect, useState } from 'react'
import { Clock, AlertCircle } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { apiClient } from '@/lib/api'

export default function HeaderBar() {
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [lastIngestionRun, setLastIngestionRun] = useState<Date | null>(null)
  const [hasData, setHasData] = useState<boolean>(true)

  useEffect(() => {
    // Try to get last updated from localStorage or set to now
    const updateLastUpdated = () => {
      const stored = localStorage.getItem('lastDataUpdate')
      if (stored) {
        setLastUpdated(new Date(stored))
      } else {
        setLastUpdated(new Date())
      }
    }

    updateLastUpdated()

    // Listen for storage events (when other tabs update)
    window.addEventListener('storage', updateLastUpdated)
    
    // Also listen for custom event (when same tab updates)
    window.addEventListener('dataUpdated', updateLastUpdated)

    return () => {
      window.removeEventListener('storage', updateLastUpdated)
      window.removeEventListener('dataUpdated', updateLastUpdated)
    }
  }, [])

  useEffect(() => {
    const fetchLastIngestionTime = async () => {
      try {
        // First check localStorage for pipeline run timestamp
        const pipelineRunTime = localStorage.getItem('lastPipelineRun')
        if (pipelineRunTime) {
          setLastIngestionRun(new Date(pipelineRunTime))
          setHasData(true)
          return
        }

        // Otherwise, try to get latest date from metrics history
        const history = await apiClient.getMetricsHistory({ days: 1 })
        if (history && history.total_records > 0 && history.date_range?.end) {
          // Use the latest date as a proxy - assume it was ingested today
          const latestDate = new Date(history.date_range.end)
          // If the latest date is today, use current time; otherwise use end of that day
          const now = new Date()
          if (latestDate.toDateString() === now.toDateString()) {
            setLastIngestionRun(now)
          } else {
            // Set to end of that day
            latestDate.setHours(23, 59, 59, 999)
            setLastIngestionRun(latestDate)
          }
          setHasData(true)
        } else {
          setHasData(false)
        }
      } catch (err) {
        // If we can't fetch, check localStorage for last pipeline run
        const pipelineRunTime = localStorage.getItem('lastPipelineRun')
        if (pipelineRunTime) {
          setLastIngestionRun(new Date(pipelineRunTime))
          setHasData(true)
        } else {
          setHasData(false)
        }
      }
    }

    fetchLastIngestionTime()

    // Listen for pipeline run events
    const handlePipelineRun = () => {
      const pipelineRunTime = localStorage.getItem('lastPipelineRun')
      if (pipelineRunTime) {
        setLastIngestionRun(new Date(pipelineRunTime))
        setHasData(true)
      }
    }

    window.addEventListener('pipelineRun', handlePipelineRun)
    window.addEventListener('dataUpdated', fetchLastIngestionTime)

    return () => {
      window.removeEventListener('pipelineRun', handlePipelineRun)
      window.removeEventListener('dataUpdated', fetchLastIngestionTime)
    }
  }, [])

  const getIngestionStatus = () => {
    if (!hasData || !lastIngestionRun) {
      return { text: 'never', icon: AlertCircle, className: 'text-muted-foreground' }
    }

    const now = new Date()
    const diffMs = now.getTime() - lastIngestionRun.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) {
      return { text: 'just now', icon: Clock, className: 'text-success' }
    } else if (diffMins < 60) {
      return { text: `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`, icon: Clock, className: 'text-foreground' }
    } else {
      const text = formatDistanceToNow(lastIngestionRun, { addSuffix: true })
      return { text, icon: Clock, className: 'text-foreground' }
    }
  }

  const ingestionStatus = getIngestionStatus()
  const StatusIcon = ingestionStatus.icon

  return (
    <header className="border-b border-border bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              Health Metrics LLM Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Ultrahuman + Azure OpenAI prototype
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 text-sm">
            {lastUpdated && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>
                  Last updated: {format(lastUpdated, 'MMM d, yyyy h:mm a')}
                </span>
              </div>
            )}
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md bg-card border border-border ${ingestionStatus.className}`}>
              <StatusIcon className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">
                Last ingestion run: {ingestionStatus.text}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

