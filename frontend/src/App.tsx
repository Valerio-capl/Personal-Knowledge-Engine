import { Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { AskPage } from './pages/AskPage'
import { SyncPage } from './pages/SyncPage'
import { SearchPage } from './pages/SearchPage'

function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<AskPage />} />
          <Route path="/sync" element={<SyncPage />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App