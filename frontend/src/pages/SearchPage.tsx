import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import type { AssetSearchResult } from '../api/types';

export default function SearchPage() {
  const navigate = useNavigate();

  function handleSelect(result: AssetSearchResult) {
    navigate(`/asset/${encodeURIComponent(result.symbol)}`);
  }

  return (
    <div style={{ maxWidth: 600, margin: '80px auto 0', padding: '0 20px', textAlign: 'center' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Asset Analytics</h1>
      <p style={{ color: '#666', marginBottom: 32 }}>
        Search any stock or ETF across global markets. Get AI-powered analysis.
      </p>
      <SearchBar onSelect={handleSelect} />
    </div>
  );
}
