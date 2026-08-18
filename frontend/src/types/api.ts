export interface SpaceResponse {
  space_id: string
  provider_name: string
  model_name: string
}

export interface SyncRequest {
  folder_path: string
  provider_name: string
  model_name: string
}

export interface SyncResponse {
  synced: string[]
  skipped: string[]
  failed: [string, string][]
  deleted: string[]
}

export interface SearchRequest {
  query: string
  provider_name: string
  model_name: string
  top_k?: number
}

export interface SearchResultResponse {
  content: string
  score: number
  rank: number
  filepath: string
}

export interface AskRequest {
  question: string
  provider_name: string
  model_name: string
  generation_provider: string
  generation_model: string
  top_k?: number
  min_score?: number
}

export interface SourceItem {
  id: number
  file: string
  score: number
}

export interface AskResponse {
  answer: string
  sources: SourceItem[]
}