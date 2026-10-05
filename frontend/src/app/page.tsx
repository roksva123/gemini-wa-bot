'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import Link from 'next/link'

interface Dashboard {
  conversations_today: number
  new_leads: number
  conversations_need_handoff: number
}

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      // Get summary data dari API
      const [convs, leads] = await Promise.all([
        api.getConversations(10),
        api.getLeads('baru', 10),
      ])

      // Simple calculation untuk hari ini
      const today = new Date().toDateString()
      const convsToday = convs.data?.filter(
        (c: any) => new Date(c.created_at).toDateString() === today
      ).length || 0

      const needHandoff = convs.data?.filter((c: any) => c.handoff).length || 0

      setData({
        conversations_today: convsToday,
        new_leads: leads.data?.length || 0,
        conversations_need_handoff: needHandoff,
      })
      setIsLoading(false)
    }

    fetchData()
  }, [])

  if (isLoading) return <LoadingSkeleton count={3} height="h-32" />

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">📊 Ringkasan</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Lihat overview bot Anda hari ini</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Percakapan Hari Ini */}
        <Link href="/percakapan">
          <div className="card card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-sm">Percakapan Hari Ini</p>
                <p className="text-3xl font-bold text-primary-600 dark:text-primary-400 mt-2">
                  {data?.conversations_today || 0}
                </p>
              </div>
              <span className="text-4xl">💬</span>
            </div>
          </div>
        </Link>

        {/* Lead Baru */}
        <Link href="/lead?status=baru">
          <div className="card card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-sm">Lead Baru</p>
                <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">
                  {data?.new_leads || 0}
                </p>
              </div>
              <span className="text-4xl">👥</span>
            </div>
          </div>
        </Link>

        {/* Perlu Admin */}
        <Link href="/percakapan?filter=handoff">
          <div className="card card-hover">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 dark:text-gray-400 text-sm">Perlu Admin Handoff</p>
                <p className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">
                  {data?.conversations_need_handoff || 0}
                </p>
              </div>
              <span className="text-4xl">⚠️</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">🚀 Mulai</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/pengaturan" className="p-4 rounded-lg border-2 border-primary-200 dark:border-primary-800 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors">
            <div className="text-2xl mb-2">⚙️</div>
            <h3 className="font-medium">Setup Bot</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Edit FAQ, jam kerja, alamat</p>
          </Link>

          <Link href="/coba-bot" className="p-4 rounded-lg border-2 border-green-200 dark:border-green-800 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
            <div className="text-2xl mb-2">🤖</div>
            <h3 className="font-medium">Test Bot</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">Coba response bot sebelum go-live</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
