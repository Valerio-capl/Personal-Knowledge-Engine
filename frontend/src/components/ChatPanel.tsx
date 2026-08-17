import { useState } from 'react'
import { runAsk } from '../api/ask'
import { ApiError } from '../api/client'
import { useSpaceContext } from '../context/SpaceContext'
import { useGenerationContext } from '../context/GenerationContext'
import { MessageBubble } from './MessageBubble'
import type { ChatMessage } from '../types/chat'

export function ChatPanel() {
  const { activeSpace } = useSpaceContext()
  const { provider: generationProvider, model: generationModel } = useGenerationContext()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)

  const isDisabled = !activeSpace || isSending

  async function handleSend() {
    const question = input.trim()
    if (!question || !activeSpace) return

    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: question }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsSending(true)

    try {
      const result = await runAsk({
        question,
        provider_name: activeSpace.provider_name,
        model_name: activeSpace.model_name,
        generation_provider: generationProvider,
        generation_model: generationModel,
      })

      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: result.answer, sources: result.sources },
      ])
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong.'
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'assistant', content: message, isError: true },
      ])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {messages.length === 0 && (
          <div className="text-sm text-stone-500">
            {activeSpace
              ? 'Ask a question about your indexed documents.'
              : 'No knowledge space available — sync some documents first.'}
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>

      <div className="border-t border-stone-800 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isDisabled) handleSend()
            }}
            disabled={isDisabled}
            placeholder={activeSpace ? 'Type a message...' : 'Index some documents first'}
            className="flex-1 rounded-md border border-stone-700 bg-stone-800 px-3 py-2 text-sm text-stone-100 placeholder:text-stone-500 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isDisabled || !input.trim()}
            className="rounded-md bg-stone-100 px-4 py-2 text-sm font-medium text-stone-900 hover:bg-white disabled:opacity-50"
          >
            {isSending ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  )
}