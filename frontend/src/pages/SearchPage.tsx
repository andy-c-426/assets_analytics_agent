import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import type { AssetSearchResult } from '../api/types';
import styles from './SearchPage.module.css';

const POPULAR = ['AAPL', 'MSFT', '0700.HK', '300502.SZ', '7203.T', '^GSPC'];

export default function SearchPage() {
  const navigate = useNavigate();

  function handleSelect(result: AssetSearchResult) {
    navigate(`/asset/${encodeURIComponent(result.symbol)}`);
  }

  function handleChip(symbol: string) {
    navigate(`/asset/${encodeURIComponent(symbol)}`);
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heroTitle}>Analyze Any Asset, Globally</h1>
      <p className={styles.heroSub}>
        Real-time data · AI-powered insights
      </p>
      <SearchBar onSelect={handleSelect} />
      <div className={styles.chips}>
        {POPULAR.map((s) => (
          <button key={s} className={styles.chip} onClick={() => handleChip(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
