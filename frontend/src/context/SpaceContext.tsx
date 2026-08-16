import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getSpaces } from '../api/spaces'
import type { SpaceResponse } from '../types/api'

interface SpaceContextValue {
  spaces: SpaceResponse[]
  activeSpace: SpaceResponse | null
  setActiveSpace: (space: SpaceResponse) => void
  isLoading: boolean
  error: string | null
}

const SpaceContext = createContext<SpaceContextValue | undefined>(undefined)

export function SpaceProvider({ children }: { children: ReactNode }) {
  const [spaces, setSpaces] = useState<SpaceResponse[]>([])
  const [activeSpace, setActiveSpace] = useState<SpaceResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSpaces()
      .then((result) => {
        setSpaces(result)
        if (result.length > 0) {
          setActiveSpace(result[0])
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load spaces'))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <SpaceContext.Provider value={{ spaces, activeSpace, setActiveSpace, isLoading, error }}>
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