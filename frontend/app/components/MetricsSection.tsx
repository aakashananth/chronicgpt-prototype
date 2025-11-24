'use client'

import { useEffect, useState } from 'react'
import { apiClient, MetricsResponse } from '@/lib/api'
import Card from './Card'
import Alert from './Alert'

export default function MetricsSection() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getMetrics()
        setMetrics(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <Card>
        <p className="text-gray-400">Loading metrics...</p>
      </Card>
    )
  }

  if (error) {
    return <Alert type="error" message={error} />
  }

  if (!metrics) {
    return (
      <Card>
        <p className="text-gray-400">No metrics data available yet. Run the pipeline first.</p>
      </Card>
    )
  }

  // The metrics response can be a summary object or contain actual metric values
  const metricValues = metrics as any

  // Check if we have individual metric values or just summary
  const hasIndividualMetrics =
    metricValues.hrv !== undefined ||
    metricValues.resting_hr !== undefined ||
    metricValues.sleep_score !== undefined ||
    metricValues.steps !== undefined

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-xl font-semibold mb-4">Metrics Summary</h2>
        {metrics.date_range && (
          <div className="mb-4 text-sm text-gray-400">
            Date Range: {metrics.date_range.start} to {metrics.date_range.end}
          </div>
        )}
        {hasIndividualMetrics ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {metricValues.hrv !== undefined && (
              <div className="bg-gray-800 rounded p-4">
                <div className="text-gray-400 text-sm mb-1">HRV</div>
                <div className="text-2xl font-bold text-white">{metricValues.hrv}</div>
              </div>
            )}
            {metricValues.resting_hr !== undefined && (
              <div className="bg-gray-800 rounded p-4">
                <div className="text-gray-400 text-sm mb-1">Resting HR</div>
                <div className="text-2xl font-bold text-white">{metricValues.resting_hr}</div>
              </div>
            )}
            {metricValues.sleep_score !== undefined && (
              <div className="bg-gray-800 rounded p-4">
                <div className="text-gray-400 text-sm mb-1">Sleep Score</div>
                <div className="text-2xl font-bold text-white">{metricValues.sleep_score}</div>
              </div>
            )}
            {metricValues.steps !== undefined && metricValues.steps !== null && (
              <div className="bg-gray-800 rounded p-4">
                <div className="text-gray-400 text-sm mb-1">Steps</div>
                <div className="text-2xl font-bold text-white">
                  {typeof metricValues.steps === 'number' ? metricValues.steps.toLocaleString() : metricValues.steps}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-400 mb-4">
            <p>Metrics data is available. Available columns are listed below.</p>
          </div>
        )}
        {metrics.total_records && (
          <div className="mb-4 text-sm text-gray-400">
            Total Records: {metrics.total_records}
          </div>
        )}
        {metrics.columns && metrics.columns.length > 0 ? (
          <div className="mt-4">
            <div className="text-gray-400 text-sm mb-3 font-medium">Available Columns:</div>
            <div className="flex flex-wrap gap-2">
              {metrics.columns.map((col: string) => (
                <span
                  key={col}
                  className="bg-gray-800 px-3 py-1.5 rounded text-sm text-gray-300 border border-gray-700"
                >
                  {col}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-4 text-sm text-gray-500">
            <p>No column information available. Run the pipeline to generate metrics data.</p>
          </div>
        )}
      </Card>
    </div>
  )
}

