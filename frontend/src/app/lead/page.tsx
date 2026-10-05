'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useUiStore } from '@/lib/store'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import Papa from 'papaparse'

interface Lead {
  id: number
  customer_name: string
  customer_phone: string
  need: string
  status: 'baru' | 'follow-up' | 'selesai'
  created_at: string
}

export default function LeadPage() {
  const showToast = useUiStore((state) => state.showToast)

  const [leads, setLeads] = useState<Lead[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')

  useEffect(() => {
    const fetchLeads = async () => {
      const response = await api.getLeads(statusFilter || undefined)
      if (response.data) {
        setLeads(response.data)
      }
      setIsLoading(false)
    }

    fetchLeads()
  }, [statusFilter])

  const handleStatusChange = async (leadId: number, newStatus: string) => {
    const response = await api.updateLead(leadId, { status: newStatus })

    if (response.error) {
      showToast('❌ Gagal mengubah status')
    } else {
      setLeads(leads.map((l) => (l.id === leadId ? { ...l, status: newStatus as any } : l)))
      showToast('✅ Status diubah')
    }
  }

  const handleExportCSV = () => {
    const csv = Papa.unparse(
      leads.map((l) => ({
        Nama: l.customer_name,
        'Nomor HP': l.customer_phone,
        Kebutuhan: l.need,
        Status: l.status,
        Tanggal: new Date(l.created_at).toLocaleDateString('id-ID'),
      }))
    )

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `leads-${new Date().toISOString().split('T')[0]}.csv`
    a.click()

    showToast('✅ CSV diunduh')
  }

  if (isLoading) return <LoadingSkeleton count={5} height="h-12" />

  const statusOptions = [
    { value: 'baru', label: '🆕 Baru', color: 'badge-info' },
    { value: 'follow-up', label: '📞 Perlu Follow-up', color: 'badge-warning' },
    { value: 'selesai', label: '✅ Selesai', color: 'badge-success' },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">👥 Lead</h1>
          <p className="text-gray-600 dark:text-gray-400">Calon customer yang tertarik</p>
        </div>
        <button onClick={handleExportCSV} className="btn btn-secondary">
          📥 Ekspor CSV
        </button>
      </div>

      {/* Filter */}
      <div className="card mb-6">
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setStatusFilter('')}
            className={`btn btn-small ${statusFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Semua ({leads.length})
          </button>
          {statusOptions.map((opt) => {
            const count = leads.filter((l) => l.status === opt.value).length
            return (
              <button
                key={opt.value}
                onClick={() => setStatusFilter(opt.value)}
                className={`btn btn-small ${statusFilter === opt.value ? 'btn-primary' : 'btn-secondary'}`}
              >
                {opt.label} ({count})
              </button>
            )
          })}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        {leads.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              Belum ada lead. Lead muncul otomatis saat customer ingin memesan.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold">Nama</th>
                <th className="text-left py-3 px-4 font-semibold">Nomor HP</th>
                <th className="text-left py-3 px-4 font-semibold">Kebutuhan</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="text-left py-3 px-4 font-semibold">Tanggal</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="py-3 px-4">{lead.customer_name}</td>
                  <td className="py-3 px-4">
                    <a href={`https://wa.me/${lead.customer_phone}`} target="_blank" rel="noopener noreferrer">
                      <span className="text-primary-600 hover:underline">{lead.customer_phone}</span>
                    </a>
                  </td>
                  <td className="py-3 px-4 truncate-2 text-sm">{lead.need}</td>
                  <td className="py-3 px-4">
                    <select
                      value={lead.status}
                      onChange={(e) => handleStatusChange(lead.id, e.target.value)}
                      className="text-sm"
                    >
                      {statusOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-3 px-4 text-sm">
                    {new Date(lead.created_at).toLocaleDateString('id-ID')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
