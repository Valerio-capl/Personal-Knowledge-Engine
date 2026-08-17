import { SpaceSelector } from '../components/SpaceSelector'
import { SyncBox } from '../components/SyncBox'
import { SearchDebugLink } from '../components/SearchDebugLink'
import { ChatPanel } from '../components/ChatPanel'

export function WorkspacePage() {
  return (
    <div className="flex h-full gap-8 p-8">
      <div className="flex w-[30rem] flex-shrink-0 flex-col gap-4">
        <SpaceSelector />
        <SyncBox />
        <SearchDebugLink />
      </div>

      <div className="flex max-w-6xl flex-1 flex-col overflow-hidden rounded-lg border border-stone-800 bg-stone-900">
        <ChatPanel />
      </div>
    </div>
  )
}