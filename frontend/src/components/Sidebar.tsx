import { NavLink } from 'react-router-dom'
import { SpaceSelector } from './SpaceSelector'

const linkBaseClasses = 'block rounded-md px-3 py-2 text-sm font-medium transition-colors'
const linkInactiveClasses = 'text-slate-300 hover:bg-slate-800 hover:text-white'
const linkActiveClasses = 'bg-slate-800 text-white'

export function Sidebar() {
  return (
    <aside className="flex h-full w-64 flex-col gap-6 bg-slate-900 p-4">
      <div className="text-lg font-semibold text-white">Personal Knowledge Engine</div>

      <SpaceSelector />

      <nav className="flex flex-col gap-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `${linkBaseClasses} ${isActive ? linkActiveClasses : linkInactiveClasses}`
          }
        >
          Chat
        </NavLink>
        <NavLink
          to="/sync"
          className={({ isActive }) =>
            `${linkBaseClasses} ${isActive ? linkActiveClasses : linkInactiveClasses}`
          }
        >
          Sync
        </NavLink>
        <NavLink
          to="/search"
          className={({ isActive }) =>
            `${linkBaseClasses} ${isActive ? linkActiveClasses : linkInactiveClasses}`
          }
        >
          Search (debug)
        </NavLink>
      </nav>
    </aside>
  )
}