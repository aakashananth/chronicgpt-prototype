'use client'

import { useEffect, useState, useMemo } from 'react'
import { apiClient, Anomaly } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Filter, X } from 'lucide-react'
import { format, parseISO } from 'date-fns'

interface AnomaliesPanelProps {
  refreshKey?: number
}

export default function AnomaliesPanel({ refreshKey }: AnomaliesPanelProps) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(true)
  const [severityFilter, setSeverityFilter] = useState<number | null>(null)
  const [flagFilter, setFlagFilter] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getAnomalies()
        setAnomalies(data)
        setExpanded(data.length > 0)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch anomalies')
        console.error('Failed to fetch anomalies', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalies()
  }, [refreshKey])

  const getFlagBadges = (anomaly: Anomaly) => {
    const flags = []
    if (anomaly.low_hrv_flag) flags.push({ label: 'Low HRV', variant: 'destructive' as const, key: 'low_hrv' })
    if (anomaly.high_rhr_flag) flags.push({ label: 'High RHR', variant: 'destructive' as const, key: 'high_rhr' })
    if (anomaly.low_sleep_flag) flags.push({ label: 'Low Sleep', variant: 'warning' as const, key: 'low_sleep' })
    if (anomaly.low_steps_flag) flags.push({ label: 'Low Steps', variant: 'warning' as const, key: 'low_steps' })
    return flags
  }

  // Filter anomalies - must be called before any conditional returns
  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((anomaly) => {
      if (severityFilter !== null && (anomaly.anomaly_severity || 0) !== severityFilter) {
        return false
      }
      if (flagFilter) {
        const flags = getFlagBadges(anomaly)
        if (!flags.some(f => f.key === flagFilter)) {
          return false
        }
      }
      return true
    })
  }, [anomalies, severityFilter, flagFilter])

  const hasActiveFilters = severityFilter !== null || flagFilter !== null

  const clearFilters = () => {
    setSeverityFilter(null)
    setFlagFilter(null)
  }

  const getSeverityColor = (severity?: number) => {
    if (!severity) return 'secondary'
    if (severity >= 3) return 'destructive'
    if (severity === 2) return 'warning'
    return 'warning'
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse text-muted-foreground">Loading anomalies...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-destructive mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Retry
            </button>
          </div>
        </CardContent>
      </Card>
    )
  }


  return (
    <Card>
      <CardHeader
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-foreground" />
            <CardTitle>
              Recent Anomalies {filteredAnomalies.length > 0 && `(${filteredAnomalies.length}${hasActiveFilters ? ` of ${anomalies.length}` : ''})`}
            </CardTitle>
          </div>
          <span className="text-sm text-muted-foreground">
            {expanded ? '▼' : '▶'}
          </span>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent>
          {anomalies.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground text-lg mb-2">
                No anomalies detected
              </p>
              <p className="text-muted-foreground text-sm">
                Your health metrics look good!
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2 pb-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Filter by:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  <select
                    value={severityFilter === null ? '' : severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value === '' ? null : parseInt(e.target.value))}
                    className="bg-background border border-border rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">All Severities</option>
                    <option value="1">Severity 1</option>
                    <option value="2">Severity 2</option>
                    <option value="3">Severity 3+</option>
                  </select>
                  <select
                    value={flagFilter || ''}
                    onChange={(e) => setFlagFilter(e.target.value === '' ? null : e.target.value)}
                    className="bg-background border border-border rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="">All Flags</option>
                    <option value="low_hrv">Low HRV</option>
                    <option value="high_rhr">High RHR</option>
                    <option value="low_sleep">Low Sleep</option>
                    <option value="low_steps">Low Steps</option>
                  </select>
                  {hasActiveFilters && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearFilters}
                      className="h-7 px-2 text-xs"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Clear
                    </Button>
                  )}
                </div>
              </div>
              {filteredAnomalies.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No anomalies match the selected filters.</p>
                </div>
              ) : (
                filteredAnomalies.map((anomaly, index) => {
                const flags = getFlagBadges(anomaly)
                return (
                  <div
                    key={index}
                    className="border border-border rounded-lg p-4 hover:border-border/80 transition-colors"
                  >
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-3">
                      <div>
                        <h3 className="text-lg font-semibold mb-1">
                          {format(parseISO(anomaly.date), 'MMM d, yyyy')}
                        </h3>
                        {anomaly.anomaly_severity !== undefined && (
                          <Badge
                            variant={getSeverityColor(anomaly.anomaly_severity)}
                            className="mt-1"
                          >
                            Severity: {anomaly.anomaly_severity}
                          </Badge>
                        )}
                      </div>
                      {flags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2 md:mt-0">
                          {flags.map((flag, idx) => (
                            <Badge key={idx} variant={flag.variant}>
                              {flag.label}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                      {anomaly.hrv !== undefined && anomaly.hrv !== null && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">HRV</div>
                          <div className="text-lg font-medium">{anomaly.hrv}ms</div>
                        </div>
                      )}
                      {anomaly.resting_hr !== undefined && anomaly.resting_hr !== null && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Resting HR</div>
                          <div className="text-lg font-medium">{anomaly.resting_hr} bpm</div>
                        </div>
                      )}
                      {anomaly.sleep_score !== undefined && anomaly.sleep_score !== null && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Sleep Score</div>
                          <div className="text-lg font-medium">{anomaly.sleep_score}/100</div>
                        </div>
                      )}
                      {anomaly.steps !== undefined && anomaly.steps !== null && (
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Steps</div>
                          <div className="text-lg font-medium">
                            {typeof anomaly.steps === 'number'
                              ? anomaly.steps.toLocaleString()
                              : anomaly.steps}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )
              }))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

