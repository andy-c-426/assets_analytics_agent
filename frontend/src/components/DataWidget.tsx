import { useLocale } from '../i18n/LocaleContext';
import Skeleton from './Skeleton';
import {
  parseMarketData,
  parseMacroResearch,
  parseSentimentNews,
  type MarketData,
  type MacroResearch,
  type SentimentNews,
} from './widgetParsers';
import styles from './DataWidget.module.css';

interface Props {
  category: 'market_data' | 'macro_research' | 'sentiment_news';
  data: string | null;
  loading: boolean;
}

const CATEGORY_KEYS: Record<Props['category'], string> = {
  market_data: 'widget.marketData',
  macro_research: 'widget.macroResearch',
  sentiment_news: 'widget.sentimentNews',
};

const ACCENT: Record<Props['category'], string> = {
  market_data: 'var(--green)',
  macro_research: 'var(--blue, #3b82f6)',
  sentiment_news: 'var(--purple, #a855f7)',
};

/* ------------------------------------------------------------------ */
/*  Market Data Widget                                                */
/* ------------------------------------------------------------------ */

function MarketDataWidget({ parsed }: { parsed: MarketData }) {
  const isPositive = parsed.price.change.startsWith('+');
  const changeColor = isPositive ? 'var(--green)' : parsed.price.change.startsWith('-') ? 'var(--red)' : 'var(--text-muted)';

  return (
    <div className={styles.marketData}>
      {/* Header */}
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>{parsed.name}</div>
        <div className={styles.mdSymbol}>{parsed.symbol}</div>
        {parsed.asOf && <div className={styles.mdAsOf}>As of {parsed.asOf}</div>}
      </div>

      {/* Price card */}
      <div className={styles.priceCard}>
        <span className={styles.priceValue}>{parsed.price.current}</span>
        {(parsed.price.change || parsed.price.changePct) && (
          <span className={styles.priceChange} style={{ color: changeColor }}>
            {parsed.price.change} ({parsed.price.changePct}%)
          </span>
        )}
      </div>

      {/* OHLC mini grid */}
      {(parsed.price.open || parsed.price.high) && (
        <div className={styles.ohlcGrid}>
          {parsed.price.open && <OhlcCell label="Open" value={parsed.price.open} />}
          {parsed.price.high && <OhlcCell label="High" value={parsed.price.high} />}
          {parsed.price.low && <OhlcCell label="Low" value={parsed.price.low} />}
          {parsed.price.prevClose && <OhlcCell label="Prev Close" value={parsed.price.prevClose} />}
        </div>
      )}

      {/* Valuation grid */}
      {parsed.valuation.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Valuation</h4>
          <div className={styles.kvGrid}>
            {parsed.valuation.map((kv, i) => (
              <KvRow key={i} {...kv} />
            ))}
          </div>
        </div>
      )}

      {/* Volume */}
      {parsed.volume.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Volume</h4>
          <div className={styles.kvGrid}>
            {parsed.volume.slice(0, 2).map((kv, i) => (
              <KvRow key={i} {...kv} />
            ))}
          </div>
        </div>
      )}

      {/* Fundamentals */}
      {parsed.fundamentals.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Fundamentals</h4>
          <div className={styles.kvGrid}>
            {parsed.fundamentals.map((kv, i) => (
              <KvRow key={i} {...kv} />
            ))}
          </div>
        </div>
      )}

      {/* 52-Week Range */}
      {parsed.week52 && (parsed.week52.high || parsed.week52.low) && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>52-Week Range</h4>
          <div className={styles.rangeBar}>
            <span className={styles.rangeLabel}>{parsed.week52.low}</span>
            <div className={styles.rangeTrack}>
              <div
                className={styles.rangeFill}
                style={{
                  left: `${parsed.week52.low && parsed.week52.high && parsed.price.current
                    ? ((parseFloat(parsed.price.current) - parseFloat(parsed.week52.low)) /
                       (parseFloat(parsed.week52.high) - parseFloat(parsed.week52.low))) * 100
                    : 50}%`,
                }}
              />
            </div>
            <span className={styles.rangeLabel}>{parsed.week52.high}</span>
          </div>
        </div>
      )}

      {/* Stock Info footer */}
      {parsed.stockInfo.length > 0 && (
        <div className={styles.footer}>
          {parsed.stockInfo.map((kv, i) => (
            <span key={i} className={styles.footerItem}>
              {kv.label}: <strong>{kv.value}</strong>
            </span>
          ))}
        </div>
      )}
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

