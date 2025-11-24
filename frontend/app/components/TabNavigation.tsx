'use client'

interface TabNavigationProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export default function TabNavigation({ activeTab, onTabChange }: TabNavigationProps) {
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'metrics', label: 'Metrics' },
    { id: 'anomalies', label: 'Anomalies' },
    { id: 'explanation', label: 'AI Explanation' },
  ]

  return (
    <div className="border-b border-gray-800">
      <nav className="flex space-x-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap
              ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-500 text-blue-400'
                  : 'text-gray-400 hover:text-gray-300 hover:border-b-2 hover:border-gray-700'
              }
            `}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

