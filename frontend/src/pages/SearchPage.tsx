import { useState } from 'react'
import { runSearch } from '../api/search'
import { ApiError } from '../api/client'
import { useSpaceContext } from '../context/SpaceContext'
import { SearchResultCard } from '../components/SearchResultCard'
import type { SearchResultResponse } from '../types/api'

export function SearchPage() {
  const { activeSpace } = useSpaceContext()
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState<SearchResultResponse[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSearch() {
    const trimmed = query.trim()
    if (!trimmed || !activeSpace) return

    setIsSearching(true)
    setError(null)

    try {
      const result = await runSearch({
        query: trimmed,
        provider_name: activeSpace.provider_name,
        model_name: activeSpace.model_name,
        top_k: topK,
      })
      setResults(result)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col gap-4 p-6">
      <div>
        <h1 className="text-lg font-semibold text-stone-100">Search (debug)</h1>
        <p className="mt-1 text-sm text-stone-500">
          Raw vector search, bypasses the LLM. Active space:{' '}
          {activeSpace ? `${activeSpace.provider_name} / ${activeSpace.model_name}` : 'none'}
        </p>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && activeSpace) handleSearch()
          }}
          disabled={!activeSpace}
          placeholder="Enter a query..."
          className="flex-1 rounded-md border border-stone-700 bg-stone-800 px-3 py-2 text-sm text-stone-100 placeholder:text-stone-500 disabled:opacity-50"
        />
        <input
          type="number"
          min={1}
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          className="w-20 rounded-md border border-stone-700 bg-stone-800 px-2 py-2 text-sm text-stone-100"
        />
        <button
          onClick={handleSearch}
          disabled={!activeSpace || isSearching || !query.trim()}
          className="rounded-md bg-stone-100 px-4 py-2 text-sm font-medium text-stone-900 hover:bg-white disabled:opacity-50"
        >
          {isSearching ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex-1 space-y-3 overflow-y-auto">
        {results.length === 0 && !isSearching && !error && (
          <p className="text-sm text-stone-500">No results yet.</p>
        )}
        {results.map((result) => (
          <SearchResultCard key={`${result.rank}-${result.filepath}`} result={result} />
        ))}
      </div>
    </div>
  )
}