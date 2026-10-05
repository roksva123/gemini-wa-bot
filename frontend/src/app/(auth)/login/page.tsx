'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore, useUiStore } from '@/lib/store'
import { api } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const showToast = useUiStore((state) => state.showToast)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const response = await api.login(email, password)

    if (response.error) {
      setError(response.error)
      showToast('Login gagal. Cek email dan password.')
      setIsLoading(false)
      return
    }

    if (response.data?.business_id) {
      setAuth(response.data.business_id, email)
      showToast('Login berhasil! 🎉')
      router.push('/')
    }

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-primary-100 dark:from-gray-900 dark:to-gray-800 p-4">
      <div className="card w-full max-w-md shadow-xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🤖</h1>
          <h2 className="text-3xl font-bold text-primary-600 dark:text-primary-400">BotWA Admin</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Panel admin untuk bot WhatsApp bisnis</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Email */}
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@business.com"
              required
              disabled={isLoading}
              className="w-full"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              disabled={isLoading}
              className="w-full"
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '⏳ Masuk...' : '🔓 Masuk'}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
            Hubungi administrator jika belum memiliki akun
          </p>
        </div>
      </div>
    </div>
  )
}
