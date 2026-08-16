import { useSpaceContext } from '../context/SpaceContext'

export function SpaceSelector() {
  const { spaces, activeSpace, setActiveSpace, isLoading, error } = useSpaceContext()

  if (isLoading) {
    return <div className="text-sm text-slate-400">Loading spaces...</div>
  }

  if (error) {
    return <div className="text-sm text-red-400">Error: {error}</div>
  }

  if (spaces.length === 0) {
    return <div className="text-sm text-slate-400">No spaces yet — run a sync first.</div>
  }

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="space-selector" className="text-xs font-medium text-slate-400">
        Knowledge Space
      </label>
      <select
        id="space-selector"
        className="rounded-md border border-slate-700 bg-slate-800 px-2 py-1.5 text-sm text-white"
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
    </div>
  )
}