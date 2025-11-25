'use client'

import { useEffect, useState } from 'react'
import { apiClient, Anomaly } from '@/lib/api'
import Card from './Card'
import Alert from './Alert'

export default function AnomaliesSection() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getAnomalies()
        setAnomalies(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch anomalies')
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalies()
  }, [])

  if (loading) {
    return (
      <Card>
        <p className="text-gray-400">Loading anomalies...</p>
      </Card>
    )
  }

  if (error) {
    return <Alert type="error" message={error} />
  }

  if (anomalies.length === 0) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-400 text-lg mb-2">No anomalies detected</p>
          <p className="text-gray-500 text-sm">Your health metrics look good!</p>
        </div>
      </Card>
    )
  }

  const getSeverityColor = (severity?: number) => {
    if (!severity) return 'bg-gray-700'
    if (severity >= 3) return 'bg-red-900/30 text-red-400'
    if (severity === 2) return 'bg-yellow-900/30 text-yellow-400'
    return 'bg-orange-900/30 text-orange-400'
  }

  const getFlagBadges = (anomaly: Anomaly) => {
    const flags = []
    if (anomaly.low_hrv_flag) flags.push({ label: 'Low HRV', color: 'bg-red-900/30 text-red-400' })
    if (anomaly.high_rhr_flag) flags.push({ label: 'High RHR', color: 'bg-red-900/30 text-red-400' })
    if (anomaly.low_sleep_flag) flags.push({ label: 'Low Sleep', color: 'bg-yellow-900/30 text-yellow-400' })
    if (anomaly.low_steps_flag) flags.push({ label: 'Low Steps', color: 'bg-orange-900/30 text-orange-400' })
    return flags
  }

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-xl font-semibold mb-4">
          Recent Anomalies ({anomalies.length})
        </h2>
      </Card>
      {anomalies.map((anomaly, index) => {
        const flags = getFlagBadges(anomaly)
        return (
          <Card key={index}>
            <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-4">
              <h3 className="text-lg font-semibold mb-2">{anomaly.date}</h3>
              {anomaly.anomaly_severity !== undefined && (
                <span
                  className={`px-3 py-1 rounded text-sm font-medium ${getSeverityColor(
                    anomaly.anomaly_severity
                  )}`}
                >
                  Severity: {anomaly.anomaly_severity}
                </span>
              )}
            </div>
            {flags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {flags.map((flag, idx) => (
                  <span
                    key={idx}
                    className={`px-2 py-1 rounded text-xs ${flag.color}`}
                  >
                    {flag.label}
                  </span>
                ))}
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {anomaly.hrv !== undefined && anomaly.hrv !== null && (
                <div>
                  <div className="text-gray-400 text-sm">HRV</div>
                  <div className="text-white font-medium">{anomaly.hrv}</div>
                </div>
              )}
              {anomaly.resting_hr !== undefined && anomaly.resting_hr !== null && (
                <div>
                  <div className="text-gray-400 text-sm">Resting HR</div>
                  <div className="text-white font-medium">{anomaly.resting_hr}</div>
                </div>
              )}
              {anomaly.sleep_score !== undefined && anomaly.sleep_score !== null && (
                <div>
                  <div className="text-gray-400 text-sm">Sleep Score</div>
                  <div className="text-white font-medium">{anomaly.sleep_score}</div>
                </div>
              )}
              {anomaly.steps !== undefined && anomaly.steps !== null && (
                <div>
                  <div className="text-gray-400 text-sm">Steps</div>
                  <div className="text-white font-medium">
                    {typeof anomaly.steps === 'number' ? anomaly.steps.toLocaleString() : anomaly.steps}
                  </div>
                </div>
              )}
            </div>
          </Card>
        )
      })}
    </div>
  )
}

