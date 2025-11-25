'use client'

import { useEffect, useState } from 'react'
import { apiClient, Anomaly } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle } from 'lucide-react'
import { format, parseISO } from 'date-fns'

export default function AnomaliesPanel() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getAnomalies()
        setAnomalies(data)
        setExpanded(data.length > 0)
      } catch (err) {
        console.error('Failed to fetch anomalies:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalies()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse">Loading anomalies...</div>
        </CardContent>
      </Card>
    )
  }

  const getSeverityColor = (severity?: number) => {
    if (!severity) return 'secondary'
    if (severity >= 3) return 'destructive'
    if (severity === 2) return 'warning'
    return 'warning'
  }

  const getFlagBadges = (anomaly: Anomaly) => {
    const flags = []
    if (anomaly.low_hrv_flag) flags.push({ label: 'Low HRV', variant: 'destructive' as const })
    if (anomaly.high_rhr_flag) flags.push({ label: 'High RHR', variant: 'destructive' as const })
    if (anomaly.low_sleep_flag) flags.push({ label: 'Low Sleep', variant: 'warning' as const })
    if (anomaly.low_steps_flag) flags.push({ label: 'Low Steps', variant: 'warning' as const })
    return flags
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
              Recent Anomalies {anomalies.length > 0 && `(${anomalies.length})`}
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
              {anomalies.map((anomaly, index) => {
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
              })}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

