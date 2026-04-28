import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar     from './components/Sidebar'
import Topbar      from './components/Topbar'
import LandingPage from './pages/LandingPage'
import UploadPage  from './pages/UploadPage'
import HistoryPage from './pages/HistoryPage'
import ResultPage  from './pages/ResultPage'
import DocsPage    from './pages/DocsPage'
import HelpPage    from './pages/HelpPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <div className="content">
          <Topbar />
          <main>
            <Routes>
              <Route path="/"           element={<LandingPage />} />
              <Route path="/upload"     element={<UploadPage />} />
              <Route path="/history"    element={<HistoryPage />} />
              <Route path="/result/:id" element={<ResultPage />} />
              <Route path="/docs"       element={<DocsPage />} />
              <Route path="/help"       element={<HelpPage />} />
              <Route path="*"           element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
