import { useState, useEffect, useRef } from 'react';
import { searchAssets } from '../api/client';
import type { AssetSearchResult } from '../api/types';

export default function SearchBar({ onSelect }: { onSelect: (r: AssetSearchResult) => void }) {
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
    <div ref={ref} style={{ position: 'relative', maxWidth: 560, margin: '0 auto' }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search ticker or name (e.g. AAPL, 0700.HK, 300502.SZ)..."
        style={{
          width: '100%', padding: '12px 16px', fontSize: 16, borderRadius: 8,
          border: '1px solid #ccc', outline: 'none', boxSizing: 'border-box',
        }}
      />
      {loading && <div style={{ padding: '8px 16px', fontSize: 13, color: '#888' }}>Searching...</div>}
      {open && results.length > 0 && (
        <ul style={{
          position: 'absolute', top: '100%', left: 0, right: 0,
          background: 'white', border: '1px solid #e0e0e0', borderRadius: 8,
          margin: '4px 0 0', padding: 0, listStyle: 'none', zIndex: 50,
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)', maxHeight: 360, overflowY: 'auto',
        }}>
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => {
                onSelect(r);
                setQuery(r.symbol);
                setOpen(false);
              }}
              style={{
                padding: '10px 16px', cursor: 'pointer', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '1px solid #f0f0f0',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{r.symbol}</div>
                <div style={{ fontSize: 12, color: '#666' }}>{r.name}</div>
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                <span style={{
                  padding: '2px 6px', borderRadius: 4, fontSize: 11,
                  background: r.type === 'etf' ? '#e8f5e9' : '#e3f2fd',
                  color: r.type === 'etf' ? '#2e7d32' : '#1565c0',
                }}>
                  {r.type.toUpperCase()}
                </span>
                <span style={{ marginLeft: 6 }}>{r.exchange}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
