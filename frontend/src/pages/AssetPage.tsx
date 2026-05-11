import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAssetDetail, getMarketData, getMacroResearch, getSentimentNews } from '../api/client';
import AssetDetailComponent from '../components/AssetDetail';
import PriceChart from '../components/PriceChart';
import NewsList from '../components/NewsList';
import DataWidget from '../components/DataWidget';
import SettingsDialog, { loadSettings } from '../components/SettingsDialog';
import AnalyzePanel from '../components/AnalyzePanel';
import Skeleton from '../components/Skeleton';
import { useLocale } from '../i18n/LocaleContext';
import { parseMarketData } from '../components/widgetParsers';
import type { AssetDetail, AnalysisRequest } from '../api/types';
import styles from './AssetPage.module.css';

type WidgetData = {
  marketData: string | null;
  macroResearch: string | null;
  sentimentNews: string | null;
};

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const { t } = useLocale();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [widgetData, setWidgetData] = useState<WidgetData>({
    marketData: null,
    macroResearch: null,
    sentimentNews: null,
  });
  const [widgetLoading, setWidgetLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [, setSettings] = useState<AnalysisRequest | null>(null);
  const widgetFetched = useRef<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    const settings = loadSettings();
    const finnhubKey = settings?.finnhub_api_key;

    getAssetDetail(symbol, finnhubKey)
      .then(setAsset)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    if (widgetFetched.current !== symbol) {
      widgetFetched.current = symbol;
      setWidgetLoading(true);
      Promise.all([
        getMarketData(symbol).then((r) => r.data).catch(() => null),
        getMacroResearch(symbol).then((r) => r.data).catch(() => null),
        getSentimentNews(symbol, finnhubKey).then((r) => r.data).catch(() => null),
      ]).then(([marketData, macroResearch, sentimentNews]) => {
        setWidgetData({ marketData, macroResearch, sentimentNews });
      }).finally(() => setWidgetLoading(false));
    }
  }, [symbol]);

  const parsedMarket = useMemo(
    () => widgetData.marketData ? parseMarketData(widgetData.marketData) : null,
    [widgetData.marketData],
  );

  const prefetchedData: Record<string, string> = {};
  if (widgetData.marketData) prefetchedData.fetch_market_data = widgetData.marketData;
  if (widgetData.macroResearch) prefetchedData.fetch_macro_research = widgetData.macroResearch;
  if (widgetData.sentimentNews) prefetchedData.fetch_sentiment_news = widgetData.sentimentNews;

  if (loading) {
    return (
      <div className={styles.skeleton}>
        <Skeleton height={20} width={120} style={{ marginBottom: 24 }} />
        <Skeleton height={180} style={{ marginBottom: 24 }} borderRadius={12} />
        <Skeleton height={200} style={{ marginBottom: 24 }} borderRadius={12} />
        <Skeleton height={140} style={{ marginBottom: 24 }} borderRadius={12} />
        <Skeleton height={340} borderRadius={12} />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <Link to="/" className={styles.backLink}>{t('asset.back')}</Link>
        <div style={{ padding: 24, background: 'var(--red-subtle)', color: 'var(--red)', borderRadius: 'var(--radius-md)', fontSize: 14 }}>
          {t('asset.error', { message: error })}
        </div>
      </div>
    );
  }

  if (!asset) return null;

  return (
    <div className={styles.page}>
      <Link to="/" className={styles.backLink}>{t('asset.back')}</Link>

      <AssetDetailComponent asset={asset} marketData={parsedMarket} />

      <div className={styles.widgetGrid}>
        <DataWidget category="macro_research" data={widgetData.macroResearch} loading={widgetLoading} />
        <DataWidget category="sentiment_news" data={widgetData.sentimentNews} loading={widgetLoading} />
      </div>

      <NewsList news={asset.news.slice(0, 3)} />
      <PriceChart symbol={asset.symbol} />
      <AnalyzePanel
        symbol={asset.symbol}
        prefetchedData={prefetchedData}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={setSettings}
      />
    </div>
  );
}
