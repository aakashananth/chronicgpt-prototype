'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiClient, Anomaly } from '@/lib/api'

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getAnomalies()
        setAnomalies(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch anomalies')
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalies()
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

          <h1 className="text-3xl md:text-4xl font-bold mb-8">Anomalies</h1>

          {loading && (
            <div className="bg-gray-900 rounded-lg p-8 shadow-lg">
              <p className="text-gray-400">Loading anomalies...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 shadow-lg">
              <p className="text-red-400">Error: {error}</p>
            </div>
          )}

          {!loading && !error && anomalies.length === 0 && (
            <div className="bg-gray-900 rounded-lg p-8 shadow-lg">
              <p className="text-gray-400">No anomalies detected.</p>
            </div>
          )}

          {anomalies.length > 0 && (
            <div className="space-y-4">
              {anomalies.map((anomaly, index) => (
                <div
                  key={index}
                  className="bg-gray-900 rounded-lg p-6 shadow-lg"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h2 className="text-lg font-semibold">
                      {anomaly.date}
                    </h2>
                    {anomaly.anomaly_severity !== undefined && (
                      <span className="bg-red-900/30 text-red-400 px-3 py-1 rounded text-sm">
                        Severity: {anomaly.anomaly_severity}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {anomaly.hrv !== undefined && (
                      <div>
                        <span className="text-gray-400 text-sm">HRV:</span>
                        <p className="text-white font-medium">{anomaly.hrv}</p>
                      </div>
                    )}
                    {anomaly.resting_hr !== undefined && (
                      <div>
                        <span className="text-gray-400 text-sm">Resting HR:</span>
                        <p className="text-white font-medium">
                          {anomaly.resting_hr}
                        </p>
                      </div>
                    )}
                    {anomaly.sleep_score !== undefined && (
                      <div>
                        <span className="text-gray-400 text-sm">Sleep Score:</span>
                        <p className="text-white font-medium">
                          {anomaly.sleep_score}
                        </p>
                      </div>
                    )}
                    {anomaly.steps !== undefined && (
                      <div>
                        <span className="text-gray-400 text-sm">Steps:</span>
                        <p className="text-white font-medium">{anomaly.steps}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

