import type { SourceItem } from './api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceItem[]
  isError?: boolean
}