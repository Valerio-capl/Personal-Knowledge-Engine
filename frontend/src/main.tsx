import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { SpaceProvider } from './context/SpaceContext'
import { GenerationProvider } from './context/GenerationContext'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <SpaceProvider>
        <GenerationProvider>
          <App />
        </GenerationProvider>
      </SpaceProvider>
    </BrowserRouter>
  </StrictMode>,
)