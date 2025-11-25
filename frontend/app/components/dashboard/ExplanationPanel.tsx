'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bot, Copy, Check, RefreshCw } from 'lucide-react'

interface ExplanationPanelProps {
  refreshKey?: number
}

export default function ExplanationPanel({ refreshKey }: ExplanationPanelProps) {
  const [explanation, setExplanation] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const fetchExplanation = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiClient.getExplanation()
        setExplanation(data.explanation)
        setExpanded(!!data.explanation)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch explanation')
        console.error('Failed to fetch explanation:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchExplanation()
  }, [refreshKey])

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(explanation)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const formatExplanation = (text: string) => {
    const sections = text.split(/(Summary|Implications|Suggestions|Reminder|Recommendations|Lifestyle Adjustments):/i)
    if (sections.length === 1) {
      return <p className="text-card-foreground/90 whitespace-pre-wrap leading-relaxed">{text}</p>
    }

    return (
      <div className="space-y-4">
        {sections.map((section, index) => {
          if (index === 0 && section.trim()) {
            return (
              <p
                key={index}
                className="text-card-foreground/90 whitespace-pre-wrap leading-relaxed"
              >
                {section.trim()}
              </p>
            )
          }
          if (index % 2 === 1) {
            return (
              <div key={index}>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {section}
                </h3>
                {sections[index + 1] && (
                  <p className="text-card-foreground/90 whitespace-pre-wrap leading-relaxed">
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

  const handleRefresh = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getExplanation()
      setExplanation(data.explanation)
      setExpanded(!!data.explanation)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch explanation')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse text-muted-foreground">Loading AI insights...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-destructive mb-4">{error}</p>
            <button
              onClick={handleRefresh}
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
            <Bot className="h-5 w-5 text-foreground" />
            <CardTitle>AI Insights</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {explanation && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRefresh()
                  }}
                  className="h-8 w-8"
                  title="Refresh explanation"
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleCopy()
                  }}
                  className="h-8 w-8"
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </>
            )}
            <span className="text-sm text-muted-foreground">
              {expanded ? '▼' : '▶'}
            </span>
          </div>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent>
          {!explanation ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                No explanation available yet. Run the pipeline to generate AI insights.
              </p>
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto pr-2">
              {formatExplanation(explanation)}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

