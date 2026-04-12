'use client'

import { AlertCircle } from 'lucide-react'

interface ErrorAlertProps {
  message: string
  onRetry?: () => void
  className?: string
}

export default function ErrorAlert({ message, onRetry, className = '' }: ErrorAlertProps) {
  return (
    <div className={`bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-3 ${className}`}>
      <AlertCircle className="w-5 h-5 flex-shrink-0" />
      <span className="flex-1">{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-sm font-medium"
        >
          Retry
        </button>
      )}
    </div>
  )
}
