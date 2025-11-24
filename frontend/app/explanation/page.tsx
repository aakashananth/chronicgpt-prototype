'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiClient } from '@/lib/api'

export default function ExplanationPage() {
  const [explanation, setExplanation] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchExplanation = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getExplanation()
        setExplanation(data.explanation)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch explanation')
      } finally {
        setLoading(false)
      }
    }

    fetchExplanation()
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

          <h1 className="text-3xl md:text-4xl font-bold mb-8">AI Explanation</h1>

          {loading && (
            <div className="bg-gray-900 rounded-lg p-8 shadow-lg">
              <p className="text-gray-400">Loading explanation...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-6 shadow-lg">
              <p className="text-red-400">Error: {error}</p>
            </div>
          )}

          {explanation && !loading && (
            <div className="bg-gray-900 rounded-lg p-6 md:p-8 shadow-lg">
              <div className="prose prose-invert max-w-none">
                <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                  {explanation}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

