import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Topbar      from './components/Topbar.jsx'
import LandingPage from './pages/LandingPage.jsx'
import UploadPage  from './pages/UploadPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import ResultPage  from './pages/ResultPage.jsx'
import DocsPage    from './pages/DocsPage.jsx'
import HelpPage    from './pages/HelpPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <div className="shell">
        <Topbar />
        <Routes>
          <Route path="/"           element={<LandingPage />} />
          <Route path="/upload"     element={<UploadPage />} />
          <Route path="/history"    element={<HistoryPage />} />
          <Route path="/result/:id" element={<ResultPage />} />
          <Route path="/docs"       element={<DocsPage />} />
          <Route path="/help"       element={<HelpPage />} />
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
