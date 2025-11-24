'use client'

interface CardProps {
  children: React.ReactNode
  className?: string
}

export default function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-gray-900 rounded-lg p-6 shadow-lg ${className}`}>
      {children}
    </div>
  )
}

