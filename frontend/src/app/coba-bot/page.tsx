'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { useUiStore } from '@/lib/store'
import ChatBubble from '@/components/ChatBubble'

export default function TestBotPage() {
  const showToast = useUiStore((state) => state.showToast)

  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async () => {
    if (!inputText.trim()) return

    // Add user message
    const newMessages = [...messages, { role: 'user' as const, content: inputText }]
    setMessages(newMessages)
    setInputText('')

    // Get bot response
    setIsLoading(true)
    const response = await api.testChat(inputText)

    if (response.error) {
      showToast('❌ Error: ' + response.error)
      setIsLoading(false)
      return
    }

    if (response.data?.message) {
      setMessages([...newMessages, { role: 'assistant' as const, content: response.data.message }])
    }

    setIsLoading(false)
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">🤖 Coba Bot</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">Test bot response sebelum di-deploy ke production</p>

      {/* Chat Container */}
      <div className="card h-96 md:h-[calc(100vh-200px)] flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 mb-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-600 dark:text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">🤖</div>
                <p>Mulai tanya bot untuk melihat response</p>
                <p className="text-sm mt-2">Bot akan menjawab berdasarkan FAQ dan pengaturan yang sudah kamu buat</p>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <ChatBubble key={idx} role={msg.role} message={msg.content} />
            ))
          )}
          {isLoading && (
            <div className="flex gap-2">
              <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-700 animate-pulse" />
              <div className="text-sm text-gray-600 dark:text-gray-400">Bot sedang mengetik...</div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4 flex gap-2">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendMessage()
              }
            }}
            placeholder="Ketik pesan untuk bot..."
            rows={1}
            disabled={isLoading}
            className="flex-1"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
            className="btn btn-primary self-end disabled:opacity-50"
          >
            📤
          </button>
        </div>
      </div>

      {/* Tips */}
      <div className="card mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <h3 className="font-bold text-blue-900 dark:text-blue-200 mb-2">💡 Tips</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
          <li>✓ Coba tanya berdasarkan FAQ yang sudah kamu buat</li>
          <li>✓ Coba pertanyaan yang tidak ada di FAQ untuk lihat response fallback</li>
          <li>✓ Coba trigger pemesanan untuk lihat lead creation</li>
          <li>✓ Edit FAQ di halaman Pengaturan untuk mengubah response bot</li>
        </ul>
      </div>
    </div>
  )
}
