'use client'

import { useState } from 'react'
import { apiClient, PipelineRunResponse } from '../../lib/api'
import Card from './Card'
import Alert from './Alert'

interface OverviewSectionProps {
  onPipelineRun: (result: PipelineRunResponse) => void
}

export default function OverviewSection({ onPipelineRun }: OverviewSectionProps) {
  const [loading, setLoading] = useState(false)
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [lastRun, setLastRun] = useState<PipelineRunResponse | null>(null)

  const handleRunPipeline = async () => {
    try {
      setLoading(true)
      setAlert(null)
      const result = await apiClient.runPipeline(14)
      setLastRun(result)
      setAlert({
        type: 'success',
        message: `Pipeline completed successfully! Found ${result.recent_anomalies.length} anomalies. Blob path: ${result.blob_path || result.parquet_path}`,
      })
      onPipelineRun(result)
    } catch (error) {
      setAlert({
        type: 'error',
        message: error instanceof Error ? error.message : 'Failed to run pipeline',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-xl font-semibold mb-4">Run Daily Pipeline</h2>
        <button
          onClick={handleRunPipeline}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium px-6 py-3 rounded transition-colors"
        >
          {loading ? (
            <span className="flex items-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Running pipeline...
            </span>
          ) : (
            'Run Daily Pipeline'
          )}
        </button>
      </Card>

      {alert && (
        <Alert
          type={alert.type}
          message={alert.message}
          onClose={() => setAlert(null)}
        />
      )}

      {lastRun && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Last Pipeline Run Status</h2>
          <div className="space-y-2">
            <div>
              <span className="text-gray-400">Status:</span>
              <span className="ml-2 text-green-400 font-medium">{lastRun.status}</span>
            </div>
            <div>
              <span className="text-gray-400">Anomalies Found:</span>
              <span className="ml-2 text-white font-medium">
                {lastRun.recent_anomalies.length}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Metrics Processed:</span>
              <span className="ml-2 text-white font-medium">{lastRun.metrics_count}</span>
            </div>
            {lastRun.blob_path && (
              <div>
                <span className="text-gray-400">Blob Path:</span>
                <span className="ml-2 text-white text-sm break-all">{lastRun.blob_path}</span>
              </div>
            )}
            {!lastRun.blob_path && lastRun.parquet_path && (
              <div>
                <span className="text-gray-400">Parquet Path:</span>
                <span className="ml-2 text-white text-sm break-all">
                  {lastRun.parquet_path}
                </span>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}

