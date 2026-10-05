'use client'

import { useUiStore } from '@/lib/store'
import { useEffect } from 'react'

export default function Toast() {
  const message = useUiStore((state) => state.toastMessage)
  const hideToast = useUiStore((state) => state.hideToast)

  useEffect(() => {
    if (message) {
      const timer = setTimeout(hideToast, 3000)
      return () => clearTimeout(timer)
    }
  }, [message, hideToast])

  if (!message) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 slide-in">
      <div className="bg-primary-600 text-white rounded-lg shadow-lg px-4 py-3 max-w-sm">
        <p className="text-sm font-medium">{message}</p>
      </div>
    </div>
  )
}
