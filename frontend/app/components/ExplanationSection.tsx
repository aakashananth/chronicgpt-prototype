'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '../../lib/api'
import Card from './Card'
import Alert from './Alert'

export default function ExplanationSection() {
  const [explanation, setExplanation] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchExplanation = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getExplanation()
        setExplanation(data.explanation)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch explanation')
      } finally {
        setLoading(false)
      }
    }

    fetchExplanation()
  }, [])

  if (loading) {
    return (
      <Card>
        <p className="text-gray-400">Loading explanation...</p>
      </Card>
    )
  }

  if (error) {
    return <Alert type="error" message={error} />
  }

  if (!explanation) {
    return (
      <Card>
        <p className="text-gray-400">No explanation available yet. Run the pipeline first.</p>
      </Card>
    )
  }

  // Simple formatting for common section headings
  const formatExplanation = (text: string) => {
    // Split by common headings and format
    const sections = text.split(/(Summary|Implications|Suggestions|Reminder|Recommendations):/i)
    if (sections.length === 1) {
      return <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">{text}</p>
    }

    return (
      <div className="space-y-4">
        {sections.map((section, index) => {
          if (index === 0 && section.trim()) {
            return (
              <p key={index} className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                {section.trim()}
              </p>
            )
          }
          if (index % 2 === 1) {
            // This is a heading
            return (
              <div key={index}>
                <h3 className="text-lg font-semibold text-white mb-2">{section}</h3>
                {sections[index + 1] && (
                  <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {sections[index + 1].trim()}
                  </p>
                )}
              </div>
            )
          }
          return null
        })}
      </div>
    )
  }

  return (
    <Card>
      <h2 className="text-xl font-semibold mb-4">AI Explanation</h2>
      <div className="max-h-96 overflow-y-auto">{formatExplanation(explanation)}</div>
    </Card>
  )
}

