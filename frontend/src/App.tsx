import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { CommandCenterPage } from './pages/CommandCenterPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Legacy map route — redirect to command center */}
        <Route path="/map" element={<Navigate to="/command-center" replace />} />
        {/* New primary route */}
        <Route path="/command-center" element={<CommandCenterPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
