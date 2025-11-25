'use client'

import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: string
  message: string
  type: ToastType
  duration?: number
}

interface ToastProps {
  toast: Toast
  onClose: (id: string) => void
}

function ToastItem({ toast, onClose }: ToastProps) {
  useEffect(() => {
    if (toast.duration !== 0) {
      const timer = setTimeout(() => {
        onClose(toast.id)
      }, toast.duration || 5000)

      return () => clearTimeout(timer)
    }
  }, [toast.id, toast.duration, onClose])

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle,
  }

  const styles = {
    success: 'bg-success/20 border-success text-success',
    error: 'bg-destructive/20 border-destructive text-destructive',
    info: 'bg-primary/20 border-primary text-primary',
    warning: 'bg-warning/20 border-warning text-warning',
  }

  const Icon = icons[toast.type]

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] max-w-md animate-in slide-in-from-top-5',
        styles[toast.type]
      )}
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 text-current/70 hover:text-current transition-colors"
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

let toastIdCounter = 0
const toastListeners = new Set<(toasts: Toast[]) => void>()
let toasts: Toast[] = []

function addToast(toast: Omit<Toast, 'id'>) {
  const newToast: Toast = {
    ...toast,
    id: `toast-${toastIdCounter++}`,
  }
  toasts = [...toasts, newToast]
  toastListeners.forEach((listener) => listener(toasts))
}

function removeToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id)
  toastListeners.forEach((listener) => listener(toasts))
}

export function toast(message: string, type: ToastType = 'info', duration?: number) {
  addToast({ message, type, duration })
}

export function useToast() {
  const [currentToasts, setCurrentToasts] = useState<Toast[]>(toasts)

  useEffect(() => {
    const listener = (newToasts: Toast[]) => {
      setCurrentToasts(newToasts)
    }
    toastListeners.add(listener)
    return () => {
      toastListeners.delete(listener)
    }
  }, [])

  return {
    toasts: currentToasts,
    toast,
    removeToast,
  }
}

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onClose={removeToast} />
        </div>
      ))}
    </div>
  )
}

