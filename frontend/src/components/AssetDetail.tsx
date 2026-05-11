import { useState } from 'react';
import { useLocale } from '../i18n/LocaleContext';
import type { AssetDetail as AssetDetailType } from '../api/types';
import type { MarketData } from './widgetParsers';
import styles from './AssetDetail.module.css';

const DESC_PREVIEW_LENGTH = 200;

function fmtNum(n?: number): string {
  if (n == null) return '—';
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

interface Props {
  asset: AssetDetailType;
  marketData: MarketData | null;
}

export default function AssetDetail({ asset, marketData }: Props) {
  const { t } = useLocale();
  const { profile, price, metrics } = asset;
  const isPositive = (price.change ?? 0) >= 0;
  const changeColor = isPositive ? 'var(--green)' : 'var(--red)';
  const [descExpanded, setDescExpanded] = useState(false);
  const isLongDesc = (profile.description?.length ?? 0) > DESC_PREVIEW_LENGTH;

  // Enrich with market data when available
  const showOHLC = marketData?.price.open || marketData?.price.high;
  const showWeek52Bar = marketData?.week52 && (marketData.week52.high || marketData.week52.low);
  const showExtraFundamentals = marketData && marketData.fundamentals.length > 0;
  const showVolume = marketData && marketData.volume.length > 0;

  // Build valuation rows: prefer Futu data but fall back to asset metrics
  const valuationRows: { label: string; value: string }[] = [];
  if (marketData) {
    for (const kv of marketData.valuation) {
      valuationRows.push(kv);
    }
  }
  // Fill gaps from asset metrics
  const hasLabel = (l: string) => valuationRows.some(r => r.label.toLowerCase().includes(l.toLowerCase()));
  if (!hasLabel('P/E') && metrics.pe_ratio != null) valuationRows.push({ label: 'P/E', value: metrics.pe_ratio.toFixed(2) });
  if (!hasLabel('P/B') && metrics.pb_ratio != null) valuationRows.push({ label: 'P/B', value: metrics.pb_ratio.toFixed(2) });
  if (!hasLabel('Market Cap') && profile.market_cap) valuationRows.push({ label: 'Market Cap', value: fmtNum(profile.market_cap) });
  if (!hasLabel('EPS') && metrics.eps != null) valuationRows.push({ label: 'EPS', value: `$${metrics.eps.toFixed(2)}` });
  if (!hasLabel('Dividend') && metrics.dividend_yield != null) valuationRows.push({ label: 'Dividend Yield', value: `${(metrics.dividend_yield * 100).toFixed(2)}%` });

  const fundamentalsRows = marketData?.fundamentals ?? [];
  if (!fundamentalsRows.length && metrics.beta != null) {
    fundamentalsRows.push({ label: 'Beta', value: metrics.beta.toFixed(2) });
  }

  // 52W data
  const week52High = marketData?.week52?.high || metrics.fifty_two_week_high?.toFixed(2) || '';
  const week52Low = marketData?.week52?.low || metrics.fifty_two_week_low?.toFixed(2) || '';

  // Current price for range bar
  const currentPrice = price.current;
  const highNum = parseFloat(week52High);
  const lowNum = parseFloat(week52Low);
  const rangePct = highNum && lowNum && highNum !== lowNum
    ? ((currentPrice - lowNum) / (highNum - lowNum)) * 100
    : 50;

  return (
    <div className={styles.card}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.name}>{profile.name}</h1>
          <div className={styles.meta}>
            <span className={styles.symbol}>{asset.symbol}</span>
            {profile.sector && <span className={styles.sectorBadge}>{profile.sector}</span>}
            {profile.country && <span className={styles.country}>{profile.country}</span>}
            {marketData?.asOf && <span className={styles.asOf}>As of {marketData.asOf}</span>}
          </div>
        </div>
      </div>

      {/* Price card */}
      <div className={styles.priceCard}>
        <span className={styles.priceValue}>
          {price.current.toLocaleString()}
          <span className={styles.priceCurrency}> {price.currency}</span>
        </span>
        {price.change != null && (
          <span className={styles.priceChange} style={{ color: changeColor }}>
            {isPositive ? '+' : ''}{price.change.toFixed(2)} ({isPositive ? '+' : ''}{price.change_pct?.toFixed(2)}%)
          </span>
        )}
      </div>

      {/* OHLC grid — only from Futu */}
      {showOHLC && (
        <div className={styles.ohlcGrid}>
          {marketData!.price.open && <OhlcCell label="Open" value={marketData!.price.open} />}
          {marketData!.price.high && <OhlcCell label="High" value={marketData!.price.high} />}
          {marketData!.price.low && <OhlcCell label="Low" value={marketData!.price.low} />}
          {marketData!.price.prevClose && <OhlcCell label="Prev Close" value={marketData!.price.prevClose} />}
        </div>
      )}

      {/* Description */}
      {profile.description && (
        <div className={styles.description}>
          <p>
            {isLongDesc && !descExpanded
              ? profile.description.slice(0, DESC_PREVIEW_LENGTH) + '...'
              : profile.description}
          </p>
          {isLongDesc && (
            <button className={styles.moreBtn} onClick={() => setDescExpanded(v => !v)}>
              {descExpanded ? t('detail.showLess') : t('detail.showMore')}
            </button>
          )}
        </div>
      )}

      {/* Valuation section */}
      {valuationRows.length > 0 && (
        <Section title="Valuation">
          <div className={styles.kvGrid}>
            {valuationRows.map((kv, i) => <KvRow key={i} {...kv} />)}
          </div>
        </Section>
      )}

      {/* Volume section */}
      {showVolume && (
        <Section title="Volume">
          <div className={styles.kvGrid}>
            {marketData!.volume.map((kv, i) => <KvRow key={i} {...kv} />)}
          </div>
        </Section>
      )}

      {/* Fundamentals section */}
      {showExtraFundamentals && (
        <Section title="Fundamentals">
          <div className={styles.kvGrid}>
            {marketData!.fundamentals.map((kv, i) => <KvRow key={i} {...kv} />)}
          </div>
        </Section>
      )}

      {/* 52-Week Range */}
      {(showWeek52Bar || week52High || week52Low) && (
        <Section title="52-Week Range">
          <div className={styles.rangeBar}>
            <span className={styles.rangeLabel}>{week52Low}</span>
            <div className={styles.rangeTrack}>
              <div
                className={styles.rangeFill}
                style={{ left: `${Math.min(100, Math.max(0, rangePct))}%` }}
              />
            </div>
            <span className={styles.rangeLabel}>{week52High}</span>
          </div>
        </Section>
      )}

      {/* Stock info footer */}
      {marketData?.stockInfo.length ? (
        <div className={styles.footer}>
          {marketData.stockInfo.map((kv, i) => (
            <span key={i} className={styles.footerItem}>
              {kv.label}: <strong>{kv.value}</strong>
            </span>
          ))}
        </div>
      ) : profile.website ? (
        <div className={styles.footer}>
          <span className={styles.footerItem}>
            Website: <strong>{profile.website}</strong>
          </span>
        </div>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                    */
/* ------------------------------------------------------------------ */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className={styles.section}>
      <h4 className={styles.sectionTitle}>{title}</h4>
      {children}
    </div>
  );
}

function OhlcCell({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.ohlcCell}>
      <span className={styles.ohlcLabel}>{label}</span>
      <span className={styles.ohlcValue}>{value}</span>
    </div>
  );
}

function KvRow({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.kvRow}>
      <span className={styles.kvLabel}>{label}</span>
      <span className={styles.kvValue}>{value}</span>
    </div>
  );
}
