import { apiPost } from './client'
import type { SearchRequest, SearchResultResponse } from '../types/api'

export function runSearch(request: SearchRequest): Promise<SearchResultResponse[]> {
  return apiPost<SearchRequest, SearchResultResponse[]>('/search', request)
}