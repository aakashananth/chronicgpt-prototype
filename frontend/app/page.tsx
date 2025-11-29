'use client'

import { useState } from 'react'
import HeaderBar from './components/dashboard/HeaderBar'
import ControlStatusRow from './components/dashboard/ControlStatusRow'
import MetricCardsRow from './components/dashboard/MetricCardsRow'
import DateRangeSelector from './components/dashboard/DateRangeSelector'
import DataCompletenessIndicator from './components/dashboard/DataCompletenessIndicator'
import SummaryPanel from './components/dashboard/SummaryPanel'
import ChartsGrid from './components/dashboard/ChartsGrid'
import AnomaliesPanel from './components/dashboard/AnomaliesPanel'
import ExplanationPanel from './components/dashboard/ExplanationPanel'
import { PipelineRunResponse } from '@/lib/api'

export default function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [days, setDays] = useState(30)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)

  const handlePipelineRun = (result: PipelineRunResponse) => {
    // Update last updated timestamp
    localStorage.setItem('lastDataUpdate', new Date().toISOString())
    window.dispatchEvent(new Event('dataUpdated'))
    // Trigger refresh of all components
    setRefreshKey((prev) => prev + 1)
  }

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar />
      <main className="container mx-auto px-4 py-6 sm:py-8 max-w-7xl">
        <div className="space-y-6 sm:space-y-8">
          {/* Control & Status Row */}
          <section>
            <ControlStatusRow onPipelineRun={handlePipelineRun} />
          </section>

          {/* Snapshot Cards */}
          <section>
            <MetricCardsRow refreshKey={refreshKey} />
          </section>

          {/* Date Picker + Time Window Selector */}
          <section>
            <div className="space-y-4">
              <DateRangeSelector
                onDateChange={setSelectedDate}
                onDaysChange={setDays}
                defaultDays={30}
              />
              <DataCompletenessIndicator
                days={days}
                endDate={selectedDate}
                refreshKey={refreshKey}
              />
            </div>
          </section>

          {/* Summary & Charts Section */}
          <section>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="lg:col-span-1">
                <SummaryPanel
                  days={days}
                  endDate={selectedDate}
                  refreshKey={refreshKey}
                />
              </div>
              <div className="lg:col-span-2">
                <h2 className="text-xl font-semibold mb-4 text-foreground">
                  Trends
                </h2>
                <ChartsGrid
                  days={days}
                  endDate={selectedDate}
                  refreshKey={refreshKey}
                />
              </div>
            </div>
          </section>

          {/* Anomalies & AI Explanation - Two Column Layout */}
          <section>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <AnomaliesPanel refreshKey={refreshKey} />
              </div>
              <div>
                <ExplanationPanel refreshKey={refreshKey} />
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
