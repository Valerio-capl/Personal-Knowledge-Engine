import { useGenerationContext } from '../context/GenerationContext'
import { GENERATION_PROVIDERS, GENERATION_MODELS, type GenerationProviderName } from '../config/generationModels'

export function GenerationSelector() {
  const { provider, model, setProvider, setModel } = useGenerationContext()

  function handleProviderChange(next: GenerationProviderName) {
    setProvider(next)
    setModel(GENERATION_MODELS[next][0])
  }

  return (
    <div className="rounded-lg border border-stone-800 bg-stone-900 p-4">
      <h2 className="text-sm font-semibold text-stone-100">Generation Model</h2>
      <p className="mt-1 text-xs text-stone-500">Used to generate answers in the chat.</p>

      <div className="mt-3 flex gap-2">
        <select
          value={provider}
          onChange={(e) => handleProviderChange(e.target.value as GenerationProviderName)}
          className="flex-1 rounded-md border border-stone-700 bg-stone-800 px-2 py-1.5 text-sm text-stone-100"
        >
          {GENERATION_PROVIDERS.map((p) => (
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
          {GENERATION_MODELS[provider].map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}