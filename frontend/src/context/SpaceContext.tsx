import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { getSpaces } from '../api/spaces'
import type { SpaceResponse } from '../types/api'

interface SpaceContextValue {
  spaces: SpaceResponse[]
  activeSpace: SpaceResponse | null
  setActiveSpace: (space: SpaceResponse) => void
  isLoading: boolean
  error: string | null
  refreshSpaces: () => Promise<void>
}

const SpaceContext = createContext<SpaceContextValue | undefined>(undefined)

export function SpaceProvider({ children }: { children: ReactNode }) {
  const [spaces, setSpaces] = useState<SpaceResponse[]>([])
  const [activeSpace, setActiveSpace] = useState<SpaceResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSpaces = useCallback(async () => {
    try {
      const result = await getSpaces()
      setSpaces(result)
      setActiveSpace((current) => {
        if (current && result.some((s) => s.space_id === current.space_id)) {
          return current
        }
        return result[0] ?? null
      })
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load spaces')
    }
  }, [])

  useEffect(() => {
    setIsLoading(true)
    loadSpaces().finally(() => setIsLoading(false))
  }, [loadSpaces])

  return (
    <SpaceContext.Provider value={{ spaces, activeSpace, setActiveSpace, isLoading, error, refreshSpaces: loadSpaces }}>
      {children}
    </SpaceContext.Provider>
  )
}

export function useSpaceContext(): SpaceContextValue {
  const context = useContext(SpaceContext)
  if (!context) {
    throw new Error('useSpaceContext must be used within a SpaceProvider')
  }
  return context
}