import { useState } from 'react'

export function SyncBox() {
  const [folderPath, setFolderPath] = useState('')

  // TODO: wire this up to POST /sync and render the SyncReport.
  function handleSync() {
    console.log('sync requested for', folderPath)
  }

  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900 p-4">
      <h2 className="text-sm font-semibold text-stone-100">Sync Documents</h2>
      <p className="mt-1 text-xs text-stone-500">Index a local folder into the active space.</p>

      <input
        type="text"
        value={folderPath}
        onChange={(e) => setFolderPath(e.target.value)}
        placeholder="C:\path\to\your\folder"
        className="mt-3 w-full rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100 placeholder:text-stone-500"
      />

      <button
        onClick={handleSync}
        className="mt-3 w-full rounded-md bg-stone-100 px-3 py-2 text-sm font-medium text-stone-900 hover:bg-white"
      >
        Sync
      </button>
    </div>
  )
}