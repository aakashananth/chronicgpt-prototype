'use client'

import { useState } from 'react'
import Link from 'next/link'
import { apiClient, PipelineRunResponse } from '../../lib/api'

export default function RunPipelinePage() {
  const [daysBack, setDaysBack] = useState(14)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PipelineRunResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.runPipeline(daysBack)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run pipeline')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8 md:py-16">
        <div className="max-w-4xl mx-auto">
          <Link
            href="/"
            className="text-gray-400 hover:text-white mb-6 inline-block"
          >
            ← Back to Home
          </Link>

          <h1 className="text-3xl md:text-4xl font-bold mb-8">
            Run Pipeline
          </h1>

          <div className="bg-gray-900 rounded-lg p-6 md:p-8 shadow-lg mb-6">
            <div className="mb-6">
              <label
                htmlFor="daysBack"
                className="block text-sm font-medium mb-2"
              >
                Days Back
              </label>
              <input
                id="daysBack"
                type="number"
                min="1"
                max="30"
                value={daysBack}
                onChange={(e) => setDaysBack(parseInt(e.target.value) || 14)}
                className="w-full md:w-48 bg-gray-800 border border-gray-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleRun}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium px-6 py-2 rounded transition-colors"
            >
              {loading ? 'Running...' : 'Run Pipeline'}
            </button>
          </div>

          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 shadow-lg mb-6">
              <p className="text-red-400">Error: {error}</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="bg-gray-900 rounded-lg p-6 shadow-lg">
                <h2 className="text-xl font-semibold mb-4">Pipeline Results</h2>
                <div className="space-y-2">
                  <p>
                    <span className="text-gray-400">Status:</span>
                    <span className="ml-2 text-green-400">{result.status}</span>
                  </p>
                  <p>
                    <span className="text-gray-400">Metrics Count:</span>
                    <span className="ml-2 text-white">{result.metrics_count}</span>
                  </p>
                  {result.parquet_path && (
                    <p>
                      <span className="text-gray-400">Parquet Path:</span>
                      <span className="ml-2 text-white text-sm">
                        {result.parquet_path}
                      </span>
                    </p>
                  )}
                  {result.blob_path && (
                    <p>
                      <span className="text-gray-400">Blob Path:</span>
                      <span className="ml-2 text-white text-sm">
                        {result.blob_path}
                      </span>
                    </p>
                  )}
                </div>
              </div>

              {result.recent_anomalies.length > 0 && (
                <div className="bg-gray-900 rounded-lg p-6 shadow-lg">
                  <h2 className="text-xl font-semibold mb-4">
                    Recent Anomalies ({result.recent_anomalies.length})
                  </h2>
                  <div className="space-y-3">
                    {result.recent_anomalies.map((anomaly, index) => (
                      <div
                        key={index}
                        className="bg-gray-800 rounded p-4"
                      >
                        <p className="font-medium mb-2">{anomaly.date}</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                          {anomaly.hrv !== undefined && (
                            <span className="text-gray-400">
                              HRV: <span className="text-white">{anomaly.hrv}</span>
                            </span>
                          )}
                          {anomaly.resting_hr !== undefined && (
                            <span className="text-gray-400">
                              RHR: <span className="text-white">{anomaly.resting_hr}</span>
                            </span>
                          )}
                          {anomaly.sleep_score !== undefined && (
                            <span className="text-gray-400">
                              Sleep: <span className="text-white">{anomaly.sleep_score}</span>
                            </span>
                          )}
                          {anomaly.steps !== undefined && (
                            <span className="text-gray-400">
                              Steps: <span className="text-white">{anomaly.steps}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.explanation && (
                <div className="bg-gray-900 rounded-lg p-6 shadow-lg">
                  <h2 className="text-xl font-semibold mb-4">Explanation</h2>
                  <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {result.explanation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

