'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useUiStore } from '@/lib/store'
import LoadingSkeleton from '@/components/LoadingSkeleton'
import ChatBubble from '@/components/ChatBubble'

interface Message {
  id: number
  role: 'user' | 'assistant'
  message: string
  created_at: string
}

interface Conversation {
  id: number
  customer_phone: string
  customer_name?: string
  handoff: boolean
  updated_at: string
}

export default function ConversationsPage() {
  const showToast = useUiStore((state) => state.showToast)

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [replyText, setReplyText] = useState('')
  const [isHandoff, setIsHandoff] = useState(false)

  useEffect(() => {
    const fetchConversations = async () => {
      const response = await api.getConversations(50)
      if (response.data) {
        setConversations(response.data)
        if (response.data.length > 0) {
          setSelectedConv(response.data[0])
        }
      }
      setIsLoading(false)
    }

    fetchConversations()
  }, [])

  useEffect(() => {
    if (selectedConv) {
      const fetchMessages = async () => {
        const response = await api.getConversation(selectedConv.id)
        if (response.data?.messages) {
          setMessages(response.data.messages)
          setIsHandoff(response.data.handoff)
        }
      }

      fetchMessages()
    }
  }, [selectedConv])

  const handleSendReply = async () => {
    if (!replyText.trim() || !selectedConv) return

    const response = await api.sendReply(selectedConv.id, replyText)

    if (response.error) {
      showToast('❌ Gagal mengirim balasan')
    } else {
      setReplyText('')
      showToast('✅ Balasan dikirim ke WhatsApp')
      // Refresh messages
      const msgRes = await api.getConversation(selectedConv.id)
      if (msgRes.data?.messages) {
        setMessages(msgRes.data.messages)
      }
    }
  }

  const handleSetHandoff = async (value: boolean) => {
    if (!selectedConv) return

    const response = await api.setHandoff(selectedConv.id, value)

    if (response.error) {
      showToast('❌ Gagal mengubah status')
    } else {
      setIsHandoff(value)
      showToast(value ? '🚨 Bot mode OFF - Admin menangani' : '✅ Bot mode ON')
    }
  }

  if (isLoading) return <LoadingSkeleton count={3} />

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">💬 Percakapan</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">Kelola percakapan dengan customer</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        {/* Conversation List */}
        <div className="card overflow-y-auto">
          <h2 className="text-lg font-bold mb-4">📋 Daftar Percakapan</h2>
          <div className="space-y-2">
            {conversations.length === 0 ? (
              <p className="text-gray-600 dark:text-gray-400 text-sm">Belum ada percakapan</p>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConv(conv)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedConv?.id === conv.id
                      ? 'bg-primary-100 dark:bg-primary-900'
                      : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <p className="font-medium truncate">{conv.customer_name || conv.customer_phone}</p>
                  <p className="text-xs text-gray-500 truncate">{conv.customer_phone}</p>
                  {conv.handoff && <p className="text-xs text-red-600 dark:text-red-400 mt-1">🚨 Admin Mode</p>}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-2 card flex flex-col">
          {selectedConv ? (
            <>
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-gray-200 dark:border-gray-700">
                <div>
                  <h3 className="font-bold">{selectedConv.customer_name || 'Customer'}</h3>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{selectedConv.customer_phone}</p>
                </div>
                <button
                  onClick={() => handleSetHandoff(!isHandoff)}
                  className={`btn btn-small ${isHandoff ? 'bg-red-600 text-white' : 'bg-green-600 text-white'}`}
                >
                  {isHandoff ? '🤖 Aktifkan Bot' : '✋ Ambil Alih'}
                </button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <p className="text-gray-600 dark:text-gray-400 text-center">Belum ada pesan</p>
                ) : (
                  messages.map((msg) => (
                    <ChatBubble
                      key={msg.id}
                      role={msg.role}
                      message={msg.message}
                      timestamp={msg.created_at}
                    />
                  ))
                )}
              </div>

              {/* Reply Box */}
              {isHandoff && (
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex gap-2">
                    <textarea
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder="Ketik balasan..."
                      rows={2}
                      className="flex-1"
                    />
                    <button
                      onClick={handleSendReply}
                      disabled={!replyText.trim()}
                      className="btn btn-primary btn-small self-end disabled:opacity-50"
                    >
                      📤
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-600 dark:text-gray-400">
              Pilih percakapan untuk melihat detail
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