/* ------------------------------------------------------------------ */
/*  Macro Research Widget                                             */
/* ------------------------------------------------------------------ */

function MacroResearchWidget({ parsed }: { parsed: MacroResearch }) {
  return (
    <div className={styles.macroResearch}>
      {/* Header */}
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>{parsed.region}</div>
        <div className={styles.mdSymbol}>{parsed.index}</div>
      </div>

      {/* Sector card */}
      {(parsed.sector || parsed.industry) && (
        <div className={styles.sectorCard}>
          {parsed.sector && <span className={styles.sectorBadge}>{parsed.sector}</span>}
          {parsed.industry && <span className={styles.industryText}>{parsed.industry}</span>}
          {parsed.sectorEtf && (
            <div className={styles.etfRow}>
              <span className={styles.etfSymbol}>{parsed.sectorEtf.symbol}</span>
              <span className={styles.etfPrice}>${parsed.sectorEtf.price}</span>
            </div>
          )}
        </div>
      )}

      {/* Macro news items */}
      {parsed.newsItems.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Market Outlook</h4>
          <ul className={styles.newsList}>
            {parsed.newsItems.map((item, i) => (
              <li key={i} className={styles.newsItem}>
                <span className={styles.newsDate}>{item.date}</span>
                <span className={styles.newsTitle}>{item.title}</span>
                <span className={styles.newsSource}>{item.source}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Note */}
      {parsed.note && <p className={styles.note}>{parsed.note}</p>}

      {!parsed.sector && !parsed.newsItems.length && (
        <p className={styles.placeholder}>Macro data temporarily limited. Sector context shown when available.</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Sentiment News Widget                                             */
/* ------------------------------------------------------------------ */

function SentimentNewsWidget({ parsed }: { parsed: SentimentNews }) {
  return (
    <div className={styles.sentimentNews}>
      {/* Header */}
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>{parsed.source}</div>
        <div className={styles.mdAsOf}>
          {parsed.period} &middot; {parsed.articleCount} articles
        </div>
      </div>

      {/* Category groups */}
      {parsed.categories.map((cat, ci) => (
        <div key={ci} className={styles.section}>
          <h4 className={styles.sectionTitle}>
            {cat.name}
            <span className={styles.catCount}>{cat.count}</span>
          </h4>
          {cat.articles.slice(0, 3).map((a, ai) => (
            <div key={ai} className={styles.articleCard}>
              <div className={styles.articleMeta}>
                <span className={styles.articleDate}>{a.date}</span>
                <span className={styles.articleSource}>{a.source}</span>
              </div>
              <div className={styles.articleHeadline}>{a.headline}</div>
              {a.summary && <div className={styles.articleSummary}>{a.summary.slice(0, 180)}{a.summary.length > 180 ? '...' : ''}</div>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Widget                                                       */
/* ------------------------------------------------------------------ */

export default function DataWidget({ category, data, loading }: Props) {
  const { t } = useLocale();

  const renderBody = () => {
    if (loading) {
      return (
        <div className={styles.skeletonWrap}>
          <Skeleton height={14} style={{ marginBottom: 10 }} />
          <Skeleton height={14} width="70%" style={{ marginBottom: 10 }} />
          <Skeleton height={14} width="50%" style={{ marginBottom: 10 }} />
          <Skeleton height={14} width="60%" />
        </div>
      );
    }

    if (!data) {
      return <p className={styles.placeholder}>{t('widget.unavailable')}</p>;
    }

    if (category === 'market_data') {
      const parsed = parseMarketData(data);
      if (parsed) return <MarketDataWidget parsed={parsed} />;
    }

    if (category === 'macro_research') {
      const parsed = parseMacroResearch(data);
      if (parsed) return <MacroResearchWidget parsed={parsed} />;
    }

    if (category === 'sentiment_news') {
      const parsed = parseSentimentNews(data);
      if (parsed) return <SentimentNewsWidget parsed={parsed} />;
    }

    // Fallback: render raw text cleanly
    return <pre className={styles.fallbackPre}>{data}</pre>;
  };

  return (
    <div className={styles.widget} style={{ borderTop: `3px solid ${ACCENT[category]}` }}>
      <h3 className={styles.title}>{t(CATEGORY_KEYS[category])}</h3>
      <div className={styles.body}>{renderBody()}</div>
    </div>
  );
}
