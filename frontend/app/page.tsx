'use client'

import { useState, useEffect } from 'react'
import HeaderBar from './components/dashboard/HeaderBar'
import MetricCardsRow from './components/dashboard/MetricCardsRow'
import ControlsBar from './components/dashboard/ControlsBar'
import ChartsGrid from './components/dashboard/ChartsGrid'
import AnomaliesPanel from './components/dashboard/AnomaliesPanel'
import ExplanationPanel from './components/dashboard/ExplanationPanel'
import { PipelineRunResponse } from '@/lib/api'

export default function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [timeRange, setTimeRange] = useState(7)
  const [selectedDate, setSelectedDate] = useState<string | undefined>()

  const handlePipelineRun = (result: PipelineRunResponse) => {
    // Update last updated timestamp
    localStorage.setItem('lastDataUpdate', new Date().toISOString())
    // Trigger refresh of all components
    setRefreshKey((prev) => prev + 1)
  }

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1)
  }

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar />
      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-8">
          {/* Today's Key Metrics */}
          <section>
            <h2 className="text-xl font-semibold mb-4 text-foreground">
              Today's Metrics
            </h2>
            <MetricCardsRow key={refreshKey} />
          </section>

          {/* Controls */}
          <section>
            <ControlsBar
              onPipelineRun={handlePipelineRun}
              onRefresh={handleRefresh}
              onTimeRangeChange={setTimeRange}
              onDateChange={setSelectedDate}
            />
          </section>

          {/* Time-Series Charts */}
          <section>
            <h2 className="text-xl font-semibold mb-4 text-foreground">
              Trends
            </h2>
            <ChartsGrid
              key={refreshKey}
              timeRange={timeRange}
              selectedDate={selectedDate}
            />
          </section>

          {/* Anomalies */}
          <section>
            <AnomaliesPanel key={refreshKey} />
          </section>

          {/* AI Explanation */}
          <section>
            <ExplanationPanel key={refreshKey} />
          </section>
        </div>
      </main>
    </div>
  )
}
