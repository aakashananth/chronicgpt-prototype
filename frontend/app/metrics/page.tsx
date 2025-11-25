'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiClient, MetricsResponse } from '../../lib/api'

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getMetrics()
        setMetrics(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

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

          <h1 className="text-3xl md:text-4xl font-bold mb-8">Metrics</h1>

          {loading && (
            <div className="bg-gray-900 rounded-lg p-8 shadow-lg">
              <p className="text-gray-400">Loading metrics...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 shadow-lg">
              <p className="text-red-400">Error: {error}</p>
            </div>
          )}

          {metrics && !loading && (
            <div className="bg-gray-900 rounded-lg p-6 md:p-8 shadow-lg">
              <h2 className="text-xl font-semibold mb-4">Metrics Summary</h2>
              <div className="space-y-4">
                {metrics.total_records && (
                  <div>
                    <span className="text-gray-400">Total Records:</span>
                    <span className="ml-2 text-white font-medium">
                      {metrics.total_records}
                    </span>
                  </div>
                )}
                {metrics.date_range && (
                  <div>
                    <span className="text-gray-400">Date Range:</span>
                    <span className="ml-2 text-white font-medium">
                      {metrics.date_range.start} to {metrics.date_range.end}
                    </span>
                  </div>
                )}
                {metrics.columns && (
                  <div>
                    <span className="text-gray-400">Available Columns:</span>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {metrics.columns.map((col) => (
                        <span
                          key={col}
                          className="bg-gray-800 px-3 py-1 rounded text-sm"
                        >
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

