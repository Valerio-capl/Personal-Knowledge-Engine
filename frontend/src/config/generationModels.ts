// mirrors the providers registered in generation/factory.py

export const GENERATION_PROVIDERS = ['ollama', 'openai'] as const
export type GenerationProviderName = (typeof GENERATION_PROVIDERS)[number]

export const GENERATION_MODELS: Record<GenerationProviderName, string[]> = {
  ollama: ['llama3.1', 'qwen2.5', 'mistral'],
  openai: ['gpt-4o-mini', 'gpt-4o'],
}