import type { ChatMessage } from '../types/chat'
import { SourceList } from './SourceList'

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-md rounded-lg px-4 py-2 text-sm ${
          isUser
            ? 'bg-stone-700 text-stone-50'
            : message.isError
              ? 'border border-red-900 bg-red-950/50 text-red-300'
              : 'bg-stone-800 text-stone-100'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.sources && <SourceList sources={message.sources} />}
      </div>
    </div>
  )
}