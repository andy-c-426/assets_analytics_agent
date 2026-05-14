import { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAssetDetail, getMarketData, getMacroResearch, getSentimentNews, getCapitalFlow, getCnSentiment, getUsFundamentals } from '../api/client';
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
  capitalFlow: string | null;
  cnSentiment: string | null;
  usFundamentals: string | null;
};

export default function AssetPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const { t } = useLocale();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [widgetData, setWidgetData] = useState<WidgetData>({
    marketData: null,
    macroResearch: null,
    sentimentNews: null,
    capitalFlow: null,
    cnSentiment: null,
    usFundamentals: null,
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

      const isCnHk = /\.(SZ|SH|SS|HK)$/i.test(symbol);
      const nonUSSuffixes = /\.(SZ|SH|SS|HK|T|JP|KS|KQ|TW|TWO|TO|V|SI|AX|L|DE|PA|AS|BR|MI|MC|SW|F|BE|VI|LS|ST|CO|HE)$/i;
      const isUS = !nonUSSuffixes.test(symbol);

      const fetchers: Promise<string | null>[] = [
        getMarketData(symbol).then((r) => r.data).catch(() => null),
        getMacroResearch(symbol).then((r) => r.data).catch(() => null),
        getSentimentNews(symbol, finnhubKey).then((r) => r.data).catch(() => null),
        isCnHk ? getCapitalFlow(symbol).then((r) => r.data).catch(() => null) : Promise.resolve(null),
        isCnHk ? getCnSentiment(symbol).then((r) => r.data).catch(() => null) : Promise.resolve(null),
        isUS ? getUsFundamentals(symbol).then((r) => r.data).catch(() => null) : Promise.resolve(null),
      ];

      Promise.all(fetchers).then(([marketData, macroResearch, sentimentNews, capitalFlow, cnSentiment, usFundamentals]) => {
        setWidgetData({ marketData, macroResearch, sentimentNews, capitalFlow, cnSentiment, usFundamentals });
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
  if (widgetData.capitalFlow) prefetchedData.fetch_capital_flow = widgetData.capitalFlow;
  if (widgetData.usFundamentals) prefetchedData.fetch_us_fundamentals = widgetData.usFundamentals;

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
        {widgetData.capitalFlow !== null && (
          <DataWidget category="capital_flow" data={widgetData.capitalFlow} loading={false} />
        )}
        {widgetData.cnSentiment !== null && (
          <DataWidget category="cn_sentiment" data={widgetData.cnSentiment} loading={false} />
        )}
        {widgetData.usFundamentals !== null && (
          <DataWidget category="us_fundamentals" data={widgetData.usFundamentals} loading={false} />
        )}
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
