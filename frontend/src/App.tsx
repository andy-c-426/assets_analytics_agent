// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SearchPage from './pages/SearchPage';
import AssetPage from './pages/AssetPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/asset/:symbol" element={<AssetPage />} />
      </Routes>
    </BrowserRouter>
  );
}
