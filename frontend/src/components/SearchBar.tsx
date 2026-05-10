import { useState, useEffect, useRef } from 'react';
import { searchAssets } from '../api/client';
import { useLocale } from '../i18n/LocaleContext';
import type { AssetSearchResult } from '../api/types';
import styles from './SearchBar.module.css';

export default function SearchBar({ onSelect }: { onSelect: (r: AssetSearchResult) => void }) {
  const { t } = useLocale();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AssetSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 1) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchAssets(query);
        setResults(data);
        setOpen(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className={styles.wrapper}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder={t('search.placeholder')}
        className={styles.input}
      />
      {loading && <div className={styles.searching}>{t('search.searching')}</div>}
      {open && results.length > 0 && (
        <ul className={styles.dropdown}>
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => {
                onSelect(r);
                setQuery(r.symbol);
                setOpen(false);
              }}
              className={styles.result}
            >
              <div>
                <div className={styles.symbol}>{r.symbol}</div>
                <div className={styles.name}>{r.name}</div>
              </div>
              <div className={styles.meta}>
                <span className={`${styles.tag} ${r.type === 'etf' ? styles.tagEtf : styles.tagStock}`}>
                  {r.type.toUpperCase()}
                </span>
                <span>{r.exchange}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
