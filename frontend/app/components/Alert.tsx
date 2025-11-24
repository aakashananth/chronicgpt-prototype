'use client'

interface AlertProps {
  type: 'success' | 'error' | 'info'
  message: string
  onClose?: () => void
}

export default function Alert({ type, message, onClose }: AlertProps) {
  const styles = {
    success: 'bg-green-900/20 border-green-500 text-green-400',
    error: 'bg-red-900/20 border-red-500 text-red-400',
    info: 'bg-blue-900/20 border-blue-500 text-blue-400',
  }

  return (
    <div
      className={`border rounded-lg p-4 ${styles[type]} flex items-start justify-between`}
    >
      <p className="flex-1">{message}</p>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-4 text-gray-400 hover:text-white"
          aria-label="Close"
        >
          ×
        </button>
      )}
    </div>
  )
}

