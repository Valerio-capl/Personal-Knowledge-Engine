import { useSpaceContext } from '../context/SpaceContext'

export function SpaceSelector() {
  const { spaces, activeSpace, setActiveSpace, isLoading, error } = useSpaceContext()

  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900 p-4">
      <h2 className="text-sm font-semibold text-stone-100">Knowledge Space</h2>

      {isLoading && <p className="mt-2 text-sm text-stone-500">Loading spaces...</p>}
      {error && <p className="mt-2 text-sm text-red-400">Error: {error}</p>}
      {!isLoading && !error && spaces.length === 0 && (
        <p className="mt-2 text-sm text-stone-500">No spaces yet — run a sync first.</p>
      )}

      {!isLoading && spaces.length > 0 && (
        <select
          className="mt-2 w-full rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100"
          value={activeSpace?.space_id ?? ''}
          onChange={(e) => {
            const selected = spaces.find((s) => s.space_id === e.target.value)
            if (selected) setActiveSpace(selected)
          }}
        >
          {spaces.map((space) => (
            <option key={space.space_id} value={space.space_id}>
              {space.provider_name} / {space.model_name}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}