'use client'

import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'
import { format } from 'date-fns'

export default function HeaderBar() {
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    // Try to get last updated from localStorage or set to now
    const updateLastUpdated = () => {
      const stored = localStorage.getItem('lastDataUpdate')
      if (stored) {
        setLastUpdated(new Date(stored))
      } else {
        setLastUpdated(new Date())
      }
    }

    updateLastUpdated()

    // Listen for storage events (when other tabs update)
    window.addEventListener('storage', updateLastUpdated)
    
    // Also listen for custom event (when same tab updates)
    window.addEventListener('dataUpdated', updateLastUpdated)

    return () => {
      window.removeEventListener('storage', updateLastUpdated)
      window.removeEventListener('dataUpdated', updateLastUpdated)
    }
  }, [])

  return (
    <header className="border-b border-border bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">
              ChronicGPT
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Health Metrics Dashboard
            </p>
          </div>
          {lastUpdated && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>
                Last updated: {format(lastUpdated, 'MMM d, yyyy h:mm a')}
              </span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

