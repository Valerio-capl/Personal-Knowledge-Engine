// mirrors the _KNOWN_MODEL_DIMENSIONS maps in embedding/providers/*.py.

export const EMBEDDING_PROVIDERS = ['openai', 'ollama'] as const
export type EmbeddingProviderName = (typeof EMBEDDING_PROVIDERS)[number]

export const EMBEDDING_MODELS: Record<EmbeddingProviderName, string[]> = {
  openai: ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'],
  ollama: ['nomic-embed-text-v2-moe', 'nomic-embed-text', 'bge-m3'],
}