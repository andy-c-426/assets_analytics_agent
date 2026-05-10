import { useState } from 'react';
import { useLocale } from '../i18n/LocaleContext';
import type { AssetDetail as AssetDetailType } from '../api/types';
import styles from './AssetDetail.module.css';

const DESC_PREVIEW_LENGTH = 200;

function fmt(n?: number): string {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

export default function AssetDetail({ asset }: { asset: AssetDetailType }) {
  const { t } = useLocale();
  const { profile, price, metrics } = asset;
  const isPositive = (price.change ?? 0) >= 0;
  const [descExpanded, setDescExpanded] = useState(false);
  const isLongDesc = (profile.description?.length ?? 0) > DESC_PREVIEW_LENGTH;

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{profile.name}</h1>
          <div className={styles.subtitle}>
            {asset.symbol} · {profile.sector || '—'} · {profile.country || '—'}
          </div>
        </div>
        <div className={styles.price}>
          <div className={styles.priceValue}>
            {price.current.toLocaleString()}{' '}
            <span className={styles.priceCurrency}>{price.currency}</span>
          </div>
          {price.change != null && (
            <div className={isPositive ? styles.changeUp : styles.changeDown}>
              {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct?.toFixed(2)}%)
            </div>
          )}
        </div>
      </div>

      {profile.description && (
        <div className={styles.description}>
          <p>
            {isLongDesc && !descExpanded
              ? profile.description.slice(0, DESC_PREVIEW_LENGTH) + '...'
              : profile.description}
          </p>
          {isLongDesc && (
            <button
              className={styles.moreBtn}
              onClick={() => setDescExpanded((v) => !v)}
            >
              {descExpanded ? t('detail.showLess') : t('detail.showMore')}
            </button>
          )}
        </div>
      )}

      <div className={styles.metricsGrid}>
        <Metric label={t('detail.marketCap')} value={fmt(profile.market_cap)} />
        <Metric label={t('detail.peRatio')} value={metrics.pe_ratio?.toFixed(2)} />
        <Metric label={t('detail.pbRatio')} value={metrics.pb_ratio?.toFixed(2)} />
        <Metric label={t('detail.eps')} value={metrics.eps != null ? `$${metrics.eps.toFixed(2)}` : undefined} />
        <Metric label={t('detail.dividendYield')} value={metrics.dividend_yield != null ? `${(metrics.dividend_yield * 100).toFixed(2)}%` : undefined} />
        <Metric label={t('detail.beta')} value={metrics.beta?.toFixed(2)} />
        <Metric label={t('detail.52wHigh')} value={metrics.fifty_two_week_high?.toFixed(2)} />
        <Metric label={t('detail.52wLow')} value={metrics.fifty_two_week_low?.toFixed(2)} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div className={styles.metric}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue}>{value || '—'}</div>
    </div>
  );
}
