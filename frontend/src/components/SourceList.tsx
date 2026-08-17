import { useState } from 'react'
import type { SourceItem } from '../types/api'

export function SourceList({ sources }: { sources: SourceItem[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className="mt-2 border-t border-stone-700 pt-2">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="text-xs font-medium text-stone-400 hover:text-stone-200"
      >
        {isOpen ? '▾' : '▸'} Show sources ({sources.length})
      </button>

      {isOpen && (
        <ul className="mt-2 flex flex-col gap-1">
          {sources.map((source) => (
            <li key={source.id} className="text-xs text-stone-400">
              [{source.id}] {source.file}{' '}
              <span className="text-stone-500">(score: {source.score.toFixed(2)})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}