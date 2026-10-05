'use client'

import { useEffect, useState } from 'react'
import { useUiStore } from '@/lib/store'
import { api } from '@/lib/api'
import LoadingSkeleton from '@/components/LoadingSkeleton'

interface Business {
  name: string
  category?: string
  tone: string
  opening_hours?: string
  address?: string
  order_flow?: string
}

interface FAQ {
  id: number
  question: string
  answer: string
  order: number
}

export default function SettingsPage() {
  const showToast = useUiStore((state) => state.showToast)

  const [business, setBusiness] = useState<Business | null>(null)
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [newFaq, setNewFaq] = useState({ question: '', answer: '' })

  useEffect(() => {
    const fetchData = async () => {
      const [bizRes, faqRes] = await Promise.all([api.getBusiness(), api.getFaqs()])

      if (bizRes.data) setBusiness(bizRes.data)
      if (faqRes.data) setFaqs(faqRes.data)

      setIsLoading(false)
    }

    fetchData()
  }, [])

  const handleBusinessChange = (field: string, value: string) => {
    setBusiness({ ...business!, [field]: value })
  }

  const handleSaveBusiness = async () => {
    setIsSaving(true)
    const response = await api.updateBusiness(business)

    if (response.error) {
      showToast('❌ Gagal menyimpan pengaturan')
    } else {
      showToast('✅ Pengaturan disimpan!')
    }

    setIsSaving(false)
  }

  const handleAddFaq = async () => {
    if (!newFaq.question.trim() || !newFaq.answer.trim()) {
      showToast('⚠️ Pertanyaan dan jawaban tidak boleh kosong')
      return
    }

    const response = await api.createFaq({
      ...newFaq,
      order: faqs.length,
    })

    if (response.error) {
      showToast('❌ Gagal menambah FAQ')
    } else {
      setFaqs([...faqs, response.data])
      setNewFaq({ question: '', answer: '' })
      showToast('✅ FAQ ditambahkan!')
    }
  }

  const handleDeleteFaq = async (faqId: number) => {
    const response = await api.deleteFaq(faqId)

    if (response.error) {
      showToast('❌ Gagal menghapus FAQ')
    } else {
      setFaqs(faqs.filter((f) => f.id !== faqId))
      showToast('✅ FAQ dihapus')
    }
  }

  if (isLoading) return <LoadingSkeleton count={4} height="h-20" />

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">⚙️ Pengaturan Bot</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">Konfigurasi bot WhatsApp Anda</p>

      {!business ? (
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">Tidak bisa load pengaturan</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Business Settings */}
          <div className="card">
            <h2 className="text-xl font-bold mb-6">📋 Info Bisnis</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Nama Bisnis</label>
                <input
                  type="text"
                  value={business.name}
                  onChange={(e) => handleBusinessChange('name', e.target.value)}
                  disabled={isSaving}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Kategori</label>
                  <input
                    type="text"
                    value={business.category || ''}
                    onChange={(e) => handleBusinessChange('category', e.target.value)}
                    placeholder="Kafe, Toko Online, Klinik..."
                    disabled={isSaving}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Gaya Bahasa</label>
                  <select
                    value={business.tone}
                    onChange={(e) => handleBusinessChange('tone', e.target.value)}
                    disabled={isSaving}
                    className="w-full"
                  >
                    <option value="ramah">🤗 Ramah dan santai</option>
                    <option value="formal">📋 Formal dan profesional</option>
                    <option value="profesional">💼 Profesional</option>
                    <option value="santai">👋 Santai dan teman</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Jam Operasional</label>
                  <input
                    type="text"
                    value={business.opening_hours || ''}
                    onChange={(e) => handleBusinessChange('opening_hours', e.target.value)}
                    placeholder="08:00 - 17:00 (Senin-Jumat)"
                    disabled={isSaving}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Alamat</label>
                  <input
                    type="text"
                    value={business.address || ''}
                    onChange={(e) => handleBusinessChange('address', e.target.value)}
                    placeholder="Jl. Sudirman No. 123"
                    disabled={isSaving}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Cara Memesan / Eskalasi</label>
                <textarea
                  value={business.order_flow || ''}
                  onChange={(e) => handleBusinessChange('order_flow', e.target.value)}
                  placeholder="Jelaskan bagaimana customer bisa memesan atau berbicara dengan admin..."
                  rows={3}
                  disabled={isSaving}
                  className="w-full"
                />
              </div>

              <button
                onClick={handleSaveBusiness}
                disabled={isSaving}
                className="btn btn-primary disabled:opacity-50"
              >
                {isSaving ? '⏳ Menyimpan...' : '💾 Simpan Pengaturan'}
              </button>
            </div>
          </div>

          {/* FAQ Section */}
          <div className="card">
            <h2 className="text-xl font-bold mb-6">❓ FAQ & Katalog</h2>

            {/* FAQ List */}
            <div className="space-y-3 mb-6">
              {faqs.length === 0 ? (
                <p className="text-gray-600 dark:text-gray-400 text-center py-4">
                  Belum ada FAQ. Tambahkan pertanyaan dan jawaban yang sering ditanyakan customer.
                </p>
              ) : (
                faqs.map((faq) => (
                  <div key={faq.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-medium">❓ {faq.question}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{faq.answer}</p>
                      </div>
                      <button
                        onClick={() => handleDeleteFaq(faq.id)}
                        className="text-red-600 dark:text-red-400 hover:text-red-700 text-sm"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Add FAQ Form */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="font-medium mb-4">➕ Tambah FAQ Baru</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  value={newFaq.question}
                  onChange={(e) => setNewFaq({ ...newFaq, question: e.target.value })}
                  placeholder="Pertanyaan (misal: Berapa harga?)"
                  className="w-full"
                />
                <textarea
                  value={newFaq.answer}
                  onChange={(e) => setNewFaq({ ...newFaq, answer: e.target.value })}
                  placeholder="Jawaban (misal: Harga mulai dari Rp 50.000)"
                  rows={2}
                  className="w-full"
                />
                <button onClick={handleAddFaq} className="btn btn-primary w-full">
                  ➕ Tambah
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
