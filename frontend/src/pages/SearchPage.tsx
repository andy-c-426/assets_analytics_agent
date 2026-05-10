import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { useLocale } from '../i18n/LocaleContext';
import type { AssetSearchResult } from '../api/types';
import styles from './SearchPage.module.css';

const POPULAR = ['AAPL', 'MSFT', '0700.HK', '300502.SZ', '7203.T', '^GSPC'];

export default function SearchPage() {
  const navigate = useNavigate();
  const { t } = useLocale();

  function handleSelect(result: AssetSearchResult) {
    navigate(`/asset/${encodeURIComponent(result.symbol)}`);
  }

  function handleChip(symbol: string) {
    navigate(`/asset/${encodeURIComponent(symbol)}`);
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heroTitle}>{t('home.title')}</h1>
      <p className={styles.heroSub}>
        {t('home.subtitle')}
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
