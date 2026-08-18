import { useState } from 'react'
import { runSync } from '../api/sync'
import { ApiError } from '../api/client'
import { useSpaceContext } from '../context/SpaceContext'
import { EMBEDDING_PROVIDERS, EMBEDDING_MODELS, type EmbeddingProviderName } from '../config/embeddingModels'
import type { SyncResponse } from '../types/api'

export function SyncBox() {
  const { refreshSpaces } = useSpaceContext()

  const [provider, setProvider] = useState<EmbeddingProviderName>('ollama')
  const [model, setModel] = useState(EMBEDDING_MODELS.ollama[0])
  const [folderPath, setFolderPath] = useState('')
  const [isSyncing, setIsSyncing] = useState(false)
  const [report, setReport] = useState<SyncResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  function handleProviderChange(next: EmbeddingProviderName) {
    setProvider(next)
    setModel(EMBEDDING_MODELS[next][0])
  }

  async function handleSync() {
    const trimmedPath = folderPath.trim()
    if (!trimmedPath) return

    setIsSyncing(true)
    setError(null)
    setReport(null)

    try {
      const result = await runSync({
        folder_path: trimmedPath,
        provider_name: provider,
        model_name: model,
      })
      setReport(result)
      await refreshSpaces()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900 p-4">
      <h2 className="text-sm font-semibold text-stone-100">Sync Documents</h2>
      <p className="mt-1 text-xs text-stone-500">Index a local folder into an embedding space.</p>

      <div className="mt-3 flex gap-2">
        <select
          value={provider}
          onChange={(e) => handleProviderChange(e.target.value as EmbeddingProviderName)}
          className="flex-1 rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100"
        >
          {EMBEDDING_PROVIDERS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="flex-1 rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100"
        >
          {EMBEDDING_MODELS[provider].map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      <input
        type="text"
        value={folderPath}
        onChange={(e) => setFolderPath(e.target.value)}
        placeholder="C:\path\to\your\folder"
        className="mt-2 w-full rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100 placeholder:text-stone-500"
      />

      <button
        onClick={handleSync}
        disabled={isSyncing || !folderPath.trim()}
        className="mt-3 w-full rounded-md bg-stone-100 px-3 py-2 text-sm font-medium text-stone-900 hover:bg-white disabled:opacity-50"
      >
        {isSyncing ? 'Syncing...' : 'Sync'}
      </button>

      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}

      {report && (
        <div className="mt-3 space-y-1 text-xs text-stone-400">
          <p>Synced: {report.synced.length}</p>
          <p>Skipped: {report.skipped.length}</p>
          <p>Deleted: {report.deleted.length}</p>
          <p>Failed: {report.failed.length}</p>
          {report.failed.length > 0 && (
            <ul className="mt-1 space-y-0.5 text-red-400">
              {report.failed.map(([file, reason]) => (
                <li key={file}>
                  {file}: {reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}