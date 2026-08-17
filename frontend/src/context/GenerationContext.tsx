import { createContext, useContext, useState, type ReactNode } from 'react'
import type { GenerationProviderName } from '../config/generationModels'

export const DEFAULT_GENERATION_PROVIDER = 'ollama'
export const DEFAULT_GENERATION_MODEL = 'llama3.1'

interface GenerationContextValue {
  provider: GenerationProviderName
  model: string
  setProvider: (provider: GenerationProviderName) => void
  setModel: (model: string) => void
}

const GenerationContext = createContext<GenerationContextValue | undefined>(undefined)

export function GenerationProvider({ children }: { children: ReactNode }) {
  const [provider, setProvider] = useState<GenerationProviderName>(
    DEFAULT_GENERATION_PROVIDER as GenerationProviderName,
  )
  const [model, setModel] = useState(DEFAULT_GENERATION_MODEL)

  return (
    <GenerationContext.Provider value={{ provider, model, setProvider, setModel }}>
      {children}
    </GenerationContext.Provider>
  )
}

export function useGenerationContext(): GenerationContextValue {
  const context = useContext(GenerationContext)
  if (!context) {
    throw new Error('useGenerationContext must be used within a GenerationProvider')
  }
  return context
}