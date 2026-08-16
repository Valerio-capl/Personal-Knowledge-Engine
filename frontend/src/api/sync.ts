import { apiPost } from './client'
import type { SyncRequest, SyncResponse } from '../types/api'

export function runSync(request: SyncRequest): Promise<SyncResponse> {
  return apiPost<SyncRequest, SyncResponse>('/sync', request)
}