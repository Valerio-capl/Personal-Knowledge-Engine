import type { SearchResultResponse } from '../types/api'

export function SearchResultCard({ result }: { result: SearchResultResponse }) {
  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900 p-4">
      <div className="flex items-center justify-between text-xs text-stone-500">
        <span>rank #{result.rank}</span>
        <span className="font-mono">score: {result.score.toFixed(4)}</span>
      </div>
      <p className="mt-2 whitespace-pre-wrap text-sm text-stone-200">{result.content}</p>
      <p className="mt-2 truncate text-xs text-stone-500">{result.filepath}</p>
    </div>
  )
}