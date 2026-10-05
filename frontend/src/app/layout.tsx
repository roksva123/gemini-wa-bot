'use client'

import { useEffect } from 'react'
import { useUiStore } from '@/lib/store'
import Sidebar from '@/components/Sidebar'
import Toast from '@/components/Toast'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isDarkMode = useUiStore((state) => state.isDarkMode)

  useEffect(() => {
    // Apply dark mode class to html element
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDarkMode])

  return (
    <html lang="id" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Admin Bot WhatsApp</title>
        <meta name="description" content="Panel admin untuk bot WhatsApp bisnis" />
      </head>
      <body className="transition-colors duration-200">
        <div className="flex min-h-screen bg-white dark:bg-gray-950">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <div className="container max-w-7xl mx-auto p-4 md:p-6">
              {children}
            </div>
          </main>
        </div>
        <Toast />
      </body>
    </html>
  )
}
