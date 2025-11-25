'use client'

import { useState } from 'react'
import TabNavigation from './components/TabNavigation'
import OverviewSection from './components/OverviewSection'
import MetricsSection from './components/MetricsSection'
import AnomaliesSection from './components/AnomaliesSection'
import ExplanationSection from './components/ExplanationSection'
import { PipelineRunResponse } from '../lib/api'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview')
  const [pipelineResult, setPipelineResult] = useState<PipelineRunResponse | null>(null)

  const handlePipelineRun = (result: PipelineRunResponse) => {
    setPipelineResult(result)
    // Optionally switch to anomalies tab if anomalies found
    if (result.recent_anomalies.length > 0) {
      // Don't auto-switch, let user decide
    }
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewSection onPipelineRun={handlePipelineRun} />
      case 'metrics':
        return <MetricsSection />
      case 'anomalies':
        return <AnomaliesSection />
      case 'explanation':
        return <ExplanationSection />
      default:
        return <OverviewSection onPipelineRun={handlePipelineRun} />
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="mt-6">{renderContent()}</div>
    </div>
  )
}
