import { NavLink } from 'react-router-dom'

export function Header() {
  return (
    <header className="flex h-14 w-full flex-shrink-0 items-center border-b border-stone-800 bg-stone-900 px-6">
      <NavLink to="/" className="text-base font-semibold tracking-wide text-stone-100">
        Personal Knowledge Engine
      </NavLink>
    </header>
  )
}