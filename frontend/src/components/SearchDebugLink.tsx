import { NavLink } from 'react-router-dom'

export function SearchDebugLink() {
  return (
    <NavLink
      to="/search"
      className="flex items-center justify-between rounded-lg border border-stone-800 bg-stone-900 px-4 py-3 text-sm font-medium text-stone-300 transition-colors hover:bg-stone-800 hover:text-stone-100"
    >
      Search (debug)
      <span aria-hidden="true">→</span>
    </NavLink>
  )
}