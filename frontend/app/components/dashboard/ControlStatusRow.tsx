'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Play, RefreshCw } from 'lucide-react'
import { apiClient, PipelineRunResponse, MetricsResponse } from '@/lib/api'
import { format } from 'date-fns'
import { toast } from '@/components/ui/toast'

interface ControlStatusRowProps {
  onPipelineRun?: (result: PipelineRunResponse) => void
}

export default function ControlStatusRow({ onPipelineRun }: ControlStatusRowProps) {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<'healthy' | 'no_data' | 'error' | 'loading'>('loading')
  const [dataUpTo, setDataUpTo] = useState<string | null>(null)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      setStatus('loading')
      const metrics = await apiClient.getMetrics()
      if (metrics && metrics.date_range?.end) {
        setDataUpTo(metrics.date_range.end)
        setStatus('healthy')
      } else {
        setStatus('no_data')
      }
    } catch (err) {
      setStatus('error')
    }
  }

  const handleRunPipeline = async () => {
    try {
      setLoading(true)
      setStatus('loading')
      const result = await apiClient.runPipeline(14)
      if (onPipelineRun) {
        onPipelineRun(result)
      }
      // Update last updated timestamp
      const now = new Date().toISOString()
      localStorage.setItem('lastDataUpdate', now)
      localStorage.setItem('lastPipelineRun', now)
      window.dispatchEvent(new Event('dataUpdated'))
      window.dispatchEvent(new Event('pipelineRun'))
      // Refresh status
      await loadStatus()
      toast(`Pipeline completed successfully! Processed ${result.metrics_count} metrics.`, 'success')
    } catch (error) {
      setStatus('error')
      const errorMessage = error instanceof Error ? error.message : 'Failed to run pipeline'
      toast(errorMessage, 'error')
      console.error('Failed to run pipeline:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = () => {
    switch (status) {
      case 'healthy':
        return <Badge variant="success">Healthy</Badge>
      case 'no_data':
        return <Badge variant="secondary">No data</Badge>
      case 'error':
        return <Badge variant="destructive">Error</Badge>
      default:
        return <Badge variant="secondary">Loading...</Badge>
    }
  }

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 bg-card border border-border rounded-lg">
      <div className="flex items-center gap-4">
        <Button
          onClick={handleRunPipeline}
          disabled={loading}
          size="default"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Run Daily Pipeline
            </>
          )}
        </Button>
      </div>
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        {dataUpTo && (
          <div className="text-sm text-muted-foreground">
            Data up to: <span className="text-foreground font-medium">{format(new Date(dataUpTo), 'MMM d, yyyy')}</span>
          </div>
        )}
        {getStatusBadge()}
      </div>
    </div>
  )
}

