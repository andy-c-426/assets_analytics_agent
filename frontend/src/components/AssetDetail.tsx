// frontend/src/components/AssetDetail.tsx
import type { AssetDetail as AssetDetailType } from '../api/types';

function fmt(n?: number): string {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return n.toLocaleString();
}

export default function AssetDetail({ asset }: { asset: AssetDetailType }) {
  const { profile, price, metrics } = asset;
  const isPositive = (price.change ?? 0) >= 0;

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24 }}>{profile.name}</h2>
          <div style={{ color: '#888', fontSize: 14, marginTop: 2 }}>
            {asset.symbol} · {profile.sector || '—'} · {profile.country || '—'}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 28, fontWeight: 700 }}>
            {price.current.toLocaleString()} <span style={{ fontSize: 14, color: '#888' }}>{price.currency}</span>
          </div>
          {price.change != null && (
            <div style={{ color: isPositive ? '#2e7d32' : '#c62828', fontSize: 14, fontWeight: 500 }}>
              {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct?.toFixed(2)}%)
            </div>
          )}
        </div>
      </div>

      {profile.description && (
        <p style={{ color: '#555', lineHeight: 1.6, marginTop: 16, fontSize: 14 }}>{profile.description}</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: 12, marginTop: 20 }}>
        <Metric label="Market Cap" value={fmt(profile.market_cap)} />
        <Metric label="P/E Ratio" value={metrics.pe_ratio?.toFixed(2)} />
        <Metric label="P/B Ratio" value={metrics.pb_ratio?.toFixed(2)} />
        <Metric label="EPS" value={metrics.eps != null ? `$${metrics.eps.toFixed(2)}` : undefined} />
        <Metric label="Dividend Yield" value={metrics.dividend_yield != null ? `${(metrics.dividend_yield * 100).toFixed(2)}%` : undefined} />
        <Metric label="Beta" value={metrics.beta?.toFixed(2)} />
        <Metric label="52W High" value={metrics.fifty_two_week_high?.toFixed(2)} />
        <Metric label="52W Low" value={metrics.fifty_two_week_low?.toFixed(2)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div style={{ background: '#f9f9f9', padding: '10px 14px', borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: '#888' }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 2 }}>{value || '—'}</div>
    </div>
  );
}
