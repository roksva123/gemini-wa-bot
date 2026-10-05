'use client'

import { useAuthStore, useUiStore } from '@/lib/store'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface NavItem {
  href: string
  label: string
  icon: string
}

const navItems: NavItem[] = [
  { href: '/', label: 'Ringkasan', icon: '📊' },
  { href: '/pengaturan', label: 'Pengaturan', icon: '⚙️' },
  { href: '/percakapan', label: 'Percakapan', icon: '💬' },
  { href: '/lead', label: 'Lead', icon: '👥' },
  { href: '/coba-bot', label: 'Coba Bot', icon: '🤖' },
]

export default function Sidebar() {
  const router = useRouter()
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const isDarkMode = useUiStore((state) => state.isDarkMode)
  const toggleDarkMode = useUiStore((state) => state.toggleDarkMode)
  const [currentPath, setCurrentPath] = useState('')
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  useEffect(() => {
    if (!isLoggedIn) {
      router.push('/login')
    }
  }, [isLoggedIn, router])

  useEffect(() => {
    setCurrentPath(window.location.pathname)
  }, [])

  const handleLogout = () => {
    clearAuth()
    router.push('/login')
  }

  if (!isLoggedIn) return null

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="md:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-primary-600 text-white"
      >
        ☰
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-20"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col transition-all fixed md:static inset-y-0 left-0 z-30 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-800">
          <Link href="/" onClick={() => setIsMobileOpen(false)}>
            <h1 className="text-2xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
              🤖 BotWA
            </h1>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const isActive = currentPath === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800 space-y-3">
          {/* Dark mode toggle */}
          <button
            onClick={toggleDarkMode}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <span className="text-xl">{isDarkMode ? '☀️' : '🌙'}</span>
            <span className="font-medium">{isDarkMode ? 'Mode Terang' : 'Mode Gelap'}</span>
          </button>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <span className="text-xl">🚪</span>
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>
    </>
  )
}
