import { apiPost } from './client'
import type { AskRequest, AskResponse } from '../types/api'

export function runAsk(request: AskRequest): Promise<AskResponse> {
  return apiPost<AskRequest, AskResponse>('/ask', request)
}