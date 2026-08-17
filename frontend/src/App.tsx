import { Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { WorkspacePage } from './pages/WorkspacePage'
import { SearchPage } from './pages/SearchPage'

function App() {
  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-stone-950">
      <Header />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<WorkspacePage />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App