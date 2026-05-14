import { useLocale } from '../i18n/LocaleContext';
import Skeleton from './Skeleton';
import {
  parseMarketData,
  parseMacroResearch,
  parseSentimentNews,
  parseCapitalFlow,
  parseCnMarketSentiment,
  parseUsFundamentals,
  type MarketData,
  type MacroResearch,
  type SentimentNews,
  type CapitalFlowData,
  type CnMarketSentiment,
  type UsFundamentals,
} from './widgetParsers';
import styles from './DataWidget.module.css';

interface Props {
  category: 'market_data' | 'macro_research' | 'sentiment_news' | 'capital_flow' | 'cn_sentiment' | 'us_fundamentals';
  data: string | null;
  loading: boolean;
}

const CATEGORY_KEYS: Record<Props['category'], string> = {
  market_data: 'widget.marketData',
  macro_research: 'widget.macroResearch',
  sentiment_news: 'widget.sentimentNews',
  capital_flow: 'widget.capitalFlow',
  cn_sentiment: 'widget.cnSentiment',
  us_fundamentals: 'widget.usFundamentals',
};

const ACCENT: Record<Props['category'], string> = {
  market_data: 'var(--green)',
  macro_research: 'var(--blue, #3b82f6)',
  sentiment_news: 'var(--purple, #a855f7)',
  capital_flow: 'var(--orange, #f97316)',
  cn_sentiment: 'var(--red)',
  us_fundamentals: 'var(--blue, #3b82f6)',
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
              <span className={styles.etfPrice}>{parsed.currency}{parsed.sectorEtf.price}</span>
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
      <div className={styles.snHeader}>
        <div className={styles.snSourceRow}>
          <span className={styles.snSourceBadge}>{parsed.source}</span>
          {parsed.period && (
            <span className={styles.snPeriod}>{parsed.period}</span>
          )}
        </div>
        <span className={styles.snCount}>{parsed.articleCount} articles</span>
      </div>

      {/* Category groups */}
      {parsed.categories.map((cat, ci) => (
        <div key={ci} className={styles.snCategory}>
          <div className={styles.snCatHeader}>
            <span className={styles.snCatDot} />
            <h4 className={styles.snCatName}>{cat.name}</h4>
            <span className={styles.snCatCount}>{cat.count}</span>
          </div>
          <div className={styles.snArticles}>
            {cat.articles.map((a, ai) => (
              <a
                key={ai}
                href={a.url || undefined}
                target="_blank"
                rel="noopener noreferrer"
                className={`${styles.snArticle} ${a.url ? styles.snArticleLink : ''}`}
              >
                <div className={styles.snArticleMeta}>
                  <span className={styles.snArticleDate}>{a.date}</span>
                  {a.source && <span className={styles.snArticleSource}>{a.source}</span>}
                  {a.url && <span className={styles.snExternalIcon}>&#8599;</span>}
                </div>
                <div className={styles.snArticleHeadline}>{a.headline}</div>
                {a.summary && (
                  <div className={styles.snArticleSummary}>
                    {a.summary.length > 200 ? a.summary.slice(0, 200) + '...' : a.summary}
                  </div>
                )}
              </a>
            ))}
          </div>
        </div>
      ))}

      {parsed.categories.length === 0 && (
        <p className={styles.placeholder}>No articles found for this period.</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Capital Flow Widget                                                */
/* ------------------------------------------------------------------ */

function CapitalFlowWidget({ parsed }: { parsed: CapitalFlowData }) {
  return (
    <div className={styles.capitalFlow}>
      {/* Header */}
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>Stock Connect</div>
        <div className={styles.mdSymbol}>{parsed.symbol}</div>
      </div>

      {/* Flow Summary */}
      {parsed.flowItems.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Capital Flow (沪深港通)</h4>
          <div className={styles.flowTable}>
            {parsed.flowItems.map((item, i) => {
              const isNorth = item.direction === 'Northbound';
              return (
                <div key={i} className={styles.flowRow}>
                  <div className={styles.flowRowTop}>
                    <span className={styles.flowBoard}>{item.board}</span>
                    <span className={isNorth ? styles.flowNorth : styles.flowSouth}>
                      {item.direction}
                    </span>
                  </div>
                  <div className={styles.flowRowMid}>
                    {item.netBuy && <span className={styles.flowMetric}>{item.netBuy}</span>}
                    {item.advancesDeclines && (
                      <span className={styles.flowAdv}>{item.advancesDeclines}</span>
                    )}
                  </div>
                  {item.indexName && (
                    <div className={styles.flowRowBot}>
                      <span>{item.indexName}</span>
                      <span className={parseFloat(item.indexChange) >= 0 ? styles.flowGreen : styles.flowRed}>
                        {item.indexChange}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Stock Holdings */}
      {parsed.holdings && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Stock Connect Holdings</h4>
          <div className={styles.kvGrid}>
            {parsed.holdings.date && <KvRow label="As of" value={parsed.holdings.date} />}
            {parsed.holdings.close && (
              <KvRow label="Close" value={`${parsed.holdings.close} (${parsed.holdings.change})`} />
            )}
            {parsed.holdings.value && <KvRow label="Holdings Value" value={parsed.holdings.value} />}
            {parsed.holdings.pct && <KvRow label="Holding %" value={parsed.holdings.pct} />}
            {parsed.holdings.chg1d && <KvRow label="Chg (1d)" value={parsed.holdings.chg1d} />}
            {parsed.holdings.chg5d && <KvRow label="Chg (5d)" value={parsed.holdings.chg5d} />}
          </div>
        </div>
      )}

      {parsed.flowItems.length === 0 && !parsed.holdings && (
        <p className={styles.placeholder}>No Stock Connect data available (may be outside trading hours).</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  CN Market Sentiment Widget                                         */
/* ------------------------------------------------------------------ */

function CnSentimentWidget({ parsed }: { parsed: CnMarketSentiment }) {
  return (
    <div className={styles.cnSentiment}>
      {/* Header */}
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>CN Market Sentiment</div>
        <div className={styles.mdSymbol}>{parsed.symbol}</div>
      </div>

      {/* Sector Flow */}
      {parsed.sectors.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Sector Flow (行业资金流向)</h4>
          <div className={styles.sectorFlowList}>
            {parsed.sectors.map((s, i) => (
              <div key={i} className={styles.sectorFlowRow}>
                <span className={styles.sectorFlowName}>{s.name}</span>
                <span className={s.type === 'inflow' ? styles.flowGreen : styles.flowRed}>
                  {s.netFlow}
                </span>
                <span className={styles.sectorFlowPct}>{s.pct}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dragon Tiger Board */}
      {parsed.lhb && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Dragon Tiger Board (龙虎榜)</h4>
          <div className={styles.kvGrid}>
            <KvRow label="Appearances" value={`${parsed.lhb.appearances} times`} />
            {parsed.lhb.cumulativeBuy && <KvRow label="Cumulative Buy" value={parsed.lhb.cumulativeBuy} />}
            {parsed.lhb.cumulativeSell && <KvRow label="Cumulative Sell" value={parsed.lhb.cumulativeSell} />}
          </div>
          {parsed.lhb.recent.length > 0 && (
            <div className={styles.lhbRecent}>
              <div className={styles.lhbRecentTitle}>Recent Appearances</div>
              {parsed.lhb.recent.slice(0, 3).map((r, i) => (
                <div key={i} className={styles.lhbItem}>
                  <span className={styles.lhbItemDate}>{r.date}</span>
                  <span className={styles.lhbItemClose}>{r.close}</span>
                  <span className={styles.lhbItemReason}>{r.reason}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Top Flow Leaders */}
      {parsed.topStocks.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Top Flow Leaders (主力净流入前5)</h4>
          <div className={styles.flowTable}>
            {parsed.topStocks.map((s, i) => (
              <div key={i} className={styles.leaderRow}>
                <span className={styles.leaderCode}>{s.code}</span>
                <span className={styles.leaderName}>{s.name}</span>
                <span className={styles.leaderPrice}>{s.price}</span>
                <span className={parseFloat(s.change) >= 0 ? styles.flowGreen : styles.flowRed}>
                  {s.change}
                </span>
                <span className={styles.leaderNet}>{s.netFlow}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {parsed.sectors.length === 0 && !parsed.lhb && parsed.topStocks.length === 0 && (
        <p className={styles.placeholder}>No market sentiment data available (may be outside trading hours).</p>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  US Fundamentals Widget                                             */
/* ------------------------------------------------------------------ */

function UsFundamentalsWidget({ parsed }: { parsed: UsFundamentals }) {
  return (
    <div className={styles.usFundamentals}>
      <div className={styles.mdHeader}>
        <div className={styles.mdName}>US Fundamentals</div>
        <div className={styles.mdSymbol}>{parsed.symbol}</div>
      </div>

      {/* Analyst Targets */}
      {parsed.analystTargets && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Analyst Consensus</h4>
          <div className={styles.kvGrid}>
            <KvRow label="Current" value={`$${parsed.analystTargets.current}`} />
            <KvRow label="Mean Target" value={`$${parsed.analystTargets.mean}`} />
            {parsed.analystTargets.premium && (
              <KvRow label="Premium" value={parsed.analystTargets.premium} />
            )}
            <KvRow
              label="Low / High"
              value={`$${parsed.analystTargets.low} - $${parsed.analystTargets.high}`}
            />
          </div>
        </div>
      )}

      {/* Recommendations */}
      {parsed.recommendations.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Recommendations</h4>
          <div className={styles.recBar}>
            {parsed.recommendations.map((r, i) => (
              <div key={i} className={styles.recItem}>
                <span className={styles.recLabel}>{r.label}</span>
                <span className={styles.recCount}>{r.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Institutional Ownership */}
      {parsed.ownershipSummary.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Ownership</h4>
          <div className={styles.kvGrid}>
            {parsed.ownershipSummary.map((kv, i) => (
              <KvRow key={i} label={kv.label} value={kv.value} />
            ))}
          </div>
        </div>
      )}

      {parsed.institutionalHolders.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Top Institutional Holders</h4>
          {parsed.institutionalHolders.map((h, i) => (
            <div key={i} className={styles.instRow}>
              <span className={styles.instName}>{h.holder}</span>
              <span className={styles.instShares}>{h.shares} shares</span>
              {h.pct && <span className={styles.instPct}>{h.pct}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Insider Transactions */}
      {parsed.insiderTrades.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Recent Insider Trades</h4>
          {parsed.insiderTrades.slice(0, 3).map((t, i) => (
            <div key={i} className={styles.insiderRow}>
              <span className={styles.insiderDate}>{t.date}</span>
              <span className={styles.insiderName}>{t.name}</span>
              <span className={styles.insiderTxn}>{t.transaction}</span>
              {t.value && <span className={styles.insiderValue}>${t.value}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Earnings Calendar */}
      {parsed.earnings.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Earnings Calendar</h4>
          {parsed.earnings.map((e, i) => (
            <div key={i} className={styles.earningsRow}>
              <span className={styles.earningsDate}>{e.date}</span>
              <span className={e.type === 'upcoming' ? styles.earningsUpcoming : styles.earningsPast}>
                {e.type === 'upcoming' ? 'Est.' : 'Past'}
              </span>
              {e.epsEstimate && <span className={styles.earningsEst}>Est: ${e.epsEstimate}</span>}
              {e.epsActual && <span className={styles.earningsAct}>Act: ${e.epsActual}</span>}
              {e.surprise && (
                <span className={e.surprise.startsWith('+') ? styles.flowGreen : styles.flowRed}>
                  {e.surprise}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* SEC Filings */}
      {parsed.secFilings.length > 0 && (
        <div className={styles.section}>
          <h4 className={styles.sectionTitle}>Recent SEC Filings</h4>
          {parsed.secFilings.slice(0, 3).map((f, i) => (
            <a
              key={i}
              href={f.url || undefined}
              target="_blank"
              rel="noopener noreferrer"
              className={`${styles.filingRow} ${f.url ? styles.filingLink : ''}`}
            >
              <span className={styles.filingDate}>{f.date}</span>
              <span className={styles.filingType}>{f.type}</span>
              {f.title && <span className={styles.filingTitle}>{f.title}</span>}
            </a>
          ))}
        </div>
      )}

      {!parsed.analystTargets && parsed.earnings.length === 0 && parsed.insiderTrades.length === 0 && (
        <p className={styles.placeholder}>No US fundamentals data available.</p>
      )}
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

    if (category === 'capital_flow') {
      const parsed = parseCapitalFlow(data);
      if (parsed) return <CapitalFlowWidget parsed={parsed} />;
    }

    if (category === 'cn_sentiment') {
      const parsed = parseCnMarketSentiment(data);
      if (parsed) return <CnSentimentWidget parsed={parsed} />;
    }

    if (category === 'us_fundamentals') {
      const parsed = parseUsFundamentals(data);
      if (parsed) return <UsFundamentalsWidget parsed={parsed} />;
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
